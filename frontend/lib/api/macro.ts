/** Contracts and endpoint helpers for macro. Import transport directly, never the compatibility facade. */
import { fetchApi, postApi } from "./transport.ts";

export type MacroObservation = {
  id: number;
  series_id: number;
  date_recorded: string;
  value: number;
};

export type MacroSeries = {
  id: number;
  name: string;
  description: string | null;
  units: string | null;
  frequency: string | null;
  provider_name: string | null;
  source_url: string | null;
  observations: MacroObservation[];
};

export type MacroSectorSensitivity = {
  market: string;
  country: string;
  classification_system: string;
  currency_context: string | null;
  currency_variable_description: string | null;
  raw_duration: number | null;
  duration_magnitude: number | null;
  duration_interpretation: string;
  sic_code: string;
  industry_name: string;
  source_file: string;
  firm_value_duration: number | null;
  firm_value_cyclicality: number | null;
  firm_value_inflation: number | null;
  firm_value_currency: number | null;
  operating_income_duration: number | null;
  operating_income_cyclicality: number | null;
  operating_income_inflation: number | null;
  operating_income_currency: number | null;
};

export type MacroScenarioRequest = {
  market: string;
  country: string;
  sic_code: string;
  rate_shock: number;
  gdp_shock: number;
  inflation_shock: number;
  currency_shock: number;
  currencyVariableDirection?: string | null;
};

export type MacroScenarioResult = {
  method: string;
  market: string;
  country: string;
  classification_system: string;
  currency_context: string | null;
  currency_variable_description: string | null;
  raw_duration: number | null;
  duration_magnitude: number | null;
  duration_interpretation: string;
  sic_code: string;
  industry_name: string;
  source_file: string;
  estimated_value_impact_pct: number | null;
  estimated_operating_income_impact_pct: number | null;
  covered_value_impact_pct: number;
  covered_operating_income_impact_pct: number;
  missing_value_factors: string[];
  missing_operating_income_factors: string[];
  claim_type: "Calculation";
  affected_assumptions: string[];
  warnings: string[];
  formula: string;
  confidence: string;
};

export type BottomUpMacroSegment = {
  segment_name: string;
  sic_code?: string | null;
  benchmark_industry_name?: string | null;
  segment_value?: number | null;
  segment_revenue?: number | null;
  segment_weight?: number | null;
};

export type MacroSensitivityMetrics = {
  duration: number | null;
  cyclicality: number | null;
  inflation_sensitivity: number | null;
  currency_sensitivity: number | null;
};

export type MacroSensitivityResult = {
  method: string;
  observation_count: number | null;
  firm_value: MacroSensitivityMetrics;
  operating_income: MacroSensitivityMetrics;
  confidence_label: string | null;
  warnings: string[] | null;
  claim_type: "Calculation";
  basis?: string;
  formula?: string;
  covered_weight?: number;
  metric_coverage?: Record<string, number>;
  covered_contributions?: Record<string, number>;
  factor_diagnostics?: Record<string, { status: string; observation_count: number }>;
  segment_exposures?: Array<{ name: string; sic_code: string; weight: number; source_file: string; source_record_id: number }>;
};

export type TopDownMacroPeriod = {
  period_label: string;
  period_end_date?: string | null;
  operating_income?: number | null;
  market_cap?: number | null;
  total_debt?: number | null;
  cash?: number | null;
  enterprise_value?: number | null;
  change_in_long_term_bond_rate?: number | null;
  gdp_growth?: number | null;
  inflation_change?: number | null;
  currency_change?: number | null;
};

export async function fetchMacroSectorSensitivity(
  params: { market: string; country: string; sic: string }
): Promise<MacroSectorSensitivity> {
  const query = new URLSearchParams({
    market: params.market,
    country: params.country,
    sic: params.sic
  });
  return fetchApi<MacroSectorSensitivity>(`/api/valuation/macro/sector?${query.toString()}`);
}

export async function runMacroScenario(payload: MacroScenarioRequest): Promise<MacroScenarioResult> {
  return postApi<MacroScenarioResult>("/api/valuation/macro/scenario", payload);
}

export async function runBottomUpMacroSensitivity(
  payload: { market: string; country: string; segments: BottomUpMacroSegment[] }
): Promise<MacroSensitivityResult> {
  return postApi<MacroSensitivityResult>("/api/valuation/macro/bottom-up", {
    market: payload.market,
    country: payload.country,
    segments: payload.segments.map((segment) => ({
      name: segment.segment_name,
      sicCode: segment.sic_code,
      value: segment.segment_value ?? segment.segment_revenue ?? segment.segment_weight,
    })),
  });
}

export async function runTopDownMacroSensitivity(
  payload: { frequency?: string; periods: TopDownMacroPeriod[] }
): Promise<MacroSensitivityResult> {
  return postApi<MacroSensitivityResult>("/api/valuation/macro/top-down", {
    frequency: payload.frequency ?? "annual",
    periods: payload.periods.map((period) => ({
      period: period.period_label,
      operating_income: period.operating_income,
      market_cap: period.market_cap,
      total_debt: period.total_debt,
      enterprise_value: period.enterprise_value,
      change_in_long_term_bond_rate: period.change_in_long_term_bond_rate,
      gdp_growth: period.gdp_growth,
      inflation_change: period.inflation_change,
      currency_change: period.currency_change,
    })),
  });
}
