"""Health API contracts, independent of HTTP and persistence."""

from datetime import (
    date,
    datetime,
)

from pydantic import (
    BaseModel,
    Field,
    model_validator,
)

from typing import (
    Literal,
)


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
