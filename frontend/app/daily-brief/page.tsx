import Link from "next/link";

import { generateDailyBrief, markDailyBriefReviewed } from "@/app/actions";
import { BriefingEventCard } from "@/components/briefing-event-card";
import { BriefSourceInbox } from "@/components/brief-source-inbox";
import { BriefPrivateResearch } from "@/components/brief-private-research";
import { DailyBriefScheduleForm } from "@/components/daily-brief-schedule-form";
import { EmptyState, ErrorState, PageHeader, Panel } from "@/components/page";
import { DataStateNotices, MockDataBadge } from "@/components/ui/data-states";
import type { DailyBrief, DailyBriefSchedule, SavedDailyBrief } from "@/lib/api";
import { serverFetchApiResponse } from "@/lib/server-api";


function statusLabel(value: string) {
  return value.replaceAll("_", " ");
}

function statusTone(value: string) {
  if (value === "complete" || value === "reviewed") return "badge-success";
  if (value === "failed" || value === "not_available") return "badge-danger";
  return "badge-outline";
}

export default async function DailyBriefPage() {
  const [briefRes, savedBriefsRes, scheduleRes] = await Promise.all([
    serverFetchApiResponse<DailyBrief>("/daily-brief"),
    serverFetchApiResponse<SavedDailyBrief[]>("/daily-brief-history"),
    serverFetchApiResponse<DailyBriefSchedule | null>("/daily-brief-schedule"),
  ]);
  const brief = briefRes.data;
  if (!brief) {
    return (
      <>
        <PageHeader eyebrow="Daily output" title="Daily Intelligence Brief" />
        <ErrorState message="Daily Brief is unavailable." errors={briefRes.errors} />
        <BriefSourceInbox />
        <Panel title="Runtime recovery">
          <p className="muted">
            Verify the backend container is healthy and apply the current database migrations before retrying.
          </p>
          <Link href="/data-health" className="text-link">Open runtime diagnostics</Link>
        </Panel>
      </>
    );
  }
    const savedBriefs = savedBriefsRes.data || [];
    const payload = brief.payload_json;
    const newSinceLastReview = payload.new_since_last_review;

    return (
      <>
        <PageHeader eyebrow="Daily output" title={brief.title} status={brief.brief_date} />
        <DataStateNotices metas={[briefRes.meta, savedBriefsRes.meta, scheduleRes.meta]} />
        <BriefSourceInbox />

        <Panel title="Briefing State">
          <div className="briefing-summary-grid">
            <div className="briefing-summary-copy">
              <div className="briefing-kicker-row">
                <span className={`badge ${statusTone(payload.calculation_status)}`}>
                  Brief {statusLabel(payload.calculation_status)}
                </span>
                <span className={`badge ${statusTone(payload.valuation_analysis_status)}`}>
                  Valuation analysis {statusLabel(payload.valuation_analysis_status)}
                </span>
                <span className={`badge ${statusTone(payload.contradiction_analysis_status)}`}>
                  Contradiction analysis {statusLabel(payload.contradiction_analysis_status)}
                </span>
                {payload.contains_mock_data && <MockDataBadge />}
              </div>
              <p className="briefing-summary-text">{brief.summary}</p>
              <p className="briefing-context-note">
                {payload.last_reviewed_at
                  ? `Changes are measured after ${new Date(payload.last_reviewed_at).toLocaleString()}.`
                  : "No reviewed brief exists yet, so this includes the latest stored event set."}
              </p>
              {payload.warnings.length > 0 && (
                <div className="briefing-warning-box">
                  <strong>Partial inputs</strong>
                  <ul className="compact-list">
                    {payload.warnings.map((warning) => <li key={warning}>{warning}</li>)}
                  </ul>
                </div>
              )}
            </div>
            <div className="briefing-controls">
              <form action={generateDailyBrief}>
                <button type="submit" className="btn btn-primary">Generate refreshed analysis</button>
              </form>
              {brief.review_status !== "reviewed" ? (
                <form action={markDailyBriefReviewed}>
                  <input type="hidden" name="id" value={brief.id} />
                  <button type="submit" className="btn btn-secondary">Mark brief reviewed</button>
                </form>
              ) : (
                <div className="briefing-review-state">
                  <span className="badge badge-success">Reviewed</span>
                  {brief.reviewed_at && (
                    <span className="muted">Reviewed {new Date(brief.reviewed_at).toLocaleString()}</span>
                  )}
                </div>
              )}
              <p>
                Refreshing explicitly runs configured AI checks. Outputs remain AI Interpretation until reviewed.
              </p>
              <Link href="/data-health" className="text-link">Inspect processing health</Link>
            </div>
          </div>
        </Panel>

        <Panel title="Local Brief Schedule">
          {scheduleRes.errors.length > 0 ? (
            <ErrorState message="The optional local schedule is unavailable." errors={scheduleRes.errors} />
          ) : (
            <DailyBriefScheduleForm schedule={scheduleRes.data} />
          )}
        </Panel>

        <BriefPrivateResearch context={payload.private_research} />

        <Panel title="Inspection Queue">
          {payload.inspection_queue.length === 0 ? (
            <EmptyState label="No blocking inspection actions were derived from the current brief." />
          ) : (
            <div className="brief-list">
              {payload.inspection_queue.map((action) => (
                <article className="brief-item" key={action.action_id}>
                  <div className="briefing-card-heading">
                    <div>
                      <span className="eyebrow">Next inspection</span>
                      <h3>{action.title}</h3>
                    </div>
                    <span className={`badge ${action.priority === "high" ? "badge-danger" : "badge-outline"}`}>
                      {action.priority} priority
                    </span>
                  </div>
                  <p>{action.reason}</p>
                  <div className="briefing-meta-row">
                    <span>{action.claim_type}</span>
                    {action.processing_run_id && <span>Run #{action.processing_run_id}</span>}
                    {action.source_event_ids.map((id) => <span key={`event-${id}`}>Event #{id}</span>)}
                    {action.source_raw_document_ids.map((id) => <span key={`document-${id}`}>Document #{id}</span>)}
                    {action.source_alert_ids.map((id) => <span key={`alert-${id}`}>Alert #{id}</span>)}
                    {action.source_market_price_ids.map((id) => <span key={`price-${id}`}>Price #{id}</span>)}
                  </div>
                  <div className="button-row briefing-actions">
                    <Link href={action.href} className="btn btn-primary">Inspect now</Link>
                  </div>
                </article>
              ))}
            </div>
          )}
        </Panel>

        <Panel title="Processing Failures">
          {payload.processing_failures.length === 0 ? (
            <EmptyState label="No failed or partial processing runs were recorded since the last review." />
          ) : (
            <div className="brief-list">
              {payload.processing_failures.map((run) => (
                <article className="brief-item" key={run.processing_run_id}>
                  <div className="briefing-card-heading">
                    <div>
                      <span className="eyebrow">{run.source_type || "internal"}</span>
                      <h3>{statusLabel(run.run_type)}</h3>
                    </div>
                    <span className="badge badge-danger">{statusLabel(run.status)}</span>
                  </div>
                  <div className="briefing-meta-row">
                    <span>{run.claim_type}</span>
                    <span>Run #{run.processing_run_id}</span>
                    <span>{run.error_count} recorded error{run.error_count === 1 ? "" : "s"}</span>
                    <span>Started {new Date(run.started_at).toLocaleString()}</span>
                  </div>
                  <div className="button-row briefing-actions">
                    <Link href="/data-health" className="btn btn-secondary">Inspect processing health</Link>
                  </div>
                </article>
              ))}
            </div>
          )}
        </Panel>

        <Panel title="New Since Last Review">
          {newSinceLastReview.filings.length === 0 && newSinceLastReview.portfolio_moves.length === 0 ? (
            <EmptyState label="No new filings or held-company events were found." />
          ) : (
            <div className="brief-list">
              {newSinceLastReview.portfolio_moves.length > 0 && (
                <section className="briefing-section">
                  <div className="briefing-section-heading">
                    <div>
                      <span className="eyebrow">Portfolio impact</span>
                      <h3>Affected held companies</h3>
                    </div>
                    <span className="badge badge-outline">Calculation</span>
                  </div>
                  <div className="briefing-card-grid">
                    {newSinceLastReview.portfolio_moves.map((move) => (
                      <article className="brief-item" key={`move-${move.event_id}`}>
                        <div className="briefing-card-heading">
                          <div>
                            <span className="eyebrow">{move.ticker}</span>
                            <h3>{move.event_headline}</h3>
                          </div>
                          {move.move_percent == null ? (
                            <span className="badge badge-danger">Move unavailable</span>
                          ) : (
                            <span className={move.move_percent < 0 ? "briefing-move-negative" : "briefing-move-positive"}>
                              {move.move_percent > 0 ? "+" : ""}{move.move_percent.toFixed(2)}%
                            </span>
                          )}
                        </div>
                        <div className="briefing-meta-row">
                          <span>{move.claim_type}</span>
                          <span>Status: {statusLabel(move.calculation_status)}</span>
                          {move.price_start_date && move.price_end_date && (
                            <span>{move.price_start_date} to {move.price_end_date}</span>
                          )}
                          {move.price_provider && <span>Price source: {move.price_provider}</span>}
                        </div>
                        <div className="briefing-portfolio-links">
                          {move.affected_portfolios.map((portfolio) => (
                            <Link key={portfolio.portfolio_id} href={`/portfolio/${portfolio.portfolio_id}`}>
                              {portfolio.portfolio_name}
                            </Link>
                          ))}
                        </div>
                        {move.warnings.length > 0 && (
                          <ul className="compact-list">
                            {move.warnings.map((warning) => <li key={warning}>{warning}</li>)}
                          </ul>
                        )}
                        <div className="button-row briefing-actions">
                          <Link href={`/events/${move.event_id}/evidence-resolution`} className="btn btn-secondary">
                            Review event evidence
                          </Link>
                        </div>
                      </article>
                    ))}
                  </div>
                </section>
              )}

              {newSinceLastReview.filings.length > 0 && (
                <section className="briefing-section">
                  <div className="briefing-section-heading">
                    <div>
                      <span className="eyebrow">New evidence</span>
                      <h3>Filings</h3>
                    </div>
                  </div>
                  {newSinceLastReview.filings.map((filing) => (
                    <BriefingEventCard
                      key={`filing-${filing.event_id}`}
                      event_id={filing.event_id}
                      headline={filing.headline}
                      ticker={filing.ticker}
                      form_type={filing.form_type}
                      status={filing.status}
                      raw_document_id={filing.raw_document_id}
                      source_name={filing.source_name}
                      source_published_at={filing.source_published_at}
                      claim_type={filing.claim_type}
                      evidence_status={filing.evidence_status}
                    />
                  ))}
                </section>
              )}
            </div>
          )}
        </Panel>

        <Panel title="High Materiality Events">
          {payload.high_materiality_events.length === 0 ? (
            <EmptyState label="No events crossed the materiality threshold." />
          ) : (
            <div className="brief-list">
              {payload.high_materiality_events.map((event) => (
                <BriefingEventCard
                  key={event.event_id}
                  event_id={event.event_id}
                  headline={event.headline}
                  priority={`${event.priority}${event.priority_score == null ? "" : ` · ${event.priority_score}`}`}
                  ticker={event.ticker}
                  form_type={event.event_type}
                  status={event.status}
                  raw_document_id={event.raw_document_id}
                  source_name={event.source_name}
                  source_published_at={event.source_published_at}
                  claim_type={event.claim_type}
                  evidence_status={event.evidence_status}
                />
              ))}
            </div>
          )}
        </Panel>

        <Panel title="Contradiction Alerts" className={payload.thesis_contradictions.length > 0 ? "danger-panel" : undefined}>
          {payload.thesis_contradictions.length === 0 ? (
            <EmptyState
              label={payload.contradiction_analysis_status === "not_run"
                ? "AI contradiction analysis has not run. Generate a refreshed analysis to run it explicitly."
                : "No unresolved contradiction alerts were found."}
            />
          ) : (
            <div className="brief-list">
              {payload.thesis_contradictions.map((alert) => (
                <article className="brief-item briefing-contradiction" key={alert.alert_id}>
                  <div className="briefing-kicker-row">
                    <span className="badge badge-danger">Unresolved</span>
                    <span className="badge badge-outline">{alert.claim_type}</span>
                  </div>
                  <div className="brief-comparison-grid">
                    <div className="briefing-comparison-cell">
                      <strong>Logged assumption</strong>
                      <p>{alert.assumption}</p>
                    </div>
                    <div className="briefing-comparison-cell briefing-comparison-danger">
                      <strong>New evidence</strong>
                      <p>{alert.evidence || "Evidence text is unavailable. Open the alert before drawing a conclusion."}</p>
                    </div>
                  </div>
                  <div className="button-row briefing-actions">
                    <Link href={`/alerts/${alert.alert_id}`} className="btn btn-primary">Review alert</Link>
                    {alert.event_id && (
                      <Link href={`/events/${alert.event_id}/evidence-resolution`} className="btn btn-secondary">
                        Review event evidence
                      </Link>
                    )}
                  </div>
                </article>
              ))}
            </div>
          )}
        </Panel>

        <Panel title="Valuation Relevance">
          {payload.valuation_relevance.length === 0 ? (
            <EmptyState
              label={payload.valuation_analysis_status === "not_run"
                ? "AI valuation mapping has not run. Generate a refreshed analysis to run it explicitly."
                : payload.valuation_analysis_status === "failed"
                  ? "Valuation mapping failed. No DCF impact was inferred."
                  : "No valuation-variable impact was identified."}
            />
          ) : (
            <div className="briefing-card-grid panel-content">
              {payload.valuation_relevance.map((item) => (
                <article className="brief-item" key={`${item.event_id}-${item.ai_output_id}-${item.variable}`}>
                  <div className="briefing-kicker-row">
                    <span className="badge badge-outline">{item.claim_type}</span>
                    <span className="badge badge-outline">Review: {item.review_status}</span>
                  </div>
                  <h3>{item.headline}</h3>
                  <p>
                    <strong>{item.variable || "Unspecified DCF variable"}</strong>
                    {item.direction ? ` · ${item.direction}` : ""}
                    {item.confidence ? ` · ${item.confidence} confidence` : ""}
                  </p>
                  <p>{item.reasoning || "No reasoning was returned."}</p>
                  <div className="briefing-meta-row">
                    {item.model_name && <span>Model: {item.model_name}</span>}
                    {item.prompt_version && <span>Prompt: {item.prompt_version}</span>}
                    {item.ai_output_id && <span>AI output #{item.ai_output_id}</span>}
                  </div>
                  <div className="button-row briefing-actions">
                    <Link href={`/events/${item.event_id}/evidence-resolution`} className="btn btn-secondary">
                      Review source evidence
                    </Link>
                  </div>
                </article>
              ))}
            </div>
          )}
        </Panel>

        <Panel title="Source Coverage">
          <div className="briefing-source-grid panel-content">
            <div><span>Events</span><strong>{payload.source_event_ids.length}</strong></div>
            <div><span>Documents</span><strong>{payload.source_raw_document_ids.length}</strong></div>
            <div><span>Price records</span><strong>{payload.source_market_price_ids.length}</strong></div>
            <div><span>Alerts</span><strong>{payload.source_alert_ids.length}</strong></div>
          </div>
        </Panel>

        <Panel title="Saved Briefs">
          {savedBriefs.length === 0 ? (
            <EmptyState label="No saved briefs yet." />
          ) : (
            <div tabIndex={0} className="table-wrap">
              <table>
                <thead>
                  <tr><th>Date</th><th>Summary</th><th>Status</th><th>Saved</th></tr>
                </thead>
                <tbody>
                  {savedBriefs.map((savedBrief) => (
                    <tr key={savedBrief.id}>
                      <td>{savedBrief.brief_date}</td>
                      <td>{savedBrief.summary}</td>
                      <td><span className={`badge ${statusTone(savedBrief.review_status)}`}>{savedBrief.review_status}</span></td>
                      <td>{new Date(savedBrief.created_at).toLocaleString()}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </Panel>
      </>
    );
}
