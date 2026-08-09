import re
from collections.abc import Sequence
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import func, literal, or_, select
from sqlalchemy.orm import Session, noload, selectinload

from app.models import Alert, Event, EventEvidenceReference, RawDocument, ThesisNote, ValuationModel
from app.models.decision_journal import DecisionLog


SEARCH_RESULT_TYPES = frozenset({"document", "event", "alert", "thesis", "decision", "valuation"})


def _first_term(query: str) -> str | None:
    terms = re.findall(r"[A-Za-z0-9][A-Za-z0-9._%-]{1,}", query)
    return terms[0] if terms else None


def _text_locator(text: str | None, query: str) -> tuple[str | None, dict[str, Any] | None]:
    if not text:
        return None, None
    term = _first_term(query)
    if not term:
        return text[:240], None
    match = re.search(re.escape(term), text, re.IGNORECASE)
    if not match:
        return text[:240], None
    start = max(0, match.start() - 100)
    end = min(len(text), match.end() + 140)
    return text[start:end].strip(), {
        "type": "text_span",
        "start_char": match.start(),
        "end_char": match.end(),
        "quote": text[match.start():match.end()],
    }


def _search_expression(columns: Sequence[Any]):
    expression = func.coalesce(columns[0], "")
    for column in columns[1:]:
        expression = expression + literal(" ") + func.coalesce(column, "")
    return expression


def _ranked_rows(
    db: Session,
    model,
    query: str,
    *,
    columns: Sequence[Any],
    base_rank: float,
    filters: Sequence[Any] = (),
    options: Sequence[Any] = (),
    limit: int,
):
    rank = literal(base_rank)
    statement = select(model, rank.label("rank")).options(*options)
    if db.bind is not None and db.bind.dialect.name == "postgresql":
        vector = func.to_tsvector("english", _search_expression(columns))
        ts_query = func.websearch_to_tsquery("english", query)
        rank = literal(base_rank) + func.ts_rank_cd(vector, ts_query)
        statement = select(model, rank.label("rank")).options(*options).where(vector.op("@@")(ts_query))
    else:
        pattern = f"%{query}%"
        statement = statement.where(or_(*(column.ilike(pattern) for column in columns)))
    if filters:
        statement = statement.where(*filters)
    return db.execute(statement.order_by(rank.desc(), model.id.desc()).limit(limit)).all()


def _excerpt(query: str, *values: str | None) -> str | None:
    text = " ".join(value.strip() for value in values if value and value.strip())
    return _text_locator(text, query)[0] if text else None


def _timestamp_value(value: datetime | None) -> float:
    if value is None:
        return 0
    normalized = value.replace(tzinfo=UTC) if value.tzinfo is None else value.astimezone(UTC)
    return normalized.timestamp()


def search_evidence(
    db: Session,
    query: str,
    *,
    user_id: str,
    company_id: int | None = None,
    result_type: str | None = None,
    limit: int = 20,
) -> list[dict[str, Any]]:
    requested_types = {result_type} if result_type else set(SEARCH_RESULT_TYPES)
    results: list[dict[str, Any]] = []
    company_filter = [] if company_id is None else [RawDocument.company_id == company_id]
    document_rows = _ranked_rows(
        db,
        RawDocument,
        query,
        columns=(RawDocument.title, RawDocument.raw_text),
        base_rank=1.0,
        filters=company_filter,
        options=(noload("*"), selectinload(RawDocument.source).options(noload("*"))),
        limit=limit,
    ) if "document" in requested_types else []
    for document, rank in document_rows:
        excerpt, locator = _text_locator(document.raw_text, query)
        results.append({
            "result_type": "document",
            "record_id": document.id,
            "company_id": document.company_id,
            "title": document.title,
            "excerpt": excerpt,
            "rank": float(rank),
            "claim_type": "Fact",
            "source_name": document.source.name if document.source else None,
            "source_timestamp": document.published_at or document.ingested_at,
            "href": f"/documents/{document.id}/sections",
            "locator": locator,
        })

    event_filter = [] if company_id is None else [Event.company_id == company_id]
    event_rows = _ranked_rows(
        db,
        Event,
        query,
        columns=(Event.title, Event.description),
        base_rank=0.9,
        filters=event_filter,
        options=(
            noload("*"),
            selectinload(Event.evidence_references).options(
                noload("*"),
                selectinload(EventEvidenceReference.raw_document).options(
                    noload("*"),
                    selectinload(RawDocument.source).options(noload("*")),
                ),
            ),
            selectinload(Event.raw_document).options(
                noload("*"),
                selectinload(RawDocument.source).options(noload("*")),
            ),
        ),
        limit=limit,
    ) if "event" in requested_types else []
    for event, rank in event_rows:
        reference = next(
            (item for item in event.evidence_references if item.locator_type in {"text_span", "pdf_region"}),
            None,
        )
        document = reference.raw_document if reference else event.raw_document
        results.append({
            "result_type": "event",
            "record_id": event.id,
            "company_id": event.company_id,
            "title": event.title,
            "excerpt": reference.quote if reference and reference.quote else event.description,
            "rank": float(rank),
            "claim_type": "Source Summary",
            "source_name": document.source.name if document and document.source else None,
            "source_timestamp": event.event_time or event.created_at,
            "href": (
                f"/documents/{document.id}/sections?evidence_reference={reference.id}"
                if document and reference
                else f"/events?event_id={event.id}"
            ),
            "locator": (
                {
                    "type": reference.locator_type,
                    "source_page": reference.source_page,
                    "source_section": reference.source_section,
                    "start_char": reference.start_char,
                    "end_char": reference.end_char,
                    "quote": reference.quote,
                }
                if reference
                else None
            ),
        })

    thesis_filters = [ThesisNote.user_id == user_id]
    if company_id is not None:
        thesis_filters.append(ThesisNote.company_id == company_id)
    thesis_rows = _ranked_rows(
        db,
        ThesisNote,
        query,
        columns=(ThesisNote.title, ThesisNote.thesis_text),
        base_rank=0.8,
        filters=thesis_filters,
        options=(noload("*"),),
        limit=limit,
    ) if "thesis" in requested_types else []
    for thesis, rank in thesis_rows:
        results.append({
            "result_type": "thesis",
            "record_id": thesis.id,
            "company_id": thesis.company_id,
            "title": thesis.title,
            "excerpt": _excerpt(query, thesis.thesis_text),
            "rank": float(rank),
            "claim_type": "User Assumption",
            "source_name": "User thesis",
            "source_timestamp": thesis.updated_at or thesis.created_at,
            "href": f"/thesis-notes/{thesis.id}",
            "locator": None,
        })

    alert_filters = [Alert.user_id == user_id]
    if company_id is not None:
        alert_filters.append(Alert.company_id == company_id)
    alert_rows = _ranked_rows(
        db,
        Alert,
        query,
        columns=(Alert.title, Alert.summary, Alert.what_changed, Alert.why_it_matters, Alert.evidence),
        base_rank=0.85,
        filters=alert_filters,
        options=(noload("*"),),
        limit=limit,
    ) if "alert" in requested_types else []
    for alert, rank in alert_rows:
        is_manual = alert.alert_type == "manual"
        results.append({
            "result_type": "alert",
            "record_id": alert.id,
            "company_id": alert.company_id,
            "title": alert.title,
            "excerpt": _excerpt(query, alert.summary, alert.what_changed, alert.why_it_matters, alert.evidence),
            "rank": float(rank),
            "claim_type": "User Assumption" if is_manual else "Source Summary",
            "source_name": "User alert" if is_manual else "Owned alert queue",
            "source_timestamp": alert.created_at,
            "href": f"/alerts/{alert.id}",
            "locator": None,
        })

    decision_filters = [DecisionLog.user_id == user_id]
    if company_id is not None:
        decision_filters.append(DecisionLog.company_id == company_id)
    decision_rows = _ranked_rows(
        db,
        DecisionLog,
        query,
        columns=(DecisionLog.decision_type, DecisionLog.rationale, DecisionLog.alternatives_considered),
        base_rank=0.75,
        filters=decision_filters,
        options=(noload("*"),),
        limit=limit,
    ) if "decision" in requested_types else []
    for decision, rank in decision_rows:
        results.append({
            "result_type": "decision",
            "record_id": decision.id,
            "company_id": decision.company_id,
            "title": f"{decision.decision_type} decision",
            "excerpt": _excerpt(query, decision.rationale, decision.alternatives_considered),
            "rank": float(rank),
            "claim_type": "User Assumption",
            "source_name": "Decision journal",
            "source_timestamp": decision.updated_at or decision.created_at,
            "href": f"/companies/{decision.company_id}/decisions?decision_id={decision.id}",
            "locator": None,
        })

    valuation_filters = [ValuationModel.user_id == user_id]
    if company_id is not None:
        valuation_filters.append(ValuationModel.company_id == company_id)
    valuation_rows = _ranked_rows(
        db,
        ValuationModel,
        query,
        columns=(ValuationModel.name, ValuationModel.description),
        base_rank=0.7,
        filters=valuation_filters,
        options=(noload("*"),),
        limit=limit,
    ) if "valuation" in requested_types else []
    for valuation, rank in valuation_rows:
        results.append({
            "result_type": "valuation",
            "record_id": valuation.id,
            "company_id": valuation.company_id,
            "title": valuation.name,
            "excerpt": _excerpt(query, valuation.description),
            "rank": float(rank),
            "claim_type": "User Assumption",
            "source_name": "Valuation model",
            "source_timestamp": valuation.updated_at or valuation.created_at,
            "href": f"/companies/{valuation.company_id}/valuation/{valuation.id}",
            "locator": None,
        })

    return sorted(
        results,
        key=lambda item: (
            item["rank"],
            _timestamp_value(item["source_timestamp"]),
        ),
        reverse=True,
    )[:limit]
