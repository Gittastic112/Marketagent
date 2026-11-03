/** Contracts and endpoint helpers for research. Import transport directly, never the compatibility facade. */
import { fetchApi, postApi } from "./transport.ts";
import type { AiOutput } from "./ai.ts";
import { AI_PRIVACY_DISCLOSURE_VERSION } from "../ai-privacy.ts";

export type ResearchMessage = {id: number; role: string; content: string; created_at: string; ai_output: AiOutput | null};
export type ResearchSession = {id: number; title: string; messages: ResearchMessage[]};

export function fetchResearchSession(id: string): Promise<ResearchSession> {
  return fetchApi<ResearchSession>(`/research/sessions/${encodeURIComponent(id)}`);
}

export function sendResearchMessage(id: string, content: string): Promise<ResearchMessage> {
  return postApi<ResearchMessage>(`/research/sessions/${encodeURIComponent(id)}/messages`, {
    role: "user", content, privacy_disclosure_version: AI_PRIVACY_DISCLOSURE_VERSION,
  });
}

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
  what_happened: string;
  wrong_assumption: string | null;
  thesis_wrong: boolean;
  valuation_wrong: boolean;
  timing_wrong: boolean;
  sizing_wrong: boolean;
  information_unavailable_or_misinterpreted: boolean;
  created_at: string;
};

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
