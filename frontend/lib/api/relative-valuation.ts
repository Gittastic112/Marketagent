/** Contracts and endpoint helpers for relative-valuation. Import transport directly, never the compatibility facade. */
import type { ApiResponse } from "./contract.ts";
import { deleteApi, fetchApi, fetchApiResponse, postApi, putApi } from "./transport.ts";

export interface CountryMarketStats {
  country: string;
  firm_count?: number;
  market_cap_usd_millions?: number;
  total_debt_usd_millions?: number;
  firm_value_usd_millions?: number;
  cash_usd_millions?: number;
  enterprise_value_usd_millions?: number;
  median_current_pe?: number;
  median_trailing_pe?: number;
  median_forward_pe?: number;
  median_peg?: number;
  median_pbv?: number;
  median_ps?: number;
  median_ev_ebit?: number;
  median_ev_ebitda?: number;
  median_ev_invested_capital?: number;
  median_ev_sales?: number;
  median_cash_to_firm_value?: number;
  dividend_yield?: number;
  total_dividends_usd_millions?: number;
  date_updated?: string;
  source: PricingSourceProvenance;
}

export interface RelativeValuationResult {
  method: string;
  methodId: string;
  benchmarkMultiple: number;
  enterpriseValue?: number;
  equityValue?: number;
  valuePerShare?: number;
  reliability: string;
  claimType: "Calculation";
  source: PricingSourceProvenance | PeerSetMethodSource;
}

export interface PricingSourceProvenance {
  sourceCode: "pe" | "pbv" | "ps" | "vebitda" | "countrystats";
  sourceFile: string;
  datasetVersionId: number;
  sourceSha256?: string;
  sourceAsOf?: string;
  dateConfidence: string;
  canonicalSourcePath?: string;
  claimType: "Fact";
}

export interface RelativeValuationResponse {
  inputBasis?: SavedRelativeInputBasis;
  benchmarkType: "industry_aggregate" | "reviewed_peer_set";
  industryName?: string | null;
  peerSet?: PeerValuationSet | null;
  relativeValues: RelativeValuationResult[];
  range?: {
    low: number;
    base: number;
    high: number;
  };
  diagnostics: string[];
  unavailableMethods: Array<{ method: string; reason: string }>;
  benchmarkSources: PricingSourceProvenance[];
}

export interface RelativeValuationRequest {
  companyId?: string;
  country?: string;
  industryName?: string;
  peerSetId?: number;
  financials: {
    revenue?: number;
    ebitda?: number;
    ebit?: number;
    netIncome?: number;
    bookEquity?: number;
    investedCapital?: number;
    debt?: number;
    cash?: number;
    dilutedShares?: number;
  };
  methods: string[];
}

export interface SavedRelativeInputBasis {
  assumptionSetId: number;
  modelId: number;
  companyId: number;
  savedAt: string | null;
  updatedAt: string | null;
  currency: string | null;
  isStale: boolean;
  isMock: boolean;
  inputBasisSha256: string;
  financials: Record<keyof RelativeValuationRequest["financials"], number | null>;
  fields: Record<string, { value: number | null; claimType: string; sourceFields: string[]; reason: string }>;
  methodInputs: Array<{ method: string; requiredField: string; hasPositiveBase: boolean; hasPerShareInputs: boolean; reason: string }>;
  canCalculate: boolean;
  blockers: string[];
  warnings: string[];
}

export type SavedRelativeRunRequest = Pick<RelativeValuationRequest, "country" | "industryName" | "peerSetId" | "methods"> & {
  confirmInputBasis: boolean;
  inputBasisSha256: string;
};

export function getSavedRelativeInputs(assumptionId: number): Promise<ApiResponse<SavedRelativeInputBasis>> {
  return fetchApiResponse<SavedRelativeInputBasis>(`/api/valuation/relative/assumptions/${assumptionId}/inputs`);
}

export function runSavedRelativeValuation(assumptionId: number, request: SavedRelativeRunRequest): Promise<RelativeValuationResponse> {
  return postApi<RelativeValuationResponse>(`/api/valuation/relative/assumptions/${assumptionId}/run`, request);
}

export type PeerMultipleMethod = "pe" | "pbv" | "ps" | "ev_sales" | "ev_ebitda" | "ev_ebit";

export type PeerMultiples = Partial<Record<PeerMultipleMethod, number>>;

export interface PeerValuationMember {
  identifier: string;
  companyId?: number | null;
  name?: string | null;
  included: boolean;
  multiples: PeerMultiples;
  sourceName: string;
  sourceUrl: string;
  sourceAsOf: string;
  claimType: "Fact" | "Source Summary";
  notes?: string | null;
  country?: string | null;
  currency?: string | null;
  fiscalPeriodEnd?: string | null;
  accountingStandard?: "IFRS" | "US GAAP" | "IND AS" | "OTHER" | null;
  marketCap?: number | null;
  revenueGrowthPct?: number | null;
  ebitdaMarginPct?: number | null;
}

export interface PeerMethodAggregate {
  multiple: number | null;
  eligibleCount: number;
  requiredCount: number;
  eligibleMemberIdentifiers: string[];
  excludedMembers: Array<{ identifier: string; reason: string }>;
  formula: string;
}

export interface PeerComparabilityWarning {
  code: string;
  severity: "warning";
  method?: PeerMultipleMethod;
  currency?: string;
  message: string;
  memberIdentifiers: string[];
}

export interface PeerMethodDiagnostics {
  eligibleCount: number;
  minimum: number | null;
  maximum: number | null;
  median: number | null;
  medianAbsoluteDeviation: number | null;
  relativeMedianAbsoluteDeviation: number | null;
  maxToMinRatio: number | null;
  warnings: string[];
}

export interface PeerComparabilityDiagnostics {
  status: "bounded" | "review_required";
  asOf: string;
  acknowledgementSha256: string;
  warningCodes: string[];
  thresholds: {
    sourceStaleDays: number;
    sourceDateSpanWarningDays: number;
    multipleRatioWarning: number;
    relativeMedianAbsoluteDeviationWarning: number;
    fiscalPeriodSpanWarningDays: number;
    marketCapRatioWarning: number;
    growthSpanWarningPct: number;
    marginSpanWarningPct: number;
  };
  sourceDates: {
    earliest: string | null;
    latest: string | null;
    spanDays: number | null;
    staleMemberIdentifiers: string[];
  };
  claimTypeCounts: Record<"Fact" | "Source Summary", number>;
  comparabilityContext: {
    countries: string[];
    currencies: string[];
    accountingStandards: string[];
    fiscalPeriodSpanDays: number | null;
    marketCapRatio: number | null;
    marketCapGroups: Record<string, {
      memberCount: number;
      memberIdentifiers: string[];
      minimum: number;
      maximum: number;
      maxToMinRatio: number;
    }>;
    unusableMarketCapMemberIdentifiers: string[];
    invalidMarketCapMemberIdentifiers: string[];
    revenueGrowthSpanPct: number | null;
    ebitdaMarginSpanPct: number | null;
    coverage: Record<string, number>;
    targetProvided: boolean;
    targetComparisons: Record<string, {
      comparedCount: number;
      mismatchCount: number;
      maximumDifference?: number | null;
      currency?: string | null;
      skippedCurrencyMismatchCount?: number;
      skippedMissingCurrencyCount?: number;
      skippedInvalidValueCount?: number;
      skippedMemberIdentifiers?: string[];
    }>;
  };
  methods: Record<PeerMultipleMethod, PeerMethodDiagnostics>;
  warnings: PeerComparabilityWarning[];
}

export interface PeerReviewReceipt {
  diagnosticsSha256: string;
  warningCodes: string[];
  diagnosticsAsOf: string;
  matchesCurrentDiagnostics: boolean;
}

export interface PeerTargetContext {
  sourceName: string;
  sourceUrl: string;
  sourceAsOf: string;
  claimType: "Fact" | "Source Summary";
  notes?: string | null;
  country?: string | null;
  currency?: string | null;
  fiscalPeriodEnd?: string | null;
  accountingStandard?: "IFRS" | "US GAAP" | "IND AS" | "OTHER" | null;
  marketCap?: number | null;
  revenueGrowthPct?: number | null;
  ebitdaMarginPct?: number | null;
}

export interface PeerValuationSet {
  id: number;
  companyId: number;
  name: string;
  notes?: string | null;
  isActive: boolean;
  reviewStatus: "draft" | "reviewed";
  reviewedAt?: string | null;
  aggregationMethod: "median";
  version: number;
  aggregates: {
    aggregationMethod: "median";
    minimumMethodPeers: number;
    methods: Record<PeerMultipleMethod, PeerMethodAggregate>;
  };
  diagnostics: PeerComparabilityDiagnostics;
  calculationEligibility: {
    canCalculate: boolean;
    receiptStatus: "missing" | "stale" | "current";
    usableMethods: PeerMultipleMethod[];
    blockers: string[];
    asOf: string;
  };
  reviewReceipt?: PeerReviewReceipt | null;
  storageConsistency: {
    status: "consistent" | "legacy_json_only" | "mismatch";
    jsonMemberCount: number;
    normalizedMemberCount: number;
  };
  targetStorageConsistency: {
    status: "consistent" | "legacy_json_only" | "mismatch";
    jsonTargetPresent: boolean;
    normalizedTargetPresent: boolean;
  };
  targetContext?: PeerTargetContext | null;
  importSha256?: string | null;
  memberCount: number;
  includedMemberCount: number;
  members?: PeerValuationMember[];
  createdAt: string;
  updatedAt: string;
}

export interface PeerValuationSetRevision {
  id: number;
  peerSetId: number;
  version: number;
  action: "create" | "import" | "update" | "review" | "archive" | "restore" | "migration_snapshot";
  changedFields: string[];
  name: string;
  notes?: string | null;
  isActive: boolean;
  reviewStatus: "draft" | "reviewed";
  reviewedAt?: string | null;
  aggregationMethod: "median";
  memberCount: number;
  includedMemberCount: number;
  members: PeerValuationMember[];
  targetContext?: PeerTargetContext | null;
  aggregates: PeerValuationSet["aggregates"];
  diagnostics: PeerComparabilityDiagnostics;
  reviewReceipt?: PeerReviewReceipt | null;
  storageConsistency: PeerValuationSet["storageConsistency"];
  targetStorageConsistency: PeerValuationSet["targetStorageConsistency"];
  createdAt: string;
}

export interface PeerSetMethodSource {
  peerSetId: number;
  peerSetName: string;
  reviewStatus: "reviewed";
  reviewedAt: string;
  aggregationMethod: "median";
  eligibleCount: number;
  eligibleMemberIdentifiers: string[];
  memberSources: Array<{
    identifier: string;
    companyId?: number | null;
    name?: string | null;
    sourceName: string;
    sourceUrl: string;
    sourceAsOf: string;
    claimType: "Fact" | "Source Summary";
  }>;
  targetContext?: PeerTargetContext | null;
  formula: string;
  diagnostics: PeerMethodDiagnostics;
  warnings: PeerComparabilityWarning[];
  claimType: "Calculation";
}

export interface PeerValuationSetCreate {
  companyId: number;
  name: string;
  notes?: string;
  targetContext?: PeerTargetContext | null;
  members: PeerValuationMember[];
}

export interface PeerCsvTemplate {
  filename: string;
  csvText: string;
  sha256: string;
  columns: string[];
  targetColumns: string[];
  formatVersion: "2";
  acceptsLegacyMemberOnlyFormat: boolean;
  maximumRows: number;
  maximumBytes: number;
  claimType: "User Assumption";
}

export interface PeerCsvPreview {
  isValid: boolean;
  sha256: string;
  setName: string | null;
  setNotes: string | null;
  formatVersion: "1" | "2" | null;
  legacyFormat: boolean;
  targetContext: PeerTargetContext | null;
  memberCount: number;
  members: PeerValuationMember[];
  errors: Array<{ row: number | null; field: string; message: string }>;
  warnings: string[];
}

export interface PeerCsvExport {
  filename: string;
  csvText: string;
  sha256: string;
  rowCount: number;
  formatVersion: "2";
  targetContextIncluded: boolean;
  claimType: "User Assumption";
  warnings: string[];
}

export interface PeerCsvApplyResult extends PeerValuationSet {
  importDisposition: "created" | "reused";
}

export async function getRelativeValuationCountries(): Promise<string[]> {
  return fetchApi<string[]>("/api/valuation/relative/countries");
}

export async function getRelativeValuationIndustries(country: string): Promise<string[]> {
  return fetchApi<string[]>(`/api/valuation/relative/countries/${encodeURIComponent(country)}/industries`);
}

export async function runRelativeValuation(request: RelativeValuationRequest): Promise<RelativeValuationResponse> {
  return postApi<RelativeValuationResponse>("/api/valuation/relative/run", request);
}

export async function listPeerValuationSets(companyId: number, includeArchived = false): Promise<PeerValuationSet[]> {
  return fetchApi<PeerValuationSet[]>(`/api/valuation/relative/peer-sets?company_id=${companyId}&include_archived=${includeArchived}`);
}

export async function createPeerValuationSet(payload: PeerValuationSetCreate): Promise<PeerValuationSet> {
  return postApi<PeerValuationSet>("/api/valuation/relative/peer-sets", payload);
}

export async function getPeerValuationSet(peerSetId: number): Promise<PeerValuationSet> {
  return fetchApi<PeerValuationSet>(`/api/valuation/relative/peer-sets/${peerSetId}`);
}

export async function updatePeerValuationSet(
  peerSetId: number,
  payload: Partial<Pick<PeerValuationSetCreate, "name" | "notes" | "targetContext" | "members">> & { expectedVersion: number },
): Promise<PeerValuationSet> {
  return putApi<PeerValuationSet>(`/api/valuation/relative/peer-sets/${peerSetId}`, payload);
}

export async function reviewPeerValuationSet(
  peerSetId: number,
  expectedVersion: number,
  diagnostics: Pick<PeerComparabilityDiagnostics, "acknowledgementSha256" | "warningCodes">,
): Promise<PeerValuationSet> {
  return postApi<PeerValuationSet>(`/api/valuation/relative/peer-sets/${peerSetId}/review`, {
    acknowledged: true,
    expectedVersion,
    expectedDiagnosticsSha256: diagnostics.acknowledgementSha256,
    acknowledgedWarningCodes: diagnostics.warningCodes,
  });
}

export async function archivePeerValuationSet(peerSetId: number, expectedVersion: number): Promise<void> {
  return deleteApi(`/api/valuation/relative/peer-sets/${peerSetId}?expected_version=${expectedVersion}`);
}

export async function restorePeerValuationSet(peerSetId: number, expectedVersion: number): Promise<PeerValuationSet> {
  return postApi<PeerValuationSet>(`/api/valuation/relative/peer-sets/${peerSetId}/restore`, {
    expectedVersion,
  });
}

export async function listPeerValuationSetRevisions(peerSetId: number): Promise<PeerValuationSetRevision[]> {
  return fetchApi<PeerValuationSetRevision[]>(`/api/valuation/relative/peer-sets/${peerSetId}/revisions`);
}

export async function getPeerCsvTemplate(): Promise<PeerCsvTemplate> {
  return fetchApi<PeerCsvTemplate>("/api/valuation/relative/peer-sets/import/template");
}

export async function previewPeerCsv(companyId: number, csvText: string): Promise<PeerCsvPreview> {
  return postApi<PeerCsvPreview>("/api/valuation/relative/peer-sets/import/preview", {
    companyId,
    csvText,
  });
}

export async function applyPeerCsv(
  companyId: number,
  csvText: string,
  expectedSha256: string,
): Promise<PeerCsvApplyResult> {
  return postApi<PeerCsvApplyResult>("/api/valuation/relative/peer-sets/import/apply", {
    companyId,
    csvText,
    expectedSha256,
  });
}

export async function exportPeerValuationSet(peerSetId: number): Promise<PeerCsvExport> {
  return fetchApi<PeerCsvExport>(`/api/valuation/relative/peer-sets/${peerSetId}/export`);
}
