"""Typed evidence and reviewed first-model commands."""
from datetime import date, datetime
from typing import Any, Literal
from uuid import UUID

from app.schemas.dated_inputs import DatedInputSource

from pydantic import BaseModel, ConfigDict, Field, model_validator


class StrictCommand(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class DraftSourceRef(StrictCommand):
    kind: Literal["source_fact_revision"]
    id: int = Field(gt=0)
    target_field: Literal["starting_revenue", "net_income", "cash", "debt", "minority_interests", "preferred_stock", "employee_options_value", "change_in_nwc", "depreciation", "capex", "diluted_shares"]


class DraftSourceProposal(StrictCommand):
    expected_updated_at: datetime
    valuation_date: date
    knowledge: Literal["available_by_date"] = "available_by_date"
    selections: list[DraftSourceRef] = Field(max_length=12)

    @model_validator(mode="after")
    def one_revision_per_input(self):
        fields = [item.target_field for item in self.selections]
        if len(set(fields)) != len(fields):
            raise ValueError("Choose one source revision per model input")
        return self


class FirstModelPreview(StrictCommand):
    name: str = Field(min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=4000)
    model_type: Literal["fcff_dcf", "financial_services", "distressed"] = "fcff_dcf"
    expected_updated_at: datetime
    valuation_date: date
    knowledge: Literal["available_by_date"] = "available_by_date"


class FirstModelConfirm(FirstModelPreview):
    submission_id: UUID
    preview_hash: str = Field(pattern=r"^[0-9a-f]{64}$")
    reason: str = Field(min_length=1, max_length=2000)


class BoundFinancialSource(BaseModel):
    model_config = ConfigDict(extra="allow")
    ref: DraftSourceRef
    status: Literal["eligible", "held"]
    reason: str | None = None
    conversion: str | None = None
    source: DatedInputSource | None = None


class FirstModelPreviewRead(BaseModel):
    draft_id: int
    valuation_date: date
    preview_hash: str
    ready: bool
    blockers: list[str]
    assumptions: dict[str, Any]
    sources: list[BoundFinancialSource]
    diagnostics: list[dict[str, Any]]
    proposed_output: dict[str, float | None] | None
    currency: str | None


class FirstModelSaved(BaseModel):
    model_id: int
    assumption_set_id: int
    replayed: bool
