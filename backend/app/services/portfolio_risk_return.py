from __future__ import annotations

from datetime import UTC, date, datetime, time, timedelta
from math import sqrt
from statistics import fmean
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models import (
    DcfAssumptionSet,
    DcfOutput,
    MarketPrice,
    Portfolio,
    PortfolioHolding,
    ValuationModel,
)
from app.services.fx_rates import FxRateUnavailable, convert_amount


TRADING_DAYS_PER_YEAR = 252
MINIMUM_DCF_QUALITY_SCORE = 60.0
CURRENT_PRICE_MAX_AGE_DAYS = 5


def _sample_covariance(left: list[float], right: list[float]) -> float:
    if len(left) != len(right) or len(left) < 2:
        raise ValueError("Sample covariance requires aligned series with at least two observations.")
    left_mean = fmean(left)
    right_mean = fmean(right)
    return sum(
        (left_value - left_mean) * (right_value - right_mean)
        for left_value, right_value in zip(left, right, strict=True)
    ) / (len(left) - 1)


def _price_history(
    db: Session,
    holding: PortfolioHolding,
    start_date: date,
    end_date: date,
) -> list[MarketPrice]:
    query = select(MarketPrice).where(
        MarketPrice.as_of_date >= start_date,
        MarketPrice.as_of_date <= end_date,
    )
    if holding.company_id is not None:
        query = query.where(MarketPrice.company_id == holding.company_id)
    else:
        query = query.where(MarketPrice.company_id.is_(None), MarketPrice.ticker == holding.ticker.upper())
    records = db.scalars(
        query.order_by(MarketPrice.as_of_date.asc(), MarketPrice.id.asc())
    ).all()
    latest_by_date: dict[date, MarketPrice] = {}
    for record in records:
        latest_by_date[record.as_of_date] = record
    return [latest_by_date[day] for day in sorted(latest_by_date)]


def _latest_price(
    db: Session,
    holding: PortfolioHolding,
    target_date: date,
) -> MarketPrice | None:
    query = select(MarketPrice).where(MarketPrice.as_of_date <= target_date)
    if holding.company_id is not None:
        query = query.where(MarketPrice.company_id == holding.company_id)
    else:
        query = query.where(MarketPrice.company_id.is_(None), MarketPrice.ticker == holding.ticker.upper())
    return db.scalar(
        query.order_by(MarketPrice.as_of_date.desc(), MarketPrice.id.desc()).limit(1)
    )


def _latest_dcf_output(
    db: Session,
    company_id: int | None,
    target_date: date,
    user_id: str | None,
) -> tuple[DcfAssumptionSet, DcfOutput] | None:
    if company_id is None:
        return None
    cutoff = datetime.combine(target_date, time.max, tzinfo=UTC)
    query = (
        select(DcfAssumptionSet, DcfOutput)
        .join(ValuationModel, ValuationModel.id == DcfAssumptionSet.valuation_model_id)
        .join(DcfOutput, DcfOutput.assumption_set_id == DcfAssumptionSet.id)
        .where(
            ValuationModel.company_id == company_id,
            DcfAssumptionSet.scenario == "Base",
            DcfOutput.created_at <= cutoff,
        )
        .order_by(DcfOutput.created_at.desc(), DcfOutput.id.desc())
        .limit(1)
    )
    if user_id is not None:
        query = query.where(ValuationModel.user_id == user_id)
    result = db.execute(query).first()
    return (result[0], result[1]) if result else None


def _dcf_valuation_gap(
    assumption_set: DcfAssumptionSet | None,
    output: DcfOutput | None,
    market_price: float | None,
    valuation_currency: str | None,
    market_price_currency: str | None,
) -> tuple[float | None, list[str]]:
    warnings: list[str] = []
    if assumption_set is None or output is None:
        return None, ["No completed Base DCF output is available."]
    if assumption_set.is_stale:
        reason = f" Reason: {assumption_set.stale_reason}." if assumption_set.stale_reason else ""
        warnings.append(f"The Base DCF assumption set is stale.{reason}")
    if output.model_quality_score is None:
        warnings.append("The DCF output has no model quality score.")
    elif float(output.model_quality_score) < MINIMUM_DCF_QUALITY_SCORE:
        warnings.append(
            f"The DCF model quality score is below {MINIMUM_DCF_QUALITY_SCORE:.0f}/100."
        )
    output_warnings = [str(warning) for warning in (output.warnings_json or [])]
    if output_warnings:
        warnings.append("The DCF output has unresolved diagnostic warnings.")
    intrinsic_value = (
        float(output.intrinsic_value_per_share)
        if output.intrinsic_value_per_share is not None
        else None
    )
    if intrinsic_value is None or intrinsic_value <= 0:
        warnings.append("The DCF output has no positive intrinsic value per share.")
    if market_price is None or market_price <= 0:
        warnings.append("No positive source-backed market price is available for comparison.")
    elif not valuation_currency:
        warnings.append("The company has no valuation currency, so the DCF output cannot be compared safely.")
    elif not market_price_currency:
        warnings.append("The market price has no currency, so the DCF output cannot be compared safely.")
    elif valuation_currency.upper() != market_price_currency.upper():
        warnings.append(
            f"DCF currency {valuation_currency.upper()} does not match market price currency {market_price_currency.upper()}."
        )
    if warnings:
        return None, warnings
    return (intrinsic_value - market_price) / market_price, []


def calculate_portfolio_risk_return(
    db: Session,
    portfolio_id: int,
    as_of_date: date | None = None,
    *,
    lookback_days: int = 365,
    min_observations: int = 20,
    user_id: str | None = None,
) -> dict[str, Any]:
    if not 30 <= lookback_days <= 3650:
        raise ValueError("lookback_days must be between 30 and 3650")
    if not 2 <= min_observations <= 2520:
        raise ValueError("min_observations must be between 2 and 2520")

    target_date = as_of_date or date.today()
    start_date = target_date - timedelta(days=lookback_days)
    portfolio_query = select(Portfolio).where(Portfolio.id == portfolio_id)
    if user_id is not None:
        portfolio_query = portfolio_query.where(Portfolio.user_id == user_id)
    portfolio = db.scalar(portfolio_query)
    if portfolio is None:
        raise ValueError(f"Portfolio {portfolio_id} not found")
    user_id = portfolio.user_id
    holdings = list(
        db.scalars(
            select(PortfolioHolding)
            .options(selectinload(PortfolioHolding.company))
            .where(
                PortfolioHolding.portfolio_id == portfolio_id,
                PortfolioHolding.quantity > 0,
            )
            .order_by(PortfolioHolding.id)
        )
    )

    blockers: list[str] = []
    warnings: list[str] = []
    rows: list[dict[str, Any]] = []
    source_market_price_ids: set[int] = set()
    source_fx_observation_ids: set[int] = set()
    source_dcf_output_ids: set[int] = set()
    contains_mock_data = False
    current_values: dict[int, float] = {}
    return_series: dict[int, dict[date, float]] = {}

    if not holdings:
        blockers.append("The portfolio has no positive-quantity holdings.")

    for holding in holdings:
        row_warnings: list[str] = []
        prices = _price_history(db, holding, start_date, target_date)
        converted_prices: list[tuple[date, float]] = []
        holding_price_ids: set[int] = set()
        holding_fx_ids: set[int] = set()
        for price in prices:
            if (
                (price.price_type or "").strip().lower() == "mock data"
                or "mock" in (price.provider_name or "").lower()
            ):
                contains_mock_data = True
            holding_price_ids.add(price.id)
            source_market_price_ids.add(price.id)
            try:
                converted, fx = convert_amount(
                    db,
                    price.price,
                    price.currency or holding.currency,
                    portfolio.base_currency,
                    price.as_of_date,
                )
            except FxRateUnavailable:
                row_warnings.append(
                    f"Missing FX rate for {(price.currency or holding.currency).upper()}/{portfolio.base_currency.upper()} on {price.as_of_date}."
                )
                continue
            converted_prices.append((price.as_of_date, float(converted)))
            if fx.observation_id is not None:
                holding_fx_ids.add(fx.observation_id)
                source_fx_observation_ids.add(fx.observation_id)
            if fx.is_stale:
                row_warnings.append(
                    f"FX observation {fx.observation_id} was {fx.age_days} days old on {price.as_of_date}."
                )

        returns: dict[date, float] = {}
        for previous, current in zip(converted_prices, converted_prices[1:]):
            if previous[1] > 0:
                returns[current[0]] = (current[1] / previous[1]) - 1
        return_series[holding.id] = returns

        latest = _latest_price(db, holding, target_date)
        current_price = float(latest.price) if latest else None
        price_age_days = (target_date - latest.as_of_date).days if latest else None
        stale_price = price_age_days is not None and price_age_days > CURRENT_PRICE_MAX_AGE_DAYS
        if stale_price:
            row_warnings.append(f"The latest price is {price_age_days} days old; weights use stale prices and the current DCF gap is unavailable.")
            warnings.append("Some current weights use prices older than 5 calendar days. Historical risk remains a partial calculation, not current risk coverage.")
        if latest and ("mock" in (latest.provider_name or "").lower() or (latest.claim_type or "").lower() == "mock data"):
            contains_mock_data = True
        current_value = None
        if latest is None:
            row_warnings.append("No market price is available on or before the requested date.")
        else:
            holding_price_ids.add(latest.id)
            source_market_price_ids.add(latest.id)
            try:
                converted_latest, latest_fx = convert_amount(
                    db,
                    float(holding.quantity) * float(latest.price),
                    latest.currency or holding.currency,
                    portfolio.base_currency,
                    latest.as_of_date,
                )
                current_value = float(converted_latest)
                current_values[holding.id] = current_value
                if latest_fx.observation_id is not None:
                    holding_fx_ids.add(latest_fx.observation_id)
                    source_fx_observation_ids.add(latest_fx.observation_id)
            except FxRateUnavailable:
                row_warnings.append(
                    f"The current holding value cannot be converted from {(latest.currency or holding.currency).upper()} to {portfolio.base_currency.upper()}."
                )

        historical_return = None
        annualized_volatility = None
        ordered_return_values = [returns[day] for day in sorted(returns)]
        if len(converted_prices) >= 2 and converted_prices[0][1] > 0:
            historical_return = converted_prices[-1][1] / converted_prices[0][1] - 1
        if len(ordered_return_values) >= 2:
            annualized_volatility = sqrt(
                _sample_covariance(ordered_return_values, ordered_return_values)
                * TRADING_DAYS_PER_YEAR
            )
        if len(returns) < min_observations:
            blockers.append(
                f"{holding.ticker} has {len(returns)} return observations; {min_observations} are required."
            )

        dcf_pair = _latest_dcf_output(
            db, holding.company_id, target_date, user_id
        )
        company = holding.company if holding.company_id is not None else None
        assumption_set = dcf_pair[0] if dcf_pair else None
        dcf_output = dcf_pair[1] if dcf_pair else None
        expected_return, dcf_warnings = _dcf_valuation_gap(
            assumption_set,
            dcf_output,
            None if stale_price else current_price,
            company.currency if company else None,
            (latest.currency or holding.currency) if latest else None,
        )
        row_warnings.extend(dcf_warnings)
        if dcf_output is not None:
            source_dcf_output_ids.add(dcf_output.id)

        rows.append(
            {
                "holding_id": holding.id,
                "company_id": holding.company_id,
                "ticker": holding.ticker,
                "portfolio_weight_decimal": None,
                "risk_model_weight_decimal": None,
                "current_market_value_base": current_value,
                "latest_market_price_as_of": latest.as_of_date if latest else None,
                "price_age_days": price_age_days,
                "is_stale_price": stale_price,
                "observation_count": len(returns),
                "aligned_observation_count": 0,
                "return_start_date": converted_prices[0][0] if converted_prices else None,
                "return_end_date": converted_prices[-1][0] if converted_prices else None,
                "historical_return_decimal": historical_return,
                "annualized_volatility": annualized_volatility,
                "marginal_volatility": None,
                "marginal_volatility_for_one_percent": None,
                "component_risk": None,
                "component_risk_percent": None,
                "expected_return_decimal": expected_return,
                "expected_return_kind": (
                    "dcf_valuation_gap_not_annualized" if expected_return is not None else "unavailable"
                ),
                "expected_return_claim_type": "Estimate" if expected_return is not None else "Unavailable",
                "expected_return_contribution": None,
                "source_dcf_output_id": dcf_output.id if dcf_output else None,
                "source_market_price_ids": sorted(holding_price_ids),
                "source_fx_observation_ids": sorted(holding_fx_ids),
                "warnings": sorted(set(row_warnings)),
            }
        )

    total_current_value = sum(current_values.values())
    if holdings and total_current_value <= 0:
        blockers.append("No holdings have a current base-currency market value.")
    for row in rows:
        current_value = current_values.get(row["holding_id"])
        if current_value is not None and total_current_value > 0:
            row["portfolio_weight_decimal"] = current_value / total_current_value

    eligible_rows = [
        row
        for row in rows
        if row["portfolio_weight_decimal"] is not None
        and row["observation_count"] >= min_observations
    ]
    risk_covered_weight = sum(row["portfolio_weight_decimal"] for row in eligible_rows)
    common_dates: set[date] = set()
    if eligible_rows:
        common_dates = set(return_series[eligible_rows[0]["holding_id"]])
        for row in eligible_rows[1:]:
            common_dates &= set(return_series[row["holding_id"]])
    aligned_dates = sorted(common_dates)
    portfolio_volatility = None
    reconciliation_error = None
    risk_status = "not_available"
    if eligible_rows and len(aligned_dates) >= min_observations and risk_covered_weight > 0:
        weights = [row["portfolio_weight_decimal"] / risk_covered_weight for row in eligible_rows]
        aligned_series = [
            [return_series[row["holding_id"]][day] for day in aligned_dates]
            for row in eligible_rows
        ]
        covariance = [
            [
                _sample_covariance(left, right) * TRADING_DAYS_PER_YEAR
                for right in aligned_series
            ]
            for left in aligned_series
        ]
        variance = sum(
            weights[i] * covariance[i][j] * weights[j]
            for i in range(len(weights))
            for j in range(len(weights))
        )
        portfolio_volatility = sqrt(max(variance, 0.0))
        components: list[float] = []
        for index, row in enumerate(eligible_rows):
            covariance_with_portfolio = sum(
                covariance[index][other] * weights[other]
                for other in range(len(weights))
            )
            marginal = (
                covariance_with_portfolio / portfolio_volatility
                if portfolio_volatility > 0
                else 0.0
            )
            component = weights[index] * marginal
            components.append(component)
            row["risk_model_weight_decimal"] = weights[index]
            row["aligned_observation_count"] = len(aligned_dates)
            row["marginal_volatility"] = marginal
            row["marginal_volatility_for_one_percent"] = marginal * 0.01
            row["component_risk"] = component
            row["component_risk_percent"] = (
                component / portfolio_volatility if portfolio_volatility > 0 else 0.0
            )
        reconciliation_error = sum(components) - portfolio_volatility
        risk_status = "complete" if len(eligible_rows) == len(holdings) and not any(row["is_stale_price"] for row in eligible_rows) else "partial"
    elif eligible_rows:
        blockers.append(
            f"Only {len(aligned_dates)} aligned return observations are available; {min_observations} are required."
        )

    expected_rows = [
        row
        for row in rows
        if row["portfolio_weight_decimal"] is not None
        and row["expected_return_decimal"] is not None
    ]
    expected_covered_weight = sum(row["portfolio_weight_decimal"] for row in expected_rows)
    portfolio_expected_return = None
    expected_status = "not_available"
    if expected_rows:
        portfolio_expected_return = 0.0
        for row in expected_rows:
            contribution = row["portfolio_weight_decimal"] * row["expected_return_decimal"]
            row["expected_return_contribution"] = contribution
            portfolio_expected_return += contribution
        expected_status = "complete" if len(expected_rows) == len(holdings) else "partial"

    if len(current_values) != len(holdings):
        warnings.append(
            "Portfolio weights cover only holdings with an available base-currency market value."
        )
    if risk_status == "partial":
        warnings.append("Historical risk has incomplete history coverage or stale current-price weights; inspect holding warnings.")
    if expected_status != "complete":
        warnings.append("DCF valuation-gap coverage is incomplete; unavailable holdings contribute zero to the aggregate rather than an invented estimate.")

    if risk_status == "complete" and expected_status == "complete":
        calculation_status = "complete"
    elif risk_status != "not_available" or expected_status != "not_available":
        calculation_status = "partial"
    else:
        calculation_status = "not_available"

    return {
        "portfolio_id": portfolio.id,
        "as_of_date": target_date,
        "lookback_start_date": start_date,
        "lookback_days": lookback_days,
        "min_observations": min_observations,
        "base_currency": portfolio.base_currency,
        "calculation_status": calculation_status,
        "risk_calculation_status": risk_status,
        "expected_return_calculation_status": expected_status,
        "portfolio_volatility_annualized": portfolio_volatility,
        "risk_covered_weight_percent": risk_covered_weight * 100,
        "risk_reconciliation_error": reconciliation_error,
        "portfolio_expected_return_decimal": portfolio_expected_return,
        "expected_return_coverage_percent": expected_covered_weight * 100,
        "risk_claim_type": "Calculation" if portfolio_volatility is not None else "Unavailable",
        "expected_return_claim_type": "Estimate" if portfolio_expected_return is not None else "Unavailable",
        "contains_mock_data": contains_mock_data,
        "risk_formula": "Sample covariance of aligned daily base-currency returns, annualized with 252 trading days; component risk sums to portfolio volatility.",
        "expected_return_formula": "Current portfolio weight multiplied by the latest trusted Base DCF valuation gap. This is not an annualized return forecast.",
        "holdings": rows,
        "warnings": sorted(set(warnings)),
        "blockers": sorted(set(blockers)),
        "source_market_price_ids": sorted(source_market_price_ids),
        "source_fx_observation_ids": sorted(source_fx_observation_ids),
        "source_dcf_output_ids": sorted(source_dcf_output_ids),
    }
