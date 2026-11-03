/** Contracts and endpoint helpers for evidence. Import transport directly, never the compatibility facade. */
import api from "./transport.ts";
import { AI_PRIVACY_DISCLOSURE_VERSION } from "../ai-privacy.ts";

export type EvidenceSearchResult = {
  result_type:
    | "document"
    | "event"
    | "alert"
    | "thesis"
    | "decision"
    | "valuation"
    | "narrative"
    | "research_session"
    | "research_message"
    | "ai_output";
  record_id: number;
  company_id: number | null;
  title: string;
  excerpt: string | null;
  rank: number;
  claim_type: "Fact" | "Source Summary" | "User Assumption" | "AI Interpretation";
  scope: "shared" | "private";
  review_status: "not_applicable" | "approved";
  is_mock: boolean;
  source_name: string | null;
  source_timestamp: string | null;
  href: string;
  locator: Record<string, unknown> | null;
};

export type EventRecord = {
  id: number;
  company_id: number | null;
  raw_document_id: number | null;
  event_type: string;
  information_speed: string;
  title: string;
  description: string | null;
  credibility_score: number | null;
  novelty_score: number | null;
  impact_score: number | null;
  priority_score: number | null;
  data_confidence_score: number | null;
  score_explanation_json: ScoreExplanation | null;
  corroborates?: EventLinkSummary[];
  contradicts?: EventLinkSummary[];
};

export type EventLinkSummary = {
  id: number;
  title: string;
  event_type: string;
};

export type IntelligenceReviewItem = {
  item_type: "contradiction" | "filing_language_change";
  item_id: string;
  company_id: number | null;
  title: string;
  summary: string;
  severity: "low" | "medium" | "high";
  claim_type: "User Assumption" | "Calculation";
  evidence_href: string;
  source_timestamp: string;
  section_name: string | null;
  added_words: number | null;
  removed_words: number | null;
};

export type ScoreExplanationInput = {
  name: string;
  value: number;
  weight: number;
  contribution: number;
  explanation: string;
};

export type ScoreExplanation = {
  score_name: string;
  value: number;
  label: string;
  direction: string;
  confidence: string;
  inputs: ScoreExplanationInput[];
  summary: string;
};

export type AlertPortfolioImpact = {
  id: number;
  alert_id: number;
  portfolio_id: number;
  exposure_amount: number;
  impact_score: number;
  created_at: string;
};

export type AlertRecord = {
  id: number;
  event_id: number | null;
  company_id: number | null;
  alert_type: string;
  severity: string;
  title: string;
  summary: string | null;
  why_it_matters: string | null;
  what_changed: string | null;
  evidence: string | null;
  confidence_bucket: string;
  review_status: string;
  review_notes: string | null;
  reviewed_at: string | null;
  created_at: string;
  portfolio_priority_score: number;
  thesis_relevance_score: number;
  ownership_weight_score: number;
  valuation_gap_score: number;
  narrative_velocity_score: number;
  score_explanation_json: ScoreExplanation | null;
  portfolio_impacts: AlertPortfolioImpact[];
};

export type Alert = AlertRecord;

export type EvidenceClaimType =
  | "Fact"
  | "Source Summary"
  | "Calculation"
  | "User Assumption"
  | "AI Interpretation"
  | "Estimate"
  | "Mock Data";

export type EvidenceAlertSummary = {
  id: number;
  event_id: number | null;
  company_id: number | null;
  alert_type: string;
  severity: string;
  title: string;
  summary: string | null;
  why_it_matters: string | null;
  confidence_bucket: string;
  created_at: string;
};

export type EvidenceEventSummary = {
  id: number;
  company_id: number | null;
  raw_document_id: number | null;
  event_type: string;
  information_speed: string;
  title: string;
  description: string | null;
  event_time: string | null;
  credibility_score: number | null;
  priority_score: number | null;
  created_at: string;
};

export type EvidenceTrail = {
  entry_point: "alert" | "event";
  claim_type: EvidenceClaimType;
  evidence_status: "complete" | "partial" | "missing";
  confidence: "high" | "medium" | "low" | "unknown";
  source_timestamp: string | null;
  claim_excerpt: string | null;
  excerpt_origin: "alert.evidence" | "event.description" | "event.evidence_reference" | "alert.summary" | "none";
  alert: EvidenceAlertSummary | null;
  event: EvidenceEventSummary | null;
  company: {
    id: number;
    ticker: string;
    name: string;
    market: string;
    primary_exchange: string | null;
  } | null;
  source: {
    id: number;
    name: string;
    source_type: string;
    reliability_score: number | null;
    active: boolean;
  } | null;
  document: {
    id: number;
    company_id: number | null;
    source_id: number;
    document_type: string;
    title: string;
    url: string | null;
    published_at: string | null;
    ingested_at: string;
    content_hash: string;
    has_raw_text: boolean;
    has_asset: boolean;
    asset_page_count: number | null;
  } | null;
  locator: {
    precision: "document" | "page" | "region" | "section" | "span" | "none";
    label: string;
    reference_id: number | null;
    locator_type: string | null;
    source_page: number | null;
    source_section: string | null;
    start_char: number | null;
    end_char: number | null;
    quote: string | null;
    confidence_label: string | null;
    internal_href: string | null;
    source_href: string | null;
    asset_href: string | null;
  };
  thesis_impacts: Array<{
    id: number;
    thesis_assumption_id: number;
    assumption_description: string;
    assumption_status: string;
    impact_classification: string;
    rationale: string;
    created_at: string;
  }>;
  valuation_impacts: Array<{
    id: number;
    valuation_model_id: number;
    assumption_set_id: number;
    parameter_name: string;
    old_value: string | null;
    new_value: string | null;
    rationale: string | null;
    is_applied: boolean;
    created_at: string;
  }>;
  warnings: string[];
};

export type EventEvidenceReference = {
  id: number;
  event_id: number;
  raw_document_id: number;
  created_by_user_id: string | null;
  locator_type: "text_span" | "pdf_region" | "section" | "xbrl_fact";
  source_page: number | null;
  source_section: string | null;
  start_char: number | null;
  end_char: number | null;
  quote: string | null;
  bounding_box_json: Record<string, unknown> | null;
  source_metadata_json: Record<string, unknown> | null;
  confidence_label: "high" | "medium" | "low";
  origin: string;
  pdf_region_status: "valid" | "invalid" | "not_applicable";
  created_at: string;
};

export type EventEvidenceSearchMatch = {
  occurrence_index: number;
  start_char: number;
  end_char: number;
  context_before: string;
  quote: string;
  context_after: string;
};

export type EventEvidenceResolutionSearch = {
  event_id: number;
  company_id: number | null;
  raw_document_id: number;
  event_title: string;
  document_title: string;
  document_content_hash: string;
  query: string;
  exact_match_count: number;
  returned_match_count: number;
  is_truncated: boolean;
  existing_reference_count: number;
  matches: EventEvidenceSearchMatch[];
  limitations: string[];
};

export type ThesisAssumption = {
  id: number;
  thesis_note_id: number;
  description: string;
  category: string | null;
  importance: string;
  original_confidence: string;
  current_confidence: string;
  status: string;
  last_reviewed: string | null;
  falsification_trigger: string | null;
  source_links: string[] | null;
  created_at: string;
  updated_at: string;
  impacts?: EventThesisImpact[];
};

export type ThesisChange = {
  id: number;
  thesis_note_id: number;
  change_summary: string;
  drift_score: number;
  created_at: string;
};

export type ThesisNote = {
  id: number;
  company_id: number;
  title: string;
  thesis_text: string;
  status: string;
  thesis_drift_score: number;
  assumptions: ThesisAssumption[];
  changes: ThesisChange[];
};

export interface SocialPost {
  id: number;
  platform: string;
  source_url: string;
  author: string | null;
  raw_text: string;
  content_hash: string;
  published_at: string | null;
  payload_json: Record<string, unknown> | unknown[] | null;
  created_at: string;
  updated_at: string;
}

export interface SentimentScore {
  id: number;
  post_id: number | null;
  company_id: number | null;
  score: string;
  rationale: string | null;
  created_at: string;
}

export interface NarrativeCluster {
  id: number;
  name: string;
  description: string | null;
  created_at: string;
  updated_at: string;
}

export interface NarrativeClaim {
  id: number;
  cluster_id: number;
  claim_text: string;
  created_at: string;
}

export interface NarrativeMention {
  id: number;
  cluster_id: number;
  event_id: number;
  context_text: string | null;
  created_at: string;
}

export type EventThesisImpact = {
  id: number;
  event_id: number;
  thesis_assumption_id: number;
  impact_classification: string;
  rationale: string;
  created_at: string;
};

export async function classifyEventImpact(eventId: number): Promise<{ message: string }> {
  return api.post<{ message: string }>(`/events/${eventId}/classify-impact`, {
    privacy_disclosure_version: AI_PRIVACY_DISCLOSURE_VERSION,
  }).then(res => res.data as { message: string });
}
