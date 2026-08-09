from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.api.schemas import (
    AiCitationValidationRequest,
    AiOutputRead,
    AiOutputReviewRequest,
    ApiResponse,
)
from app.db.session import get_db
from app.models.ai import AiOutput
from app.services.ai_citations import evaluate_ai_output, validate_ai_citations


router = APIRouter()


def _owned_output(db: Session, output_id: int, user_id: str) -> AiOutput:
    output = db.scalar(
        select(AiOutput).where(AiOutput.id == output_id, AiOutput.user_id == user_id)
    )
    if output is None:
        raise HTTPException(status_code=404, detail="AI output not found")
    return output


@router.get("/ai-outputs/{output_id}", response_model=ApiResponse[AiOutputRead])
def get_ai_output(
    output_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
) -> ApiResponse[AiOutput]:
    return ApiResponse(data=_owned_output(db, output_id, current_user["id"]))


@router.post(
    "/ai-outputs/{output_id}/citations/validate",
    response_model=ApiResponse[AiOutputRead],
)
def validate_output_citations(
    output_id: int,
    payload: AiCitationValidationRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
) -> ApiResponse[AiOutput]:
    output = _owned_output(db, output_id, current_user["id"])
    validate_ai_citations(db, output, [citation.model_dump() for citation in payload.citations])
    return ApiResponse(data=output)


@router.post("/ai-outputs/{output_id}/evaluate", response_model=ApiResponse[AiOutputRead])
def evaluate_output(
    output_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
) -> ApiResponse[AiOutput]:
    output = _owned_output(db, output_id, current_user["id"])
    output.evaluation_json = evaluate_ai_output(output)
    db.commit()
    db.refresh(output)
    return ApiResponse(data=output)


@router.patch("/ai-outputs/{output_id}/review", response_model=ApiResponse[AiOutputRead])
def review_output(
    output_id: int,
    payload: AiOutputReviewRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
) -> ApiResponse[AiOutput]:
    output = _owned_output(db, output_id, current_user["id"])
    evaluation = evaluate_ai_output(output)
    if payload.status == "approved" and not evaluation["passed"]:
        raise HTTPException(
            status_code=409,
            detail="AI output cannot be approved until execution, citation, and recommendation-language checks pass",
        )
    output.evaluation_json = evaluation
    output.human_review_status = payload.status
    output.review_notes = (payload.notes or "").strip() or None
    output.reviewer_id = current_user["id"]
    output.reviewed_at = datetime.now(UTC)
    db.commit()
    db.refresh(output)
    return ApiResponse(data=output)
