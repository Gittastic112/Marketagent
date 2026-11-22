import type { DcfAssumptionSet, DiagnosticWarning } from "./valuation";
import { postApi } from "./transport.ts";

export type ValuationPreview = {
  model_id: number; base_assumption_set_id: number | null; base_assumption_set_updated_at: string | null;
  valuation_date: string | null; preview_hash: string; ready: boolean; missing_fields: string[];
  changes: { field: string; previous: unknown; proposed: unknown }[];
  previous_output: Record<string, number | null> | null; proposed_output: Record<string, number | null> | null;
  diagnostics: DiagnosticWarning[]; currency: string | null; limitations: string[];
};
export type ValuationVersionReceipt = {
  draft_id?: number | null; sources?: import("./first-valuation.ts").DraftBinding[] | null;
  assumption_set_id: number; previous_assumption_set_id: number | null; valuation_date: string | null;
  reason: string | null; saved_at: string; preview_hash: string | null;
};
export const previewValuationVersion = (modelId: number, payload: Record<string, unknown>) =>
  postApi<ValuationPreview>(`/valuation-models/${modelId}/assumptions/preview`, payload);
export const saveReviewedValuationVersion = (modelId: number, payload: Record<string, unknown>) =>
  postApi<DcfAssumptionSet>(`/valuation-models/${modelId}/assumptions`, payload);
