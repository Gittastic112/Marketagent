import Link from "next/link";
import type { BriefSource } from "@/lib/api/brief-sources";

export function BriefSourceFindings({ source, includeAnchors = false }: { source: BriefSource; includeAnchors?: boolean }) {
  if (!source.analysis) return null;
  return <div className="brief-findings">
    <div className="section-intro"><span className="badge">AI Interpretation</span>
      {source.is_mock && <span className="badge badge-warn">Mock Data</span>}
      <span>{source.review_status.replaceAll("_", " ")} · {source.provider} / {source.model}</span>
    </div>
    <p>{source.analysis.summary}</p>
    <p className="muted">Importance is the model&apos;s judgment, not a verified materiality score. Suggested directions need your review, not automatic numerical edits.</p>
    {source.analysis.findings.map((finding, index) => <article className="brief-finding" id={includeAnchors ? `finding-${index}` : undefined} key={index}>
      <div className="brief-finding-heading"><span className={`badge ${finding.importance === "high" ? "badge-warn" : "badge-outline"}`}>{finding.importance} importance</span><h3>{finding.title}</h3></div>
      <p>{finding.importance_reason}</p>
      <details><summary>Exact source passage{finding.page ? ` · PDF page ${finding.page}` : ""}</summary>
        <blockquote className="brief-source-quote">{finding.quote}</blockquote>
        <Link prefetch={false} href={`/daily-brief/sources/${source.id}`}>Read stored source</Link>
        <span className="muted"> · Source match verified; interpretation not verified · {finding.confidence} AI confidence</span>
      </details>
      {finding.valuation_inputs.length ? <div className="brief-input-links">{finding.valuation_inputs.map((input, i) => <div key={i}>
        <Link prefetch={false} href={input.review_href}>Review {input.label} →</Link>
        <p><span className="badge badge-outline">{input.direction === "review" ? "Review basis" : `Potential ${input.direction}`}</span> {input.reason}</p>
      </div>)}</div> : <p className="muted">No specific valuation input change supported by this finding.</p>}
    </article>)}
    <p className="muted">Generated {source.generated_at ? new Date(source.generated_at).toLocaleString() : "date unavailable"}. No saved model or reviewed input was changed.</p>
  </div>;
}
