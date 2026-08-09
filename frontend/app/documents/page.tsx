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

export default async function DocumentsPage() {
  try {
    const [docsRes, companiesRes, sourcesRes] = await Promise.all([
      serverFetchApiResponse<RawDocument[]>("/raw-documents/summaries"),
      serverFetchApiResponse<Company[]>("/companies"),
      serverFetchApiResponse<Source[]>("/sources")
    ]);
    const documents = docsRes.data || [];
    const companies = companiesRes.data || [];
    const sources = sourcesRes.data || [];

    return (
      <>
        <PageHeader eyebrow="Source material" title="Raw Documents" status={`${documents.length} stored`} />
        <DataStateNotices
          metas={[docsRes.meta, companiesRes.meta, sourcesRes.meta]}
          mockMessage="One or more document inputs are using mock data. Treat affected source trails as placeholders."
        />
        <Panel title="Stored Documents">
          {documents.length === 0 ? (
            <EmptyState label="No raw documents yet." />
          ) : (
            <div className="table-wrap">
              <table>
                <thead>
                  <tr>
                    <th>Title</th>
                    <th>Type</th>
                    <th>Company ID</th>
                    <th>Source ID</th>
                    <th>Hash</th>
                    <th>Action</th>
                  </tr>
                </thead>
                <tbody>
                  {documents.map((document) => (
                    <tr key={document.id}>
                      <td>{document.title}</td>
                      <td>{document.document_type}</td>
                      <td>{document.company_id ?? "-"}</td>
                      <td>{document.source_id}</td>
                      <td>{document.content_hash}</td>
                      <td>
                        <div className="action-stack">
                          <details className="edit-panel">
                            <summary>Edit</summary>
                            <form action={updateRawDocument} className="inline-form">
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
                              <div className="button-row">
                                <button className="secondary-button" type="submit">Save</button>
                              </div>
                            </form>
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
