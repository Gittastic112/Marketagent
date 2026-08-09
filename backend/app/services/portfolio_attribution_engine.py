from datetime import date
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Company, Portfolio, PortfolioTransaction
from app.services.portfolio_valuation import calculate_portfolio_valuation


def _empty_activity() -> dict[str, float]:
    return {
        "purchases": 0.0,
        "sales": 0.0,
        "dividends": 0.0,
        "deposits": 0.0,
        "withdrawals": 0.0,
        "fees": 0.0,
        "taxes": 0.0,
        "net_position_cash_flow": 0.0,
        "net_external_cash_flow": 0.0,
    }


class PortfolioAttributionEngine:
    """Build an honest portfolio activity and unrealized-change bridge.

    This is intentionally partial until point-in-time security prices,
    historical FX rates, and a selected benchmark series are persisted.
    Transaction activity is never converted or summed across currencies.
    """

    @staticmethod
    def decompose_performance(
        db: Session,
        portfolio_id: int,
        as_of_date: date | None = None,
    ) -> dict[str, Any]:
        target_date = as_of_date or date.today()
        portfolio = db.scalar(select(Portfolio).where(Portfolio.id == portfolio_id))
        if portfolio is None:
            raise ValueError(f"Portfolio {portfolio_id} not found")

        valuation = calculate_portfolio_valuation(db, portfolio_id, target_date)
        holdings = valuation.get("holdings", [])
        transactions = db.scalars(
            select(PortfolioTransaction)
            .where(PortfolioTransaction.portfolio_id == portfolio_id)
            .where(PortfolioTransaction.transaction_date <= target_date)
            .order_by(PortfolioTransaction.transaction_date, PortfolioTransaction.id)
        ).all()

        activity_by_currency: dict[str, dict[str, float]] = {}
        for transaction in transactions:
            currency = (transaction.currency or portfolio.base_currency).upper()
            activity = activity_by_currency.setdefault(currency, _empty_activity())
            quantity = float(transaction.quantity)
            price = float(transaction.price)
            explicit_fees = float(transaction.fees)
            gross_value = quantity * price

            activity["fees"] += explicit_fees
            if transaction.transaction_type == "buy":
                activity["purchases"] += gross_value
            elif transaction.transaction_type == "sell":
                activity["sales"] += gross_value
            elif transaction.transaction_type == "dividend":
                activity["dividends"] += gross_value
            elif transaction.transaction_type == "deposit":
                activity["deposits"] += quantity
            elif transaction.transaction_type == "withdrawal":
                activity["withdrawals"] += quantity
            elif transaction.transaction_type == "fee":
                activity["fees"] += quantity
            elif transaction.transaction_type == "tax":
                activity["taxes"] += quantity

        for activity in activity_by_currency.values():
            activity["net_position_cash_flow"] = (
                activity["sales"] - activity["purchases"]
            )
            activity["net_external_cash_flow"] = (
                activity["deposits"] - activity["withdrawals"]
            )

        holding_currencies = {
            (holding.get("currency") or portfolio.base_currency).upper()
            for holding in holdings
        }
        all_holdings_in_base_currency = not holding_currencies or holding_currencies == {
            portfolio.base_currency.upper()
        }
        total_unrealized_pnl = valuation.get("total_unrealized_pnl")
        price_movement = (
            total_unrealized_pnl
            if all_holdings_in_base_currency and total_unrealized_pnl is not None
            else None
        )
        if price_movement is None:
            total_unrealized_pnl = None

        warnings = [
            "Historical FX rates are not stored, so FX impact is not available.",
            "Opportunity cost is not available because no benchmark series is configured.",
        ]
        if price_movement is not None:
            warnings.append(
                "Price movement is unrealized change since average cost, not time-period performance attribution."
            )
        elif holdings and not all_holdings_in_base_currency:
            warnings.append(
                "Aggregate price movement is unavailable because one or more holdings are not in the portfolio base currency."
            )
        elif holdings:
            warnings.append(
                "Aggregate price movement is unavailable because one or more active holdings lack a usable market price."
            )
        if any(currency != portfolio.base_currency.upper() for currency in activity_by_currency):
            warnings.append(
                "Transaction activity is reported separately by currency and is not converted into the portfolio base currency."
            )

        company_ids = {
            holding["company_id"]
            for holding in holdings
            if holding.get("company_id") is not None
        }
        companies: dict[int, Company] = {}
        if company_ids:
            records = db.scalars(select(Company).where(Company.id.in_(company_ids))).all()
            companies = {company.id: company for company in records}

        sector_attribution: dict[str, float] = {}
        geography_attribution: dict[str, float] = {}
        asset_type_attribution: dict[str, float] = {}
        if all_holdings_in_base_currency and all(
            holding.get("weight_percent") is not None for holding in holdings
        ):
            for holding in holdings:
                company = companies.get(holding.get("company_id"))
                weight = float(holding["weight_percent"])
                sector = company.sector if company and company.sector else "Unknown"
                country = company.country if company and company.country else "Unknown"
                asset_type = company.asset_type if company and company.asset_type else "Unknown"
                sector_attribution[sector] = sector_attribution.get(sector, 0.0) + weight
                geography_attribution[country] = geography_attribution.get(country, 0.0) + weight
                asset_type_attribution[asset_type] = (
                    asset_type_attribution.get(asset_type, 0.0) + weight
                )

        status = "partial" if holdings or transactions else "not_available"
        return {
            "as_of_date": target_date,
            "base_currency": portfolio.base_currency,
            "calculation_status": status,
            "total_unrealized_pnl": total_unrealized_pnl,
            "components": {
                "price_movement": price_movement,
                "fx_impact": None,
            },
            "opportunity_cost": None,
            "activity_by_currency": activity_by_currency,
            "attribution_by_sector": sector_attribution,
            "attribution_by_geography": geography_attribution,
            "attribution_by_asset_type": asset_type_attribution,
            "warnings": warnings,
        }
