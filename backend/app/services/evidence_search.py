import re
from collections.abc import Sequence
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import and_, false, func, literal, or_, select
from sqlalchemy.orm import Session, joinedload, noload, selectinload

from app.models import (
    AiOutput,
    Alert,
    Event,
    EventEvidenceReference,
    NarrativeClaim,
    NarrativeCluster,
    NarrativeMention,
    RawDocument,
    ResearchMessage,
    ResearchSession,
    ThesisNote,
    ValuationModel,
)
from app.models.decision_journal import DecisionLog


SEARCH_RESULT_TYPES = frozenset({
    "document",
    "event",
    "alert",
    "thesis",
    "decision",
    "valuation",
    "narrative",
    "research_session",
    "research_message",
    "ai_output",
})
MAX_EXCERPT_CHARS = 280


def _first_term(query: str) -> str | None:
    terms = re.findall(r"[A-Za-z0-9][A-Za-z0-9._%-]{1,}", query)
    return terms[0] if terms else None


def _text_locator(text: str | None, query: str) -> tuple[str | None, dict[str, Any] | None]:
    if not text:
        return None, None
    term = _first_term(query)
    if not term:
        return text[:MAX_EXCERPT_CHARS], None
    match = re.search(re.escape(term), text, re.IGNORECASE)
    if not match:
        return text[:MAX_EXCERPT_CHARS], None
    match_length = match.end() - match.start()
    leading_context = max(0, (MAX_EXCERPT_CHARS - match_length) // 2)
    start = max(0, match.start() - leading_context)
    end = min(len(text), start + MAX_EXCERPT_CHARS)
    if end - start < MAX_EXCERPT_CHARS and start > 0:
        start = max(0, end - MAX_EXCERPT_CHARS)
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
            "scope": "shared",
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
            "scope": "shared",
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
            "scope": "private",
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
            "scope": "private",
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
            "scope": "private",
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
            "scope": "private",
            "source_name": "Valuation model",
            "source_timestamp": valuation.updated_at or valuation.created_at,
            "href": f"/companies/{valuation.company_id}/valuation/{valuation.id}",
            "locator": None,
        })

    if "narrative" in requested_types:
        cluster_filters = []
        claim_filters = []
        if company_id is not None:
            cluster_company_match = NarrativeCluster.mentions.any(
                NarrativeMention.event.has(Event.company_id == company_id)
            )
            cluster_filters.append(cluster_company_match)
            claim_filters.append(NarrativeClaim.cluster.has(cluster_company_match))
        narrative_by_cluster: dict[int, dict[str, Any]] = {}
        cluster_rows = _ranked_rows(
            db,
            NarrativeCluster,
            query,
            columns=(NarrativeCluster.name, NarrativeCluster.description),
            base_rank=0.65,
            filters=cluster_filters,
            options=(noload("*"),),
            limit=limit,
        )
        for cluster, rank in cluster_rows:
            narrative_by_cluster[cluster.id] = {
                "result_type": "narrative",
                "record_id": cluster.id,
                "company_id": company_id,
                "title": cluster.name,
                "excerpt": _excerpt(query, cluster.description),
                "rank": float(rank),
                "claim_type": "AI Interpretation",
                "scope": "shared",
                "source_name": "Shared narrative workspace",
                "source_timestamp": cluster.updated_at or cluster.created_at,
                "href": f"/narratives#narrative-{cluster.id}",
                "locator": None,
            }
        claim_rows = _ranked_rows(
            db,
            NarrativeClaim,
            query,
            columns=(NarrativeClaim.claim_text,),
            base_rank=0.72,
            filters=claim_filters,
            options=(noload("*"), joinedload(NarrativeClaim.cluster)),
            limit=limit,
        )
        for claim, rank in claim_rows:
            candidate = {
                "result_type": "narrative",
                "record_id": claim.cluster_id,
                "company_id": company_id,
                "title": claim.cluster.name,
                "excerpt": _excerpt(query, claim.claim_text),
                "rank": float(rank),
                "claim_type": "AI Interpretation",
                "scope": "shared",
                "source_name": "Shared narrative claim",
                "source_timestamp": claim.created_at,
                "href": f"/narratives#narrative-{claim.cluster_id}",
                "locator": None,
            }
            current = narrative_by_cluster.get(claim.cluster_id)
            if current is None or candidate["rank"] > current["rank"]:
                narrative_by_cluster[claim.cluster_id] = candidate
        results.extend(narrative_by_cluster.values())

    if company_id is None and "research_session" in requested_types:
        research_session_rows = _ranked_rows(
            db,
            ResearchSession,
            query,
            columns=(ResearchSession.title,),
            base_rank=0.68,
            filters=(ResearchSession.user_id == user_id,),
            options=(noload("*"),),
            limit=limit,
        )
        for session, rank in research_session_rows:
            results.append({
                "result_type": "research_session",
                "record_id": session.id,
                "company_id": None,
                "title": session.title,
                "excerpt": None,
                "rank": float(rank),
                "claim_type": "User Assumption",
                "scope": "private",
                "source_name": "Private research session",
                "source_timestamp": session.updated_at or session.created_at,
                "href": f"/research/sessions/{session.id}",
                "locator": None,
            })

    if company_id is None and "research_message" in requested_types:
        research_message_rows = _ranked_rows(
            db,
            ResearchMessage,
            query,
            columns=(ResearchMessage.content,),
            base_rank=0.74,
            filters=(
                ResearchMessage.role == "user",
                ResearchMessage.session.has(ResearchSession.user_id == user_id),
            ),
            options=(noload("*"), joinedload(ResearchMessage.session)),
            limit=limit,
        )
        for message, rank in research_message_rows:
            results.append({
                "result_type": "research_message",
                "record_id": message.id,
                "company_id": None,
                "title": message.session.title,
                "excerpt": _excerpt(query, message.content),
                "rank": float(rank),
                "claim_type": "User Assumption",
                "scope": "private",
                "source_name": "Private user research message",
                "source_timestamp": message.created_at,
                "href": f"/research/sessions/{message.session_id}#message-{message.id}",
                "locator": None,
            })

    if "ai_output" in requested_types:
        ai_filters = [
            AiOutput.user_id == user_id,
            AiOutput.human_review_status == "approved",
            AiOutput.is_blocked == false(),
            AiOutput.execution_status == "success",
            AiOutput.reviewed_at.is_not(None),
            or_(
                AiOutput.raw_document_id.is_not(None),
                and_(
                    AiOutput.reference_type == "research_session",
                    AiOutput.reference_id.is_not(None),
                ),
            ),
        ]
        if company_id is not None:
            ai_filters.append(
                AiOutput.raw_document.has(RawDocument.company_id == company_id)
            )
        ai_output_rows = _ranked_rows(
            db,
            AiOutput,
            query,
            columns=(AiOutput.output_text,),
            base_rank=0.78,
            filters=ai_filters,
            options=(noload("*"), joinedload(AiOutput.raw_document)),
            limit=limit,
        )
        for output, rank in ai_output_rows:
            document = output.raw_document
            if document is not None:
                title = f"Reviewed AI summary: {document.title}"
                href = f"/documents/{document.id}/ai#ai-output-{output.id}"
                result_company_id = document.company_id
            else:
                title = "Reviewed research response"
                href = f"/research/sessions/{output.reference_id}#ai-output-{output.id}"
                result_company_id = None
            results.append({
                "result_type": "ai_output",
                "record_id": output.id,
                "company_id": result_company_id,
                "title": title,
                "excerpt": _excerpt(query, output.output_text),
                "rank": float(rank),
                "claim_type": "AI Interpretation",
                "scope": "private",
                "review_status": "approved",
                "is_mock": output.is_mock,
                "source_name": f"{output.provider_name} · {output.model_name}",
                "source_timestamp": output.reviewed_at or output.created_at,
                "href": href,
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
