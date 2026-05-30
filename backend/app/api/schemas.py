from datetime import date, datetime
from typing import Any, Literal, Generic, TypeVar

from pydantic import BaseModel, ConfigDict, Field

T = TypeVar("T")

class ApiMeta(BaseModel):
    is_stale: bool = False
    processing_time_ms: int | None = None

class ApiErrorDetail(BaseModel):
    code: str
    message: str
    target: str | None = None

class ApiResponse(BaseModel, Generic[T]):
    data: T | None = None
    meta: ApiMeta = Field(default_factory=ApiMeta)
    errors: list[ApiErrorDetail] = Field(default_factory=list)


class ScoringConfigUpdate(BaseModel):
    weight_credibility: float | None = None
    weight_novelty: float | None = None
    weight_impact: float | None = None
    weight_speed: float | None = None

class FredIngestionCreate(BaseModel):
    series_id: str

class FredIngestionRead(BaseModel):
    series_id: str
    observations_fetched: int
    observations_created: int


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
    exchange: str | None = None
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
    exchange: str | None = None
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


class CompanyLookupRead(BaseModel):
    ticker: str
    name: str
    cik: str


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


class EventRead(EventCreate):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime


class EventLinkCreate(BaseModel):
    target_event_id: int


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


class ThesisAssumptionRead(ThesisAssumptionCreate):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    updated_at: datetime


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


class PortfolioCreate(BaseModel):
    name: str
    base_currency: str = "USD"
    description: str | None = None


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
    post_id: int
    context_text: str | None = None


class NarrativeMentionUpdate(BaseModel):
    cluster_id: int | None = None
    post_id: int | None = None
    context_text: str | None = None


class NarrativeMentionRead(NarrativeMentionCreate):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime


class PortfolioUpdate(BaseModel):
    name: str | None = None
    base_currency: str | None = None
    description: str | None = None


class PortfolioRead(PortfolioCreate):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    updated_at: datetime


class PortfolioHoldingCreate(BaseModel):
    portfolio_id: int
    company_id: int | None = None
    ticker: str
    quantity: float = Field(ge=0)
    average_cost: float = Field(default=0, ge=0)
    currency: str = "USD"
    as_of_date: date


class PortfolioHoldingUpdate(BaseModel):
    portfolio_id: int | None = None
    company_id: int | None = None
    ticker: str | None = None
    quantity: float | None = Field(default=None, ge=0)
    average_cost: float | None = Field(default=None, ge=0)
    currency: str | None = None
    as_of_date: date | None = None


class PortfolioHoldingRead(PortfolioHoldingCreate):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    updated_at: datetime


PortfolioTransactionType = Literal[
    "buy",
    "sell",
    "dividend",
    "split",
    "bonus",
    "deposit",
    "withdrawal",
    "fee",
    "tax",
    "manual_adjustment",
]


class PortfolioTransactionCreate(BaseModel):
    portfolio_id: int
    company_id: int | None = None
    ticker: str
    transaction_type: PortfolioTransactionType
    quantity: float = Field(ge=0)
    price: float = Field(default=0, ge=0)
    fees: float = Field(default=0, ge=0)
    currency: str = "USD"
    transaction_date: date
    notes: str | None = None


class PortfolioTransactionUpdate(BaseModel):
    portfolio_id: int | None = None
    company_id: int | None = None
    ticker: str | None = None
    transaction_type: PortfolioTransactionType | None = None
    quantity: float | None = Field(default=None, ge=0)
    price: float | None = Field(default=None, ge=0)
    fees: float | None = Field(default=None, ge=0)
    currency: str | None = None
    transaction_date: date | None = None
    notes: str | None = None


class PortfolioTransactionRead(PortfolioTransactionCreate):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    updated_at: datetime


class PortfolioCashBalanceCreate(BaseModel):
    portfolio_id: int
    currency: str = "USD"
    amount: float = Field(default=0)
    as_of_date: date


class PortfolioCashBalanceUpdate(BaseModel):
    portfolio_id: int | None = None
    currency: str | None = None
    amount: float | None = Field(default=None)
    as_of_date: date | None = None


class PortfolioCashBalanceRead(PortfolioCashBalanceCreate):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    updated_at: datetime


class PortfolioSnapshotCreate(BaseModel):
    portfolio_id: int
    snapshot_date: date
    total_market_value: float | None = Field(default=None, ge=0)
    total_cost_basis: float | None = Field(default=None, ge=0)
    total_cash: float | None = Field(default=None)
    payload_json: dict[str, Any] | None = None


class PortfolioSnapshotUpdate(BaseModel):
    portfolio_id: int | None = None
    snapshot_date: date | None = None
    total_market_value: float | None = Field(default=None, ge=0)
    total_cost_basis: float | None = Field(default=None, ge=0)
    total_cash: float | None = Field(default=None, ge=0)
    payload_json: dict[str, Any] | None = None


class PortfolioSnapshotRead(PortfolioSnapshotCreate):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime


class DailyBriefRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    brief_date: date
    title: str
    summary: str
    payload_json: dict[str, Any]
    created_at: datetime


class ProcessingRunRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
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
    accession_number: str
    form_type: str
    filing_date: date
    report_date: date | None = None
    primary_document: str | None = None
    filing_url: str | None = None


class SecFilingIngestionCreate(BaseModel):
    source_id: int
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
    created_at: datetime
    updated_at: datetime


class PortfolioValuationHoldingRead(BaseModel):
    holding_id: int
    ticker: str
    company_id: int | None
    quantity: float
    average_cost: float
    currency: str
    market_price: float | None
    market_price_as_of: date | None
    market_value: float | None
    total_cost: float
    unrealized_pnl: float | None
    unrealized_pnl_percent: float | None
    weight_percent: float | None
    is_stale_price: bool


class PortfolioValuationRead(BaseModel):
    portfolio_id: int
    as_of_date: date
    base_currency: str
    total_market_value: float | None
    total_portfolio_value: float | None
    total_cash_value: float
    total_cost_basis: float
    total_unrealized_pnl: float | None
    total_unrealized_pnl_percent: float | None
    holdings: list[PortfolioValuationHoldingRead]


class PortfolioAnalyticsRead(BaseModel):
    portfolio_id: int
    as_of_date: date
    base_currency: str
    total_portfolio_value: float | None
    total_cash_value: float
    total_invested_value: float | None
    total_unrealized_pnl: float | None
    total_unrealized_pnl_percent: float | None
    top_positions: list[PortfolioValuationHoldingRead]
    top_gainers: list[PortfolioValuationHoldingRead]
    top_losers: list[PortfolioValuationHoldingRead]
    sector_exposure: dict[str, float]
    industry_exposure: dict[str, float]
    country_exposure: dict[str, float]
    currency_exposure: dict[str, float]
    asset_type_exposure: dict[str, float]
    concentration_score: float | None
    diversification_warnings: list[str]


class FinancialStatementPeriodCreate(BaseModel):
    company_id: int | None = None
    period_type: str
    year: int
    quarter: int | None = None
    report_date: date
    currency: str = "USD"


class FinancialStatementPeriodUpdate(BaseModel):
    company_id: int | None = None
    period_type: str | None = None
    year: int | None = None
    quarter: int | None = None
    report_date: date | None = None
    currency: str | None = None


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


class FinancialMetricRead(FinancialMetricCreate):
    model_config = ConfigDict(from_attributes=True)
    id: int
    created_at: datetime
    updated_at: datetime


class FinancialStatementPeriodRead(FinancialStatementPeriodCreate):
    model_config = ConfigDict(from_attributes=True)
    id: int
    created_at: datetime
    updated_at: datetime
    metrics: list[FinancialMetricRead] = Field(default_factory=list)


class ValuationModelCreate(BaseModel):
    company_id: int | None = None
    name: str
    description: str | None = None


class ValuationModelUpdate(BaseModel):
    company_id: int | None = None
    name: str | None = None
    description: str | None = None


class DcfAssumptionSetCreate(BaseModel):
    valuation_model_id: int | None = None
    scenario: str = "Base"
    discount_rate: float
    terminal_growth_rate: float
    projection_years: int = 5
    assumptions_json: dict[str, Any]


class DcfAssumptionSetUpdate(BaseModel):
    valuation_model_id: int | None = None
    scenario: str | None = None
    discount_rate: float | None = None
    terminal_growth_rate: float | None = None
    projection_years: int | None = None
    assumptions_json: dict[str, Any] | None = None


class DcfOutputCreate(BaseModel):
    assumption_set_id: int
    enterprise_value: float
    equity_value: float
    implied_share_price: float
    output_json: dict[str, Any] | None = None


class DcfOutputRead(DcfOutputCreate):
    model_config = ConfigDict(from_attributes=True)
    id: int
    created_at: datetime


class DcfAssumptionSetRead(DcfAssumptionSetCreate):
    model_config = ConfigDict(from_attributes=True)
    id: int
    created_at: datetime
    updated_at: datetime
    outputs: list[DcfOutputRead] = Field(default_factory=list)


class ValuationModelRead(ValuationModelCreate):
    model_config = ConfigDict(from_attributes=True)
    id: int
    created_at: datetime
    updated_at: datetime
    assumption_sets: list[DcfAssumptionSetRead] = Field(default_factory=list)


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
    raw_document_id: int
    model_name: str
    prompt_version: str
    input_hash: str
    output_text: str
    limitations: str | None = None
    confidence_label: str
    human_review_status: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class CompanyMarketDataRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    current_price: float | None = None
    change_percent: float | None = None
    volume: int | None = None
    market_cap: float | None = None
    pe_ratio: float | None = None
    fifty_two_week_high: float | None = None
    fifty_two_week_low: float | None = None
    last_updated: datetime

class MarketPriceRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    date: date = Field(alias="as_of_date")
    price: float

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
