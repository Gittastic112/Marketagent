"""Operations API contracts, independent of HTTP and persistence."""

from app.schemas.companies import (
    CompanyRead,
)

from app.schemas.evidence import (
    AlertRead,
    EventRead,
)

from app.schemas.portfolio import (
    PortfolioAnalyticsRead,
    PortfolioRead,
    PortfolioSnapshotRead,
)

from app.schemas.research import (
    ThesisNoteRead,
)

from datetime import (
    datetime,
)

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
)

from typing import (
    Any,
    Literal,
)


class RuntimeReadinessRead(BaseModel):
    status: Literal["ready", "blocked"]
    database_status: Literal["ready", "unavailable"]
    schema_status: Literal["ready", "blocked", "unknown"]
    expected_migration_head: str
    current_migration_heads: list[str] = Field(default_factory=list)
    missing_tables: list[str] = Field(default_factory=list)
    missing_columns: list[str] = Field(default_factory=list)
    missing_constraints: list[str] = Field(default_factory=list)
    recovery_steps: list[str] = Field(default_factory=list)


class ProcessingRunRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    request_id: str | None = None
    run_type: str
    source_type: str | None
    source_id: int | None
    company_id: int | None
    started_at: datetime
    finished_at: datetime | None
    status: str
    fetched_count: int
    created_count: int
    skipped_duplicate_count: int
    error_count: int
    error_details_json: dict[str, Any] | None = None
    metadata_json: dict[str, Any] | None = None
    created_at: datetime


class ProviderHealthRead(BaseModel):
    provider_name: str
    capability: str
    requirement_level: Literal["core", "optional", "manual"]
    market: str | None = None
    status: Literal[
        "configured",
        "missing_key",
        "working",
        "running",
        "partial",
        "failing",
        "manual_only",
        "not_configured",
        "unsupported_market",
        "mock",
        "unknown",
    ]
    configured: bool
    last_attempt_at: datetime | None = None
    latest_run_status: str | None = None
    recent_run_count: int = 0
    consecutive_failures: int = 0
    data_age_hours: float | None = None
    freshness_threshold_hours: int | None = None
    configured_source_count: int | None = None
    last_success_at: datetime | None = None
    last_failure_at: datetime | None = None
    failure_reason: str | None = None
    freshness_label: str
    notes: str | None = None
    action_required: str | None = None
    rate_limit_status: str | None = None
    coverage_state: str | None = None


class DashboardOverviewRead(BaseModel):
    companies: list[CompanyRead]
    events: list[EventRead]
    alerts: list[AlertRead]
    thesis_notes: list[ThesisNoteRead]
    daily_brief: dict[str, Any]
    processing_runs: list[ProcessingRunRead]
    default_portfolio: PortfolioRead | None = None
    default_portfolio_snapshot: PortfolioSnapshotRead | None = None
    portfolio_analytics: PortfolioAnalyticsRead | None = None
