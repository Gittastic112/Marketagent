/** Contracts and endpoint helpers for portfolio. Import transport directly, never the compatibility facade. */
import { fetchApi } from "./transport.ts";

export type Portfolio = {
  id: number;
  name: string;
  base_currency: string;
  description: string | null;
};

export type PortfolioBenchmarkConfig = {
  id: number;
  portfolio_id: number;
  benchmark_company_id: number | null;
  ticker: string;
  currency: string;
  provider_name: string;
  provider_symbol: string | null;
  effective_from: string;
  active: boolean;
  notes: string | null;
  created_at: string;
  updated_at: string;
};

export type FxRateObservation = {
  id: number;
  base_currency: string;
  quote_currency: string;
  rate: number;
  as_of_date: string;
  provider_name: string;
  provider_symbol: string | null;
  source_url: string | null;
  source_timestamp: string | null;
  claim_type: string;
  import_run_id: number | null;
  observed_at: string;
  created_at: string;
};

export interface PortfolioAttributionComponent {
  price_movement: number | null;
  fx_impact: number | null;
}

export interface PortfolioTransactionActivity {
  purchases: number;
  sales: number;
  dividends: number;
  deposits: number;
  withdrawals: number;
  fees: number;
  taxes: number;
  net_position_cash_flow: number;
  net_external_cash_flow: number;
}

export interface PortfolioAttributionRead {
  as_of_date: string;
  base_currency: string;
  calculation_status: "partial" | "not_available";
  total_unrealized_pnl: number | null;
  components: PortfolioAttributionComponent;
  opportunity_cost: number | null;
  activity_by_currency: Record<string, PortfolioTransactionActivity>;
  attribution_by_sector: Record<string, number>;
  attribution_by_geography: Record<string, number>;
  attribution_by_asset_type: Record<string, number>;
  warnings: string[];
}

export interface PortfolioSnapshot {
  id: number;
  portfolio_id: number;
  snapshot_date: string;
  total_market_value: number | null;
  total_cost_basis: number | null;
  total_cash: number | null;
  total_portfolio_value: number | null;
  base_currency: string | null;
  calculation_status: "complete" | "partial" | "not_available";
  holdings_count: number;
  priced_holdings_count: number;
  missing_price_tickers_json: string[];
  missing_fx_pairs_json: string[];
  payload_json: Record<string, unknown> | null;
  created_at: string;
}

export interface PortfolioCashBalance {
  id: number;
  portfolio_id: number;
  currency: string;
  amount: number;
  as_of_date: string;
  created_at: string;
  updated_at: string;
}

export interface PortfolioValuationHolding {
  holding_id: number;
  ticker: string;
  company_id: number | null;
  quantity: number;
  average_cost: number;
  currency: string;
  market_price: number | null;
  market_price_id?: number | null;
  market_price_provider?: string | null;
  market_price_as_of: string | null;
  market_value: number | null;
  total_cost: number;
  unrealized_pnl: number | null;
  unrealized_pnl_percent: number | null;
  market_value_base?: number | null;
  total_cost_base?: number | null;
  unrealized_pnl_base?: number | null;
  market_fx_rate_to_base?: number | null;
  market_fx_rate_as_of?: string | null;
  market_fx_observation_id?: number | null;
  market_fx_is_stale?: boolean;
  cost_fx_rate_to_base?: number | null;
  cost_fx_rate_as_of?: string | null;
  cost_fx_observation_id?: number | null;
  cost_fx_is_stale?: boolean;
  weight_percent: number | null;
  is_stale_price: boolean;
  is_valuation_stale?: boolean;
  stale_valuation_reason?: string | null;
  valuation_status?: "trusted" | "stale" | "untrusted" | "unavailable";
  valuation_status_reason?: string | null;
  intrinsic_value?: number | null;
  dcf_output_id?: number | null;
  thesis_status?: string | null;
  active_alerts_count?: number;
}

export interface PortfolioValuation {
  portfolio_id: number;
  as_of_date: string;
  base_currency: string;
  total_market_value: number | null;
  total_portfolio_value: number | null;
  total_cash_value: number | null;
  total_cost_basis: number | null;
  total_unrealized_pnl: number | null;
  total_unrealized_pnl_percent: number | null;
  missing_fx_pairs: string[];
  holdings: PortfolioValuationHolding[];
}

export interface PortfolioAnalytics {
  portfolio_id: number;
  as_of_date: string;
  base_currency: string;
  total_portfolio_value: number | null;
  total_cash_value: number | null;
  total_invested_value: number | null;
  total_unrealized_pnl: number | null;
  total_unrealized_pnl_percent: number | null;
  top_positions: PortfolioValuationHolding[];
  top_gainers: PortfolioValuationHolding[];
  top_losers: PortfolioValuationHolding[];
  sector_exposure: Record<string, number>;
  industry_exposure: Record<string, number>;
  country_exposure: Record<string, number>;
  currency_exposure: Record<string, number>;
  asset_type_exposure: Record<string, number>;
  concentration_score: number | null;
  diversification_warnings: string[];
  fx_impact: number | null;
  opportunity_cost: number | null;
  opportunity_cost_percent: number | null;
  missing_fx_pairs: string[];
}

export type PortfolioReturnMetric = {
  calculation_status: "complete" | "partial" | "not_available";
  return_decimal: number | null;
  start_date: string | null;
  end_date: string;
  warnings: string[];
  source_snapshot_ids: number[];
  source_transaction_ids: number[];
};

export type PortfolioPerformance = {
  portfolio_id: number;
  requested_start_date: string;
  requested_end_date: string;
  time_weighted_return: PortfolioReturnMetric;
  money_weighted_return: PortfolioReturnMetric;
};

export type PortfolioPeriodHoldingAttribution = {
  key: string;
  company_id: number | null;
  ticker: string | null;
  price_movement: number | null;
  fx_impact: number | null;
  position_change: number | null;
  total_contribution: number | null;
  calculation_status: "complete" | "partial" | "not_available";
};

export type PortfolioPeriodAttribution = {
  portfolio_id: number;
  start_date: string;
  end_date: string;
  base_currency: string | null;
  calculation_status: "complete" | "partial" | "not_available";
  confidence: "high" | "medium" | "low" | "invalid";
  formula: string;
  total_change: number | null;
  price_movement: number | null;
  fx_impact: number | null;
  position_change: number | null;
  cash_change: number | null;
  external_cash_flow: number | null;
  internal_cash_change: number | null;
  unexplained_change: number | null;
  holdings: PortfolioPeriodHoldingAttribution[];
  attribution_by_sector: Record<string, number>;
  attribution_by_geography: Record<string, number>;
  attribution_by_asset_type: Record<string, number>;
  attribution_by_tag: Record<string, number>;
  warnings: string[];
  blockers: string[];
  source_snapshot_ids: number[];
  source_transaction_ids: number[];
};

export type PortfolioOpportunityCost = {
  calculation_status: "complete" | "not_available" | "not_configured";
  portfolio_id: number;
  start_date: string;
  end_date: string;
  benchmark_ticker: string | null;
  benchmark_return: number | null;
  portfolio_return: number | null;
  return_spread: number | null;
  benchmark_ending_value: number | null;
  actual_ending_value: number | null;
  opportunity_cost: number | null;
  opportunity_cost_percent: number | null;
  warnings: string[];
  source_snapshot_ids: number[];
  source_market_price_ids: number[];
  source_transaction_ids: number[];
};

export type PortfolioRiskReturnHolding = {
  holding_id: number;
  company_id: number | null;
  ticker: string;
  portfolio_weight_decimal: number | null;
  risk_model_weight_decimal: number | null;
  current_market_value_base: number | null;
  latest_market_price_as_of?: string | null;
  price_age_days?: number | null;
  is_stale_price?: boolean;
  observation_count: number;
  aligned_observation_count: number;
  return_start_date: string | null;
  return_end_date: string | null;
  historical_return_decimal: number | null;
  annualized_volatility: number | null;
  marginal_volatility: number | null;
  marginal_volatility_for_one_percent: number | null;
  component_risk: number | null;
  component_risk_percent: number | null;
  expected_return_decimal: number | null;
  expected_return_kind: "dcf_valuation_gap_not_annualized" | "unavailable";
  expected_return_claim_type: "Estimate" | "Unavailable";
  expected_return_contribution: number | null;
  source_dcf_output_id: number | null;
  source_market_price_ids: number[];
  source_fx_observation_ids: number[];
  warnings: string[];
};

export type PortfolioRiskReturn = {
  portfolio_id: number;
  as_of_date: string;
  lookback_start_date: string;
  lookback_days: number;
  min_observations: number;
  base_currency: string;
  calculation_status: "complete" | "partial" | "not_available";
  risk_calculation_status: "complete" | "partial" | "not_available";
  expected_return_calculation_status: "complete" | "partial" | "not_available";
  portfolio_volatility_annualized: number | null;
  risk_covered_weight_percent: number;
  risk_reconciliation_error: number | null;
  portfolio_expected_return_decimal: number | null;
  expected_return_coverage_percent: number;
  risk_claim_type: "Calculation" | "Unavailable";
  expected_return_claim_type: "Estimate" | "Unavailable";
  contains_mock_data: boolean;
  risk_formula: string;
  expected_return_formula: string;
  holdings: PortfolioRiskReturnHolding[];
  warnings: string[];
  blockers: string[];
  source_market_price_ids: number[];
  source_fx_observation_ids: number[];
  source_dcf_output_ids: number[];
};

export type PortfolioRealInputReadinessCheck = {
  code: string;
  label: string;
  status: "passed" | "blocked";
  required: string;
  observed: string;
  message: string;
  source_record_ids: number[];
};

export type PortfolioRealInputReadiness = {
  portfolio_id: number;
  user_id: string;
  certification_status: "ready" | "blocked";
  claim_type: "Calculation";
  as_of_date: string;
  start_date: string | null;
  end_date: string | null;
  lookback_days: number;
  min_observations: number;
  contains_mock_data: boolean;
  checks: PortfolioRealInputReadinessCheck[];
  blockers: string[];
  warnings: string[];
  source_snapshot_ids: number[];
  source_market_price_ids: number[];
  source_fx_observation_ids: number[];
  source_dcf_output_ids: number[];
};

export type PortfolioHolding = {
  id: number;
  portfolio_id: number;
  company_id: number | null;
  ticker: string;
  quantity: number;
  average_cost: number;
  currency: string;
  as_of_date: string;
};

export type PortfolioTransaction = {
  id: number;
  portfolio_id: number;
  company_id: number | null;
  ticker: string;
  transaction_type: string;
  quantity: number;
  price: number;
  fees: number;
  currency: string;
  transaction_date: string;
  notes: string | null;
};

export async function listPortfolioCashBalances(portfolioId: number): Promise<PortfolioCashBalance[]> {
  return fetchApi<PortfolioCashBalance[]>(`/portfolio-cash-balances?portfolio_id=${portfolioId}`);
}

export async function listPortfolioSnapshots(portfolioId: number): Promise<PortfolioSnapshot[]> {
  return fetchApi<PortfolioSnapshot[]>(`/portfolio-snapshots?portfolio_id=${portfolioId}`);
}
