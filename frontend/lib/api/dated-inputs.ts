import { fetchApi } from "./transport.ts";

export type DatedInputSource = {
  revision_id: number; revision_number: number; candidate_id: number; document_id: number;
  href: string; value: number; unit: string | null; claim_type: string;
  published_at: string | null; recorded_at: string; retrieved_at: string;
  publication_date: string | null; publication_precision: "date" | "timestamp" | "unknown";
  availability: "available_by_date" | "published_later" | "publication_unknown";
  period: Record<string, unknown>; locator: Record<string, unknown>; passage: string;
};
export type DatedInputRow = {
  metric: string; label: string;
  status: "available" | "missing" | "conflict" | "unavailable_by_date" | "unit_review";
  selected_revision_id: number | null; original_value: number | null; original_unit: string | null;
  normalized_value: number | null; normalized_unit: string | null; conversion: string | null;
  claim_type: string | null; effective_at: string | null; sources: DatedInputSource[]; limitations: string[];
};
export type DatedInputs = {
  company_id: number; valuation_date: string; knowledge: "available_by_date" | "latest_recorded";
  track: "operating" | "bank_equity" | "equity_cash_flow"; rows: DatedInputRow[];
  truncated: boolean; limitations: string[];
};
export function getDatedInputs(companyId: number, valuationDate: string) {
  return fetchApi<DatedInputs>(`/companies/${companyId}/dated-inputs?valuation_date=${encodeURIComponent(valuationDate)}`);
}
