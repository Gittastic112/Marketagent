from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api.schemas import ApiResponse, AlertGenerationRead, EventExtractionRead
from app.db.session import get_db
from app.services.alert_generation import generate_alerts_from_events
from app.services.event_extraction import extract_events_from_raw_documents


router = APIRouter()


@router.post("/extract/events", response_model=ApiResponse[EventExtractionRead], status_code=status.HTTP_201_CREATED)
def extract_events(db: Session = Depends(get_db)) -> dict[str, int]:
    result = extract_events_from_raw_documents(db)
    return ApiResponse(data={"created": result.created, "skipped_existing": result.skipped_existing})


@router.post("/generate/alerts", response_model=ApiResponse[AlertGenerationRead], status_code=status.HTTP_201_CREATED)
def generate_alerts(db: Session = Depends(get_db)) -> dict[str, int]:
    result = generate_alerts_from_events(db)
    return ApiResponse(data={
        "created": result.created,
        "skipped_existing": result.skipped_existing,
        "skipped_below_threshold": result.skipped_below_threshold,
    })
