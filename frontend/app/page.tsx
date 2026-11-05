import Link from "next/link";
import { ArrowUpRight, BriefcaseBusiness, Building2, FileText, Bell } from "lucide-react";
import { DataStateNotices, EmptyState, ErrorState, PageHeader, Panel } from "@/components/page";
import { DailyBriefPanel } from "@/components/daily-brief-panel";
import { EventsTimeline } from "@/components/events-timeline";
import { AlertsPanel } from "@/components/alerts-panel";
import { serverFetchApiResponse } from "@/lib/server-api";
import { formatCurrency } from "@/lib/formatting";
import type { DashboardOverview } from "@/lib/api";

export const dynamic = "force-dynamic";

export default async function HomePage() {
  const overviewRes = await serverFetchApiResponse<DashboardOverview>("/dashboard/overview", { timeoutMs: 30_000 });
  const overview = overviewRes.data;
  const heading = <PageHeader eyebrow="Research workspace" title="Overview"
    description="What changed, what needs attention, and where to look next."
    actions={<Link prefetch={false} className="primary-button" href="/daily-brief">Open daily brief <ArrowUpRight size={16} aria-hidden="true" /></Link>} />;
  if (!overview) return <>{heading}<ErrorState message="The dashboard could not be loaded." errors={overviewRes.errors} /></>;

  const { companies, events, alerts, thesis_notes: thesisNotes, daily_brief: dailyBrief,
    default_portfolio: portfolio, default_portfolio_snapshot: snapshot, processing_runs: runs } = overview;
  const companiesById = new Map(companies.map(company => [company.id, company]));
  const activeAlerts = alerts.filter(alert => ["unreviewed", "needs_follow_up"].includes(alert.review_status));
  const recentRuns = runs.slice(0, 5);
  const failedRuns = recentRuns.filter(run => ["failed", "error"].includes(run.status));
  const snapshotNeedsInputs = Boolean(snapshot && snapshot.calculation_status !== "complete");

  return <>
    {heading}
    <DataStateNotices metas={[overviewRes.meta]}
      mockMessage="One or more dashboard panels use Mock Data, not source-backed research." />
    <section className="metric-grid dashboard-metrics" aria-label="Research summary">
      <Link prefetch={false} className="metric metric-featured" href={portfolio ? `/portfolio/${portfolio.id}` : "/portfolio/manage"}>
        <div className="metric-label"><BriefcaseBusiness size={16} aria-hidden="true" />Portfolio value</div>
        <div className="metric-value">{snapshot?.total_portfolio_value == null ? "Not available" : formatCurrency(snapshot.total_portfolio_value, snapshot.base_currency || portfolio?.base_currency || "USD")}</div>
        {portfolio && <div className="metric-detail">{portfolio.name}</div>}
        {snapshotNeedsInputs && snapshot && <div className="metric-detail">
          {snapshot.priced_holdings_count} of {snapshot.holdings_count} holdings priced.
          {snapshot.missing_price_tickers_json.length > 0 && ` Prices needed: ${snapshot.missing_price_tickers_json.join(", ")}.`}
          {snapshot.missing_fx_pairs_json.length > 0 && ` FX rates needed: ${snapshot.missing_fx_pairs_json.join(", ")}.`}
          {" Open portfolio to review missing inputs."}
        </div>}
        <div className="metric-detail">{snapshot ? `Stored snapshot · ${snapshot.snapshot_date}` : portfolio ? "Capture a priced snapshot" : "Set up a portfolio"}<ArrowUpRight size={14} aria-hidden="true" /></div>
      </Link>
      <Link prefetch={false} className="metric" href="/alerts"><div className="metric-label"><Bell size={16} aria-hidden="true" />Alerts to review</div><div className="metric-value">{activeAlerts.length}</div><div className="metric-detail">From the latest loaded alerts<ArrowUpRight size={14} aria-hidden="true" /></div></Link>
      <Link prefetch={false} className="metric" href="/companies"><div className="metric-label"><Building2 size={16} aria-hidden="true" />Tracked companies</div><div className="metric-value">{companies.length}</div><div className="metric-detail">Your research universe<ArrowUpRight size={14} aria-hidden="true" /></div></Link>
      <Link prefetch={false} className="metric" href="/thesis-notes"><div className="metric-label"><FileText size={16} aria-hidden="true" />Thesis notes</div><div className="metric-value">{thesisNotes.length}</div><div className="metric-detail">Saved research context<ArrowUpRight size={14} aria-hidden="true" /></div></Link>
    </section>
    {portfolio?.description && <details className="disclosure basis-disclosure"><summary>Portfolio basis & assumptions</summary><p>{portfolio.description}</p></details>}
    <div className="dashboard-content-grid">
      <div className="content-stack">
        <DailyBriefPanel dailyBrief={dailyBrief} />
        <Panel title="Thesis notebook" actions={<Link prefetch={false} href="/thesis-notes">Write Thesis</Link>}>
          {thesisNotes.length === 0 ? <EmptyState label="No thesis notes yet. Record a thesis and the assumptions that would change it." /> : <div className="table-wrap"><table>
            <thead><tr><th>Thesis</th><th>Company</th><th>Review state</th></tr></thead>
            <tbody>{thesisNotes.map(note => <tr key={note.id}><td><Link href={`/thesis-notes/${note.id}`}>{note.title}</Link></td><td>{companiesById.get(note.company_id)?.ticker || `#${note.company_id}`}</td><td><span className="badge">{note.status}</span></td></tr>)}</tbody>
          </table></div>}
        </Panel>
        <Panel title="Recent source activity" actions={<Link prefetch={false} href="/data-health">Data health →</Link>}>
          {failedRuns.length > 0 && <p className="basis-note">{failedRuns.length} of the last {recentRuns.length} processing runs failed. Open data health for details.</p>}
          {recentRuns.length === 0 ? <EmptyState label="No processing runs yet. Configure sources and run ingestion to collect evidence." /> : <div className="run-list">{recentRuns.map(run => <div className="run-row" key={run.id}>
            <div><strong>{run.run_type.replaceAll("_", " ")}</strong><span className="cell-secondary">{new Date(run.started_at).toLocaleDateString("en-US", { month: "short", day: "numeric" })} · {run.created_count} records created</span></div>
            <span className={`badge ${["failed", "error"].includes(run.status) ? "badge-error" : ""}`}>{run.status.replaceAll("_", " ")}</span>
          </div>)}</div>}
        </Panel>
      </div>
      <div className="content-stack">
        <AlertsPanel alerts={alerts} companiesById={companiesById} />
        <EventsTimeline events={events} />
        <Panel title="Continue research">
          <div className="research-links">
            <Link prefetch={false} href="/companies">Add Company <ArrowUpRight size={16} aria-hidden="true" /></Link>
            <Link prefetch={false} href="/valuation">Valuation workspace <ArrowUpRight size={16} aria-hidden="true" /></Link>
            <Link prefetch={false} href="/documents">Review source documents <ArrowUpRight size={16} aria-hidden="true" /></Link>
          </div>
        </Panel>
      </div>
    </div>
  </>;
}
