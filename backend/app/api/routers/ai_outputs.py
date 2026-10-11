from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.api.schemas import (
    AiCitationValidationRequest,
    AiCitationSuggestionRead,
    AiOutputRead,
    AiOutputReviewRequest,
    ApiMeta,
    ApiResponse,
)
from app.db.session import get_db
from app.models.ai import AiOutput
from app.services.ai_citations import evaluate_ai_output, validate_ai_citations
from app.services.ai_citation_suggestions import suggest_ai_citations


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


@router.get(
    "/ai-outputs/{output_id}/citations/suggestions",
    response_model=ApiResponse[list[AiCitationSuggestionRead]],
)
def suggest_output_citations(
    output_id: int,
    limit_per_source: int = Query(default=3, ge=1, le=5),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
) -> ApiResponse[list[dict]]:
    output = _owned_output(db, output_id, current_user["id"])
    suggestions = suggest_ai_citations(db, output, limit_per_source=limit_per_source)
    unavailable_count = sum(item["status"] != "ready" for item in suggestions)
    warnings = (
        [f"{unavailable_count} cited source(s) have no ready exact-passage candidate."]
        if unavailable_count
        else []
    )
    return ApiResponse(
        data=suggestions,
        meta=ApiMeta(
            source="stored_source_text_lexical_match",
            last_updated=output.created_at,
            is_stale=False,
            is_mock=output.is_mock,
            confidence="medium",
            warnings=warnings,
        ),
    )


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
