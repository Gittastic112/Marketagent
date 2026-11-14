import { RetainedActionForm } from "@/components/retained-action-form";
import Link from "next/link";
import { formatDataLabel } from "@/lib/formatting";
import { hasUsableData } from "@/lib/data-state-meta";
import {
  deleteRawDocumentWithState,
  updateRawDocument
} from "@/app/actions";
import { DeleteRecordForm } from "@/components/delete-record-form";
import { SelectField, TextField } from "@/components/form-fields";
import { EmptyState, ErrorState, PageHeader, Panel } from "@/components/page";
import { DataStateNotices } from "@/components/ui/data-states";
import { serverFetchApiResponse } from "@/lib/server-api";
import type { Company, RawDocument, Source } from "@/lib/api";

function sourceOptions(sources: Source[]) {
  return sources.map((source) => (
    <option key={source.id} value={source.id}>
      {source.name}
    </option>
  ));
}

function companyOptions(companies: Company[]) {
  return companies.map((company) => (
    <option key={company.id} value={company.id}>
      {company.ticker}
    </option>
  ));
}

export default async function DocumentsPage({ searchParams }: { searchParams?: Promise<Record<string, string | string[] | undefined>> }) {
  try {
    const params = (await searchParams) ?? {};
    const filters = new URLSearchParams();
    for (const field of ["q", "company_id", "document_type", "review", "published_from", "published_to", "offset"]) {
      const value = params[field]; if (typeof value === "string" && value) filters.set(field, value);
    }
    const [docsRes, companiesRes, sourcesRes] = await Promise.all([
      serverFetchApiResponse<{items: RawDocument[]; total: number; offset: number; limit: number}>(`/raw-documents/library?${filters}`),
      serverFetchApiResponse<Company[]>("/companies"),
      serverFetchApiResponse<Source[]>("/sources")
    ]);
    const documents = [...(docsRes.data?.items || [])].sort((a, b) =>
      (Date.parse(b.ingested_at || b.created_at || "") || 0) - (Date.parse(a.ingested_at || a.created_at || "") || 0) || b.id - a.id);
    const companies = companiesRes.data || [];
    const sources = sourcesRes.data || [];
    const companiesById = new Map(companies.map(company => [company.id, company]));
    const sourcesById = new Map(sources.map(source => [source.id, source]));
    const pageLink = (offset: number) => { const query = new URLSearchParams(filters); query.set("offset", String(offset)); return `/documents?${query}`; };

    return (
      <>
        <PageHeader eyebrow="Source material" title="Raw Documents" status={hasUsableData(docsRes) ? `${docsRes.data?.total} matching documents` : "Documents unavailable"} />
        <p><Link href="/research">Research library</Link> · <Link href="/">Today review queue</Link> · <Link href="/settings">Source configuration and processing</Link></p>
        <form method="get" className="panel form-grid" aria-label="Filter stored sources">
          <label>Search titles<input name="q" defaultValue={filters.get("q") || ""} maxLength={200} /></label>
          <label>Company<select name="company_id" defaultValue={filters.get("company_id") || ""}><option value="">All companies</option>{companyOptions(companies)}</select></label>
          <label>Document type<input name="document_type" defaultValue={filters.get("document_type") || ""} placeholder="e.g. annual_report" maxLength={80} /></label>
          <label>Financial review<select name="review" defaultValue={filters.get("review") || "all"}>
            <option value="all">All sources</option><option value="needs_review">Has candidates to review or promote</option><option value="promoted">Has promoted candidates</option></select></label>
          <label>Published from<input name="published_from" type="date" defaultValue={filters.get("published_from") || ""} /></label>
          <label>Published through<input name="published_to" type="date" defaultValue={filters.get("published_to") || ""} /></label>
          <button type="submit">Filter library</button><Link href="/documents">Clear filters</Link>
        </form>
        <p>Review filters describe financial candidates, not approval of the whole document. Sources with unknown publication dates are excluded from date-filtered results.</p>
        {docsRes.data && <nav className="button-row" aria-label="Document pages">
          {docsRes.data.offset > 0 && <Link href={pageLink(Math.max(0, docsRes.data.offset - docsRes.data.limit))}>Previous page</Link>}
          <span>{docsRes.data.total ? docsRes.data.offset + 1 : 0}–{docsRes.data.offset + documents.length} of {docsRes.data.total}</span>
          {docsRes.data.offset + documents.length < docsRes.data.total && <Link href={pageLink(docsRes.data.offset + docsRes.data.limit)}>Next page</Link>}
        </nav>}
        <DataStateNotices
          metas={[docsRes.meta, companiesRes.meta, sourcesRes.meta]}
          mockMessage="One or more document inputs are using mock data. Treat affected source trails as placeholders."
        />
        <Panel title="Stored Documents">
          {!hasUsableData(docsRes) ? <ErrorState message="Documents could not be loaded. Reload to retry." /> : documents.length === 0 ? (
            <EmptyState label="No raw documents yet." />
          ) : (
            <div className="table-wrap" tabIndex={0} role="region" aria-label="Stored source documents">
              <table>
                <thead>
                  <tr>
                    <th>Title</th>
                    <th>Type</th>
                    <th>Company</th>
                    <th>Source</th>
                    <th>Hash</th>
                    <th>Action</th>
                  </tr>
                </thead>
                <tbody>
                  {documents.map((document) => (
                    <tr key={document.id}>
                      <td><Link href={`/documents/${document.id}/sections`}>{document.title}</Link></td>
                      <td>{formatDataLabel(document.document_type)}</td>
                      <td>{document.company_id == null ? "Unlinked" : <Link href={`/companies/${document.company_id}`}>{companiesById.get(document.company_id)?.ticker || `Company #${document.company_id}`}</Link>}</td>
                      <td>{sourcesById.get(document.source_id)?.name || `Source #${document.source_id}`}</td>
                      <td><details className="source-hash"><summary>View hash</summary><code>{document.content_hash}</code></details></td>
                      <td>
                        <div className="action-stack">
                          <details className="edit-panel">
                            <summary>Edit</summary>
                            <RetainedActionForm label="Update raw document" action={updateRawDocument} className="inline-form">
                              <input name="id" type="hidden" value={document.id} />
                              <SelectField defaultValue={document.source_id} id={`doc-source-${document.id}`} label="Source" name="source_id" required>
                                {sourceOptions(sources)}
                              </SelectField>
                              <SelectField defaultValue={document.company_id ?? ""} id={`doc-company-${document.id}`} label="Company" name="company_id">
                                <option value="">Unlinked</option>
                                {companyOptions(companies)}
                              </SelectField>
                              <TextField defaultValue={document.document_type} id={`doc-type-${document.id}`} label="Type" name="document_type" required />
                              <TextField defaultValue={document.content_hash} id={`doc-hash-${document.id}`} label="Hash" name="content_hash" required />
                              <TextField className="field field-full" defaultValue={document.title} id={`doc-title-${document.id}`} label="Title" name="title" required />
                              <TextField className="field field-full" defaultValue={document.url ?? ""} id={`doc-url-${document.id}`} label="URL" name="url" type="url" />
                              <TextField
                                defaultValue={document.published_at?.slice(0, 16) ?? ""}
                                id={`doc-published-${document.id}`}
                                label="Source publication time"
                                name="published_at"
                                type="datetime-local"
                              />
                              <div className="button-row">
                                <button className="secondary-button" type="submit">Save</button>
                              </div>
                            </RetainedActionForm>
                          </details>
                          <a className="secondary-button" href={`/documents/${document.id}/sections`}>Sections &amp; Diffs</a>
                          <a className="secondary-button" href={`/documents/${document.id}/ai`}>AI Summaries</a>
                          <DeleteRecordForm action={deleteRawDocumentWithState} recordId={document.id} />
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </Panel>
      </>
    );
  } catch {
    return (
      <>
        <PageHeader eyebrow="Source material" title="Raw Documents" />
        <ErrorState message="Could not load raw documents from the backend API." />
      </>
    );
  }
}
