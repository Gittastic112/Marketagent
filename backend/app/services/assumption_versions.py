"""Create calculation versions from an owned model and an optional optimistic basis."""
from datetime import UTC, datetime
import hashlib
import json
from math import isfinite

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.dcf import DcfAssumptionSet, DcfDecisionLog, ValuationModel
from app.schemas.valuation_inputs import DcfAssumptionSetCreate, DcfAssumptionSetWrite, DcfAssumptionVersionWrite
from app.services.assumption_diff_service import AssumptionDiffService
from app.services.dcf import calculate_dcf
from app.services.assumption_provenance import required_fields_by_model, unavailable_discount_component


COMMAND_FIELDS = {"base_assumption_set_id", "base_assumption_set_updated_at", "submission_id",
                  "preview_hash", "change_reason", "valuation_date"}
OUTPUT_FIELDS = ("enterprise_value", "equity_value", "intrinsic_value_per_share", "terminal_value_pct_of_ev")


def _hash(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), default=str, allow_nan=False).encode()).hexdigest()


class AssumptionVersionConflict(ValueError):
    pass


def _utc(value: datetime) -> datetime:
    return value.replace(tzinfo=UTC) if value.tzinfo is None else value.astimezone(UTC)


def _prepare(db, model, request):
    previous = db.scalar(select(DcfAssumptionSet).where(
        DcfAssumptionSet.valuation_model_id == model.id
    ).order_by(DcfAssumptionSet.created_at.desc(), DcfAssumptionSet.id.desc()).limit(1)
        .execution_options(populate_existing=True))
    if request.base_assumption_set_id is not None:
        expected = request.base_assumption_set_updated_at
        if (previous is None or previous.id != request.base_assumption_set_id
                or expected is None or _utc(previous.updated_at) != _utc(expected)):
            raise AssumptionVersionConflict("Saved assumptions changed. Reload the latest version before saving; your submitted inputs were not written.")
        inputs = {field: getattr(previous, field) for field in DcfAssumptionSetCreate.model_fields}
        # A reviewed resave produces a fresh calculation, not a copied stale receipt.
        inputs.update(is_stale=False, stale_reason=None, stale_event_id=None)
        inputs.update(request.model_dump(exclude_unset=True, exclude=COMMAND_FIELDS))
    else:
        inputs = request.model_dump(exclude=COMMAND_FIELDS)
    inputs["valuation_model_id"] = model.id
    validated = DcfAssumptionSetWrite.model_validate(inputs)
    return previous, validated.model_dump()


def preview_assumption_version(db, model, request):
    previous, inputs = _prepare(db, model, request)
    missing = sorted(field for field in required_fields_by_model()[model.model_type]
        if (inputs.get(field) is None or inputs.get(field) == "" or inputs.get(field) == {})
        and not unavailable_discount_component(field, inputs.get(field), inputs, model.model_type))
    digest_basis = {"model_id": model.id, "model_type": model.model_type,
        "base_id": previous.id if previous else None,
        "base_updated_at": _utc(previous.updated_at).isoformat() if previous else None,
        "valuation_date": request.valuation_date, "inputs": inputs}
    output = None
    diagnostics = []
    if not missing:
        output, _, _ = calculate_dcf(DcfAssumptionSet(id=0, **inputs), model_type=model.model_type, include_sensitivity=False)
        diagnostics = [item for item in output.warnings_json or [] if isinstance(item, dict)]
    def summary(value):
        if value is None:
            return None
        return {key: getattr(value, key) if isinstance(getattr(value, key), (int, float))
            and isfinite(getattr(value, key)) else None for key in OUTPUT_FIELDS}
    blocked = any(item.get("severity") in {"critical", "blocking"} for item in diagnostics)
    ready = not missing and not blocked
    previous_result = previous.outputs if previous else None
    previous_warnings = previous_result.warnings_json if previous_result else None
    previous_safe = bool(previous and not previous.is_stale and previous.diluted_shares and previous.diluted_shares > 0
        and isinstance(previous_warnings, list) and all(isinstance(item, dict)
        and item.get("severity") in {"info", "watch", "warning"} for item in previous_warnings))
    digest = _hash({**digest_basis, "proposed_output": summary(output), "diagnostics": diagnostics})
    return dict(model_id=model.id, base_assumption_set_id=previous.id if previous else None,
        base_assumption_set_updated_at=previous.updated_at if previous else None,
        valuation_date=request.valuation_date, preview_hash=digest, ready=ready,
        missing_fields=missing, changes=[dict(field=field, previous=getattr(previous, field) if previous else None,
            proposed=inputs.get(field)) for field in AssumptionDiffService.DIFF_FIELDS
            if (getattr(previous, field) if previous else None) != inputs.get(field)],
        previous_output=summary(previous_result) if previous_safe else None, proposed_output=summary(output) if ready else None,
        diagnostics=diagnostics, currency=inputs.get("cash_flow_currency"), limitations=[
            "Unsaved deterministic calculation. Inputs remain User Assumptions; preview is not source approval.",
            "Valuation date labels the research basis; it does not reconstruct historical market data or alter source selection.",
            "Scenario ranges, sensitivities and memo interpretations must be checked against the saved version.",
        ])


def create_assumption_version(db: Session, model: ValuationModel, request: DcfAssumptionVersionWrite) -> DcfAssumptionSet:
    # Model lock serializes the receipt check and atomic save, including retries.
    db.execute(select(ValuationModel.id).where(ValuationModel.id == model.id).with_for_update()).one()
    fingerprint = _hash(request.model_dump(mode="json", exclude_unset=True))
    receipt_type = f"version_save:{request.submission_id}" if request.submission_id else None
    if receipt_type:
        receipt = db.scalar(select(DcfDecisionLog).where(DcfDecisionLog.valuation_model_id == model.id,
            DcfDecisionLog.decision_type == receipt_type))
        if receipt:
            if json.loads(receipt.user_note or "{}").get("request_hash") != fingerprint:
                raise AssumptionVersionConflict("This save request was already used with different inputs. Preview again before saving.")
            return db.get(DcfAssumptionSet, receipt.assumption_set_id)
    previous, inputs = _prepare(db, model, request)
    if inputs.get("diluted_shares") is None:
        raise ValueError("Explicit positive diluted shares are required. No one-share fallback is allowed.")
    if request.preview_hash:
        preview = preview_assumption_version(db, model, request)
        if preview["preview_hash"] != request.preview_hash:
            raise AssumptionVersionConflict("Inputs or saved basis changed after preview. Preview the current proposal before saving.")
        if not preview["ready"]:
            raise ValueError("Resolve the required inputs and blocking diagnostics before saving this preview.")
    row = DcfAssumptionSet(**inputs)
    db.add(row)
    db.flush()
    output, projections, sensitivities = calculate_dcf(row, model_type=model.model_type)
    db.add(output)
    db.add_all(projections)
    db.add_all(sensitivities)
    AssumptionDiffService.generate_change_logs(db, row)
    if receipt_type:
        db.add(DcfDecisionLog(valuation_model_id=model.id, assumption_set_id=row.id,
            decision_type=receipt_type, user_note=json.dumps({"request_hash": fingerprint,
                "previous_assumption_set_id": previous.id if previous else None,
                "reason": request.change_reason, "preview_hash": request.preview_hash,
                "valuation_date": request.valuation_date.isoformat() if request.valuation_date else None})))
    return row


def version_receipts(db, model):
    receipts = db.scalars(select(DcfDecisionLog).where(DcfDecisionLog.valuation_model_id == model.id,
        DcfDecisionLog.decision_type.like("version_save:%"))
        .order_by(DcfDecisionLog.created_at.desc(), DcfDecisionLog.id.desc()).limit(100)).all()
    return [dict(assumption_set_id=r.assumption_set_id, saved_at=r.created_at,
        **{key: json.loads(r.user_note or "{}").get(key) for key in (
            "previous_assumption_set_id", "valuation_date", "reason", "preview_hash")}) for r in receipts]
