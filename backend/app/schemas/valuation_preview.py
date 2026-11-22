from datetime import date, datetime
from typing import Any

from pydantic import BaseModel
from app.schemas.first_valuation import BoundFinancialSource
from app.schemas.valuation_outputs import DiagnosticWarning


class ValuationInputChange(BaseModel):
    field: str
    previous: Any
    proposed: Any


class ValuationPreviewRead(BaseModel):
    model_id: int
    base_assumption_set_id: int | None
    base_assumption_set_updated_at: datetime | None
    valuation_date: date | None
    preview_hash: str
    ready: bool
    missing_fields: list[str]
    changes: list[ValuationInputChange]
    previous_output: dict[str, float | None] | None
    proposed_output: dict[str, float | None] | None
    diagnostics: list[DiagnosticWarning]
    currency: str | None
    limitations: list[str]


class ValuationVersionReceiptRead(BaseModel):
    draft_id: int | None = None
    sources: list[BoundFinancialSource] | None = None
    assumption_set_id: int
    previous_assumption_set_id: int | None
    valuation_date: date | None
    reason: str | None
    saved_at: datetime
    preview_hash: str | None
