"""Read-only identity and diagnostics for explanations of saved calculations."""
from datetime import UTC, datetime
import hashlib
import json
from math import isfinite

from pydantic import ValidationError
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.ai import AiOutput
from app.models.dcf import DcfAssumptionSet
from app.schemas.valuation_inputs import DcfAssumptionSetWrite


def utc(value: datetime) -> datetime:
    return value.replace(tzinfo=UTC) if value.tzinfo is None else value.astimezone(UTC)


def latest_scenario(db: Session, model_id: int, scenario: str) -> DcfAssumptionSet | None:
    return db.scalar(select(DcfAssumptionSet).where(
        DcfAssumptionSet.valuation_model_id == model_id, DcfAssumptionSet.scenario == scenario,
    ).order_by(DcfAssumptionSet.created_at.desc(), DcfAssumptionSet.id.desc()).limit(1)
        .execution_options(populate_existing=True))


def valuation_basis(row: DcfAssumptionSet) -> dict:
    output = row.outputs
    try:
        output_hash = hashlib.sha256(json.dumps(
            {column.key: getattr(output, column.key) for column in output.__table__.columns},
            sort_keys=True, separators=(",", ":"), default=str, allow_nan=False,
        ).encode()).hexdigest() if output else None
    except (ValueError, TypeError):
        output_hash = None  # A malformed legacy calculation is never verified.
    return {"assumption_set_id": row.id, "assumptions_updated_at": utc(row.updated_at).isoformat(),
            "valuation_model_id": row.valuation_model_id, "scenario": row.scenario,
            "output_id": output.id if output else None,
            "output_hash": output_hash,
            "output_calculated_at": utc(output.created_at).isoformat() if output and output.created_at else None,
            "currency": row.cash_flow_currency,
            "input_claim_type": "User Assumption", "output_claim_type": "Calculation"}


def require_memo_basis(row: DcfAssumptionSet) -> None:
    if row.is_stale:
        raise ValueError("Saved assumptions are stale. Review and save a current calculation before generating a memo.")
    try:
        DcfAssumptionSetWrite.model_validate(row, from_attributes=True)
    except ValidationError:
        raise ValueError("Saved assumption units or currencies are invalid. Correct and save them before generating a memo.") from None
    output = row.outputs
    warnings = output.warnings_json if output else None
    if (not row.cash_flow_currency or not row.discount_rate_currency or output is None
            or output.assumption_set_id != row.id or output.intrinsic_value_per_share is None
            or not isfinite(output.intrinsic_value_per_share) or valuation_basis(row)["output_hash"] is None
            or not isinstance(warnings, list)
            or any(not isinstance(w, dict) or w.get("severity") not in {"info", "watch", "warning"}
                   or not isinstance(w.get("message"), str) or not isinstance(w.get("module"), str) for w in warnings)):
        raise ValueError("Saved output is missing, invalid or blocked by diagnostics. Save a valid calculation before generating a memo.")


def explanation_evidence(db: Session, output: AiOutput, row: DcfAssumptionSet) -> dict:
    stored = (output.evaluation_json or {}).get("valuation_basis")
    latest = latest_scenario(db, row.valuation_model_id, row.scenario)
    current = bool(stored and stored.get("output_hash") and latest and not latest.is_stale and valuation_basis(latest) == stored)
    return {**(stored or {"assumption_set_id": row.id, "valuation_model_id": row.valuation_model_id,
                         "scenario": row.scenario}),
            "ai_output_id": output.id, "claim_type": "AI Interpretation", "is_current": current,
            "basis_verified": bool(stored), "provider_name": output.provider_name, "model_name": output.model_name,
            "prompt_version": output.prompt_version, "input_hash": output.input_hash,
            "source_ids": output.source_ids_json, "generated_at": utc(output.created_at).isoformat(),
            "review_status": output.human_review_status, "is_mock": output.is_mock,
            "confidence_label": output.confidence_label, "limitations": output.limitations,
            "interpretation_quality": "not_evaluated"}
