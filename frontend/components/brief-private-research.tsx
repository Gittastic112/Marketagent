import Link from "next/link";
import { EmptyState, Panel } from "@/components/page";
import type { SavedBriefResearchContext, BriefResearchDecision } from "@/lib/api/brief-context";

function Decision({ item }: { item: BriefResearchDecision }) {
  return <article className="brief-item">
    <h4>{item.ticker} · {item.field.replaceAll("_", " ")}</h4>
    <p>{item.state.replaceAll("_", " ")} · Comparison basis: {item.comparability_status}</p>
    {item.receipt && <>
      <p>User Assumption · {item.receipt.disposition.replaceAll("_", " ")} · v{item.receipt.version} · {item.receipt.created_at.slice(0, 10)}</p>
      <p>{item.receipt.notes}</p>
      <Link prefetch={false} href={`/daily-brief/triage/reviews/${item.receipt.id}`}>Open analyst receipt #{item.receipt.id}</Link>
    </>}
    <div className="button-row"><Link prefetch={false} href={item.href}>Review current comparison</Link>
      {item.source_ids.map(id => <Link key={id} prefetch={false} href={`/daily-brief/sources/${id}`}>Source #{id}</Link>)}
    </div>
  </article>;
}

export function BriefPrivateResearch({ context }: { context?: SavedBriefResearchContext | null }) {
  if (context?.version === 1) return <Panel title="Private research as generated">
    <p className="basis-note">This brief contains a legacy private research snapshot (version 1). Its original data is preserved, but this format is not supported by the current review view. No current reviewed or pending status is inferred.</p>
  </Panel>;
  return <Panel title="Private research as generated">
    {!context ? <EmptyState label="This older brief has no private research snapshot. Its saved evidence has not been rewritten." /> : <>
      <p className="basis-note">Saved as generated {context.captured_at}. Sources and receipts may have changed since this snapshot. {context.status.replaceAll("_", " ")} coverage.</p>
      {context.limitations.map(note => <p className="basis-note" key={note}>{note}</p>)}
      <h3>Reviewed analyst context</h3>
      {context.reviewed.length ? <div className="briefing-card-grid">{context.reviewed.map(item => <Decision key={`${item.company_id}:${item.field}`} item={item} />)}</div> : <EmptyState label="No current analyst receipts with approved source interpretations were included." />}
      <h3>Private research review queue</h3>
      {context.review_queue.length ? <div className="briefing-card-grid">{context.review_queue.map(item => <Decision key={`${item.company_id}:${item.field}`} item={item} />)}</div> : <EmptyState label="No eligible pending private-source comparisons in this snapshot." />}
      <details><summary>Source evidence and coverage ({context.sources.length} sources)</summary>
        {context.sources.map(({ source, freshness }) => <article className="brief-item" key={source.id}>
          <h4><Link prefetch={false} href={`/daily-brief/sources/${source.id}`}>{source.title}</Link></h4>
          <p>AI Interpretation · {source.review_status} at capture · {freshness} · source date {source.as_of_date || "unknown"}</p>
          <p>{source.provider} / {source.model} · {source.prompt_version} · AI output #{source.ai_output_id}</p>
          {source.findings.map((finding, index) => <div key={index}><blockquote>{finding.quote}</blockquote><p>Stored exact span {finding.start_char}–{finding.end_char}{finding.page ? ` · page ${finding.page}` : ""}. Text identity does not verify interpretation.</p></div>)}
          <p className="basis-note" style={{ overflowWrap: "anywhere" }}>Source SHA256: {source.source_sha256}</p>
        </article>)}
        <p>Limits: {context.company_limit} companies, {context.source_limit} sources, {context.decision_limit} decisions. {context.company_count} active companies available.</p>
        {Object.entries(context.excluded).filter(([, count]) => count > 0).map(([reason, count]) => <p key={reason}>Excluded: {reason.replaceAll("_", " ")} ({count})</p>)}
        <p className="basis-note" style={{ overflowWrap: "anywhere" }}>Snapshot input SHA256: {context.input_sha256}</p>
      </details>
    </>}
  </Panel>;
}
