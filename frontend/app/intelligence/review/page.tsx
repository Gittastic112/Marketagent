import Link from "next/link";
import { EmptyState, ErrorState, PageHeader, Panel } from "@/components/page";
import { hasUsableData } from "@/lib/data-state-meta";

import { DataStateNotices } from "@/components/ui/data-states";
import type { IntelligenceReviewItem } from "@/lib/api";
import { serverFetchApiResponse } from "@/lib/server-api";


export const dynamic = "force-dynamic";

export default async function IntelligenceReviewPage() {
  const itemsRes = await serverFetchApiResponse<IntelligenceReviewItem[]>("/intelligence/review");
  const items = itemsRes.data || [];
  const changes = items.filter(item => item.item_type !== "filing_baseline");
  const baselines = items.filter(item => item.item_type === "filing_baseline");
  return (
    <>
      <PageHeader eyebrow="Evidence review" title="Contradictions & Language Changes" status={hasUsableData(itemsRes) ? `${changes.length} review items · ${baselines.length} baselines` : "Review queue unavailable"} />
      <DataStateNotices metas={[itemsRes.meta]} />
      <Panel title="Review Queue">
        {!hasUsableData(itemsRes) ? <ErrorState message="Review queue could not be loaded. Reload to retry." /> : changes.length === 0 ? (
          <EmptyState label="No explicit contradictions or filing language changes are waiting for review." />
        ) : (
          <div className="table-wrap">
            <table>
              <thead><tr><th>Signal</th><th>Type</th><th>Severity</th><th>Basis</th><th>Evidence</th></tr></thead>
              <tbody>
                {changes.map((item) => (
                  <tr key={item.item_id}>
                    <td><strong>{item.title}</strong><br /><small>{item.summary}</small></td>
                    <td>{item.item_type.replaceAll("_", " ")}</td>
                    <td><span className={item.severity === "high" ? "badge badge-warn" : "badge"}>{item.severity}</span></td>
                    <td>{item.claim_type}</td>
                    <td><Link href={item.evidence_href}>Review source</Link></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Panel>
      {baselines.length > 0 && <Panel title={`Filing baselines (${baselines.length})`} collapsible>
        <p className="muted">These sections have no matching prior section. Their text is retained for comparison when earlier evidence is available.</p>
        <div className="table-wrap"><table>
          <thead><tr><th>Section</th><th>Comparison basis</th><th>Evidence</th></tr></thead>
          <tbody>{baselines.map(item => <tr key={item.item_id}>
            <td>{item.title}</td><td>{item.summary}</td><td><Link href={item.evidence_href}>Review source</Link></td>
          </tr>)}</tbody>
        </table></div>
      </Panel>}
    </>
  );
}
