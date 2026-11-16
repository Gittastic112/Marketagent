import Link from "next/link";
import { ArrowUpRight, BriefcaseBusiness, Building2, FileText, Bell } from "lucide-react";
import { DataStateNotices, EmptyState, ErrorState, PageHeader, Panel } from "@/components/page";
import { DailyBriefPanel } from "@/components/daily-brief-panel";
import { EventsTimeline } from "@/components/events-timeline";
import { AlertsPanel } from "@/components/alerts-panel";
import { serverFetchApiResponse } from "@/lib/server-api";
import { formatCurrency } from "@/lib/formatting";
import type { DashboardOverview } from "@/lib/api";
import type { ReviewQueue } from "@/lib/api/review-queue";
import { ResearchReviewQueue } from "@/components/review-queue";

export const dynamic = "force-dynamic";

export default async function HomePage({ searchParams }: { searchParams: Promise<{ portfolio_id?: string; review_state?: string }> }) {
  const { portfolio_id: selectedId, review_state: reviewState } = await searchParams;
  const selectedReview = reviewState === undefined ? "needs_review" : reviewState === "all" ? "" : reviewState;
  const query = selectedId === undefined ? "" : `?portfolio_id=${encodeURIComponent(selectedId)}`;
  const reviewQuery = new URLSearchParams({ limit: "6", ...(selectedId ? { portfolio_id: selectedId } : {}), ...(selectedReview ? { state: selectedReview } : {}) });
  const [overviewRes, reviewRes] = await Promise.all([
    serverFetchApiResponse<DashboardOverview>(`/dashboard/overview${query}`, { timeoutMs: 30_000 }),
    serverFetchApiResponse<ReviewQueue>(`/review-queue?${reviewQuery}`),
  ]);
  const queue = <ResearchReviewQueue report={reviewRes.data} error={reviewRes.errors[0]?.message} selectedState={selectedReview} portfolioId={selectedId ? Number(selectedId) : undefined} />;
  const overview = overviewRes.data;
  const heading = <PageHeader eyebrow="Research workspace" title="Today"
    description="Review the evidence. Pick up where you left off."
    actions={<><Link prefetch={false} className="secondary-button" href="/alerts">Review alerts</Link><Link prefetch={false} className="primary-button" href="/daily-brief">Open daily brief <ArrowUpRight size={16} aria-hidden="true" /></Link></>} />;
  if (!overview) return <>{heading}{queue}<ErrorState message="The dashboard could not be loaded." errors={overviewRes.errors} /></>;

  const { companies, events, alerts, thesis_notes: thesisNotes, daily_brief: dailyBrief,
    default_portfolio: portfolio, default_portfolio_snapshot: snapshot, processing_runs: runs } = overview;
  const companiesById = new Map(companies.map(company => [company.id, company]));
  const activeAlerts = alerts.filter(alert => ["unreviewed", "needs_follow_up"].includes(alert.review_status));
  const recentRuns = runs.slice(0, 5);
  const failedRuns = recentRuns.filter(run => ["failed", "error"].includes(run.status));
  const snapshotNeedsInputs = Boolean(snapshot && snapshot.calculation_status !== "complete");
  const recentNotes = [...thesisNotes].sort((a, b) => b.updated_at.localeCompare(a.updated_at) || b.id - a.id).slice(0, 4);

  return <div className="today-workspace">
    {heading}
    <DataStateNotices metas={[overviewRes.meta]}
      mockMessage="One or more dashboard panels use Mock Data, not source-backed research." />
    <div className="today-context">
    {overview.portfolios.length > 1 && <form action="/" className="dashboard-portfolio-picker">
      <input type="hidden" name="review_state" value={selectedReview || "all"} />
      <label htmlFor="dashboard-portfolio">Portfolio</label>
      <select id="dashboard-portfolio" name="portfolio_id" defaultValue={portfolio?.id}>
        {overview.portfolios.map(item => <option key={item.id} value={item.id}>{item.name}</option>)}
      </select>
      <button className="secondary-button" type="submit">Show portfolio</button>
      <Link href="/portfolio">View all portfolios</Link>
    </form>}
    </div>
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
    <div className="today-research-grid">
      <div className="content-stack today-primary">
        {queue}
        <Panel title="Thesis notebook" actions={<Link prefetch={false} href="/thesis-notes">Write Thesis</Link>}>
          {recentNotes.length === 0 ? <EmptyState label="No thesis notes yet. Record a thesis and the assumptions that would change it." /> : <>
            <ul className="today-notes">{recentNotes.map(note => <li key={note.id}>
              <span className="today-ticker">{companiesById.get(note.company_id)?.ticker || `#${note.company_id}`}</span>
              <Link href={`/thesis-notes/${note.id}`}>{note.title}</Link><span className="badge">{note.status}</span>
            </li>)}</ul>
            <Link className="today-text-link" href="/thesis-notes">View all {thesisNotes.length} notes <ArrowUpRight size={14} aria-hidden="true" /></Link>
          </>}
        </Panel>
      </div>
      <aside className="content-stack today-secondary" aria-label="Research context">
        <DailyBriefPanel dailyBrief={dailyBrief} />
        <Panel title="Your companies" actions={<Link prefetch={false} href="/companies">Add Company</Link>}>
          {companies.length === 0 ? <EmptyState label="Add a company to start collecting research." /> : <div className="today-company-links">{companies.map(company =>
            <Link prefetch={false} key={company.id} href={`/companies/${company.id}`}>{company.ticker}<ArrowUpRight size={13} aria-hidden="true" /></Link>)}</div>}
          <Link className="today-text-link" href="/valuation">Open valuation workspace <ArrowUpRight size={14} aria-hidden="true" /></Link>
        </Panel>
        <details className="disclosure today-source-activity"><summary>Source activity <span className={failedRuns.length ? "badge badge-error" : "muted"}>{failedRuns.length ? `${failedRuns.length} failed` : `${recentRuns.length} recent runs`}</span></summary>
        <Panel title="Recent source activity" actions={<Link prefetch={false} href="/data-health">Data health →</Link>}>
          {failedRuns.length > 0 && <p className="basis-note">{failedRuns.length} of the last {recentRuns.length} processing runs failed. Open data health for details.</p>}
          {recentRuns.length === 0 ? <EmptyState label="No processing runs yet. Configure sources and run ingestion to collect evidence." /> : <div className="run-list">{recentRuns.map(run => <div className="run-row" key={run.id}>
            <div><strong>{run.run_type.replaceAll("_", " ")}</strong><span className="cell-secondary">{new Date(run.started_at).toLocaleDateString("en-US", { month: "short", day: "numeric" })} · {run.created_count} record{run.created_count === 1 ? "" : "s"} created</span></div>
            <span className={`badge ${["failed", "error"].includes(run.status) ? "badge-error" : ""}`}>{run.status.replaceAll("_", " ")}</span>
          </div>)}</div>}
        </Panel>
        </details>
      </aside>
    </div>
    <details className="disclosure today-more-activity"><summary>Alerts and event detail <span className="muted">{activeAlerts.length} alerts to review · {events.length} loaded events</span></summary>
      <div className="dashboard-content-grid">
        <AlertsPanel alerts={alerts} companiesById={companiesById} />
        <EventsTimeline events={events} companies={companies} />
      </div>
    </details>
  </div>;
}
