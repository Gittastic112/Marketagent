from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.schemas.common import ApiResponse
from app.db.session import get_db
from app.services.company_research import company_research_profiles

router = APIRouter(tags=["company-research"])


@router.get("/company-research/profiles", response_model=ApiResponse[list[dict]])
def research_profiles(company_id: list[int] = Query(..., min_length=1, max_length=50), db: Session = Depends(get_db)):
    return ApiResponse(data=company_research_profiles(db, list(set(company_id))),
                       meta={"source": "stored_company_catalog_and_annual_business_sections"})
