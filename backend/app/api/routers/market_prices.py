from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.errors import PublicApiError
from app.api.helpers import create_record, delete_record, get_or_404, update_record
from app.api.schemas import ApiResponse, MarketPriceCreate, MarketPriceRead, MarketPriceUpdate
from app.db.session import get_db
from app.models import Company, MarketPrice
from app.services.market_data.base import MarketDataProviderError
from app.services.market_data.ingestion import ingest_company_prices
from app.api.dependencies import get_current_user
from app.services.valuation_alert_service import check_price_valuation_divergence


router = APIRouter()


def normalize_market_price_symbols(payload: object) -> ApiResponse[None]:
    if hasattr(payload, "ticker") and getattr(payload, "ticker") is not None:
        setattr(payload, "ticker", getattr(payload, "ticker").upper())
    if hasattr(payload, "currency") and getattr(payload, "currency") is not None:
        setattr(payload, "currency", getattr(payload, "currency").upper())


@router.post("/market-prices", response_model=ApiResponse[MarketPriceRead], status_code=status.HTTP_201_CREATED)
def create_market_price(payload: MarketPriceCreate, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)) -> MarketPrice:
    normalize_market_price_symbols(payload)
    market_price = create_record(db, MarketPrice, payload)
    check_price_valuation_divergence(db, market_price.company_id, user_id=current_user["id"])
    return ApiResponse(data=market_price)


@router.post("/market-prices/fetch-latest", response_model=ApiResponse[MarketPriceRead], status_code=status.HTTP_201_CREATED)
async def fetch_latest_market_price(
    company_id: int, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user),
):
    """Compatibility quote endpoint, using the canonical ingestion service."""
    company = get_or_404(db, Company, company_id)
    try:
        result = await ingest_company_prices(db, company=company, user_id=current_user["id"], include_history=False)
    except MarketDataProviderError as exc:
        raise PublicApiError(status_code=exc.status_code, code=exc.code, message=exc.message,
            retryable=exc.retryable, provider=exc.provider, processing_run_id=exc.processing_run_id) from None
    return ApiResponse(data=result.market_price)


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
    db: Session = Depends(get_db), current_user: dict = Depends(get_current_user),
) -> MarketPrice:
    normalize_market_price_symbols(payload)
    market_price = update_record(db, get_or_404(db, MarketPrice, price_id), payload)
    check_price_valuation_divergence(db, market_price.company_id, user_id=current_user["id"])
    return ApiResponse(data=market_price)


@router.delete("/market-prices/{price_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_market_price(price_id: int, db: Session = Depends(get_db)) -> None:
    delete_record(db, get_or_404(db, MarketPrice, price_id))
