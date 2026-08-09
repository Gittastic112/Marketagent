import Link from "next/link";
import { EmptyState, PageHeader, Panel } from "@/components/page";

import { DataStateNotices } from "@/components/ui/data-states";
import type { IntelligenceReviewItem } from "@/lib/api";
import { serverFetchApiResponse } from "@/lib/server-api";


export const dynamic = "force-dynamic";

export default async function IntelligenceReviewPage() {
  const itemsRes = await serverFetchApiResponse<IntelligenceReviewItem[]>("/intelligence/review").catch(() => ({ data: [], meta: null }));
  const items = itemsRes.data || [];
  return (
    <>
      <PageHeader eyebrow="Evidence review" title="Contradictions & Language Changes" status={`${items.length} items`} />
      <DataStateNotices metas={[itemsRes.meta]} />
      <Panel title="Review Queue">
        {items.length === 0 ? (
          <EmptyState label="No explicit contradictions or filing language changes are waiting for review." />
        ) : (
          <div className="table-wrap">
            <table>
              <thead><tr><th>Signal</th><th>Type</th><th>Severity</th><th>Basis</th><th>Evidence</th></tr></thead>
              <tbody>
                {items.map((item) => (
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
    </>
  );
}
