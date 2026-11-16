import Link from "next/link";
import { ArrowUpRight } from "lucide-react";
import { ErrorState } from "@/components/page";
import type { ReviewQueue } from "@/lib/api/review-queue";

const states = { needs_review: "Needs review", waiting_for_source: "Source attempts to inspect", in_progress: "In progress", new_source: "Recently stored sources" };
const filterLabels = { needs_review: "Needs review", waiting_for_source: "Source attempts", in_progress: "In progress", new_source: "New sources" };

export function ResearchReviewQueue({ report, error, selectedState = "", portfolioId, compact = false }: {
  report: ReviewQueue | null; error?: string; selectedState?: string; portfolioId?: number; compact?: boolean;
}) {
  const url = (state: string) => "/?" + new URLSearchParams({ review_state: state || "all",
    ...(portfolioId ? { portfolio_id: String(portfolioId) } : {}) });
  return <section className="panel panel-content review-queue" aria-label={compact ? "Research for these holdings" : "Research review queue"}>
    <div className="review-queue-heading"><div><span className="eyebrow">Your next steps</span>
      <h2>{compact ? "Research for these holdings" : "Continue your research"}</h2></div>
      {!compact && <Link href="/documents" className="today-text-link">Sources <ArrowUpRight size={14} aria-hidden="true" /></Link>}
    </div>
    {!report ? <ErrorState message={error || "Review items could not be loaded. Reload to retry."} /> : <>
      <p className="review-queue-intro">Source updates do not change saved valuations.</p>
      {!compact && <nav className="review-queue-filters" aria-label="Review state">
        <Link href={url("")} aria-current={!selectedState ? "page" : undefined}>All</Link>
        {Object.entries(filterLabels).map(([state, label]) => <Link key={state} href={url(state)} aria-current={selectedState === state ? "page" : undefined}>
          {label} <span>{report.counts[state] ?? 0}</span></Link>)}
      </nav>}
      <p className="review-queue-count">Showing {report.returned} of {report.total} matching records{report.truncated ? " · newest first" : ""}</p>
      {report.items.length === 0 ? <p>No matching items in the covered workflows. This does not establish complete financial coverage.</p> :
        <ul className="review-queue-list">{report.items.map(item => <li key={item.identity}>
          <div><div className="review-queue-row-meta">
            {item.company_id && <Link className="today-ticker" href={`/companies/${item.company_id}`}>{item.ticker || `Company ${item.company_id}`}</Link>}
            <span>{states[item.state as keyof typeof states] ?? item.state}</span></div>
            <h3>{item.title}</h3><p>{item.reason}</p>
            <small><time dateTime={item.relevant_at}>{new Date(item.relevant_at).toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" })}</time> · {item.permission_scope === "owned" ? "Your research" : "Shared source record"}</small>
          </div><Link className="review-queue-action" href={item.href}>{item.action}<ArrowUpRight size={14} aria-hidden="true" /></Link>
        </li>)}</ul>}
      <details className="review-queue-coverage"><summary>Coverage and ordering</summary><p>{report.basis}. Checked {new Date(report.captured_at).toLocaleString()}.</p><ul>{report.limitations.map(limit => <li key={limit}>{limit}</li>)}</ul><p>Newest records first. This is a workflow list, not an investment ranking. Open a company workspace for its full history.</p></details>
    </>}
  </section>;
}
