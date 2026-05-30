const SERVER_API_BASE_URL = process.env.API_BASE_URL ?? process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://127.0.0.1:8000";
const BROWSER_API_BASE_URL = process.env.NEXT_PUBLIC_BROWSER_API_BASE_URL ?? "/api/backend";
const DEBUG_LOGS_ENABLED = process.env.NEXT_PUBLIC_DEBUG_LOGS === "true";

function getApiBaseUrl(): string {
  return typeof window === "undefined" ? SERVER_API_BASE_URL : BROWSER_API_BASE_URL;
}

function logApiStart(method: string, path: string) {
  if (DEBUG_LOGS_ENABLED) {
    console.log(`[api] ${method} ${path} -> ${getApiBaseUrl()}${path}`);
  }
}

function logApiSuccess(method: string, path: string, status: number) {
  if (DEBUG_LOGS_ENABLED) {
    console.log(`[api] ${method} ${path} succeeded with ${status}`);
  }
}

function logApiFailure(method: string, path: string, status: number) {
  if (DEBUG_LOGS_ENABLED) {
    console.log(`[api] ${method} ${path} failed with ${status}`);
  }
}

export class ApiError extends Error {
  readonly status: number;

  constructor(message: string, status: number) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

async function apiError(response: Response): Promise<ApiError> {
  try {
    const body = await response.json();
    if (body && Array.isArray(body.errors) && body.errors.length > 0) {
      return new ApiError(body.errors[0].message, response.status);
    }
    if (body && typeof body.detail === "string") {
      return new ApiError(body.detail, response.status);
    }
  } catch {
    // Fall back to the generic message below when the response body is not JSON.
  }
  return new ApiError(`API request failed: ${response.status}`, response.status);
}

export interface ApiMeta {
  is_stale: boolean;
  processing_time_ms?: number;
}

export interface ApiErrorDetail {
  code: string;
  message: string;
  target?: string;
}

export interface ApiResponse<T> {
  data: T | null;
  meta: ApiMeta;
  errors: ApiErrorDetail[];
}

async function parseApiResponse<T>(response: Response): Promise<T> {
  const payload = await response.json() as ApiResponse<T>;
  if (payload.errors && payload.errors.length > 0) {
    throw new ApiError(payload.errors[0].message, response.status);
  }
  return payload.data as T;
}

export type ExposureTag = {
  id: number;
  name: string;
  description: string | null;
};

export type Company = {
  id: number;
  ticker: string;
  name: string;
  sector: string | null;
  industry: string | null;
  exchange: string | null;
  cik: string | null;
  aliases_json: string[] | null;
  country: string | null;
  region: string | null;
  currency: string | null;
  asset_type: string | null;
  security_type: string | null;
  market_cap_category: string | null;
  is_etf: boolean;
  etf_provider: string | null;
  active: boolean;
  exposure_tags: ExposureTag[];
};

export type CompanyLookup = {
  ticker: string;
  name: string;
  cik: string;
};

export type Source = {
  id: number;
  name: string;
  source_type: string;
  base_url: string | null;
  reliability_score: number | null;
  active: boolean;
};

export type RawDocument = {
  id: number;
  company_id: number | null;
  source_id: number;
  document_type: string;
  title: string;
  url: string | null;
  raw_text: string | null;
  content_hash: string;
};

export type FilingSectionDiff = {
  id: number;
  current_section_id: number;
  prior_section_id: number | null;
  added_words: number;
  removed_words: number;
  diff_html: string | null;
  created_at: string;
};

export type FilingSection = {
  id: number;
  raw_document_id: number;
  item_name: string;
  title: string | null;
  text_content: string;
  word_count: number;
  created_at: string;
  updated_at: string;
  diffs_as_current: FilingSectionDiff[];
};

export type AiOutput = {
  id: number;
  raw_document_id: number;
  model_name: string;
  prompt_version: string;
  input_hash: string;
  output_text: string;
  limitations: string | null;
  confidence_label: string;
  human_review_status: string;
  created_at: string;
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
  score_explanation_json: ScoreExplanation | null;
  corroborates?: EventRecord[];
  contradicts?: EventRecord[];
};

export type ScoreExplanation = {
  information_speed?: {
    value: string;
    factors: string[];
  };
  credibility?: {
    score: number;
    factors: string[];
  };
  novelty?: {
    score: number;
    factors: string[];
  };
  impact?: {
    score: number;
    factors: string[];
  };
  priority?: {
    score: number;
    formula: string;
    weights: Record<string, number>;
    speed_bonus: number;
  };
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
  confidence_bucket: string;
  review_status: string;
  review_notes: string | null;
  reviewed_at: string | null;
  portfolio_priority_score: number;
  portfolio_impacts: AlertPortfolioImpact[];
};

export type ThesisAssumption = {
  id: number;
  thesis_note_id: number;
  description: string;
  original_confidence: string;
  current_confidence: string;
  created_at: string;
  updated_at: string;
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

export type Portfolio = {
  id: number;
  name: string;
  base_currency: string;
  description: string | null;
};

export interface PortfolioSnapshot {
  id: number;
  portfolio_id: number;
  snapshot_date: string;
  total_market_value: number | null;
  total_cost_basis: number | null;
  total_cash: number | null;
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

export interface MarketPrice {
  id: number;
  company_id: number | null;
  ticker: string;
  price: number;
  currency: string;
  as_of_date: string;
  created_at: string;
  updated_at: string;
}

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
  post_id: number;
  context_text: string | null;
  created_at: string;
}

export interface PortfolioValuationHolding {
  holding_id: number;
  ticker: string;
  company_id: number | null;
  quantity: number;
  average_cost: number;
  currency: string;
  market_price: number | null;
  market_price_as_of: string | null;
  market_value: number | null;
  total_cost: number;
  unrealized_pnl: number | null;
  unrealized_pnl_percent: number | null;
  weight_percent: number | null;
  is_stale_price: boolean;
}

export interface PortfolioValuation {
  portfolio_id: number;
  as_of_date: string;
  base_currency: string;
  total_market_value: number | null;
  total_cost_basis: number;
  total_unrealized_pnl: number | null;
  total_unrealized_pnl_percent: number | null;
  holdings: PortfolioValuationHolding[];
}

export interface PortfolioAnalytics {
  portfolio_id: number;
  as_of_date: string;
  base_currency: string;
  total_portfolio_value: number | null;
  total_cash_value: number;
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
}

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

export type DailyBrief = {
  title: string;
  date: string;
  summary: string;
  top_events: Array<{
    id: number;
    company: string | null;
    title: string;
    event_type: string;
    information_speed: string;
    description: string | null;
    credibility_score: number | null;
    novelty_score: number | null;
    impact_score: number | null;
    priority_score: number | null;
    source: string | null;
    source_url: string | null;
  }>;
  alerts: Array<{
    id: number;
    company: string | null;
    title: string;
    severity: string;
    confidence_bucket: string;
    review_status: string;
    summary: string | null;
  }>;
  follow_up_questions: string[];
};

export type SavedDailyBrief = {
  id: number;
  brief_date: string;
  title: string;
  summary: string;
  payload_json: DailyBrief;
  created_at: string;
};

export type RssIngestionResult = {
  fetched_count: number;
  created_count: number;
  skipped_duplicate_count: number;
  error_count: number;
  errors: string[];
  created: number;
  skipped_duplicates: number;
  events_created: number;
  events_skipped_existing: number;
  alerts_created: number;
  alerts_skipped_existing: number;
  alerts_skipped_below_threshold: number;
};

export type SecFilingIngestionResult = {
  fetched_count: number;
  created_count: number;
  skipped_duplicate_count: number;
  error_count: number;
  errors: string[];
  created: number;
  skipped_duplicates: number;
  events_created: number;
  events_skipped_existing: number;
  alerts_created: number;
  alerts_skipped_existing: number;
  alerts_skipped_below_threshold: number;
};

export type SecFilingMetadata = {
  accession_number: string;
  form_type: string;
  filing_date: string;
  report_date: string | null;
  primary_document: string | null;
  filing_url: string | null;
};

export type EventExtractionResult = {
  created: number;
  skipped_existing: number;
};

export type AlertGenerationResult = {
  created: number;
  skipped_existing: number;
  skipped_below_threshold: number;
};

export type FinancialMetric = {
  id: number;
  period_id: number;
  metric_name: string;
  value: number;
  unit: string | null;
  created_at: string;
  updated_at: string;
};

export type FinancialStatementPeriod = {
  id: number;
  company_id: number;
  period_type: string;
  year: number;
  quarter: number | null;
  report_date: string;
  currency: string;
  created_at: string;
  updated_at: string;
  metrics: FinancialMetric[];
};

export type DcfOutput = {
  id: number;
  assumption_set_id: number;
  enterprise_value: number;
  equity_value: number;
  implied_share_price: number;
  output_json: Record<string, unknown> | null;
  created_at: string;
};

export type DcfAssumptionSet = {
  id: number;
  valuation_model_id: number;
  scenario: string;
  discount_rate: number;
  terminal_growth_rate: number;
  projection_years: number;
  assumptions_json: Record<string, unknown>;
  created_at: string;
  updated_at: string;
  outputs: DcfOutput[];
};

export type ValuationModel = {
  id: number;
  company_id: number;
  name: string;
  description: string | null;
  created_at: string;
  updated_at: string;
  assumption_sets: DcfAssumptionSet[];
};

export type ValuationModelCreate = {
  company_id: number;
  name: string;
  description?: string;
};

export type DcfAssumptionSetCreate = {
  scenario: string;
  discount_rate: number;
  terminal_growth_rate: number;
  projection_years: number;
  assumptions_json: {
    current_fcf: number;
    shares_outstanding: number;
    net_debt: number;
    fcf_growth_rate: number;
    [key: string]: unknown;
  };
};

export async function fetchApi<T>(path: string): Promise<T> {
  logApiStart("GET", path);
  const response = await fetch(`${getApiBaseUrl()}${path}`, {
    cache: "no-store"
  });

  if (!response.ok) {
    logApiFailure("GET", path, response.status);
    throw await apiError(response);
  }

  logApiSuccess("GET", path, response.status);
  return parseApiResponse<T>(response);
}

export async function createValuationModel(companyId: number, data: ValuationModelCreate): Promise<ValuationModel> {
  return postApi<ValuationModel>(`/companies/${companyId}/valuation-models`, data);
}

export async function createDcfAssumptionSet(modelId: number, data: DcfAssumptionSetCreate): Promise<DcfAssumptionSet> {
  return postApi<DcfAssumptionSet>(`/valuation-models/${modelId}/assumptions`, data);
}

export async function lookupCompanyByTicker(ticker: string): Promise<CompanyLookup> {
  return fetchApi<CompanyLookup>(`/companies/lookup?ticker=${encodeURIComponent(ticker)}`);
}

export async function listFinancialPeriods(companyId: number): Promise<FinancialStatementPeriod[]> {
  return fetchApi<FinancialStatementPeriod[]>(`/companies/${companyId}/financial-periods`);
}

export async function listValuationModels(companyId: number): Promise<ValuationModel[]> {
  return fetchApi<ValuationModel[]>(`/companies/${companyId}/valuation-models`);
}

export async function getValuationModelAssumptions(modelId: number): Promise<DcfAssumptionSet[]> {
  return fetchApi<DcfAssumptionSet[]>(`/valuation-models/${modelId}/assumptions`);
}

export async function listFilingSections(rawDocumentId: number): Promise<FilingSection[]> {
  return fetchApi<FilingSection[]>(`/raw-documents/${rawDocumentId}/sections`);
}

export async function parseFilingSections(rawDocumentId: number): Promise<{ status: string }> {
  return postApi<{ status: string }>(`/raw-documents/${rawDocumentId}/parse`, {});
}

export async function listAiOutputs(rawDocumentId: number): Promise<AiOutput[]> {
  return fetchApi<AiOutput[]>(`/raw-documents/${rawDocumentId}/ai-outputs`);
}

export async function generateAiSummary(rawDocumentId: number): Promise<AiOutput> {
  return postApi<AiOutput>(`/raw-documents/${rawDocumentId}/ai-summary`, {});
}

export async function listPortfolioCashBalances(portfolioId: number): Promise<PortfolioCashBalance[]> {
  return fetchApi<PortfolioCashBalance[]>(`/portfolio-cash-balances?portfolio_id=${portfolioId}`);
}

export async function listPortfolioSnapshots(portfolioId: number): Promise<PortfolioSnapshot[]> {
  return fetchApi<PortfolioSnapshot[]>(`/portfolio-snapshots?portfolio_id=${portfolioId}`);
}

export async function postApi<T>(path: string, payload: unknown): Promise<T> {
  logApiStart("POST", path);
  const response = await fetch(`${getApiBaseUrl()}${path}`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify(payload)
  });

  if (!response.ok) {
    logApiFailure("POST", path, response.status);
    throw await apiError(response);
  }

  logApiSuccess("POST", path, response.status);
  return parseApiResponse<T>(response);
}

export async function postApiFormData<T>(path: string, formData: FormData): Promise<T> {
  logApiStart("POST", path);
  const response = await fetch(`${getApiBaseUrl()}${path}`, {
    method: "POST",
    body: formData
  });

  if (!response.ok) {
    logApiFailure("POST", path, response.status);
    throw await apiError(response);
  }

  logApiSuccess("POST", path, response.status);
  return parseApiResponse<T>(response);
}

export async function patchApi<T>(path: string, payload: unknown): Promise<T> {
  logApiStart("PATCH", path);
  const response = await fetch(`${getApiBaseUrl()}${path}`, {
    method: "PATCH",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify(payload)
  });

  if (!response.ok) {
    logApiFailure("PATCH", path, response.status);
    throw await apiError(response);
  }

  logApiSuccess("PATCH", path, response.status);
  return parseApiResponse<T>(response);
}

export async function deleteApi(path: string): Promise<void> {
  logApiStart("DELETE", path);
  const response = await fetch(`${getApiBaseUrl()}${path}`, {
    method: "DELETE"
  });

  if (!response.ok) {
    logApiFailure("DELETE", path, response.status);
    throw await apiError(response);
  }

  logApiSuccess("DELETE", path, response.status);
}

export async function deleteScoringConfig(id: number): Promise<void> {
  const method = "DELETE";
  const path = `/scoring-configs/${id}`;
  logApiStart(method, path);

  const response = await fetch(`${getApiBaseUrl()}${path}`, {
    method,
  });

  if (!response.ok) {
    logApiFailure(method, path, response.status);
    throw await apiError(response);
  }

  logApiSuccess(method, path, response.status);
}

// -- Market Data --
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

export async function fetchMarketQuote(ticker: string): Promise<CompanyMarketData | null> {
  const method = "GET";
  const path = `/market/quote/${ticker}`;
  logApiStart(method, path);

  const response = await fetch(`${getApiBaseUrl()}${path}`, {
    method,
    headers: { Accept: "application/json" },
    cache: "no-store",
  });

  if (!response.ok) {
    if (response.status === 404) return null;
    logApiFailure(method, path, response.status);
    throw await apiError(response);
  }

  logApiSuccess(method, path, response.status);
  return parseApiResponse<CompanyMarketData>(response);
}

// -- Financial Trends --
export type FinancialMetric = {
  metric_name: string;
  value: number;
  unit: string | null;
};

export type FinancialPeriod = {
  period_type: string;
  year: number;
  quarter: number | null;
  report_date: string;
  metrics: FinancialMetric[];
};

export async function fetchFinancialTrends(ticker: string): Promise<FinancialPeriod[]> {
  const method = "GET";
  const path = `/fundamentals/${ticker}/trends`;
  logApiStart(method, path);

  const response = await fetch(`${getApiBaseUrl()}${path}`, {
    method,
    headers: { Accept: "application/json" },
    cache: "no-store",
  });

  if (!response.ok) {
    if (response.status === 404) return [];
    logApiFailure(method, path, response.status);
    throw await apiError(response);
  }

  logApiSuccess(method, path, response.status);
  return parseApiResponse<FinancialPeriod[]>(response);
}

export type ScoringConfig = {
  id: number;
  weight_credibility: number;
  weight_novelty: number;
  weight_impact: number;
  weight_speed: number;
};

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
  observations: MacroObservation[];
};

export type TokenStatusResponse = {
  provider_name: string;
  is_connected: boolean;
  expires_at: string | null;
};

export async function fetchOAuthStatus(): Promise<TokenStatusResponse[]> {
  return fetchApi<TokenStatusResponse[]>("/oauth/status");
}

export type ProcessingRun = {
  id: number;
  run_type: string;
  source_type: string | null;
  source_id: number | null;
  company_id: number | null;
  started_at: string;
  finished_at: string | null;
  status: string;
  fetched_count: number;
  created_count: number;
  skipped_duplicate_count: number;
  error_count: number;
  error_details_json: Record<string, unknown> | null;
  metadata_json: Record<string, unknown> | null;
  created_at: string;
};
