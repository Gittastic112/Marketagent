from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models import Event, RawDocument


@dataclass(frozen=True)
class EventExtractionResult:
    created: int
    skipped_existing: int


def extract_events_from_raw_documents(db: Session, limit: int = 100) -> EventExtractionResult:
    documents = list(
        db.scalars(
            select(RawDocument)
            .options(selectinload(RawDocument.company), selectinload(RawDocument.source), selectinload(RawDocument.events))
            .order_by(RawDocument.id)
            .limit(limit)
        )
    )

    created = 0
    skipped_existing = 0

    for document in documents:
        if document.events:
            skipped_existing += 1
            continue

        db.add(_event_from_document(document))
        created += 1

    db.commit()
    return EventExtractionResult(created=created, skipped_existing=skipped_existing)


def _event_from_document(document: RawDocument) -> Event:
    credibility_score, novelty_score, impact_score, priority_score = _scores_for_document(document)

    return Event(
        company_id=document.company_id,
        raw_document_id=document.id,
        event_type=_event_type_for_document(document),
        information_speed=_speed_for_document(document),
        title=document.title,
        description=_description_for_document(document),
        event_time=document.published_at,
        credibility_score=credibility_score,
        novelty_score=novelty_score,
        impact_score=impact_score,
        priority_score=priority_score,
    )


def _event_type_for_document(document: RawDocument) -> str:
    if document.document_type == "sec_filing_metadata":
        return "sec_filing"
    if document.document_type == "rss_item":
        return "rss_news"
    return "raw_document"


def _speed_for_document(document: RawDocument) -> str:
    if document.document_type == "sec_filing_metadata":
        return "slow"
    if document.document_type == "rss_item":
        return "fast"
    return "medium"


def _scores_for_document(document: RawDocument) -> tuple[int, int, int, int]:
    if document.document_type == "sec_filing_metadata":
        return 95, 70, 75, 80
    if document.document_type == "rss_item":
        credibility = document.source.reliability_score if document.source and document.source.reliability_score else 60
        return credibility, 65, 55, 61
    return 70, 50, 50, 57


def _description_for_document(document: RawDocument) -> str | None:
    if document.raw_text:
        return document.raw_text
    if document.url:
        return f"Source URL: {document.url}"
    return None
