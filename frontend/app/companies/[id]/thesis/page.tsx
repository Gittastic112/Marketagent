import { PageHeader, Panel, EmptyState, ErrorState } from "@/components/page";
import { serverFetchApiResponse } from "@/lib/server-api";
import type { Company, ThesisNote } from "@/lib/api";
import Link from "next/link";
import { DataHealthUpdater } from "@/components/providers/data-health-updater";
import { DataStateNotices } from "@/components/ui/data-states";

export const dynamic = "force-dynamic";

export default async function ThesisEnginePage({ params, searchParams }: { params: Promise<{ id: string }>; searchParams?: Promise<{ note_id?: string }> }) {
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
  const requested = (await searchParams)?.note_id;
  const orderedNotes = [...companyNotes].sort((a, b) => (b.updated_at ?? "").localeCompare(a.updated_at ?? "") || b.id - a.id);
  const activeThesis = requested ? companyNotes.find(note => String(note.id) === requested) ?? null
    : orderedNotes.find(note => note.status === "active") ?? orderedNotes[0] ?? null;

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
        title="Thesis and research notes"
        status={activeThesis ? activeThesis.status : "No note selected"}
      />

      {thesisRes.meta.status === "success" && companyNotes.length > 0 && <Panel title="Selected research note">
        <form method="get" className="form-grid"><label>Research note<select name="note_id" defaultValue={activeThesis?.id ?? ""} required>
          {!activeThesis && <option value="">Choose an available note</option>}
          {orderedNotes.map(note => <option key={note.id} value={note.id}>{note.title} · {note.status}</option>)}
        </select></label><button type="submit">Show this note</button></form>
        {requested && !activeThesis && <ErrorState message="That note is unavailable for this company. Select one of your available notes." />}
        {activeThesis && <><h2>{activeThesis.title}</h2><p>User Assumption / research interpretation · Updated {new Date(activeThesis.updated_at).toLocaleString()}</p>
          <div className="preserve-whitespace">{activeThesis.thesis_text}</div>
          <p>Supporting or opposing interpretations do not approve financial facts. No linked evidence does not mean no evidence exists.</p>
          <Link href={`/thesis-notes/${activeThesis.id}`}>Edit this exact note and its evidence</Link></>}
        {orderedNotes.length > 1 && <details><summary>Other notes for this company ({orderedNotes.length - (activeThesis ? 1 : 0)})</summary><ul>
          {orderedNotes.filter(note => note.id !== activeThesis?.id).map(note => <li key={note.id}><Link href={`?note_id=${note.id}`}>{note.title}</Link> · {note.status}</li>)}
        </ul></details>}
      </Panel>}

      <div style={{ display: "grid", gridTemplateColumns: "1fr", gap: "2rem" }}>
        <div id="thesis-evidence" className="min-w-0"><Panel title="Core Assumptions">
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
                                </span> {imp.rationale}<br /><span className="badge">{(imp.review_status || "unreviewed").replaceAll("_", " ")}</span>{" "}<Link href={`/events/${imp.event_id}`}>Inspect source event</Link>
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
        </Panel></div>

        {activeThesis && <Panel title="Recorded note changes">
          {activeThesis.changes.length === 0 ? <p>No changes have been logged for this note.</p> : <ol>
            {[...activeThesis.changes].sort((a, b) => b.created_at.localeCompare(a.created_at)).map(change => <li key={change.id}>
              <time>{new Date(change.created_at).toLocaleString()}</time><p>{change.change_summary}</p>
            </li>)}
          </ol>}
          <Link href={`/companies/${companyId}/decisions`}>Decision journal and next review triggers</Link>
        </Panel>}

        <Panel title="Variant Perception Map">
          <p>Compare the recorded market view with your own interpretation in the decision journal.</p>
          <Link href={`/companies/${companyId}/decisions`}>Review variant perceptions and next actions</Link>
        </Panel>
      </div>
    </>
  );
}
