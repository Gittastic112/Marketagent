/** Contracts and endpoint helpers for ai. Import transport directly, never the compatibility facade. */
import api from "./transport.ts";
import type { ApiMeta, ApiResponse } from "./contract.ts";
import { fetchApi, postApi } from "./transport.ts";
import { AI_PRIVACY_DISCLOSURE_VERSION } from "../ai-privacy.ts";

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
  // Persisted JSON can contain legacy or malformed provider metadata. Consumers
  // validate it before showing citations or enabling approval.
  citations_json: Array<Record<string, unknown>>;
  citation_validation_status: string;
  evaluation_json: Record<string, unknown> | null;
  privacy_disclosure_version: string;
  consent_decision_id?: number | null;
  external_data_classes_json: string[];
  transmission_scope: string;
  execution_status: string;
  failure_code: string | null;
  is_blocked: boolean;
  output_text: string;
  limitations: string | null;
  confidence_label: string;
  human_review_status: string;
  review_notes: string | null;
  reviewer_id: string | null;
  reviewed_at: string | null;
  created_at: string;
};

export type AiCitationSuggestionCandidate = {
  quote: string;
  start_char: number;
  end_char: number;
  score: number;
  confidence: "high" | "medium" | "low";
  matched_terms: string[];
  claim_term_count: number;
  matched_term_count: number;
  internal_href: string;
};

export type AiCitationSuggestion = {
  source_id: string;
  claim_text: string | null;
  source_title: string | null;
  status:
    | "ready"
    | "no_candidate"
    | "source_text_unavailable"
    | "unsupported_source"
    | "undeclared_source"
    | "claim_text_unavailable";
  candidates: AiCitationSuggestionCandidate[];
  limitations: string[];
};

export async function listAiOutputs(rawDocumentId: number): Promise<AiOutput[]> {
  return fetchApi<AiOutput[]>(`/raw-documents/${rawDocumentId}/ai-outputs`);
}

export async function generateAiSummary(rawDocumentId: number): Promise<AiOutput> {
  return postApi<AiOutput>(`/raw-documents/${rawDocumentId}/ai-summary`, {
    privacy_disclosure_version: AI_PRIVACY_DISCLOSURE_VERSION,
  });
}

export async function fetchAiCitationSuggestions(outputId: number): Promise<AiCitationSuggestion[]> {
  return fetchApi<AiCitationSuggestion[]>(`/ai-outputs/${outputId}/citations/suggestions`);
}

export interface DcfVariableImpact {
  variable_name: string;
  impact_direction: "increase" | "decrease" | "unknown";
  confidence: "high" | "medium" | "low";
  reasoning: string;
}

export type DcfMappingResponse = ApiResponse<{
  impacted_variables: DcfVariableImpact[];
  ai_output_id: number;
  model_name: string;
  ai_output: AiOutput;
  error?: string;
}>;

export async function mapEventToDcf(eventId: number, eventText: string): Promise<DcfMappingResponse> {
  return api.post("/ai/research/map-event-to-dcf", {event_id: eventId, event_text: eventText,
    privacy_disclosure_version: AI_PRIVACY_DISCLOSURE_VERSION});
}

export type NarrativeToNumbersRequest = {
  narrative_text: string;
  assumption_set_id?: number;
  assumptions_updated_at?: string;
};

export type ValuationAIEvidence = {
  assumption_set_id: number; assumptions_updated_at?: string; valuation_model_id: number;
  scenario: string; output_id?: number | null; output_calculated_at?: string | null; currency?: string | null;
  ai_output_id: number; claim_type: "AI Interpretation"; is_current: boolean; basis_verified: boolean;
  provider_name: string; model_name: string; prompt_version: string; input_hash: string;
  source_ids: string[]; generated_at: string; review_status: string; is_mock: boolean;
  confidence_label: string; limitations: string | null; interpretation_quality: "not_evaluated";
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
  evidence?: ValuationAIEvidence;
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
  evidence?: ValuationAIEvidence;
};

export async function generateValuationMemo(valuationId: number, scenario: string,
  basis?: {assumption_set_id: number; assumptions_updated_at: string}): Promise<ValuationMemoResponse> {
  return postApi<ValuationMemoResponse>(`/valuation/${valuationId}/scenarios/${scenario}/ai/memo`, {
    privacy_disclosure_version: AI_PRIVACY_DISCLOSURE_VERSION,
    ...basis,
  });
}

export async function fetchValuationMemo(valuationId: number, scenario: string, assumptionId?: number): Promise<ValuationMemoResponse> {
  const suffix = assumptionId === undefined ? "" : `?assumption_set_id=${assumptionId}`;
  return fetchApi<ValuationMemoResponse>(`/valuation/${valuationId}/scenarios/${encodeURIComponent(scenario)}/ai/memo${suffix}`);
}
