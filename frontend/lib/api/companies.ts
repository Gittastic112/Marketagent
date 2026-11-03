/** Contracts and endpoint helpers for companies. Import transport directly, never the compatibility facade. */
import api from "./transport.ts";
import { fetchApi, putApi } from "./transport.ts";

export type SourceCapabilityStatus = "available" | "manual_only" | "not_configured" | "not_supported";

export type SourceCapability = {
  id: number;
  market: "US" | "IN" | string;
  source_type: string;
  provider_name: string;
  capability: string;
  status: SourceCapabilityStatus;
  requires_api_key: boolean;
  freshness_expected_seconds: number | null;
  notes: string | null;
  updated_at: string;
};

export type ExposureTag = {
  id: number;
  name: string;
  description: string | null;
};

export type Company = {
  id: number;
  market: string | null;
  primary_exchange: string | null;
  local_symbol: string | null;
  isin: string | null;
  figi: string | null;
  regulatory_id: string | null;
  regulatory_id_type: string | null;
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
  damodaran_industry?: string | null;
  asset_type: string | null;
  security_type: string | null;
  market_cap_category: string | null;
  is_etf: boolean;
  etf_provider: string | null;
  active: boolean;
  exposure_tags: ExposureTag[];
};

export type CompanyLookup = {
  market?: string;
  exchange?: string | null;
  primary_exchange?: string | null;
  ticker: string;
  local_symbol?: string;
  name: string;
  sector?: string | null;
  industry?: string | null;
  currency?: string;
  country?: string;
  regulatory_id?: string | null;
  regulatory_id_type?: string | null;
  isin?: string | null;
  source?: string;
  warnings?: string[];
  cik?: string;
};

export type Source = {
  id: number;
  name: string;
  source_type: string;
  base_url: string | null;
  reliability_score: number | null;
  active: boolean;
};

export async function lookupCompanyByTicker(
  ticker: string,
  options: { market?: string; exchange?: string | null } = {}
): Promise<CompanyLookup> {
  const params = new URLSearchParams();
  if (options.market) {
    params.set("market", options.market);
  }
  if (options.exchange) {
    params.set("exchange", options.exchange);
  }
  params.set("ticker", ticker);
  return fetchApi<CompanyLookup>(`/companies/lookup?${params.toString()}`);
}

export type CompanySetupSourceReadiness = {
  provider_name: string;
  capability: string;
  market: string;
  status: string;
  notes: string;
  action_required: string | null;
};

export type CompanySetupWorkflow = {
  id: number;
  company_id: number;
  current_step: string;
  identity_status: string;
  source_status: string;
  filing_status: string;
  financial_extraction_status: string;
  industry_mapping_status: string;
  valuation_readiness_status: string;
  security_review_status: string;
  source_readiness: CompanySetupSourceReadiness[];
  next_recommended_step: string;
  created_at: string;
  updated_at: string;
};

export type IndustryMappingCandidate = {
  industryName: string;
  confidence: string;
  reason: string;
  benchmarkAvailability?: Record<string, boolean>;
};

export type IndustryAllocation = {
  id?: number;
  segment_name: string;
  industry_name: string;
  weight_percent: number;
  benchmark_availability?: Record<string, boolean>;
  created_at?: string;
  updated_at?: string;
};

export type CompanyIndustryMix = {
  id: number;
  company_id: number;
  basis: "revenue";
  as_of_date: string | null;
  source_document_id: number | null;
  notes: string | null;
  primary_industry: string;
  total_weight_percent: number;
  claim_type: "User Assumption";
  coverage_status: "complete" | "partial" | "unavailable";
  benchmark_field_coverage: Record<string, Record<string, boolean>>;
  warnings: string[];
  allocations: IndustryAllocation[];
  created_at: string;
  updated_at: string;
};

export type CompanyIndustryMixInput = {
  basis: "revenue";
  as_of_date?: string | null;
  source_document_id?: number | null;
  notes?: string | null;
  allocations: Array<Pick<IndustryAllocation, "segment_name" | "industry_name" | "weight_percent">>;
};

export async function fetchIndustryMappingCandidates(companyId: number, country: string = "India"): Promise<IndustryMappingCandidate[]> {
  const query = new URLSearchParams({ country });
  return api.get<IndustryMappingCandidate[]>(`/companies/${companyId}/industry-mapping-candidates?${query.toString()}`).then(res => res.data as unknown as IndustryMappingCandidate[]);
}

export async function fetchAllIndustryCandidates(country: string = "India"): Promise<string[]> {
  const query = new URLSearchParams({ country });
  return api.get<string[]>(`/industries/candidates?${query.toString()}`).then(res => res.data as unknown as string[]);
}

export async function fetchIndustryMix(companyId: number): Promise<CompanyIndustryMix | null> {
  return fetchApi<CompanyIndustryMix | null>(`/companies/${companyId}/industry-allocations`);
}

export async function saveIndustryMix(
  companyId: number,
  payload: CompanyIndustryMixInput,
): Promise<CompanyIndustryMix> {
  return putApi<CompanyIndustryMix>(`/companies/${companyId}/industry-allocations`, payload);
}

export async function confirmIndustryMapping(companyId: number, industry_name: string): Promise<Company> {
  return api.post<Company>(`/companies/${companyId}/industry-mapping`, { industry_name }).then(res => res.data as Company);
}
