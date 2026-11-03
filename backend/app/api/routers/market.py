from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.errors import PublicApiError
from app.api.schemas import ApiResponse, CompanyMarketDataRead, MarketDataIngestionRequest, MarketHistoryPriceRead
from app.db.session import get_db
from app.models.company import Company
from app.models.market_price import CompanyMarketData, MarketPrice
from app.services.market_data.base import MarketDataProviderError
from app.services.market_data.ingestion import ingest_company_prices
from app.api.dependencies import get_current_user

router = APIRouter(prefix="/api/market", tags=["market"])


def _normalize_upper(value: str | None) -> str | None:
    if value is None:
        return None
    stripped = value.strip()
    return stripped.upper() if stripped else None


def _resolve_company_by_identity(db: Session, market: str, ticker: str, exchange: str | None = None) -> Company:
    normalized_market = _normalize_upper(market)
    normalized_ticker = _normalize_upper(ticker)
    normalized_exchange = _normalize_upper(exchange)
    if normalized_market not in {"US", "IN"}:
        raise HTTPException(status_code=400, detail=f"Unsupported market {normalized_market}")
    if not normalized_ticker:
        raise HTTPException(status_code=400, detail="ticker is required")

    query = select(Company).where(
        Company.market == normalized_market,
        Company.local_symbol == normalized_ticker,
    )
    if normalized_exchange is not None:
        query = query.where(Company.primary_exchange == normalized_exchange)

    companies = list(db.scalars(query.order_by(Company.id)))
    if not companies:
        raise HTTPException(status_code=404, detail="Company not found")
    if len(companies) > 1:
        raise HTTPException(status_code=409, detail="Ticker is ambiguous across exchanges. Use exchange.")
    return companies[0]


def _resolve_company_by_legacy_ticker(db: Session, ticker: str) -> Company:
    normalized_ticker = _normalize_upper(ticker)
    companies = list(db.scalars(select(Company).where(Company.ticker == normalized_ticker).order_by(Company.id)))
    if not companies:
        raise HTTPException(status_code=404, detail="Company not found")
    if len(companies) > 1:
        raise HTTPException(status_code=409, detail="Ticker is ambiguous across markets. Use market and exchange.")
    return companies[0]


def _market_data_response(company: Company, market_data: CompanyMarketData | None) -> dict | None:
    if market_data is None:
        return None

    return {
        "market": company.market,
        "exchange": company.primary_exchange,
        "ticker": company.local_symbol or company.ticker,
        "currency": market_data.currency or company.currency,
        "provider_name": market_data.provider_name,
        "provider_symbol": market_data.provider_symbol,
        "current_price": market_data.current_price,
        "change_percent": market_data.change_percent,
        "volume": market_data.volume,
        "market_cap": market_data.market_cap,
        "pe_ratio": market_data.pe_ratio,
        "fifty_two_week_high": market_data.fifty_two_week_high,
        "fifty_two_week_low": market_data.fifty_two_week_low,
        "source_timestamp": market_data.source_timestamp,
        "observed_at": market_data.observed_at,
        "price_type": market_data.price_type,
        "delay_minutes": market_data.delay_minutes,
        "adjustment_state": market_data.adjustment_state,
        "warnings": market_data.warnings,
        "last_updated": market_data.last_updated,
    }


@router.get("/quote", response_model=ApiResponse[CompanyMarketDataRead])
def get_market_quote_for_identity(
    market: str,
    ticker: str,
    exchange: str | None = None,
    db: Session = Depends(get_db),
):
    company = _resolve_company_by_identity(db, market=market, ticker=ticker, exchange=exchange)
    return ApiResponse(data=_market_data_response(company, company.market_data))


@router.get("/quote/{ticker}", response_model=ApiResponse[CompanyMarketDataRead])
def get_market_quote(ticker: str, db: Session = Depends(get_db)):
    company = _resolve_company_by_legacy_ticker(db, ticker)
    return ApiResponse(data=_market_data_response(company, company.market_data))

@router.get("/history/{ticker}", response_model=ApiResponse[list[MarketHistoryPriceRead]])
def get_market_history(ticker: str, range: str = "1y", db: Session = Depends(get_db)):
    company = _resolve_company_by_legacy_ticker(db, ticker)

    query = select(MarketPrice).where(MarketPrice.company_id == company.id)

    # Calculate start date based on range (default 1y)
    start_date = datetime.now(timezone.utc).date() - timedelta(days=365)
    if range == "6m":
        start_date = datetime.now(timezone.utc).date() - timedelta(days=180)
    elif range == "3m":
        start_date = datetime.now(timezone.utc).date() - timedelta(days=90)

    query = query.where(MarketPrice.as_of_date >= start_date).order_by(MarketPrice.as_of_date.asc())

    prices = db.execute(query).scalars().all()

    # Format to match MarketHistoryPriceRead alias date
    # Alias mapping happens in Pydantic automatically with alias_generator or explicit Field alias
    return ApiResponse(data=[MarketHistoryPriceRead.model_validate(p) for p in prices])


@router.post("/ingest", response_model=ApiResponse[dict])
async def ingest_market_data_for_identity(
    payload: MarketDataIngestionRequest, db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    company = _resolve_company_by_identity(db, market=payload.market, ticker=payload.ticker, exchange=payload.exchange)
    return await _ingest_market_data_for_company(company=company, db=db, days=payload.days, user_id=current_user["id"])


@router.post("/ingest/{ticker}", response_model=ApiResponse[dict])
async def ingest_market_data(
    ticker: str, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user),
):
    company = _resolve_company_by_legacy_ticker(db, ticker)
    return await _ingest_market_data_for_company(company=company, db=db, days=365, user_id=current_user["id"])


async def _ingest_market_data_for_company(*, company: Company, db: Session, days: int, user_id: str) -> ApiResponse[dict]:
    try:
        result = await ingest_company_prices(db, company=company, days=days, user_id=user_id)
    except MarketDataProviderError as exc:
        raise PublicApiError(status_code=exc.status_code, code=exc.code, message=exc.message,
            retryable=exc.retryable, provider=exc.provider, processing_run_id=exc.processing_run_id) from None
    return ApiResponse(data={
        "status": "success", "provider": result.provider, "fetched_count": result.fetched_count,
        "created_count": result.created_count, "skipped_duplicate_count": result.skipped_duplicate_count,
        "processing_run_id": result.processing_run_id,
    })
