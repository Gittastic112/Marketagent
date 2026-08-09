import Link from "next/link";

import { createAlert, deleteAlertWithState, generateAlerts, reviewAlert, updateAlert } from "@/app/actions";
import { DeleteRecordForm } from "@/components/delete-record-form";
import { SelectField, TextAreaField, TextField } from "@/components/form-fields";
import { EvidenceTrailDrawerWrapper } from "@/components/intelligence/EvidenceTrailDrawerWrapper";
import { EmptyState, ErrorState, PageHeader, Panel } from "@/components/page";
import { ScoreExplanationView } from "@/components/score-explanation";
import { DataStateNotices, SourceBadge } from "@/components/ui/data-states";
import { serverFetchApiResponse } from "@/lib/server-api";
import type { AlertRecord, Company, EventRecord } from "@/lib/api";

const REVIEW_STATUSES = ["unreviewed", "useful", "not_useful", "false_positive", "needs_follow_up"] as const;
const REVIEW_FILTERS = ["all", ...REVIEW_STATUSES] as const;

type ReviewFilter = (typeof REVIEW_FILTERS)[number];

type AlertsPageProps = {
  searchParams?: Promise<{
    review_status?: string | string[];
    owned_only?: string | string[];
  }>;
};

function reviewStatusOptions() {
  return REVIEW_STATUSES.map((reviewStatus) => (
    <option key={reviewStatus} value={reviewStatus}>
      {reviewStatus}
    </option>
  ));
}

function severityOptions() {
  return ["low", "medium", "high"].map((severity) => (
    <option key={severity} value={severity}>
      {severity}
    </option>
  ));
}

function confidenceOptions() {
  return ["low", "medium", "high"].map((confidence) => (
    <option key={confidence} value={confidence}>
      {confidence}
    </option>
  ));
}

function getReviewFilter(value: string | string[] | undefined): ReviewFilter {
  const reviewStatus = Array.isArray(value) ? value[0] : value;
  return REVIEW_FILTERS.includes(reviewStatus as ReviewFilter) ? (reviewStatus as ReviewFilter) : "all";
}

function formatReviewedAt(value: string | null) {
  return value ? new Date(value).toLocaleString() : "Not reviewed";
}

export default async function AlertsPage({ searchParams }: AlertsPageProps) {
  try {
    const params = await searchParams;
    const selectedReviewStatus = getReviewFilter(params?.review_status);
    const rawOwned = Array.isArray(params?.owned_only) ? params.owned_only[0] : params?.owned_only;
    const ownedOnly = rawOwned === "true";
    const alertsPath = ownedOnly ? "/alerts?owned_only=true" : "/alerts";
    const [alertsRes, companiesRes, eventsRes] = await Promise.all([
      serverFetchApiResponse<AlertRecord[]>(alertsPath),
      serverFetchApiResponse<Company[]>("/companies"),
      serverFetchApiResponse<EventRecord[]>("/events")
    ]);
    const alerts = alertsRes.data || [];
    const companies = companiesRes.data || [];
    const events = eventsRes.data || [];

    const filteredAlerts =
      selectedReviewStatus === "all" ? alerts : alerts.filter((alert) => alert.review_status === selectedReviewStatus);
    const eventsById = new Map(events.map((event) => [event.id, event]));
    const companiesById = new Map(companies.map((c) => [c.id, c]));

    return (
      <>
        <PageHeader eyebrow="Review queue" title="Alerts" status={`${filteredAlerts.length} of ${alerts.length} alerts`} />
        <DataStateNotices
          metas={[alertsRes.meta, companiesRes.meta, eventsRes.meta]}
          mockMessage="One or more alert inputs are using mock data. Review those alerts as placeholders, not source-backed intelligence."
        />
        <Panel title="Generate Alerts">
          <form action={generateAlerts} className="brief-list">
            <div className="brief-item">
              <div className="button-row">
                <button type="submit">Generate alerts</button>
              </div>
            </div>
          </form>
        </Panel>
        <Panel title="Filter Alerts">
          <div className="button-row" style={{ flexWrap: "wrap" }}>
            {REVIEW_FILTERS.map((reviewStatus) => {
              const base = ownedOnly ? `owned_only=true` : "";
              const qs = reviewStatus === "all" ? (base ? `?${base}` : "") : `?review_status=${reviewStatus}${base ? `&${base}` : ""}`;
              return (
                <a
                  aria-current={selectedReviewStatus === reviewStatus ? "page" : undefined}
                  className={selectedReviewStatus === reviewStatus ? "secondary-button active-link" : "secondary-button"}
                  href={`/alerts${qs}`}
                  key={reviewStatus}
                >
                  {reviewStatus}
                </a>
              );
            })}
            <span style={{ borderLeft: "1px solid var(--line)", margin: "0 4px" }} />
            <a
              className={ownedOnly ? "secondary-button active-link" : "secondary-button"}
              href={ownedOnly ? "/alerts" : "/alerts?owned_only=true"}
            >
              {ownedOnly ? "✓ Owned companies" : "Owned companies"}
            </a>
          </div>
        </Panel>
        <Panel title="Add Alert">
          <form action={createAlert} className="form-grid">
            <SelectField id="company_id" label="Company" name="company_id">
              <option value="">Unlinked</option>
              {companies.map((company) => (
                <option key={company.id} value={company.id}>
                  {company.ticker}
                </option>
              ))}
            </SelectField>
            <SelectField id="event_id" label="Event" name="event_id">
              <option value="">Unlinked</option>
              {events.map((event) => (
                <option key={event.id} value={event.id}>
                  {event.title}
                </option>
              ))}
            </SelectField>
            <TextField id="alert_type" label="Type" name="alert_type" placeholder="thesis_watch" required />
            <SelectField defaultValue="low" id="severity" label="Severity" name="severity">
              {severityOptions()}
            </SelectField>
            <TextField className="field field-wide" id="title" label="Title" name="title" required />
            <SelectField defaultValue="low" id="confidence_bucket" label="Confidence" name="confidence_bucket">
              {confidenceOptions()}
            </SelectField>
            <SelectField defaultValue="unreviewed" id="review_status" label="Review" name="review_status">
              {reviewStatusOptions()}
            </SelectField>
            <TextAreaField className="field field-full" id="summary" label="Summary" name="summary" />
            <TextAreaField className="field field-full" id="why_it_matters" label="Why It Matters" name="why_it_matters" />
            <TextAreaField className="field field-full" id="review_notes" label="Review Notes" name="review_notes" />
            <div className="button-row">
              <button type="submit">Add alert</button>
            </div>
          </form>
        </Panel>
        <Panel title="Alerts">
          {filteredAlerts.length === 0 ? (
            <EmptyState label="No alerts yet." />
          ) : (
            <div className="table-wrap">
              <table>
                <thead>
                  <tr>
                    <th>Title</th>
                    <th>Company</th>
                    <th>Type</th>
                    <th>Severity</th>
                    <th>Confidence</th>
                    <th>Priority</th>
                    <th>Review</th>
                    <th>Reviewed</th>
                    <th>Action</th>
                  </tr>
                </thead>
                <tbody>
                  {filteredAlerts.map((alert) => (
                    <tr key={alert.id}>
                      <td>
                        <strong>{alert.title}</strong>
                        {alert.review_notes ? <p className="muted">{alert.review_notes}</p> : null}
                      </td>
                      <td>{alert.company_id ? (companiesById.get(alert.company_id)?.ticker ?? `#${alert.company_id}`) : "—"}</td>
                      <td>
                        <div style={{ display: "flex", flexDirection: "column", gap: "0.25rem", alignItems: "flex-start" }}>
                          {alert.alert_type === "priority_event" ? <SourceBadge source="System" /> : <SourceBadge source="Manual" />}
                          <span>{alert.alert_type}</span>
                        </div>
                      </td>
                      <td>{alert.severity}</td>
                      <td>{alert.confidence_bucket}</td>
                      <td>{alert.portfolio_priority_score > 0 ? alert.portfolio_priority_score.toFixed(1) : "—"}</td>
                      <td>
                        <form action={reviewAlert} className="inline-form">
                          <input name="id" type="hidden" value={alert.id} />
                          <SelectField defaultValue={alert.review_status} id={`quick-review-${alert.id}`} label="Review" name="review_status">
                            {reviewStatusOptions()}
                          </SelectField>
                          <TextAreaField defaultValue={alert.review_notes ?? ""} id={`quick-review-notes-${alert.id}`} label="Notes" name="review_notes" />
                          <button className="secondary-button" type="submit">Save review</button>
                        </form>
                      </td>
                      <td>{formatReviewedAt(alert.reviewed_at)}</td>
                      <td>
                        <div className="action-stack">
                          <Link className="secondary-button" href={`/alerts/${alert.id}`}>Review alert</Link>
                          <EvidenceTrailDrawerWrapper alertId={alert.id} />
                          <details className="edit-panel">
                            <summary>Why this score?</summary>
                            <ScoreExplanationView explanation={alert.event_id ? eventsById.get(alert.event_id)?.score_explanation_json ?? null : null} />
                          </details>
                          <details className="edit-panel">
                            <summary>Edit</summary>
                            <form action={updateAlert} className="inline-form">
                              <input name="id" type="hidden" value={alert.id} />
                              <SelectField defaultValue={alert.company_id ?? ""} id={`alert-company-${alert.id}`} label="Company" name="company_id">
                                <option value="">Unlinked</option>
                                {companies.map((company) => (
                                  <option key={company.id} value={company.id}>
                                    {company.ticker}
                                  </option>
                                ))}
                              </SelectField>
                              <SelectField defaultValue={alert.event_id ?? ""} id={`alert-event-${alert.id}`} label="Event" name="event_id">
                                <option value="">Unlinked</option>
                                {events.map((event) => (
                                  <option key={event.id} value={event.id}>
                                    {event.title}
                                  </option>
                                ))}
                              </SelectField>
                              <TextField defaultValue={alert.alert_type} id={`alert-type-${alert.id}`} label="Type" name="alert_type" required />
                              <SelectField defaultValue={alert.severity} id={`alert-severity-${alert.id}`} label="Severity" name="severity">
                                {severityOptions()}
                              </SelectField>
                              <TextField className="field field-full" defaultValue={alert.title} id={`alert-title-${alert.id}`} label="Title" name="title" required />
                              <SelectField defaultValue={alert.confidence_bucket} id={`alert-confidence-${alert.id}`} label="Confidence" name="confidence_bucket">
                                {confidenceOptions()}
                              </SelectField>
                              <SelectField defaultValue={alert.review_status} id={`alert-review-${alert.id}`} label="Review" name="review_status">
                                {reviewStatusOptions()}
                              </SelectField>
                              <TextAreaField className="field field-full" defaultValue={alert.summary ?? ""} id={`alert-summary-${alert.id}`} label="Summary" name="summary" />
                              <TextAreaField className="field field-full" defaultValue={alert.why_it_matters ?? ""} id={`alert-why-${alert.id}`} label="Why It Matters" name="why_it_matters" />
                              <TextAreaField className="field field-full" defaultValue={alert.review_notes ?? ""} id={`alert-review-notes-${alert.id}`} label="Review Notes" name="review_notes" />
                              <div className="button-row">
                                <button className="secondary-button" type="submit">Save</button>
                              </div>
                            </form>
                          </details>
                          <DeleteRecordForm action={deleteAlertWithState} recordId={alert.id} />
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
        <PageHeader eyebrow="Review queue" title="Alerts" />
        <ErrorState message="Could not load alerts from the backend API." />
      </>
    );
  }
}
