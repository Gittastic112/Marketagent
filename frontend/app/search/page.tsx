import Link from "next/link";

import { EmptyState, ErrorState, PageHeader, Panel } from "@/components/page";
import { DataStateNotices } from "@/components/ui/data-states";
import type { EvidenceSearchResult } from "@/lib/api";
import { serverFetchApiResponse } from "@/lib/server-api";


export const dynamic = "force-dynamic";

const SEARCH_TYPES = {
  document: "Documents",
  event: "Events",
  alert: "Alerts",
  thesis: "Thesis notes",
  decision: "Decision journal",
  valuation: "Valuation models",
  narrative: "Narratives",
  research_session: "Research sessions",
  research_message: "Research messages",
  ai_output: "Reviewed AI outputs",
} as const;

type SearchType = keyof typeof SEARCH_TYPES;

export default async function EvidenceSearchPage({
  searchParams,
}: {
  searchParams: Promise<{ q?: string; type?: string }>;
}) {
  const params = await searchParams;
  const query = params.q?.trim() || "";
  const selectedType = params.type && params.type in SEARCH_TYPES
    ? params.type as SearchType
    : "";
  let searchResponse = null;
  let searchFailed = false;
  if (query.length >= 2) {
    try {
      searchResponse = await serverFetchApiResponse<EvidenceSearchResult[]>(
        `/search/evidence?q=${encodeURIComponent(query)}${selectedType ? `&type=${selectedType}` : ""}`,
      );
    } catch {
      searchFailed = true;
    }
  }
  const results = searchResponse?.data || [];
  const status = query
    ? `${results.length} results${searchResponse?.meta.processing_time_ms !== null && searchResponse?.meta.processing_time_ms !== undefined
      ? ` in ${searchResponse.meta.processing_time_ms} ms`
      : ""}`
    : undefined;

  return (
    <>
      <PageHeader eyebrow="Evidence" title="Search Stored Corpus" status={status} />
      {searchResponse ? (
        <DataStateNotices
          metas={[searchResponse.meta]}
          staleMessage="Search results include stale records. Check each result timestamp before relying on it."
          mockMessage="Search results include mock records. Treat them as test or demonstration data."
        />
      ) : null}
      <Panel title="Search">
        <form action="/search" className="search-form" method="get">
          <div className="field" style={{ flex: "1 1 320px" }}>
            <label htmlFor="evidence-query">Search terms</label>
            <input id="evidence-query" name="q" defaultValue={query} minLength={2} maxLength={200} required placeholder="Search sources, narratives, private research, and reviewed AI" />
          </div>
          <div className="field" style={{ flex: "0 1 220px" }}>
            <label htmlFor="corpus-type">Record type</label>
            <select id="corpus-type" name="type" defaultValue={selectedType}>
              <option value="">All stored records</option>
              {Object.entries(SEARCH_TYPES).map(([value, label]) => (
                <option value={value} key={value}>{label}</option>
              ))}
            </select>
          </div>
          <button type="submit">Search</button>
        </form>
      </Panel>
      {searchFailed ? (
        <ErrorState message="Stored research search is unavailable. Check backend readiness and try again." />
      ) : !query ? (
        <EmptyState label="Enter a term to search stored evidence." />
      ) : query.length < 2 ? (
        <EmptyState label="Enter at least two characters to search stored evidence." />
      ) : results.length === 0 ? (
        <EmptyState label={`No ${selectedType ? SEARCH_TYPES[selectedType].toLowerCase() : "stored research"} matched this search.`} />
      ) : (
        <section className="search-results" aria-label="Search results">
          {results.map((result) => (
            <article key={`${result.result_type}-${result.record_id}`} className="panel search-result">
              <div className="search-result-header">
                <Link href={result.href} className="search-result-title">{result.title}</Link>
                <div className="search-result-badges" aria-label="Result classifications">
                  <span className="badge">{SEARCH_TYPES[result.result_type]}</span>
                  <span className="badge">{result.claim_type}</span>
                  <span className="badge">{result.scope === "private" ? "Private" : "Shared"}</span>
                  {result.review_status === "approved" ? <span className="badge badge-success">Human reviewed</span> : null}
                  {result.is_mock ? <span className="badge badge-warn">Mock Data</span> : null}
                </div>
              </div>
              {result.excerpt ? <p className="search-result-excerpt">{result.excerpt}</p> : null}
              <footer className="search-result-source">
                <span>{result.source_name || "Stored source"}</span>
                {result.source_timestamp ? (
                  <time dateTime={result.source_timestamp}>{new Date(result.source_timestamp).toLocaleString()}</time>
                ) : null}
              </footer>
            </article>
          ))}
        </section>
      )}
    </>
  );
}
