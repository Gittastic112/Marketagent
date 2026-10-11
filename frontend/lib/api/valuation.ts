/** Contracts and endpoint helpers for valuation. Import transport directly, never the compatibility facade. */
import { fetchApi, postApi } from "./transport.ts";

export type ValuationCompanyContext = {
  company_id: number;
  market: string;
  country: string;
  default_currency: string;
  cash_flow_currency: string;
  discount_rate_currency: string;
  available_benchmark_countries: string[];
  recommended_benchmark_country: string;
  benchmark_source: string;
  warnings: string[];
};

export type RiskFreeRate = {
  market: string;
  country: string;
  currency: string;
  risk_free_rate: number;
  risk_free_rate_source: string;
  as_of_date: string | null;
  is_manual: boolean;
  warnings: string[];
};

export type DcfProjectionYear = {
  id: number;
  assumption_set_id: number;
  year_index: number;
  calendar_year: number;
  revenue: number | null;
  revenue_growth: number | null;
  ebit_margin: number | null;
  ebit: number | null;
  tax_rate: number | null;
  nopat: number | null;
  reinvestment: number | null;
  fcff: number | null;
  invested_capital: number | null;
  roic: number | null;
  wacc: number | null;
  discount_factor: number | null;
  pv_fcff: number | null;
  created_at: string;
};

export type DiagnosticWarning = {
  severity: "info" | "watch" | "warning" | "critical" | "blocking";
  module: string;
  message: string;
  affectedAssumptions: string[];
  suggestedFix: string | null;
  formula: string | null;
};

export type DcfScenarioOutput = {
  scenario_name: string;
  description: string;
  output: DcfOutput;
};

export type ImpliedPricingBasis = {
  version: number;
  claimType: "Calculation";
  assumptionSetId: number | null;
  outputCreatedAt: string | null;
  assumptionsUpdatedAt: string | null;
  isStale: boolean;
  methods: Array<{
    field: string;
    label: string;
    value: number | null;
    numerator: number | null;
    denominator: number | null;
    sourceFields: string[];
    formula: string;
    reason: string | null;
  }>;
  note: string;
};

export type DcfOutput = {
  id: number;
  assumption_set_id: number;
  sum_pv_fcff: number | null;
  terminal_value: number | null;
  pv_terminal_value: number | null;
  enterprise_value: number | null;
  cash: number | null;
  non_operating_assets: number | null;
  debt: number | null;
  minority_interests: number | null;
  preferred_stock: number | null;
  employee_options_value: number | null;
  equity_value: number | null;
  diluted_shares: number | null;
  intrinsic_value_per_share: number | null;
  current_market_price: number | null;
  upside_downside_pct: number | null;
  terminal_value_pct_of_ev: number | null;
  implied_exit_multiple: number | null;
  implied_terminal_roic: number | null;
  implied_pe: number | null;
  implied_ev_ebitda: number | null;
  implied_ev_sales: number | null;
  implied_ev_ebit: number | null;
  implied_pbv: number | null;
  implied_pricing_basis?: ImpliedPricingBasis | null;

  fcfe_intrinsic_value_per_share?: number | null;
  ddm_intrinsic_value_per_share?: number | null;

  base_dcf_value?: number | null;
  pv_of_excess_returns?: number | null;

  model_quality_score: number | null;
  warnings_json: DiagnosticWarning[] | null;
  created_at: string;
};

export type QuickValuationAssumptions = {
  company_id: number;
  assumptions: DcfAssumptionSetCreate;
  provenance: Record<string, unknown>;
  source_metadata: Record<string, unknown>;
  warnings: string[];
};

export type QuickValuationProjection = {
  year_index: number;
  revenue: number;
  revenue_growth: number;
  ebit_margin: number;
  nopat: number;
  reinvestment: number;
  fcff: number;
  roic: number;
  wacc: number;
  pv_fcff: number;
};

export type QuickValuationOutput = {
  company_id: number;
  currency: string | null;
  claim_type: "Calculation";
  is_persisted: false;
  sum_pv_fcff: number;
  terminal_value: number;
  pv_terminal_value: number;
  enterprise_value: number;
  cash: number;
  debt: number;
  minority_interests: number;
  preferred_stock: number;
  employee_options_value: number;
  equity_value: number;
  diluted_shares: number;
  intrinsic_value_per_share: number;
  current_market_price: number;
  upside_downside_pct: number;
  terminal_value_pct_of_ev: number;
  model_quality_score: number | null;
  warnings_json: DiagnosticWarning[];
  projection_years: QuickValuationProjection[];
  limitations: string[];
};

export interface DcfSensitivityTable {
  id: number;
  assumption_set_id: number;
  table_type: string;
  x_axis_json: any;
  y_axis_json: any;
  values_json: any;
  created_at: string;
}

export interface ReverseDcfRequest {
  assumption_set_id: number;
  target_parameter: "target_operating_margin" | "revenue_growth" | "wacc_start" | "terminal_growth_rate";
  current_market_price: number;
  diluted_shares?: number;
}

export interface ReverseDcfResponse {
  target_parameter: string;
  implied_value: number | null;
  original_value: number | null;
  intrinsic_value_at_implied: number | null;
  diagnostics: DiagnosticWarning[];
  error?: string;
  assumption_set_id?: number | null;
  assumptions_updated_at?: string | null;
  calculated_at?: string | null;
  currency?: string | null;
  model_type?: string | null;
  comparison_price?: number | null;
  diluted_shares?: number | null;
  price_residual?: number | null;
  converged?: boolean;
}

export type DcfDecisionLog = {
  id: number;
  valuation_model_id: number;
  assumption_set_id: number;
  decision_type: string;
  user_note: string | null;
  price_at_decision: number | null;
  intrinsic_value_at_decision: number | null;
  upside_downside_at_decision: number | null;
  confidence_label: string | null;
  created_at: string;
};

export type ValuationAssumptionChangeLog = {
  id: number;
  valuation_model_id: number;
  assumption_set_id: number;
  event_id: number | null;
  parameter_name: string;
  old_value: string | null;
  new_value: string | null;
  rationale: string | null;
  is_applied: boolean;
  created_at: string;
};

export type DcfAssumptionSet = {
  id: number;
  valuation_model_id: number;
  scenario: string;
  projection_years_count?: number;

  story_text: string | null;
  growth_story: string | null;
  margin_story: string | null;
  reinvestment_story: string | null;
  risk_story: string | null;

  starting_revenue: number | null;
  revenue_growth_years_json: Record<string, unknown> | number[] | null;
  target_operating_margin: number | null;
  current_operating_margin: number | null;
  tax_rate: number | null;
  sales_to_capital_ratio: number | null;
  reinvestment_method: string;
  starting_invested_capital: number | null;

  risk_free_rate: number | null;
  equity_risk_premium: number | null;
  beta: number | null;
  cost_of_equity: number | null;
  pre_tax_cost_of_debt: number | null;
  debt_to_capital: number | null;
  equity_to_capital: number | null;
  wacc_start: number | null;
  wacc_terminal: number | null;

  terminal_growth_rate: number | null;
  terminal_roic: number | null;

  cash: number | null;
  cross_holdings: number | null;
  minority_interests: number | null;
  preferred_stock: number | null;
  debt: number | null;
  operating_leases: number | null;
  employee_options_value: number | null;
  diluted_shares: number | null;
  basic_shares: number | null;
  current_market_price: number | null;
  cash_flow_currency?: string | null;
  discount_rate_currency?: string | null;
  currency_override_note?: string | null;
  net_income?: number | null;
  capex?: number | null;
  depreciation?: number | null;
  change_in_nwc?: number | null;
  dividends?: number | null;
  buybacks?: number | null;
  stock_issuances?: number | null;
  new_debt_issued?: number | null;
  debt_repaid?: number | null;
  company_age?: number | null;

  is_stale?: boolean;
  stale_reason?: string | null;
  stale_event_id?: number | null;

  probability_of_failure?: number | null;
  distress_sale_proceeds?: number | null;
  book_value_of_equity?: number | null;
  target_roe?: number | null;

  created_at: string;
  updated_at: string;
  outputs: DcfOutput | null;
  projection_years: DcfProjectionYear[];
  sensitivity_tables: DcfSensitivityTable[];
  decision_logs: DcfDecisionLog[];
  change_logs: ValuationAssumptionChangeLog[];
};

export type ValuationModel = {
  id: number;
  company_id: number;
  name: string;
  description: string | null;
  model_type: string;
  created_at: string;
  updated_at: string;
  assumption_sets: DcfAssumptionSet[];
  decision_logs: DcfDecisionLog[];
};

export type ValuationModelSummary = {
  id: number;
  company_id: number;
  name: string;
  description: string | null;
  model_type: string;
  created_at: string;
  updated_at: string;
  assumption_set_count: number;
  latest_assumption_set_id: number | null;
  latest_scenario: string | null;
  latest_run_at: string | null;
  readiness: "setup_incomplete" | "review_required" | "calculation_unavailable" | "blocked" | "calculated";
  readiness_detail: string;
  intrinsic_value_per_share: number | null;
  model_quality_score: number | null;
  cash_flow_currency: string | null;
};

export type ValuationModelCreate = {
  company_id: number;
  name: string;
  description?: string;
  model_type?: string;
};

export type DcfAssumptionSetCreate = {
  scenario: string;

  story_text?: string | null;
  growth_story?: string | null;
  margin_story?: string | null;
  reinvestment_story?: string | null;
  risk_story?: string | null;

  starting_revenue?: number | null;
  revenue_growth_years_json?: Record<string, unknown> | null;
  target_operating_margin?: number | null;
  current_operating_margin?: number | null;
  tax_rate?: number | null;
  sales_to_capital_ratio?: number | null;
  reinvestment_method?: string;
  starting_invested_capital?: number | null;

  risk_free_rate?: number | null;
  equity_risk_premium?: number | null;
  beta?: number | null;
  cost_of_equity?: number | null;
  pre_tax_cost_of_debt?: number | null;
  debt_to_capital?: number | null;
  equity_to_capital?: number | null;
  wacc_start?: number | null;
  wacc_terminal?: number | null;

  terminal_growth_rate?: number | null;
  terminal_roic?: number | null;

  cash?: number | null;
  cross_holdings?: number | null;
  minority_interests?: number | null;
  preferred_stock?: number | null;
  debt?: number | null;
  operating_leases?: number | null;
  employee_options_value?: number | null;
  diluted_shares?: number | null;
  basic_shares?: number | null;
  current_market_price?: number | null;
  cash_flow_currency?: string | null;
  discount_rate_currency?: string | null;
  currency_override_note?: string | null;

  net_income?: number;
  capex?: number;
  depreciation?: number;
  change_in_nwc?: number;
  new_debt_issued?: number;
  debt_repaid?: number;
  dividends?: number;
  buybacks?: number;
  stock_issuances?: number;
  company_age?: number;
};

export async function createValuationModel(companyId: number, data: ValuationModelCreate): Promise<ValuationModel> {
  return postApi<ValuationModel>(`/companies/${companyId}/valuation-models`, data);
}

export async function getValuationModel(id: number): Promise<ValuationModel> {
  return fetchApi<ValuationModel>(`/valuation-models/${id}`);
}

export async function solveReverseDcf(request: ReverseDcfRequest): Promise<ReverseDcfResponse> {
  return postApi<ReverseDcfResponse>(`/dcf/reverse`, request);
}

export async function resolveStaleValuation(modelId: number, assumptionId: number): Promise<DcfAssumptionSet> {
  return postApi<DcfAssumptionSet>(`/valuation-models/${modelId}/assumptions/${assumptionId}/resolve-stale`, {});
}

export async function getValuationChangeLogs(modelId: number, assumptionId: number): Promise<ValuationAssumptionChangeLog[]> {
  return fetchApi<ValuationAssumptionChangeLog[]>(`/valuation-models/${modelId}/assumptions/${assumptionId}/change-logs`);
}

export async function createDcfAssumptionSet(modelId: number, data: DcfAssumptionSetCreate): Promise<DcfAssumptionSet> {
  return postApi<DcfAssumptionSet>(`/valuation-models/${modelId}/assumptions`, data);
}

export async function listValuationModels(companyId: number): Promise<ValuationModel[]> {
  return fetchApi<ValuationModel[]>(`/companies/${companyId}/valuation-models`);
}

export async function getValuationModelAssumptions(modelId: number): Promise<DcfAssumptionSet[]> {
  return fetchApi<DcfAssumptionSet[]>(`/valuation-models/${modelId}/assumptions`);
}

export async function getDcfScenarios(modelId: number, assumptionId: number): Promise<DcfScenarioOutput[]> {
  return fetchApi<DcfScenarioOutput[]>(`/valuation-models/${modelId}/assumptions/${assumptionId}/scenarios`);
}

export async function fetchValuationContext(companyId: number): Promise<ValuationCompanyContext> {
  return fetchApi<ValuationCompanyContext>(`/api/valuation/context/company/${companyId}`);
}
