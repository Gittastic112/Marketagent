from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.services.alert_generation import AlertGenerationResult, generate_alerts_from_events
from app.services.event_extraction import EventExtractionResult, extract_events_from_raw_documents
from app.services.narrative_extraction import NarrativeExtractionResult, extract_narratives_from_events


@dataclass(frozen=True)
class PostIngestionPipelineResult:
    event_extraction: EventExtractionResult
    narrative_extraction: NarrativeExtractionResult
    alert_generation: AlertGenerationResult


def run_post_ingestion_pipeline(db: Session, *, user_id: str) -> PostIngestionPipelineResult:
    event_extraction = extract_events_from_raw_documents(db, limit=None)
    # External AI work requires a separate, versioned privacy acknowledgement.
    narrative_extraction = NarrativeExtractionResult(0, 0, 0, 0)
    alert_generation = generate_alerts_from_events(db, user_id=user_id, limit=None)
    return PostIngestionPipelineResult(
        event_extraction=event_extraction,
        narrative_extraction=narrative_extraction,
        alert_generation=alert_generation,
    )
