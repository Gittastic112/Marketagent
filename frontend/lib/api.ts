import { AI_PRIVACY_DISCLOSURE_VERSION } from "./ai-privacy.ts";

const SERVER_API_BASE_URL = process.env.API_BASE_URL ?? process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://127.0.0.1:8000";
const BROWSER_API_BASE_URL = process.env.NEXT_PUBLIC_BROWSER_API_BASE_URL ?? "/api/backend";
const DEBUG_LOGS_ENABLED = process.env.NEXT_PUBLIC_DEBUG_LOGS === "true";

function getApiBaseUrl(): string {
  return typeof window === "undefined" ? SERVER_API_BASE_URL : BROWSER_API_BASE_URL;
}

function logApiStart(method: string, path: string) {
  if (DEBUG_LOGS_ENABLED) {
    console.log(`[api] ${method} ${path} -> ${getApiBaseUrl()}${path}`);
  }
}

function logApiSuccess(method: string, path: string, status: number) {
  if (DEBUG_LOGS_ENABLED) {
    console.log(`[api] ${method} ${path} succeeded with ${status}`);
  }
}

function logApiFailure(method: string, path: string, status: number) {
  if (DEBUG_LOGS_ENABLED) {
    console.log(`[api] ${method} ${path} failed with ${status}`);
  }
}

export class ApiError extends Error {
  readonly status: number;

  constructor(message: string, status: number) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

async function apiError(response: Response): Promise<ApiError> {
  try {
    const body = await response.json();
    if (body && Array.isArray(body.errors) && body.errors.length > 0) {
      return new ApiError(body.errors[0].message, response.status);
    }
    if (body && typeof body.detail === "string") {
      return new ApiError(body.detail, response.status);
    }
  } catch {
    // Fall back to the generic message below when the response body is not JSON.
  }
  return new ApiError(`API request failed: ${response.status}`, response.status);
}

export type ApiMeta = {
  status: string;
  last_updated: string | null;
  source: string;
  is_stale: boolean;
  is_mock?: boolean;
  warnings: string[];
  confidence: string;
  processing_time_ms: number | null;
  request_id?: string | null;
};

export interface ApiErrorDetail {
  code: string;
  message: string;
  target?: string;
  retryable?: boolean;
  field?: string | null;
  provider?: string | null;
  processing_run_id?: number | null;
}

export interface ApiResponse<T> {
  data: T | null;
  meta: ApiMeta;
  errors: ApiErrorDetail[];
}

export type SourceCapabilityStatus = "available" | "manual_only" | "not_configured" | "not_supported";

export type SourceCapability = {
  id: number;
  market: "US" | "IN" | string;
  source_type: string;
  provider_name: string;
  capability: string;
  status: SourceCapabilityStatus;
  requires_api_key: boolean;
  freshness_expected_seconds: number | null;
  notes: string | null;
  updated_at: string;
};

export type ValuationCompanyContext = {
  company_id: number;
  market: string;
  country: string;
  default_currency: string;
  cash_flow_currency: string;
  discount_rate_currency: string;
  available_benchmark_countries: string[];
  recommended_benchmark_country: string;
  benchmark_source: string;
  warnings: string[];
};

export type RiskFreeRate = {
  market: string;
  country: string;
  currency: string;
  risk_free_rate: number;
  risk_free_rate_source: string;
  as_of_date: string | null;
  is_manual: boolean;
  warnings: string[];
};

async function parseApiResponse<T>(response: Response): Promise<T> {
  const payload = await response.json();

  if (payload && typeof payload === "object" && "meta" in payload) {
    const apiResponse = payload as ApiResponse<T>;
    if (apiResponse.errors && apiResponse.errors.length > 0) {
      throw new ApiError(apiResponse.errors[0].message, response.status);
    }
    return apiResponse.data as T;
  }

  return payload as T;
}

export type ExposureTag = {
  id: number;
  name: string;
  description: string | null;
};

export type Company = {
  id: number;
  market: string | null;
  primary_exchange: string | null;
  local_symbol: string | null;
  isin: string | null;
  figi: string | null;
  regulatory_id: string | null;
  regulatory_id_type: string | null;
  ticker: string;
  name: string;
  sector: string | null;
  industry: string | null;
  exchange: string | null;
  cik: string | null;
  aliases_json: string[] | null;
  country: string | null;
  region: string | null;
  currency: string | null;
  damodaran_industry?: string | null;
  asset_type: string | null;
  security_type: string | null;
  market_cap_category: string | null;
  is_etf: boolean;
  etf_provider: string | null;
  active: boolean;
  exposure_tags: ExposureTag[];
};

export type CompanyLookup = {
  market?: string;
  exchange?: string | null;
  primary_exchange?: string | null;
  ticker: string;
  local_symbol?: string;
  name: string;
  sector?: string | null;
  industry?: string | null;
  currency?: string;
  country?: string;
  regulatory_id?: string | null;
  regulatory_id_type?: string | null;
  isin?: string | null;
  source?: string;
  warnings?: string[];
  cik?: string;
};

export type Source = {
  id: number;
  name: string;
  source_type: string;
  base_url: string | null;
  reliability_score: number | null;
  active: boolean;
};

export type RawDocument = {
  id: number;
  company_id: number | null;
  source_id: number;
  document_type: string;
  title: string;
  url: string | null;
  published_at?: string | null;
  raw_text?: string | null;
  raw_payload_json?: Record<string, unknown> | null;
  has_raw_text?: boolean;
  content_hash: string;
  ingested_at?: string;
  created_at?: string;
};

export type DocumentAsset = {
  id: number;
  raw_document_id: number;
  original_filename: string;
  mime_type: string;
  size_bytes: number;
  sha256: string;
  page_count: number;
  created_at: string;
};

export type PdfFinancialExtractionResult = {
  raw_document_id: number;
  asset: DocumentAsset;
  page_count: number;
  scanned_page_count: number;
  scanned_pages: number[];
  table_count: number;
  created_count: number;
  skipped_existing_count: number;
  warnings: string[];
  candidates: FinancialExtractionCandidate[];
};

export type FilingDiscovery = {
  company_id: number;
  market: string;
  provider_name: string;
  mode: "automated" | "manual";
  manual_required: boolean;
  filings: SecFilingMetadata[];
  next_action: string;
};

export type FilingSectionDiff = {
  id: number;
  current_section_id: number;
  prior_section_id: number | null;
  added_words: number;
  removed_words: number;
  diff_html: string | null;
  created_at: string;
};

export type FilingSection = {
  id: number;
  raw_document_id: number;
  item_name: string;
  title: string | null;
  text_content: string;
  word_count: number;
  created_at: string;
  updated_at: string;
  diffs_as_current: FilingSectionDiff[];
};

export type AiOutput = {
  id: number;
  raw_document_id: number | null;
  reference_type: string | null;
  reference_id: number | null;
  model_name: string;
  provider_name: string;
  is_mock: boolean;
  prompt_version: string;
  input_hash: string;
  source_ids_json: string[];
  source_scope: string;
  citations_json: Array<{
    source_id: string;
    quote: string;
    start_char?: number;
    end_char?: number;
    status: "valid" | "invalid";
    reason?: string | null;
    internal_href?: string;
  }>;
  citation_validation_status: "not_evaluated" | "valid" | "partial" | "invalid";
  evaluation_json: {
    version: string;
    passed: boolean;
    checks: Record<string, boolean>;
  } | null;
  privacy_disclosure_version: string;
  external_data_classes_json: string[];
  transmission_scope: string;
  execution_status: string;
  failure_code: string | null;
  output_text: string;
  limitations: string | null;
  confidence_label: string;
  human_review_status: string;
  review_notes: string | null;
  reviewer_id: string | null;
  reviewed_at: string | null;
  created_at: string;
};

export type DashboardOverview = {
  companies: Company[];
  events: EventRecord[];
  alerts: AlertRecord[];
  thesis_notes: ThesisNote[];
  daily_brief: DailyBrief;
  processing_runs: ProcessingRun[];
  default_portfolio: Portfolio | null;
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

export type EvidenceSearchResult = {
  result_type: "document" | "event" | "alert" | "thesis" | "decision" | "valuation";
  record_id: number;
  company_id: number | null;
  title: string;
  excerpt: string | null;
  rank: number;
  claim_type: "Fact" | "Source Summary" | "User Assumption";
  source_name: string | null;
  source_timestamp: string | null;
  href: string;
  locator: Record<string, unknown> | null;
};

export type EventRecord = {
  id: number;
  company_id: number | null;
  raw_document_id: number | null;
  event_type: string;
  information_speed: string;
  title: string;
  description: string | null;
  credibility_score: number | null;
  novelty_score: number | null;
  impact_score: number | null;
  priority_score: number | null;
  data_confidence_score: number | null;
  score_explanation_json: ScoreExplanation | null;
  corroborates?: EventLinkSummary[];
  contradicts?: EventLinkSummary[];
};

export type EventLinkSummary = {
  id: number;
  title: string;
  event_type: string;
};

export type IntelligenceReviewItem = {
  item_type: "contradiction" | "filing_language_change";
  item_id: string;
  company_id: number | null;
  title: string;
  summary: string;
  severity: "low" | "medium" | "high";
  claim_type: "User Assumption" | "Calculation";
  evidence_href: string;
  source_timestamp: string;
  section_name: string | null;
  added_words: number | null;
  removed_words: number | null;
};

export type ScoreExplanationInput = {
  name: string;
  value: number;
  weight: number;
  contribution: number;
  explanation: string;
};

export type ScoreExplanation = {
  score_name: string;
  value: number;
  label: string;
  direction: string;
  confidence: string;
  inputs: ScoreExplanationInput[];
  summary: string;
};

export type AlertPortfolioImpact = {
  id: number;
  alert_id: number;
  portfolio_id: number;
  exposure_amount: number;
  impact_score: number;
  created_at: string;
};

export type AlertRecord = {
  id: number;
  event_id: number | null;
  company_id: number | null;
  alert_type: string;
  severity: string;
  title: string;
  summary: string | null;
  why_it_matters: string | null;
  what_changed: string | null;
  evidence: string | null;
  confidence_bucket: string;
  review_status: string;
  review_notes: string | null;
  reviewed_at: string | null;
  created_at: string;
  portfolio_priority_score: number;
  thesis_relevance_score: number;
  ownership_weight_score: number;
  valuation_gap_score: number;
  narrative_velocity_score: number;
  score_explanation_json: ScoreExplanation | null;
  portfolio_impacts: AlertPortfolioImpact[];
};

export type Alert = AlertRecord;

export type EvidenceClaimType =
  | "Fact"
  | "Source Summary"
  | "Calculation"
  | "User Assumption"
  | "AI Interpretation"
  | "Estimate"
  | "Mock Data";

export type EvidenceAlertSummary = {
  id: number;
  event_id: number | null;
  company_id: number | null;
  alert_type: string;
  severity: string;
  title: string;
  summary: string | null;
  why_it_matters: string | null;
  confidence_bucket: string;
  created_at: string;
};

export type EvidenceEventSummary = {
  id: number;
  company_id: number | null;
  raw_document_id: number | null;
  event_type: string;
  information_speed: string;
  title: string;
  description: string | null;
  event_time: string | null;
  credibility_score: number | null;
  priority_score: number | null;
  created_at: string;
};

export type EvidenceTrail = {
  entry_point: "alert" | "event";
  claim_type: EvidenceClaimType;
  evidence_status: "complete" | "partial" | "missing";
  confidence: "high" | "medium" | "low" | "unknown";
  source_timestamp: string | null;
  claim_excerpt: string | null;
  excerpt_origin: "alert.evidence" | "event.description" | "event.evidence_reference" | "alert.summary" | "none";
  alert: EvidenceAlertSummary | null;
  event: EvidenceEventSummary | null;
  company: {
    id: number;
    ticker: string;
    name: string;
    market: string;
    primary_exchange: string | null;
  } | null;
  source: {
    id: number;
    name: string;
    source_type: string;
    reliability_score: number | null;
    active: boolean;
  } | null;
  document: {
    id: number;
    company_id: number | null;
    source_id: number;
    document_type: string;
    title: string;
    url: string | null;
    published_at: string | null;
    ingested_at: string;
    content_hash: string;
    has_raw_text: boolean;
    has_asset: boolean;
    asset_page_count: number | null;
  } | null;
  locator: {
    precision: "document" | "page" | "region" | "section" | "span" | "none";
    label: string;
    reference_id: number | null;
    locator_type: string | null;
    source_page: number | null;
    source_section: string | null;
    start_char: number | null;
    end_char: number | null;
    quote: string | null;
    confidence_label: string | null;
    internal_href: string | null;
    source_href: string | null;
    asset_href: string | null;
  };
  thesis_impacts: Array<{
    id: number;
    thesis_assumption_id: number;
    assumption_description: string;
    assumption_status: string;
    impact_classification: string;
    rationale: string;
    created_at: string;
  }>;
  valuation_impacts: Array<{
    id: number;
    valuation_model_id: number;
    assumption_set_id: number;
    parameter_name: string;
    old_value: string | null;
    new_value: string | null;
    rationale: string | null;
    is_applied: boolean;
    created_at: string;
  }>;
  warnings: string[];
};

export type EventEvidenceReference = {
  id: number;
  event_id: number;
  raw_document_id: number;
  created_by_user_id: string | null;
  locator_type: "text_span" | "pdf_region" | "section" | "xbrl_fact";
  source_page: number | null;
  source_section: string | null;
  start_char: number | null;
  end_char: number | null;
  quote: string | null;
  bounding_box_json: Record<string, unknown> | null;
  source_metadata_json: Record<string, unknown> | null;
  confidence_label: "high" | "medium" | "low";
  origin: string;
  pdf_region_status: "valid" | "invalid" | "not_applicable";
  created_at: string;
};

export type EventEvidenceSearchMatch = {
  occurrence_index: number;
  start_char: number;
  end_char: number;
  context_before: string;
  quote: string;
  context_after: string;
};

export type EventEvidenceResolutionSearch = {
  event_id: number;
  company_id: number | null;
  raw_document_id: number;
  event_title: string;
  document_title: string;
  document_content_hash: string;
  query: string;
  exact_match_count: number;
  returned_match_count: number;
  is_truncated: boolean;
  existing_reference_count: number;
  matches: EventEvidenceSearchMatch[];
  limitations: string[];
};

export type ThesisAssumption = {
  id: number;
  thesis_note_id: number;
  description: string;
  category: string | null;
  importance: string;
  original_confidence: string;
  current_confidence: string;
  status: string;
  last_reviewed: string | null;
  falsification_trigger: string | null;
  source_links: string[] | null;
  created_at: string;
  updated_at: string;
  impacts?: EventThesisImpact[];
};

export type ThesisChange = {
  id: number;
  thesis_note_id: number;
  change_summary: string;
  drift_score: number;
  created_at: string;
};

export type ThesisNote = {
  id: number;
  company_id: number;
  title: string;
  thesis_text: string;
  status: string;
  thesis_drift_score: number;
  assumptions: ThesisAssumption[];
  changes: ThesisChange[];
};

export type Portfolio = {
  id: number;
  name: string;
  base_currency: string;
  description: string | null;
};

export interface PortfolioAttributionComponent {
  price_movement: number;
  fx_impact: number;
  dividends: number;
  fees: number;
}

export interface PortfolioAttributionRead {
  total_unrealized_pnl: number;
  components: PortfolioAttributionComponent;
  attribution_by_sector: Record<string, number>;
  attribution_by_geography: Record<string, number>;
  attribution_by_asset_type: Record<string, number>;
}

export interface PortfolioSnapshot {
  id: number;
  portfolio_id: number;
  snapshot_date: string;
  total_market_value: number | null;
  total_cost_basis: number | null;
  total_cash: number | null;
  payload_json: Record<string, unknown> | null;
  created_at: string;
}

export interface PortfolioCashBalance {
  id: number;
  portfolio_id: number;
  currency: string;
  amount: number;
  as_of_date: string;
  created_at: string;
  updated_at: string;
}

export interface MarketPrice {
  id: number;
  company_id: number | null;
  ticker: string;
  price: number;
  currency: string;
  as_of_date: string;
  provider_name?: string;
  provider_symbol?: string | null;
  market?: string | null;
  exchange?: string | null;
  source_timestamp?: string | null;
  observed_at?: string | null;
  price_type?: string;
  delay_minutes?: number | null;
  adjustment_state?: string;
  warnings?: string[];
  created_at: string;
  updated_at: string;
}

export interface SocialPost {
  id: number;
  platform: string;
  source_url: string;
  author: string | null;
  raw_text: string;
  content_hash: string;
  published_at: string | null;
  payload_json: Record<string, unknown> | unknown[] | null;
  created_at: string;
  updated_at: string;
}

export interface SentimentScore {
  id: number;
  post_id: number | null;
  company_id: number | null;
  score: string;
  rationale: string | null;
  created_at: string;
}

export interface NarrativeCluster {
  id: number;
  name: string;
  description: string | null;
  created_at: string;
  updated_at: string;
}

export interface NarrativeClaim {
  id: number;
  cluster_id: number;
  claim_text: string;
  created_at: string;
}

export interface NarrativeMention {
  id: number;
  cluster_id: number;
  event_id: number;
  context_text: string | null;
  created_at: string;
}

export interface PortfolioValuationHolding {
  holding_id: number;
  ticker: string;
  company_id: number | null;
  quantity: number;
  average_cost: number;
  currency: string;
  market_price: number | null;
  market_price_as_of: string | null;
  market_value: number | null;
  total_cost: number;
  unrealized_pnl: number | null;
  unrealized_pnl_percent: number | null;
  weight_percent: number | null;
  is_stale_price: boolean;
  is_valuation_stale?: boolean;
  stale_valuation_reason?: string | null;
  intrinsic_value?: number | null;
  thesis_status?: string | null;
  active_alerts_count?: number;
}

export interface PortfolioValuation {
  portfolio_id: number;
  as_of_date: string;
  base_currency: string;
  total_market_value: number | null;
  total_cost_basis: number;
  total_unrealized_pnl: number | null;
  total_unrealized_pnl_percent: number | null;
  holdings: PortfolioValuationHolding[];
}

export interface PortfolioAnalytics {
  portfolio_id: number;
  as_of_date: string;
  base_currency: string;
  total_portfolio_value: number | null;
  total_cash_value: number;
  total_invested_value: number | null;
  total_unrealized_pnl: number | null;
  total_unrealized_pnl_percent: number | null;
  top_positions: PortfolioValuationHolding[];
  top_gainers: PortfolioValuationHolding[];
  top_losers: PortfolioValuationHolding[];
  sector_exposure: Record<string, number>;
  industry_exposure: Record<string, number>;
  country_exposure: Record<string, number>;
  currency_exposure: Record<string, number>;
  asset_type_exposure: Record<string, number>;
  concentration_score: number | null;
  diversification_warnings: string[];
  fx_impact: number | null;
  opportunity_cost: number | null;
  opportunity_cost_percent: number | null;
}

export type PortfolioHolding = {
  id: number;
  portfolio_id: number;
  company_id: number | null;
  ticker: string;
  quantity: number;
  average_cost: number;
  currency: string;
  as_of_date: string;
};

export type PortfolioTransaction = {
  id: number;
  portfolio_id: number;
  company_id: number | null;
  ticker: string;
  transaction_type: string;
  quantity: number;
  price: number;
  fees: number;
  currency: string;
  transaction_date: string;
  notes: string | null;
};

export type DailyBrief = {
  title: string;
  date: string;
  summary: string;
  top_events: Array<{
    id: number;
    company: string | null;
    title: string;
    event_type: string;
    information_speed: string;
    description: string | null;
    credibility_score: number | null;
    novelty_score: number | null;
    impact_score: number | null;
    priority_score: number | null;
    source: string | null;
    source_url: string | null;
  }>;
  alerts: Array<{
    id: number;
    company: string | null;
    title: string;
    severity: string;
    confidence_bucket: string;
    review_status: string;
    summary: string | null;
  }>;
  follow_up_questions: string[];
};

export type SavedDailyBrief = {
  id: number;
  brief_date: string;
  title: string;
  summary: string;
  payload_json: DailyBrief;
  created_at: string;
};

export type RssIngestionResult = {
  fetched_count: number;
  created_count: number;
  skipped_duplicate_count: number;
  error_count: number;
  errors: string[];
  created: number;
  skipped_duplicates: number;
  events_created: number;
  events_skipped_existing: number;
  alerts_created: number;
  alerts_skipped_existing: number;
  alerts_skipped_below_threshold: number;
};

export type SecFilingIngestionResult = {
  fetched_count: number;
  created_count: number;
  skipped_duplicate_count: number;
  error_count: number;
  errors: string[];
  created: number;
  skipped_duplicates: number;
  events_created: number;
  events_skipped_existing: number;
  alerts_created: number;
  alerts_skipped_existing: number;
  alerts_skipped_below_threshold: number;
};

export type SecFilingMetadata = {
  accession_number: string;
  form_type: string;
  filing_date: string;
  report_date: string | null;
  primary_document: string | null;
  filing_url: string | null;
};

export type EventExtractionResult = {
  created: number;
  skipped_existing: number;
};

export type AlertGenerationResult = {
  created: number;
  skipped_existing: number;
  skipped_below_threshold: number;
};

export type FinancialMetric = {
  id: number;
  period_id: number;
  metric_name: string;
  value: number;
  unit: string | null;
  created_at: string;
  updated_at: string;
};

export type FinancialStatementPeriod = {
  id: number;
  company_id: number;
  period_type: string;
  year: number;
  quarter: number | null;
  report_date: string;
  currency: string;
  currency_source: string;
  currency_confidence: string;
  created_at: string;
  updated_at: string;
  metrics: FinancialMetric[];
};

export type FinancialExtractionCandidate = {
  id: number;
  company_id: number;
  raw_document_id: number;
  metric_code: string;
  reported_label: string;
  value: number;
  unit: string | null;
  fiscal_year: number | null;
  period_type: string;
  source_text: string;
  source_line_number: number | null;
  source_page: number | null;
  source_section: string | null;
  source_table_name: string | null;
  source_row_label: string | null;
  source_column_label: string | null;
  source_cell_reference: string | null;
  source_locator_json: Record<string, unknown> | null;
  extraction_warnings: string | null;
  extraction_method: string;
  confidence_label: string;
  review_status: string;
  created_at: string;
  updated_at: string;
};

export type DcfProjectionYear = {
  id: number;
  assumption_set_id: number;
  year_index: number;
  calendar_year: number;
  revenue: number | null;
  revenue_growth: number | null;
  ebit_margin: number | null;
  ebit: number | null;
  tax_rate: number | null;
  nopat: number | null;
  reinvestment: number | null;
  fcff: number | null;
  invested_capital: number | null;
  roic: number | null;
  wacc: number | null;
  discount_factor: number | null;
  pv_fcff: number | null;
  created_at: string;
};

export type DiagnosticWarning = {
  severity: "info" | "watch" | "warning" | "critical" | "blocking";
  module: string;
  message: string;
  affectedAssumptions: string[];
  suggestedFix: string | null;
  formula: string | null;
};

export type DcfScenarioOutput = {
  scenario_name: string;
  description: string;
  output: DcfOutput;
};

export type DcfOutput = {
  id: number;
  assumption_set_id: number;
  sum_pv_fcff: number | null;
  terminal_value: number | null;
  pv_terminal_value: number | null;
  enterprise_value: number | null;
  cash: number | null;
  non_operating_assets: number | null;
  debt: number | null;
  minority_interests: number | null;
  preferred_stock: number | null;
  employee_options_value: number | null;
  equity_value: number | null;
  diluted_shares: number | null;
  intrinsic_value_per_share: number | null;
  current_market_price: number | null;
  upside_downside_pct: number | null;
  terminal_value_pct_of_ev: number | null;
  implied_exit_multiple: number | null;
  implied_terminal_roic: number | null;
  implied_pe: number | null;
  implied_ev_ebitda: number | null;
  implied_ev_sales: number | null;
  implied_ev_ebit: number | null;
  implied_pbv: number | null;

  fcfe_intrinsic_value_per_share?: number | null;
  ddm_intrinsic_value_per_share?: number | null;

  base_dcf_value?: number | null;
  pv_of_excess_returns?: number | null;

  model_quality_score: number | null;
  warnings_json: DiagnosticWarning[] | null;
  created_at: string;
};

export type QuickValuationAssumptions = {
  company_id: number;
  assumptions: DcfAssumptionSetCreate;
  provenance: Record<string, unknown>;
  source_metadata: Record<string, unknown>;
  warnings: string[];
};

export type QuickValuationProjection = {
  year_index: number;
  revenue: number;
  revenue_growth: number;
  ebit_margin: number;
  nopat: number;
  reinvestment: number;
  fcff: number;
  roic: number;
  wacc: number;
  pv_fcff: number;
};

export type QuickValuationOutput = {
  company_id: number;
  currency: string | null;
  claim_type: "Calculation";
  is_persisted: false;
  sum_pv_fcff: number;
  terminal_value: number;
  pv_terminal_value: number;
  enterprise_value: number;
  cash: number;
  debt: number;
  minority_interests: number;
  preferred_stock: number;
  employee_options_value: number;
  equity_value: number;
  diluted_shares: number;
  intrinsic_value_per_share: number;
  current_market_price: number;
  upside_downside_pct: number;
  terminal_value_pct_of_ev: number;
  model_quality_score: number | null;
  warnings_json: DiagnosticWarning[];
  projection_years: QuickValuationProjection[];
  limitations: string[];
};

export interface DcfSensitivityTable {
  id: number;
  assumption_set_id: number;
  table_type: string;
  x_axis_json: any;
  y_axis_json: any;
  values_json: any;
  created_at: string;
}

export interface ReverseDcfRequest {
  assumption_set_id: number;
  target_parameter: string;
  current_market_price: number;
  diluted_shares?: number;
}

export interface ReverseDcfResponse {
  target_parameter: string;
  implied_value: number | null;
  original_value: number | null;
  intrinsic_value_at_implied: number | null;
  diagnostics: DiagnosticWarning[];
  error?: string;
}

export type DcfDecisionLog = {
  id: number;
  valuation_model_id: number;
  assumption_set_id: number;
  decision_type: string;
  user_note: string | null;
  price_at_decision: number | null;
  intrinsic_value_at_decision: number | null;
  upside_downside_at_decision: number | null;
  confidence_label: string | null;
  created_at: string;
};

export type ValuationAssumptionChangeLog = {
  id: number;
  valuation_model_id: number;
  assumption_set_id: number;
  event_id: number | null;
  parameter_name: string;
  old_value: string | null;
  new_value: string | null;
  rationale: string | null;
  is_applied: boolean;
  created_at: string;
};

export type DcfAssumptionSet = {
  id: number;
  valuation_model_id: number;
  scenario: string;

  story_text: string | null;
  growth_story: string | null;
  margin_story: string | null;
  reinvestment_story: string | null;
  risk_story: string | null;

  starting_revenue: number | null;
  revenue_growth_years_json: Record<string, unknown> | number[] | null;
  target_operating_margin: number | null;
  current_operating_margin: number | null;
  tax_rate: number | null;
  sales_to_capital_ratio: number | null;
  reinvestment_method: string;
  starting_invested_capital: number | null;

  risk_free_rate: number | null;
  equity_risk_premium: number | null;
  beta: number | null;
  cost_of_equity: number | null;
  pre_tax_cost_of_debt: number | null;
  debt_to_capital: number | null;
  equity_to_capital: number | null;
  wacc_start: number | null;
  wacc_terminal: number | null;

  terminal_growth_rate: number | null;
  terminal_roic: number | null;

  cash: number | null;
  cross_holdings: number | null;
  minority_interests: number | null;
  preferred_stock: number | null;
  debt: number | null;
  operating_leases: number | null;
  employee_options_value: number | null;
  diluted_shares: number | null;
  current_market_price: number | null;
  net_income?: number | null;
  capex?: number | null;
  depreciation?: number | null;
  change_in_nwc?: number | null;
  dividends?: number | null;
  buybacks?: number | null;
  stock_issuances?: number | null;
  new_debt_issued?: number | null;
  debt_repaid?: number | null;
  company_age?: number | null;

  is_stale?: boolean;
  stale_reason?: string | null;
  stale_event_id?: number | null;

  probability_of_failure?: number | null;
  distress_sale_proceeds?: number | null;
  book_value_of_equity?: number | null;
  target_roe?: number | null;

  created_at: string;
  updated_at: string;
  outputs: DcfOutput | null;
  projection_years: DcfProjectionYear[];
  sensitivity_tables: DcfSensitivityTable[];
  decision_logs: DcfDecisionLog[];
  change_logs: ValuationAssumptionChangeLog[];
};

export type ValuationModel = {
  id: number;
  company_id: number;
  name: string;
  description: string | null;
  model_type: string;
  created_at: string;
  updated_at: string;
  assumption_sets: DcfAssumptionSet[];
  decision_logs: DcfDecisionLog[];
};

export type ValuationModelCreate = {
  company_id: number;
  name: string;
  description?: string;
  model_type?: string;
};

export type DcfAssumptionSetCreate = {
  scenario: string;

  story_text?: string | null;
  growth_story?: string | null;
  margin_story?: string | null;
  reinvestment_story?: string | null;
  risk_story?: string | null;

  starting_revenue?: number | null;
  revenue_growth_years_json?: Record<string, unknown> | null;
  target_operating_margin?: number | null;
  current_operating_margin?: number | null;
  tax_rate?: number | null;
  sales_to_capital_ratio?: number | null;
  reinvestment_method?: string;
  starting_invested_capital?: number | null;

  risk_free_rate?: number | null;
  equity_risk_premium?: number | null;
  beta?: number | null;
  cost_of_equity?: number | null;
  pre_tax_cost_of_debt?: number | null;
  debt_to_capital?: number | null;
  equity_to_capital?: number | null;
  wacc_start?: number | null;
  wacc_terminal?: number | null;

  terminal_growth_rate?: number | null;
  terminal_roic?: number | null;

  cash?: number | null;
  minority_interests?: number | null;
  preferred_stock?: number | null;
  debt?: number | null;
  employee_options_value?: number | null;
  diluted_shares?: number | null;
  current_market_price?: number | null;

  net_income?: number;
  capex?: number;
  depreciation?: number;
  change_in_nwc?: number;
  new_debt_issued?: number;
  debt_repaid?: number;
  dividends?: number;
  buybacks?: number;
  stock_issuances?: number;
  company_age?: number;
};

export async function fetchApi<T>(path: string): Promise<T> {
  logApiStart("GET", path);
  const response = await fetch(`${getApiBaseUrl()}${path}`, {
    cache: "no-store"
  });

  if (!response.ok) {
    logApiFailure("GET", path, response.status);
    throw await apiError(response);
  }

  logApiSuccess("GET", path, response.status);
  return parseApiResponse<T>(response);
}

export async function fetchApiResponse<T>(path: string): Promise<ApiResponse<T>> {
  logApiStart("GET", path);
  let response: Response;
  try {
    response = await fetch(`${getApiBaseUrl()}${path}`, {
      cache: "no-store"
    });
  } catch (e: any) {
    logApiFailure("GET", path, 0);
    return {
      data: null,
      meta: { is_stale: true } as any,
      errors: [{ code: "NETWORK_ERROR", message: `Network request failed: ${e.message}` }]
    };
  }

  if (!response.ok) {
    logApiFailure("GET", path, response.status);
    // Even if it's an error, try to parse it as an ApiResponse to get the structured errors.
    try {
      const payload = await response.json() as ApiResponse<T>;
      if (payload.meta && payload.errors) {
        return payload;
      }
    } catch {
      // Fallback if not JSON or doesn't match format
    }

    // Return a synthetic ApiResponse for network/generic errors
    return {
      data: null,
      meta: {
        status: "error",
        last_updated: null,
        source: "internal",
        is_stale: true,
        warnings: [],
        confidence: "none",
        processing_time_ms: null
      },
      errors: [{ code: "NETWORK_ERROR", message: `API request failed: ${response.status}` }]
    };
  }

  logApiSuccess("GET", path, response.status);
  try {
    return await response.json() as ApiResponse<T>;
  } catch {
    return {
      data: null,
      meta: {
        status: "error",
        last_updated: null,
        source: "internal",
        is_stale: true,
        warnings: [],
        confidence: "none",
        processing_time_ms: null
      },
      errors: [{ code: "PARSE_ERROR", message: "Failed to parse API response" }]
    };
  }
}

export async function createValuationModel(companyId: number, data: ValuationModelCreate): Promise<ValuationModel> {
  return postApi<ValuationModel>(`/companies/${companyId}/valuation-models`, data);
}

export async function getValuationModel(id: number): Promise<ValuationModel> {
  return fetchApi<ValuationModel>(`/valuation-models/${id}`);
}

export async function solveReverseDcf(request: ReverseDcfRequest): Promise<ReverseDcfResponse> {
  return postApi<ReverseDcfResponse>(`/dcf/reverse`, request);
}

export async function resolveStaleValuation(modelId: number, assumptionId: number): Promise<DcfAssumptionSet> {
  return postApi<DcfAssumptionSet>(`/valuation-models/${modelId}/assumptions/${assumptionId}/resolve-stale`, {});
}

export async function getValuationChangeLogs(modelId: number, assumptionId: number): Promise<ValuationAssumptionChangeLog[]> {
  return fetchApi<ValuationAssumptionChangeLog[]>(`/valuation-models/${modelId}/assumptions/${assumptionId}/change-logs`);
}

export async function createDcfAssumptionSet(modelId: number, data: DcfAssumptionSetCreate): Promise<DcfAssumptionSet> {
  return postApi<DcfAssumptionSet>(`/valuation-models/${modelId}/assumptions`, data);
}

export async function lookupCompanyByTicker(
  ticker: string,
  options: { market?: string; exchange?: string | null } = {}
): Promise<CompanyLookup> {
  const params = new URLSearchParams();
  if (options.market) {
    params.set("market", options.market);
  }
  if (options.exchange) {
    params.set("exchange", options.exchange);
  }
  params.set("ticker", ticker);
  return fetchApi<CompanyLookup>(`/companies/lookup?${params.toString()}`);
}

export async function listFinancialPeriods(companyId: number): Promise<FinancialStatementPeriod[]> {
  return fetchApi<FinancialStatementPeriod[]>(`/companies/${companyId}/financial-periods`);
}

export async function extractFinancialsFromFiling(filingId: number) {
  return postApi(`/api/filings/${filingId}/extract-financials`, {});
}

export async function extractXbrl(companyId: number) {
  return postApi(`/api/companies/${companyId}/extract-xbrl`, {});
}

export async function listExtractedFinancialCandidates(companyId: number): Promise<FinancialExtractionCandidate[]> {
  return fetchApi<FinancialExtractionCandidate[]>(`/api/companies/${companyId}/financial-statements/extracted`);
}

export async function getFinancialCandidate(candidateId: number): Promise<FinancialExtractionCandidate> {
  return fetchApi<FinancialExtractionCandidate>(`/api/financial-line-items/${candidateId}`);
}

export async function reviewFinancialCandidate(candidateId: number, reviewStatus: "needs_review" | "reviewed" | "rejected" | "overridden"): Promise<FinancialExtractionCandidate> {
  return patchApi<FinancialExtractionCandidate>(`/api/financial-line-items/${candidateId}/review`, { review_status: reviewStatus });
}

export async function overrideFinancialCandidate(candidateId: number, value: number, unit: string | null = null): Promise<FinancialExtractionCandidate> {
  return patchApi<FinancialExtractionCandidate>(`/api/financial-line-items/${candidateId}/override`, { value, unit });
}

export async function promoteFinancialCandidates(companyId: number): Promise<{ status: string; promoted_count: number }> {
  return postApi<{ status: string; promoted_count: number }>(`/api/companies/${companyId}/financial-statements/mark-reviewed`, {});
}

export async function listValuationModels(companyId: number): Promise<ValuationModel[]> {
  return fetchApi<ValuationModel[]>(`/companies/${companyId}/valuation-models`);
}

export async function getValuationModelAssumptions(modelId: number): Promise<DcfAssumptionSet[]> {
  return fetchApi<DcfAssumptionSet[]>(`/valuation-models/${modelId}/assumptions`);
}

export async function getDcfScenarios(modelId: number, assumptionId: number): Promise<DcfScenarioOutput[]> {
  return fetchApi<DcfScenarioOutput[]>(`/valuation-models/${modelId}/assumptions/${assumptionId}/scenarios`);
}

export async function listFilingSections(rawDocumentId: number): Promise<FilingSection[]> {
  return fetchApi<FilingSection[]>(`/raw-documents/${rawDocumentId}/sections`);
}

// Relative Valuation
export interface CountryMarketStats {
  country: string;
  firm_count?: number;
  market_cap_usd_millions?: number;
  total_debt_usd_millions?: number;
  firm_value_usd_millions?: number;
  cash_usd_millions?: number;
  enterprise_value_usd_millions?: number;
  median_current_pe?: number;
  median_trailing_pe?: number;
  median_forward_pe?: number;
  median_peg?: number;
  median_pbv?: number;
  median_ps?: number;
  median_ev_ebit?: number;
  median_ev_ebitda?: number;
  median_ev_invested_capital?: number;
  median_ev_sales?: number;
  median_cash_to_firm_value?: number;
  dividend_yield?: number;
  total_dividends_usd_millions?: number;
  date_updated?: string;
  source: PricingSourceProvenance;
}

export interface RelativeValuationResult {
  method: string;
  methodId: string;
  benchmarkMultiple: number;
  enterpriseValue?: number;
  equityValue?: number;
  valuePerShare?: number;
  reliability: string;
  claimType: "Calculation";
  source: PricingSourceProvenance;
}

export interface PricingSourceProvenance {
  sourceCode: "pe" | "pbv" | "ps" | "vebitda" | "countrystats";
  sourceFile: string;
  datasetVersionId: number;
  sourceSha256?: string;
  sourceAsOf?: string;
  dateConfidence: string;
  canonicalSourcePath?: string;
  claimType: "Fact";
}

export interface RelativeValuationResponse {
  industryName: string;
  relativeValues: RelativeValuationResult[];
  range?: {
    low: number;
    base: number;
    high: number;
  };
  diagnostics: string[];
  unavailableMethods: Array<{ method: string; reason: string }>;
  benchmarkSources: PricingSourceProvenance[];
}

export interface RelativeValuationRequest {
  companyId?: string;
  country: string;
  industryName: string;
  financials: {
    revenue?: number;
    ebitda?: number;
    ebit?: number;
    netIncome?: number;
    bookEquity?: number;
    investedCapital?: number;
    debt?: number;
    cash?: number;
    dilutedShares?: number;
  };
  methods: string[];
}

export async function getRelativeValuationCountries(): Promise<string[]> {
  return fetchApi<string[]>("/api/valuation/relative/countries");
}

export async function getRelativeValuationIndustries(country: string): Promise<string[]> {
  return fetchApi<string[]>(`/api/valuation/relative/countries/${encodeURIComponent(country)}/industries`);
}

export async function runRelativeValuation(request: RelativeValuationRequest): Promise<RelativeValuationResponse> {
  return postApi<RelativeValuationResponse>("/api/valuation/relative/run", request);
}


export async function parseFilingSections(rawDocumentId: number): Promise<{ status: string }> {
  return postApi<{ status: string }>(`/raw-documents/${rawDocumentId}/parse`, {});
}

export async function listAiOutputs(rawDocumentId: number): Promise<AiOutput[]> {
  return fetchApi<AiOutput[]>(`/raw-documents/${rawDocumentId}/ai-outputs`);
}

export async function generateAiSummary(rawDocumentId: number): Promise<AiOutput> {
  return postApi<AiOutput>(`/raw-documents/${rawDocumentId}/ai-summary`, {
    privacy_disclosure_version: AI_PRIVACY_DISCLOSURE_VERSION,
  });
}

export async function listPortfolioCashBalances(portfolioId: number): Promise<PortfolioCashBalance[]> {
  return fetchApi<PortfolioCashBalance[]>(`/portfolio-cash-balances?portfolio_id=${portfolioId}`);
}

export async function listPortfolioSnapshots(portfolioId: number): Promise<PortfolioSnapshot[]> {
  return fetchApi<PortfolioSnapshot[]>(`/portfolio-snapshots?portfolio_id=${portfolioId}`);
}

export async function exportData(resource_types: string[], export_format: string): Promise<Blob> {
  const url = `${getApiBaseUrl()}/data-transfer/export`;
  const response = await fetch(url, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ resource_types, export_format }),
  });

  if (!response.ok) {
    throw new Error(`Export failed with status ${response.status}`);
  }

  return response.blob();
}

// -- Phase 13 Types --

export type EvidenceLedgerItem = {
  id: number;
  company_id: number;
  evidence_text: string;
  effect: string; // Supports, Weakens, Contradicts, Neutral
  source_link: string | null;
  confidence: string;
  date_discovered: string;
  created_at: string;
  updated_at: string;
};

export type VariantPerception = {
  id: number;
  company_id: number;
  market_belief: string;
  my_belief: string;
  evidence_for_my_belief: string | null;
  evidence_against_my_belief: string | null;
  how_price_reflects_market_belief: string | null;
  what_would_close_the_gap: string | null;
  confidence: string;
  created_at: string;
  updated_at: string;
};

export type DecisionLog = {
  id: number;
  company_id: number;
  decision_type: string; // Buy, Sell, Hold, Trim, Pass
  rationale: string;
  price_at_time: number | null;
  emotional_state: string | null;
  alternatives_considered: string | null;
  outcome_review: OutcomeReview | null;
  created_at: string;
  updated_at: string;
};

export type OutcomeReview = {
  id: number;
  decision_log_id: number;
  what_happened: string;
  thesis_wrong: boolean;
  valuation_wrong: boolean;
  timing_wrong: boolean;
  sizing_wrong: boolean;
  information_unavailable_or_misinterpreted: boolean;
  lessons_learned: string | null;
  reviewed_at: string;
};

// -- Phase 13 Fetch Helpers --

export async function fetchEvidenceLedger(companyId?: number): Promise<EvidenceLedgerItem[]> {
  const url = companyId ? `/evidence?company_id=${companyId}` : "/evidence";
  return fetchApi<EvidenceLedgerItem[]>(url);
}

export async function createEvidence(payload: Omit<EvidenceLedgerItem, "id" | "created_at" | "updated_at">): Promise<EvidenceLedgerItem> {
  return postApi<EvidenceLedgerItem>("/evidence", payload);
}

export async function fetchVariantPerceptions(companyId?: number): Promise<VariantPerception[]> {
  const url = companyId ? `/variant-perceptions?company_id=${companyId}` : "/variant-perceptions";
  return fetchApi<VariantPerception[]>(url);
}

export async function createVariantPerception(payload: Omit<VariantPerception, "id" | "created_at" | "updated_at">): Promise<VariantPerception> {
  return postApi<VariantPerception>("/variant-perceptions", payload);
}

export async function fetchDecisionLogs(companyId?: number): Promise<DecisionLog[]> {
  const url = companyId ? `/decisions?company_id=${companyId}` : "/decisions";
  return fetchApi<DecisionLog[]>(url);
}

export async function createDecisionLog(payload: Omit<DecisionLog, "id" | "created_at" | "updated_at">): Promise<DecisionLog> {
  return postApi<DecisionLog>("/decisions", payload);
}

export async function postApi<T>(path: string, payload: unknown): Promise<T> {
  logApiStart("POST", path);
  const response = await fetch(`${getApiBaseUrl()}${path}`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify(payload)
  });

  if (!response.ok) {
    logApiFailure("POST", path, response.status);
    throw await apiError(response);
  }

  logApiSuccess("POST", path, response.status);
  return parseApiResponse<T>(response);
}

export async function postFormApi<T>(path: string, formData: FormData): Promise<T> {
  logApiStart("POST", path);
  const response = await fetch(`${getApiBaseUrl()}${path}`, {
    method: "POST",
    body: formData
  });

  if (!response.ok) {
    logApiFailure("POST", path, response.status);
    throw await apiError(response);
  }

  logApiSuccess("POST", path, response.status);
  return parseApiResponse<T>(response);
}

export const postApiFormData = postFormApi;

export async function patchApi<T>(path: string, payload: unknown): Promise<T> {
  logApiStart("PATCH", path);
  const response = await fetch(`${getApiBaseUrl()}${path}`, {
    method: "PATCH",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify(payload)
  });

  if (!response.ok) {
    logApiFailure("PATCH", path, response.status);
    throw await apiError(response);
  }

  logApiSuccess("PATCH", path, response.status);
  return parseApiResponse<T>(response);
}

export async function putApi<T>(path: string, payload: unknown): Promise<T> {
  logApiStart("PUT", path);
  const response = await fetch(`${getApiBaseUrl()}${path}`, {
    method: "PUT",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify(payload)
  });

  if (!response.ok) {
    logApiFailure("PUT", path, response.status);
    throw await apiError(response);
  }

  logApiSuccess("PUT", path, response.status);
  return parseApiResponse<T>(response);
}

export async function deleteApi(path: string): Promise<void> {
  logApiStart("DELETE", path);
  const response = await fetch(`${getApiBaseUrl()}${path}`, {
    method: "DELETE"
  });

  if (!response.ok) {
    logApiFailure("DELETE", path, response.status);
    throw await apiError(response);
  }

  logApiSuccess("DELETE", path, response.status);
}

export async function deleteScoringConfig(id: number): Promise<void> {
  const method = "DELETE";
  const path = `/scoring-configs/${id}`;
  logApiStart(method, path);

  const response = await fetch(`${getApiBaseUrl()}${path}`, {
    method,
  });

  if (!response.ok) {
    logApiFailure(method, path, response.status);
    throw await apiError(response);
  }

  logApiSuccess(method, path, response.status);
}

// -- Market Data --
export type CompanyMarketData = {
  current_price: number | null;
  change_percent: number | null;
  volume: number | null;
  market_cap: number | null;
  pe_ratio: number | null;
  fifty_two_week_high: number | null;
  fifty_two_week_low: number | null;
  last_updated: string;
};

export async function fetchMarketQuote(
  ticker: string,
  context: { market?: string | null; exchange?: string | null; currency?: string | null } = {}
): Promise<CompanyMarketData | null> {
  const method = "GET";
  const params = new URLSearchParams();
  if (context.market) {
    params.set("market", context.market);
  }
  if (context.exchange) {
    params.set("exchange", context.exchange);
  }
  params.set("ticker", ticker);
  if (context.currency) {
    params.set("currency", context.currency);
  }
  const path = context.market || context.exchange || context.currency
    ? `/api/market/quote?${params.toString()}`
    : `/market/quote/${ticker}`;
  logApiStart(method, path);

  const response = await fetch(`${getApiBaseUrl()}${path}`, {
    method,
    headers: { Accept: "application/json" },
    cache: "no-store",
  });

  if (!response.ok) {
    if (response.status === 404) return null;
    logApiFailure(method, path, response.status);
    throw await apiError(response);
  }

  logApiSuccess(method, path, response.status);
  return parseApiResponse<CompanyMarketData>(response);
}

// -- Financial Trends --
export type ChartFinancialMetric = {
  metric_name: string;
  value: number;
  unit: string | null;
};

export type FinancialPeriod = {
  period_type: string;
  year: number;
  quarter: number | null;
  report_date: string;
  metrics: FinancialMetric[];
};

export async function fetchFinancialTrends(ticker: string): Promise<FinancialPeriod[]> {
  const method = "GET";
  const path = `/fundamentals/${ticker}/trends`;
  logApiStart(method, path);

  const response = await fetch(`${getApiBaseUrl()}${path}`, {
    method,
    headers: { Accept: "application/json" },
    cache: "no-store",
  });

  if (!response.ok) {
    if (response.status === 404) return [];
    logApiFailure(method, path, response.status);
    throw await apiError(response);
  }

  logApiSuccess(method, path, response.status);
  return parseApiResponse<FinancialPeriod[]>(response);
}

export type ScoringConfig = {
  id: number;
  weight_credibility: number;
  weight_novelty: number;
  weight_impact: number;
  weight_speed: number;
};

export type MacroObservation = {
  id: number;
  series_id: number;
  date_recorded: string;
  value: number;
};

export type MacroSeries = {
  id: number;
  name: string;
  description: string | null;
  units: string | null;
  frequency: string | null;
  observations: MacroObservation[];
};

export type MacroSectorSensitivity = {
  market: string;
  country: string;
  classification_system: string;
  currency_context: string | null;
  currency_variable_description: string | null;
  raw_duration: number | null;
  duration_magnitude: number | null;
  duration_interpretation: string;
  sic_code: string;
  industry_name: string;
  source_file: string;
  firm_value_duration: number | null;
  firm_value_cyclicality: number | null;
  firm_value_inflation: number | null;
  firm_value_currency: number | null;
  operating_income_duration: number | null;
  operating_income_cyclicality: number | null;
  operating_income_inflation: number | null;
  operating_income_currency: number | null;
};

export type MacroScenarioRequest = {
  market: string;
  country: string;
  sic_code: string;
  rate_shock: number;
  gdp_shock: number;
  inflation_shock: number;
  currency_shock: number;
  currencyVariableDirection?: string | null;
};

export type MacroScenarioResult = {
  method: string;
  market: string;
  country: string;
  classification_system: string;
  currency_context: string | null;
  currency_variable_description: string | null;
  raw_duration: number | null;
  duration_magnitude: number | null;
  duration_interpretation: string;
  sic_code: string;
  industry_name: string;
  source_file: string;
  estimated_value_impact_pct: number;
  estimated_operating_income_impact_pct: number;
  affected_assumptions: string[];
  warnings: string[];
  formula: string;
  confidence: string;
};

export type BottomUpMacroSegment = {
  segment_name: string;
  sic_code?: string | null;
  benchmark_industry_name?: string | null;
  segment_value?: number | null;
  segment_revenue?: number | null;
  segment_weight?: number | null;
};

export type MacroSensitivityMetrics = {
  duration: number | null;
  cyclicality: number | null;
  inflation_sensitivity: number | null;
  currency_sensitivity: number | null;
};

export type MacroSensitivityResult = {
  method: string;
  observation_count: number | null;
  firm_value: MacroSensitivityMetrics;
  operating_income: MacroSensitivityMetrics;
  confidence_label: string | null;
  warnings: string[] | null;
};

export type TopDownMacroPeriod = {
  period_label: string;
  period_end_date?: string | null;
  operating_income?: number | null;
  market_cap?: number | null;
  total_debt?: number | null;
  cash?: number | null;
  enterprise_value?: number | null;
  change_in_long_term_bond_rate?: number | null;
  gdp_growth?: number | null;
  inflation_change?: number | null;
  currency_change?: number | null;
};

export async function fetchMacroSectorSensitivity(
  params: { market: string; country: string; sic: string }
): Promise<MacroSectorSensitivity> {
  const query = new URLSearchParams({
    market: params.market,
    country: params.country,
    sic: params.sic
  });
  return fetchApi<MacroSectorSensitivity>(`/api/valuation/macro/sector?${query.toString()}`);
}

export async function runMacroScenario(payload: MacroScenarioRequest): Promise<MacroScenarioResult> {
  return postApi<MacroScenarioResult>("/api/valuation/macro/scenario", payload);
}

export async function runBottomUpMacroSensitivity(
  payload: { market: string; country: string; segments: BottomUpMacroSegment[] }
): Promise<MacroSensitivityResult> {
  return postApi<MacroSensitivityResult>("/api/valuation/macro/bottom-up", {
    market: payload.market,
    country: payload.country,
    segments: payload.segments.map((segment) => ({
      name: segment.segment_name,
      sicCode: segment.sic_code,
      value: segment.segment_value ?? segment.segment_revenue ?? segment.segment_weight,
    })),
  });
}

export async function runTopDownMacroSensitivity(
  payload: { frequency?: string; periods: TopDownMacroPeriod[] }
): Promise<MacroSensitivityResult> {
  return postApi<MacroSensitivityResult>("/api/valuation/macro/top-down", {
    frequency: payload.frequency ?? "annual",
    periods: payload.periods.map((period) => ({
      period: period.period_label,
      operating_income: period.operating_income,
      market_cap: period.market_cap,
      total_debt: period.total_debt,
      enterprise_value: period.enterprise_value,
      change_in_long_term_bond_rate: period.change_in_long_term_bond_rate,
      gdp_growth: period.gdp_growth,
      inflation_change: period.inflation_change,
      currency_change: period.currency_change,
    })),
  });
}

// --- Real Options ---

export type VolatilityBenchmarkRead = {
  country: string;
  industry: string;
  numberOfFirms: number | null;
  equityStandardDeviation: number | null;
  firmValueStandardDeviation: number | null;
  equityValueWeight: number | null;
  debtValueWeight: number | null;
  assumptions: Record<string, number>;
  claimType: "Source Summary";
  datasetVersionId: number;
  sourceFile: string;
  sourceSha256: string;
  sourceAsOf: string;
  dateConfidence: string;
  canonicalSourcePath: string;
};

export type OptionEligibilityTestRequest = {
  valuation_id?: string | null;
  option_type: string;
  has_underlying_asset: boolean;
  has_finite_life: boolean;
  has_clear_exercise_price: boolean;
  has_asymmetric_payoff: boolean;
  has_exclusivity: boolean;
  can_estimate_volatility: boolean;
  can_estimate_underlying_value: boolean;
};

export type OptionEligibilityTestResponse = {
  eligibilityPassed: boolean;
  eligibilityScore: number;
  recommendation: string;
  warnings: string[];
};

export type RealOptionCalculateRequest = {
  valuation_id?: string | null;
  option_type: string;
  underlying_asset_value: number;
  exercise_price: number;
  option_life_years: number;
  risk_free_rate: number;
  volatility: number;
  dividend_yield_or_cost_of_delay: number;
  exclusivity_score: number;
  is_already_counted: boolean;
  base_dcf_value: number;
};

export type RealOptionCalculateResponse = {
  d1: number;
  d2: number;
  nd1: number;
  nd2: number;
  raw_option_value: number;
  adjusted_option_value: number;
  option_delta: number;
  option_adjusted_intrinsic_value: number | null;
  warnings: string[];
};

export async function fetchVolatilityBenchmark(country: string, industry: string): Promise<VolatilityBenchmarkRead> {
  return fetchApi<VolatilityBenchmarkRead>(`/api/valuation/options/volatility?country=${encodeURIComponent(country)}&industry=${encodeURIComponent(industry)}`);
}

export async function runOptionEligibilityTest(payload: OptionEligibilityTestRequest): Promise<OptionEligibilityTestResponse> {
  return postApi<OptionEligibilityTestResponse>("/api/valuation/options/eligibility", payload);
}

export async function calculateRealOption(payload: RealOptionCalculateRequest): Promise<RealOptionCalculateResponse> {
  return postApi<RealOptionCalculateResponse>("/api/valuation/options/calculate", payload);
}

export type TokenStatusResponse = {
  provider_name: string;
  is_connected: boolean;
  expires_at: string | null;
};

export async function fetchOAuthStatus(): Promise<TokenStatusResponse[]> {
  return fetchApi<TokenStatusResponse[]>("/oauth/status");
}

export type ProcessingRun = {
  id: number;
  run_type: string;
  source_type: string | null;
  source_id: number | null;
  company_id: number | null;
  started_at: string;
  finished_at: string | null;
  status: string;
  fetched_count: number;
  created_count: number;
  skipped_duplicate_count: number;
  error_count: number;
  error_details_json: Record<string, unknown> | null;
  metadata_json: Record<string, unknown> | null;
  created_at: string;
};

export type ProviderHealth = {
  provider_name: string;
  capability: string;
  market: string | null;
  status:
    | "configured"
    | "missing_key"
    | "working"
    | "failing"
    | "manual_only"
    | "not_configured"
    | "unsupported_market"
    | "unknown";
  configured: boolean;
  last_success_at: string | null;
  last_failure_at: string | null;
  failure_reason: string | null;
  freshness_label: string;
  notes: string | null;
  action_required: string | null;
  rate_limit_status: string | null;
  coverage_state: string | null;
};

export type ProviderHealthRead = ProviderHealth;

export interface DcfVariableImpact {
  variable_name: string;
  impact_direction: "increase" | "decrease" | "unknown";
  confidence: "high" | "medium" | "low";
  reasoning: string;
}

export interface DcfMappingResponse {
  status: string;
  data: {
    impacted_variables: DcfVariableImpact[];
    error?: string;
  };
  ai_metadata: {
    model_name: string;
    is_mock: boolean;
    confidence: string;
  };
}

export type CompanySetupSourceReadiness = {
  provider_name: string;
  capability: string;
  market: string;
  status: string;
  notes: string;
  action_required: string | null;
};

export type CompanySetupWorkflow = {
  id: number;
  company_id: number;
  current_step: string;
  identity_status: string;
  source_status: string;
  filing_status: string;
  financial_extraction_status: string;
  industry_mapping_status: string;
  valuation_readiness_status: string;
  security_review_status: string;
  source_readiness: CompanySetupSourceReadiness[];
  next_recommended_step: string;
  created_at: string;
  updated_at: string;
};

// Default export for client-side components that use api.get / api.post pattern
const api = {
  async get<T = unknown>(path: string): Promise<ApiResponse<T>> {
    const response = await fetch(`${getApiBaseUrl()}${path}`, {
      cache: "no-store",
    });
    if (!response.ok) {
      throw await apiError(response);
    }
    return response.json() as Promise<ApiResponse<T>>;
  },
  async post<T = unknown>(path: string, payload?: unknown): Promise<ApiResponse<T>> {
    const response = await fetch(`${getApiBaseUrl()}${path}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: payload ? JSON.stringify(payload) : undefined,
    });
    if (!response.ok) {
      throw await apiError(response);
    }
    return response.json() as Promise<ApiResponse<T>>;
  },
};
export async function fetchValuationContext(companyId: number): Promise<ValuationCompanyContext> {
  const url = `/api/valuation/context/company/${companyId}`;
  logApiStart("GET", url);
  const response = await fetch(`${getApiBaseUrl()}${url}`, {
    cache: "no-store",
  });
  if (!response.ok) {
    logApiFailure("GET", url, response.status);
    throw await apiError(response);
  }
  logApiSuccess("GET", url, response.status);
  return parseApiResponse<ValuationCompanyContext>(response);
}

// -- AI Valuation Services --

export type NarrativeToNumbersRequest = {
  narrative_text: string;
};

export type NarrativeToNumbersResponse = {
  target_operating_margin: number;
  target_operating_margin_reason: string;
  revenue_growth_years: Record<string, number>;
  revenue_growth_reason: string;
  sales_to_capital_ratio: number;
  sales_to_capital_reason: string;
  terminal_growth_rate: number;
  terminal_growth_reason: string;
  ai_meta?: ApiMeta;
};

export async function runNarrativeToNumbers(
  valuationId: number,
  scenario: string,
  payload: NarrativeToNumbersRequest
): Promise<NarrativeToNumbersResponse> {
  const response = await api.post<NarrativeToNumbersResponse>(
    `/valuation/${valuationId}/scenarios/${scenario}/ai/narrative-to-numbers`,
    {
      ...payload,
      privacy_disclosure_version: AI_PRIVACY_DISCLOSURE_VERSION,
    },
  );
  return { ...(response.data as NarrativeToNumbersResponse), ai_meta: response.meta };
}

export type ValuationMemoResponse = {
  memo_markdown: string | null;
  created_at?: string;
  confidence_label?: string;
  provider_name?: string;
  is_mock?: boolean;
  ai_output_id?: number;
};

export async function generateValuationMemo(valuationId: number, scenario: string): Promise<ValuationMemoResponse> {
  return postApi<ValuationMemoResponse>(`/valuation/${valuationId}/scenarios/${scenario}/ai/memo`, {
    privacy_disclosure_version: AI_PRIVACY_DISCLOSURE_VERSION,
  });
}

export async function fetchValuationMemo(valuationId: number, scenario: string): Promise<ValuationMemoResponse> {
  return fetchApi<ValuationMemoResponse>(`/valuation/${valuationId}/scenarios/${scenario}/ai/memo`);
}

// -- Regression Priors --

export type DebtRatioPriorRequest = {
  effective_tax_rate: number;
  expected_eps_growth: number;
  institutional_holdings: number;
  company_age_years: number;
  region?: "Global" | "US";
};

export type DividendYieldPriorRequest = {
  effective_tax_rate: number;
  expected_eps_growth: number;
  company_age_years: number;
  beta: number;
  region?: "Global" | "US";
};

export type DividendPayoutPriorRequest = {
  beta: number;
  return_on_equity: number;
  region?: "Global" | "US";
};

export type RegressionPriorResponse = {
  prior_value: number | null;
  formula: string;
  model: string;
  claim_type: "Estimate";
  confidence: "low" | "not_usable";
  source: string;
  source_path: string;
  source_as_of: string;
  adjusted_r_squared: number;
  input_units: Record<string, string>;
  output_unit: string;
  usable: boolean;
  warnings: string[];
};

export async function fetchDebtRatioPrior(payload: DebtRatioPriorRequest): Promise<RegressionPriorResponse> {
  return postApi<RegressionPriorResponse>(`/priors/debt-ratio`, payload);
}

export async function fetchDividendYieldPrior(payload: DividendYieldPriorRequest): Promise<RegressionPriorResponse> {
  return postApi<RegressionPriorResponse>(`/priors/dividend-yield`, payload);
}

export async function fetchDividendPayoutPrior(payload: DividendPayoutPriorRequest): Promise<RegressionPriorResponse> {
  return postApi<RegressionPriorResponse>(`/priors/dividend-payout`, payload);
}

// -- Metric Normalization --

export type NormalizedMetricRead = {
  id: number;
  metric_code: string;
  value: number;
  unit: string | null;
  provenance_notes: string | null;
  warnings: string | null;
};

export type NormalizedSnapshotRead = {
  id: number;
  company_id: number;
  period_id: number;
  created_at: string;
  updated_at: string;
  metrics: NormalizedMetricRead[];
};

export type NormalizedCoveragePeriod = {
  period_id: number;
  year: number;
  quarter: number | null;
  period_type: string;
  source_metric_count: number;
  normalized_metric_count: number;
  needs_backfill: boolean;
  trust_ready: boolean;
  reasons: string[];
  currency: string;
  currency_source: string;
  currency_confidence: string;
  currency_conflict: string | null;
};

export type NormalizedCoverage = {
  status: "no_data" | "partial" | "blocked" | "complete";
  period_count: number;
  normalized_period_count: number;
  coverage_percent: number;
  trust_ready_period_count: number;
  needs_backfill_count: number;
  conflict_count: number;
  low_confidence_currency_count: number;
  stale_snapshot_count: number;
  missing_snapshot_count: number;
  periods: NormalizedCoveragePeriod[];
  recommended_actions: string[];
};

export type FinancialReconciliationItem = {
  metric_code: string;
  source_metric_code: string | null;
  status: "exact" | "mismatch" | "missing_normalized" | "normalized_only";
  source_value: number | null;
  normalized_value: number | null;
  delta: number | null;
  delta_percent: number | null;
  source_unit: string | null;
  normalized_unit: string | null;
  provenance_notes: string | null;
  warnings: string | null;
};

export type FinancialReconciliationPeriod = {
  period_id: number;
  snapshot_id: number | null;
  year: number;
  quarter: number | null;
  period_type: string;
  status: "partial" | "blocked" | "complete";
  items: FinancialReconciliationItem[];
};

export type FinancialReconciliation = {
  status: "no_data" | "partial" | "blocked" | "complete";
  period_count: number;
  item_count: number;
  exact_count: number;
  mismatch_count: number;
  missing_normalized_count: number;
  normalized_only_count: number;
  periods: FinancialReconciliationPeriod[];
  recommended_actions: string[];
};

export type FinancialStatementIdentityCheck = {
  identity_code: string;
  label: string;
  formula: string;
  status: "passed" | "failed" | "not_available";
  actual_value: number | null;
  expected_value: number | null;
  delta: number | null;
  tolerance: number | null;
  unit: string;
  inputs: Record<string, number>;
  missing_metrics: string[];
  ambiguous_metrics: string[];
  blocking: boolean;
};

export type FinancialStatementIdentityPeriod = {
  period_id: number;
  year: number;
  quarter: number | null;
  period_type: string;
  report_date: string;
  currency: string;
  status: "passed" | "partial" | "failed" | "not_available";
  applicable_check_count: number;
  passed_check_count: number;
  failed_check_count: number;
  unavailable_check_count: number;
  checks: FinancialStatementIdentityCheck[];
};

export type FinancialStatementIdentityReport = {
  company_id: number;
  period_type: string;
  status: "passed" | "partial" | "failed" | "not_available";
  tolerance_contract: {
    absolute_tolerance: number;
    relative_tolerance: number;
    formula: string;
  };
  period_count: number;
  applicable_period_count: number;
  passed_period_count: number;
  partial_period_count: number;
  failed_period_count: number;
  unavailable_period_count: number;
  applicable_check_count: number;
  passed_check_count: number;
  failed_check_count: number;
  unavailable_check_count: number;
  periods: FinancialStatementIdentityPeriod[];
};

export async function normalizeFinancialPeriod(companyId: number, periodId: number): Promise<NormalizedSnapshotRead> {
  return postApi<NormalizedSnapshotRead>(`/api/companies/${companyId}/financial-statements/${periodId}/normalize`, {});
}

export async function listNormalizedSnapshots(companyId: number): Promise<NormalizedSnapshotRead[]> {
  return fetchApi<NormalizedSnapshotRead[]>(`/api/companies/${companyId}/financial-statements/normalized`);
}

export async function getNormalizedCoverage(companyId: number): Promise<NormalizedCoverage> {
  return fetchApi<NormalizedCoverage>(`/api/companies/${companyId}/financial-statements/normalized/coverage`);
}

export async function getFinancialReconciliation(companyId: number): Promise<FinancialReconciliation> {
  return fetchApi<FinancialReconciliation>(
    `/api/companies/${companyId}/financial-statements/normalized/reconciliation`,
  );
}

export async function getFinancialStatementIdentities(companyId: number): Promise<FinancialStatementIdentityReport> {
  return fetchApi<FinancialStatementIdentityReport>(
    `/api/companies/${companyId}/financial-statements/identities`,
  );
}

export type IndustryMappingCandidate = {
  industryName: string;
  confidence: string;
  reason: string;
  benchmarkAvailability?: Record<string, boolean>;
};

export type IndustryAllocation = {
  id?: number;
  segment_name: string;
  industry_name: string;
  weight_percent: number;
  benchmark_availability?: Record<string, boolean>;
  created_at?: string;
  updated_at?: string;
};

export type CompanyIndustryMix = {
  id: number;
  company_id: number;
  basis: "revenue";
  as_of_date: string | null;
  source_document_id: number | null;
  notes: string | null;
  primary_industry: string;
  total_weight_percent: number;
  claim_type: "User Assumption";
  coverage_status: "complete" | "partial" | "unavailable";
  benchmark_field_coverage: Record<string, Record<string, boolean>>;
  warnings: string[];
  allocations: IndustryAllocation[];
  created_at: string;
  updated_at: string;
};

export type CompanyIndustryMixInput = {
  basis: "revenue";
  as_of_date?: string | null;
  source_document_id?: number | null;
  notes?: string | null;
  allocations: Array<Pick<IndustryAllocation, "segment_name" | "industry_name" | "weight_percent">>;
};

export async function fetchIndustryMappingCandidates(companyId: number, country: string = "India"): Promise<IndustryMappingCandidate[]> {
  const query = new URLSearchParams({ country });
  return api.get<IndustryMappingCandidate[]>(`/companies/${companyId}/industry-mapping-candidates?${query.toString()}`).then(res => res.data as unknown as IndustryMappingCandidate[]);
}

export async function fetchAllIndustryCandidates(country: string = "India"): Promise<string[]> {
  const query = new URLSearchParams({ country });
  return api.get<string[]>(`/industries/candidates?${query.toString()}`).then(res => res.data as unknown as string[]);
}

export async function fetchIndustryMix(companyId: number): Promise<CompanyIndustryMix | null> {
  return fetchApi<CompanyIndustryMix | null>(`/companies/${companyId}/industry-allocations`);
}

export async function fetchRawDocumentSummaries(): Promise<RawDocument[]> {
  return fetchApi<RawDocument[]>("/raw-documents/summaries");
}

export async function saveIndustryMix(
  companyId: number,
  payload: CompanyIndustryMixInput,
): Promise<CompanyIndustryMix> {
  return putApi<CompanyIndustryMix>(`/companies/${companyId}/industry-allocations`, payload);
}

export async function confirmIndustryMapping(companyId: number, industry_name: string): Promise<Company> {
  return api.post<Company>(`/companies/${companyId}/industry-mapping`, { industry_name }).then(res => res.data as Company);
}

export type AssumptionProvenance = {
  source_type?: string;
  label?: string;
  confidence?: string;
  claim_type?: string;
  is_placeholder?: boolean;
  requires_review?: boolean;
  [key: string]: unknown;
};

export type AutofillSourceMetadata = {
  promotion_ready: boolean;
  requires_review: boolean;
  placeholder_fields: string[];
  review_fields: string[];
  source_counts_by_type: Record<string, number>;
  legacy_fallback_fields?: string[];
  stale_source_fields?: string[];
  freshness_unknown_fields?: string[];
  oldest_source_as_of?: string | null;
  latest_source_as_of?: string | null;
  unresolved_fields?: string[];
  reporting_currency?: string | null;
  reporting_currency_source?: string | null;
  reporting_currency_confidence?: string | null;
  industry_mix_id?: number;
  industry_mix_signature?: string;
  industry_mix_basis?: "revenue";
  industry_mix_as_of_date?: string | null;
  industry_mix_allocations?: Array<Pick<IndustryAllocation, "segment_name" | "industry_name" | "weight_percent">>;
};

export type AutofillAssumptionDraft = {
  assumptions: Partial<DcfAssumptionSet>;
  provenance: Record<string, AssumptionProvenance | string>;
  source_metadata: AutofillSourceMetadata;
  warnings: string[];
};

export type ValuationSetupDraft = {
  id: number;
  user_id: string;
  company_id: number;
  promoted_model_id: number | null;
  status: "draft" | "ready_to_value" | "promoted" | "archived";
  industry_name: string | null;
  assumptions_json: Record<string, unknown>;
  provenance_json: Record<string, AssumptionProvenance | string>;
  source_metadata_json: AutofillSourceMetadata;
  warnings_json: string[];
  reviewed_fields_json: string[];
  edited_fields_json: string[];
  created_at: string;
  updated_at: string;
};

export async function createOrReopenValuationDraft(companyId: number): Promise<ValuationSetupDraft> {
  return postApi<ValuationSetupDraft>(`/companies/${companyId}/valuation-drafts`, {});
}

export async function updateValuationDraft(
  draftId: number,
  assumptionsPatch: Record<string, unknown>,
  reviewedFields: string[],
  expectedUpdatedAt?: string,
): Promise<ValuationSetupDraft> {
  return patchApi<ValuationSetupDraft>(`/valuation-drafts/${draftId}`, {
    assumptions_patch: assumptionsPatch,
    reviewed_fields: reviewedFields,
    expected_updated_at: expectedUpdatedAt,
  });
}

export async function refreshValuationDraft(
  draftId: number,
  expectedUpdatedAt?: string,
): Promise<ValuationSetupDraft> {
  return postApi<ValuationSetupDraft>(`/valuation-drafts/${draftId}/refresh`, {
    expected_updated_at: expectedUpdatedAt,
  });
}

export async function resetValuationDraftFields(
  draftId: number,
  fields: string[],
  expectedUpdatedAt?: string,
): Promise<ValuationSetupDraft> {
  return postApi<ValuationSetupDraft>(`/valuation-drafts/${draftId}/reset`, {
    fields,
    expected_updated_at: expectedUpdatedAt,
  });
}

export async function archiveValuationDraft(
  draftId: number,
  expectedUpdatedAt?: string,
): Promise<ValuationSetupDraft> {
  return postApi<ValuationSetupDraft>(`/valuation-drafts/${draftId}/archive`, {
    expected_updated_at: expectedUpdatedAt,
  });
}

export async function draftAutofillAssumptions(companyId: number, base_assumptions: Record<string, any> = {}): Promise<AutofillAssumptionDraft> {
  return api.post<AutofillAssumptionDraft>(`/companies/${companyId}/valuation-models/autofill`, { base_assumptions }).then(res => res.data as AutofillAssumptionDraft);
}

export type EventThesisImpact = {
  id: number;
  event_id: number;
  thesis_assumption_id: number;
  impact_classification: string;
  rationale: string;
  created_at: string;
};

export async function classifyEventImpact(eventId: number): Promise<{ message: string }> {
  return api.post<{ message: string }>(`/events/${eventId}/classify-impact`, {
    privacy_disclosure_version: AI_PRIVACY_DISCLOSURE_VERSION,
  }).then(res => res.data as { message: string });
}

export default api;

export async function uploadScreenerExport(companyId: number, file: File) {
  const formData = new FormData();
  formData.append("file", file);
  return postFormApi<{ status: string; extracted_count: number }>(
    `/api/companies/${companyId}/fundamentals/screener`,
    formData,
  );
}

export async function fetchLatestMarketPrice(companyId: number) {
  return postApi(`/market-prices/fetch-latest?company_id=${companyId}`, {});
}

export type MarketRegimeScoreRead = {
  id: number;
  score_date: string;
  overall_score: number;
  options_score: number | null;
  liquidity_score: number | null;
  volume_score: number | null;
  breadth_score: number | null;
  macro_score: number | null;
  confidence: string;
  warnings: string[];
  mode: string;
  live_modules: string[];
  manual_modules: string[];
  simulated_modules: string[];
  created_at: string;
};

export type MarketRegimeInputCreate = {
  metric_name: string;
  value: number;
  as_of_date: string;
  source_url: string | null;
};

export type MarketRegimeInputRead = MarketRegimeInputCreate & {
  id: number;
  created_at: string;
};

export async function submitMarketRegimeInput(data: MarketRegimeInputCreate): Promise<MarketRegimeInputRead> {
  return postApi<MarketRegimeInputRead>("/market-regime/inputs", data);
}

export async function fetchCurrentMarketRegime(): Promise<MarketRegimeScoreRead> {
  return fetchApi<MarketRegimeScoreRead>("/market-regime/current");
}
