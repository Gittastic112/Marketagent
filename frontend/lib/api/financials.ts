/** Contracts and endpoint helpers for financials. Import transport directly, never the compatibility facade. */
import { fetchApi, fetchApiOrNotFound, patchApi, postApi, postFormApi } from "./transport.ts";

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
  return fetchApiOrNotFound<FinancialPeriod[]>(`/fundamentals/${ticker}/trends`, []);
}

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

export async function uploadScreenerExport(companyId: number, file: File) {
  const formData = new FormData();
  formData.append("file", file);
  return postFormApi<{ status: string; extracted_count: number }>(
    `/api/companies/${companyId}/fundamentals/screener`,
    formData,
  );
}
