import Link from "next/link";
import { notFound } from "next/navigation";
import { BriefSourceFindings } from "@/components/brief-source-findings";
import { BriefSourceLifecycle } from "@/components/brief-source-lifecycle";
import { ErrorState, PageHeader, Panel } from "@/components/page";
import type { BriefSource } from "@/lib/api/brief-sources";
import { serverFetchApiResponse } from "@/lib/server-api";

export default async function BriefSourcePage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  if (!/^\d+$/.test(id)) notFound();
  const response = await serverFetchApiResponse<BriefSource & { text: string }>(`/brief-sources/${id}`);
  const source = response.data;
  if (!source) return <ErrorState message="Source is unavailable or does not belong to this account." errors={response.errors} />;
  return <>
    <PageHeader eyebrow={`Private research · ${source.ticker}`} title={source.title} status={source.as_of_date || "Source date unknown"} />
    <div className="section-intro"><Link href="/daily-brief">← Research inbox</Link><Link href={`/companies/${source.company_id}`}>Company workspace</Link>
      <Link prefetch={false} href={`/daily-brief/triage?company_id=${source.company_id}`}>Compare this company&apos;s sources</Link>
      {source.source_kind === "pdf" && <a href={`/api/backend/brief-sources/${source.id}/pdf`} target="_blank" rel="noopener noreferrer">Open original PDF ↗</a>}
      {source.source_url && <a href={source.source_url} target="_blank" rel="noopener noreferrer">Supplied source URL ↗</a>}
    </div>
    <Panel title={source.archived_at ? "Archived source" : "Source organization"}>
      <BriefSourceLifecycle key={source.id} source={source} />
    </Panel>
    <Panel title="Source and extraction basis"><p>Uploaded by you, not independently authenticated. Source date: {source.as_of_date || "unknown"}. Stored {new Date(source.created_at).toLocaleString("en-US", { timeZone: "UTC", timeZoneName: "short" })}.</p>
      <p className="muted">SHA-256: <span className="brief-source-hash">{source.source_sha256}</span></p>
      {source.extraction.selected_pages && <p>Extracted PDF pages: {source.extraction.selected_pages.join(", ")} of {source.extraction.page_count}.</p>}
      <ul className="compact-list muted">{source.warnings.map(warning => <li key={warning}>{warning}</li>)}</ul>
      <details open><summary>Stored source text</summary><pre className="brief-source-text">{source.text}</pre></details>
    </Panel>
    {source.analysis && <Panel title="Ranked findings and valuation review"><BriefSourceFindings source={source} includeAnchors /></Panel>}
  </>;
}
