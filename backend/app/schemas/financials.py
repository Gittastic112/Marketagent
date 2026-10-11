"""Financials API contracts, independent of HTTP and persistence."""

from app.schemas.evidence import (
    DocumentAssetRead,
)

from datetime import (
    date,
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


class FinancialStatementPeriodCreate(BaseModel):
    company_id: int | None = None
    period_type: str
    year: int
    quarter: int | None = None
    report_date: date
    currency: str = "USD"
    currency_source: str = "manual_entry"
    currency_confidence: str = "medium"


class FinancialStatementPeriodUpdate(BaseModel):
    company_id: int | None = None
    period_type: str | None = None
    year: int | None = None
    quarter: int | None = None
    report_date: date | None = None
    currency: str | None = None
    currency_source: str | None = None
    currency_confidence: str | None = None


class FinancialMetricCreate(BaseModel):
    period_id: int | None = None
    metric_name: str
    value: float
    unit: str | None = None


class FinancialMetricUpdate(BaseModel):
    period_id: int | None = None
    metric_name: str | None = None
    value: float | None = None
    unit: str | None = None


class StoredFinancialMetricRead(FinancialMetricCreate):
    model_config = ConfigDict(from_attributes=True)
    id: int
    created_at: datetime
    updated_at: datetime


class FinancialStatementPeriodRead(FinancialStatementPeriodCreate):
    model_config = ConfigDict(from_attributes=True)
    id: int
    created_at: datetime
    updated_at: datetime
    metrics: list[StoredFinancialMetricRead] = Field(default_factory=list)


CandidateReviewStatus = Literal["needs_review", "reviewed", "rejected", "overridden"]


class FinancialCandidateReviewUpdate(BaseModel):
    review_status: CandidateReviewStatus


class FinancialCandidateOverride(BaseModel):
    value: float
    unit: str | None = None


class FinancialExtractionCandidateRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    company_id: int
    raw_document_id: int
    metric_code: str
    reported_label: str
    value: float
    unit: str | None = None
    fiscal_year: int | None = None
    period_type: str
    source_text: str
    source_line_number: int | None = None
    source_page: int | None = None
    source_section: str | None = None
    source_table_name: str | None = None
    source_row_label: str | None = None
    source_column_label: str | None = None
    source_cell_reference: str | None = None
    source_locator_json: dict | None = None
    extraction_warnings: str | None = None
    extraction_method: str
    confidence_label: str
    review_status: str
    created_at: datetime
    updated_at: datetime


class FinancialExtractionResultRead(BaseModel):
    raw_document_id: int
    created_count: int
    skipped_existing_count: int
    candidates: list[FinancialExtractionCandidateRead] = Field(default_factory=list)


class PdfFinancialExtractionResultRead(FinancialExtractionResultRead):
    asset: DocumentAssetRead
    page_count: int
    scanned_page_count: int
    scanned_pages: list[int] = Field(default_factory=list)
    table_count: int
    warnings: list[str] = Field(default_factory=list)


class NormalizedMetricRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    metric_code: str
    value: float
    unit: str | None = None
    provenance_notes: str | None = None
    warnings: str | None = None


class NormalizedSnapshotRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    company_id: int
    period_id: int
    created_at: datetime
    updated_at: datetime
    metrics: list[NormalizedMetricRead] = Field(default_factory=list)


class NormalizedBackfillRequest(BaseModel):
    dry_run: bool = True


class NormalizedCoveragePeriodRead(BaseModel):
    period_id: int
    year: int
    quarter: int | None = None
    period_type: str
    source_metric_count: int
    normalized_metric_count: int
    needs_backfill: bool
    trust_ready: bool
    reasons: list[str] = Field(default_factory=list)
    currency: str
    currency_source: str
    currency_confidence: str
    currency_conflict: str | None = None


class NormalizedCoverageRead(BaseModel):
    status: Literal["no_data", "partial", "blocked", "complete"]
    period_count: int
    normalized_period_count: int
    coverage_percent: float
    trust_ready_period_count: int
    needs_backfill_count: int
    conflict_count: int
    low_confidence_currency_count: int
    stale_snapshot_count: int
    missing_snapshot_count: int
    periods: list[NormalizedCoveragePeriodRead] = Field(default_factory=list)
    recommended_actions: list[str] = Field(default_factory=list)


class NormalizedBackfillRead(BaseModel):
    dry_run: bool
    examined_count: int
    eligible_count: int
    normalized_count: int
    eligible_periods: list[NormalizedCoveragePeriodRead] = Field(default_factory=list)
    skipped_conflicts: list[dict[str, Any]] = Field(default_factory=list)
    coverage_before: NormalizedCoverageRead
    coverage_after: NormalizedCoverageRead | None = None


class FinancialReconciliationItemRead(BaseModel):
    metric_code: str
    source_metric_code: str | None = None
    status: Literal["exact", "mismatch", "missing_normalized", "normalized_only"]
    source_value: float | None = None
    normalized_value: float | None = None
    delta: float | None = None
    delta_percent: float | None = None
    source_unit: str | None = None
    normalized_unit: str | None = None
    provenance_notes: str | None = None
    warnings: str | None = None


class FinancialReconciliationPeriodRead(BaseModel):
    period_id: int
    snapshot_id: int | None = None
    year: int
    quarter: int | None = None
    period_type: str
    status: Literal["partial", "blocked", "complete"]
    items: list[FinancialReconciliationItemRead] = Field(default_factory=list)


class FinancialReconciliationRead(BaseModel):
    status: Literal["no_data", "partial", "blocked", "complete"]
    period_count: int
    item_count: int
    exact_count: int
    mismatch_count: int
    missing_normalized_count: int
    normalized_only_count: int
    periods: list[FinancialReconciliationPeriodRead] = Field(default_factory=list)
    recommended_actions: list[str] = Field(default_factory=list)


class FinancialStatementIdentityCheckRead(BaseModel):
    identity_code: str
    label: str
    formula: str
    status: Literal["passed", "failed", "not_available"]
    actual_value: float | None = None
    expected_value: float | None = None
    delta: float | None = None
    tolerance: float | None = None
    unit: str
    inputs: dict[str, float] = Field(default_factory=dict)
    missing_metrics: list[str] = Field(default_factory=list)
    ambiguous_metrics: list[str] = Field(default_factory=list)
    blocking: bool


class FinancialStatementIdentityPeriodRead(BaseModel):
    period_id: int
    year: int
    quarter: int | None = None
    period_type: str
    report_date: date
    currency: str
    status: Literal["passed", "partial", "failed", "not_available"]
    applicable_check_count: int
    passed_check_count: int
    failed_check_count: int
    unavailable_check_count: int
    checks: list[FinancialStatementIdentityCheckRead] = Field(default_factory=list)


class FinancialStatementIdentityReportRead(BaseModel):
    company_id: int
    period_type: str
    status: Literal["passed", "partial", "failed", "not_available"]
    tolerance_contract: dict[str, Any]
    period_count: int
    applicable_period_count: int
    passed_period_count: int
    partial_period_count: int
    failed_period_count: int
    unavailable_period_count: int
    applicable_check_count: int
    passed_check_count: int
    failed_check_count: int
    unavailable_check_count: int
    periods: list[FinancialStatementIdentityPeriodRead] = Field(default_factory=list)
