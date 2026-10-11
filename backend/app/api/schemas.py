"""Legacy HTTP schema facade. New valuation contracts live in app.schemas.

Keep re-exports compatible; add valuation fields in their owning contract module.
"""
from app.schemas.valuation_inputs import (
    ValuationModelCreate,
    ValuationModelUpdate,
    ValuationCompanyContextRead,
    DcfAssumptionSetCreate,
    DcfAssumptionSetWrite,
    DcfAssumptionVersionWrite,
    DcfAssumptionSetUpdate,
    ReverseDcfRequest,
    QuickValuationAssumptionsRequest,
    QuickValuationCalculateRequest,
    ValuationSetupDraftUpdate,
    ValuationSetupDraftCommand,
    ValuationSetupDraftReset,
    ValuationSetupDraftPromote,
)
from app.schemas.valuation_outputs import (
    DiagnosticWarning,
    DcfOutputCreate,
    ReverseDcfResponse,
    QuickValuationProjectionRead,
    QuickValuationOutputRead,
    DcfProjectionYearRead,
    DcfSensitivityTableRead,
    DcfDecisionLogRead,
    ValuationAssumptionChangeLogCreate,
    ValuationAssumptionChangeLogRead,
)
from app.schemas.valuation import (
    DcfOutputRead,
    QuickValuationAssumptionsRead,
    DcfAssumptionSetRead,
    ValuationModelRead,
    ValuationModelSummaryRead,
    ValuationSetupDraftRead,
    DcfScenarioOutput,
)

from app.schemas.portfolio import (
    PortfolioCreate,
    PortfolioUpdate,
    PortfolioRead,
    PortfolioBenchmarkConfigCreate,
    PortfolioBenchmarkConfigUpdate,
    PortfolioBenchmarkConfigRead,
    PortfolioHoldingCreate,
    PortfolioHoldingUpdate,
    PortfolioHoldingRead,
    PortfolioTransactionType,
    PortfolioTransactionCreate,
    PortfolioTransactionUpdate,
    PortfolioTransactionRead,
    PortfolioCashBalanceCreate,
    PortfolioCashBalanceUpdate,
    PortfolioCashBalanceRead,
    PortfolioSnapshotCreate,
    PortfolioSnapshotUpdate,
    PortfolioSnapshotRead,
    PortfolioValuationHoldingRead,
    PortfolioCashValuationRead,
    PortfolioValuationRead,
    PortfolioAttributionComponent,
    PortfolioTransactionActivityRead,
    PortfolioAttributionRead,
    PortfolioReturnMetricRead,
    PortfolioPerformanceRead,
    PortfolioPeriodHoldingAttributionRead,
    PortfolioPeriodAttributionRead,
    PortfolioOpportunityCostRead,
    PortfolioRiskReturnHoldingRead,
    PortfolioRiskReturnRead,
    PortfolioRealInputReadinessCheck,
    PortfolioRealInputReadinessRead,
    PortfolioAnalyticsRead,
)

from datetime import date, datetime, time
from typing import Any, Literal
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from pydantic import BaseModel, ConfigDict, Field, HttpUrl, field_validator, model_validator

from app.schemas.common import ApiErrorDetail, ApiMeta, ApiResponse


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


class ScoringConfigUpdate(BaseModel):
    weight_credibility: float | None = None
    weight_novelty: float | None = None
    weight_impact: float | None = None
    weight_speed: float | None = None

class FredIngestionCreate(BaseModel):
    series_id: str = Field(min_length=1, max_length=50)

class FredIngestionRead(BaseModel):
    series_id: str
    macro_series_id: int
    processing_run_id: int
    source_url: str
    observations_fetched: int
    observations_created: int
    observations_skipped_duplicate: int
    observations_skipped_missing: int
    observations_rejected: int


class ScoringConfigRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    weight_credibility: float
    weight_novelty: float
    weight_impact: float
    weight_speed: float


class MacroObservationCreate(BaseModel):
    date_recorded: date
    value: float

class MacroObservationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    series_id: int
    date_recorded: date
    value: float

class MacroSeriesCreate(BaseModel):
    name: str
    description: str | None = None
    units: str | None = None
    frequency: str | None = None

class MacroSeriesRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    description: str | None
    units: str | None
    frequency: str | None
    provider_name: str | None = None
    source_url: str | None = None
    observations: list[MacroObservationRead] = []

class ExposureTagCreate(BaseModel):
    name: str
    description: str | None = None

class ExposureTagRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    description: str | None

class CompanyCreate(BaseModel):
    ticker: str
    name: str
    sector: str | None = None
    industry: str | None = None
    damodaran_industry: str | None = None
    exchange: str | None = None
    market: str | None = None
    primary_exchange: str | None = None
    local_symbol: str | None = None
    isin: str | None = None
    figi: str | None = None
    regulatory_id: str | None = None
    regulatory_id_type: str | None = None
    cik: str | None = None
    aliases_json: list[str] | None = None
    country: str | None = None
    region: str | None = None
    currency: str | None = None
    asset_type: str | None = None
    security_type: str | None = None
    market_cap_category: str | None = None
    is_etf: bool = False
    etf_provider: str | None = None
    active: bool = True


class CompanyUpdate(BaseModel):
    ticker: str | None = None
    name: str | None = None
    sector: str | None = None
    industry: str | None = None
    damodaran_industry: str | None = None
    exchange: str | None = None
    market: str | None = None
    primary_exchange: str | None = None
    local_symbol: str | None = None
    isin: str | None = None
    figi: str | None = None
    regulatory_id: str | None = None
    regulatory_id_type: str | None = None
    cik: str | None = None
    aliases_json: list[str] | None = None
    country: str | None = None
    region: str | None = None
    currency: str | None = None
    asset_type: str | None = None
    security_type: str | None = None
    market_cap_category: str | None = None
    is_etf: bool | None = None
    etf_provider: str | None = None
    active: bool | None = None


class CompanyRead(CompanyCreate):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    updated_at: datetime
    exposure_tags: list[ExposureTagRead] = []

class IndustryMappingUpdate(BaseModel):
    industry_name: str


class IndustryAllocationInput(BaseModel):
    segment_name: str = Field(min_length=1, max_length=120)
    industry_name: str = Field(min_length=1, max_length=255)
    weight_percent: float = Field(gt=0, le=100)


class CompanyIndustryMixUpdate(BaseModel):
    basis: Literal["revenue"] = "revenue"
    as_of_date: date | None = None
    source_document_id: int | None = None
    notes: str | None = Field(default=None, max_length=1000)
    allocations: list[IndustryAllocationInput] = Field(min_length=1, max_length=20)

    @model_validator(mode="after")
    def validate_mix(self):
        labels = [allocation.segment_name.strip().casefold() for allocation in self.allocations]
        if len(labels) != len(set(labels)):
            raise ValueError("Segment labels must be unique")
        total = sum(allocation.weight_percent for allocation in self.allocations)
        if abs(total - 100.0) > 0.01:
            raise ValueError(f"Industry weights must total 100%; received {total:.4f}%")
        return self


class IndustryAllocationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    segment_name: str
    industry_name: str
    weight_percent: float
    benchmark_availability: dict[str, bool] = Field(default_factory=dict)
    created_at: datetime
    updated_at: datetime


class CompanyIndustryMixRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    company_id: int
    basis: str
    as_of_date: date | None
    source_document_id: int | None
    notes: str | None
    primary_industry: str
    total_weight_percent: float
    claim_type: Literal["User Assumption"] = "User Assumption"
    coverage_status: Literal["complete", "partial", "unavailable"]
    benchmark_field_coverage: dict[str, dict[str, bool]]
    warnings: list[str] = Field(default_factory=list)
    allocations: list[IndustryAllocationRead]
    created_at: datetime
    updated_at: datetime


class CompanyLookupRead(BaseModel):
    market: str
    primary_exchange: str | None = None
    ticker: str
    local_symbol: str
    name: str
    currency: str
    country: str
    regulatory_id: str | None = None
    regulatory_id_type: str | None = None
    cik: str | None = None
    isin: str | None = None
    source: str
    warnings: list[str] = Field(default_factory=list)


class SourceCreate(BaseModel):
    name: str
    source_type: str
    base_url: str | None = None
    reliability_score: int | None = None
    active: bool = True


class SourceUpdate(BaseModel):
    name: str | None = None
    source_type: str | None = None
    base_url: str | None = None
    reliability_score: int | None = None
    active: bool | None = None


class SourceRead(SourceCreate):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    updated_at: datetime


class SourceCapabilityRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    market: str
    source_type: str
    provider_name: str
    capability: str
    status: Literal["available", "manual_only", "not_configured", "not_supported"]
    requires_api_key: bool
    freshness_expected_seconds: int | None = None
    notes: str | None = None
    updated_at: datetime


class CountryMarketContextManualCreate(BaseModel):
    market: str
    country: str
    currency: str
    risk_free_rate: float | None = None
    risk_free_rate_source: str | None = None
    equity_risk_premium: float | None = None
    country_risk_premium: float | None = None
    inflation_rate: float | None = None
    fx_rate_to_usd: float | None = None
    as_of_date: date | None = None
    notes: str | None = None


class CountryMarketContextRead(CountryMarketContextManualCreate):
    model_config = ConfigDict(from_attributes=True)

    id: int
    is_manual: bool
    created_at: datetime
    updated_at: datetime


class RiskFreeRateRead(BaseModel):
    market: str
    country: str
    currency: str
    risk_free_rate: float
    risk_free_rate_source: str
    as_of_date: date | None = None
    is_manual: bool
    warnings: list[str] = Field(default_factory=list)


class RawDocumentCreate(BaseModel):
    company_id: int | None = None
    source_id: int
    document_type: str
    title: str
    url: str | None = None
    published_at: datetime | None = None
    raw_text: str | None = None
    raw_payload_json: dict[str, Any] | None = None
    content_hash: str


class RawDocumentUpdate(BaseModel):
    company_id: int | None = None
    source_id: int | None = None
    document_type: str | None = None
    title: str | None = None
    url: str | None = None
    published_at: datetime | None = None
    raw_text: str | None = None
    raw_payload_json: dict[str, Any] | None = None
    content_hash: str | None = None


class RawDocumentRead(RawDocumentCreate):
    model_config = ConfigDict(from_attributes=True)

    id: int
    ingested_at: datetime
    created_at: datetime


class RawDocumentSummaryRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    company_id: int | None
    source_id: int
    document_type: str
    title: str
    url: str | None
    published_at: datetime | None
    content_hash: str
    ingested_at: datetime
    created_at: datetime
    has_raw_text: bool


class DocumentAssetRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    raw_document_id: int
    original_filename: str
    mime_type: str
    size_bytes: int
    sha256: str
    page_count: int
    created_at: datetime


class EventCreate(BaseModel):
    company_id: int | None = None
    raw_document_id: int | None = None
    event_type: str
    information_speed: str
    title: str
    description: str | None = None
    event_time: datetime | None = None
    credibility_score: int | None = None
    novelty_score: int | None = None
    impact_score: int | None = None
    priority_score: int | None = None
    score_explanation_json: dict[str, Any] | None = None


class EventUpdate(BaseModel):
    company_id: int | None = None
    raw_document_id: int | None = None
    event_type: str | None = None
    information_speed: str | None = None
    title: str | None = None
    description: str | None = None
    event_time: datetime | None = None
    credibility_score: int | None = None
    novelty_score: int | None = None
    impact_score: int | None = None
    priority_score: int | None = None
    score_explanation_json: dict[str, Any] | None = None


class EventLinkSummaryRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    event_type: str


class EventRead(EventCreate):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    corroborates: list[EventLinkSummaryRead] = Field(default_factory=list)
    contradicts: list[EventLinkSummaryRead] = Field(default_factory=list)


class EventLinkCreate(BaseModel):
    target_event_id: int


class EventEvidenceReferenceCreate(BaseModel):
    raw_document_id: int
    locator_type: Literal["text_span", "pdf_region", "section", "xbrl_fact"]
    source_page: int | None = Field(default=None, ge=1)
    source_section: str | None = Field(default=None, max_length=500)
    start_char: int | None = Field(default=None, ge=0)
    end_char: int | None = Field(default=None, gt=0)
    quote: str | None = Field(default=None, max_length=2_000)
    bounding_box_json: dict[str, Any] | None = None
    source_metadata_json: dict[str, Any] | None = None
    confidence_label: Literal["high", "medium", "low"] = "high"

    @model_validator(mode="after")
    def validate_locator(self):
        if self.locator_type == "text_span":
            if self.start_char is None or self.end_char is None or not self.quote:
                raise ValueError("text_span requires start_char, end_char, and quote")
            if self.end_char <= self.start_char:
                raise ValueError("end_char must be greater than start_char")
        if self.locator_type == "pdf_region":
            if self.source_page is None:
                raise ValueError("pdf_region requires source_page")
        if self.locator_type == "section" and not self.source_section:
            raise ValueError("section requires source_section")
        return self


class EventEvidenceReferenceRead(EventEvidenceReferenceCreate):
    model_config = ConfigDict(from_attributes=True)

    id: int
    event_id: int
    created_by_user_id: str | None = None
    origin: str
    pdf_region_status: Literal["valid", "invalid", "not_applicable"] = "not_applicable"
    created_at: datetime


class EventEvidenceSearchMatchRead(BaseModel):
    occurrence_index: int
    start_char: int
    end_char: int
    context_before: str
    quote: str
    context_after: str


class EventEvidenceResolutionSearchRead(BaseModel):
    event_id: int
    company_id: int | None
    raw_document_id: int
    event_title: str
    document_title: str
    document_content_hash: str
    query: str
    exact_match_count: int
    returned_match_count: int
    is_truncated: bool
    existing_reference_count: int
    matches: list[EventEvidenceSearchMatchRead]
    limitations: list[str]


class EventEvidenceResolutionCreate(BaseModel):
    raw_document_id: int = Field(gt=0)
    start_char: int = Field(ge=0)
    end_char: int = Field(gt=0)
    quote: str = Field(min_length=8, max_length=300)
    search_query: str = Field(min_length=8, max_length=300)
    occurrence_index: int = Field(ge=1)
    document_content_hash: str = Field(min_length=1, max_length=128)

    @model_validator(mode="after")
    def validate_exact_resolution(self):
        if self.end_char <= self.start_char:
            raise ValueError("end_char must be greater than start_char")
        if self.end_char - self.start_char != len(self.quote):
            raise ValueError("Evidence offsets must match the exact quote length")
        if self.quote != self.search_query:
            raise ValueError("The selected quote must equal the exact search query")
        return self


ReviewStatus = Literal["unreviewed", "useful", "not_useful", "false_positive", "needs_follow_up"]


class AlertCreate(BaseModel):
    event_id: int | None = None
    company_id: int | None = None
    alert_type: str
    severity: str = "low"
    title: str
    summary: str | None = None
    why_it_matters: str | None = None
    what_changed: str | None = None
    evidence: str | None = None
    confidence_bucket: str = "low"
    review_status: ReviewStatus = "unreviewed"
    review_notes: str | None = None


class AlertUpdate(BaseModel):
    event_id: int | None = None
    company_id: int | None = None
    alert_type: str | None = None
    severity: str | None = None
    title: str | None = None
    summary: str | None = None
    why_it_matters: str | None = None
    what_changed: str | None = None
    evidence: str | None = None
    confidence_bucket: str | None = None
    review_status: ReviewStatus | None = None
    review_notes: str | None = None


class AlertPortfolioImpactCreate(BaseModel):
    alert_id: int
    portfolio_id: int
    exposure_amount: float = 0.0
    impact_score: float = 0.0


class AlertPortfolioImpactRead(AlertPortfolioImpactCreate):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime


class AlertRead(AlertCreate):
    model_config = ConfigDict(from_attributes=True)

    id: int
    portfolio_priority_score: float
    reviewed_at: datetime | None = None
    created_at: datetime
    portfolio_impacts: list[AlertPortfolioImpactRead] = Field(default_factory=list)


class ThesisNoteCreate(BaseModel):
    company_id: int
    title: str
    thesis_text: str
    assumptions_json: dict[str, Any] | None = None
    status: str = "active"


class ThesisNoteUpdate(BaseModel):
    company_id: int | None = None
    title: str | None = None
    thesis_text: str | None = None
    assumptions_json: dict[str, Any] | None = None
    status: str | None = None


class ThesisAssumptionCreate(BaseModel):
    thesis_note_id: int
    description: str
    original_confidence: str = "medium"
    current_confidence: str = "medium"


class ThesisAssumptionUpdate(BaseModel):
    description: str | None = None
    original_confidence: str | None = None
    current_confidence: str | None = None


class EventThesisImpactCreate(BaseModel):
    event_id: int
    thesis_assumption_id: int
    impact_classification: str
    rationale: str

class EventThesisImpactRead(EventThesisImpactCreate):
    model_config = ConfigDict(from_attributes=True)
    id: int
    created_at: datetime

class ThesisAssumptionRead(ThesisAssumptionCreate):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    updated_at: datetime
    impacts: list[EventThesisImpactRead] = Field(default_factory=list)


class ThesisChangeCreate(BaseModel):
    thesis_note_id: int
    change_summary: str
    drift_score: float = 0.0


class ThesisChangeRead(ThesisChangeCreate):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime


class ThesisNoteRead(ThesisNoteCreate):
    model_config = ConfigDict(from_attributes=True)

    id: int
    thesis_drift_score: float
    created_at: datetime
    updated_at: datetime
    assumptions: list[ThesisAssumptionRead] = Field(default_factory=list)
    changes: list[ThesisChangeRead] = Field(default_factory=list)


class SocialPostCreate(BaseModel):
    platform: str
    source_url: str
    author: str | None = None
    raw_text: str
    published_at: datetime | None = None
    payload_json: dict[str, Any] | list[Any] | None = None


class SocialPostUpdate(BaseModel):
    platform: str | None = None
    source_url: str | None = None
    author: str | None = None
    raw_text: str | None = None
    published_at: datetime | None = None
    payload_json: dict[str, Any] | list[Any] | None = None


class SocialPostRead(SocialPostCreate):
    model_config = ConfigDict(from_attributes=True)

    id: int
    content_hash: str
    created_at: datetime
    updated_at: datetime


class SentimentScoreCreate(BaseModel):
    post_id: int | None = None
    company_id: int | None = None
    score: str
    rationale: str | None = None


class SentimentScoreUpdate(BaseModel):
    post_id: int | None = None
    company_id: int | None = None
    score: str | None = None
    rationale: str | None = None


class SentimentScoreRead(SentimentScoreCreate):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime


class NarrativeClusterCreate(BaseModel):
    name: str
    description: str | None = None


class NarrativeClusterUpdate(BaseModel):
    name: str | None = None
    description: str | None = None


class NarrativeClusterRead(NarrativeClusterCreate):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    updated_at: datetime


class NarrativeClaimCreate(BaseModel):
    cluster_id: int
    claim_text: str


class NarrativeClaimUpdate(BaseModel):
    cluster_id: int | None = None
    claim_text: str | None = None


class NarrativeClaimRead(NarrativeClaimCreate):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime


class NarrativeMentionCreate(BaseModel):
    cluster_id: int
    event_id: int
    context_text: str | None = None


class NarrativeMentionUpdate(BaseModel):
    cluster_id: int | None = None
    event_id: int | None = None
    context_text: str | None = None


class NarrativeMentionRead(NarrativeMentionCreate):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime


class FxRateObservationCreate(BaseModel):
    base_currency: str = Field(min_length=3, max_length=10)
    quote_currency: str = Field(min_length=3, max_length=10)
    rate: float = Field(gt=0)
    as_of_date: date
    provider_name: str = Field(default="manual", min_length=1, max_length=80)
    provider_symbol: str | None = Field(default=None, max_length=80)
    source_url: str | None = Field(default=None, max_length=1000)
    source_timestamp: datetime | None = None

    @field_validator("base_currency", "quote_currency")
    @classmethod
    def normalize_currency(cls, value: str) -> str:
        return value.strip().upper()

    @field_validator("provider_name")
    @classmethod
    def normalize_fx_provider(cls, value: str) -> str:
        return value.strip()

    @model_validator(mode="after")
    def validate_pair(self):
        if self.base_currency == self.quote_currency:
            raise ValueError("FX base and quote currencies must differ")
        return self


class FxRateObservationRead(FxRateObservationCreate):
    model_config = ConfigDict(from_attributes=True)

    id: int
    claim_type: str
    import_run_id: int | None = None
    observed_at: datetime
    created_at: datetime


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


class CompanySetupStartRequest(BaseModel):
    company_id: int


class CompanySetupStepUpdate(BaseModel):
    current_step: str | None = None
    identity_status: str | None = None
    source_status: str | None = None
    filing_status: str | None = None
    financial_extraction_status: str | None = None
    industry_mapping_status: str | None = None
    valuation_readiness_status: str | None = None
    security_review_status: str | None = None


class CompanySetupSourceReadiness(BaseModel):
    provider_name: str
    capability: str
    market: str
    status: str
    notes: str
    action_required: str | None = None


class CompanySetupIdentityResolution(BaseModel):
    company_id: int
    market: str
    ticker: str
    local_symbol: str | None = None
    primary_exchange: str | None = None
    regulatory_id: str | None = None
    regulatory_id_type: str | None = None
    cik: str | None = None
    confidence_label: str
    missing_identifiers: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


class CompanySetupWorkflowRead(BaseModel):
    id: int
    company_id: int
    current_step: str
    identity_status: str
    source_status: str
    filing_status: str
    financial_extraction_status: str
    industry_mapping_status: str
    valuation_readiness_status: str
    security_review_status: str
    source_readiness: list[CompanySetupSourceReadiness] = Field(default_factory=list)
    next_recommended_step: str
    created_at: datetime
    updated_at: datetime


class RssIngestionCreate(BaseModel):
    source_id: int
    company_id: int | None = None
    rss_xml: str | None = None
    feed_url: str | None = None


class RssIngestionRead(BaseModel):
    fetched_count: int
    created_count: int
    skipped_duplicate_count: int
    error_count: int = 0
    errors: list[str] = Field(default_factory=list)
    created: int
    skipped_duplicates: int
    events_created: int = 0
    events_skipped_existing: int = 0
    alerts_created: int = 0
    alerts_skipped_existing: int = 0
    alerts_skipped_below_threshold: int = 0


class RssBatchIngestionRead(RssIngestionRead):
    source_count: int = 0


class SecFilingMetadataCreate(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    accession_number: str
    form_type: str
    filing_date: date
    report_date: date | None = None
    primary_document: str | None = None
    filing_url: str | None = None


class FilingDiscoveryRead(BaseModel):
    company_id: int
    market: str
    provider_name: str
    mode: Literal["automated", "manual"]
    manual_required: bool
    filings: list[SecFilingMetadataCreate] = Field(default_factory=list)
    next_action: str


class SecFilingIngestionCreate(BaseModel):
    source_id: int | None = None
    company_id: int
    filings: list[SecFilingMetadataCreate] = Field(default_factory=list)
    form_types: list[str] = Field(default_factory=lambda: ["10-K", "10-Q", "8-K"])
    filing_year: int | None = None
    limit: int = 40
    download_text: bool = False


class SecFilingIngestionRead(BaseModel):
    fetched_count: int
    created_count: int
    skipped_duplicate_count: int
    error_count: int = 0
    errors: list[str] = Field(default_factory=list)
    created: int
    skipped_duplicates: int
    events_created: int = 0
    events_skipped_existing: int = 0
    alerts_created: int = 0
    alerts_skipped_existing: int = 0
    alerts_skipped_below_threshold: int = 0


class EventExtractionRead(BaseModel):
    created: int
    skipped_existing: int


class AlertGenerationRead(BaseModel):
    created: int
    skipped_existing: int
    skipped_below_threshold: int


class MarketPriceCreate(BaseModel):
    company_id: int | None = None
    ticker: str
    price: float = Field(ge=0)
    currency: str = "USD"
    as_of_date: date


class MarketPriceUpdate(BaseModel):
    company_id: int | None = None
    ticker: str | None = None
    price: float | None = Field(default=None, ge=0)
    currency: str | None = None
    as_of_date: date | None = None


class MarketPriceRead(MarketPriceCreate):
    model_config = ConfigDict(from_attributes=True)

    id: int
    provider_name: str
    provider_symbol: str | None = None
    source_url: str | None = None
    market: str | None = None
    exchange: str | None = None
    source_timestamp: datetime | None = None
    observed_at: datetime
    price_type: str
    claim_type: str
    import_run_id: int | None = None
    delay_minutes: int | None = None
    adjustment_state: str
    warnings: list[str] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime


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


class EvidenceIntegrityIssueRead(BaseModel):
    code: str
    severity: Literal["error", "warning"]
    entity_type: Literal[
        "document",
        "asset",
        "evidence_reference",
        "financial_candidate",
        "financial_history",
    ]
    entity_id: int
    message: str
    action: str
    company_id: int | None = None
    document_id: int | None = None
    reference_id: int | None = None


class FinancialHistoryIntegrityRead(BaseModel):
    label: str | None = None
    company_id: int
    company: str
    market: str
    eligible_for_certification: bool
    failures: list[str] = Field(default_factory=list)
    limitations: list[str] = Field(default_factory=list)
    period_count: int
    source_document_count: int
    reviewed_evidence_count: int
    uncovered_core_metrics_by_year: dict[int, list[str]] = Field(default_factory=dict)
    coverage_status: str
    reconciliation_status: str
    statement_identity_status: Literal["passed", "partial", "failed", "not_available"]
    statement_identity_check_count: int
    statement_identity_failed_count: int


class EvidenceIntegrityReportRead(BaseModel):
    status: Literal["healthy", "issues_found"]
    verification_scope: Literal["metadata", "deep"]
    asset_content_verification_status: Literal["not_run", "checked"]
    limitations: list[str] = Field(default_factory=list)
    checked_documents: int
    checked_assets: int
    checked_references: int
    checked_financial_candidates: int
    checked_financial_periods: int
    financial_history_candidate_count: int
    certified_financial_history_count: int
    certified_markets: list[str]
    financial_certification_status: Literal["passed", "partial", "blocked", "not_available"]
    financial_histories: list[FinancialHistoryIntegrityRead]
    error_count: int
    warning_count: int
    reported_issue_count: int
    is_truncated: bool
    checked_at: datetime
    issues: list[EvidenceIntegrityIssueRead]


class PeerReviewReceiptHealthItemRead(BaseModel):
    peer_set_id: int
    company_id: int
    name: str
    version: int
    review_status: Literal["reviewed"]
    receipt_status: Literal["missing", "stale", "current"]
    blockers: list[str]
    usable_methods: list[str]
    current_diagnostics_as_of: date
    receipt_diagnostics_as_of: date | None = None
    current_warning_codes: list[str]
    acknowledged_warning_codes: list[str]
    action: str


class PeerReviewReceiptHealthRead(BaseModel):
    status: Literal["healthy", "attention_required"]
    scope: Literal["page"]
    total_owned_set_count: int
    after_id: int
    limit: int
    has_more: bool
    next_after_id: int | None
    checked_set_count: int
    active_reviewed_set_count: int
    ready_for_valuation_count: int
    missing_receipt_count: int
    stale_receipt_count: int
    storage_blocked_count: int
    coverage_blocked_count: int
    draft_set_count: int
    archived_set_count: int
    sets_requiring_attention: list[PeerReviewReceiptHealthItemRead]
    generated_at: datetime


class DamodaranCoverageRowRead(BaseModel):
    source_filename: str
    canonical_path: str
    source_type: str
    metric_family: str
    geography: str
    source_as_of: str
    date_confidence: Literal["high", "medium", "low"]
    catalog_status: Literal["active", "historical_only"]
    claim_type: Literal["Source Summary"]
    implementation_status: Literal["supported", "partial", "unsupported"]
    ingestion_available: bool
    ingestion_status: Literal["ingested", "metadata_only", "not_ingested", "source_missing"]
    source_present: bool
    metadata_import_count: int
    typed_record_count: int
    stored_version_count: int
    active_version_id: int | None
    active_source_sha256: str | None
    active_source_as_of: str | None
    active_date_confidence: Literal["high", "medium", "low", "unknown"] | None
    active_import_kind: str | None
    active_row_count: int | None
    mirror_source_sha256: str | None
    hash_matches_mirror: bool | None
    provenance_status: Literal[
        "complete",
        "partial",
        "missing",
        "not_available",
        "hash_mismatch",
    ]
    freshness_status: Literal[
        "current",
        "stale",
        "historical",
        "unknown",
        "user_assumed_recent",
    ]
    destination_tables: list[str]
    supported_metrics: list[str]
    missing_metrics: list[str]
    limitations: list[str]
    action_required: str


class DamodaranCoverageReportRead(BaseModel):
    inventory_version: str
    generated_at: datetime
    source_count: int
    source_present_count: int
    supported_count: int
    partial_count: int
    unsupported_count: int
    ingested_count: int
    metadata_only_count: int
    not_ingested_count: int
    source_missing_count: int
    current_count: int
    stale_count: int
    historical_count: int
    unknown_date_count: int
    user_assumed_recent_count: int
    typed_record_count: int
    provenance_complete_count: int
    provenance_partial_count: int
    provenance_missing_count: int
    provenance_hash_mismatch_count: int
    warnings: list[str]
    limitations: list[str]
    rows: list[DamodaranCoverageRowRead]


EventEvidenceBackfillStatus = Literal[
    "eligible",
    "applied",
    "missing_document",
    "missing_source_text",
    "missing_candidate_claim",
    "no_exact_match",
    "ambiguous_match",
    "conflicting_exact_matches",
    "race_skipped_existing_reference",
    "race_skipped_event_missing",
]


class EventEvidenceBackfillEntryRead(BaseModel):
    event_id: int
    company_id: int | None
    raw_document_id: int | None
    event_title: str
    priority_score: int | None
    status: EventEvidenceBackfillStatus
    claim_origin: str | None = None
    quote: str | None = None
    start_char: int | None = None
    end_char: int | None = None
    occurrence_count: int
    action: str


class EventEvidenceBackfillReportRead(BaseModel):
    dry_run: bool
    processing_run_id: int | None
    checked_event_count: int
    eligible_count: int
    applied_count: int
    race_skipped_count: int
    status_counts: dict[str, int]
    generated_at: datetime
    limitations: list[str]
    entries: list[EventEvidenceBackfillEntryRead]


class EventEvidenceBackfillRequest(BaseModel):
    dry_run: bool = True
    limit: int = Field(default=100, ge=1, le=200)
    event_ids: list[int] | None = Field(default=None, min_length=1, max_length=100)

    @model_validator(mode="after")
    def validate_event_ids(self):
        if self.event_ids and len(self.event_ids) != len(set(self.event_ids)):
            raise ValueError("event_ids must not contain duplicates")
        return self


class SourceFactRevisionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    company_id: int
    raw_document_id: int
    financial_candidate_id: int
    fact_key: str
    value: float
    unit: str | None = None
    period_type: str
    effective_at: date
    observed_at: datetime
    superseded_at: datetime | None = None
    revision_number: int
    claim_type: Literal["Fact"]
    created_at: datetime


SearchResultType = Literal[
    "document",
    "event",
    "alert",
    "thesis",
    "decision",
    "valuation",
    "narrative",
    "research_session",
    "research_message",
    "ai_output",
]
SearchClaimType = Literal["Fact", "Source Summary", "User Assumption", "AI Interpretation"]
SearchScope = Literal["shared", "private"]
SearchReviewStatus = Literal["not_applicable", "approved"]


class EvidenceSearchResultRead(BaseModel):
    result_type: SearchResultType
    record_id: int
    company_id: int | None = None
    title: str
    excerpt: str | None = None
    rank: float
    claim_type: SearchClaimType
    scope: SearchScope
    review_status: SearchReviewStatus = "not_applicable"
    is_mock: bool = False
    source_name: str | None = None
    source_timestamp: datetime | None = None
    href: str
    locator: dict[str, Any] | None = None


class IntelligenceReviewItemRead(BaseModel):
    item_type: Literal["contradiction", "filing_language_change"]
    item_id: str
    company_id: int | None = None
    title: str
    summary: str
    severity: Literal["low", "medium", "high"]
    claim_type: Literal["User Assumption", "Calculation"]
    source_event_id: int | None = None
    target_event_id: int | None = None
    current_document_id: int | None = None
    prior_document_id: int | None = None
    section_name: str | None = None
    added_words: int | None = None
    removed_words: int | None = None
    evidence_href: str
    source_timestamp: datetime


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


EvidenceClaimType = Literal[
    "Fact",
    "Source Summary",
    "Calculation",
    "User Assumption",
    "AI Interpretation",
    "Estimate",
    "Mock Data",
]
EvidenceStatus = Literal["complete", "partial", "missing"]
EvidenceLocatorPrecision = Literal["document", "page", "region", "section", "span", "none"]


class EvidenceAlertSummaryRead(BaseModel):
    id: int
    event_id: int | None
    company_id: int | None
    alert_type: str
    severity: str
    title: str
    summary: str | None
    why_it_matters: str | None
    confidence_bucket: str
    created_at: datetime


class EvidenceEventSummaryRead(BaseModel):
    id: int
    company_id: int | None
    raw_document_id: int | None
    event_type: str
    information_speed: str
    title: str
    description: str | None
    event_time: datetime | None
    credibility_score: int | None
    priority_score: int | None
    created_at: datetime


class EvidenceCompanySummaryRead(BaseModel):
    id: int
    ticker: str
    name: str
    market: str
    primary_exchange: str | None


class EvidenceSourceSummaryRead(BaseModel):
    id: int
    name: str
    source_type: str
    reliability_score: int | None
    active: bool


class EvidenceDocumentSummaryRead(BaseModel):
    id: int
    company_id: int | None
    source_id: int
    document_type: str
    title: str
    url: str | None
    published_at: datetime | None
    ingested_at: datetime
    content_hash: str
    has_raw_text: bool
    has_asset: bool
    asset_page_count: int | None


class EvidenceLocatorRead(BaseModel):
    precision: EvidenceLocatorPrecision
    label: str
    reference_id: int | None = None
    locator_type: str | None = None
    source_page: int | None = None
    source_section: str | None = None
    start_char: int | None = None
    end_char: int | None = None
    quote: str | None = None
    confidence_label: str | None = None
    internal_href: str | None = None
    source_href: str | None = None
    asset_href: str | None = None


class EvidenceThesisImpactSummaryRead(BaseModel):
    id: int
    thesis_assumption_id: int
    assumption_description: str
    assumption_status: str
    impact_classification: str
    rationale: str
    created_at: datetime


class EvidenceValuationImpactSummaryRead(BaseModel):
    id: int
    valuation_model_id: int
    assumption_set_id: int
    parameter_name: str
    old_value: str | None
    new_value: str | None
    rationale: str | None
    is_applied: bool
    created_at: datetime


class EvidenceTrailRead(BaseModel):
    entry_point: Literal["alert", "event"]
    claim_type: EvidenceClaimType
    evidence_status: EvidenceStatus
    confidence: Literal["high", "medium", "low", "unknown"]
    source_timestamp: datetime | None
    claim_excerpt: str | None
    excerpt_origin: Literal[
        "alert.evidence",
        "event.description",
        "event.evidence_reference",
        "alert.summary",
        "none",
    ]
    alert: EvidenceAlertSummaryRead | None = None
    event: EvidenceEventSummaryRead | None = None
    company: EvidenceCompanySummaryRead | None = None
    source: EvidenceSourceSummaryRead | None = None
    document: EvidenceDocumentSummaryRead | None = None
    locator: EvidenceLocatorRead
    thesis_impacts: list[EvidenceThesisImpactSummaryRead] = Field(default_factory=list)
    valuation_impacts: list[EvidenceValuationImpactSummaryRead] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


class FilingSectionDiffRead(BaseModel):
    id: int
    current_section_id: int
    prior_section_id: int | None = None
    added_words: int
    removed_words: int
    diff_html: str | None = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class FilingSectionRead(BaseModel):
    id: int
    raw_document_id: int
    item_name: str
    title: str | None = None
    text_content: str
    word_count: int
    created_at: datetime
    updated_at: datetime

    diffs_as_current: list[FilingSectionDiffRead] = []

    model_config = ConfigDict(from_attributes=True)


class AiOutputRead(BaseModel):
    id: int
    raw_document_id: int | None = None
    reference_type: str | None = None
    reference_id: int | None = None
    model_name: str
    provider_name: str
    is_mock: bool
    prompt_version: str
    input_hash: str
    source_ids_json: list[str] = Field(default_factory=list)
    source_scope: str
    citations_json: list[dict[str, Any]] = Field(default_factory=list)
    citation_validation_status: str
    evaluation_json: dict[str, Any] | None = None
    privacy_disclosure_version: str
    external_data_classes_json: list[str] = Field(default_factory=list)
    transmission_scope: str
    execution_status: str
    failure_code: str | None = None
    is_blocked: bool
    output_text: str
    limitations: str | None = None
    confidence_label: str
    human_review_status: str
    review_notes: str | None = None
    reviewer_id: str | None = None
    reviewed_at: datetime | None = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AiCitationCreate(BaseModel):
    source_id: str = Field(min_length=1, max_length=255)
    quote: str = Field(min_length=1, max_length=2_000)
    start_char: int | None = Field(default=None, ge=0)
    end_char: int | None = Field(default=None, gt=0)

    @model_validator(mode="after")
    def validate_span(self):
        if (self.start_char is None) != (self.end_char is None):
            raise ValueError("start_char and end_char must be provided together")
        if self.start_char is not None and self.end_char <= self.start_char:
            raise ValueError("end_char must be greater than start_char")
        return self


class AiCitationValidationRequest(BaseModel):
    citations: list[AiCitationCreate] = Field(min_length=1, max_length=50)


class AiCitationSuggestionCandidate(BaseModel):
    quote: str = Field(min_length=1, max_length=2_000)
    start_char: int = Field(ge=0)
    end_char: int = Field(gt=0)
    score: float = Field(ge=0, le=1)
    confidence: Literal["high", "medium", "low"]
    matched_terms: list[str] = Field(default_factory=list)
    claim_term_count: int = Field(ge=0)
    matched_term_count: int = Field(ge=0)
    internal_href: str


class AiCitationSuggestionRead(BaseModel):
    source_id: str
    claim_text: str | None = None
    source_title: str | None = None
    status: Literal[
        "ready",
        "no_candidate",
        "source_text_unavailable",
        "unsupported_source",
        "undeclared_source",
        "claim_text_unavailable",
    ]
    candidates: list[AiCitationSuggestionCandidate] = Field(default_factory=list)
    limitations: list[str] = Field(default_factory=list)


class AiOutputReviewRequest(BaseModel):
    status: Literal["approved", "rejected", "needs_revision"]
    notes: str | None = Field(default=None, max_length=2_000)

    @model_validator(mode="after")
    def require_review_notes(self):
        if self.status != "approved" and not (self.notes or "").strip():
            raise ValueError("Review notes are required for rejection or revision")
        return self


class AIPrivacyAcknowledgement(BaseModel):
    privacy_disclosure_version: str

class CompanyMarketDataRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    market: str | None = None
    exchange: str | None = None
    ticker: str | None = None
    currency: str | None = None
    provider_name: str | None = None
    provider_symbol: str | None = None
    current_price: float | None = None
    change_percent: float | None = None
    volume: int | None = None
    market_cap: float | None = None
    pe_ratio: float | None = None
    fifty_two_week_high: float | None = None
    fifty_two_week_low: float | None = None
    source_timestamp: datetime | None = None
    observed_at: datetime | None = None
    price_type: str | None = None
    delay_minutes: int | None = None
    adjustment_state: str | None = None
    warnings: list[str] = Field(default_factory=list)
    last_updated: datetime


class MarketDataIngestionRequest(BaseModel):
    market: str
    exchange: str | None = None
    ticker: str
    days: int = Field(default=365, ge=1, le=3650)


class MarketHistoryPriceRead(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)
    as_of_date: date = Field(serialization_alias="date")
    price: float
    currency: str
    provider_name: str
    provider_symbol: str | None = None
    market: str | None = None
    exchange: str | None = None
    observed_at: datetime
    price_type: str
    adjustment_state: str
    warnings: list[str] = Field(default_factory=list)

class FinancialMetricRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    metric_name: str
    value: float
    unit: str | None = None

class FinancialPeriodRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    period_type: str
    year: int
    quarter: int | None = None
    report_date: date
    metrics: list[FinancialMetricRead] = Field(default_factory=list)

# --- Research Workspace ---

class ResearchMessageCreate(BaseModel):
    role: Literal["user"] = "user"
    content: str = Field(min_length=1, max_length=20_000)
    privacy_disclosure_version: str

class CitationSchema(BaseModel):
    source_id: str
    quote: str | None = None
    start_char: int | None = None
    end_char: int | None = None
    status: Literal["valid", "invalid", "partial", "not_evaluated"] = "not_evaluated"
    reason: str | None = None
    internal_href: str | None = None

class ResearchAiOutputRead(AiOutputRead):
    """Full review contract so research responses use the same approval gates as document AI."""

class ResearchMessageRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    session_id: int
    role: str
    content: str
    created_at: datetime
    ai_output_id: int | None = None
    ai_output: ResearchAiOutputRead | None = None

class ResearchSessionCreate(BaseModel):
    title: str = Field(min_length=1, max_length=255)

class ResearchSessionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    created_at: datetime
    updated_at: datetime

class ResearchSessionDetail(ResearchSessionRead):
    messages: list[ResearchMessageRead] = Field(default_factory=list)

# --- Variant Perception ---

class VariantPerceptionCreate(BaseModel):
    market_belief: str
    my_belief: str
    evidence_for_my_belief: str | None = None
    evidence_against_my_belief: str | None = None
    how_price_reflects_market_belief: str | None = None
    what_would_close_the_gap: str | None = None
    confidence: str = "medium"

class VariantPerceptionUpdate(BaseModel):
    market_belief: str | None = None
    my_belief: str | None = None
    evidence_for_my_belief: str | None = None
    evidence_against_my_belief: str | None = None
    how_price_reflects_market_belief: str | None = None
    what_would_close_the_gap: str | None = None
    confidence: str | None = None

class VariantPerceptionRead(VariantPerceptionCreate):
    id: int
    company_id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

# --- Decision Journal ---

class DecisionLogCreate(BaseModel):
    company_id: int
    decision_type: str
    rationale: str
    price_at_time: float | None = None
    emotional_state: str | None = None
    alternatives_considered: str | None = None

class DecisionLogUpdate(BaseModel):
    decision_type: str | None = None
    rationale: str | None = None
    price_at_time: float | None = None
    emotional_state: str | None = None
    alternatives_considered: str | None = None

class OutcomeReviewRead(BaseModel):
    id: int
    what_happened: str
    wrong_assumption: str | None = None
    information_unavailable_or_misinterpreted: bool
    valuation_wrong: bool
    thesis_wrong: bool
    timing_wrong: bool
    sizing_wrong: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class DecisionLogRead(DecisionLogCreate):
    id: int
    company_id: int
    created_at: datetime
    updated_at: datetime
    outcome_review: OutcomeReviewRead | None = None

    model_config = ConfigDict(from_attributes=True)

# --- Evidence Ledger ---

class EvidenceLedgerItemCreate(BaseModel):
    evidence_text: str
    effect: str
    source_link: str | None = None
    confidence: str = "medium"

class EvidenceLedgerItemUpdate(BaseModel):
    evidence_text: str | None = None
    effect: str | None = None
    source_link: str | None = None
    confidence: str | None = None

class EvidenceLedgerItemRead(EvidenceLedgerItemCreate):
    id: int
    company_id: int
    date_discovered: datetime
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# --- Real Options ---

class OptionEligibilityTestRequest(BaseModel):
    valuation_id: str | None = None
    option_type: str
    has_underlying_asset: bool = False
    has_finite_life: bool = False
    has_clear_exercise_price: bool = False
    has_asymmetric_payoff: bool = False
    has_exclusivity: bool = False
    can_estimate_volatility: bool = False
    can_estimate_underlying_value: bool = False

class OptionEligibilityTestResponse(BaseModel):
    eligibilityPassed: bool
    eligibilityScore: float
    recommendation: str
    warnings: list[str] = []

class RealOptionCalculateRequest(BaseModel):
    valuation_id: str | None = None
    option_type: str = "call"
    underlying_asset_value: float
    exercise_price: float
    option_life_years: float
    risk_free_rate: float
    volatility: float
    dividend_yield_or_cost_of_delay: float = 0.0
    exclusivity_score: float = 1.0
    is_already_counted: bool = False
    base_dcf_value: float = 0.0

class RealOptionCalculateResponse(BaseModel):
    d1: float
    d2: float
    nd1: float
    nd2: float
    raw_option_value: float
    adjusted_option_value: float
    option_delta: float
    option_adjusted_intrinsic_value: float | None = None
    warnings: list[str] = []

class VolatilityBenchmarkRead(BaseModel):
    country: str
    industry: str
    numberOfFirms: int | None
    equityStandardDeviation: float | None
    firmValueStandardDeviation: float | None
    equityValueWeight: float | None
    debtValueWeight: float | None
    assumptions: dict[str, float]
    claimType: Literal["Source Summary"] = "Source Summary"
    datasetVersionId: int
    sourceFile: str
    sourceSha256: str
    sourceAsOf: str
    dateConfidence: str
    canonicalSourcePath: str

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

class MarketRegimeInputCreate(BaseModel):
    metric_name: Literal["options", "liquidity", "volume", "breadth", "macro"]
    value: float = Field(ge=-100, le=100)
    as_of_date: date
    source_url: HttpUrl | None = None
    source_name: str = Field(min_length=2, max_length=200)
    input_type: Literal["manual", "provider"] = "manual"
    methodology: str = Field(min_length=10, max_length=1000)

    @field_validator("as_of_date")
    @classmethod
    def reject_future_observations(cls, value: date) -> date:
        if value > date.today():
            raise ValueError("as_of_date cannot be in the future")
        return value

    @model_validator(mode="after")
    def require_provider_source_url(self):
        if self.input_type == "provider" and self.source_url is None:
            raise ValueError("provider inputs require source_url")
        return self

class MarketRegimeInputRead(MarketRegimeInputCreate):
    id: int
    source_record_type: str | None = None
    source_record_id: int | None = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class MarketRegimeScoreRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    score_date: date
    overall_score: float
    options_score: float | None = None
    liquidity_score: float | None = None
    volume_score: float | None = None
    breadth_score: float | None = None
    macro_score: float | None = None
    confidence: str
    calculation_status: Literal["complete", "stale", "blocked"]
    formula: str
    blockers: list[str] = Field(default_factory=list)
    input_sources: list[dict[str, Any]] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    mode: str
    live_modules: list[str] = Field(default_factory=list)
    manual_modules: list[str] = Field(default_factory=list)
    simulated_modules: list[str] = Field(default_factory=list)
    created_at: datetime


class MarketRegimeMacroProviderRead(BaseModel):
    metric_name: Literal["macro"] = "macro"
    series_id: Literal["NFCI"] = "NFCI"
    macro_series_id: int | None = None
    observation_id: int | None = None
    observed_value: float | None = None
    normalized_value: float | None = None
    as_of_date: date | None = None
    source_name: str
    source_url: str
    methodology: str
    claim_type: Literal["Calculation"] = "Calculation"
    freshness_threshold_days: int
    age_days: int | None = None
    is_stale: bool = False
    can_apply: bool = False
    blockers: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    applied_input_id: int | None = None
    created: bool = False
