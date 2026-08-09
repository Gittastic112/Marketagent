from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.schemas import EventEvidenceResolutionCreate, EventEvidenceReferenceCreate
from app.models import Event, EventEvidenceReference, RawDocument


MIN_QUERY_LENGTH = 8
MAX_QUERY_LENGTH = 300
DEFAULT_CONTEXT_CHARS = 180
MAX_CONTEXT_CHARS = 300
DEFAULT_MATCH_LIMIT = 25
MAX_MATCH_LIMIT = 25


@dataclass(frozen=True)
class EvidenceResolutionError(Exception):
    status_code: int
    code: str
    message: str


def _linked_source(db: Session, event_id: int) -> tuple[Event, RawDocument]:
    event = db.get(Event, event_id)
    if event is None:
        raise EvidenceResolutionError(404, "EVIDENCE_RESOLUTION_EVENT_NOT_FOUND", "The event was not found.")
    if event.raw_document_id is None:
        raise EvidenceResolutionError(
            409,
            "EVIDENCE_RESOLUTION_DOCUMENT_MISSING",
            "The event is not linked to a source document.",
        )
    document = db.get(RawDocument, event.raw_document_id)
    if document is None:
        raise EvidenceResolutionError(
            409,
            "EVIDENCE_RESOLUTION_DOCUMENT_MISSING",
            "The event's linked source document no longer exists.",
        )
    if not document.raw_text:
        raise EvidenceResolutionError(
            409,
            "EVIDENCE_RESOLUTION_SOURCE_TEXT_MISSING",
            "The linked source document has no stored source text.",
        )
    return event, document


def _exact_match_starts(source_text: str, query: str, *, limit: int) -> list[int]:
    starts: list[int] = []
    offset = 0
    while len(starts) < limit:
        start = source_text.find(query, offset)
        if start < 0:
            break
        starts.append(start)
        offset = start + len(query)
    return starts


def search_event_evidence(
    db: Session,
    *,
    event_id: int,
    query: str,
    context_chars: int = DEFAULT_CONTEXT_CHARS,
    limit: int = DEFAULT_MATCH_LIMIT,
) -> dict[str, Any]:
    if not query.strip():
        raise EvidenceResolutionError(422, "EVIDENCE_RESOLUTION_QUERY_EMPTY", "Enter non-whitespace source text.")
    event, document = _linked_source(db, event_id)
    source_text = document.raw_text or ""
    bounded_context = min(max(context_chars, 40), MAX_CONTEXT_CHARS)
    bounded_limit = min(max(limit, 1), MAX_MATCH_LIMIT)
    exact_match_count = source_text.count(query)
    starts = _exact_match_starts(source_text, query, limit=bounded_limit)
    existing_reference_count = db.scalar(
        select(func.count(EventEvidenceReference.id)).where(
            EventEvidenceReference.event_id == event.id
        )
    ) or 0

    matches = []
    for occurrence_index, start in enumerate(starts, start=1):
        end = start + len(query)
        matches.append({
            "occurrence_index": occurrence_index,
            "start_char": start,
            "end_char": end,
            "context_before": source_text[max(0, start - bounded_context):start],
            "quote": source_text[start:end],
            "context_after": source_text[end:min(len(source_text), end + bounded_context)],
        })

    return {
        "event_id": event.id,
        "company_id": event.company_id,
        "raw_document_id": document.id,
        "event_title": event.title,
        "document_title": document.title,
        "document_content_hash": document.content_hash,
        "query": query,
        "exact_match_count": exact_match_count,
        "returned_match_count": len(matches),
        "is_truncated": exact_match_count > len(matches),
        "existing_reference_count": existing_reference_count,
        "matches": matches,
        "limitations": [
            "Search is exact and case-sensitive; whitespace and punctuation are not normalized.",
            f"Only {bounded_context} characters of context on each side are returned.",
            f"At most {bounded_limit} occurrences are returned; the full source body is never included.",
        ],
    }


def create_manual_exact_evidence(
    db: Session,
    *,
    event_id: int,
    user_id: str,
    payload: EventEvidenceResolutionCreate,
) -> EventEvidenceReference:
    event = db.scalar(select(Event).where(Event.id == event_id).with_for_update())
    if event is None:
        raise EvidenceResolutionError(404, "EVIDENCE_RESOLUTION_EVENT_NOT_FOUND", "The event was not found.")
    if event.raw_document_id != payload.raw_document_id:
        raise EvidenceResolutionError(
            422,
            "EVIDENCE_RESOLUTION_DOCUMENT_MISMATCH",
            "The selected document is not the event's linked source document.",
        )
    document = db.get(RawDocument, payload.raw_document_id)
    if document is None or not document.raw_text:
        raise EvidenceResolutionError(
            409,
            "EVIDENCE_RESOLUTION_SOURCE_TEXT_MISSING",
            "The linked source text is unavailable.",
        )
    if event.company_id and document.company_id and event.company_id != document.company_id:
        raise EvidenceResolutionError(
            422,
            "EVIDENCE_RESOLUTION_COMPANY_MISMATCH",
            "The linked source document belongs to another company.",
        )
    if document.content_hash != payload.document_content_hash:
        raise EvidenceResolutionError(
            409,
            "EVIDENCE_RESOLUTION_SOURCE_CHANGED",
            "The source document changed after the search. Search again before saving evidence.",
        )
    if payload.end_char > len(document.raw_text):
        raise EvidenceResolutionError(
            422,
            "EVIDENCE_RESOLUTION_SPAN_OUT_OF_BOUNDS",
            "The selected span exceeds the stored source text.",
        )
    if document.raw_text[payload.start_char:payload.end_char] != payload.quote:
        raise EvidenceResolutionError(
            409,
            "EVIDENCE_RESOLUTION_SPAN_CHANGED",
            "The selected quote no longer matches the stored source span.",
        )
    occurrence_starts = _exact_match_starts(
        document.raw_text,
        payload.search_query,
        limit=payload.occurrence_index,
    )
    if (
        len(occurrence_starts) < payload.occurrence_index
        or occurrence_starts[payload.occurrence_index - 1] != payload.start_char
    ):
        raise EvidenceResolutionError(
            409,
            "EVIDENCE_RESOLUTION_OCCURRENCE_CHANGED",
            "The selected occurrence no longer matches the source. Search again before saving evidence.",
        )
    duplicate_id = db.scalar(
        select(EventEvidenceReference.id).where(
            EventEvidenceReference.event_id == event.id,
            EventEvidenceReference.raw_document_id == document.id,
            EventEvidenceReference.locator_type == "text_span",
            EventEvidenceReference.start_char == payload.start_char,
            EventEvidenceReference.end_char == payload.end_char,
        ).limit(1)
    )
    if duplicate_id is not None:
        raise EvidenceResolutionError(
            409,
            "EVIDENCE_RESOLUTION_DUPLICATE",
            "This exact source span is already linked to the event.",
        )

    reference_payload = EventEvidenceReferenceCreate(
        raw_document_id=document.id,
        locator_type="text_span",
        start_char=payload.start_char,
        end_char=payload.end_char,
        quote=payload.quote,
        source_metadata_json={
            "resolution_method": "manual_exact_case_sensitive_search",
            "search_query": payload.search_query,
            "occurrence_index": payload.occurrence_index,
            "validated_content_hash": document.content_hash,
        },
        confidence_label="high",
    )
    reference = EventEvidenceReference(
        event_id=event.id,
        created_by_user_id=user_id,
        origin="manual_exact_resolution",
        **reference_payload.model_dump(),
    )
    db.add(reference)
    db.commit()
    db.refresh(reference)
    return reference
