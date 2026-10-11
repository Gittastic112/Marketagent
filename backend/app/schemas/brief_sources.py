"""Source intake and constrained AI suggestions, never valuation mutations."""
from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


ValuationField = Literal[
    "starting_revenue", "revenue_growth_years_json", "current_operating_margin",
    "target_operating_margin", "tax_rate", "sales_to_capital_ratio", "starting_invested_capital",
    "wacc_start", "wacc_terminal", "terminal_growth_rate", "terminal_roic", "cash", "debt", "diluted_shares",
]

FIELD_LABELS = {
    "starting_revenue": "Base-year revenue", "revenue_growth_years_json": "Revenue growth path",
    "current_operating_margin": "Base-year operating margin", "target_operating_margin": "Target operating margin",
    "tax_rate": "Tax rate", "sales_to_capital_ratio": "Sales-to-capital ratio",
    "starting_invested_capital": "Starting invested capital", "wacc_start": "Starting WACC", "wacc_terminal": "Terminal WACC",
    "terminal_growth_rate": "Terminal growth", "terminal_roic": "Terminal ROIC",
    "cash": "Cash / non-operating assets", "debt": "Borrowings", "diluted_shares": "Diluted shares",
}


class BriefSourceCreate(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    company_id: int = Field(gt=0)
    title: str = Field(min_length=1, max_length=240)
    text: str = Field(min_length=40, max_length=60_000)
    source_url: str | None = Field(default=None, max_length=1000)
    as_of_date: date | None = None

    @field_validator("text")
    @classmethod
    def no_nulls(cls, value: str) -> str:
        if "\x00" in value:
            raise ValueError("Text must not contain null characters")
        return value

    @field_validator("as_of_date")
    @classmethod
    def historical_date(cls, value: date | None) -> date | None:
        if value and value > date.today():
            raise ValueError("The source date cannot be in the future")
        return value


class BriefAnalysisRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    privacy_disclosure_version: str


class BriefSourceLifecycleWrite(BaseModel):
    model_config = ConfigDict(extra="forbid")
    archived: bool = Field(strict=True)
    expected_version: int = Field(gt=0, strict=True)


class BriefSourceQuery(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    q: str = Field(default="", max_length=200)
    company_id: int | None = Field(default=None, gt=0)
    source_kind: Literal["text", "pdf"] | None = None
    analysis_status: Literal["not_scanned", "scanning", "failed", "complete"] | None = None
    lifecycle: Literal["active", "archived", "all"] = "active"
    before_id: int | None = Field(default=None, gt=0)
    limit: int = Field(default=20, ge=1, le=50)

    @field_validator("q")
    @classmethod
    def no_nulls(cls, value: str) -> str:
        if "\x00" in value:
            raise ValueError("Search must not contain null characters")
        return value


class ValuationSuggestion(BaseModel):
    model_config = ConfigDict(extra="forbid")
    field: ValuationField
    direction: Literal["increase", "decrease", "review"]
    reason: str = Field(min_length=10, max_length=600)


class BriefFinding(BaseModel):
    model_config = ConfigDict(extra="forbid")
    title: str = Field(min_length=5, max_length=160)
    importance: Literal["high", "medium", "low"]
    importance_reason: str = Field(min_length=10, max_length=600)
    quote: str = Field(min_length=12, max_length=800)
    confidence: Literal["low", "medium", "high"]
    valuation_inputs: list[ValuationSuggestion] = Field(max_length=4)


class BriefAnalysis(BaseModel):
    model_config = ConfigDict(extra="forbid")
    source_marker: str
    summary: str = Field(min_length=10, max_length=1200)
    findings: list[BriefFinding] = Field(min_length=1, max_length=6)


class BriefSourceRead(BaseModel):
    id: int
    company_id: int
    company_name: str
    ticker: str
    title: str
    source_kind: str
    source_url: str | None
    as_of_date: date | None
    source_sha256: str
    created_at: datetime
    archived_at: datetime | None
    lifecycle_version: int
    extraction: dict
    analysis_status: str
    analysis: dict | None
    ai_output_id: int | None
    provider: str | None
    model: str | None
    is_mock: bool
    generated_at: datetime | None
    review_status: str
    warnings: list[str]


class BriefSourcePage(BaseModel):
    items: list[BriefSourceRead]
    next_before_id: int | None
