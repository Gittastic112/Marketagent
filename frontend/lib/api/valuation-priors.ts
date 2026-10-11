/** Contracts and endpoint helpers for valuation-priors. Import transport directly, never the compatibility facade. */
import { postApi } from "./transport.ts";

export type DebtRatioPriorRequest = {
  effective_tax_rate: number;
  expected_eps_growth: number;
  institutional_holdings: number;
  company_age_years: number;
  region?: "Global" | "US";
};

export type DividendYieldPriorRequest = {
  effective_tax_rate: number;
  expected_eps_growth: number;
  company_age_years: number;
  beta: number;
  region?: "Global" | "US";
};

export type DividendPayoutPriorRequest = {
  beta: number;
  return_on_equity: number;
  region?: "Global" | "US";
};

export type RegressionPriorResponse = {
  prior_value: number | null;
  formula: string;
  model: string;
  claim_type: "Estimate";
  confidence: "low" | "not_usable";
  source: string;
  source_path: string;
  source_as_of: string;
  adjusted_r_squared: number;
  input_units: Record<string, string>;
  output_unit: string;
  usable: boolean;
  warnings: string[];
};

export async function fetchDebtRatioPrior(payload: DebtRatioPriorRequest): Promise<RegressionPriorResponse> {
  return postApi<RegressionPriorResponse>(`/priors/debt-ratio`, payload);
}

export async function fetchDividendYieldPrior(payload: DividendYieldPriorRequest): Promise<RegressionPriorResponse> {
  return postApi<RegressionPriorResponse>(`/priors/dividend-yield`, payload);
}

export async function fetchDividendPayoutPrior(payload: DividendPayoutPriorRequest): Promise<RegressionPriorResponse> {
  return postApi<RegressionPriorResponse>(`/priors/dividend-payout`, payload);
}
