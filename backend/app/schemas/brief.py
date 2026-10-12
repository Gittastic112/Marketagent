"""Brief API contracts, independent of HTTP and persistence."""
from app.schemas.brief_context import BriefResearchContext

from datetime import (
    date,
    datetime,
    time,
)

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
    model_validator,
)

from typing import (
    Any,
    Literal,
)

from zoneinfo import (
    ZoneInfo,
    ZoneInfoNotFoundError,
)


class BriefingFiling(BaseModel):
    ticker: str
    form_type: str
    headline: str
    event_id: int
    status: Literal["New", "Unresolved", "Stale", "Reviewed"] = "New"
    raw_document_id: int | None = None
    source_name: str | None = None
    source_url: str | None = None
    source_published_at: datetime | None = None
    event_created_at: datetime | None = None
    claim_type: Literal["Source Summary", "User Assumption"] = "User Assumption"
    evidence_status: Literal["source_linked", "manual"] = "manual"


class BriefingPortfolioExposure(BaseModel):
    portfolio_id: int
    portfolio_name: str


class BriefingPortfolioMove(BaseModel):
    ticker: str
    event_headline: str
    event_id: int
    move_percent: float | None = None
    calculation_status: Literal["complete", "stale", "not_available"] = "not_available"
    claim_type: Literal["Calculation", "Unavailable"] = "Unavailable"
    price_start_date: date | None = None
    price_end_date: date | None = None
    price_currency: str | None = None
    price_provider: str | None = None
    source_market_price_ids: list[int] = Field(default_factory=list)
    affected_portfolios: list[BriefingPortfolioExposure] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    contains_mock_data: bool = False


class BriefingNewSinceReview(BaseModel):
    filings: list[BriefingFiling] = Field(default_factory=list)
    portfolio_moves: list[BriefingPortfolioMove] = Field(default_factory=list)


class BriefingHighMaterialityEvent(BaseModel):
    headline: str
    priority: str
    event_id: int
    priority_score: int | None = None
    ticker: str | None = None
    event_type: str | None = None
    status: Literal["New", "Unresolved", "Stale", "Reviewed"] = "New"
    raw_document_id: int | None = None
    source_name: str | None = None
    source_url: str | None = None
    source_published_at: datetime | None = None
    event_created_at: datetime | None = None
    claim_type: Literal["Source Summary", "User Assumption"] = "User Assumption"
    evidence_status: Literal["source_linked", "manual"] = "manual"


class BriefingThesisContradiction(BaseModel):
    assumption: str
    evidence: str | None = None
    alert_id: int
    event_id: int | None = None
    raw_document_id: int | None = None
    review_status: str = "unreviewed"
    claim_type: Literal["AI Interpretation"] = "AI Interpretation"


class BriefingValuationRelevance(BaseModel):
    event_id: int
    headline: str
    variable: str | None = None
    direction: str | None = None
    reasoning: str | None = None
    confidence: str | None = None
    claim_type: Literal["AI Interpretation"] = "AI Interpretation"
    ai_output_id: int | None = None
    model_name: str | None = None
    prompt_version: str | None = None
    review_status: str = "pending"
    raw_document_id: int | None = None


class BriefingProcessingFailure(BaseModel):
    processing_run_id: int
    run_type: str
    source_type: str | None = None
    status: str
    error_count: int
    started_at: datetime
    finished_at: datetime | None = None
    claim_type: Literal["Fact"] = "Fact"


class BriefingInspectionAction(BaseModel):
    action_id: str
    action_type: Literal[
        "review_contradiction",
        "inspect_processing_failure",
        "add_market_prices",
        "resolve_event_evidence",
    ]
    priority: Literal["high", "medium", "low"]
    title: str
    reason: str
    href: str
    claim_type: Literal["Calculation"] = "Calculation"
    source_event_ids: list[int] = Field(default_factory=list)
    source_raw_document_ids: list[int] = Field(default_factory=list)
    source_market_price_ids: list[int] = Field(default_factory=list)
    source_alert_ids: list[int] = Field(default_factory=list)
    processing_run_id: int | None = None


class DailyBriefPayload(BaseModel):
    private_research: BriefResearchContext | None = None
    summary: str = "Daily brief summary unavailable."
    calculation_status: Literal["complete", "partial", "not_available"] = "not_available"
    valuation_analysis_status: Literal[
        "complete", "partial", "failed", "not_run", "not_required"
    ] = "not_run"
    contradiction_analysis_status: Literal[
        "complete", "partial", "failed", "not_run", "not_required"
    ] = "not_run"
    last_reviewed_at: datetime | None = None
    new_since_last_review: BriefingNewSinceReview = Field(default_factory=BriefingNewSinceReview)
    high_materiality_events: list[BriefingHighMaterialityEvent] = Field(default_factory=list)
    thesis_contradictions: list[BriefingThesisContradiction] = Field(default_factory=list)
    thesis_confirmations: list[Any] = Field(default_factory=list)
    valuation_relevance: list[BriefingValuationRelevance] = Field(default_factory=list)
    processing_failures: list[BriefingProcessingFailure] = Field(default_factory=list)
    inspection_queue: list[BriefingInspectionAction] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    contains_mock_data: bool = False
    contains_stale_data: bool = False
    source_event_ids: list[int] = Field(default_factory=list)
    source_raw_document_ids: list[int] = Field(default_factory=list)
    source_market_price_ids: list[int] = Field(default_factory=list)
    source_alert_ids: list[int] = Field(default_factory=list)


class DailyBriefRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    brief_date: date
    title: str
    summary: str
    payload_json: DailyBriefPayload
    review_status: str
    reviewed_at: datetime | None = None
    created_at: datetime


class DailyBriefScheduleUpdate(BaseModel):
    enabled: bool
    timezone: str = "UTC"
    local_time: time = time(7, 0)
    days_of_week: list[int] = Field(default_factory=lambda: [0, 1, 2, 3, 4])

    @field_validator("timezone")
    @classmethod
    def validate_timezone(cls, value: str) -> str:
        try:
            ZoneInfo(value)
        except ZoneInfoNotFoundError:
            raise ValueError("Timezone must be a valid IANA timezone") from None
        return value

    @field_validator("days_of_week")
    @classmethod
    def validate_days(cls, value: list[int]) -> list[int]:
        if any(day < 0 or day > 6 for day in value):
            raise ValueError("Schedule days must be integers from 0 (Monday) to 6 (Sunday)")
        return sorted(set(value))

    @model_validator(mode="after")
    def validate_enabled_days(self):
        if self.enabled and not self.days_of_week:
            raise ValueError("At least one schedule day is required when scheduling is enabled")
        return self


class DailyBriefScheduleRead(BaseModel):
    id: int
    enabled: bool
    timezone: str
    local_time: time
    days_of_week: list[int]
    next_run_at: datetime | None = None
    due_now: bool
    last_attempted_at: datetime | None = None
    last_succeeded_at: datetime | None = None
    last_status: str
    last_processing_run_id: int | None = None
    last_brief_id: int | None = None
    generation_mode: Literal["deterministic_no_external_ai"]
    created_at: datetime
    updated_at: datetime


class DailyBriefScheduleRunResult(BaseModel):
    schedules_checked: int
    schedules_completed: int
    briefs_created: int
    failures: int
