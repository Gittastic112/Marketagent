import { PageHeader, Panel, EmptyState, ErrorState } from "@/components/page";
import { serverFetchApiResponse } from "@/lib/server-api";
import type { Company, ThesisNote } from "@/lib/api";
import Link from "next/link";
import { DataHealthUpdater } from "@/components/providers/data-health-updater";
import { DataStateNotices } from "@/components/ui/data-states";

export const dynamic = "force-dynamic";

export default async function ThesisEnginePage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const companyId = parseInt(id, 10);
  const companyRes = await serverFetchApiResponse<Company>(`/companies/${companyId}`);
  const company = companyRes.data;

  if (!company) {
    return <ErrorState message="Company information is unavailable. Reload to retry." errors={companyRes.errors} />;
  }

  const thesisRes = await serverFetchApiResponse<ThesisNote[]>(`/thesis-notes?company_id=${companyId}`);
  const allNotes = thesisRes.data || [];
  const companyNotes = allNotes.filter(n => n.company_id === companyId);
  const activeThesis = companyNotes.find(note => note.status === "active") ?? null;

  const isStale = !!thesisRes.meta?.is_stale;

  return (
    <>
      <DataHealthUpdater segment="thesis" isStale={isStale} />
      <DataStateNotices metas={[companyRes.meta, thesisRes.meta]} />
      <div style={{ display: "flex", alignItems: "center", gap: "1rem", marginBottom: "1rem" }}>
        <Link href={`/companies/${company.id}`} className="btn btn-outline" style={{ fontSize: "0.85rem", padding: "0.4rem 0.8rem" }}>
          ← Back to Overview
        </Link>
      </div>

      <PageHeader
        eyebrow={`${company.name} (${company.ticker})`}
        title="Thesis Assumption Engine"
        status={activeThesis ? "Active Thesis" : "No active thesis"}
      />

      <div style={{ display: "grid", gridTemplateColumns: "1fr", gap: "2rem" }}>
        <Panel title="Core Assumptions">
          {thesisRes.meta.status !== "success" ? <ErrorState message="Thesis notes are unavailable. Reload to retry." errors={thesisRes.errors} /> : !activeThesis ? (
            <EmptyState label="No thesis created for this company yet." />
          ) : activeThesis.assumptions.length === 0 ? (
            <EmptyState label="No structured assumptions added to this thesis." />
          ) : (
            <div className="table-wrap" role="region" aria-label="Thesis assumptions" tabIndex={0}>
              <table>
                <thead>
                  <tr>
                    <th>Category</th>
                    <th>Assumption</th>
                    <th>Importance</th>
                    <th>Confidence</th>
                    <th>Evidence Chain</th>
                    <th>Falsification Trigger</th>
                  </tr>
                </thead>
                <tbody>
                  {activeThesis.assumptions.map((assump) => (
                    <tr key={assump.id}>
                      <td><span className="badge">{assump.category || "General"}</span></td>
                      <td style={{ maxWidth: "300px", whiteSpace: "normal" }}><strong>{assump.description}</strong></td>
                      <td>{assump.importance}</td>
                      <td>
                        <span style={{
                          color: assump.current_confidence === 'high' ? 'var(--success)' : assump.current_confidence === 'low' ? 'var(--error)' : 'var(--warning)',
                          fontWeight: 600
                        }}>
                          {assump.current_confidence}
                        </span>
                      </td>
                      <td>
                        {assump.impacts && assump.impacts.length > 0 ? (
                          <div style={{ display: "flex", flexDirection: "column", gap: "0.25rem" }}>
                            {assump.impacts.map(imp => (
                              <div key={imp.id} style={{ fontSize: "0.8rem", padding: "0.2rem 0.4rem", background: "var(--panel-bg-alt)", border: "1px solid var(--border-color)", borderRadius: "4px" }}>
                                <span style={{
                                  color: imp.impact_classification === 'Supports' ? 'var(--success)' : imp.impact_classification === 'Weakens' ? 'var(--error)' : 'inherit',
                                  fontWeight: "bold"
                                }}>
                                  [{imp.impact_classification}]
                                </span> {imp.rationale}
                              </div>
                            ))}
                          </div>
                        ) : (
                          <span className="muted" style={{ fontSize: "0.85rem" }}>No events linked</span>
                        )}
                      </td>
                      <td style={{ maxWidth: "250px", whiteSpace: "normal", color: "var(--muted)", fontStyle: "italic", fontSize: "0.85rem" }}>
                        {assump.falsification_trigger || "None defined"}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
          <div style={{ marginTop: "1.5rem", padding: "0 1.5rem 1.5rem" }}>
            <Link className="btn btn-primary" href={activeThesis ? `/thesis-notes/${activeThesis.id}` : "/thesis-notes"}>
              {activeThesis ? "Review or add thesis assumptions" : "Create or select a thesis note"}
            </Link>
          </div>
        </Panel>

        <Panel title="Variant Perception Map">
          <p>Compare the recorded market view with your own interpretation in the decision journal.</p>
          <Link href={`/companies/${companyId}/decisions`}>Review variant perceptions and next actions</Link>
        </Panel>
      </div>
    </>
  );
}
