import Link from "next/link";
import { ErrorState, PageHeader, Panel } from "@/components/page";
import { FindingEvidence } from "@/components/brief-source-triage";
import type { ComparisonReviewDetail } from "@/lib/api/brief-triage";
import { serverFetchApiResponse } from "@/lib/server-api";

export default async function ReviewReceiptPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  if (!/^\d+$/.test(id)) return <ErrorState message="Review not found." />;
  const response = await serverFetchApiResponse<ComparisonReviewDetail>(`/brief-sources/triage/reviews/${id}`);
  const review = response.data;
  if (!review) return <ErrorState message="Review receipt unavailable or not owned by this account." errors={response.errors} />;
  const evidence = review.evidence;
  const sources = new Map(evidence.sources.map(source => [source.id, source]));
  return <>
    <PageHeader eyebrow="Private research · User Assumption" title={`${evidence.ticker} · ${evidence.group.label} review`} status={`Version ${review.version}`} />
    <Link prefetch={false} href={`/daily-brief/triage?company_id=${review.company_id}`}>← Current company comparison (non-mock default)</Link>
    <Panel title="Saved analyst decision">
      <p><strong>{review.disposition.replaceAll("_", " ")}</strong> · Recorded {new Date(review.created_at).toLocaleString("en-US", { timeZone: "UTC", timeZoneName: "short" })}</p>
      <p className="preserve-whitespace">{review.notes}</p>
      <p className="basis-note">{review.is_current ? "The current bounded evidence matches this receipt." : "Evidence has changed. This decision applies only to the saved evidence below."} This may not be the latest decision. It never approves AI output, certifies facts or changes financial inputs.</p>
      {review.include_mock && <p className="badge badge-warn">Mock-inclusive comparison scope</p>}
      <p className="brief-source-hash">Evidence SHA-256: {review.evidence_hash}</p>
    </Panel>
    <Panel title="Evidence preserved at review">
      <p>{evidence.coverage.included_sources} included sources of {evidence.coverage.active_sources} active records in the compared company scope. {evidence.coverage.not_examined} older active sources were outside the limit. {evidence.coverage.archived_sources} archived sources were excluded.</p>
      <p className="muted">Only this input&apos;s source records are reproduced below. Method {evidence.methodology}. Original source links may now show a newer scan; the passages below are the saved receipt.</p>
      {Object.keys(evidence.coverage.excluded).length > 0 && <ul className="compact-list">{Object.entries(evidence.coverage.excluded).map(([reason, count]) => <li key={reason}>{reason.replaceAll("_", " ")}: {count} excluded</li>)}</ul>}
      <div className="triage-evidence-grid">{evidence.group.items.map(item => {
        const source = sources.get(item.source_id)!;
        const finding = source.findings[item.finding_index];
        return <FindingEvidence key={`${item.source_id}:${item.finding_index}:${item.suggestion_index}`} source={source} finding={finding}
          index={item.finding_index} suggestion={finding.valuation_inputs[item.suggestion_index]} />;
      })}</div>
    </Panel>
  </>;
}
