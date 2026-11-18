import api, { fetchApi, postApi } from "./transport.ts";
import { ApiError } from "./contract.ts";
import type { ApiMeta } from "./contract.ts";
import type { RawDocument } from "./documents.ts";
import type { components } from "./generated/adapters.ts";

type Schemas = components["schemas"];
export type SourceRequestByAction = {
  "sec-facts": Schemas["SecFactsAdapterRequest"];
  "india-filings": Schemas["IndiaFilingsRequest"];
  transcript: Schemas["TranscriptRequest"];
  extract: Schemas["DocumentExtractionRequest"];
  "fred-vintage": Schemas["FredVintageRequest"];
};
export type SourceAction = keyof SourceRequestByAction;
export type SourceAdapterCapability = Schemas["SourceAdapterCapability"];
export type SourceAdapterResult = Schemas["SourceAdapterResult"];
export type DataRequestByAction = {
  quote: Schemas["MarketDataRequest"];
  history: Schemas["AdapterHistoryRequest"];
  "dated-quote": Schemas["AdapterDatedQuoteRequest"];
  "corporate-actions": Schemas["AdapterActionRequest"];
  reference: Schemas["MarketDataRequest"];
  identity: Schemas["IdentityMappingRequest"];
  calendar: Schemas["CalendarScheduleRequest"];
};
export type DataAdapterReceipt = Schemas["DataAdapterReceipt_MarketQuoteResult_"]
  | Schemas["DataAdapterReceipt_AdapterHistoryResult_"]
  | Schemas["DataAdapterReceipt_AdapterDatedQuoteResult_"]
  | Schemas["DataAdapterReceipt_AdapterActionsResult_"]
  | Schemas["DataAdapterReceipt_SecurityReferenceResult_"]
  | Schemas["DataAdapterReceipt_IdentityMappingResult_"]
  | Schemas["DataAdapterReceipt_CalendarScheduleResult_"];
export type MarketAdapterProvider = "fmp" | "massive" | "nse_mcp";
export type MarketAdapterAction = keyof DataRequestByAction;
export type DataAdapterExecution = { receipt: DataAdapterReceipt; meta: ApiMeta };

export function providersForMarketAction(action: MarketAdapterAction): MarketAdapterProvider[] {
  if (action === "identity" || action === "calendar") return [];
  if (action === "dated-quote") return ["nse_mcp"];
  if (action === "reference") return ["massive"];
  if (action === "corporate-actions") return ["massive", "nse_mcp"];
  return ["fmp", "massive", "nse_mcp"];
}

export const getSourceAdapterCapabilities = () => fetchApi<SourceAdapterCapability[]>("/api/source-adapters");
export const getExtractionDocuments = (companyId: number) => fetchApi<{ items: RawDocument[]; total: number }>(`/raw-documents/library?company_id=${companyId}&limit=100`);

export function runSourceAdapter<K extends SourceAction>(action: K, payload: SourceRequestByAction[K], companyId?: number, documentId?: number) {
  if (action !== "fred-vintage" && (!companyId || !Number.isSafeInteger(companyId))) throw new Error("Select a company first.");
  if (action === "extract" && (!documentId || !Number.isSafeInteger(documentId))) throw new Error("Select a stored document first.");
  const path = action === "fred-vintage" ? "/api/source-adapters/fred-vintage"
    : action === "extract" ? `/api/companies/${companyId}/source-adapters/documents/${documentId}/extract`
      : `/api/companies/${companyId}/source-adapters/${action}`;
  return postApi<SourceAdapterResult>(path, payload);
}

export async function runDataAdapter<K extends MarketAdapterAction>(provider: MarketAdapterProvider, action: K, payload: DataRequestByAction[K]): Promise<DataAdapterExecution> {
  const supported = providersForMarketAction(action);
  if (supported.length && !supported.includes(provider)) throw new Error("The selected provider does not support this data action.");
  const path = action === "identity" ? "/api/data-adapters/identity/openfigi"
    : action === "calendar" ? "/api/data-adapters/calendars/schedule"
      : `/api/data-adapters/${provider}/${action}`;
  // Freshness is computed in the response envelope, not only in the stored receipt.
  const response = await api.post<DataAdapterReceipt>(path, payload);
  if (response.errors.length) throw new ApiError(response.errors[0].message, 200, response.errors[0]);
  if (!response.data) throw new ApiError("The adapter returned no source receipt.", 200);
  return { receipt: response.data, meta: response.meta };
}
