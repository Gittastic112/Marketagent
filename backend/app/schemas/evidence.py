"""Evidence API contracts, independent of HTTP and persistence."""

from datetime import (
    date,
    datetime,
)

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    model_validator,
)

from typing import (
    Any,
    Literal,
)


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
