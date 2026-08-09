import { saveDailyBrief, markDailyBriefReviewed } from "@/app/actions";
import { EmptyState, ErrorState, PageHeader, Panel } from "@/components/page";
import { DataStateNotices } from "@/components/ui/data-states";
import { BriefingEventCard } from "@/components/briefing-event-card";
import { serverFetchApiResponse } from "@/lib/server-api";
import { PrototypeBadge } from "@/components/ui/data-states";
import type { DailyBrief, SavedDailyBrief } from "@/lib/api";

export default async function DailyBriefPage() {
  try {
    const briefRes = await serverFetchApiResponse<DailyBrief>("/daily-brief");
    const savedBriefsRes = await serverFetchApiResponse<SavedDailyBrief[]>("/daily-brief-history");
    const brief = briefRes.data!;
    const savedBriefs = savedBriefsRes.data || [];
    const newSinceLastReview = brief.payload_json.new_since_last_review;
    const highMaterialityEvents = brief.payload_json.high_materiality_events;
    const thesisContradictions = brief.payload_json.thesis_contradictions;
    const valuationRelevance = brief.payload_json.valuation_relevance;

    return (
      <>
        <PageHeader eyebrow="Daily output" title={brief.title} status={brief.brief_date} />
        <DataStateNotices metas={[briefRes.meta, savedBriefsRes.meta]} />
        <Panel title="Summary">
          <div className="brief-list">
            <div className="brief-item">
              <p>{brief.summary}</p>
              <div className="button-row" style={{ display: 'flex', gap: '8px', marginTop: '16px' }}>
                <form action={saveDailyBrief}>
                  <button type="submit" className="btn btn-secondary">Save brief</button>
                </form>
                {brief.review_status !== "reviewed" && (
                  <form action={markDailyBriefReviewed}>
                    <input type="hidden" name="id" value={brief.id} />
                    <button type="submit" className="btn btn-primary" style={{ backgroundColor: 'var(--success)' }}>Mark as Reviewed</button>
                  </form>
                )}
                {brief.review_status === "reviewed" && (
                    <span className="badge reviewed" style={{ padding: '8px', backgroundColor: 'var(--success-bg)', color: 'var(--success)' }}>✓ Reviewed</span>
                )}
              </div>
            </div>
          </div>
        </Panel>
        <Panel title="Saved Briefs">
          {savedBriefs.length === 0 ? (
            <EmptyState label="No saved briefs yet." />
          ) : (
            <div className="table-wrap">
              <table>
                <thead>
                  <tr>
                    <th>Date</th>
                    <th>Summary</th>
                    <th>Saved</th>
                  </tr>
                </thead>
                <tbody>
                  {savedBriefs.map((savedBrief) => (
                    <tr key={savedBrief.id}>
                      <td>{savedBrief.brief_date}</td>
                      <td>{savedBrief.summary}</td>
                      <td>{new Date(savedBrief.created_at).toLocaleString()}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </Panel>
        <Panel title="New Since Last Review">
          {newSinceLastReview.filings.length === 0 && newSinceLastReview.portfolio_moves.length === 0 ? (
            <EmptyState label="Nothing new since last review." />
          ) : (
              <div className="brief-list">
                {newSinceLastReview.portfolio_moves.length > 0 && (
                  <div style={{ marginBottom: '16px' }}>
                    <h4 style={{ marginBottom: '8px' }}>Portfolio Impact</h4>
                    {newSinceLastReview.portfolio_moves.map((move: any, i: number) => (
                      <article className="brief-item" key={`move-${i}`} style={{ borderLeft: move.move_percent < 0 ? '4px solid var(--danger)' : '4px solid var(--success)'}}>
                        <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                          <h3 style={{ margin: 0 }}>{move.ticker} - {move.event_headline}</h3>
                          <span style={{ fontWeight: 'bold', color: move.move_percent < 0 ? 'var(--danger)' : 'var(--success)' }}>
                              {move.move_percent.toFixed(2)}%
                          </span>
                        </div>
                        <div className="button-row" style={{ marginTop: '12px' }}>
                          <a href={`/events/${move.event_id}`} className="btn btn-secondary" style={{ fontSize: '14px', textDecoration: 'none' }}>View News</a>
                        </div>
                      </article>
                    ))}
                  </div>
                )}
                {newSinceLastReview.filings.length > 0 && (
                  <div>
                    <h4 style={{ marginBottom: '8px' }}>New Filings</h4>
                    {newSinceLastReview.filings.map((filing: any, i: number) => (
                      <BriefingEventCard
                          key={`filing-${i}`}
                          event_id={filing.event_id}
                          headline={filing.headline}
                          ticker={filing.ticker}
                          form_type={filing.form_type}
                          status="New"
                      />
                    ))}
                  </div>
                )}
              </div>
          )}
        </Panel>

        <Panel title="High Materiality Events">
          {highMaterialityEvents.length === 0 ? (
            <EmptyState label="No events in the brief." />
          ) : (
            <div className="brief-list">
              {highMaterialityEvents.map((event: any, i: number) => (
                <BriefingEventCard
                    key={i}
                    event_id={event.event_id}
                    headline={event.headline}
                    priority={event.priority}
                    status="New"
                />
              ))}
            </div>
          )}
        </Panel>

        {thesisContradictions.length > 0 && (
          <Panel title={<div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>Contradiction Alerts <PrototypeBadge /></div>} className="danger-panel">
            <div className="brief-list">
              {thesisContradictions.map((alert: any, i: number) => (
                <article className="brief-item" key={i} style={{ borderLeft: '4px solid var(--danger)', backgroundColor: 'var(--danger-bg)' }}>
                  <h3 style={{ color: 'var(--danger)', marginBottom: '12px' }}>Thesis Contradiction</h3>
                  <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px', marginBottom: '16px' }}>
                    <div style={{ padding: '12px', backgroundColor: 'var(--surface)', borderRadius: '6px' }}>
                      <strong style={{ display: 'block', marginBottom: '8px', color: 'var(--text-muted)' }}>Logged Assumption</strong>
                      <p style={{ margin: 0 }}>{alert.assumption}</p>
                    </div>
                    <div style={{ padding: '12px', backgroundColor: 'var(--surface)', borderRadius: '6px', border: '1px solid var(--danger)' }}>
                      <strong style={{ display: 'block', marginBottom: '8px', color: 'var(--danger)' }}>New Evidence</strong>
                      <p style={{ margin: 0 }}>{alert.evidence}</p>
                    </div>
                  </div>
                  <div className="button-row">
                    <a href={`/alerts/${alert.alert_id}`} className="btn btn-primary" style={{ backgroundColor: 'var(--danger)', color: 'white', textDecoration: 'none' }}>Review Alert</a>
                  </div>
                </article>
              ))}
            </div>
          </Panel>
        )}

        <Panel title={<div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>Valuation Relevance <PrototypeBadge /></div>}>
          {valuationRelevance.length === 0 ? (
            <EmptyState label="No valuation impact." />
          ) : (
            <div className="brief-list">
              {valuationRelevance.map((val: any, i: number) => (
                <article className="brief-item" key={i}>
                  <h3 style={{ marginBottom: '8px' }}>{val.headline}</h3>
                  <div style={{ padding: '12px', backgroundColor: 'var(--surface-sunken)', borderRadius: '6px' }}>
                    <p style={{ margin: '0 0 8px 0' }}>
                      <strong>{val.variable}</strong> may be impacted by this event.
                      <span className="badge" style={{ marginLeft: '8px', backgroundColor: val.direction === 'up' ? 'var(--success-bg)' : 'var(--danger-bg)', color: val.direction === 'up' ? 'var(--success)' : 'var(--danger)' }}>
                        Impact: {val.direction}
                      </span>
                    </p>
                    <p style={{ margin: 0, fontSize: '14px', color: 'var(--text-muted)' }}>{val.reasoning}</p>
                  </div>
                  <div className="button-row" style={{ marginTop: '12px' }}>
                    <a href={`/events/${val.event_id}`} className="btn btn-secondary" style={{ fontSize: '14px', textDecoration: 'none' }}>View Event</a>
                  </div>
                </article>
              ))}
            </div>
          )}
        </Panel>

      </>
    );
  } catch {
    return (
      <>
        <PageHeader eyebrow="Daily output" title="Daily Intelligence Brief" />
        <ErrorState message="Could not load the daily brief from the backend API." />
      </>
    );
  }
}
