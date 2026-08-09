from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.schemas import ApiResponse, IntelligenceReviewItemRead
from app.db.session import get_db
from app.services.intelligence_review import build_intelligence_review_queue


router = APIRouter()


@router.get(
    "/intelligence/review",
    response_model=ApiResponse[list[IntelligenceReviewItemRead]],
)
def get_intelligence_review_queue(
    company_id: int | None = None,
    limit: int = Query(default=100, ge=1, le=250),
    db: Session = Depends(get_db),
) -> ApiResponse[list[dict]]:
    return ApiResponse(
        data=build_intelligence_review_queue(db, company_id=company_id, limit=limit)
    )
