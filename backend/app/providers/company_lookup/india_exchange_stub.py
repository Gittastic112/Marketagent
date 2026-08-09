from app.providers.company_lookup.base import CompanyLookupResult


class IndiaExchangeLookupStub:
    market = "IN"
    source_name = "NSE/BSE"

    def lookup(self, ticker: str, exchange: str | None = None) -> CompanyLookupResult | None:
        return None
