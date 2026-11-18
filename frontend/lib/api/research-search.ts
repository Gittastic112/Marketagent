import type { Company } from "./companies.ts";
import type { EvidenceSearchResult } from "./evidence.ts";
import { fetchApiResponse } from "./transport.ts";

export function fetchResearchCompanies() {
  return fetchApiResponse<Company[]>("/companies");
}

export function searchStoredEvidence(query: string) {
  return fetchApiResponse<EvidenceSearchResult[]>(`/search/evidence?${new URLSearchParams({ q: query.trim() })}`);
}
