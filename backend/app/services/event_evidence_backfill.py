from __future__ import annotations

from collections import Counter, defaultdict
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models import Alert, Event, EventEvidenceReference
from app.services.processing_runs import (
    complete_processing_run,
    fail_processing_run,
    start_processing_run,
)


MIN_EXACT_CLAIM_LENGTH = 24
MAX_EXACT_CLAIM_LENGTH = 2_000
DEFAULT_BACKFILL_LIMIT = 100
MAX_BACKFILL_LIMIT = 200


def _candidate_claim(value: str | None) -> str | None:
    if value is None:
        return None
    claim = value.strip()
    if len(claim) < MIN_EXACT_CLAIM_LENGTH or len(claim) > MAX_EXACT_CLAIM_LENGTH:
        return None
    return claim


def _base_entry(event: Event, status: str, action: str) -> dict[str, Any]:
    return {
        "event_id": event.id,
        "company_id": event.company_id,
        "raw_document_id": event.raw_document_id,
        "event_title": event.title,
        "priority_score": event.priority_score,
        "status": status,
        "claim_origin": None,
        "quote": None,
        "start_char": None,
        "end_char": None,
        "occurrence_count": 0,
        "action": action,
    }


def _assess_event(event: Event, alerts: list[Alert]) -> dict[str, Any]:
    document = event.raw_document
    if document is None:
        return _base_entry(event, "missing_document", "Link the event to a stored source document.")
    if not document.raw_text:
        return _base_entry(event, "missing_source_text", "Re-ingest source text before creating an exact span.")

    candidates: list[tuple[str, str]] = []
    for alert in alerts:
        claim = _candidate_claim(alert.evidence)
        if claim:
            candidates.append(("alert.evidence", claim))
    description = _candidate_claim(event.description)
    if description:
        candidates.append(("event.description", description))

    unique_candidates = list(dict.fromkeys(candidates))
    if not unique_candidates:
        return _base_entry(
            event,
            "missing_candidate_claim",
            f"Add a source-derived claim between {MIN_EXACT_CLAIM_LENGTH} and {MAX_EXACT_CLAIM_LENGTH} characters.",
        )

    matches: list[tuple[str, str, int]] = []
    maximum_occurrences = 0
    for origin, claim in unique_candidates:
        occurrence_count = document.raw_text.count(claim)
        maximum_occurrences = max(maximum_occurrences, occurrence_count)
        if occurrence_count == 1:
            matches.append((origin, claim, document.raw_text.index(claim)))

    distinct_matches = {(claim, start) for _, claim, start in matches}
    if len(distinct_matches) > 1:
        entry = _base_entry(
            event,
            "conflicting_exact_matches",
            "Review the competing exact claims and select the intended source span manually.",
        )
        entry["occurrence_count"] = len(distinct_matches)
        return entry
    if len(matches) == 1:
        origin, quote, start = matches[0]
        entry = _base_entry(event, "eligible", "Apply the exact deterministic text span.")
        entry.update({
            "claim_origin": origin,
            "quote": quote,
            "start_char": start,
            "end_char": start + len(quote),
            "occurrence_count": 1,
        })
        return entry
    if maximum_occurrences > 1:
        entry = _base_entry(
            event,
            "ambiguous_match",
            "Capture a longer or more specific source passage before backfilling.",
        )
        entry["occurrence_count"] = maximum_occurrences
        return entry
    return _base_entry(
        event,
        "no_exact_match",
        "Review the source manually; fuzzy matching is intentionally disabled.",
    )


def preview_event_evidence_backfill(
    db: Session,
    *,
    user_id: str,
    limit: int = DEFAULT_BACKFILL_LIMIT,
    event_ids: list[int] | None = None,
) -> dict[str, Any]:
    bounded_limit = min(max(limit, 1), MAX_BACKFILL_LIMIT)
    statement = (
        select(Event)
        .options(selectinload(Event.raw_document))
        .where(~Event.evidence_references.any())
        .order_by(
            Event.priority_score.desc().nullslast(),
            Event.event_time.desc().nullslast(),
            Event.id.desc(),
        )
        .limit(bounded_limit)
    )
    if event_ids:
        statement = statement.where(Event.id.in_(event_ids))
    events = list(db.scalars(statement))
    alerts_by_event: dict[int, list[Alert]] = defaultdict(list)
    if events:
        alerts = db.scalars(
            select(Alert)
            .where(
                Alert.user_id == user_id,
                Alert.event_id.in_([event.id for event in events]),
                Alert.evidence.is_not(None),
            )
            .order_by(Alert.id)
        )
        for alert in alerts:
            if alert.event_id is not None:
                alerts_by_event[alert.event_id].append(alert)

    entries = [_assess_event(event, alerts_by_event[event.id]) for event in events]
    status_counts = Counter(entry["status"] for entry in entries)
    return {
        "dry_run": True,
        "processing_run_id": None,
        "checked_event_count": len(entries),
        "eligible_count": status_counts["eligible"],
        "applied_count": 0,
        "race_skipped_count": 0,
        "status_counts": dict(status_counts),
        "generated_at": datetime.now(UTC),
        "limitations": [
            "Only events without any evidence reference are scanned.",
            "Only exact case-sensitive matches are eligible; fuzzy and whitespace-normalized matching are disabled.",
            "Alert evidence is restricted to the authenticated user's alerts.",
            f"Claims must be {MIN_EXACT_CLAIM_LENGTH}-{MAX_EXACT_CLAIM_LENGTH} characters and occur exactly once.",
        ],
        "entries": entries,
    }


def execute_event_evidence_backfill(
    db: Session,
    *,
    user_id: str,
    dry_run: bool,
    limit: int = DEFAULT_BACKFILL_LIMIT,
    event_ids: list[int] | None = None,
) -> dict[str, Any]:
    run = start_processing_run(
        db,
        run_type="event_evidence_backfill",
        source_type="stored_documents",
        metadata={"dry_run": dry_run, "limit": limit, "requested_event_ids": event_ids or []},
    )
    try:
        report = preview_event_evidence_backfill(
            db,
            user_id=user_id,
            limit=limit,
            event_ids=event_ids,
        )
        applied_count = 0
        race_skipped_count = 0
        if not dry_run:
            for entry in report["entries"]:
                if entry["status"] != "eligible":
                    continue
                locked_event = db.scalar(
                    select(Event)
                    .where(Event.id == entry["event_id"])
                    .with_for_update()
                )
                if locked_event is None:
                    entry["status"] = "race_skipped_event_missing"
                    entry["action"] = "The event was deleted before apply; no evidence was created."
                    race_skipped_count += 1
                    continue
                has_reference = db.scalar(
                    select(EventEvidenceReference.id)
                    .where(EventEvidenceReference.event_id == entry["event_id"])
                    .limit(1)
                )
                if has_reference is not None:
                    entry["status"] = "race_skipped_existing_reference"
                    entry["action"] = "No action required; another reference was created before apply."
                    race_skipped_count += 1
                    continue
                db.add(EventEvidenceReference(
                    event_id=entry["event_id"],
                    raw_document_id=entry["raw_document_id"],
                    created_by_user_id=user_id,
                    locator_type="text_span",
                    start_char=entry["start_char"],
                    end_char=entry["end_char"],
                    quote=entry["quote"],
                    source_metadata_json={
                        "backfill_method": "exact_unique_case_sensitive_match",
                        "claim_origin": entry["claim_origin"],
                        "processing_run_id": run.id,
                    },
                    confidence_label="high",
                    origin="deterministic_backfill",
                ))
                entry["status"] = "applied"
                entry["action"] = "Exact text-span evidence created."
                applied_count += 1
            db.flush()

        status_counts = Counter(entry["status"] for entry in report["entries"])
        completed = complete_processing_run(
            db,
            run,
            fetched_count=report["checked_event_count"],
            created_count=applied_count,
            skipped_duplicate_count=race_skipped_count,
            metadata_patch={
                "eligible_count": report["eligible_count"],
                "status_counts": dict(status_counts),
            },
        )
        report.update({
            "dry_run": dry_run,
            "processing_run_id": completed.id,
            "applied_count": applied_count,
            "race_skipped_count": race_skipped_count,
            "status_counts": dict(status_counts),
        })
        return report
    except Exception:
        db.rollback()
        fail_processing_run(
            db,
            run,
            error_type="EVENT_EVIDENCE_BACKFILL_FAILED",
            message="Historical event evidence backfill failed.",
        )
        raise
