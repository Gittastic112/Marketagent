import { postApi, putApi } from "./transport.ts";
import type { ValuationSetupDraft } from "./valuation-drafts.ts";

export type DraftSource = { kind: "source_fact_revision"; id: number; target_field: string };
export type DraftBinding = { ref: DraftSource; status: "eligible" | "held"; reason?: string | null; conversion?: string | null;
  source?: import("./dated-inputs.ts").DatedInputSource | null };
export type FirstCommand = { name: string; description: string | null; model_type: string;
  expected_updated_at: string; valuation_date: string };
export type FirstPreview = { ready: boolean; preview_hash: string; blockers: string[];
  proposed_output: Record<string, number | null> | null; currency: string | null; sources: DraftBinding[];
  diagnostics: Record<string,unknown>[] };
export function chooseDraftSources(id: number, version: string, day: string, selections: DraftSource[]) {
  return putApi<ValuationSetupDraft>(`/valuation-drafts/${id}/source-proposal`, {
    expected_updated_at: version, valuation_date: day, selections });
}
export const previewFirstModel = (id: number, command: FirstCommand) =>
  postApi<FirstPreview>(`/valuation-drafts/${id}/preview`, command);
export const confirmFirstModel = (id: number, command: FirstCommand & {preview_hash: string; submission_id: string; reason: string}) =>
  postApi<{model_id: number; assumption_set_id: number; replayed: boolean}>(`/valuation-drafts/${id}/confirm`, command);
