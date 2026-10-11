/** Contracts and endpoint helpers for real-options. Import transport directly, never the compatibility facade. */
import { fetchApi, postApi } from "./transport.ts";

export type VolatilityBenchmarkRead = {
  country: string;
  industry: string;
  numberOfFirms: number | null;
  equityStandardDeviation: number | null;
  firmValueStandardDeviation: number | null;
  equityValueWeight: number | null;
  debtValueWeight: number | null;
  assumptions: Record<string, number>;
  claimType: "Source Summary";
  datasetVersionId: number;
  sourceFile: string;
  sourceSha256: string;
  sourceAsOf: string;
  dateConfidence: string;
  canonicalSourcePath: string;
};

export type OptionEligibilityTestRequest = {
  valuation_id?: string | null;
  option_type: string;
  has_underlying_asset: boolean;
  has_finite_life: boolean;
  has_clear_exercise_price: boolean;
  has_asymmetric_payoff: boolean;
  has_exclusivity: boolean;
  can_estimate_volatility: boolean;
  can_estimate_underlying_value: boolean;
};

export type OptionEligibilityTestResponse = {
  eligibilityPassed: boolean;
  eligibilityScore: number;
  recommendation: string;
  warnings: string[];
};

export type RealOptionCalculateRequest = {
  valuation_id?: string | null;
  option_type: string;
  underlying_asset_value: number;
  exercise_price: number;
  option_life_years: number;
  risk_free_rate: number;
  volatility: number;
  dividend_yield_or_cost_of_delay: number;
  exclusivity_score: number;
  is_already_counted: boolean;
  base_dcf_value: number;
};

export type RealOptionCalculateResponse = {
  d1: number;
  d2: number;
  nd1: number;
  nd2: number;
  raw_option_value: number;
  adjusted_option_value: number;
  option_delta: number;
  option_adjusted_intrinsic_value: number | null;
  warnings: string[];
};

export async function fetchVolatilityBenchmark(country: string, industry: string): Promise<VolatilityBenchmarkRead> {
  return fetchApi<VolatilityBenchmarkRead>(`/api/valuation/options/volatility?country=${encodeURIComponent(country)}&industry=${encodeURIComponent(industry)}`);
}

export async function runOptionEligibilityTest(payload: OptionEligibilityTestRequest): Promise<OptionEligibilityTestResponse> {
  return postApi<OptionEligibilityTestResponse>("/api/valuation/options/eligibility", payload);
}

export async function calculateRealOption(payload: RealOptionCalculateRequest): Promise<RealOptionCalculateResponse> {
  return postApi<RealOptionCalculateResponse>("/api/valuation/options/calculate", payload);
}

export type SavedRealOptionRequest = Omit<RealOptionCalculateRequest, "valuation_id" | "base_dcf_value" | "option_type"> & {
  option_type: "call" | "put";
  assumptions_updated_at: string;
  currency: string;
  confirm_incremental_equity_basis: boolean;
  eligibility: Omit<OptionEligibilityTestRequest, "valuation_id" | "option_type">;
};

export type SavedRealOptionResponse = {
  assumption_set_id: number; assumptions_updated_at: string; output_created_at: string;
  calculated_at: string; currency: string; model_type: string; input_sha256: string;
  diluted_shares: number; base_equity_value: number; base_value_per_share: number;
  raw_option_value: number; adjusted_option_value: number; option_value_per_share: number;
  option_adjusted_equity_value: number; option_adjusted_intrinsic_value: number; warnings: string[];
};

export async function calculateSavedRealOption(assumptionId: number, payload: SavedRealOptionRequest): Promise<SavedRealOptionResponse> {
  return postApi<SavedRealOptionResponse>(`/api/valuation/options/assumptions/${assumptionId}/calculate`, payload);
}
