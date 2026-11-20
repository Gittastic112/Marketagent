"""Read-only dated financial evidence. Not model approval or historical reconstruction."""
from datetime import date, datetime
from typing import Any, Literal

from pydantic import BaseModel


class DatedInputSource(BaseModel):
    revision_id: int
    revision_number: int
    candidate_id: int
    document_id: int
    href: str
    value: float
    unit: str | None
    claim_type: str
    published_at: datetime | None
    publication_date: date | None
    publication_precision: Literal["date", "timestamp", "unknown"]
    recorded_at: datetime
    retrieved_at: datetime
    availability: Literal["available_by_date", "published_later", "publication_unknown"]
    period: dict[str, Any]
    locator: dict[str, Any]
    passage: str


class DatedInputRow(BaseModel):
    metric: str
    label: str
    status: Literal["available", "missing", "conflict", "unavailable_by_date", "unit_review"]
    selected_revision_id: int | None
    original_value: float | None
    original_unit: str | None
    normalized_value: float | None
    normalized_unit: str | None
    conversion: str | None
    claim_type: str | None
    effective_at: date | None
    sources: list[DatedInputSource]
    limitations: list[str]


class DatedInputsRead(BaseModel):
    company_id: int
    valuation_date: date
    knowledge: Literal["available_by_date", "latest_recorded"]
    track: Literal["operating", "bank_equity", "equity_cash_flow"]
    rows: list[DatedInputRow]
    truncated: bool
    limitations: list[str]
