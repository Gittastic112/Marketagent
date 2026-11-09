/** Contracts and endpoint helpers for health. Import transport directly, never the compatibility facade. */
import type { AlertRecord, EventRecord, ThesisNote } from "./evidence.ts";
import type { Company } from "./companies.ts";
import type { DailyBriefPayload } from "./daily-brief.ts";
import type { Portfolio, PortfolioAnalytics, PortfolioSnapshot } from "./portfolio.ts";
import type { ProcessingRun } from "./operations.ts";

export type DashboardOverview = {
  portfolios: Portfolio[];
  companies: Company[];
  events: EventRecord[];
  alerts: AlertRecord[];
  thesis_notes: ThesisNote[];
  daily_brief: DailyBriefPayload;
  processing_runs: ProcessingRun[];
  default_portfolio: Portfolio | null;
  default_portfolio_snapshot: PortfolioSnapshot | null;
  portfolio_analytics: PortfolioAnalytics | null;
};

export type EvidenceIntegrityIssue = {
  code: string;
  severity: "error" | "warning";
  entity_type: "document" | "asset" | "evidence_reference" | "financial_candidate" | "financial_history";
  entity_id: number;
  message: string;
  action: string;
  company_id: number | null;
  document_id: number | null;
  reference_id: number | null;
};

export type FinancialHistoryIntegrity = {
  label: string | null;
  company_id: number;
  company: string;
  market: string;
  eligible_for_certification: boolean;
  failures: string[];
  limitations: string[];
  period_count: number;
  source_document_count: number;
  reviewed_evidence_count: number;
  uncovered_core_metrics_by_year: Record<string, string[]>;
  coverage_status: string;
  reconciliation_status: string;
  statement_identity_status: "passed" | "partial" | "failed" | "not_available";
  statement_identity_check_count: number;
  statement_identity_failed_count: number;
};

export type EvidenceIntegrityReport = {
  status: "healthy" | "issues_found";
  verification_scope: "metadata" | "deep";
  asset_content_verification_status: "not_run" | "checked";
  limitations: string[];
  checked_documents: number;
  checked_assets: number;
  checked_references: number;
  checked_financial_candidates: number;
  checked_financial_periods: number;
  financial_history_candidate_count: number;
  certified_financial_history_count: number;
  certified_markets: string[];
  financial_certification_status: "passed" | "partial" | "blocked" | "not_available";
  financial_histories: FinancialHistoryIntegrity[];
  error_count: number;
  warning_count: number;
  reported_issue_count: number;
  is_truncated: boolean;
  checked_at: string;
  issues: EvidenceIntegrityIssue[];
};

export type PeerReviewReceiptHealthItem = {
  peer_set_id: number;
  company_id: number;
  name: string;
  version: number;
  review_status: "reviewed";
  receipt_status: "missing" | "stale" | "current";
  blockers: string[];
  usable_methods: string[];
  current_diagnostics_as_of: string;
  receipt_diagnostics_as_of: string | null;
  current_warning_codes: string[];
  acknowledged_warning_codes: string[];
  action: string;
};

export type PeerReviewReceiptHealth = {
  status: "healthy" | "attention_required";
  scope: "page";
  total_owned_set_count: number;
  after_id: number;
  limit: number;
  has_more: boolean;
  next_after_id: number | null;
  checked_set_count: number;
  active_reviewed_set_count: number;
  ready_for_valuation_count: number;
  missing_receipt_count: number;
  stale_receipt_count: number;
  storage_blocked_count: number;
  coverage_blocked_count: number;
  draft_set_count: number;
  archived_set_count: number;
  sets_requiring_attention: PeerReviewReceiptHealthItem[];
  generated_at: string;
};

export type DamodaranCoverageRow = {
  source_filename: string;
  canonical_path: string;
  source_type: string;
  metric_family: string;
  geography: string;
  source_as_of: string;
  date_confidence: "high" | "medium" | "low";
  catalog_status: "active" | "historical_only";
  claim_type: "Source Summary";
  implementation_status: "supported" | "partial" | "unsupported";
  ingestion_available: boolean;
  ingestion_status: "ingested" | "metadata_only" | "not_ingested" | "source_missing";
  source_present: boolean;
  metadata_import_count: number;
  typed_record_count: number;
  stored_version_count: number;
  active_version_id: number | null;
  active_source_sha256: string | null;
  active_source_as_of: string | null;
  active_date_confidence: "high" | "medium" | "low" | "unknown" | null;
  active_import_kind: string | null;
  active_row_count: number | null;
  mirror_source_sha256: string | null;
  hash_matches_mirror: boolean | null;
  provenance_status: "complete" | "partial" | "missing" | "not_available" | "hash_mismatch";
  freshness_status: "current" | "stale" | "historical" | "unknown" | "user_assumed_recent";
  destination_tables: string[];
  supported_metrics: string[];
  missing_metrics: string[];
  limitations: string[];
  action_required: string;
};

export type DamodaranCoverageReport = {
  inventory_version: string;
  generated_at: string;
  source_count: number;
  source_present_count: number;
  supported_count: number;
  partial_count: number;
  unsupported_count: number;
  ingested_count: number;
  metadata_only_count: number;
  not_ingested_count: number;
  source_missing_count: number;
  current_count: number;
  stale_count: number;
  historical_count: number;
  unknown_date_count: number;
  user_assumed_recent_count: number;
  typed_record_count: number;
  provenance_complete_count: number;
  provenance_partial_count: number;
  provenance_missing_count: number;
  provenance_hash_mismatch_count: number;
  warnings: string[];
  limitations: string[];
  rows: DamodaranCoverageRow[];
};

export type EventEvidenceBackfillStatus =
  | "eligible"
  | "applied"
  | "missing_document"
  | "missing_source_text"
  | "missing_candidate_claim"
  | "no_exact_match"
  | "ambiguous_match"
  | "conflicting_exact_matches"
  | "race_skipped_existing_reference"
  | "race_skipped_event_missing";

export type EventEvidenceBackfillEntry = {
  event_id: number;
  company_id: number | null;
  raw_document_id: number | null;
  event_title: string;
  priority_score: number | null;
  status: EventEvidenceBackfillStatus;
  claim_origin: string | null;
  quote: string | null;
  start_char: number | null;
  end_char: number | null;
  occurrence_count: number;
  action: string;
};

export type EventEvidenceBackfillReport = {
  dry_run: boolean;
  processing_run_id: number | null;
  checked_event_count: number;
  eligible_count: number;
  applied_count: number;
  race_skipped_count: number;
  status_counts: Record<string, number>;
  generated_at: string;
  limitations: string[];
  entries: EventEvidenceBackfillEntry[];
};
