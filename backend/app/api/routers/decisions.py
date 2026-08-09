from fastapi import APIRouter, Depends, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.helpers import create_record, delete_record, get_or_404, require_reference, update_record
from app.api.schemas import (
    ApiResponse,
    DecisionLogCreate, DecisionLogRead, DecisionLogUpdate
)
from app.api.dependencies import get_current_user
from app.db.session import get_db
from app.models.decision_journal import DecisionLog, OutcomeReview
from app.models.company import Company
from app.services.forecast_learning_engine import ForecastLearningEngine
from pydantic import BaseModel
from typing import Dict, Any

class OutcomeReviewCreate(BaseModel):
    what_happened: str
    wrong_assumption: str | None = None
    information_unavailable_or_misinterpreted: bool = False
    valuation_wrong: bool = False
    thesis_wrong: bool = False
    timing_wrong: bool = False
    sizing_wrong: bool = False


router = APIRouter()


@router.post("/decisions", response_model=ApiResponse[dict], status_code=status.HTTP_201_CREATED)
def create_decision(payload: DecisionLogCreate, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    require_reference(db, Company, payload.company_id, "Company")
    engine = ForecastLearningEngine()

    decision_data = payload.model_dump()
    log = engine.log_decision(db, current_user["id"], payload.company_id, decision_data)

    return ApiResponse(data={"id": log.id, "status": "logged"})

@router.post("/decisions/{decision_id}/review", response_model=ApiResponse[dict], status_code=status.HTTP_201_CREATED)
def review_decision_outcome(decision_id: int, payload: OutcomeReviewCreate, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    # Verify ownership
    get_or_404(db, DecisionLog, decision_id, user_id=current_user["id"])

    engine = ForecastLearningEngine()
    outcome_data = payload.model_dump()
    review = engine.review_outcome(db, decision_id, outcome_data)

    return ApiResponse(data={"id": review.id, "status": "reviewed"})


@router.get("/decisions", response_model=ApiResponse[list[DecisionLogRead]])
def list_decisions(company_id: int | None = None, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)) -> list[DecisionLog]:
    query = select(DecisionLog).where(DecisionLog.user_id == current_user["id"])
    if company_id:
        query = query.where(DecisionLog.company_id == company_id)
    return ApiResponse(data=list(db.scalars(query.order_by(DecisionLog.created_at.desc()))))


@router.get("/decisions/{decision_id}", response_model=ApiResponse[DecisionLogRead])
def get_decision(decision_id: int, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)) -> DecisionLog:
    return ApiResponse(data=get_or_404(db, DecisionLog, decision_id, user_id=current_user["id"]))


@router.patch("/decisions/{decision_id}", response_model=ApiResponse[DecisionLogRead])
def update_decision(
    decision_id: int,
    payload: DecisionLogUpdate,
    db: Session = Depends(get_db), current_user: dict = Depends(get_current_user),
) -> DecisionLog:
    return ApiResponse(data=update_record(db, get_or_404(db, DecisionLog, decision_id, user_id=current_user["id"]), payload))


@router.delete("/decisions/{decision_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_decision(decision_id: int, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)) -> None:
    delete_record(db, get_or_404(db, DecisionLog, decision_id, user_id=current_user["id"]))
