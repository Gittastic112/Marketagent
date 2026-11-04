/** Owner-scoped external AI permission management. Reads do not grant permission. */
import { fetchApi, postApi } from "./transport.ts";

export type AIConsentState = "granted" | "refused" | "revoked";
export type AIConsentDecision = {
  id: number; provider_name: string; action_key: string; revision: number;
  state: AIConsentState; disclosure_version: string; scope_hash: string;
  external_data_classes: string[]; created_at: string;
};
export type AIConsentAction = {
  provider_name: "gemini"; action_key: string; label: string; description: string;
  external_data_classes: string[]; disclosure_version: string; scope_hash: string;
  state: AIConsentState | "not_granted" | "outdated"; current_revision: number;
  latest_decision: AIConsentDecision | null;
};
export type AIConsentOverview = { actions: AIConsentAction[]; limitations: string[] };
export type AIConsentHistory = { items: AIConsentDecision[]; next_cursor: number | null };
export type AIConsentDecisionRequest = {
  provider_name: "gemini"; action_key: string; state: AIConsentState;
  disclosure_version: string; scope_hash: string; expected_revision: number;
};

export const fetchAIConsent = () => fetchApi<AIConsentOverview>("/ai/consent");
export const fetchAIConsentHistory = (cursor?: number) =>
  fetchApi<AIConsentHistory>(`/ai/consent/history${cursor === undefined ? "" : `?cursor=${cursor}`}`);
export const saveAIConsentDecision = (request: AIConsentDecisionRequest) =>
  postApi<AIConsentDecision>("/ai/consent/decisions", request);
