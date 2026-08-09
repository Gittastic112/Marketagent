import Link from "next/link";

import { EmptyState, PageHeader, Panel } from "@/components/page";
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
  const searchResponse = query.length >= 2
    ? await serverFetchApiResponse<EvidenceSearchResult[]>(
        `/search/evidence?q=${encodeURIComponent(query)}${selectedType ? `&type=${selectedType}` : ""}`,
      )
    : null;
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
        <form action="/search" method="get" style={{ display: "flex", gap: "0.5rem", flexWrap: "wrap" }}>
          <div className="field" style={{ flex: "1 1 320px" }}>
            <label htmlFor="evidence-query">Search terms</label>
            <input id="evidence-query" name="q" defaultValue={query} minLength={2} required placeholder="Search filings, alerts, theses, decisions, and valuations" />
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
      {!query ? (
        <EmptyState label="Enter a term to search stored evidence." />
      ) : results.length === 0 ? (
        <EmptyState label="No stored evidence matched this search." />
      ) : (
        <section style={{ display: "grid", gap: "0.75rem" }} aria-label="Search results">
          {results.map((result) => (
            <article key={`${result.result_type}-${result.record_id}`} className="panel" style={{ padding: "1rem" }}>
              <div style={{ display: "flex", justifyContent: "space-between", gap: "1rem", flexWrap: "wrap" }}>
                <Link href={result.href} style={{ fontWeight: 700 }}>{result.title}</Link>
                <div style={{ display: "flex", gap: "0.4rem", flexWrap: "wrap" }}>
                  <span className="badge">{SEARCH_TYPES[result.result_type]}</span>
                  <span className="badge">{result.claim_type}</span>
                </div>
              </div>
              {result.excerpt ? <p style={{ margin: "0.5rem 0" }}>{result.excerpt}</p> : null}
              <small>{result.source_name || "Stored source"}{result.source_timestamp ? ` · ${new Date(result.source_timestamp).toLocaleString()}` : ""}</small>
            </article>
          ))}
        </section>
      )}
    </>
  );
}
