from datetime import date, timedelta
from typing import Any

from sqlalchemy import case, func, or_, select
from sqlalchemy.orm import Session, selectinload

from app.models import Alert, DcfAssumptionSet, DcfOutput, MarketPrice, Portfolio, PortfolioCashBalance, PortfolioHolding, ThesisNote, ValuationModel
from app.services.fx_rates import FxRateUnavailable, convert_amount


def get_latest_price(
    db: Session,
    ticker: str,
    as_of_date: date | None = None,
    *,
    company_id: int | None = None,
) -> MarketPrice | None:
    query = select(MarketPrice).where(MarketPrice.ticker == ticker.upper())
    if company_id is not None:
        query = query.where(MarketPrice.company_id == company_id)
    if as_of_date:
        query = query.where(MarketPrice.as_of_date <= as_of_date)
    query = query.order_by(MarketPrice.as_of_date.desc(), MarketPrice.id.desc()).limit(1)
    return db.scalars(query).first()


def calculate_portfolio_valuation(
    db: Session,
    portfolio_id: int,
    as_of_date: date | None = None,
    *,
    user_id: str | None = None,
) -> dict[str, Any]:
    target_date = as_of_date or date.today()
    portfolio_query = select(Portfolio).where(Portfolio.id == portfolio_id)
    if user_id is not None:
        portfolio_query = portfolio_query.where(Portfolio.user_id == user_id)
    portfolio = db.scalar(portfolio_query)
    if not portfolio:
        raise ValueError(f"Portfolio {portfolio_id} not found")
    # Internal snapshot/attribution callers omit an explicit owner. They must still
    # use this portfolio's private context, never global latest research records.
    user_id = portfolio.user_id

    holdings = list(db.scalars(
        select(PortfolioHolding)
        .options(selectinload(PortfolioHolding.company))
        .where(
            PortfolioHolding.portfolio_id == portfolio_id,
            PortfolioHolding.quantity > 0,
        )
        .order_by(PortfolioHolding.id)
    ))

    company_ids = sorted({
        holding.company_id for holding in holdings if holding.company_id is not None
    })
    unlinked_tickers = sorted({
        holding.ticker.upper() for holding in holdings if holding.company_id is None
    })
    price_filters = []
    if company_ids:
        price_filters.append(MarketPrice.company_id.in_(company_ids))
    if unlinked_tickers:
        price_filters.append(
            (MarketPrice.company_id.is_(None))
            & (MarketPrice.ticker.in_(unlinked_tickers))
        )
    price_records = []
    if price_filters:
        # Rank in SQL so a current valuation does not materialize years of prices.
        # Linked company identity wins; unlinked tickers remain a separate namespace.
        ranked_prices = select(
            MarketPrice.id,
            func.row_number().over(
                partition_by=(MarketPrice.company_id, case(
                    (MarketPrice.company_id.is_(None), func.upper(MarketPrice.ticker)),
                    else_=None,
                )),
                order_by=(MarketPrice.as_of_date.desc(), MarketPrice.id.desc()),
            ).label("position"),
        ).where(MarketPrice.as_of_date <= target_date, or_(*price_filters)).subquery()
        price_records = list(db.scalars(
            select(MarketPrice)
            .join(ranked_prices, ranked_prices.c.id == MarketPrice.id)
            .where(ranked_prices.c.position == 1)
        ))
    latest_price_by_company: dict[int, MarketPrice] = {}
    latest_price_by_ticker: dict[str, MarketPrice] = {}
    for price in price_records:
        if price.company_id is not None:
            latest_price_by_company.setdefault(price.company_id, price)
        else:
            latest_price_by_ticker.setdefault(price.ticker.upper(), price)

    latest_valuation_by_company: dict[int, tuple[DcfAssumptionSet, DcfOutput | None]] = {}
    if company_ids:
        valuation_query = (
            select(ValuationModel.company_id, DcfAssumptionSet, DcfOutput)
            .join(DcfAssumptionSet, DcfAssumptionSet.valuation_model_id == ValuationModel.id)
            .outerjoin(DcfOutput, DcfOutput.assumption_set_id == DcfAssumptionSet.id)
            .where(
                ValuationModel.company_id.in_(company_ids),
                DcfAssumptionSet.scenario == "Base",
            )
            .order_by(
                ValuationModel.company_id,
                DcfAssumptionSet.id.desc(),
                DcfOutput.id.desc(),
            )
        )
        if user_id is not None:
            valuation_query = valuation_query.where(ValuationModel.user_id == user_id)
        for company_id, assumption_set, output in db.execute(valuation_query):
            latest_valuation_by_company.setdefault(company_id, (assumption_set, output))

    thesis_status_by_company: dict[int, str] = {}
    if company_ids:
        for company_id, status in db.execute(
            select(ThesisNote.company_id, ThesisNote.status)
            .where(
                ThesisNote.company_id.in_(company_ids),
                ThesisNote.user_id == user_id,
                ThesisNote.status != "archived",
            )
            .order_by(ThesisNote.company_id, ThesisNote.updated_at.desc())
        ):
            thesis_status_by_company.setdefault(company_id, status)

    alert_count_by_company: dict[int, int] = {}
    if company_ids:
        active_alerts_query = (
            select(Alert.company_id, func.count(Alert.id))
            .where(
                Alert.company_id.in_(company_ids),
                Alert.review_status == "unreviewed",
            )
            .group_by(Alert.company_id)
        )
        if user_id is not None:
            active_alerts_query = active_alerts_query.where(Alert.user_id == user_id)
        alert_count_by_company = {
            company_id: count
            for company_id, count in db.execute(active_alerts_query)
            if company_id is not None
        }

    total_market_value = 0.0
    total_cost_basis = 0.0
    missing_fx_pairs: set[str] = set()
    stale_threshold = timedelta(days=5)

    holdings_valuation = []

    for holding in holdings:
        # Ignore holding as_of_date for current valuation, use target_date
        qty = float(holding.quantity)
        avg_cost = float(holding.average_cost)
        total_cost = qty * avg_cost

        latest_price = (
            latest_price_by_company.get(holding.company_id)
            if holding.company_id is not None
            else latest_price_by_ticker.get(holding.ticker.upper())
        )

        market_price = None
        market_price_as_of = None
        market_value = None
        unrealized_pnl = None
        unrealized_pnl_percent = None
        market_value_base = None
        total_cost_base = None
        unrealized_pnl_base = None
        market_fx = None
        cost_fx = None
        is_stale = True

        try:
            converted_cost, cost_fx = convert_amount(
                db,
                total_cost,
                holding.currency,
                portfolio.base_currency,
                holding.as_of_date,
            )
            total_cost_base = float(converted_cost)
        except FxRateUnavailable:
            missing_fx_pairs.add(f"{holding.currency.upper()}/{portfolio.base_currency.upper()}")

        if latest_price:
            market_price = float(latest_price.price)
            market_price_as_of = latest_price.as_of_date
            market_value = qty * market_price
            unrealized_pnl = market_value - total_cost
            if total_cost > 0:
                unrealized_pnl_percent = (unrealized_pnl / total_cost) * 100

            is_stale = (target_date - market_price_as_of) > stale_threshold
            try:
                converted_market_value, market_fx = convert_amount(
                    db,
                    market_value,
                    latest_price.currency or holding.currency,
                    portfolio.base_currency,
                    target_date,
                )
                market_value_base = float(converted_market_value)
            except FxRateUnavailable:
                missing_fx_pairs.add(
                    f"{(latest_price.currency or holding.currency).upper()}/{portfolio.base_currency.upper()}"
                )

            if market_value_base is not None:
                total_market_value += market_value_base

        base_valuation = latest_valuation_by_company.get(holding.company_id)
        assumption_set = base_valuation[0] if base_valuation else None
        dcf_output = base_valuation[1] if base_valuation else None
        is_valuation_stale = assumption_set.is_stale if assumption_set else False
        stale_valuation_reason = assumption_set.stale_reason if assumption_set else None
        raw_intrinsic_value = (
            float(dcf_output.intrinsic_value_per_share)
            if dcf_output and dcf_output.intrinsic_value_per_share is not None
            else None
        )

        thesis_status = thesis_status_by_company.get(holding.company_id)
        active_alerts_count = alert_count_by_company.get(holding.company_id, 0)

        if total_cost_base is not None:
            total_cost_basis += total_cost_base
        if market_value_base is not None and total_cost_base is not None:
            unrealized_pnl_base = market_value_base - total_cost_base

        expected_return = None
        valuation_currency = holding.company.currency if holding.company else None
        market_currency = (latest_price.currency or holding.currency) if latest_price else None
        valuation_status = "trusted"
        valuation_status_reason = None
        if assumption_set is None or dcf_output is None:
            valuation_status = "unavailable"
            valuation_status_reason = "No completed Base DCF output is available."
        elif assumption_set.is_stale:
            valuation_status = "stale"
            valuation_status_reason = assumption_set.stale_reason or "Base DCF assumptions are stale."
        elif dcf_output.model_quality_score is None or float(dcf_output.model_quality_score) < 60:
            valuation_status = "untrusted"
            valuation_status_reason = "The latest Base DCF output does not meet the 60/100 quality gate."
        elif dcf_output.warnings_json:
            valuation_status = "untrusted"
            valuation_status_reason = "The latest Base DCF output has unresolved diagnostic warnings."
        elif raw_intrinsic_value is None or raw_intrinsic_value <= 0:
            valuation_status = "untrusted"
            valuation_status_reason = "The latest Base DCF output has no positive intrinsic value per share."
        elif not valuation_currency or not market_currency:
            valuation_status = "untrusted"
            valuation_status_reason = "Valuation and market-price currencies are required for a safe comparison."
        elif valuation_currency.upper() != market_currency.upper():
            valuation_status = "untrusted"
            valuation_status_reason = (
                f"DCF currency {valuation_currency.upper()} does not match market-price currency {market_currency.upper()}."
            )
        dcf_is_trusted = valuation_status == "trusted"
        intrinsic_value = raw_intrinsic_value if dcf_is_trusted else None
        if intrinsic_value is not None and market_price is not None and market_price > 0:
            expected_return = (intrinsic_value - market_price) / market_price

        holdings_valuation.append({
            "holding_id": holding.id,
            "ticker": holding.ticker,
            "company_id": holding.company_id,
            "quantity": qty,
            "average_cost": avg_cost,
            "currency": holding.currency,
            "market_price": market_price,
            "market_price_id": latest_price.id if latest_price else None,
            "market_price_provider": latest_price.provider_name if latest_price else None,
            "market_price_as_of": market_price_as_of,
            "market_value": market_value,
            "total_cost": total_cost,
            "unrealized_pnl": unrealized_pnl,
            "unrealized_pnl_percent": unrealized_pnl_percent,
            "market_value_base": market_value_base,
            "total_cost_base": total_cost_base,
            "unrealized_pnl_base": unrealized_pnl_base,
            "market_fx_rate_to_base": float(market_fx.rate) if market_fx else None,
            "market_fx_rate_as_of": market_fx.as_of_date if market_fx else None,
            "market_fx_observation_id": market_fx.observation_id if market_fx else None,
            "market_fx_is_stale": market_fx.is_stale if market_fx else False,
            "cost_fx_rate_to_base": float(cost_fx.rate) if cost_fx else None,
            "cost_fx_rate_as_of": cost_fx.as_of_date if cost_fx else None,
            "cost_fx_observation_id": cost_fx.observation_id if cost_fx else None,
            "cost_fx_is_stale": cost_fx.is_stale if cost_fx else False,
            "weight_percent": None,  # Will calculate after total_market_value is known
            "is_stale_price": is_stale,
            "is_valuation_stale": is_valuation_stale,
            "stale_valuation_reason": stale_valuation_reason,
            "valuation_status": valuation_status,
            "valuation_status_reason": valuation_status_reason,
            "intrinsic_value": intrinsic_value,
            "dcf_output_id": dcf_output.id if dcf_output else None,
            "expected_return": expected_return,
            "thesis_status": thesis_status,
            "active_alerts_count": active_alerts_count or 0,
            # Historical FX and benchmark series are not persisted yet. These
            # fields must remain unavailable instead of presenting estimates.
            "fx_impact": None,
            "opportunity_cost": None,
            "opportunity_cost_percent": None,
        })

    has_holdings = bool(holdings_valuation)
    has_missing_prices = any(
        holding["market_value_base"] is None
        for holding in holdings_valuation
    )
    has_complete_market_value = has_holdings and not has_missing_prices
    has_complete_cost_basis = has_holdings and all(
        holding["total_cost_base"] is not None for holding in holdings_valuation
    )

    total_unrealized_pnl = None
    total_unrealized_pnl_percent = None
    if has_complete_market_value and has_complete_cost_basis:
        total_unrealized_pnl = total_market_value - total_cost_basis
        if total_cost_basis > 0:
            total_unrealized_pnl_percent = (total_unrealized_pnl / total_cost_basis) * 100

    # Second pass for weights
    for hv in holdings_valuation:
        if has_complete_market_value and total_market_value > 0:
            hv["weight_percent"] = (hv["market_value_base"] / total_market_value) * 100
        else:
            hv["weight_percent"] = None

    # Sort holdings by weight descending
    holdings_valuation.sort(key=lambda x: x["weight_percent"] or 0, reverse=True)

    cash_records = list(db.scalars(
        select(PortfolioCashBalance)
        .where(PortfolioCashBalance.portfolio_id == portfolio_id)
        .where(PortfolioCashBalance.as_of_date <= target_date)
        .order_by(PortfolioCashBalance.as_of_date.desc(), PortfolioCashBalance.id.desc())
    ))
    latest_cash_by_currency: dict[str, PortfolioCashBalance] = {}
    for cash_record in cash_records:
        latest_cash_by_currency.setdefault(cash_record.currency.upper(), cash_record)

    cash_valuations = []
    total_cash_value = 0.0
    cash_complete = True
    for currency, cash_record in sorted(latest_cash_by_currency.items()):
        value_base = None
        cash_fx = None
        try:
            converted_cash, cash_fx = convert_amount(
                db,
                cash_record.amount,
                currency,
                portfolio.base_currency,
                target_date,
            )
            value_base = float(converted_cash)
            total_cash_value += value_base
        except FxRateUnavailable:
            cash_complete = False
            missing_fx_pairs.add(f"{currency}/{portfolio.base_currency.upper()}")
        cash_valuations.append(
            {
                "cash_balance_id": cash_record.id,
                "currency": currency,
                "amount": float(cash_record.amount),
                "as_of_date": cash_record.as_of_date,
                "value_base": value_base,
                "fx_rate_to_base": float(cash_fx.rate) if cash_fx else None,
                "fx_rate_as_of": cash_fx.as_of_date if cash_fx else None,
                "fx_observation_id": cash_fx.observation_id if cash_fx else None,
                "fx_is_stale": cash_fx.is_stale if cash_fx else False,
            }
        )
    if not cash_complete:
        total_cash_value = None

    total_portfolio_value = None
    if has_complete_market_value and cash_complete:
        total_portfolio_value = total_market_value + total_cash_value
    elif not has_holdings and latest_cash_by_currency and cash_complete:
        total_portfolio_value = total_cash_value

    return {
        "portfolio_id": portfolio.id,
        "as_of_date": target_date,
        "base_currency": portfolio.base_currency,
        "total_market_value": total_market_value if has_complete_market_value else None,
        "total_portfolio_value": total_portfolio_value,
        "total_cash_value": total_cash_value,
        "total_cost_basis": total_cost_basis if has_complete_cost_basis else None,
        "total_unrealized_pnl": total_unrealized_pnl,
        "total_unrealized_pnl_percent": total_unrealized_pnl_percent,
        "missing_fx_pairs": sorted(missing_fx_pairs),
        "cash_balances": cash_valuations,
        "holdings": holdings_valuation,
    }
