from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.providers.company_lookup import (
    CompanyLookupResult,
    IndiaExchangeLookupStub,
    ManualCompanyLookupProvider,
    SecCompanyLookupProvider,
)


SUPPORTED_MARKETS = {"US", "IN"}


def normalize_market(market: str | None) -> str:
    normalized = (market or "US").strip().upper()
    if normalized not in SUPPORTED_MARKETS:
        raise HTTPException(status_code=400, detail=f"Unsupported market {normalized}")
    return normalized


def normalize_exchange(exchange: str | None) -> str | None:
    if exchange is None:
        return None
    normalized = exchange.strip().upper()
    return normalized or None


def lookup_company(
    db: Session,
    ticker: str,
    market: str | None = None,
    exchange: str | None = None,
) -> CompanyLookupResult:
    normalized_market = normalize_market(market)
    normalized_exchange = normalize_exchange(exchange)
    symbol = ticker.strip().upper()

    local_result = ManualCompanyLookupProvider(db=db, market=normalized_market).lookup(
        ticker=symbol,
        exchange=normalized_exchange,
    )
    if local_result is not None:
        return local_result

    if normalized_market == "US":
        sec_result = SecCompanyLookupProvider().lookup(ticker=symbol, exchange=normalized_exchange)
        if sec_result is None:
            raise HTTPException(status_code=404, detail="Company ticker not found in SEC company tickers")
        return sec_result

    IndiaExchangeLookupStub().lookup(ticker=symbol, exchange=normalized_exchange)
    raise HTTPException(
        status_code=404,
        detail="India company lookup provider not implemented; add company manually or configure provider",
    )
