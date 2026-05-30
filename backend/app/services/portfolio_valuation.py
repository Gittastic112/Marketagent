from datetime import date, timedelta
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import MarketPrice, Portfolio, PortfolioHolding


def get_latest_price(db: Session, ticker: str, as_of_date: date | None = None) -> MarketPrice | None:
    query = select(MarketPrice).where(MarketPrice.ticker == ticker.upper())
    if as_of_date:
        query = query.where(MarketPrice.as_of_date <= as_of_date)
    query = query.order_by(MarketPrice.as_of_date.desc(), MarketPrice.id.desc()).limit(1)
    return db.scalars(query).first()


def calculate_portfolio_valuation(db: Session, portfolio_id: int, as_of_date: date | None = None) -> dict[str, Any]:
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
    stale_threshold = timedelta(days=5)

    holdings_valuation = []

    for holding in holdings:
        # Ignore holding as_of_date for current valuation, use target_date
        qty = float(holding.quantity)
        avg_cost = float(holding.average_cost)
        total_cost = qty * avg_cost

        latest_price = get_latest_price(db, holding.ticker, target_date)

        market_price = None
        market_price_as_of = None
        market_value = None
        unrealized_pnl = None
        unrealized_pnl_percent = None
        is_stale = True

        if latest_price:
            market_price = float(latest_price.price)
            market_price_as_of = latest_price.as_of_date
            market_value = qty * market_price
            unrealized_pnl = market_value - total_cost
            if total_cost > 0:
                unrealized_pnl_percent = (unrealized_pnl / total_cost) * 100
            
            is_stale = (target_date - market_price_as_of) > stale_threshold
            total_market_value += market_value

        total_cost_basis += total_cost

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
            "weight_percent": None,  # Will calculate after total_market_value is known
            "is_stale_price": is_stale,
        })

    total_unrealized_pnl = None
    total_unrealized_pnl_percent = None

    if total_market_value > 0 or total_cost_basis > 0:
        total_unrealized_pnl = total_market_value - total_cost_basis
        if total_cost_basis > 0:
            total_unrealized_pnl_percent = (total_unrealized_pnl / total_cost_basis) * 100

    # Second pass for weights
    for hv in holdings_valuation:
        if hv["market_value"] is not None and total_market_value > 0:
            hv["weight_percent"] = (hv["market_value"] / total_market_value) * 100
        elif hv["market_value"] is None and total_market_value == 0 and total_cost_basis > 0:
            # Fallback weight by cost basis if no market values exist
            hv["weight_percent"] = (hv["total_cost"] / total_cost_basis) * 100
        else:
            hv["weight_percent"] = 0.0

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
    if total_market_value > 0 or total_cost_basis > 0:
        total_portfolio_value = total_market_value + total_cash_value

    return {
        "portfolio_id": portfolio.id,
        "as_of_date": target_date,
        "base_currency": portfolio.base_currency,
        "total_market_value": total_market_value if any(h["market_value"] is not None for h in holdings_valuation) else None,
        "total_portfolio_value": total_portfolio_value,
        "total_cash_value": total_cash_value,
        "total_cost_basis": total_cost_basis,
        "total_unrealized_pnl": total_unrealized_pnl,
        "total_unrealized_pnl_percent": total_unrealized_pnl_percent,
        "holdings": holdings_valuation,
    }
