"""Stored-input selection accounting, independent of provider/source verification."""
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.models import Event, ProcessingRun
from app.schemas.brief import BriefPublicCoverage

EVENT_CAP = 50
FAILED_RUN_CAP = 10
INSPECTION_ACTION_CAP = 20
FAILED_RUN_STATUSES = ("failed", "error", "partial", "completed_with_errors")


def time_window(column, start: datetime | None, end: datetime):
    filters = [column <= end]
    if start is not None:
        filters.append(column > start)
    return filters


def failed_run_filter():
    return or_(ProcessingRun.status.in_(FAILED_RUN_STATUSES),
        ProcessingRun.error_count > 0)


def is_failed_run(run: ProcessingRun) -> bool:
    return run.status in FAILED_RUN_STATUSES or (run.error_count or 0) > 0


def count_public_inputs(db: Session, start: datetime | None, end: datetime) -> tuple[int, int]:
    # Scalar subqueries avoid loading bodies or joining unrelated private records.
    events = select(func.count(Event.id)).where(*time_window(Event.created_at, start, end)).scalar_subquery()
    runs = select(func.count(ProcessingRun.id)).where(failed_run_filter(),
        *time_window(ProcessingRun.started_at, start, end)).scalar_subquery()
    event_count, run_count = db.execute(select(events, runs)).one()
    return int(event_count), int(run_count)


def selection_counts(eligible: int | None, included: int, cap: int | None, reason: str) -> dict[str, Any]:
    # A changing underlying collection must not produce negative exclusions.
    if eligible is None or eligible < included:
        return {"eligible_count": None, "included_count": included, "excluded_count": None,
            "cap": cap, "status": "unknown", "exclusion_reasons": {}}
    excluded = eligible - included
    return {"eligible_count": eligible, "included_count": included, "excluded_count": excluded,
        "cap": cap, "status": "partial" if excluded else "complete",
        "exclusion_reasons": {reason: excluded} if excluded else {}}


def public_coverage_context(*, captured_at: datetime, start: datetime | None, end: datetime,
        basis: str, event_total: int, event_included: int, event_cap: int,
        failed_run_total: int, failed_run_included: int, failed_run_cap: int,
        failed_run_reason: str = "failed_run_cap") -> dict[str, Any]:
    return {"captured_at": captured_at, "window_start_exclusive": start, "window_end_inclusive": end,
        "selection_basis": basis,
        "events": selection_counts(event_total, event_included, event_cap, "event_cap"),
        "failed_runs": selection_counts(failed_run_total, failed_run_included, failed_run_cap, failed_run_reason)}


def finish_public_coverage(context: dict[str, Any] | None, *, event_count: int,
        failed_run_count: int, action_count: int) -> dict[str, Any]:
    basis = dict(context) if context is not None else {
        "captured_at": datetime.now(UTC), "selection_basis": "caller_supplied",
        "events": selection_counts(None, event_count, None, "not_counted"),
        "failed_runs": selection_counts(None, failed_run_count, None, "not_counted"),
    }
    actions = selection_counts(action_count, min(action_count, INSPECTION_ACTION_CAP),
        INSPECTION_ACTION_CAP, "inspection_action_cap")
    statuses = {basis["events"]["status"], basis["failed_runs"]["status"], actions["status"]}
    status = "partial" if "partial" in statuses else "unknown" if "unknown" in statuses else "complete"
    return BriefPublicCoverage(**basis, inspection_actions=actions, status=status, limitations=[
        "Counts describe selected stored records, not complete provider ingestion or independent source verification.",
        "Inspection actions are derived from included inputs; excluded inputs may require additional actions.",
        "The collection-time window is separate from publication dates and the brief date; this is not a historical backtest.",
        *(["The dashboard previews ten events and failures from its twenty most recently stored processing runs."]
            if basis["selection_basis"] == "dashboard_preview" else []),
    ]).model_dump(mode="json")
