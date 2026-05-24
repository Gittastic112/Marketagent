import { createRawDocument, deleteRawDocument, importRssXml, importSecFilings, updateRawDocument } from "@/app/actions";
import { EmptyState, ErrorState, PageHeader, Panel } from "@/components/page";
import { fetchApi } from "@/lib/api";
import type { Company, RawDocument, Source } from "@/lib/api";

export default async function DocumentsPage() {
  try {
    const [documents, companies, sources] = await Promise.all([
      fetchApi<RawDocument[]>("/raw-documents"),
      fetchApi<Company[]>("/companies"),
      fetchApi<Source[]>("/sources")
    ]);

    return (
      <>
        <PageHeader eyebrow="Source material" title="Raw Documents" status={`${documents.length} stored`} />
        <Panel title="Add Raw Document">
          <form action={createRawDocument} className="form-grid">
            <div className="field">
              <label htmlFor="source_id">Source</label>
              <select disabled={sources.length === 0} id="source_id" name="source_id" required>
                <option value="">Select source</option>
                {sources.map((source) => (
                  <option key={source.id} value={source.id}>
                    {source.name}
                  </option>
                ))}
              </select>
            </div>
            <div className="field">
              <label htmlFor="company_id">Company</label>
              <select id="company_id" name="company_id">
                <option value="">Unlinked</option>
                {companies.map((company) => (
                  <option key={company.id} value={company.id}>
                    {company.ticker}
                  </option>
                ))}
              </select>
            </div>
            <div className="field">
              <label htmlFor="document_type">Type</label>
              <input id="document_type" name="document_type" placeholder="filing" required />
            </div>
            <div className="field">
              <label htmlFor="content_hash">Content Hash</label>
              <input id="content_hash" name="content_hash" required />
            </div>
            <div className="field field-wide">
              <label htmlFor="title">Title</label>
              <input id="title" name="title" required />
            </div>
            <div className="field field-wide">
              <label htmlFor="url">URL</label>
              <input id="url" name="url" type="url" />
            </div>
            <div className="field field-full">
              <label htmlFor="raw_text">Raw Text</label>
              <textarea id="raw_text" name="raw_text" />
            </div>
            <div className="button-row">
              <button disabled={sources.length === 0} type="submit">Add document</button>
            </div>
          </form>
        </Panel>
        <Panel title="Import RSS XML">
          <form action={importRssXml} className="form-grid">
            <div className="field">
              <label htmlFor="rss-source-id">Source</label>
              <select disabled={sources.length === 0} id="rss-source-id" name="source_id" required>
                <option value="">Select RSS source</option>
                {sources.map((source) => (
                  <option key={source.id} value={source.id}>
                    {source.name}
                  </option>
                ))}
              </select>
            </div>
            <div className="field">
              <label htmlFor="rss-company-id">Company</label>
              <select id="rss-company-id" name="company_id">
                <option value="">Unlinked</option>
                {companies.map((company) => (
                  <option key={company.id} value={company.id}>
                    {company.ticker}
                  </option>
                ))}
              </select>
            </div>
            <div className="field field-full">
              <label htmlFor="rss-xml">RSS XML</label>
              <textarea id="rss-xml" name="rss_xml" required />
            </div>
            <div className="button-row">
              <button disabled={sources.length === 0} type="submit">Import RSS</button>
            </div>
          </form>
        </Panel>
        <Panel title="Import SEC Filing Metadata">
          <form action={importSecFilings} className="form-grid">
            <div className="field">
              <label htmlFor="sec-source-id">Source</label>
              <select disabled={sources.length === 0} id="sec-source-id" name="source_id" required>
                <option value="">Select SEC source</option>
                {sources.map((source) => (
                  <option key={source.id} value={source.id}>
                    {source.name}
                  </option>
                ))}
              </select>
            </div>
            <div className="field">
              <label htmlFor="sec-company-id">Company</label>
              <select disabled={companies.length === 0} id="sec-company-id" name="company_id" required>
                <option value="">Select company</option>
                {companies.map((company) => (
                  <option key={company.id} value={company.id}>
                    {company.ticker}
                  </option>
                ))}
              </select>
            </div>
            <div className="field field-full">
              <label htmlFor="filings-json">Filings JSON</label>
              <textarea
                id="filings-json"
                name="filings_json"
                required
                defaultValue={`[
  {
    "accession_number": "0000320193-26-000001",
    "form_type": "10-K",
    "filing_date": "2026-05-24",
    "report_date": "2026-03-31",
    "primary_document": "aapl-20260331.htm",
    "filing_url": "https://www.sec.gov/example/aapl-20260331.htm"
  }
]`}
              />
            </div>
            <div className="button-row">
              <button disabled={sources.length === 0 || companies.length === 0} type="submit">Import SEC filings</button>
            </div>
          </form>
        </Panel>
        <Panel title="Documents">
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
                              <div className="field">
                                <label htmlFor={`doc-source-${document.id}`}>Source</label>
                                <select defaultValue={document.source_id} id={`doc-source-${document.id}`} name="source_id" required>
                                  {sources.map((source) => (
                                    <option key={source.id} value={source.id}>
                                      {source.name}
                                    </option>
                                  ))}
                                </select>
                              </div>
                              <div className="field">
                                <label htmlFor={`doc-company-${document.id}`}>Company</label>
                                <select defaultValue={document.company_id ?? ""} id={`doc-company-${document.id}`} name="company_id">
                                  <option value="">Unlinked</option>
                                  {companies.map((company) => (
                                    <option key={company.id} value={company.id}>
                                      {company.ticker}
                                    </option>
                                  ))}
                                </select>
                              </div>
                              <div className="field">
                                <label htmlFor={`doc-type-${document.id}`}>Type</label>
                                <input defaultValue={document.document_type} id={`doc-type-${document.id}`} name="document_type" required />
                              </div>
                              <div className="field">
                                <label htmlFor={`doc-hash-${document.id}`}>Hash</label>
                                <input defaultValue={document.content_hash} id={`doc-hash-${document.id}`} name="content_hash" required />
                              </div>
                              <div className="field field-full">
                                <label htmlFor={`doc-title-${document.id}`}>Title</label>
                                <input defaultValue={document.title} id={`doc-title-${document.id}`} name="title" required />
                              </div>
                              <div className="field field-full">
                                <label htmlFor={`doc-url-${document.id}`}>URL</label>
                                <input defaultValue={document.url ?? ""} id={`doc-url-${document.id}`} name="url" type="url" />
                              </div>
                              <div className="field field-full">
                                <label htmlFor={`doc-text-${document.id}`}>Raw Text</label>
                                <textarea defaultValue={document.raw_text ?? ""} id={`doc-text-${document.id}`} name="raw_text" />
                              </div>
                              <div className="button-row">
                                <button className="secondary-button" type="submit">Save</button>
                              </div>
                            </form>
                          </details>
                          <form action={deleteRawDocument} className="row-action">
                            <input name="id" type="hidden" value={document.id} />
                            <button className="danger-button" type="submit">Delete</button>
                          </form>
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
