import Link from "next/link";
import { importSecFilings, lookupCompanyCik, addCompanyExposureTag, removeCompanyExposureTag, createExposureTag } from "@/app/actions";
import { EmptyState, ErrorState, MockDataState, PageHeader, Panel } from "@/components/page";
import { ScoreExplanationView } from "@/components/score-explanation";
import { triggerEventClassification } from "@/app/actions";
import { CompanyMarketHeader } from "@/components/company-market-header";
import { SyncPriceButton } from "@/components/sync-price-button";
import { FinancialTrends } from "@/components/financial-trends";
import { CheckboxField } from "@/components/form-fields";
import { StaleDataBanner, PartialDataNotice, ManualDataBadge } from "@/components/ui/data-states";
import { summarizeApiMetas } from "@/lib/data-state-meta";
import type { AlertRecord, Company, EventRecord, RawDocument, SecFilingMetadata, Source, ThesisNote, ExposureTag, CompanyMarketData, FinancialPeriod } from "@/lib/api";
import { serverFetchApi, serverFetchApiResponse } from "@/lib/server-api";
import { buildCompanyDetail } from "@/lib/company-detail";
import { AI_DISCLOSURES, AI_PRIVACY_DISCLOSURE_VERSION } from "@/lib/ai-privacy";
import { DataHealthUpdater } from "@/components/providers/data-health-updater";

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

function boundedSummary(value: string | null | undefined) {
  if (!value) {
    return null;
  }
  const normalized = value.replace(/\s+/g, " ").trim();
  return normalized.length > 500 ? `${normalized.slice(0, 500).trimEnd()}...` : normalized;
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
    const [companiesRes, documentsRes, eventsRes, alertsRes, thesisNotesRes, sourcesRes, allExposureTagsRes] = await Promise.all([
      serverFetchApiResponse<Company[]>("/companies"),
      serverFetchApiResponse<RawDocument[]>("/raw-documents/summaries"),
      serverFetchApiResponse<EventRecord[]>("/events"),
      serverFetchApiResponse<AlertRecord[]>("/alerts"),
      serverFetchApiResponse<ThesisNote[]>("/thesis-notes"),
      serverFetchApiResponse<Source[]>("/sources"),
      serverFetchApiResponse<ExposureTag[]>("/exposure-tags")
    ]);

    const companies = companiesRes.data || [];
    const documents = documentsRes.data || [];
    const events = eventsRes.data || [];
    const alerts = alertsRes.data || [];
    const thesisNotes = thesisNotesRes.data || [];
    const sources = sourcesRes.data || [];
    const allExposureTags = allExposureTagsRes.data || [];

    const dataState = summarizeApiMetas([
      companiesRes.meta,
      documentsRes.meta,
      eventsRes.meta,
      alertsRes.meta,
      thesisNotesRes.meta,
      sourcesRes.meta,
      allExposureTagsRes.meta
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

    const quoteParams = new URLSearchParams({ ticker: company.local_symbol ?? company.ticker });
    if (company.market) quoteParams.set("market", company.market);
    if (company.primary_exchange ?? company.exchange) quoteParams.set("exchange", company.primary_exchange ?? company.exchange ?? "");
    if (company.currency) quoteParams.set("currency", company.currency);
    const [marketQuote, financialTrends] = await Promise.all([
      serverFetchApi<CompanyMarketData>(`/api/market/quote?${quoteParams.toString()}`).catch(() => null),
      serverFetchApi<FinancialPeriod[]>(`/fundamentals/${encodeURIComponent(company.ticker)}/trends`).catch(() => [])
    ]);

    const detail = buildCompanyDetail(company, documents, events, alerts, thesisNotes);
    const secSources = sources.filter(
      (source) => source.active && (
        source.source_type === "sec"
        || source.source_type === "filing"
        || source.name.toLowerCase().includes("sec")
      )
    );
    const preferredSecSource = secSources[0] ?? null;
    let secFilings: SecFilingMetadata[] = [];
    let secPreviewError: string | null = null;

    if (shouldPreviewSecFilings && company.cik) {
      try {
        const previewRes = await serverFetchApiResponse<SecFilingMetadata[]>(
          `/companies/${company.id}/sec-filings/preview?form_type=${encodeURIComponent(formType)}&filing_year=${filingYear}&limit=20`
        );
        secFilings = previewRes.data || [];
        if (previewRes.errors?.length > 0) {
          secPreviewError = previewRes.errors[0].message;
        }
      } catch (error) {
        secPreviewError = error instanceof Error ? error.message : "Could not preview SEC filings.";
      }
    }

    return (
      <>
        <DataHealthUpdater segment="" isStale={dataState.someStale || dataState.allStale} />
        {dataState.someStale && <PartialDataNotice message="Some company panels are showing cached data because the backend is partially reachable." />}
        {dataState.hasMock && <MockDataState message="One or more company panels are using mock data. Treat affected evidence, alerts, or thesis signals as placeholders." />}
        <header className="company-overview-header">
          <div className="company-overview-identity">
              <div className="company-meta-line">
                <span>{company.market ?? "Unknown Market"} / {company.primary_exchange ?? company.exchange ?? "Unknown Exchange"}</span>
                {company.local_symbol && <span>• Local: {company.local_symbol}</span>}
                {company.regulatory_id && <span>• {company.regulatory_id_type || "Reg ID"}: {company.regulatory_id}</span>}
                {company.market && company.market !== "US" && <ManualDataBadge />}
              </div>
              <h1 className="company-title">
                <span>{company.ticker}</span>
                <span className="company-title-divider" aria-hidden="true">/</span>
                <span>{company.name}</span>
              </h1>
              <div className="company-market-row">
                <CompanyMarketHeader data={marketQuote} />
                <SyncPriceButton companyId={company.id} market={company.market} />
              </div>
              <div className="company-badge-row">
                <span className="badge">{metadataValue(company.sector)}</span>
                <span className="badge">{metadataValue(company.market_cap_category)}</span>
                <span className="badge">{company.active ? "Active Tracking" : "Inactive"}</span>
                {company.exposure_tags?.map(tag => (
                  <span key={tag.id} className="badge">{tag.name}</span>
                ))}
              </div>
          </div>
          <a className="secondary-button company-memo-link" href={`/api/backend/companies/${company.id}/memo`} target="_blank" rel="noopener noreferrer">Download memo</a>
        </header>

        {/* Metric Cards */}
        <section className="metric-grid company-metric-grid">
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

        <div className="company-overview-grid">
          {/* Left Column */}
          <div className="company-overview-column">
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

            <Panel title={company.market === "IN" ? "Filing Source" : "SEC Filing Picker"}>
              <div className="brief-list">
                {company.market === "IN" ? (
                  <EmptyState label="India automated filing provider not configured. Add exchange filing links manually from the Documents page." />
                ) : !company.cik ? (
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
                          {preferredSecSource ? (
                            <input name="source_id" type="hidden" value={preferredSecSource.id} />
                          ) : null}
                          <div className="field field-wide">
                            <label>SEC Source</label>
                            <div className="data-line">
                              <strong>{preferredSecSource?.name ?? "SEC EDGAR (automatic)"}</strong>
                            </div>
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
                          <CheckboxField
                            checkboxLabel="Download filing text"
                            className="field field-wide"
                            id="download_text"
                            label="Filing Content"
                            name="download_text"
                          />
                          <div className="button-row">
                            <button type="submit">Import selected filing</button>
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
          <div className="company-overview-column">
            <Panel title="News Flow (Events)">
              {detail.events.length === 0 ? (
                <EmptyState label="No linked events." />
              ) : (
                <div className="company-event-list">
                  {detail.events.map((event) => (
                    <article className="company-event-card" key={event.id}>
                      <div className="company-event-copy">
                        <strong>{event.title}</strong>
                        {boundedSummary(event.description) ? (
                          <p className="muted">{boundedSummary(event.description)}</p>
                        ) : null}
                        <div className="company-event-meta">
                          <span className="badge">{event.event_type}</span>
                          <span>Priority {scoreText(event.priority_score)}</span>
                        </div>
                      </div>
                      <details className="edit-panel company-event-details">
                        <summary>Score details</summary>
                        <ScoreExplanationView explanation={event.score_explanation_json} />
                      </details>
                      <form action={triggerEventClassification} className="company-event-action">
                        <input type="hidden" name="event_id" value={event.id} />
                        <input type="hidden" name="company_id" value={company.id} />
                        <label className="privacy-consent">
                          <input
                            type="checkbox"
                            name="privacy_disclosure_version"
                            value={AI_PRIVACY_DISCLOSURE_VERSION}
                            required
                          />
                          <span>{AI_DISCLOSURES.thesisImpact}</span>
                        </label>
                        <button type="submit" className="secondary-button">Propose impact</button>
                      </form>
                    </article>
                  ))}
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
                            {boundedSummary(alert.summary) ? (
                              <p className="muted">{boundedSummary(alert.summary)}</p>
                            ) : null}
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
