from datetime import date, timedelta
from typing import Any

from sqlalchemy import select, func
from sqlalchemy.orm import Session

from app.models import MarketPrice, Portfolio, PortfolioHolding, ValuationModel, DcfAssumptionSet, ThesisNote, Alert
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
    portfolio = db.scalar(select(Portfolio).where(Portfolio.id == portfolio_id))
    if not portfolio:
        raise ValueError(f"Portfolio {portfolio_id} not found")

    holdings = db.scalars(
        select(PortfolioHolding).where(
            PortfolioHolding.portfolio_id == portfolio_id,
            PortfolioHolding.quantity > 0,
        )
    ).all()

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

        latest_price = get_latest_price(
            db,
            holding.ticker,
            target_date,
            company_id=holding.company_id,
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

            # Phase 18: Trigger divergence alert check for the company if a new price is pulled
            from app.services.valuation_alert_service import check_price_valuation_divergence
            check_price_valuation_divergence(db, holding.company_id)

        # Check valuation staleness
        base_valuation = db.scalar(
            select(DcfAssumptionSet)
            .join(ValuationModel, ValuationModel.id == DcfAssumptionSet.valuation_model_id)
            .where(ValuationModel.company_id == holding.company_id)
            .where(DcfAssumptionSet.scenario == "Base")
            .order_by(DcfAssumptionSet.id.desc())
            .limit(1)
        )
        is_valuation_stale = base_valuation.is_stale if base_valuation else False
        stale_valuation_reason = base_valuation.stale_reason if base_valuation else None
        intrinsic_value = float(base_valuation.implied_share_price) if base_valuation and base_valuation.implied_share_price is not None else None

        active_thesis = db.scalar(
            select(ThesisNote.status)
            .where(ThesisNote.company_id == holding.company_id)
            .where(ThesisNote.status != "archived")
            .order_by(ThesisNote.updated_at.desc())
            .limit(1)
        )
        thesis_status = active_thesis

        active_alerts_query = (
            select(func.count(Alert.id))
            .where(Alert.company_id == holding.company_id)
            .where(Alert.review_status == "unreviewed")
        )
        if user_id is not None:
            active_alerts_query = active_alerts_query.where(Alert.user_id == user_id)
        active_alerts_count = db.scalar(active_alerts_query)

        if total_cost_base is not None:
            total_cost_basis += total_cost_base
        if market_value_base is not None and total_cost_base is not None:
            unrealized_pnl_base = market_value_base - total_cost_base

        expected_return = None
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
            "intrinsic_value": intrinsic_value,
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

    # Fetch Cash Balance
    from app.models import PortfolioCashBalance
    cash_record = db.scalar(
        select(PortfolioCashBalance)
        .where(PortfolioCashBalance.portfolio_id == portfolio_id)
        .where(PortfolioCashBalance.as_of_date <= target_date)
        .order_by(PortfolioCashBalance.as_of_date.desc(), PortfolioCashBalance.id.desc())
        .limit(1)
    )
    total_cash_value = float(cash_record.amount) if cash_record else 0.0

    total_portfolio_value = None
    if has_complete_market_value:
        total_portfolio_value = total_market_value + total_cash_value
    elif not has_holdings and cash_record is not None:
        total_portfolio_value = total_cash_value

    return {
        "portfolio_id": portfolio.id,
        "as_of_date": target_date,
        "base_currency": portfolio.base_currency,
        "total_market_value": total_market_value if has_complete_market_value else None,
        "total_portfolio_value": total_portfolio_value,
        "total_cash_value": total_cash_value,
        "total_cost_basis": total_cost_basis,
        "total_unrealized_pnl": total_unrealized_pnl,
        "total_unrealized_pnl_percent": total_unrealized_pnl_percent,
        "missing_fx_pairs": sorted(missing_fx_pairs),
        "holdings": holdings_valuation,
    }
