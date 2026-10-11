import { fetchApi, postApi } from "./transport.ts";

export type ExpectedFinancialMetric = {
  metric_code: string; value: number; unit: string; fiscal_year: number;
  period_type: "annual" | "quarterly"; source_line_number: number;
};
export type EvaluationBasis = {
  document_id: number; title: string; source_text_sha256: string;
  source_content_hash: string; line_count: number; extractor_version: string; is_mock: boolean;
};
export type EvaluationReport = EvaluationBasis & {
  evaluator_version: string; reference_sha256: string; reference: ExpectedFinancialMetric[];
  is_mock: boolean; predicted_count: number; expected_count: number; true_positive_count: number;
  false_positive_count: number; false_negative_count: number; precision: number | null;
  recall: number; unit_accuracy: number | null; numeric_accuracy: number | null;
  period_accuracy: number | null; source_locator_accuracy: number | null;
  formula: string; limitations: string[];
  comparisons: Array<{ metric_code: string; source_line_number: number; exact_match: boolean;
    value_matches: boolean; unit_matches: boolean; period_matches: boolean; locator_matches: boolean }>;
};
export type EvaluationRun = {
  id: number; run_name: string; evaluation_type: string; status: string;
  created_at: string; completed_at: string | null; report_json: EvaluationReport | null;
};
export type FinancialEvaluationRequest = {
  run_name: string; document_id: number; source_text_sha256: string;
  reference_reviewed: true; reference_is_complete: true; is_mock: boolean;
  expected: ExpectedFinancialMetric[];
};
export const getEvaluationBasis = (documentId: number) => fetchApi<EvaluationBasis>(`/evaluations/documents/${documentId}/basis`);
export const executeFinancialEvaluation = (payload: FinancialEvaluationRequest) => postApi<EvaluationRun>("/evaluations/runs", payload);
