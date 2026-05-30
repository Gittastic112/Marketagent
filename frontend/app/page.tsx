import Link from "next/link";
import { EmptyState, ErrorState, PageHeader, Panel } from "@/components/page";
import { DailyBriefPanel } from "@/components/daily-brief-panel";
import { EventsTimeline } from "@/components/events-timeline";
import { AlertsPanel } from "@/components/alerts-panel";
import { fetchApi } from "@/lib/api";
import type { AlertRecord, Company, DailyBrief, EventRecord, Portfolio, PortfolioAnalytics, ProcessingRun, ThesisNote } from "@/lib/api";

export const dynamic = "force-dynamic";

async function loadOverview() {
  const [companies, events, alerts, thesisNotes, dailyBrief, portfolios, processingRuns] = await Promise.all([
    fetchApi<Company[]>("/companies"),
    fetchApi<EventRecord[]>("/events"),
    fetchApi<AlertRecord[]>("/alerts"),
    fetchApi<ThesisNote[]>("/thesis-notes"),
    fetchApi<DailyBrief>("/daily-brief"),
    fetchApi<Portfolio[]>("/portfolios"),
    fetchApi<ProcessingRun[]>("/processing-runs").catch(() => [])
  ]);

  let analytics = null;
  if (portfolios && portfolios.length > 0) {
    const defaultPortfolio = portfolios[0];
    try {
      analytics = await fetchApi<PortfolioAnalytics>(`/portfolios/${defaultPortfolio.id}/analytics`);
    } catch {
      // Ignored if analytics fail
    }
  }

  return { companies, events, alerts, thesisNotes, dailyBrief, analytics, processingRuns };
}

export default async function HomePage() {
  try {
    const { companies, events, alerts, thesisNotes, dailyBrief, analytics, processingRuns } = await loadOverview();
    const companiesById = new Map(companies.map((c) => [c.id, c]));
    
    // Sort alerts by priority (assuming higher priority is better, or just use active count)
    const activeAlerts = alerts.filter(a => a.review_status === "unreviewed" || a.review_status === "needs_follow_up");

    return (
      <>
        <PageHeader eyebrow="Command Center" title="Overview" status={dailyBrief?.date} />
        
        <section className="metric-grid" style={{ marginBottom: "2rem" }}>
          <Metric 
            label="Total Portfolio Value" 
            value={analytics?.total_portfolio_value ? `$${analytics.total_portfolio_value.toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 2})}` : "—"} 
          />
          <Metric label="Active Alerts" value={activeAlerts.length} />
          <Metric label="Tracked Companies" value={companies.length} />
          <Metric label="Thesis Notes" value={thesisNotes.length} />
        </section>

        {/* Ingestion Health Summary */}
        {processingRuns.length > 0 && (() => {
          const recentRuns = processingRuns.slice(0, 5);
          const failedRecent = recentRuns.filter(r => r.status === "failed" || r.status === "error");
          return (
            <Panel title="Ingestion Health">
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "0.75rem" }}>
                <span style={{ fontSize: "0.85rem", color: "var(--text-secondary)" }}>Last {recentRuns.length} runs</span>
                <Link href="/data-health" style={{ fontSize: "0.85rem" }}>View All →</Link>
              </div>
              {failedRecent.length > 0 && (
                <div style={{ padding: "0.5rem 0.75rem", borderRadius: "6px", backgroundColor: "var(--error-bg, #fef2f2)", border: "1px solid var(--error, #ef4444)30", marginBottom: "0.75rem", fontSize: "0.85rem", color: "var(--error)" }}>
                  ⚠ {failedRecent.length} of the last {recentRuns.length} ingestion runs failed
                </div>
              )}
              <div style={{ display: "flex", gap: "0.5rem", flexWrap: "wrap" }}>
                {recentRuns.map(run => (
                  <div key={run.id} style={{ padding: "0.25rem 0.5rem", borderRadius: "4px", fontSize: "0.75rem", backgroundColor: run.status === "success" || run.status === "completed" ? "#dcfce720" : run.status === "failed" || run.status === "error" ? "#fef2f220" : "var(--bg-secondary)", border: `1px solid ${run.status === "success" || run.status === "completed" ? "var(--success)" : run.status === "failed" || run.status === "error" ? "var(--error)" : "var(--border-color)"}30` }}>
                    <strong>{run.run_type}</strong> · {run.status} · {run.created_count} created
                  </div>
                ))}
              </div>
            </Panel>
          );
        })()}

        {/* Concentration Warnings */}
        {analytics && analytics.top_positions && analytics.top_positions.length > 0 && (() => {
          const concentrated = analytics.top_positions.filter(p => (p.weight_percent ?? 0) > 25);
          if (concentrated.length === 0) return null;
          return (
            <div style={{ padding: "0.75rem 1rem", borderRadius: "8px", backgroundColor: "#fef9c320", border: "1px solid var(--warning, #f59e0b)40", marginBottom: "1.5rem", fontSize: "0.85rem" }}>
              <strong>⚠ Concentration Warning:</strong>{" "}
              {concentrated.map(p => `${p.ticker} (${p.weight_percent?.toFixed(1)}%)`).join(", ")} — positions exceed 25% portfolio weight.
            </div>
          );
        })()}
        
        <div style={{ display: "grid", gridTemplateColumns: "1fr 350px", gap: "2rem", alignItems: "start" }}>
          
          {/* Main Content Column */}
          <div style={{ display: "flex", flexDirection: "column", gap: "2rem" }}>
            <DailyBriefPanel dailyBrief={dailyBrief} />

            {analytics && analytics.top_positions && analytics.top_positions.length > 0 && (
              <Panel title="Top Exposures">
                <div className="table-wrap">
                  <table>
                    <thead>
                      <tr>
                        <th>Ticker</th>
                        <th>Market Value</th>
                        <th>Unrealized P&L</th>
                        <th>Weight</th>
                      </tr>
                    </thead>
                    <tbody>
                      {analytics.top_positions.slice(0, 5).map((pos) => (
                        <tr key={pos.holding_id}>
                          <td style={{ fontWeight: 600 }}>{pos.ticker}</td>
                          <td>${pos.market_value?.toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 2}) ?? "—"}</td>
                          <td style={{ color: (pos.unrealized_pnl ?? 0) >= 0 ? "var(--success)" : "var(--error)" }}>
                            {pos.unrealized_pnl ? `$${pos.unrealized_pnl.toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 2})}` : "—"}
                          </td>
                          <td>{pos.weight_percent ? `${pos.weight_percent.toFixed(1)}%` : "—"}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </Panel>
            )}

            <Panel title="Active Thesis Notes">
              {thesisNotes.length === 0 ? (
                <EmptyState label="No thesis notes yet." />
              ) : (
                <div className="table-wrap">
                  <table>
                    <thead>
                      <tr>
                        <th>Title</th>
                        <th>Company</th>
                        <th>Status</th>
                        <th>Drift</th>
                      </tr>
                    </thead>
                    <tbody>
                      {thesisNotes.map((note) => {
                        const ticker = companiesById.get(note.company_id)?.ticker ?? `#${note.company_id}`;
                        const driftScore = (note as any).thesis_drift_score ?? 0.0;
                        const driftBadge = driftScore > 0.5 ? "badge badge-warn" : "badge";
                        return (
                          <tr key={note.id}>
                            <td>
                              <Link href={`/thesis-notes/${note.id}`} style={{ color: "var(--accent)", fontWeight: 600 }}>
                                {note.title}
                              </Link>
                            </td>
                            <td>{ticker}</td>
                            <td>
                              <span className="badge">{note.status}</span>
                            </td>
                            <td>
                              <span className={driftBadge}>{driftScore.toFixed(2)}</span>
                            </td>
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                </div>
              )}
            </Panel>
          </div>

          {/* Sidebar Column */}
          <div style={{ display: "flex", flexDirection: "column", gap: "2rem" }}>
            <AlertsPanel alerts={alerts} companiesById={companiesById} />
            <EventsTimeline events={events} />
          </div>

        </div>
      </>
    );
  } catch (error) {
    return (
      <>
        <PageHeader eyebrow="Command Center" title="Overview" />
        <ErrorState message="The frontend could not reach the backend API." />
      </>
    );
  }
}

function Metric({ label, value }: { label: string; value: string | number }) {
  return (
    <div className="metric">
      <div className="metric-label">{label}</div>
      <div className="metric-value" style={{ fontSize: typeof value === 'string' && value.startsWith('$') ? '1.5rem' : undefined }}>{value}</div>
    </div>
  );
}
