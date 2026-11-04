/** Contracts and endpoint helpers for daily-brief. Import transport directly, never the compatibility facade. */
import type { SavedBriefResearchContext } from "./brief-context";

export type BriefSelectionCounts = {
  eligible_count: number | null;
  included_count: number;
  excluded_count: number | null;
  cap: number | null;
  status: "complete" | "partial" | "unknown";
  exclusion_reasons: Record<string, number>;
};

export type BriefPublicCoverage = {
  version: "public-brief-coverage-v1";
  captured_at: string;
  window_start_exclusive: string | null;
  window_end_inclusive: string | null;
  selection_basis: "since_last_review" | "stored_history" | "dashboard_preview" | "caller_supplied";
  event_timestamp_basis: "created_at";
  failed_run_timestamp_basis: "started_at";
  inspection_action_basis: "derived_from_included_inputs";
  status: "complete" | "partial" | "unknown";
  provider_coverage: "not_assessed";
  source_verification: "not_assessed";
  events: BriefSelectionCounts;
  failed_runs: BriefSelectionCounts;
  inspection_actions: BriefSelectionCounts;
  limitations: string[];
};

export type DailyBriefPayload = {
  private_research?: SavedBriefResearchContext | null;
  public_coverage?: BriefPublicCoverage | null;
  summary: string;
  calculation_status: "complete" | "partial" | "not_available";
  valuation_analysis_status: "complete" | "partial" | "failed" | "not_run" | "not_required";
  contradiction_analysis_status: "complete" | "partial" | "failed" | "not_run" | "not_required";
  last_reviewed_at: string | null;
  new_since_last_review: {
    filings: Array<{
      ticker: string;
      form_type: string;
      headline: string;
      event_id: number;
      status: "New" | "Unresolved" | "Stale" | "Reviewed";
      raw_document_id: number | null;
      source_name: string | null;
      source_url: string | null;
      source_published_at: string | null;
      event_created_at: string | null;
      claim_type: "Source Summary" | "User Assumption";
      evidence_status: "source_linked" | "manual";
    }>;
    portfolio_moves: Array<{
      ticker: string;
      event_headline: string;
      event_id: number;
      move_percent: number | null;
      calculation_status: "complete" | "stale" | "not_available";
      claim_type: "Calculation" | "Unavailable";
      price_start_date: string | null;
      price_end_date: string | null;
      price_currency: string | null;
      price_provider: string | null;
      source_market_price_ids: number[];
      affected_portfolios: Array<{ portfolio_id: number; portfolio_name: string }>;
      warnings: string[];
      contains_mock_data: boolean;
    }>;
  };
  high_materiality_events: Array<{
    headline: string;
    priority: string;
    event_id: number;
    priority_score: number | null;
    ticker: string | null;
    event_type: string | null;
    status: "New" | "Unresolved" | "Stale" | "Reviewed";
    raw_document_id: number | null;
    source_name: string | null;
    source_url: string | null;
    source_published_at: string | null;
    event_created_at: string | null;
    claim_type: "Source Summary" | "User Assumption";
    evidence_status: "source_linked" | "manual";
  }>;
  thesis_contradictions: Array<{
    assumption: string;
    evidence: string | null;
    alert_id: number;
    event_id: number | null;
    raw_document_id: number | null;
    review_status: string;
    claim_type: "AI Interpretation";
  }>;
  thesis_confirmations: unknown[];
  valuation_relevance: Array<{
    event_id: number;
    headline: string;
    variable: string | null;
    direction: string | null;
    reasoning: string | null;
    confidence: string | null;
    claim_type: "AI Interpretation";
    ai_output_id: number | null;
    model_name: string | null;
    prompt_version: string | null;
    review_status: string;
    raw_document_id: number | null;
  }>;
  processing_failures: Array<{
    processing_run_id: number;
    run_type: string;
    source_type: string | null;
    status: string;
    error_count: number;
    started_at: string;
    finished_at: string | null;
    claim_type: "Fact";
  }>;
  inspection_queue: Array<{
    action_id: string;
    action_type: "review_contradiction" | "inspect_processing_failure" | "add_market_prices" | "resolve_event_evidence";
    priority: "high" | "medium" | "low";
    title: string;
    reason: string;
    href: string;
    claim_type: "Calculation";
    source_event_ids: number[];
    source_raw_document_ids: number[];
    source_market_price_ids: number[];
    source_alert_ids: number[];
    processing_run_id: number | null;
  }>;
  warnings: string[];
  contains_mock_data: boolean;
  contains_stale_data: boolean;
  source_event_ids: number[];
  source_raw_document_ids: number[];
  source_market_price_ids: number[];
  source_alert_ids: number[];
};

export type DailyBrief = {
  id: number;
  brief_date: string;
  title: string;
  summary: string;
  payload_json: DailyBriefPayload;
  review_status: string;
  reviewed_at: string | null;
  created_at: string;
};

export type SavedDailyBrief = DailyBrief;

export type DailyBriefSchedule = {
  id: number;
  enabled: boolean;
  timezone: string;
  local_time: string;
  days_of_week: number[];
  next_run_at: string | null;
  due_now: boolean;
  last_attempted_at: string | null;
  last_succeeded_at: string | null;
  last_status: string;
  last_processing_run_id: number | null;
  last_brief_id: number | null;
  generation_mode: "deterministic_no_external_ai";
  created_at: string;
  updated_at: string;
};

export type DailyBriefScheduleRunResult = {
  schedules_checked: number;
  schedules_completed: number;
  briefs_created: number;
  failures: number;
};
