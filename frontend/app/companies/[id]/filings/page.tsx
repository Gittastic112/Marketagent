import Link from "next/link";
import { notFound } from "next/navigation";

import { createManualCompanyFilingLink, extractFinancialCandidatesFromFiling, extractXbrlFromCompany } from "@/app/actions";
import { SelectField, TextAreaField, TextField } from "@/components/form-fields";
import { EmptyState, ErrorState, PageHeader, Panel } from "@/components/page";
import { PdfFilingUpload } from "@/components/pdf-filing-upload";
import type { Company, FilingDiscovery, RawDocument } from "@/lib/api";
import { serverFetchApi, serverFetchApiResponse } from "@/lib/server-api";


function formatDate(value: string | null | undefined) {
  if (!value) {
    return "-";
  }
  return new Date(value).toLocaleDateString("en-US", { year: "numeric", month: "short", day: "numeric" });
}

function sourceLabel(document: RawDocument) {
  const payload = document.raw_payload_json || {};
  const sourceKind = typeof payload.source_kind === "string" ? payload.source_kind : "filing";
  const market = typeof payload.market === "string" ? payload.market : null;
  return market ? `${sourceKind.replaceAll("_", " ")} / ${market}` : sourceKind.replaceAll("_", " ");
}

function isPdfUpload(document: RawDocument) {
  return document.raw_payload_json?.source_kind === "pdf_filing_upload";
}

async function loadFilings(companyId: number) {
  return serverFetchApiResponse<RawDocument[]>(`/api/companies/${companyId}/filings`);
}

async function loadDiscovery(companyId: number) {
  return serverFetchApiResponse<FilingDiscovery>(`/api/companies/${companyId}/filings/discover?limit=10`);
}

export default async function CompanyFilingsPage(props: { params: Promise<{ id: string }> }) {
  const params = await props.params;
  const companyId = Number(params.id);
  if (!Number.isFinite(companyId)) {
    notFound();
  }

  let company: Company;
  try {
    company = await serverFetchApi<Company>(`/companies/${companyId}`);
  } catch {
    notFound();
  }

  const [discoveryRes, filingsRes] = await Promise.all([
    loadDiscovery(companyId),
    loadFilings(companyId),
  ]);
  const discovery = discoveryRes.data;
  const filings = filingsRes.data || [];

  return (
    <>
      <PageHeader
        eyebrow="Filings"
        title={company.name}
        status={`${company.market ?? "US"} / ${company.primary_exchange ?? company.exchange ?? "-"}`}
      />

      <div className="button-row" style={{ marginBottom: "1.5rem" }}>
        <Link className="secondary-button" href={`/companies/${company.id}`}>Back to company</Link>
        <Link className="secondary-button" href={`/companies/${company.id}/setup`}>Setup</Link>
        <Link className="secondary-button" href={`/companies/${company.id}/fundamentals`}>Financials</Link>
        <Link className="secondary-button" href={`/companies/${company.id}/valuation`}>Valuation</Link>
        {company.cik && (
          <form action={extractXbrlFromCompany} style={{ display: "inline-block" }}>
            <input name="company_id" type="hidden" value={company.id} />
            <button type="submit" className="primary-button">Extract via SEC XBRL</button>
          </form>
        )}
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "minmax(0, 1fr) 360px", gap: "1.5rem", alignItems: "start" }}>
        <div style={{ display: "flex", flexDirection: "column", gap: "1.5rem" }}>
          <Panel title="Discovery Status">
            {discovery ? (
              <>
                <div className="metric-grid" style={{ marginBottom: "1rem" }}>
                  <div className="metric">
                    <div className="metric-label">Provider</div>
                    <div className="metric-value" style={{ fontSize: "1rem" }}>{discovery.provider_name}</div>
                  </div>
                  <div className="metric">
                    <div className="metric-label">Mode</div>
                    <div className="metric-value" style={{ fontSize: "1rem" }}>{discovery.mode.replaceAll("_", " ")}</div>
                  </div>
                  <div className="metric">
                    <div className="metric-label">Candidates</div>
                    <div className="metric-value">{discovery.filings.length}</div>
                  </div>
                </div>
                <p className="muted" style={{ margin: 0 }}>{discovery.next_action}</p>
              </>
            ) : (
              <ErrorState message="Could not discover filing candidates." errors={discoveryRes.errors} />
            )}
          </Panel>

          <Panel title="Discovered Candidates">
            {discovery?.filings.length ? (
              <div className="table-wrap">
                <table>
                  <thead>
                    <tr>
                      <th>Form</th>
                      <th>Filing date</th>
                      <th>Report date</th>
                      <th>Accession</th>
                      <th>Source</th>
                    </tr>
                  </thead>
                  <tbody>
                    {discovery.filings.map((filing) => (
                      <tr key={filing.accession_number}>
                        <td>{filing.form_type}</td>
                        <td>{formatDate(filing.filing_date)}</td>
                        <td>{formatDate(filing.report_date)}</td>
                        <td><code>{filing.accession_number}</code></td>
                        <td>
                          {filing.filing_url ? (
                            <a href={filing.filing_url} target="_blank" rel="noopener noreferrer">Open filing</a>
                          ) : (
                            <span className="muted">No URL</span>
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : (
              <EmptyState label={discovery?.manual_required ? "Automated filing discovery is not configured for this market." : "No filing candidates returned."} />
            )}
          </Panel>

          <Panel title="Stored Filings">
            {filingsRes.errors.length > 0 ? (
              <ErrorState message="Could not load stored filings." errors={filingsRes.errors} />
            ) : filings.length ? (
              <div className="table-wrap">
                <table>
                  <thead>
                    <tr>
                      <th>Title</th>
                      <th>Type</th>
                      <th>Published</th>
                      <th>Source</th>
                      <th>Link</th>
                      <th>Extraction</th>
                    </tr>
                  </thead>
                  <tbody>
                    {filings.map((filing) => (
                      <tr key={filing.id}>
                        <td>
                          <strong>{filing.title}</strong>
                          <div className="muted" style={{ fontSize: "0.82rem" }}>Document #{filing.id}</div>
                        </td>
                        <td>{filing.document_type.replaceAll("_", " ")}</td>
                        <td>{formatDate(filing.published_at)}</td>
                        <td>{sourceLabel(filing)}</td>
                        <td>
                          {isPdfUpload(filing) ? (
                            <a
                              href={`/api/backend/api/raw-documents/${filing.id}/asset/content`}
                              target="_blank"
                              rel="noopener noreferrer"
                            >
                              Open PDF
                            </a>
                          ) : filing.url ? (
                            <a href={filing.url} target="_blank" rel="noopener noreferrer">Open source</a>
                          ) : (
                            <span className="muted">Text only</span>
                          )}
                        </td>
                        <td>
                          {isPdfUpload(filing) ? (
                            <Link href={`/companies/${company.id}/fundamentals`}>Review candidates</Link>
                          ) : (
                            <form action={extractFinancialCandidatesFromFiling}>
                              <input name="filing_id" type="hidden" value={filing.id} />
                              <input name="company_id" type="hidden" value={company.id} />
                              <button type="submit" className="secondary-button" style={{ padding: "0.35rem 0.6rem" }}>
                                Extract candidates
                              </button>
                            </form>
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : (
              <EmptyState label="No filing documents stored yet." />
            )}
          </Panel>
        </div>

        <div style={{ display: "flex", flexDirection: "column", gap: "1.5rem" }}>
          <Panel title="Upload PDF Filing">
            <PdfFilingUpload companyId={company.id} />
          </Panel>
          <Panel title="Add Manual Filing">
            <form action={createManualCompanyFilingLink} className="form-grid">
            <input name="id" type="hidden" value={company.id} />
            <SelectField defaultValue={company.market === "IN" ? "annual_report" : "annual_report"} id="document_type" label="Document type" name="document_type" required>
              <option value="annual_report">Annual report</option>
              <option value="quarterly_result">Quarterly result</option>
              <option value="investor_presentation">Investor presentation</option>
              <option value="exchange_announcement">Exchange announcement</option>
              <option value="shareholding_pattern">Shareholding pattern</option>
              <option value="corporate_action">Corporate action</option>
            </SelectField>
            <TextField id="title" label="Title" name="title" required placeholder="FY2026 Annual Report" />
            <TextField id="url" label="Source URL" name="url" type="url" placeholder="https://..." />
            <TextField id="published_at" label="Published date" name="published_at" type="date" />
            <TextAreaField
              className="field field-full"
              id="raw_text"
              label="Reviewed source text"
              name="raw_text"
              rows={8}
              placeholder="Paste reviewed filing text or a short excerpt. Do not paste unreviewed HTML."
            />
            <div className="button-row field-full">
              <button type="submit">Add filing source</button>
            </div>
            </form>
            <p className="muted" style={{ marginBottom: 0, marginTop: "1rem" }}>
              Manual sources are stored as raw documents and marked for review before financial extraction.
            </p>
          </Panel>
        </div>
      </div>
    </>
  );
}
