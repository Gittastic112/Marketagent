from datetime import date
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Company, PortfolioSnapshot
from app.services.portfolio_valuation import calculate_portfolio_valuation


def _snapshot_json_value(value: Any) -> Any:
    return value.isoformat() if isinstance(value, date) else value


def record_daily_snapshot(db: Session, portfolio_id: int, as_of_date: date | None = None) -> PortfolioSnapshot:
    target_date = as_of_date or date.today()
    existing_snapshot = db.scalar(
        select(PortfolioSnapshot)
        .where(PortfolioSnapshot.portfolio_id == portfolio_id)
        .where(PortfolioSnapshot.snapshot_date == target_date)
    )

    valuation = calculate_portfolio_valuation(db, portfolio_id, target_date)
    holdings = valuation["holdings"]
    missing_price_tickers = sorted(
        holding["ticker"] for holding in holdings if holding["market_price"] is None
    )
    missing_fx_pairs = valuation.get("missing_fx_pairs", [])
    has_any_data = bool(holdings or valuation.get("cash_balances"))
    calculation_status = "not_available"
    if has_any_data:
        calculation_status = (
            "complete"
            if valuation["total_portfolio_value"] is not None
            and not missing_price_tickers
            and not missing_fx_pairs
            else "partial"
        )

    payload = {
        "valuation_summary": {
            "portfolio_id": valuation["portfolio_id"],
            "as_of_date": valuation["as_of_date"].isoformat(),
            "base_currency": valuation["base_currency"],
            "total_portfolio_value": valuation["total_portfolio_value"],
            "total_market_value": valuation["total_market_value"],
            "total_cash_value": valuation["total_cash_value"],
            "total_cost_basis": valuation["total_cost_basis"],
        },
        "holdings": [
            {
                key: _snapshot_json_value(holding.get(key))
                for key in (
                    "holding_id",
                    "company_id",
                    "ticker",
                    "quantity",
                    "currency",
                    "market_price",
                    "market_price_id",
                    "market_price_provider",
                    "market_price_as_of",
                    "market_value",
                    "market_value_base",
                    "total_cost",
                    "total_cost_base",
                    "unrealized_pnl_base",
                    "weight_percent",
                    "market_fx_rate_to_base",
                    "market_fx_rate_as_of",
                    "market_fx_observation_id",
                    "cost_fx_rate_to_base",
                    "cost_fx_rate_as_of",
                    "cost_fx_observation_id",
                )
            }
            for holding in holdings
        ],
        "cash_balances": [
            {key: _snapshot_json_value(value) for key, value in cash.items()}
            for cash in valuation.get("cash_balances", [])
        ],
    }

    if existing_snapshot:
        existing_snapshot.total_market_value = valuation["total_market_value"]
        existing_snapshot.total_cost_basis = valuation["total_cost_basis"]
        existing_snapshot.total_cash = valuation["total_cash_value"]
        existing_snapshot.total_portfolio_value = valuation["total_portfolio_value"]
        existing_snapshot.base_currency = valuation["base_currency"]
        existing_snapshot.calculation_status = calculation_status
        existing_snapshot.holdings_count = len(holdings)
        existing_snapshot.priced_holdings_count = sum(
            holding["market_value_base"] is not None for holding in holdings
        )
        existing_snapshot.missing_price_tickers_json = missing_price_tickers
        existing_snapshot.missing_fx_pairs_json = missing_fx_pairs
        existing_snapshot.payload_json = payload
        snapshot = existing_snapshot
    else:
        snapshot = PortfolioSnapshot(
            portfolio_id=portfolio_id,
            snapshot_date=target_date,
            total_market_value=valuation["total_market_value"],
            total_cost_basis=valuation["total_cost_basis"],
            total_cash=valuation["total_cash_value"],
            total_portfolio_value=valuation["total_portfolio_value"],
            base_currency=valuation["base_currency"],
            calculation_status=calculation_status,
            holdings_count=len(holdings),
            priced_holdings_count=sum(
                holding["market_value_base"] is not None for holding in holdings
            ),
            missing_price_tickers_json=missing_price_tickers,
            missing_fx_pairs_json=missing_fx_pairs,
            payload_json=payload,
        )
        db.add(snapshot)

    db.commit()
    db.refresh(snapshot)
    return snapshot


def calculate_portfolio_analytics(
    db: Session,
    portfolio_id: int,
    as_of_date: date | None = None,
    *,
    user_id: str | None = None,
) -> dict[str, Any]:
    target_date = as_of_date or date.today()

    # 1. Get Base Valuation
    valuation = calculate_portfolio_valuation(
        db,
        portfolio_id,
        target_date,
        user_id=user_id,
    )

    # 2. Cash is already converted and completeness-checked by valuation.
    total_cash_value = valuation["total_cash_value"]

    # 3. Calculate Totals
    total_invested_value = valuation["total_market_value"]
    total_portfolio_value = None
    if total_invested_value is not None and total_cash_value is not None:
        total_portfolio_value = total_invested_value + total_cash_value

    # 4. Fetch Company classifications for exposures
    holdings = valuation["holdings"]
    company_ids = [h["company_id"] for h in holdings if h["company_id"] is not None]

    companies = {}
    if company_ids:
        company_records = db.scalars(select(Company).where(Company.id.in_(company_ids))).all()
        companies = {c.id: c for c in company_records}

    # 5. Calculate Exposures (relative to invested value to ensure they sum to 100% of equities)
    sector_exposure: dict[str, float] = {}
    industry_exposure: dict[str, float] = {}
    country_exposure: dict[str, float] = {}
    currency_exposure: dict[str, float] = {}
    asset_type_exposure: dict[str, float] = {}

    for holding in holdings:
        company = companies.get(holding["company_id"])
        weight = holding["weight_percent"] or 0.0

        sector = company.sector if company and company.sector else "Unknown"
        industry = company.industry if company and company.industry else "Unknown"
        country = company.country if company and company.country else "Unknown"
        asset_type = company.asset_type if company and company.asset_type else "Unknown"
        currency = holding["currency"]

        sector_exposure[sector] = sector_exposure.get(sector, 0.0) + weight
        industry_exposure[industry] = industry_exposure.get(industry, 0.0) + weight
        country_exposure[country] = country_exposure.get(country, 0.0) + weight
        asset_type_exposure[asset_type] = asset_type_exposure.get(asset_type, 0.0) + weight
        currency_exposure[currency] = currency_exposure.get(currency, 0.0) + weight

    # 6. Top Positions & Movers
    top_positions = sorted(holdings, key=lambda x: x["weight_percent"] or 0.0, reverse=True)[:5]

    # Filter out None pnl for gainers/losers
    top_gainers = sorted(
        [holding for holding in holdings if (holding["unrealized_pnl"] or 0) > 0],
        key=lambda holding: holding["unrealized_pnl"],
        reverse=True,
    )[:5]
    top_losers = sorted(
        [holding for holding in holdings if (holding["unrealized_pnl"] or 0) < 0],
        key=lambda holding: holding["unrealized_pnl"],
    )[:5]

    # 7. Concentration & Warnings
    # HHI (Herfindahl-Hirschman Index): Sum of squares of weights (in decimals)
    concentration_score = sum(((h["weight_percent"] or 0.0) / 100.0) ** 2 for h in holdings) if holdings else None

    diversification_warnings = []
    if holdings:
        top_weight = holdings[0]["weight_percent"] or 0.0
        if top_weight > 25.0:
            diversification_warnings.append(f"High concentration: Top position ({holdings[0]['ticker']}) is {top_weight:.1f}% of invested value.")

        if len(holdings) < 5:
            diversification_warnings.append(f"Low diversification: Only {len(holdings)} holdings.")

        if concentration_score is not None and concentration_score > 0.25:
            diversification_warnings.append("High overall portfolio concentration (HHI > 0.25).")

    return {
        "portfolio_id": valuation["portfolio_id"],
        "as_of_date": valuation["as_of_date"],
        "base_currency": valuation["base_currency"],
        "total_portfolio_value": total_portfolio_value,
        "total_cash_value": total_cash_value,
        "total_invested_value": total_invested_value,
        "total_cost_basis": valuation.get("total_cost_basis"),
        "total_unrealized_pnl": valuation["total_unrealized_pnl"],
        "total_unrealized_pnl_percent": valuation["total_unrealized_pnl_percent"],
        "top_positions": top_positions,
        "top_gainers": top_gainers,
        "top_losers": top_losers,
        "sector_exposure": sector_exposure,
        "industry_exposure": industry_exposure,
        "country_exposure": country_exposure,
        "currency_exposure": currency_exposure,
        "asset_type_exposure": asset_type_exposure,
        "concentration_score": concentration_score,
        "diversification_warnings": diversification_warnings,
        "fx_impact": None,
        "opportunity_cost": None,
        "opportunity_cost_percent": None,
        "missing_fx_pairs": valuation.get("missing_fx_pairs", []),
    }
