import { fetchApi, postApi, postFormApi } from "./transport.ts";

export type BriefFinding = {
  title: string; importance: "high" | "medium" | "low"; importance_reason: string;
  quote: string; confidence: string; page: number | null; start_char: number; end_char: number;
  valuation_inputs: Array<{ field: string; label: string; direction: string; reason: string; review_href: string }>;
};
export type BriefSource = {
  id: number; company_id: number; company_name: string; ticker: string; title: string;
  source_kind: "pdf" | "text"; source_url: string | null; as_of_date: string | null;
  source_sha256: string; created_at: string; analysis_status: string; ai_output_id: number | null;
  archived_at: string | null; lifecycle_version: number;
  provider: string | null; model: string | null; generated_at: string | null; is_mock: boolean;
  review_status: string; warnings: string[];
  extraction: { character_count: number; selected_pages?: number[]; page_count?: number; warnings: string[] };
  analysis: { summary: string; findings: BriefFinding[] } | null;
};
export const listBriefSources = () => fetchApi<BriefSource[]>("/brief-sources");
export type BriefSourceQuery = {
  q?: string; company_id?: number; source_kind?: "text" | "pdf";
  analysis_status?: "not_scanned" | "scanning" | "failed" | "complete";
  lifecycle?: "active" | "archived" | "all";
  before_id?: number; limit?: number;
};
export type BriefSourcePage = { items: BriefSource[]; next_before_id: number | null };
export function searchBriefSources(query: BriefSourceQuery = {}) {
  const params = new URLSearchParams();
  for (const [key, value] of Object.entries(query)) {
    if (value !== undefined && value !== "") params.set(key, String(value));
  }
  const suffix = params.size ? `?${params}` : "";
  return fetchApi<BriefSourcePage>(`/brief-sources/search${suffix}`);
}
export const pasteBriefSource = (payload: {company_id: number; title: string; text: string; source_url: string | null; as_of_date: string | null}) =>
  postApi<BriefSource>("/brief-sources", payload);
export const uploadBriefSource = (payload: FormData) => postFormApi<BriefSource>("/brief-sources/pdf", payload);
export const analyzeBriefSource = (id: number, version: string) =>
  postApi<BriefSource>(`/brief-sources/${id}/analyze`, { privacy_disclosure_version: version });
export const setBriefSourceArchived = (id: number, archived: boolean, expectedVersion: number) =>
  postApi<BriefSource>(`/brief-sources/${id}/lifecycle`, { archived, expected_version: expectedVersion });
