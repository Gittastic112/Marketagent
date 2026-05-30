from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.helpers import create_record, delete_record, get_or_404, has_matching_record, update_record, validate_event_refs
from app.api.schemas import ApiResponse, EventCreate, EventRead, EventUpdate
from app.db.session import get_db
from app.models import Alert, Event


router = APIRouter()


@router.post("/events", response_model=ApiResponse[EventRead], status_code=status.HTTP_201_CREATED)
def create_event(payload: EventCreate, db: Session = Depends(get_db)) -> Event:
    validate_event_refs(db, payload)
    return ApiResponse(data=create_record(db, Event, payload))


@router.get("/events", response_model=ApiResponse[list[EventRead]])
def list_events(db: Session = Depends(get_db)) -> list[Event]:
    return ApiResponse(data=list(db.scalars(select(Event).order_by(Event.id))))


@router.get("/events/{event_id}", response_model=ApiResponse[EventRead])
def get_event(event_id: int, db: Session = Depends(get_db)) -> Event:
    return ApiResponse(data=get_or_404(db, Event, event_id))


@router.patch("/events/{event_id}", response_model=ApiResponse[EventRead])
def update_event(event_id: int, payload: EventUpdate, db: Session = Depends(get_db)) -> Event:
    validate_event_refs(db, payload)
    return ApiResponse(data=update_record(db, get_or_404(db, Event, event_id), payload))


@router.delete("/events/{event_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_event(event_id: int, db: Session = Depends(get_db)) -> None:
    event = get_or_404(db, Event, event_id)
    if has_matching_record(db, select(Alert.id).where(Alert.event_id == event_id)):
        raise HTTPException(
            status_code=409,
            detail="Event cannot be deleted while it has linked alerts. Delete linked alerts first.",
        )
    delete_record(db, event)


from app.api.schemas import EventLinkCreate
from app.models.event import EventCorroboration, EventContradiction

@router.post("/events/{event_id}/corroborations", status_code=status.HTTP_201_CREATED)
def add_corroboration(event_id: int, payload: EventLinkCreate, db: Session = Depends(get_db)):
    get_or_404(db, Event, event_id)
    get_or_404(db, Event, payload.target_event_id)
    link = EventCorroboration(source_event_id=event_id, target_event_id=payload.target_event_id)
    db.add(link)
    db.commit()
    return ApiResponse(data={"message": "Corroboration added"})

@router.delete("/events/{event_id}/corroborations/{target_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_corroboration(event_id: int, target_id: int, db: Session = Depends(get_db)):
    link = db.scalar(select(EventCorroboration).where(
        EventCorroboration.source_event_id == event_id,
        EventCorroboration.target_event_id == target_id
    ))
    if not link:
        raise HTTPException(status_code=404, detail="Corroboration not found")
    db.delete(link)
    db.commit()

@router.post("/events/{event_id}/contradictions", status_code=status.HTTP_201_CREATED)
def add_contradiction(event_id: int, payload: EventLinkCreate, db: Session = Depends(get_db)):
    get_or_404(db, Event, event_id)
    get_or_404(db, Event, payload.target_event_id)
    link = EventContradiction(source_event_id=event_id, target_event_id=payload.target_event_id)
    db.add(link)
    db.commit()
    return ApiResponse(data={"message": "Contradiction added"})

@router.delete("/events/{event_id}/contradictions/{target_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_contradiction(event_id: int, target_id: int, db: Session = Depends(get_db)):
    link = db.scalar(select(EventContradiction).where(
        EventContradiction.source_event_id == event_id,
        EventContradiction.target_event_id == target_id
    ))
    if not link:
        raise HTTPException(status_code=404, detail="Contradiction not found")
    db.delete(link)
    db.commit()
