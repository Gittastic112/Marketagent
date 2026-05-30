from dataclasses import dataclass
from difflib import unified_diff

from sqlalchemy import or_, select
from sqlalchemy.orm import Session, selectinload

from app.models import Event, RawDocument
from app.services.scoring import score_event


@dataclass(frozen=True)
class EventExtractionResult:
    created: int
    skipped_existing: int


def extract_events_from_raw_documents(db: Session, limit: int | None = 100) -> EventExtractionResult:
    query = (
        select(RawDocument)
        .options(selectinload(RawDocument.company), selectinload(RawDocument.source), selectinload(RawDocument.events))
        .order_by(RawDocument.id)
    )
    if limit is not None:
        query = query.limit(limit)
    documents = list(db.scalars(query))

    created = 0
    skipped_existing = 0

    for document in documents:
        if document.events:
            skipped_existing += 1
            continue

        db.add(_event_from_document(db, document))
        created += 1

    db.commit()
    return EventExtractionResult(created=created, skipped_existing=skipped_existing)


def _event_from_document(db: Session, document: RawDocument) -> Event:
    filing_change_event = _filing_change_event_from_document(db, document)
    if filing_change_event is not None:
        return filing_change_event

    event = Event(
        company_id=document.company_id,
        raw_document_id=document.id,
        company=document.company,
        raw_document=document,
        event_type=_event_type_for_document(document),
        information_speed="medium",
        title=document.title,
        description=_description_for_document(document),
        event_time=document.published_at,
    )
    score_event(db, event)
    return event


def _filing_change_event_from_document(db: Session, document: RawDocument) -> Event | None:
    if not _is_sec_filing_with_text(document):
        return None
    prior_document = _find_prior_comparable_filing(db, document)
    if prior_document is None or not prior_document.raw_text or prior_document.raw_text == document.raw_text:
        return None

    event = Event(
        company_id=document.company_id,
        raw_document_id=document.id,
        company=document.company,
        raw_document=document,
        event_type="filing_text_change",
        information_speed="slow",
        title=f"Filing text changed: {document.title}",
        description=_filing_change_description(prior_document, document),
        event_time=document.published_at,
    )
    score_event(db, event)
    return event


def _find_prior_comparable_filing(db: Session, document: RawDocument) -> RawDocument | None:
    form_type = _payload_value(document, "form_type")
    if not form_type or document.company_id is None:
        return None

    earlier_timestamp_filter = RawDocument.id < document.id
    if document.published_at is not None:
        earlier_timestamp_filter = or_(RawDocument.published_at < document.published_at, RawDocument.published_at.is_(None))

    return db.scalar(
        select(RawDocument)
        .where(
            RawDocument.id != document.id,
            RawDocument.company_id == document.company_id,
            RawDocument.document_type == document.document_type,
            RawDocument.raw_text.is_not(None),
            RawDocument.raw_payload_json["form_type"].as_string() == str(form_type),
            earlier_timestamp_filter,
        )
        .order_by(RawDocument.published_at.desc().nullslast(), RawDocument.id.desc())
        .limit(1)
    )


def _filing_change_description(prior_document: RawDocument, current_document: RawDocument) -> str:
    diff_lines = list(
        unified_diff(
            _normalized_lines(prior_document.raw_text),
            _normalized_lines(current_document.raw_text),
            fromfile=f"prior_raw_document_{prior_document.id}",
            tofile=f"current_raw_document_{current_document.id}",
            lineterm="",
            n=2,
        )
    )
    diff_preview = "\n".join(diff_lines[:80])
    return "\n".join(
        [
            f"Prior RawDocument #{prior_document.id}: {prior_document.url or 'no URL'}",
            f"Current RawDocument #{current_document.id}: {current_document.url or 'no URL'}",
            "First-pass text diff:",
            diff_preview,
        ]
    )


def _normalized_lines(raw_text: str | None) -> list[str]:
    if not raw_text:
        return []
    return [line.strip() for line in raw_text.splitlines() if line.strip()]


def _event_type_for_document(document: RawDocument) -> str:
    if document.document_type == "sec_filing_metadata":
        return "sec_filing"
    if document.document_type == "rss_item":
        return "rss_news"
    return "raw_document"


def _is_sec_filing_with_text(document: RawDocument) -> bool:
    return document.document_type == "sec_filing_metadata" and bool(document.raw_text)


def _payload_value(document: RawDocument, key: str) -> object | None:
    if not document.raw_payload_json:
        return None
    return document.raw_payload_json.get(key)


def _description_for_document(document: RawDocument) -> str | None:
    if document.raw_text:
        return document.raw_text
    if document.url:
        return f"Source URL: {document.url}"
    return None
