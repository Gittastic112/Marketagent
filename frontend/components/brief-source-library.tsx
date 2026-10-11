"use client";

import Link from "next/link";
import { useCallback, useRef, useState } from "react";
import { BriefSourceFindings } from "@/components/brief-source-findings";
import { BriefSourceLifecycle } from "@/components/brief-source-lifecycle";
import { MockDataBadge } from "@/components/ui/data-states";
import { searchBriefSources, type BriefSourceQuery } from "@/lib/api/brief-sources";
import type { Company } from "@/lib/api/companies";
import { useLatestResource } from "@/lib/use-latest-resource";

type Props = {
  companies: Company[];
  consent: boolean;
  busy: number | "upload" | "organize" | null;
  refreshToken: number;
  onScan: (id: number) => Promise<void>;
  onOrganizeBusy: (busy: boolean) => void;
  onOrganized: (message: string) => void;
};

export function BriefSourceLibrary({ companies, consent, busy, refreshToken, onScan, onOrganizeBusy, onOrganized }: Props) {
  const [filters, setFilters] = useState<BriefSourceQuery>({});
  const [cursors, setCursors] = useState<Array<number | undefined>>([undefined]);
  const form = useRef<HTMLFormElement>(null);
  const beforeId = cursors[cursors.length - 1];
  // A new filter/page or completed mutation gets its own clean request scope.
  const loader = useCallback(() => searchBriefSources({ ...filters, before_id: beforeId }), [filters, beforeId, refreshToken]);
  const result = useLatestResource(loader);
  const sources = result.data?.items ?? [];
  const nextCursor = result.data?.next_before_id;
  const filtered = Object.values(filters).some(value => value !== undefined && value !== "");

  function search(data: FormData) {
    setFilters({
      q: String(data.get("q") || "").trim(),
      company_id: Number(data.get("company_id")) || undefined,
      source_kind: (String(data.get("source_kind") || "") || undefined) as BriefSourceQuery["source_kind"],
      analysis_status: (String(data.get("analysis_status") || "") || undefined) as BriefSourceQuery["analysis_status"],
      lifecycle: (String(data.get("lifecycle") || "active")) as BriefSourceQuery["lifecycle"],
    });
    setCursors([undefined]);
  }

  return <section aria-label="Saved research sources">
    <h3>Saved sources</h3>
    <p className="muted">Search titles and stored source text, including extracted PDF pages. Active sources are shown by default, newest saved first. Archiving and scan status do not indicate human approval.</p>
    <form ref={form} className="brief-intake-form" role="search" aria-label="Search private research" onSubmit={event => {
      event.preventDefault(); search(new FormData(event.currentTarget));
    }}>
      <fieldset disabled={busy !== null}>
        <legend className="sr-only">Find saved sources</legend>
        <div className="brief-intake-grid">
          <label>Search saved sources<input type="search" name="q" maxLength={200} placeholder="A word or phrase from the source" /></label>
          <label>Filter by company<select name="company_id" defaultValue="" disabled={!companies.length}>
            <option value="">All companies</option>{companies.map(company => <option key={company.id} value={company.id}>{company.ticker} · {company.name}</option>)}
          </select></label>
          <label>Source format<select name="source_kind" defaultValue=""><option value="">All formats</option><option value="text">Pasted text</option><option value="pdf">PDF</option></select></label>
          <label>Scan status<select name="analysis_status" defaultValue=""><option value="">All scan states</option><option value="not_scanned">Not scanned</option><option value="scanning">Scanning</option><option value="failed">Failed</option><option value="complete">Complete</option></select></label>
          <label>Inbox status<select name="lifecycle" defaultValue="active"><option value="active">Active</option><option value="archived">Archived</option><option value="all">Active and archived</option></select></label>
        </div>
        <div className="section-intro">
          <button className="btn btn-secondary" type="submit">Search sources</button>
          <button className="btn btn-secondary" type="button" onClick={() => { form.current?.reset(); setFilters({}); setCursors([undefined]); }}>Clear filters</button>
        </div>
      </fieldset>
    </form>
    {filtered && <p className="muted">Applied filters: {[
      filters.q ? `“${filters.q}”` : null,
      filters.company_id ? companies.find(company => company.id === filters.company_id)?.ticker ?? `Company ${filters.company_id}` : null,
      filters.source_kind?.toUpperCase(), filters.analysis_status?.replaceAll("_", " "), filters.lifecycle,
    ].filter(Boolean).join(" · ")}</p>}
    {result.status === "loading" && <p role="status">Searching your sources…</p>}
    {result.status === "error" && <div role="alert" className="basis-note">Sources unavailable: {result.error} <button className="btn btn-secondary" disabled={busy !== null} onClick={() => void result.reload().catch(() => {})}>Retry search</button></div>}
    {result.status === "ready" && <>
      <p role="status">{sources.length ? `${sources.length} source${sources.length === 1 ? "" : "s"} on this page${filtered ? " matching the applied filters" : ""}.`
        : beforeId ? "No older sources match these filters. Return to the previous page or clear filters."
          : filtered ? "No sources match these filters. Try another phrase or clear filters."
            : "No active private sources. Add a source above or select Archived to restore saved research."}</p>
      <div className="brief-source-list">{sources.map(source => <details className="brief-source-card" key={source.id} open={sources.length === 1 || undefined}>
        <summary><span><strong>{source.title}</strong><span className="cell-secondary">{source.ticker} · {source.source_kind.toUpperCase()} · Source date {source.as_of_date || "unknown"}</span></span>{source.archived_at && <span className="badge badge-outline">Archived</span>}<span className="badge badge-outline">{source.analysis_status.replaceAll("_", " ")}</span>{source.is_mock && <MockDataBadge />}</summary>
        <div className="brief-source-body">
          <div className="section-intro"><Link prefetch={false} href={`/daily-brief/sources/${source.id}`}>Inspect source text{source.source_kind === "pdf" ? " & original PDF" : ""}</Link><span>{source.extraction.character_count.toLocaleString()} characters</span></div>
          {!source.archived_at && source.analysis_status !== "complete" && <button className="btn btn-secondary" disabled={!consent || busy !== null} onClick={() => void onScan(source.id)}>{busy === source.id ? "Scanning…" : source.analysis_status === "failed" || source.analysis_status === "scanning" ? "Retry scan" : "Scan with AI"}</button>}
          <BriefSourceLifecycle source={source} disabled={busy !== null} onBusyChange={onOrganizeBusy} onChanged={onOrganized} />
          {source.warnings.length > 0 && <ul className="compact-list muted">{source.warnings.map(warning => <li key={warning}>{warning}</li>)}</ul>}
          <BriefSourceFindings source={source} />
        </div>
      </details>)}</div>
    </>}
    <nav className="section-intro" aria-label="Research source pages">
      <button className="btn btn-secondary" disabled={cursors.length === 1 || result.status === "loading" || busy !== null} onClick={() => setCursors(current => current.slice(0, -1))}>Previous page</button>
      <span>Page {cursors.length}</span>
      <button className="btn btn-secondary" disabled={!nextCursor || result.status !== "ready" || busy !== null} onClick={() => { if (nextCursor) setCursors(current => [...current, nextCursor]); }}>Older sources</button>
    </nav>
  </section>;
}
