"""State-bound review receipts and raw historical exports; never recalculate evidence."""
from datetime import UTC, datetime
import hashlib
import json

from sqlalchemy import inspect, select
from sqlalchemy.orm import Session

from app.models.dcf import DcfAssumptionSet, DcfDecisionLog


def stale_review_token(value) -> str:
    def field(name):
        return value.get(name) if isinstance(value, dict) else getattr(value, name, None)
    updated = field("updated_at")
    if isinstance(updated, str):
        updated = datetime.fromisoformat(updated.replace("Z", "+00:00"))
    if isinstance(updated, datetime):
        updated = (updated.replace(tzinfo=UTC) if updated.tzinfo is None else updated.astimezone(UTC)).isoformat()
    basis = {key: field(key) for key in ("id", "is_stale", "stale_reason", "stale_event_id")}
    basis["updated_at"] = updated
    basis["change_log_ids"] = sorted(log.get("id") if isinstance(log, dict) else log.id for log in field("change_logs") or [])
    return hashlib.sha256(json.dumps(basis, sort_keys=True, default=str).encode()).hexdigest()


def acknowledge_stale_review(db: Session, assumption_id: int, request, user_id: str):
    row = db.scalar(select(DcfAssumptionSet).where(DcfAssumptionSet.id == assumption_id)
        .with_for_update().execution_options(populate_existing=True))
    db.expire(row, ["change_logs"])
    expected = request.expected_updated_at
    expected = expected.replace(tzinfo=UTC) if expected.tzinfo is None else expected.astimezone(UTC)
    updated = row.updated_at.replace(tzinfo=UTC) if row.updated_at.tzinfo is None else row.updated_at.astimezone(UTC)
    if updated != expected or stale_review_token(row) != request.review_token or not row.is_stale:
        raise ValueError("The saved version or review trigger changed. Reload and inspect it before acknowledging.")
    receipt = {"reviewed_by": user_id, "review_token": request.review_token,
        "reviewed_updated_at": updated.isoformat(), "stale_event_id": row.stale_event_id,
        "stale_reason": row.stale_reason, "reason": request.reason,
        "disposition": "assumptions_unchanged_after_review"}
    db.add(DcfDecisionLog(valuation_model_id=row.valuation_model_id, assumption_set_id=row.id,
        decision_type="stale_review", user_note=json.dumps(receipt)))
    row.is_stale = False
    row.stale_reason = None
    row.stale_event_id = None
    row.updated_at = datetime.now(UTC)
    db.flush()
    return row


def export_saved_valuation(row: DcfAssumptionSet) -> dict:
    def columns(record):
        return {attribute.key: getattr(record, attribute.key) for attribute in inspect(record).mapper.column_attrs}
    saved = columns(row)
    saved["outputs"] = columns(row.outputs) if row.outputs else None
    for relation in ("projection_years", "sensitivity_tables", "change_logs"):
        saved[relation] = [columns(item) for item in sorted(getattr(row, relation), key=lambda item: item.id)]
    return {"model_id": row.valuation_model_id, "assumption_set_id": row.id,
        "export_kind": "raw_saved_valuation_v1", "saved_version": saved,
        "decision_receipts": [columns(item) for item in sorted(row.decision_logs, key=lambda item: item.id)],
        "limitations": ["Historical stored inputs and outputs, including original warnings and superseded calculations. No read-time reconciliation or recalculation is applied.",
            "The current interpreted view may differ. This archive is not source approval, a current quote or investment advice."]}
