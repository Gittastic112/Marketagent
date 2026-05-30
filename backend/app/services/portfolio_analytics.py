from datetime import date
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Company, PortfolioCashBalance
from app.services.portfolio_valuation import calculate_portfolio_valuation


def calculate_portfolio_analytics(db: Session, portfolio_id: int, as_of_date: date | None = None) -> dict[str, Any]:
    target_date = as_of_date or date.today()
    
    # 1. Get Base Valuation
    valuation = calculate_portfolio_valuation(db, portfolio_id, target_date)
    
    # 2. Get Cash Balance
    cash_record = db.scalar(
        select(PortfolioCashBalance)
        .where(PortfolioCashBalance.portfolio_id == portfolio_id)
        .where(PortfolioCashBalance.as_of_date <= target_date)
        .order_by(PortfolioCashBalance.as_of_date.desc(), PortfolioCashBalance.id.desc())
        .limit(1)
    )
    total_cash_value = float(cash_record.amount) if cash_record else 0.0
    
    # 3. Calculate Totals
    total_invested_value = valuation["total_market_value"]
    total_portfolio_value = None
    if total_invested_value is not None:
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
    holdings_with_pnl = [h for h in holdings if h["unrealized_pnl"] is not None]
    top_gainers = sorted(holdings_with_pnl, key=lambda x: x["unrealized_pnl"], reverse=True)[:5]
    top_losers = sorted(holdings_with_pnl, key=lambda x: x["unrealized_pnl"])[:5]
    
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
    }
