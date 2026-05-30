from fastapi import APIRouter, Depends, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.helpers import create_record, delete_record, get_or_404, update_record, validate_thesis_note_refs
from app.api.schemas import (
    ApiResponse,
    ThesisNoteCreate, ThesisNoteRead, ThesisNoteUpdate,
    ThesisAssumptionCreate, ThesisAssumptionRead, ThesisAssumptionUpdate,
    ThesisChangeCreate, ThesisChangeRead
)
from app.db.session import get_db
from app.models import ThesisNote, ThesisAssumption, ThesisChange


router = APIRouter()


@router.post("/thesis-notes", response_model=ApiResponse[ThesisNoteRead], status_code=status.HTTP_201_CREATED)
def create_thesis_note(payload: ThesisNoteCreate, db: Session = Depends(get_db)) -> ThesisNote:
    validate_thesis_note_refs(db, payload)
    return ApiResponse(data=create_record(db, ThesisNote, payload))


@router.get("/thesis-notes", response_model=ApiResponse[list[ThesisNoteRead]])
def list_thesis_notes(db: Session = Depends(get_db)) -> list[ThesisNote]:
    return ApiResponse(data=list(db.scalars(select(ThesisNote).order_by(ThesisNote.id))))


@router.get("/thesis-notes/{thesis_note_id}", response_model=ApiResponse[ThesisNoteRead])
def get_thesis_note(thesis_note_id: int, db: Session = Depends(get_db)) -> ThesisNote:
    return ApiResponse(data=get_or_404(db, ThesisNote, thesis_note_id))


@router.patch("/thesis-notes/{thesis_note_id}", response_model=ApiResponse[ThesisNoteRead])
def update_thesis_note(
    thesis_note_id: int,
    payload: ThesisNoteUpdate,
    db: Session = Depends(get_db),
) -> ThesisNote:
    validate_thesis_note_refs(db, payload)
    return ApiResponse(data=update_record(db, get_or_404(db, ThesisNote, thesis_note_id), payload))


@router.delete("/thesis-notes/{thesis_note_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_thesis_note(thesis_note_id: int, db: Session = Depends(get_db)) -> None:
    delete_record(db, get_or_404(db, ThesisNote, thesis_note_id))


@router.post("/thesis-notes/{thesis_note_id}/assumptions", response_model=ApiResponse[ThesisAssumptionRead], status_code=status.HTTP_201_CREATED)
def create_thesis_assumption(thesis_note_id: int, payload: ThesisAssumptionCreate, db: Session = Depends(get_db)) -> ThesisAssumption:
    get_or_404(db, ThesisNote, thesis_note_id)
    if payload.thesis_note_id != thesis_note_id:
        payload.thesis_note_id = thesis_note_id
    return ApiResponse(data=create_record(db, ThesisAssumption, payload))


@router.patch("/thesis-assumptions/{assumption_id}", response_model=ApiResponse[ThesisAssumptionRead])
def update_thesis_assumption(
    assumption_id: int,
    payload: ThesisAssumptionUpdate,
    db: Session = Depends(get_db),
) -> ThesisAssumption:
    return ApiResponse(data=update_record(db, get_or_404(db, ThesisAssumption, assumption_id), payload))


@router.delete("/thesis-assumptions/{assumption_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_thesis_assumption(assumption_id: int, db: Session = Depends(get_db)) -> None:
    delete_record(db, get_or_404(db, ThesisAssumption, assumption_id))


@router.post("/thesis-notes/{thesis_note_id}/changes", response_model=ApiResponse[ThesisChangeRead], status_code=status.HTTP_201_CREATED)
def create_thesis_change(thesis_note_id: int, payload: ThesisChangeCreate, db: Session = Depends(get_db)) -> ThesisChange:
    thesis = get_or_404(db, ThesisNote, thesis_note_id)
    if payload.thesis_note_id != thesis_note_id:
        payload.thesis_note_id = thesis_note_id
    change = create_record(db, ThesisChange, payload)
    
    # Update drift score
    thesis.thesis_drift_score += payload.drift_score
    db.commit()
    db.refresh(change)
    return ApiResponse(data=change)
