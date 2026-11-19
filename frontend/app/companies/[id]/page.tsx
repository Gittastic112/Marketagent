import { RetainedActionForm } from "@/components/retained-action-form";
import Link from "next/link";
import { Suspense } from "react";
import { CompanyResearchCards } from "@/components/company-research-cards";
import { CompanyValuationSummary } from "@/components/company-valuation-summary";
import { importSecFilings, lookupCompanyCik, addCompanyExposureTag, removeCompanyExposureTag, createExposureTag } from "@/app/actions";
import { DataStateNotices, EmptyState, ErrorState, PageHeader, Panel } from "@/components/page";
import { ScoreExplanationView } from "@/components/score-explanation";
import { triggerEventClassification } from "@/app/actions";
import { CompanyMarketHeader } from "@/components/company-market-header";
import { CompanyPriceChart } from "@/components/company-price-chart";
import type { PricePin, PriceTimeline } from "@/lib/api/price-timeline";
import { SyncPriceButton } from "@/components/sync-price-button";
import { FinancialTrends } from "@/components/financial-trends";
import { CheckboxField } from "@/components/form-fields";
import { ManualDataBadge } from "@/components/ui/data-states";
import { hasUsableData, summarizeApiMetas } from "@/lib/data-state-meta";
import type { AlertRecord, Company, EventRecord, RawDocument, SecFilingMetadata, Source, ThesisNote, ExposureTag, CompanyMarketData, FinancialStatementPeriod } from "@/lib/api";
import type { ValuationModelSummary } from "@/lib/api/valuation";
import { serverFetchApiResponse } from "@/lib/server-api";
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
    price_series?: string | string[];
    price_date?: string | string[];
    thesis?: string | string[];
    pin?: string | string[];
  }>;
};

const SEC_FORM_TYPES = ["10-K", "10-Q", "8-K"];

function scoreText(value: number | null) {
  return value === null ? "-" : String(value);
}

function metadataValue(value: string | null | undefined) {
  return value && value.trim() ? value : "-";
}

function boundedSummary(value: string | null | undefined, limit = 500) {
  if (!value) {
    return null;
  }
  const normalized = value.replace(/\s+/g, " ").trim();
  return normalized.length > limit ? `${normalized.slice(0, limit).trimEnd()}...` : normalized;
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

    const companies = hasUsableData(companiesRes) ? companiesRes.data : [];
    const documentsAvailable = hasUsableData(documentsRes);
    const eventsAvailable = hasUsableData(eventsRes);
    const alertsAvailable = hasUsableData(alertsRes);
    const thesisNotesAvailable = hasUsableData(thesisNotesRes);
    const sourcesAvailable = hasUsableData(sourcesRes);
    const exposureTagsAvailable = hasUsableData(allExposureTagsRes);
    const documents = documentsAvailable ? documentsRes.data : [];
    const events = eventsAvailable ? eventsRes.data : [];
    const alerts = alertsAvailable ? alertsRes.data : [];
    const thesisNotes = thesisNotesAvailable ? thesisNotesRes.data : [];
    const sources = sourcesAvailable ? sourcesRes.data : [];
    const allExposureTags = exposureTagsAvailable ? allExposureTagsRes.data : [];

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
      if (!hasUsableData(companiesRes) || companiesRes.errors.length) {
        return <><PageHeader eyebrow="Company" title="Company unavailable" />
          <ErrorState message="Company records could not be loaded." errors={companiesRes.errors} />
          <div className="button-row"><a className="secondary-button" href={`/companies/${companyId}`}>Try again</a>
            <Link href="/companies">Back to companies</Link></div></>;
      }
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
    const priceQuery = new URLSearchParams();
    const thesisId = Number(firstParam(query?.thesis));
    const pinId = Number(firstParam(query?.pin));
    const requestedPin = Number.isSafeInteger(thesisId) && thesisId > 0 && Number.isSafeInteger(pinId) && pinId > 0;
    const priceSeries = firstParam(query?.price_series);
    const priceDate = firstParam(query?.price_date);
    if (priceSeries) priceQuery.set("series", priceSeries);
    if (priceDate) priceQuery.set("through", priceDate);
    const [marketQuote, financialTrends, modelSummaries, priceTimeline, pinResponse] = await Promise.all([
      serverFetchApiResponse<CompanyMarketData>(`/api/market/quote?${quoteParams.toString()}`),
      serverFetchApiResponse<FinancialStatementPeriod[]>(`/companies/${company.id}/financial-periods`),
      serverFetchApiResponse<ValuationModelSummary[]>(`/companies/${company.id}/valuation-model-summaries`),
      serverFetchApiResponse<PriceTimeline>(`/companies/${company.id}/price-timeline${priceQuery.size ? `?${priceQuery}` : ""}`),
      requestedPin ? serverFetchApiResponse<PricePin[]>(`/thesis-notes/${thesisId}/price-pins`) : null
    ]);

    const originalPin = hasUsableData(pinResponse) && !pinResponse.errors.length && Array.isArray(pinResponse.data)
      ? pinResponse.data.find(pin => pin.id === pinId && pin.thesis_note_id === thesisId && pin.company_id === company.id) : null;
    const sameDate = originalPin && hasUsableData(priceTimeline) && priceTimeline.data.series?.key === originalPin.anchor.key
      ? priceTimeline.data.points.find(point => point.date === originalPin.anchor.date) : null;

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
        <DataStateNotices
          metas={[companiesRes.meta, documentsRes.meta, eventsRes.meta, alertsRes.meta, thesisNotesRes.meta, sourcesRes.meta, allExposureTagsRes.meta]}
          mockMessage="One or more company panels are using mock data. Treat affected evidence, alerts, or thesis signals as placeholders."
        />
        {(!documentsAvailable || !eventsAvailable || !alertsAvailable || !thesisNotesAvailable || !sourcesAvailable || !exposureTagsAvailable) && <p className="button-row">
          <a className="secondary-button" href={`/companies/${company.id}`}>Try again</a>
          <Link href="/data-health">Check data connections</Link>
        </p>}
        <header className="company-overview-header">
          <div className="company-overview-identity">
              <div className="company-meta-line">
                <span>{company.market ?? "Unknown Market"} / {company.primary_exchange ?? company.exchange ?? "Unknown Exchange"}</span>
                {company.local_symbol && <span>• Local: {company.local_symbol}</span>}
                {company.market && company.market !== "US" && <ManualDataBadge />}
              </div>
              <h1 className="company-title">
                <span>{company.ticker}</span>
                <span className="company-title-divider" aria-hidden="true">/</span>
                <span>{company.name}</span>
              </h1>
              <div className="company-market-row">
                <CompanyMarketHeader response={marketQuote} />
                <SyncPriceButton companyId={company.id} market={company.market} />
              </div>
              <div className="company-badge-row">
                <span className="badge">{metadataValue(company.sector)}</span>
                {company.market_cap_category && <span className="badge">{company.market_cap_category}</span>}
                <span className="badge">{company.active ? "Active Tracking" : "Inactive"}</span>
                {company.exposure_tags?.map(tag => (
                  <span key={tag.id} className="badge">{tag.name}</span>
                ))}
              </div>
          </div>
          <a className="secondary-button company-memo-link" href={`/api/backend/companies/${company.id}/memo`} target="_blank" rel="noopener noreferrer">Download memo</a>
        </header>

        <section id="price-history" className="company-overview-history" aria-label="Stock price history">
          {requestedPin && (originalPin ? <Panel title="Historical thesis note">
            <p>Close when pinned · {originalPin.anchor.date} · {originalPin.anchor.currency} {originalPin.anchor.price}</p>
            <p>{sameDate?.price != null ? `Current stored close for that date · ${originalPin.anchor.currency} ${sameDate.price}` : "Current close for the pinned observation is unavailable."}</p>
            <p className="price-note-text">{originalPin.text}</p>
            <Link href={`/thesis-notes/${originalPin.thesis_note_id}#price-pins`}>Open original thesis note</Link>
          </Panel> : <p>The requested private price note is unavailable.</p>)}
          <Panel title="Price history">
            {hasUsableData(priceTimeline) && Array.isArray(priceTimeline.data.points) && Array.isArray(priceTimeline.data.choices) ? <>
              <DataStateNotices metas={[priceTimeline.meta]} />
              <CompanyPriceChart key={`${company.id}-${priceTimeline.data.series?.key}-${priceDate ?? ""}`}
                data={priceTimeline.data} companyId={company.id} requestedDate={priceDate}
                notes={thesisNotesAvailable ? detail.thesisNotes.map(({ id, title }) => ({ id, title })) : null} />
            </> : <><ErrorState message="Price history could not be loaded." errors={priceTimeline.errors} />
              <Link href={`/companies/${company.id}#price-history`}>Reload latest history</Link></>}
          </Panel>
        </section>

        <div className="company-summary-grid">
          <Suspense fallback={<p role="status">Loading business context…</p>}><CompanyResearchCards companyIds={[company.id]} compact /></Suspense>
          <CompanyValuationSummary companyId={company.id} response={modelSummaries} />
        </div>

        <div className="company-overview-history"><FinancialTrends response={financialTrends} companyId={company.id} compact /></div>

        <div className="company-overview-grid">
          {/* Left Column */}
          <div className="company-overview-column">
            <Panel title="Research notes" actions={<Link prefetch={false} href={`/companies/${company.id}/thesis`}>Open thesis</Link>}>
              {!thesisNotesAvailable ? <ErrorState message="Thesis notes could not be loaded." errors={thesisNotesRes.errors} /> : detail.thesisNotes.length === 0 ? (
                <EmptyState label="No linked thesis notes." />
              ) : (
                <div className="brief-list">
                  {[...detail.thesisNotes].sort((a, b) => b.id - a.id).slice(0, 3).map((note) => (
                    <div className="brief-item" key={note.id}>
                      <div className="brief-heading">
                        <Link prefetch={false} href={`/thesis-notes/${note.id}`}><strong>{note.title}</strong></Link>
                        <span className="badge">{note.status}</span>
                      </div>
                      <p className="company-note-excerpt">{boundedSummary(note.thesis_text, 300)}</p>
                      <Link prefetch={false} href={`/thesis-notes/${note.id}`}>Read full note</Link>
                    </div>
                  ))}
                  {detail.thesisNotes.length > 3 && <details>
                    <summary>All research notes ({detail.thesisNotes.length})</summary>
                    <div className="company-note-links">{detail.thesisNotes.map(note => <Link prefetch={false} key={note.id} href={`/thesis-notes/${note.id}`}>{note.title}</Link>)}</div>
                  </details>}
                </div>
              )}
            </Panel>

            <div id="company-tools" className="company-overview-tools"><Panel title="Exposure tags" collapsible>
              <div style={{ marginBottom: "1rem" }}>
                {company.exposure_tags?.length > 0 ? (
                  <div style={{ display: "flex", flexWrap: "wrap", gap: "0.5rem", marginBottom: "1rem" }}>
                    {company.exposure_tags.map(tag => (
                      <span key={tag.id} className="badge" style={{ display: "inline-flex", alignItems: "center", gap: "0.25rem" }}>
                        {tag.name}
                        <RetainedActionForm label="Remove company exposure tag" action={removeCompanyExposureTag} style={{ display: "inline", marginLeft: "0.25rem" }}>
                          <input type="hidden" name="company_id" value={company.id} />
                          <input type="hidden" name="tag_id" value={tag.id} />
                          <button type="submit" aria-label={`Remove ${tag.name} exposure tag`} style={{ background: "none", border: "none", cursor: "pointer", padding: 0, color: "var(--error)" }}>&times;</button>
                        </RetainedActionForm>
                      </span>
                    ))}
                  </div>
                ) : (
                  <EmptyState label="No exposure factors linked." />
                )}
                {!exposureTagsAvailable ? <ErrorState message="Exposure tags could not be loaded." errors={allExposureTagsRes.errors} /> : <RetainedActionForm label="Add company exposure tag" action={addCompanyExposureTag} style={{ display: "flex", gap: "0.5rem" }}>
                  <input type="hidden" name="company_id" value={company.id} />
                  <select name="tag_id" aria-label="Exposure tag" className="input" style={{ flex: 1, fontSize: "0.85rem" }} defaultValue="">
                    <option value="" disabled>Add an exposure tag...</option>
                    {allExposureTags.filter(t => !company.exposure_tags?.some(ct => ct.id === t.id)).map(tag => (
                      <option key={tag.id} value={tag.id}>{tag.name}</option>
                    ))}
                  </select>
                  <button type="submit" style={{ fontSize: "0.85rem" }}>Add</button>
                </RetainedActionForm>}
              </div>
            </Panel></div>

            <Panel title={company.market === "IN" ? "Filing source" : "SEC filing intake"} collapsible={!shouldPreviewSecFilings}>
              <div className="brief-list">
                {!sourcesAvailable && <ErrorState message="Filing sources could not be loaded." errors={sourcesRes.errors} />}
                {company.market === "IN" ? (
                  <EmptyState label="India automated filing provider not configured. Add exchange filing links manually from the Documents page." />
                ) : !company.cik ? (
                  <RetainedActionForm label="Lookup company cik" action={lookupCompanyCik} className="inline-form">
                    <input name="id" type="hidden" value={company.id} />
                    <div>
                      <strong>CIK is missing.</strong>
                      <p className="muted">Look up the company CIK before selecting SEC filings.</p>
                    </div>
                    <button className="secondary-button" type="submit">Look up CIK</button>
                  </RetainedActionForm>
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
                        <RetainedActionForm label="Import sec filings" resetOnSuccess action={importSecFilings} className="form-grid">
                          <input name="company_id" type="hidden" value={company.id} />
                          <input name="form_type" type="hidden" value={formType} />
                          <input name="filing_year" type="hidden" value={filingYear} />
                          {preferredSecSource ? (
                            <input name="source_id" type="hidden" value={preferredSecSource.id} />
                          ) : null}
                          <div className="field field-wide">
                            <label>SEC Source</label>
                            <div className="data-line">
                              <strong>{sourcesAvailable ? preferredSecSource?.name ?? "SEC EDGAR (automatic)" : "Source list unavailable"}</strong>
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
                            <button type="submit" disabled={!sourcesAvailable}>Import selected filing</button>
                          </div>
                        </RetainedActionForm>
                      )
                    ) : null}
                  </>
                )}
              </div>
            </Panel>

            <Panel title={`Source documents (${documentsAvailable ? detail.counts.documents : "unavailable"})`} collapsible>
              {!documentsAvailable ? <ErrorState message="Documents could not be loaded." errors={documentsRes.errors} /> : detail.documents.length === 0 ? (
                <EmptyState label="No linked documents." />
              ) : (
                <div tabIndex={0} className="table-wrap">
                  <table>
                    <thead>
                      <tr>
                        <th>Title</th>
                        <th>Type</th>
                        <th>Technical details</th>
                      </tr>
                    </thead>
                    <tbody>
                      {detail.documents.map((document) => (
                        <tr key={document.id}>
                          <td><Link prefetch={false} href={`/documents/${document.id}/sections`}>{document.title}</Link>{document.url && <div><a href={document.url} target="_blank" rel="noopener noreferrer">Original source</a></div>}</td>
                          <td>{document.document_type}</td>
                          <td><details><summary>Source details</summary><p>Source ID: {document.source_id}</p><p className="company-note-excerpt">Hash: {document.content_hash}</p></details></td>
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
            <Panel title="Recent source activity" actions={<Link prefetch={false} href={`/companies/${company.id}/filings`}>Open sources</Link>}>
              {!eventsAvailable ? <ErrorState message="Events could not be loaded." errors={eventsRes.errors} /> : detail.events.length === 0 ? (
                <EmptyState label="No linked events." />
              ) : (
                <div className="company-event-list">
                  {detail.events.map((event) => (
                    <article className="company-event-card" key={event.id}>
                      <div className="company-event-copy">
                        <Link prefetch={false} href={`/events/${event.id}/evidence-resolution`}><strong>{event.title}</strong></Link>
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
                      <details className="company-event-details"><summary>Propose thesis impact</summary><RetainedActionForm label="Trigger event classification" action={triggerEventClassification} className="company-event-action">
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
                      </RetainedActionForm></details>
                    </article>
                  ))}
                </div>
              )}
            </Panel>

            <Panel title="Alerts to review">
              {!alertsAvailable ? <ErrorState message="Alerts could not be loaded." errors={alertsRes.errors} /> : detail.alerts.length === 0 ? (
                <EmptyState label="No active alerts." />
              ) : (
                <div tabIndex={0} className="table-wrap">
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
                            <Link prefetch={false} href={`/alerts/${alert.id}`}><strong>{alert.title}</strong></Link>
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
        <div className="button-row"><a className="secondary-button" href={`/companies/${companyId}`}>Try again</a>
          <Link href="/companies">Back to companies</Link></div>
      </>
    );
  }
}
