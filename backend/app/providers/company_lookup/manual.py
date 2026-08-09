from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Company
from app.providers.company_lookup.base import CompanyLookupResult


class ManualCompanyLookupProvider:
    source_name = "local_company"

    def __init__(self, db: Session, market: str):
        self.db = db
        self.market = market

    def lookup(self, ticker: str, exchange: str | None = None) -> CompanyLookupResult | None:
        symbol = ticker.strip().upper()
        market = self.market.strip().upper()
        primary_exchange = exchange.strip().upper() if exchange else None

        query = select(Company).where(
            Company.market == market,
            Company.local_symbol == symbol,
        )
        if primary_exchange is not None:
            query = query.where(Company.primary_exchange == primary_exchange)

        company = self.db.scalar(query.order_by(Company.id).limit(1))
        if company is None:
            return None

        return CompanyLookupResult(
            market=company.market,
            primary_exchange=company.primary_exchange,
            ticker=company.ticker,
            local_symbol=company.local_symbol or company.ticker,
            name=company.name,
            currency=company.currency or ("INR" if company.market == "IN" else "USD"),
            country=company.country or ("India" if company.market == "IN" else "United States"),
            regulatory_id=company.regulatory_id or company.cik,
            regulatory_id_type=company.regulatory_id_type or ("CIK" if company.cik else None),
            cik=company.cik,
            isin=company.isin,
            source=self.source_name,
            warnings=[],
        )
