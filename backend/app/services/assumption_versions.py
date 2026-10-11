"""Create calculation versions from an owned model and an optional optimistic basis."""
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.dcf import DcfAssumptionSet, ValuationModel
from app.schemas.valuation_inputs import DcfAssumptionSetCreate, DcfAssumptionSetWrite, DcfAssumptionVersionWrite
from app.services.assumption_diff_service import AssumptionDiffService
from app.services.dcf import calculate_dcf


class AssumptionVersionConflict(ValueError):
    pass


def _utc(value: datetime) -> datetime:
    return value.replace(tzinfo=UTC) if value.tzinfo is None else value.astimezone(UTC)


def create_assumption_version(db: Session, model: ValuationModel, request: DcfAssumptionVersionWrite) -> DcfAssumptionSet:
    # Serialize writers for this model in PostgreSQL, including legacy full saves.
    # The caller has already authorized the model. No commit belongs in this service.
    db.execute(select(ValuationModel.id).where(ValuationModel.id == model.id).with_for_update()).one()
    transient = {"base_assumption_set_id", "base_assumption_set_updated_at"}
    if request.base_assumption_set_id is not None:
        previous = db.scalar(select(DcfAssumptionSet).where(
            DcfAssumptionSet.valuation_model_id == model.id
        ).order_by(DcfAssumptionSet.created_at.desc(), DcfAssumptionSet.id.desc()).limit(1)
            .execution_options(populate_existing=True))
        expected = request.base_assumption_set_updated_at
        if (previous is None or previous.id != request.base_assumption_set_id
                or expected is None or _utc(previous.updated_at) != _utc(expected)):
            raise AssumptionVersionConflict("Saved assumptions changed. Reload the latest version before saving; your submitted inputs were not written.")
        inputs = {field: getattr(previous, field) for field in DcfAssumptionSetCreate.model_fields}
        # A reviewed resave produces a fresh calculation, not a copied stale receipt.
        inputs.update(is_stale=False, stale_reason=None, stale_event_id=None)
        inputs.update(request.model_dump(exclude_unset=True, exclude=transient))
    else:
        inputs = request.model_dump(exclude=transient)
    inputs["valuation_model_id"] = model.id
    validated = DcfAssumptionSetWrite.model_validate(inputs)
    row = DcfAssumptionSet(**validated.model_dump(exclude=transient))
    db.add(row)
    db.flush()
    output, projections, sensitivities = calculate_dcf(row, model_type=model.model_type)
    db.add(output)
    db.add_all(projections)
    db.add_all(sensitivities)
    AssumptionDiffService.generate_change_logs(db, row)
    return row
