import Link from "next/link";
import { ErrorState } from "@/components/page";
import type { ReviewQueue } from "@/lib/api/review-queue";

const states = { needs_review: "Needs review", waiting_for_source: "Source attempts to inspect", in_progress: "In progress", new_source: "Recently stored sources" };

export function ResearchReviewQueue({ report, error, selectedState = "", portfolioId, compact = false }: {
  report: ReviewQueue | null; error?: string; selectedState?: string; portfolioId?: number; compact?: boolean;
}) {
  const url = (state: string) => "/?" + new URLSearchParams({ ...(state ? { review_state: state } : {}),
    ...(portfolioId ? { portfolio_id: String(portfolioId) } : {}) });
  return <section className="panel panel-content review-queue" aria-label={compact ? "Research for these holdings" : "Research review queue"}>
    <h2 className="text-lg font-semibold">{compact ? "Research for these holdings" : "Continue your research"}</h2>
    {!report ? <ErrorState message={error || "Review items could not be loaded. Reload to retry."} /> : <>
      <p>{report.basis}. Source updates do not change saved valuations.</p>
      {!compact && <nav className="review-queue-filters" aria-label="Review state">
        <Link href={url("")} aria-current={!selectedState ? "page" : undefined}>All</Link>
        {Object.entries(states).map(([state, label]) => <Link key={state} href={url(state)} aria-current={selectedState === state ? "page" : undefined}>
          {label} ({report.counts[state] ?? 0})</Link>)}
      </nav>}
      <p>{report.returned} of {report.total} matching records shown · checked {new Date(report.captured_at).toLocaleString()}
        {report.truncated ? " · Limited to newest items; use the company workspace for full history." : ""}</p>
      {report.items.length === 0 ? <p>No matching items in the covered workflows. This does not establish complete financial coverage.</p> :
        <ul className="review-queue-list">{report.items.map(item => <li key={item.identity}>
          <div><span className="badge">{states[item.state as keyof typeof states] ?? item.state}</span>{" "}
            {item.company_id && <Link href={`/companies/${item.company_id}`}>{item.ticker || `Company ${item.company_id}`}</Link>}
            <h3>{item.title}</h3><p>{item.reason}</p>
            <small>{new Date(item.relevant_at).toLocaleString()} · {item.permission_scope === "owned" ? "Your research" : "Shared source record"}</small>
          </div><Link className="secondary-button" href={item.href}>{item.action}</Link>
        </li>)}</ul>}
      <details><summary>Coverage and ordering</summary><ul>{report.limitations.map(limit => <li key={limit}>{limit}</li>)}</ul><p>Newest records first. This is a workflow list, not an investment ranking.</p></details>
    </>}
  </section>;
}
