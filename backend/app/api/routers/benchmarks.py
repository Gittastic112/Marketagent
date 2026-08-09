from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.services.industry_assumption import IndustryAssumptionService
from app.api.schemas import ApiResponse

router = APIRouter(prefix="/api/valuation/benchmarks", tags=["benchmarks"])

@router.get("/fundamentals", response_model=ApiResponse[dict])
def get_fundamentals(
    industry: str = Query(..., description="Damodaran industry name"),
    country: str = Query(None, description="Country name"),
    db: Session = Depends(get_db)
):
    """
    Returns suggested assumption priors for a given industry and optional country.
    Matches the schema required by the Valuation Agent phase 3 master plan.
    """
    priors = IndustryAssumptionService.get_assumption_priors(db, country=country, industry=industry)

    return ApiResponse(data=priors)
