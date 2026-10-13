/** Contracts and endpoint helpers for operations. Import transport directly, never the compatibility facade. */
import { fetchApi } from "./transport.ts";
import { ApiError } from "./contract.ts";

export type RuntimeReadiness = {
  status: "ready" | "blocked";
  database_status: "ready" | "unavailable";
  schema_status: "ready" | "blocked" | "unknown";
  expected_migration_head: string;
  current_migration_heads: string[];
  missing_tables: string[];
  missing_columns: string[];
  missing_constraints: string[];
  recovery_steps: string[];
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

/** @deprecated Bulk export has no backend endpoint. The Data page exposes supported resource exports. */
export async function exportData(_resource_types: string[], _export_format: string): Promise<Blob> {
  throw new ApiError("Not available yet. Use the individual resource exports on the Data page.", 501);
}

/** @deprecated No deletion endpoint exists. Use the scoring settings update workflow. */
export async function deleteScoringConfig(_id: number): Promise<void> {
  throw new ApiError("Not available yet. Scoring configuration deletion is unsupported.", 501);
}

export type ScoringConfig = {
  id: number;
  weight_credibility: number;
  weight_novelty: number;
  weight_impact: number;
  weight_speed: number;
};

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
  requirement_level: "core" | "optional" | "manual";
  market: string | null;
  status:
    | "configured"
    | "missing_key"
    | "working"
    | "running"
    | "partial"
    | "failing"
    | "manual_only"
    | "not_configured"
    | "unsupported_market"
    | "mock"
    | "unknown";
  configured: boolean;
  last_attempt_at: string | null;
  latest_run_status: string | null;
  recent_run_count: number;
  consecutive_failures: number;
  data_age_hours: number | null;
  freshness_threshold_hours: number | null;
  configured_source_count: number | null;
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
