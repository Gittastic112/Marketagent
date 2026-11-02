/** Contracts and endpoint helpers for valuation-drafts. Import transport directly, never the compatibility facade. */
import api from "./transport.ts";
import type { DcfAssumptionSet } from "./valuation.ts";
import type { IndustryAllocation } from "./companies.ts";
import { patchApi, postApi } from "./transport.ts";

export type AssumptionProvenance = {
  source_type?: string;
  label?: string;
  confidence?: string;
  claim_type?: string;
  is_placeholder?: boolean;
  requires_review?: boolean;
  [key: string]: unknown;
};

export type AutofillSourceMetadata = {
  promotion_ready: boolean;
  requires_review: boolean;
  placeholder_fields: string[];
  review_fields: string[];
  review_fields_by_model?: Record<string, string[]>;
  required_fields_by_model?: Record<string, string[]>;
  source_counts_by_type: Record<string, number>;
  legacy_fallback_fields?: string[];
  stale_source_fields?: string[];
  freshness_unknown_fields?: string[];
  oldest_source_as_of?: string | null;
  latest_source_as_of?: string | null;
  unresolved_fields?: string[];
  reporting_currency?: string | null;
  reporting_currency_source?: string | null;
  reporting_currency_confidence?: string | null;
  input_unit_policy?: "full_currency_and_shares_v1";
  industry_mix_id?: number;
  industry_mix_signature?: string;
  industry_mix_basis?: "revenue";
  industry_mix_as_of_date?: string | null;
  industry_mix_allocations?: Array<Pick<IndustryAllocation, "segment_name" | "industry_name" | "weight_percent">>;
  input_readiness?: Array<{
    field: string;
    category: string;
    required: boolean;
    model_scope: string;
    status: "missing" | "optional_unavailable" | "user_input" | "review_required" | "calculated" | "source_backed";
    source_type?: string | null;
    source_file?: string | null;
    source_as_of?: string | null;
    claim_type?: string | null;
  }>;
  input_readiness_summary?: {
    field_count: number;
    counts_by_status: Record<string, number>;
    required_missing_fields: string[];
    required_review_fields: string[];
    ready_for_review: boolean;
    ready_for_promotion: boolean;
  };
};

export type AutofillAssumptionDraft = {
  assumptions: Partial<DcfAssumptionSet>;
  provenance: Record<string, AssumptionProvenance | string>;
  source_metadata: AutofillSourceMetadata;
  warnings: string[];
};

export type ValuationSetupDraft = {
  id: number;
  user_id: string;
  company_id: number;
  promoted_model_id: number | null;
  status: "draft" | "ready_to_value" | "promoted" | "archived";
  industry_name: string | null;
  assumptions_json: Record<string, unknown>;
  provenance_json: Record<string, AssumptionProvenance | string>;
  source_metadata_json: AutofillSourceMetadata;
  warnings_json: string[];
  reviewed_fields_json: string[];
  edited_fields_json: string[];
  created_at: string;
  updated_at: string;
};

export async function createOrReopenValuationDraft(companyId: number): Promise<ValuationSetupDraft> {
  return postApi<ValuationSetupDraft>(`/companies/${companyId}/valuation-drafts`, {});
}

export async function updateValuationDraft(
  draftId: number,
  assumptionsPatch: Record<string, unknown>,
  reviewedFields: string[],
  expectedUpdatedAt?: string,
): Promise<ValuationSetupDraft> {
  return patchApi<ValuationSetupDraft>(`/valuation-drafts/${draftId}`, {
    assumptions_patch: assumptionsPatch,
    reviewed_fields: reviewedFields,
    expected_updated_at: expectedUpdatedAt,
  });
}

export async function refreshValuationDraft(
  draftId: number,
  expectedUpdatedAt?: string,
): Promise<ValuationSetupDraft> {
  return postApi<ValuationSetupDraft>(`/valuation-drafts/${draftId}/refresh`, {
    expected_updated_at: expectedUpdatedAt,
  });
}

export async function resetValuationDraftFields(
  draftId: number,
  fields: string[],
  expectedUpdatedAt?: string,
): Promise<ValuationSetupDraft> {
  return postApi<ValuationSetupDraft>(`/valuation-drafts/${draftId}/reset`, {
    fields,
    expected_updated_at: expectedUpdatedAt,
  });
}

export async function archiveValuationDraft(
  draftId: number,
  expectedUpdatedAt?: string,
): Promise<ValuationSetupDraft> {
  return postApi<ValuationSetupDraft>(`/valuation-drafts/${draftId}/archive`, {
    expected_updated_at: expectedUpdatedAt,
  });
}

export async function draftAutofillAssumptions(companyId: number, base_assumptions: Record<string, any> = {}): Promise<AutofillAssumptionDraft> {
  return api.post<AutofillAssumptionDraft>(`/companies/${companyId}/valuation-models/autofill`, { base_assumptions }).then(res => res.data as AutofillAssumptionDraft);
}
