/** Contracts and endpoint helpers for market. Import transport directly, never the compatibility facade. */
import { fetchApi, fetchApiOrNotFound, postApi } from "./transport.ts";

export interface MarketPrice {
  id: number;
  company_id: number | null;
  ticker: string;
  price: number;
  currency: string;
  as_of_date: string;
  provider_name?: string;
  provider_symbol?: string | null;
  source_url?: string | null;
  market?: string | null;
  exchange?: string | null;
  source_timestamp?: string | null;
  observed_at?: string | null;
  price_type?: string;
  claim_type?: string;
  import_run_id?: number | null;
  delay_minutes?: number | null;
  adjustment_state?: string;
  warnings?: string[];
  created_at: string;
  updated_at: string;
}

export type CompanyMarketData = {
  current_price: number | null;
  change_percent: number | null;
  volume: number | null;
  market_cap: number | null;
  pe_ratio: number | null;
  fifty_two_week_high: number | null;
  fifty_two_week_low: number | null;
  last_updated: string;
};

export async function fetchMarketQuote(
  ticker: string,
  context: { market?: string | null; exchange?: string | null; currency?: string | null } = {}
): Promise<CompanyMarketData | null> {
  const params = new URLSearchParams();
  if (context.market) {
    params.set("market", context.market);
  }
  if (context.exchange) {
    params.set("exchange", context.exchange);
  }
  params.set("ticker", ticker);
  if (context.currency) {
    params.set("currency", context.currency);
  }
  const path = context.market || context.exchange || context.currency
    ? `/api/market/quote?${params.toString()}`
    : `/market/quote/${ticker}`;
  return fetchApiOrNotFound<CompanyMarketData | null>(path, null);
}

export async function fetchLatestMarketPrice(companyId: number) {
  return postApi(`/market-prices/fetch-latest?company_id=${companyId}`, {});
}

export type MarketRegimeScoreRead = {
  id: number;
  score_date: string;
  overall_score: number;
  options_score: number | null;
  liquidity_score: number | null;
  volume_score: number | null;
  breadth_score: number | null;
  macro_score: number | null;
  confidence: string;
  calculation_status: "complete" | "stale" | "blocked";
  formula: string;
  blockers: string[];
  input_sources: Array<{
    input_id: number;
    metric_name: string;
    value: number;
    as_of_date: string;
    age_days: number;
    freshness_threshold_days: number;
    input_type: "manual" | "provider";
    source_name: string;
    source_url: string | null;
    methodology: string;
    claim_type: "Calculation" | "Source Summary" | "User Assumption";
    evidence_state: "linked_record" | "declared_source" | "manual_assumption";
    source_record_type: string | null;
    source_record_id: number | null;
  }>;
  warnings: string[];
  mode: string;
  live_modules: string[];
  manual_modules: string[];
  simulated_modules: string[];
  created_at: string;
};

export type MarketRegimeInputCreate = {
  metric_name: "options" | "liquidity" | "volume" | "breadth" | "macro";
  value: number;
  as_of_date: string;
  source_url: string | null;
  source_name: string;
  input_type: "manual" | "provider";
  methodology: string;
};

export type MarketRegimeInputRead = MarketRegimeInputCreate & {
  id: number;
  source_record_type: string | null;
  source_record_id: number | null;
  created_at: string;
};

export type MarketRegimeMacroProviderRead = {
  metric_name: "macro";
  series_id: "NFCI";
  macro_series_id: number | null;
  observation_id: number | null;
  observed_value: number | null;
  normalized_value: number | null;
  as_of_date: string | null;
  source_name: string;
  source_url: string;
  methodology: string;
  claim_type: "Calculation";
  freshness_threshold_days: number;
  age_days: number | null;
  is_stale: boolean;
  can_apply: boolean;
  blockers: string[];
  warnings: string[];
  applied_input_id: number | null;
  created: boolean;
};

export async function submitMarketRegimeInput(data: MarketRegimeInputCreate): Promise<MarketRegimeInputRead> {
  return postApi<MarketRegimeInputRead>("/market-regime/inputs", data);
}

export async function fetchCurrentMarketRegime(): Promise<MarketRegimeScoreRead> {
  return fetchApi<MarketRegimeScoreRead>("/market-regime/current");
}
