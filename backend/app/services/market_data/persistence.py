from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.company import Company
from app.models.market_price import CompanyMarketData, MarketPrice
from app.services.market_data.base import (
    MarketDataProviderError,
    MarketDataRequest,
    MarketHistoryResult,
    MarketQuoteResult,
)


def request_for_company(company: Company) -> MarketDataRequest:
    ticker = company.local_symbol or company.ticker
    if not ticker:
        raise MarketDataProviderError(
            code="MARKET_SYMBOL_MISSING",
            message="The company has no market symbol configured.",
            provider="internal",
            status_code=422,
            retryable=False,
        )
    if not company.market:
        raise MarketDataProviderError(
            code="MARKET_IDENTITY_MISSING",
            message="The company has no market configured.",
            provider="internal",
            status_code=422,
            retryable=False,
        )
    return MarketDataRequest(
        market=company.market,
        exchange=company.primary_exchange,
        ticker=ticker,
        currency=company.currency,
    )


def _validate_identity(
    company: Company,
    *,
    provider: str,
    ticker: str,
    market: str,
    exchange: str | None,
    currency: str,
) -> None:
    expected_market = (company.market or "").upper()
    expected_exchange = (company.primary_exchange or "").upper()
    expected_currency = (company.currency or "").upper()
    expected_ticker = (company.local_symbol or company.ticker or "").upper()
    if expected_ticker and ticker.upper() != expected_ticker:
        raise MarketDataProviderError(
            code="PROVIDER_IDENTITY_MISMATCH",
            message="The provider returned a different security than the company identity.",
            provider=provider, status_code=502, retryable=False,
        )
    if expected_market and market.upper() != expected_market:
        raise MarketDataProviderError(
            code="PROVIDER_IDENTITY_MISMATCH",
            message="The provider returned a different market than the company identity.",
            provider=provider,
            status_code=502,
            retryable=False,
        )
    if expected_exchange and exchange and exchange.upper() != expected_exchange:
        raise MarketDataProviderError(
            code="PROVIDER_IDENTITY_MISMATCH",
            message="The provider returned a different exchange than the company identity.",
            provider=provider,
            status_code=502,
            retryable=False,
        )
    if expected_currency and currency.upper() != expected_currency:
        raise MarketDataProviderError(
            code="PROVIDER_CURRENCY_MISMATCH",
            message="The provider returned a different currency than the company identity.",
            provider=provider,
            status_code=502,
            retryable=False,
        )


def persist_quote(
    db: Session,
    *,
    company: Company,
    quote: MarketQuoteResult,
) -> tuple[MarketPrice, CompanyMarketData, bool]:
    _validate_identity(
        company,
        provider=quote.provider_name,
        ticker=quote.ticker,
        market=quote.market,
        exchange=quote.exchange,
        currency=quote.currency,
    )
    as_of_date = (quote.source_timestamp or quote.observed_at).date()
    market_price = db.scalar(
        select(MarketPrice).where(
            MarketPrice.company_id == company.id,
            MarketPrice.as_of_date == as_of_date,
            MarketPrice.provider_name == quote.provider_name,
        )
    )
    market_price_created = market_price is None
    if market_price is None:
        market_price = MarketPrice(company_id=company.id, ticker=company.local_symbol or company.ticker)
        db.add(market_price)

    market_price.ticker = company.local_symbol or company.ticker
    market_price.price = quote.current_price
    market_price.currency = quote.currency.upper()
    market_price.as_of_date = as_of_date
    market_price.provider_name = quote.provider_name
    market_price.provider_symbol = quote.provider_symbol
    market_price.market = quote.market.upper()
    market_price.exchange = quote.exchange.upper() if quote.exchange else None
    market_price.source_timestamp = quote.source_timestamp
    market_price.observed_at = quote.observed_at
    market_price.price_type = quote.price_type
    market_price.delay_minutes = quote.delay_minutes
    market_price.adjustment_state = quote.adjustment_state
    market_price.warnings_json = list(quote.warnings)

    market_data = company.market_data
    if market_data is None:
        market_data = CompanyMarketData(company_id=company.id)
        db.add(market_data)
    market_data.current_price = quote.current_price
    market_data.change_percent = quote.change_percent
    market_data.volume = quote.volume
    market_data.market_cap = quote.market_cap
    market_data.pe_ratio = quote.pe_ratio
    market_data.fifty_two_week_high = quote.fifty_two_week_high
    market_data.fifty_two_week_low = quote.fifty_two_week_low
    market_data.currency = quote.currency.upper()
    market_data.provider_name = quote.provider_name
    market_data.provider_symbol = quote.provider_symbol
    market_data.source_timestamp = quote.source_timestamp
    market_data.observed_at = quote.observed_at
    market_data.price_type = quote.price_type
    market_data.delay_minutes = quote.delay_minutes
    market_data.adjustment_state = quote.adjustment_state
    market_data.warnings_json = list(quote.warnings)
    market_data.last_updated = quote.observed_at
    return market_price, market_data, market_price_created


def persist_history_point(
    db: Session,
    *,
    company: Company,
    point: MarketHistoryResult,
) -> tuple[MarketPrice, bool]:
    _validate_identity(
        company,
        provider=point.provider_name,
        ticker=point.ticker,
        market=point.market,
        exchange=point.exchange,
        currency=point.currency,
    )
    market_price = db.scalar(
        select(MarketPrice).where(
            MarketPrice.company_id == company.id,
            MarketPrice.as_of_date == point.date,
            MarketPrice.provider_name == point.provider_name,
        )
    )
    created = market_price is None
    if market_price is None:
        market_price = MarketPrice(company_id=company.id, ticker=company.local_symbol or company.ticker)
        db.add(market_price)

    market_price.ticker = company.local_symbol or company.ticker
    market_price.price = point.close_price
    market_price.currency = point.currency.upper()
    market_price.as_of_date = point.date
    market_price.provider_name = point.provider_name
    market_price.provider_symbol = point.provider_symbol
    market_price.market = point.market.upper()
    market_price.exchange = point.exchange.upper() if point.exchange else None
    market_price.source_timestamp = None
    market_price.observed_at = point.observed_at
    market_price.price_type = point.price_type
    market_price.delay_minutes = None
    market_price.adjustment_state = point.adjustment_state
    market_price.warnings_json = list(point.warnings)
    return market_price, created
