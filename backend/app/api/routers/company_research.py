from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.schemas.common import ApiResponse
from app.db.session import get_db
from app.services.company_research import company_research_profiles
from app.api.dependencies import get_current_user
from app.schemas.price_timeline import PricePinCreate, PricePinRead, PriceTimeline
from app.services.price_timeline import company_timeline, save_pin, thesis_pins

router = APIRouter(tags=["company-research"])


@router.get("/company-research/profiles", response_model=ApiResponse[list[dict]])
def research_profiles(company_id: list[int] = Query(..., min_length=1, max_length=50), db: Session = Depends(get_db)):
    return ApiResponse(data=company_research_profiles(db, list(set(company_id))),
                       meta={"source": "stored_company_catalog_and_annual_business_sections"})


@router.get("/companies/{company_id}/price-timeline", response_model=ApiResponse[PriceTimeline])
def price_timeline(company_id: int, series: str | None = Query(None, pattern=r"^[a-f0-9]{64}$"),
                   through: date | None = None, db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    return ApiResponse(data=company_timeline(db, company_id, user["id"], series, through),
                       meta={"source": "stored_daily_closes_and_dated_sources"})


@router.post("/companies/{company_id}/price-timeline/pins", response_model=ApiResponse[PricePinRead])
def add_price_pin(company_id: int, payload: PricePinCreate, db: Session = Depends(get_db),
                  user: dict = Depends(get_current_user)):
    return ApiResponse(data=save_pin(db, company_id, user["id"], payload))


@router.get("/thesis-notes/{thesis_id}/price-pins", response_model=ApiResponse[list[PricePinRead]])
def list_price_pins(thesis_id: int, db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    return ApiResponse(data=thesis_pins(db, thesis_id, user["id"]))
