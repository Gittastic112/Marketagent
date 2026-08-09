import { PageHeader, Panel, EmptyState } from "@/components/page";
import type { Company, EvidenceLedgerItem } from "@/lib/api";
import { serverFetchApi, serverFetchApiResponse } from "@/lib/server-api";
import Link from "next/link";
import { Suspense } from "react";

export const dynamic = "force-dynamic";

export default async function EvidenceLedgerPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const companyId = parseInt(id, 10);
  const companyRes = await serverFetchApiResponse<Company>(`/companies/${companyId}`);
  const company = companyRes.data;

  if (!company) {
    return <EmptyState label="Company not found." />;
  }

  // Fallback to empty array if backend is not yet migrated
  let evidenceItems: EvidenceLedgerItem[] = [];
  try {
    evidenceItems = await serverFetchApi<EvidenceLedgerItem[]>(`/evidence?company_id=${companyId}`);
  } catch (e) {
    console.warn("Evidence ledger API failed, possibly unmigrated.", e);
  }

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
        status={`${evidenceItems.length} items logged`}
      />

      <Panel title="Accumulating Evidence">
        {evidenceItems.length === 0 ? (
          <EmptyState label="No evidence items logged for this company yet." />
        ) : (
          <div className="table-wrap">
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
                      {item.source_link ? (
                        <a href={item.source_link} target="_blank" rel="noopener noreferrer" style={{ color: "var(--accent)" }}>View Source</a>
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
          <button className="btn btn-primary">+ Log Evidence</button>
        </div>
      </Panel>
    </>
  );
}
