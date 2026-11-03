from typing import Literal

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.schemas.common import ApiResponse
from app.db.session import get_db
from app.models import Event
from app.models.thesis_note import ThesisNote
from app.services.thesis_evidence_engine import ThesisEvidenceEngine

router = APIRouter(prefix="/thesis", tags=["thesis-evidence"])


class ThesisEvidenceDetectRequest(BaseModel):
    event_id: int = Field(gt=0)


class ThesisEvidenceDetectRead(BaseModel):
    event_id: int
    thesis_id: int
    contradictions: list[int]
    confirmations: list[int]
    claim_type: Literal["Calculation"] = "Calculation"


@router.post(
    "/{thesis_id}/evidence/detect",
    response_model=ApiResponse[ThesisEvidenceDetectRead],
)
def detect_evidence(
    thesis_id: int,
    payload: ThesisEvidenceDetectRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Runs the ThesisEvidenceEngine to detect contradictions and confirmations
    for the given thesis based on recent events.
    """
    thesis = db.scalar(
        select(ThesisNote).where(
            ThesisNote.id == thesis_id,
            ThesisNote.user_id == current_user["id"],
        )
    )
    if thesis is None:
        raise HTTPException(status_code=404, detail="Thesis note not found")
    event = db.get(Event, payload.event_id)
    if event is None:
        raise HTTPException(status_code=404, detail="Event not found")
    if event.company_id != thesis.company_id:
        raise HTTPException(status_code=422, detail="Event and thesis must belong to the same company")

    contradictions = ThesisEvidenceEngine.detect_contradictions(
        db,
        payload.event_id,
        thesis_id,
    )
    confirmations = ThesisEvidenceEngine.detect_confirmations(
        db,
        payload.event_id,
        thesis_id,
    )

    return ApiResponse(
        data=ThesisEvidenceDetectRead(
            event_id=payload.event_id,
            thesis_id=thesis_id,
            contradictions=[impact.id for impact in contradictions],
            confirmations=[impact.id for impact in confirmations],
        ),
        meta={
            "is_mock": False,
            "warnings": [
                "Deterministic candidates use user-authored falsification triggers and require review. "
                "No confirmation is inferred automatically."
            ],
            "confidence": "low",
        },
    )
