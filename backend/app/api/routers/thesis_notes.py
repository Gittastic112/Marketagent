from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.helpers import create_record, delete_record, get_or_404, update_record, validate_thesis_note_refs
from app.api.schemas import (
    ApiResponse,
    ThesisNoteCreate, ThesisNoteRead, ThesisNoteUpdate,
    ThesisAssumptionCreate, ThesisAssumptionRead, ThesisAssumptionUpdate,
    ThesisChangeCreate, ThesisChangeRead
)
import app.api.schemas as schemas
from app.api.dependencies import get_current_user
from app.db.session import get_db
from app.models import ThesisNote, ThesisAssumption, ThesisChange
from app.models.thesis_note import EventThesisImpact


router = APIRouter()


def get_owned_thesis_assumption(
    db: Session,
    assumption_id: int,
    user_id: str,
) -> ThesisAssumption:
    assumption = db.scalar(
        select(ThesisAssumption)
        .join(ThesisNote, ThesisAssumption.thesis_note_id == ThesisNote.id)
        .where(
            ThesisAssumption.id == assumption_id,
            ThesisNote.user_id == user_id,
        )
    )
    if assumption is None:
        raise HTTPException(status_code=404, detail="Thesis assumption not found")
    return assumption


def get_owned_thesis_impact(db: Session, impact_id: int, user_id: str) -> EventThesisImpact:
    impact = db.scalar(
        select(EventThesisImpact)
        .join(ThesisAssumption, EventThesisImpact.thesis_assumption_id == ThesisAssumption.id)
        .join(ThesisNote, ThesisAssumption.thesis_note_id == ThesisNote.id)
        .where(
            EventThesisImpact.id == impact_id,
            ThesisNote.user_id == user_id,
        )
    )
    if impact is None:
        raise HTTPException(status_code=404, detail="Thesis impact not found")
    return impact


@router.post("/thesis-notes", response_model=ApiResponse[ThesisNoteRead], status_code=status.HTTP_201_CREATED)
def create_thesis_note(payload: ThesisNoteCreate, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)) -> ThesisNote:
    validate_thesis_note_refs(db, payload)
    return ApiResponse(data=create_record(db, ThesisNote, payload, user_id=current_user["id"]))


@router.get("/thesis-notes", response_model=ApiResponse[list[ThesisNoteRead]])
def list_thesis_notes(db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)) -> list[ThesisNote]:
    return ApiResponse(data=list(db.scalars(select(ThesisNote).where(ThesisNote.user_id == current_user["id"]).order_by(ThesisNote.id))))


@router.get("/thesis-notes/{thesis_note_id}", response_model=ApiResponse[ThesisNoteRead])
def get_thesis_note(thesis_note_id: int, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)) -> ThesisNote:
    return ApiResponse(data=get_or_404(db, ThesisNote, thesis_note_id, user_id=current_user["id"]))


@router.patch("/thesis-notes/{thesis_note_id}", response_model=ApiResponse[ThesisNoteRead])
def update_thesis_note(
    thesis_note_id: int,
    payload: ThesisNoteUpdate,
    db: Session = Depends(get_db), current_user: dict = Depends(get_current_user),
) -> ThesisNote:
    validate_thesis_note_refs(db, payload)
    return ApiResponse(data=update_record(db, get_or_404(db, ThesisNote, thesis_note_id, user_id=current_user["id"]), payload))


@router.delete("/thesis-notes/{thesis_note_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_thesis_note(thesis_note_id: int, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)) -> None:
    delete_record(db, get_or_404(db, ThesisNote, thesis_note_id, user_id=current_user["id"]))


@router.post("/thesis-notes/{thesis_note_id}/assumptions", response_model=ApiResponse[ThesisAssumptionRead], status_code=status.HTTP_201_CREATED)
def create_thesis_assumption(thesis_note_id: int, payload: ThesisAssumptionCreate, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)) -> ThesisAssumption:
    get_or_404(db, ThesisNote, thesis_note_id, user_id=current_user["id"])
    if payload.thesis_note_id != thesis_note_id:
        payload.thesis_note_id = thesis_note_id
    return ApiResponse(data=create_record(db, ThesisAssumption, payload))


@router.patch("/thesis-assumptions/{assumption_id}", response_model=ApiResponse[ThesisAssumptionRead])
def update_thesis_assumption(
    assumption_id: int,
    payload: ThesisAssumptionUpdate,
    db: Session = Depends(get_db), current_user: dict = Depends(get_current_user),
) -> ThesisAssumption:
    assumption = get_owned_thesis_assumption(db, assumption_id, current_user["id"])
    return ApiResponse(data=update_record(db, assumption, payload))


@router.delete("/thesis-assumptions/{assumption_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_thesis_assumption(assumption_id: int, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)) -> None:
    delete_record(db, get_owned_thesis_assumption(db, assumption_id, current_user["id"]))


@router.get("/thesis-assumptions/{assumption_id}/impacts", response_model=ApiResponse[list[schemas.EventThesisImpactRead]])
def list_thesis_impacts(assumption_id: int, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    assumption = get_owned_thesis_assumption(db, assumption_id, current_user["id"])
    return ApiResponse(data=assumption.impacts)

@router.post("/thesis-assumptions/{assumption_id}/impacts", response_model=ApiResponse[schemas.EventThesisImpactRead], status_code=status.HTTP_201_CREATED)
def create_thesis_impact(assumption_id: int, payload: schemas.EventThesisImpactCreate, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    assumption = get_owned_thesis_assumption(db, assumption_id, current_user["id"])
    if payload.thesis_assumption_id != assumption_id:
        payload.thesis_assumption_id = assumption_id

    impact = EventThesisImpact(**payload.model_dump())
    db.add(impact)
    db.commit()
    db.refresh(impact)
    return ApiResponse(data=impact)

@router.delete("/thesis-impacts/{impact_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_thesis_impact(impact_id: int, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)) -> None:
    delete_record(db, get_owned_thesis_impact(db, impact_id, current_user["id"]))


@router.post("/thesis-notes/{thesis_note_id}/changes", response_model=ApiResponse[ThesisChangeRead], status_code=status.HTTP_201_CREATED)
def create_thesis_change(thesis_note_id: int, payload: ThesisChangeCreate, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)) -> ThesisChange:
    thesis = get_or_404(db, ThesisNote, thesis_note_id, user_id=current_user["id"])
    if payload.thesis_note_id != thesis_note_id:
        payload.thesis_note_id = thesis_note_id
    change = create_record(db, ThesisChange, payload)

    # Update drift score
    thesis.thesis_drift_score += payload.drift_score
    db.commit()
    db.refresh(change)
    return ApiResponse(data=change)
