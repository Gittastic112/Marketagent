from fastapi import APIRouter, Depends, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.helpers import create_record, delete_record, get_or_404, update_record
from app.api.schemas import ApiResponse, MarketPriceCreate, MarketPriceRead, MarketPriceUpdate
from app.db.session import get_db
from app.models import MarketPrice


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
