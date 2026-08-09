from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api import schemas
from app.models.country_market_data import CountryMarketContext


SUPPORTED_MARKETS = {"US", "IN"}


def normalize_market(market: str | None) -> str:
    normalized = (market or "").strip().upper()
    if normalized not in SUPPORTED_MARKETS:
        raise ValueError(f"Unsupported market {normalized or '<empty>'}")
    return normalized


def normalize_currency(currency: str | None) -> str:
    normalized = (currency or "").strip().upper()
    if not normalized:
        raise ValueError("Currency is required")
    return normalized


def get_market_context(db: Session, market: str) -> CountryMarketContext | None:
    normalized_market = normalize_market(market)
    return db.scalar(
        select(CountryMarketContext).where(CountryMarketContext.market == normalized_market)
    )


def save_manual_market_context(
    db: Session,
    payload: schemas.CountryMarketContextManualCreate,
) -> CountryMarketContext:
    market = normalize_market(payload.market)
    currency = normalize_currency(payload.currency)
    country = payload.country.strip()
    if not country:
        raise ValueError("Country is required")
    if payload.risk_free_rate is not None and not payload.risk_free_rate_source:
        raise ValueError("Risk-free rate source is required when risk-free rate is provided")

    context = db.scalar(select(CountryMarketContext).where(CountryMarketContext.market == market))
    if context is None:
        context = CountryMarketContext(market=market, country=country, currency=currency)
        db.add(context)

    context.market = market
    context.country = country
    context.currency = currency
    context.risk_free_rate = payload.risk_free_rate
    context.risk_free_rate_source = payload.risk_free_rate_source.strip() if payload.risk_free_rate_source else None
    context.equity_risk_premium = payload.equity_risk_premium
    context.country_risk_premium = payload.country_risk_premium
    context.inflation_rate = payload.inflation_rate
    context.fx_rate_to_usd = payload.fx_rate_to_usd
    context.as_of_date = payload.as_of_date
    context.is_manual = True
    context.notes = payload.notes.strip() if payload.notes else None

    db.commit()
    db.refresh(context)
    return context


def get_risk_free_rate_for_currency(db: Session, currency: str) -> CountryMarketContext | None:
    normalized_currency = normalize_currency(currency)
    return db.scalar(
        select(CountryMarketContext)
        .where(CountryMarketContext.currency == normalized_currency)
        .where(CountryMarketContext.risk_free_rate.is_not(None))
        .where(CountryMarketContext.risk_free_rate_source.is_not(None))
        .order_by(CountryMarketContext.updated_at.desc())
        .limit(1)
    )


def market_context_warnings(context: CountryMarketContext) -> list[str]:
    warnings: list[str] = []
    if context.risk_free_rate is None:
        warnings.append("Risk-free rate is not configured for this market context.")
    if context.risk_free_rate is not None and not context.risk_free_rate_source:
        warnings.append("Risk-free rate exists but has no source.")
    if context.is_manual:
        warnings.append("This market context was entered manually; verify source freshness before using it.")
    return warnings
