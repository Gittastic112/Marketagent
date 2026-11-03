import Link from "next/link";
import { EmptyState, ErrorState, Panel } from "@/components/page";
import type { ApiResponse, PeerReviewReceiptHealth } from "@/lib/api";
import { receiptAuditHref } from "@/lib/peer-health-navigation";

export function PeerReceiptHealthPanel({ response, audit }: {
  response: ApiResponse<PeerReviewReceiptHealth>;
  audit?: string | null;
}) {
  const report = response.data;
  return <Panel title="Peer Review Receipts">
    {!report ? <ErrorState message="Peer review receipt health is unavailable." errors={response.errors} /> : <>
      <p className="muted">Calculation from your stored peer evidence, checked {new Date(report.generated_at).toISOString()}.
        {" "}{report.checked_set_count} sets checked on this page; {report.total_owned_set_count} owned sets in total.
        Counts below apply only to this page. Eligible peer evidence still requires company financial inputs at calculation time.</p>
      <div className="health-metric-grid">
        {[
          ["Eligible peer sets", report.ready_for_valuation_count],
          ["Missing receipts", report.missing_receipt_count],
          ["Stale receipts", report.stale_receipt_count],
          ["Evidence conflicts", report.storage_blocked_count],
          ["Insufficient method coverage", report.coverage_blocked_count],
          ["Draft sets", report.draft_set_count],
          ["Archived sets", report.archived_set_count],
        ].map(([label, count]) => <article key={label} className="health-metric-card">
          <span className="health-metric-label">{label}</span><strong className="health-metric-value">{count}</strong>
        </article>)}
      </div>
      {report.total_owned_set_count === 0 ? <div className="empty">
        No peer sets yet. <Link prefetch={false} href="/companies">Choose a company to add sourced peers</Link>.
      </div> : report.checked_set_count === 0 ? <EmptyState label="No peer sets remain after this cursor. Restart the audit to check current evidence." />
        : report.active_reviewed_set_count === 0 ? <EmptyState label="No active reviewed peer sets on this page. Draft and archived sets are excluded from calculation eligibility." />
        : report.sets_requiring_attention.length === 0 ? <EmptyState label="No peer evidence blockers found among the active reviewed sets on this page." />
        : <div className="table-wrap"><table>
          <thead><tr><th>Peer set</th><th>Receipt</th><th>Evidence blockers</th><th>Warnings</th><th>Action</th></tr></thead>
          <tbody>{report.sets_requiring_attention.map((item) => <tr key={item.peer_set_id}>
            <td><Link prefetch={false} href={`/companies/${item.company_id}/valuation/peers#peer-set-${item.peer_set_id}`}>
              {item.name} (v{item.version})
            </Link></td>
            <td>{item.receipt_status}<br />Current: {item.current_diagnostics_as_of}<br />Acknowledged: {item.receipt_diagnostics_as_of ?? "Never"}</td>
            <td>{item.blockers.map(code => code.replaceAll("_", " ")).join("; ")}<br />Usable methods: {item.usable_methods.join(", ") || "None"}</td>
            <td>Current: {item.current_warning_codes.join(", ") || "None"}<br />Acknowledged: {item.acknowledged_warning_codes.join(", ") || "None"}</td>
            <td>{item.action}</td>
          </tr>)}</tbody>
        </table></div>}
      <nav aria-label="Peer audit pages" style={{ display: "flex", gap: "1rem", marginTop: "1rem" }}>
        <Link prefetch={false} href={receiptAuditHref(0, audit)}>Refresh from first page</Link>
        {report.has_more && report.next_after_id !== null ? <Link prefetch={false} href={receiptAuditHref(report.next_after_id, audit)}>Check next peer sets</Link> : null}
      </nav>
    </>}
  </Panel>;
}
