import { fetchApi, postApi } from "./transport.ts";

export type TriageSuggestion = { field: string; direction: "increase" | "decrease" | "review"; reason: string;
  comparison_context?: { period: string; currency: string; economic_scope: string } };
export type TriageFinding = {
  title: string; importance: "high" | "medium" | "low"; importance_reason: string;
  quote: string; confidence: string; start_char: number; end_char: number; page: number | null;
  valuation_inputs: TriageSuggestion[];
};
export type TriageSource = {
  id: number; title: string; source_kind: string; as_of_date: string | null; source_sha256: string;
  created_at: string; ai_output_id: number; provider: string; model: string; prompt_version: string;
  input_hash: string; generated_at: string; is_mock: boolean; review_status: string;
  reviewed_at: string | null; lifecycle_version: number;
  warnings: string[]; findings: TriageFinding[];
};
export type TriageFindingRef = { source_id: number; finding_index: number };
export type TriageGroup = {
  field: string; label: string; review_href: string;
  status: "opposing_directions" | "mixed_within_content" | "no_opposition_detected";
  opposition_basis: Array<"stored_sources" | "mock_data">;
  source_count: number; distinct_content_count: number; highest_importance: string;
  items: Array<TriageFindingRef & { suggestion_index: number }>;
  comparability_status?: "same" | "unknown" | "incompatible";
  comparability?: Record<string, { labels: string[]; missing_count: number; status: "same" | "unknown" | "incompatible" }>;
};
export type BriefTriage = {
  company_id: number; company_name: string; ticker: string; claim_type: "Calculation";
  methodology: string; computed_at: string; include_mock: boolean; evidence_hash: string; reviews: ComparisonReview[];
  coverage: { active_sources: number; archived_sources: number; examined_sources: number; included_sources: number;
    not_examined: number; source_limit: number; excluded: Record<string, number> };
  sources: TriageSource[]; groups: TriageGroup[]; unmapped_findings: TriageFindingRef[]; warnings: string[];
};
export const fetchBriefTriage = (companyId: number, includeMock: boolean) =>
  fetchApi<BriefTriage>(`/brief-sources/triage?${new URLSearchParams({ company_id: String(companyId), include_mock: String(includeMock) })}`);

export type ReviewDisposition = "investigate" | "keep_input" | "revisit_input" | "not_relevant";
export type ComparisonReview = {
  id: number; company_id: number; field: string; include_mock: boolean; version: number;
  evidence_hash: string; disposition: ReviewDisposition; notes: string; created_at: string;
  is_current: boolean; claim_type: "User Assumption";
};
export type ComparisonReviewWrite = {
  company_id: number; field: string; include_mock: boolean; expected_version: number; evidence_hash: string;
  disposition: ReviewDisposition; notes: string; evidence_reviewed: true;
};
export type ComparisonReviewDetail = ComparisonReview & { evidence: {
  company_id: number; company_name: string; ticker: string; include_mock: boolean; methodology: string;
  compared_at: string; coverage: BriefTriage["coverage"]; group: TriageGroup; sources: TriageSource[];
} };
export const saveComparisonReview = (payload: ComparisonReviewWrite) => postApi<ComparisonReview>("/brief-sources/triage/reviews", payload);
export const fetchComparisonHistory = (companyId: number, field: string, includeMock: boolean, beforeId?: number) => {
  const params = new URLSearchParams({ company_id: String(companyId), field, include_mock: String(includeMock), limit: "20" });
  if (beforeId !== undefined) params.set("before_id", String(beforeId));
  return fetchApi<ComparisonReview[]>(`/brief-sources/triage/reviews?${params}`);
};
