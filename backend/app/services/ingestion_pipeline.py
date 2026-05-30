from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.services.alert_generation import AlertGenerationResult, generate_alerts_from_events
from app.services.event_extraction import EventExtractionResult, extract_events_from_raw_documents


@dataclass(frozen=True)
class PostIngestionPipelineResult:
    event_extraction: EventExtractionResult
    alert_generation: AlertGenerationResult


def run_post_ingestion_pipeline(db: Session) -> PostIngestionPipelineResult:
    event_extraction = extract_events_from_raw_documents(db, limit=None)
    alert_generation = generate_alerts_from_events(db, limit=None)
    return PostIngestionPipelineResult(event_extraction=event_extraction, alert_generation=alert_generation)
