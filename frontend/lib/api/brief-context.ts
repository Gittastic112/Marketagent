import type { ComparisonReview, TriageSource } from "./brief-triage";

/** Preserved historical JSON. Its fields are not current reviewed-source receipts. */
export type LegacyBriefResearchContext = { version: 1; [field: string]: unknown };
export type SavedBriefResearchContext = BriefResearchContext | LegacyBriefResearchContext;

export type BriefResearchDecision = {
  company_id: number; ticker: string; field: string; comparison_hash: string;
  comparability_status: "same" | "unknown" | "incompatible"; source_ids: number[];
  receipt: ComparisonReview | null;
  state: "reviewed" | "pending_ai_review" | "missing_receipt" | "stale_receipt" | "incompatible_basis" | "incomplete_source_snapshot";
  href: string;
};

export type BriefResearchContext = {
  version: "private-research-snapshot-v1"; captured_at: string; as_of_date: string;
  status: "empty" | "partial" | "complete"; basis: "as_generated"; input_sha256: string;
  company_count: number; company_limit: number; source_limit: number; decision_limit: number;
  excluded: Record<string, number>;
  sources: Array<{ source: TriageSource; content_hash: string; freshness: "historical" | "dated_today" | "unknown"; claim_type: "AI Interpretation"; href: string }>;
  reviewed: BriefResearchDecision[]; review_queue: BriefResearchDecision[]; limitations: string[];
};
