import Link from "next/link";
import { importSecFilings, lookupCompanyCik, addCompanyExposureTag, removeCompanyExposureTag, createExposureTag } from "@/app/actions";
import { EmptyState, ErrorState, PageHeader, Panel } from "@/components/page";
import { ScoreExplanationView } from "@/components/score-explanation";
import { CompanyMarketHeader } from "@/components/company-market-header";
import { FinancialTrends } from "@/components/financial-trends";
import { fetchApi, fetchMarketQuote, fetchFinancialTrends } from "@/lib/api";
import type { AlertRecord, Company, EventRecord, RawDocument, SecFilingMetadata, Source, ThesisNote, ExposureTag, CompanyMarketData, FinancialPeriod } from "@/lib/api";
import { buildCompanyDetail } from "@/lib/company-detail";

type CompanyDetailPageProps = {
  params: Promise<{
    id: string;
  }>;
  searchParams?: Promise<{
    sec_lookup?: string | string[];
    form_type?: string | string[];
    filing_year?: string | string[];
  }>;
};

const SEC_FORM_TYPES = ["10-K", "10-Q", "8-K"];

function scoreText(value: number | null) {
  return value === null ? "-" : String(value);
}

function metadataValue(value: string | null | undefined) {
  return value && value.trim() ? value : "-";
}

function firstParam(value: string | string[] | undefined) {
  return Array.isArray(value) ? value[0] : value;
}

function selectedSecFormType(value: string | string[] | undefined) {
  const formType = firstParam(value);
  return formType && SEC_FORM_TYPES.includes(formType) ? formType : "10-K";
}

function selectedFilingYear(value: string | string[] | undefined) {
  const year = Number(firstParam(value));
  return Number.isInteger(year) && year >= 1994 ? year : new Date().getFullYear();
}

function recentYears() {
  const currentYear = new Date().getFullYear();
  return Array.from({ length: 10 }, (_value, index) => currentYear - index);
}

function filingOptionLabel(filing: SecFilingMetadata) {
  const reportDate = filing.report_date ? `, report ${filing.report_date}` : "";
  return `${filing.form_type} filed ${filing.filing_date}${reportDate}`;
}

function filingJsonValue(filing: SecFilingMetadata) {
  return JSON.stringify([filing]);
}

export default async function CompanyDetailPage({ params, searchParams }: CompanyDetailPageProps) {
  const { id } = await params;
  const query = await searchParams;
  const companyId = Number(id);
  const formType = selectedSecFormType(query?.form_type);
  const filingYear = selectedFilingYear(query?.filing_year);
  const shouldPreviewSecFilings = firstParam(query?.sec_lookup) === "1";

  if (!Number.isInteger(companyId) || companyId <= 0) {
    return (
      <>
        <PageHeader eyebrow="Company" title="Invalid company" />
        <ErrorState message="This company URL is not valid." />
      </>
    );
  }

  try {
    const [companies, documents, events, alerts, thesisNotes, sources, allExposureTags] = await Promise.all([
      fetchApi<Company[]>("/companies"),
      fetchApi<RawDocument[]>("/raw-documents"),
      fetchApi<EventRecord[]>("/events"),
      fetchApi<AlertRecord[]>("/alerts"),
      fetchApi<ThesisNote[]>("/thesis-notes"),
      fetchApi<Source[]>("/sources"),
      fetchApi<ExposureTag[]>("/exposure-tags")
    ]);
    const company = companies.find((item) => item.id === companyId);

    if (!company) {
      return (
        <>
          <PageHeader eyebrow="Company" title="Not found" />
          <ErrorState message="No company exists for this ID." />
        </>
      );
    }

    const [marketQuote, financialTrends] = await Promise.all([
      fetchMarketQuote(company.ticker).catch(() => null),
      fetchFinancialTrends(company.ticker).catch(() => [])
    ]);

    const detail = buildCompanyDetail(company, documents, events, alerts, thesisNotes);
    const secSources = sources.filter((source) => source.source_type === "sec" || source.source_type === "filing" || source.name.toLowerCase().includes("sec"));
    let secFilings: SecFilingMetadata[] = [];
    let secPreviewError: string | null = null;

    if (shouldPreviewSecFilings && company.cik) {
      try {
        secFilings = await fetchApi<SecFilingMetadata[]>(
          `/companies/${company.id}/sec-filings/preview?form_type=${encodeURIComponent(formType)}&filing_year=${filingYear}&limit=20`
        );
      } catch (error) {
        secPreviewError = error instanceof Error ? error.message : "Could not preview SEC filings.";
      }
    }

    return (
      <>
        {/* Header */}
        <div style={{ marginBottom: "1.5rem", paddingBottom: "1.5rem", borderBottom: "1px solid var(--border-color)" }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: "1rem" }}>
            <div>
              <div style={{ fontSize: "0.85rem", fontWeight: 500, color: "var(--text-secondary)", marginBottom: "0.25rem" }}>{company.exchange ?? "Unknown Exchange"}</div>
              <h1 style={{ fontSize: "1.75rem", fontWeight: 600, margin: 0 }}>
                {company.ticker} <span style={{ color: "var(--text-secondary)", fontWeight: 400, fontSize: "1.5rem", margin: "0 0.5rem" }}>|</span> {company.name}
              </h1>
              <CompanyMarketHeader data={marketQuote} />
              <div style={{ display: "flex", flexWrap: "wrap", gap: "0.5rem", marginTop: "0.75rem" }}>
                <span className="badge">{metadataValue(company.sector)}</span>
                <span className="badge">{metadataValue(company.market_cap_category)}</span>
                <span className="badge">{company.active ? "Active Tracking" : "Inactive"}</span>
                {company.exposure_tags?.map(tag => (
                  <span key={tag.id} className="badge">{tag.name}</span>
                ))}
              </div>
            </div>
            <div style={{ display: "flex", gap: "0.5rem" }}>
              <Link className="btn btn-outline" href={`/companies/${company.id}/fundamentals`}>Fundamentals</Link>
              <Link className="btn btn-outline" href={`/companies/${company.id}/valuation`}>Valuation</Link>
              <a className="btn btn-primary" href={`/api/backend/companies/${company.id}/memo`} target="_blank" rel="noopener noreferrer">Download Memo</a>
            </div>
          </div>
        </div>

        {/* Metric Cards */}
        <section className="metric-grid" style={{ marginBottom: "2rem" }}>
          <div className="metric">
            <div className="metric-label">Activity Score</div>
            <div className="metric-value">{detail.counts.events + detail.counts.alerts}</div>
          </div>
          <div className="metric">
            <div className="metric-label">Risk Status</div>
            <div className="metric-value">{detail.counts.alerts > 0 ? "Elevated" : "Normal"}</div>
          </div>
          <div className="metric">
            <div className="metric-label">Documents</div>
            <div className="metric-value">{detail.counts.documents}</div>
          </div>
          <div className="metric">
            <div className="metric-label">Thesis</div>
            <div className="metric-value">{detail.counts.thesisNotes > 0 ? "Active" : "None"}</div>
          </div>
        </section>

        {/* Two-column Grid */}
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "1.5rem", alignItems: "start" }}>
          {/* Left Column */}
          <div style={{ display: "flex", flexDirection: "column", gap: "1.5rem" }}>
            <Panel title="Thesis Notes">
              {detail.thesisNotes.length === 0 ? (
                <EmptyState label="No linked thesis notes." />
              ) : (
                <div className="brief-list">
                  {detail.thesisNotes.map((note) => (
                    <div className="brief-item" key={note.id}>
                      <div className="brief-heading">
                        <strong>{note.title}</strong>
                        <span className="badge">{note.status}</span>
                      </div>
                      <p>{note.thesis_text}</p>
                    </div>
                  ))}
                </div>
              )}
            </Panel>

            <Panel title="Exposure &amp; Factors">
              <div style={{ marginBottom: "1rem" }}>
                {company.exposure_tags?.length > 0 ? (
                  <div style={{ display: "flex", flexWrap: "wrap", gap: "0.5rem", marginBottom: "1rem" }}>
                    {company.exposure_tags.map(tag => (
                      <span key={tag.id} className="badge" style={{ display: "inline-flex", alignItems: "center", gap: "0.25rem" }}>
                        {tag.name}
                        <form action={removeCompanyExposureTag} style={{ display: "inline", marginLeft: "0.25rem" }}>
                          <input type="hidden" name="company_id" value={company.id} />
                          <input type="hidden" name="tag_id" value={tag.id} />
                          <button type="submit" style={{ background: "none", border: "none", cursor: "pointer", padding: 0, color: "var(--error)" }}>&times;</button>
                        </form>
                      </span>
                    ))}
                  </div>
                ) : (
                  <EmptyState label="No exposure factors linked." />
                )}
                <form action={addCompanyExposureTag} style={{ display: "flex", gap: "0.5rem" }}>
                  <input type="hidden" name="company_id" value={company.id} />
                  <select name="tag_id" className="input" style={{ flex: 1, fontSize: "0.85rem" }} defaultValue="">
                    <option value="" disabled>Add an exposure tag...</option>
                    {allExposureTags.filter(t => !company.exposure_tags?.some(ct => ct.id === t.id)).map(tag => (
                      <option key={tag.id} value={tag.id}>{tag.name}</option>
                    ))}
                  </select>
                  <button type="submit" style={{ fontSize: "0.85rem" }}>Add</button>
                </form>
              </div>
            </Panel>

            <FinancialTrends trends={financialTrends} />

            <Panel title="SEC Filing Picker">
              <div className="brief-list">
                {!company.cik ? (
                  <form action={lookupCompanyCik} className="inline-form">
                    <input name="id" type="hidden" value={company.id} />
                    <div>
                      <strong>CIK is missing.</strong>
                      <p className="muted">Look up the company CIK before selecting SEC filings.</p>
                    </div>
                    <button className="secondary-button" type="submit">Look up CIK</button>
                  </form>
                ) : (
                  <>
                    <form className="form-grid" method="get">
                      <input name="sec_lookup" type="hidden" value="1" />
                      <div className="field">
                        <label htmlFor="form_type">Form</label>
                        <select defaultValue={formType} id="form_type" name="form_type">
                          {SEC_FORM_TYPES.map((type) => (
                            <option key={type} value={type}>{type}</option>
                          ))}
                        </select>
                      </div>
                      <div className="field">
                        <label htmlFor="filing_year">Filing Year</label>
                        <select defaultValue={filingYear} id="filing_year" name="filing_year">
                          {recentYears().map((year) => (
                            <option key={year} value={year}>{year}</option>
                          ))}
                        </select>
                      </div>
                      <div className="button-row">
                        <button type="submit">Preview filings</button>
                      </div>
                    </form>
                    {secPreviewError ? <ErrorState message={secPreviewError} /> : null}
                    {shouldPreviewSecFilings && !secPreviewError ? (
                      secFilings.length === 0 ? (
                        <EmptyState label={`No ${formType} filings found for ${filingYear}.`} />
                      ) : (
                        <form action={importSecFilings} className="form-grid">
                          <input name="company_id" type="hidden" value={company.id} />
                          <input name="form_type" type="hidden" value={formType} />
                          <input name="filing_year" type="hidden" value={filingYear} />
                          <div className="field">
                            <label htmlFor="source_id">SEC Source</label>
                            <select disabled={secSources.length === 0} id="source_id" name="source_id" required>
                              <option value="">Select SEC source</option>
                              {secSources.map((source) => (
                                <option key={source.id} value={source.id}>{source.name}</option>
                              ))}
                            </select>
                          </div>
                          <div className="field field-wide">
                            <label htmlFor="filings_json">Filing</label>
                            <select id="filings_json" name="filings_json" required>
                              {secFilings.map((filing) => (
                                <option key={filing.accession_number} value={filingJsonValue(filing)}>
                                  {filingOptionLabel(filing)}
                                </option>
                              ))}
                            </select>
                          </div>
                          <div className="field field-wide checkbox-field">
                            <label htmlFor="download_text">
                              <input id="download_text" name="download_text" type="checkbox" />
                              Download filing text
                            </label>
                          </div>
                          <div className="button-row">
                            <button disabled={secSources.length === 0} type="submit">Import selected filing</button>
                          </div>
                        </form>
                      )
                    ) : null}
                  </>
                )}
              </div>
            </Panel>

            <Panel title="Raw Documents">
              {detail.documents.length === 0 ? (
                <EmptyState label="No linked documents." />
              ) : (
                <div className="table-wrap">
                  <table>
                    <thead>
                      <tr>
                        <th>Title</th>
                        <th>Type</th>
                        <th>Source ID</th>
                        <th>Hash</th>
                      </tr>
                    </thead>
                    <tbody>
                      {detail.documents.map((document) => (
                        <tr key={document.id}>
                          <td>{document.url ? <a href={document.url}>{document.title}</a> : document.title}</td>
                          <td>{document.document_type}</td>
                          <td>{document.source_id}</td>
                          <td>{document.content_hash}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </Panel>
          </div>

          {/* Right Column */}
          <div style={{ display: "flex", flexDirection: "column", gap: "1.5rem" }}>
            <Panel title="News Flow (Events)">
              {detail.events.length === 0 ? (
                <EmptyState label="No linked events." />
              ) : (
                <div className="table-wrap">
                  <table>
                    <thead>
                      <tr>
                        <th>Headline</th>
                        <th>Type</th>
                        <th>Priority</th>
                        <th>Score</th>
                      </tr>
                    </thead>
                    <tbody>
                      {detail.events.map((event) => (
                        <tr key={event.id}>
                          <td>
                            <strong>{event.title}</strong>
                            {event.description ? <p className="muted">{event.description}</p> : null}
                          </td>
                          <td>{event.event_type}</td>
                          <td>{scoreText(event.priority_score)}</td>
                          <td>
                            <details className="edit-panel">
                              <summary>Details</summary>
                              <ScoreExplanationView explanation={event.score_explanation_json} />
                            </details>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </Panel>

            <Panel title="Risks (Alerts)">
              {detail.alerts.length === 0 ? (
                <EmptyState label="No active alerts." />
              ) : (
                <div className="table-wrap">
                  <table>
                    <thead>
                      <tr>
                        <th>Title</th>
                        <th>Severity</th>
                        <th>Status</th>
                      </tr>
                    </thead>
                    <tbody>
                      {detail.alerts.map((alert) => (
                        <tr key={alert.id}>
                          <td>
                            <strong>{alert.title}</strong>
                            {alert.summary ? <p className="muted">{alert.summary}</p> : null}
                          </td>
                          <td>
                            <span className={`badge ${alert.severity === 'high' ? 'badge-danger' : alert.severity === 'medium' ? 'badge-warning' : ''}`}>
                              {alert.severity}
                            </span>
                          </td>
                          <td>{alert.review_status}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </Panel>
          </div>
        </div>

        <div className="button-row">
          <Link className="secondary-button" href="/companies">Back to companies</Link>
        </div>
      </>
    );
  } catch {
    return (
      <>
        <PageHeader eyebrow="Company" title="Company detail" />
        <ErrorState message="Could not load company detail from the backend API." />
      </>
    );
  }
}
