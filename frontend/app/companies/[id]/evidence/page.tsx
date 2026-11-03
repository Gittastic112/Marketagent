import { PageHeader, Panel, EmptyState, ErrorState } from "@/components/page";
import { DataStateNotices } from "@/components/ui/data-states";
import type { Company, EvidenceLedgerItem } from "@/lib/api";
import { serverFetchApiResponse } from "@/lib/server-api";
import Link from "next/link";
import { hasUsableData } from "@/lib/data-state-meta";

export const dynamic = "force-dynamic";

export default async function EvidenceLedgerPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const companyId = parseInt(id, 10);
  const companyRes = await serverFetchApiResponse<Company>(`/companies/${companyId}`);
  const company = companyRes.data;

  if (!hasUsableData(companyRes)) return <ErrorState message="Company evidence could not be loaded. Reload to retry." />;

  if (!company) {
    return <EmptyState label="Company not found." />;
  }

  const evidenceRes = await serverFetchApiResponse<EvidenceLedgerItem[]>(`/evidence?company_id=${companyId}`);
  const evidenceItems = evidenceRes?.data || [];

  return (
    <>
      <div style={{ display: "flex", alignItems: "center", gap: "1rem", marginBottom: "1rem" }}>
        <Link href={`/companies/${company.id}`} className="btn btn-outline" style={{ fontSize: "0.85rem", padding: "0.4rem 0.8rem" }}>
          ← Back to Overview
        </Link>
      </div>

      <PageHeader
        eyebrow={`${company.name} (${company.ticker})`}
        title="Evidence Ledger"
        status={hasUsableData(evidenceRes) ? `${evidenceItems.length} items logged` : "Evidence unavailable"}
      />
      <DataStateNotices metas={[companyRes.meta, evidenceRes?.meta]}
        mockMessage="Mock Data: these evidence records are test inputs, not verified company facts." />
      <p className="muted">User Assumption: manually recorded evidence and its interpretation require source review.</p>

      <Panel title="Accumulating Evidence">
        {!hasUsableData(evidenceRes) ? <ErrorState message="Evidence could not be loaded. Reload to retry; this does not mean the ledger is empty." /> : evidenceItems.length === 0 ? (
          <EmptyState label="No evidence items logged for this company yet." />
        ) : (
          <div className="table-wrap" tabIndex={0} role="region" aria-label="Recorded company evidence">
            <table>
              <thead>
                <tr>
                  <th>Date</th>
                  <th>Effect</th>
                  <th>Evidence</th>
                  <th>Confidence</th>
                  <th>Source</th>
                </tr>
              </thead>
              <tbody>
                {evidenceItems.map((item) => (
                  <tr key={item.id}>
                    <td style={{ whiteSpace: "nowrap" }}>{new Date(item.date_discovered).toLocaleDateString()}</td>
                    <td>
                      <span className="badge" style={{
                        backgroundColor: item.effect === 'Supports' ? 'var(--success-bg)' : item.effect === 'Contradicts' ? 'var(--error-bg)' : 'var(--warning-bg)',
                        color: item.effect === 'Supports' ? 'var(--success)' : item.effect === 'Contradicts' ? 'var(--error)' : 'var(--warning)'
                      }}>
                        {item.effect}
                      </span>
                    </td>
                    <td style={{ maxWidth: "400px", whiteSpace: "normal" }}>{item.evidence_text}</td>
                    <td>{item.confidence}</td>
                    <td>
                      {item.source_link && /^https?:\/\//i.test(item.source_link) ? (
                        <a href={item.source_link} target="_blank" rel="noopener noreferrer" className="text-link">View Source</a>
                      ) : (
                        <span className="muted">Manual</span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
        <div style={{ marginTop: "1.5rem", padding: "0 1.5rem 1.5rem" }}>
          <Link href={`/companies/${company.id}/decisions#evidence-entry`} className="btn btn-primary">+ Log Evidence</Link>
        </div>
      </Panel>
    </>
  );
}
