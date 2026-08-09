from typing import Protocol

from pydantic import BaseModel, ConfigDict


class CompanyLookupResult(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    market: str
    primary_exchange: str | None = None
    ticker: str
    local_symbol: str
    name: str
    currency: str
    country: str
    regulatory_id: str | None = None
    regulatory_id_type: str | None = None
    cik: str | None = None
    isin: str | None = None
    source: str
    warnings: list[str] = []


class CompanyLookupProvider(Protocol):
    market: str
    source_name: str

    def lookup(self, ticker: str, exchange: str | None = None) -> CompanyLookupResult | None:
        ...
