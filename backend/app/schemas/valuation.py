"""Saved valuation response assembly, including non-writing implied-pricing reconciliation."""
from datetime import datetime
from typing import Any, Literal
from pydantic import BaseModel, ConfigDict, Field, ValidationInfo, model_validator
from app.schemas.valuation_inputs import ValuationModelCreate, DcfAssumptionSetCreate
from app.schemas.valuation_outputs import DcfOutputCreate, DcfProjectionYearRead, DcfSensitivityTableRead, DcfDecisionLogRead, ValuationAssumptionChangeLogRead


class DcfOutputRead(DcfOutputCreate):
    model_config = ConfigDict(from_attributes=True)
    id: int
    created_at: datetime
    implied_pricing_basis: dict[str, Any] | None = None

    @model_validator(mode="before")
    @classmethod
    def reconcile_pricing_read(cls, value: Any, info: ValidationInfo) -> Any:
        if isinstance(value, cls):
            return value
        from app.services.relative_valuation_service import reconcile_output_read
        data = dict(value) if isinstance(value, dict) else {
            key: getattr(value, key) for key in cls.model_fields if hasattr(value, key)
        }
        return reconcile_output_read(data, (info.context or {}).get("assumption_set"))


class QuickValuationAssumptionsRead(BaseModel):
    company_id: int
    assumptions: DcfAssumptionSetCreate
    provenance: dict[str, Any]
    source_metadata: dict[str, Any]
    warnings: list[str]


class DcfAssumptionSetRead(DcfAssumptionSetCreate):
    model_config = ConfigDict(from_attributes=True)
    id: int
    created_at: datetime
    updated_at: datetime
    outputs: DcfOutputRead | None = None
    projection_years: list[DcfProjectionYearRead] = Field(default_factory=list)
    sensitivity_tables: list[DcfSensitivityTableRead] = Field(default_factory=list)
    change_logs: list[ValuationAssumptionChangeLogRead] = Field(default_factory=list)

    @model_validator(mode="before")
    @classmethod
    def provide_pricing_input_context(cls, value: Any) -> Any:
        if isinstance(value, cls):
            return value
        data = dict(value) if isinstance(value, dict) else {
            key: getattr(value, key) for key in cls.model_fields if hasattr(value, key)
        }
        if data.get("outputs") is not None:
            data["outputs"] = DcfOutputRead.model_validate(data["outputs"], context={"assumption_set": value})
        return data


class ValuationModelRead(ValuationModelCreate):
    model_config = ConfigDict(from_attributes=True)
    id: int
    model_type: str | None = None
    created_at: datetime
    updated_at: datetime
    assumption_sets: list[DcfAssumptionSetRead] = Field(default_factory=list)
    decision_logs: list[DcfDecisionLogRead] = Field(default_factory=list)


class ValuationModelSummaryRead(BaseModel):
    id: int
    company_id: int
    name: str
    description: str | None = None
    model_type: str
    created_at: datetime
    updated_at: datetime
    assumption_set_count: int
    latest_assumption_set_id: int | None = None
    latest_scenario: str | None = None
    latest_run_at: datetime | None = None
    readiness: Literal["setup_incomplete", "review_required", "calculation_unavailable", "blocked", "calculated"]
    readiness_detail: str
    intrinsic_value_per_share: float | None = None
    model_quality_score: float | None = None
    cash_flow_currency: str | None = None


class ValuationSetupDraftRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: str
    company_id: int
    promoted_model_id: int | None = None
    status: str
    industry_name: str | None = None
    assumptions_json: dict[str, Any]
    provenance_json: dict[str, Any]
    source_metadata_json: dict[str, Any]
    warnings_json: list[str]
    reviewed_fields_json: list[str]
    edited_fields_json: list[str]
    created_at: datetime
    updated_at: datetime


class DcfScenarioOutput(BaseModel):
    scenario_name: str
    description: str
    output: DcfOutputRead
