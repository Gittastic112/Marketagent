from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.errors import PublicApiError
from app.api.helpers import create_record, delete_record, get_or_404, update_record
from app.api.schemas import ApiResponse, MarketPriceCreate, MarketPriceRead, MarketPriceUpdate
from app.db.session import get_db
from app.models import Company, MarketPrice
from app.models.processing_run import ProcessingRun
from app.services.market_data.base import MarketDataProviderError
from app.services.market_data.factory import get_market_data_provider
from app.services.market_data.persistence import persist_quote, request_for_company


router = APIRouter()


def normalize_market_price_symbols(payload: object) -> ApiResponse[None]:
    if hasattr(payload, "ticker") and getattr(payload, "ticker") is not None:
        setattr(payload, "ticker", getattr(payload, "ticker").upper())
    if hasattr(payload, "currency") and getattr(payload, "currency") is not None:
        setattr(payload, "currency", getattr(payload, "currency").upper())


@router.post("/market-prices", response_model=ApiResponse[MarketPriceRead], status_code=status.HTTP_201_CREATED)
def create_market_price(payload: MarketPriceCreate, db: Session = Depends(get_db)) -> MarketPrice:
    normalize_market_price_symbols(payload)
    return ApiResponse(data=create_record(db, MarketPrice, payload))


@router.post("/market-prices/fetch-latest", response_model=ApiResponse[MarketPriceRead], status_code=status.HTTP_201_CREATED)
async def fetch_latest_market_price(company_id: int, db: Session = Depends(get_db)):
    """Compatibility quote endpoint. `/api/market/ingest` is canonical for quote plus history."""
    company = db.get(Company, company_id)
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")

    try:
        provider = get_market_data_provider()
        request = request_for_company(company)
    except MarketDataProviderError as exc:
        raise PublicApiError(
            status_code=exc.status_code,
            code=exc.code,
            message=exc.message,
            retryable=exc.retryable,
            provider=exc.provider,
        ) from exc

    run = ProcessingRun(
        run_type="market_quote_ingestion",
        source_type=provider.provider_name,
        company_id=company.id,
        started_at=datetime.now(timezone.utc),
        status="running",
        metadata_json={"provider": provider.provider_name, "route": "/market-prices/fetch-latest"},
    )
    db.add(run)
    db.commit()

    try:
        quote = await provider.get_quote(request)
        market_price, _, created = persist_quote(db, company=company, quote=quote)
        run.fetched_count = 1
        run.created_count = int(created)
        run.skipped_duplicate_count = int(not created)
        run.status = "completed"
        run.finished_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(market_price)
        return ApiResponse(data=market_price)
    except MarketDataProviderError as exc:
        db.rollback()
        run = db.get(ProcessingRun, run.id)
        run.status = "failed"
        run.error_count = 1
        run.error_details_json = {"code": exc.code, "provider": exc.provider}
        run.finished_at = datetime.now(timezone.utc)
        db.commit()
        raise PublicApiError(
            status_code=exc.status_code,
            code=exc.code,
            message=exc.message,
            retryable=exc.retryable,
            provider=exc.provider,
            processing_run_id=run.id,
        ) from exc
    except Exception as exc:
        db.rollback()
        run = db.get(ProcessingRun, run.id)
        run.status = "failed"
        run.error_count = 1
        run.error_details_json = {
            "code": "MARKET_PRICE_FETCH_FAILED",
            "exception_type": type(exc).__name__,
        }
        run.finished_at = datetime.now(timezone.utc)
        db.commit()
        raise PublicApiError(
            status_code=502,
            code="MARKET_PRICE_FETCH_FAILED",
            message="The market price provider could not return a usable price.",
            retryable=True,
            provider=provider.provider_name,
            processing_run_id=run.id,
        ) from exc


@router.get("/market-prices", response_model=ApiResponse[list[MarketPriceRead]])
def list_market_prices(
    ticker: str | None = None,
    company_id: int | None = None,
    db: Session = Depends(get_db),
) -> list[MarketPrice]:
    query = select(MarketPrice).order_by(MarketPrice.as_of_date.desc(), MarketPrice.id.desc())
    if ticker:
        query = query.where(MarketPrice.ticker == ticker.upper())
    if company_id:
        query = query.where(MarketPrice.company_id == company_id)
    return ApiResponse(data=list(db.scalars(query)))


@router.get("/market-prices/{price_id}", response_model=ApiResponse[MarketPriceRead])
def get_market_price(price_id: int, db: Session = Depends(get_db)) -> MarketPrice:
    return ApiResponse(data=get_or_404(db, MarketPrice, price_id))


@router.patch("/market-prices/{price_id}", response_model=ApiResponse[MarketPriceRead])
def update_market_price(
    price_id: int,
    payload: MarketPriceUpdate,
    db: Session = Depends(get_db),
) -> MarketPrice:
    normalize_market_price_symbols(payload)
    return ApiResponse(data=update_record(db, get_or_404(db, MarketPrice, price_id), payload))


@router.delete("/market-prices/{price_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_market_price(price_id: int, db: Session = Depends(get_db)) -> None:
    delete_record(db, get_or_404(db, MarketPrice, price_id))
