from dataclasses import dataclass
from difflib import unified_diff
import re

from sqlalchemy import or_, select
from sqlalchemy.orm import Session, selectinload

from app.models import Event, EventEvidenceReference, RawDocument
from app.services.scoring import score_event
from app.services.sec_parsing import strip_html


MAX_EVENT_DESCRIPTION_CHARS = 1_200
MAX_DIFF_LINE_CHARS = 500


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
    events_to_evaluate = []

    for document in documents:
        if document.events:
            skipped_existing += 1
            continue

        event = _event_from_document(db, document)
        reference = _exact_reference_from_document(event, document)
        if reference is not None:
            event.evidence_references.append(reference)
        db.add(event)
        events_to_evaluate.append(event)
        created += 1

    db.commit()

    # Trigger Phase 18 Event Impact Agent for newly created events
    from app.services.market_intelligence_agent import evaluate_event_impact_on_valuation
    from app.models.dcf import DcfAssumptionSet, ValuationModel
    from app.services.valuation_alert_service import generate_valuation_alert

    for event in events_to_evaluate:
        # Check if the event is material/important enough to bother the AI
        if (event.priority_score and event.priority_score > 5) or "earnings" in (event.title or "").lower():
            # Find active assumption set for the company
            latest_assumption_set = db.scalar(
                select(DcfAssumptionSet)
                .join(ValuationModel, ValuationModel.id == DcfAssumptionSet.valuation_model_id)
                .where(ValuationModel.company_id == event.company_id)
                .where(DcfAssumptionSet.scenario == "Base")
                .order_by(DcfAssumptionSet.id.desc())
                .limit(1)
            )

            if latest_assumption_set:
                result = evaluate_event_impact_on_valuation(db, event.id, latest_assumption_set.id)
                if result.get("is_stale"):
                    # Phase 18: Generate a valuation alert if AI decides assumptions are broken
                    generate_valuation_alert(db, event.id, latest_assumption_set.id)

    return EventExtractionResult(created=created, skipped_existing=skipped_existing)


def _exact_reference_from_document(
    event: Event,
    document: RawDocument,
) -> EventEvidenceReference | None:
    if not document.raw_text:
        return None

    quote = event.description or ""
    if event.event_type == "filing_text_change":
        quote = next(
            (
                line[1:]
                for line in quote.splitlines()
                if line.startswith("+") and not line.startswith("+++") and line[1:] in document.raw_text
            ),
            "",
        )
    if not quote:
        return None

    start_char = document.raw_text.find(quote)
    if start_char < 0:
        return None
    return EventEvidenceReference(
        raw_document=document,
        locator_type="text_span",
        start_char=start_char,
        end_char=start_char + len(quote),
        quote=quote,
        confidence_label="high",
        origin="deterministic_extraction",
    )


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
    with db.no_autoflush:
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
    with db.no_autoflush:
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
    if "<" in raw_text and ">" in raw_text:
        cleaned_text = strip_html(raw_text)
        lines = re.split(r"(?<=[.!?])\s+", cleaned_text)
    else:
        lines = raw_text.splitlines()
    return [
        line.strip()[:MAX_DIFF_LINE_CHARS]
        for line in lines
        if line.strip()
    ]


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
    if document.document_type == "sec_filing_metadata":
        form_type = _payload_value(document, "form_type") or "SEC"
        report_date = _payload_value(document, "report_date")
        details = [f"{form_type} filing imported from SEC EDGAR."]
        if report_date:
            details.append(f"Report date: {report_date}.")
        if document.raw_text:
            details.append("Filing text downloaded and stored with the source document.")
        if document.url:
            details.append(f"Source URL: {document.url}")
        return " ".join(details)

    if document.raw_text:
        cleaned_text = strip_html(document.raw_text)
        if len(cleaned_text) > MAX_EVENT_DESCRIPTION_CHARS:
            return f"{cleaned_text[:MAX_EVENT_DESCRIPTION_CHARS].rstrip()}..."
        return cleaned_text
    if document.url:
        return f"Source URL: {document.url}"
    return None
