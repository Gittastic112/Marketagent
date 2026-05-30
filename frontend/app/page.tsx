import Link from "next/link";
import { EmptyState, ErrorState, PageHeader, Panel } from "@/components/page";
import { fetchApi } from "@/lib/api";
import type { AlertRecord, Company, DailyBrief, EventRecord, Portfolio, PortfolioAnalytics, ThesisNote } from "@/lib/api";

async function loadOverview() {
  const [companies, events, alerts, thesisNotes, dailyBrief, portfolios] = await Promise.all([
    fetchApi<Company[]>("/companies"),
    fetchApi<EventRecord[]>("/events"),
    fetchApi<AlertRecord[]>("/alerts"),
    fetchApi<ThesisNote[]>("/thesis-notes"),
    fetchApi<DailyBrief>("/daily-brief"),
    fetchApi<Portfolio[]>("/portfolios")
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

  return { companies, events, alerts, thesisNotes, dailyBrief, analytics };
}

export default async function HomePage() {
  try {
    const { companies, events, alerts, thesisNotes, dailyBrief, analytics } = await loadOverview();
    const companiesById = new Map(companies.map((c) => [c.id, c]));
    
    // Sort alerts by priority (assuming higher priority is better, or just use active count)
    const activeAlerts = alerts.filter(a => a.review_status === "unreviewed" || a.review_status === "needs_follow_up");

    return (
      <>
        <PageHeader eyebrow="Command Center" title="Overview" status={dailyBrief?.date} />
        <section className="metric-grid">
          <Metric 
            label="Total Portfolio Value" 
            value={analytics?.total_portfolio_value ? `$${analytics.total_portfolio_value.toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 2})}` : "—"} 
          />
          <Metric label="Active Alerts" value={activeAlerts.length} />
          <Metric label="Tracked Companies" value={companies.length} />
          <Metric label="Thesis Notes" value={thesisNotes.length} />
        </section>
        
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
