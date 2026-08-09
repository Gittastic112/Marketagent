from collections.abc import Callable
from typing import Any

from app.providers.company_lookup.base import CompanyLookupResult
from app.services.sec_ingestion import lookup_company_profile_for_ticker


class SecCompanyLookupProvider:
    market = "US"
    source_name = "SEC EDGAR"

    def __init__(self, http_get: Callable[..., Any] | None = None):
        self.http_get = http_get

    def lookup(self, ticker: str, exchange: str | None = None) -> CompanyLookupResult | None:
        profile = lookup_company_profile_for_ticker(ticker, http_get=self.http_get)
        if profile is None:
            return None

        return CompanyLookupResult(
            market="US",
            primary_exchange=exchange.upper() if exchange else None,
            ticker=profile.ticker.upper(),
            local_symbol=profile.ticker.upper(),
            name=profile.title,
            currency="USD",
            country="United States",
            regulatory_id=profile.cik,
            regulatory_id_type="CIK",
            cik=profile.cik,
            source=self.source_name,
        )
