import Link from "next/link";
import { importSecFilings, lookupCompanyCik, addCompanyExposureTag, removeCompanyExposureTag, createExposureTag } from "@/app/actions";
import { EmptyState, ErrorState, PageHeader, Panel } from "@/components/page";
import { ScoreExplanationView } from "@/components/score-explanation";
import { fetchApi } from "@/lib/api";
import type { AlertRecord, Company, EventRecord, RawDocument, SecFilingMetadata, Source, ThesisNote, ExposureTag } from "@/lib/api";
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
        <PageHeader eyebrow="Company" title={`${company.ticker} - ${company.name}`} status={company.active ? "active" : "inactive"} />
        <div className="button-row" style={{ marginBottom: "1rem" }}>
          <Link className="secondary-button" href={`/companies/${company.id}/fundamentals`}>
            Fundamentals
          </Link>
          <Link className="secondary-button" href={`/companies/${company.id}/valuation`}>
            Valuation Models
          </Link>
          <a className="secondary-button" href={`/api/backend/companies/${company.id}/memo`} target="_blank" rel="noopener noreferrer">
            Download Memo
          </a>
        </div>
        <Panel title="Company Profile">
          <div className="summary-grid">
            <div>
              <span className="label">Sector</span>
              <strong>{metadataValue(company.sector)}</strong>
            </div>
            <div>
              <span className="label">Industry</span>
              <strong>{metadataValue(company.industry)}</strong>
            </div>
            <div>
              <span className="label">Exchange</span>
              <strong>{metadataValue(company.exchange)}</strong>
            </div>
            <div>
              <span className="label">Country</span>
              <strong>{metadataValue(company.country)}</strong>
            </div>
            <div>
              <span className="label">Region</span>
              <strong>{metadataValue(company.region)}</strong>
            </div>
            <div>
              <span className="label">Currency</span>
              <strong>{metadataValue(company.currency)}</strong>
            </div>
            <div>
              <span className="label">Asset Type</span>
              <strong>{metadataValue(company.asset_type)}</strong>
            </div>
            <div>
              <span className="label">Security Type</span>
              <strong>{metadataValue(company.security_type)}</strong>
            </div>
            <div>
              <span className="label">Market Cap</span>
              <strong>{metadataValue(company.market_cap_category)}</strong>
            </div>
            <div>
              <span className="label">ETF</span>
              <strong>{company.is_etf ? "yes" : "no"}</strong>
            </div>
            <div>
              <span className="label">ETF Provider</span>
              <strong>{metadataValue(company.etf_provider)}</strong>
            </div>
            <div>
              <span className="label">CIK</span>
              <strong>{metadataValue(company.cik)}</strong>
            </div>
            <div>
              <span className="label">Aliases</span>
              <strong>{company.aliases_json?.join(", ") || "-"}</strong>
            </div>
          </div>
        </Panel>
        <Panel title="Linked Records">
          <div className="summary-grid">
            <div>
              <span className="label">Documents</span>
              <strong>{detail.counts.documents}</strong>
            </div>
            <div>
              <span className="label">Events</span>
              <strong>{detail.counts.events}</strong>
            </div>
            <div>
              <span className="label">Alerts</span>
              <strong>{detail.counts.alerts}</strong>
            </div>
            <div>
              <span className="label">Thesis Notes</span>
              <strong>{detail.counts.thesisNotes}</strong>
            </div>
          </div>
        </Panel>

        <Panel title="Exposure & Factors">
          <div className="mb-4">
            {company.exposure_tags?.length > 0 ? (
              <div className="flex flex-wrap gap-2 mb-4">
                {company.exposure_tags.map(tag => (
                  <span key={tag.id} className="inline-flex items-center px-2 py-1 rounded bg-blue-100 text-blue-800 text-sm">
                    {tag.name}
                    <form action={removeCompanyExposureTag} className="ml-2 inline">
                      <input type="hidden" name="company_id" value={company.id} />
                      <input type="hidden" name="tag_id" value={tag.id} />
                      <button type="submit" className="text-blue-500 hover:text-blue-900 leading-none">&times;</button>
                    </form>
                  </span>
                ))}
              </div>
            ) : (
              <p className="text-sm text-gray-500 mb-4">No exposure tags assigned.</p>
            )}
            
            <form action={addCompanyExposureTag} className="flex gap-2 items-center mb-4">
              <input type="hidden" name="company_id" value={company.id} />
              <select name="tag_id" className="p-2 border rounded" required>
                <option value="">Assign existing tag...</option>
                {allExposureTags
                  .filter(t => !company.exposure_tags?.some(ct => ct.id === t.id))
                  .map(tag => (
                  <option key={tag.id} value={tag.id}>{tag.name}</option>
                ))}
              </select>
              <button type="submit" className="px-4 py-2 bg-blue-600 text-white rounded">Assign</button>
            </form>

            <div className="border-t pt-4 mt-2">
              <h4 className="text-sm font-medium mb-2">Create New Tag</h4>
              <form action={createExposureTag} className="flex gap-2 items-center">
                <input type="hidden" name="company_id" value={company.id} />
                <input type="text" name="name" placeholder="Tag Name (e.g. rate_sensitive)" className="p-2 border rounded" required />
                <input type="text" name="description" placeholder="Description (optional)" className="p-2 border rounded flex-1" />
                <button type="submit" className="px-4 py-2 bg-gray-200 text-gray-800 rounded">Create & Refresh</button>
              </form>
            </div>
          </div>
        </Panel>

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
                        <option key={type} value={type}>
                          {type}
                        </option>
                      ))}
                    </select>
                  </div>
                  <div className="field">
                    <label htmlFor="filing_year">Filing Year</label>
                    <select defaultValue={filingYear} id="filing_year" name="filing_year">
                      {recentYears().map((year) => (
                        <option key={year} value={year}>
                          {year}
                        </option>
                      ))}
                    </select>
                  </div>
                  <div className="button-row">
                    <button type="submit">Find filings</button>
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
                            <option key={source.id} value={source.id}>
                              {source.name}
                            </option>
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
        <Panel title="Events">
          {detail.events.length === 0 ? (
            <EmptyState label="No linked events." />
          ) : (
            <div className="table-wrap">
              <table>
                <thead>
                  <tr>
                    <th>Title</th>
                    <th>Type</th>
                    <th>Priority</th>
                    <th>Speed</th>
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
                      <td>{event.information_speed}</td>
                      <td>
                        <details className="edit-panel">
                          <summary>Why this score?</summary>
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
        <Panel title="Alerts">
          {detail.alerts.length === 0 ? (
            <EmptyState label="No linked alerts." />
          ) : (
            <div className="table-wrap">
              <table>
                <thead>
                  <tr>
                    <th>Title</th>
                    <th>Severity</th>
                    <th>Confidence</th>
                    <th>Review</th>
                  </tr>
                </thead>
                <tbody>
                  {detail.alerts.map((alert) => (
                    <tr key={alert.id}>
                      <td>
                        <strong>{alert.title}</strong>
                        {alert.summary ? <p className="muted">{alert.summary}</p> : null}
                      </td>
                      <td>{alert.severity}</td>
                      <td>{alert.confidence_bucket}</td>
                      <td>{alert.review_status}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </Panel>
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
        <div className="button-row">
          <Link className="secondary-button" href="/companies">
            Back to companies
          </Link>
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
