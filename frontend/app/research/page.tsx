import Link from "next/link";
import { PageHeader, Panel, ErrorState, EmptyState } from "@/components/page";
import { fetchApi } from "@/lib/api";
import type { RawDocument, EventRecord, ThesisNote } from "@/lib/api";

function formatDate(isoString: string) {
  return new Date(isoString).toLocaleDateString(undefined, { month: 'short', day: 'numeric', year: 'numeric' });
}

export default async function ResearchPage() {
  try {
    const [documents, events, thesisNotes] = await Promise.all([
      fetchApi<RawDocument[]>("/raw-documents").catch(() => []),
      fetchApi<EventRecord[]>("/events").catch(() => []),
      fetchApi<ThesisNote[]>("/thesis-notes").catch(() => [])
    ]);

    const recentDocuments = documents.slice(0, 5);
    const recentEvents = events.slice(0, 5);
    const recentThesisNotes = thesisNotes.slice(0, 5);

    return (
      <>
        <PageHeader eyebrow="Source-backed evidence" title="Research Hub" />
        
        <div style={{ display: "flex", gap: "1rem", marginBottom: "1rem" }}>
          <Link href="/documents" className="secondary-button">All Documents</Link>
          <Link href="/events" className="secondary-button">All Events</Link>
          <Link href="/thesis-notes" className="secondary-button">All Thesis Notes</Link>
          <Link href="/daily-brief" className="secondary-button">Daily Briefs</Link>
        </div>

        <div className="metric-grid" style={{ gridTemplateColumns: "repeat(auto-fit, minmax(400px, 1fr))", gap: "1.5rem" }}>
          
          <Panel title="Recent Source Documents">
            {recentDocuments.length === 0 ? (
              <EmptyState label="No documents ingested yet." />
            ) : (
              <div className="brief-list">
                {recentDocuments.map((doc) => (
                  <div key={doc.id} className="brief-item" style={{ padding: "0.75rem", borderBottom: "1px solid var(--border-color)", marginBottom: 0 }}>
                    <div style={{ display: "flex", justifyContent: "space-between", alignItems: "baseline" }}>
                      <strong>{doc.url ? <a href={doc.url} target="_blank" rel="noopener noreferrer">{doc.title}</a> : doc.title}</strong>
                      <span className="badge">{doc.document_type}</span>
                    </div>
                    {doc.published_at && <p className="muted" style={{ margin: "0.25rem 0 0 0", fontSize: "0.8rem" }}>Published: {formatDate(doc.published_at)}</p>}
                    <div style={{ marginTop: "0.5rem" }}>
                      <Link href={`/documents/${doc.id}/sections`} style={{ fontSize: "0.85rem", marginRight: "0.75rem" }}>View Sections</Link>
                      <Link href={`/documents/${doc.id}/ai`} style={{ fontSize: "0.85rem" }}>AI Summaries</Link>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </Panel>

          <Panel title="Recent Extracted Events">
            {recentEvents.length === 0 ? (
              <EmptyState label="No events extracted yet." />
            ) : (
              <div className="brief-list">
                {recentEvents.map((evt) => (
                  <div key={evt.id} className="brief-item" style={{ padding: "0.75rem", borderBottom: "1px solid var(--border-color)", marginBottom: 0 }}>
                    <div style={{ display: "flex", justifyContent: "space-between", alignItems: "baseline" }}>
                      <strong>{evt.title}</strong>
                      <span className="badge" style={{ backgroundColor: evt.priority_score && evt.priority_score > 7 ? "var(--error-bg)" : "var(--bg-secondary)" }}>
                        Score: {evt.priority_score ?? "-"}
                      </span>
                    </div>
                    {evt.description && <p style={{ fontSize: "0.9rem", margin: "0.5rem 0 0 0" }}>{evt.description}</p>}
                    {evt.event_date && <p className="muted" style={{ margin: "0.25rem 0 0 0", fontSize: "0.8rem" }}>Date: {formatDate(evt.event_date)}</p>}
                  </div>
                ))}
              </div>
            )}
          </Panel>

          <Panel title="Active Thesis Notes">
            {recentThesisNotes.length === 0 ? (
              <EmptyState label="No thesis notes recorded." />
            ) : (
              <div className="brief-list">
                {recentThesisNotes.map((note) => (
                  <div key={note.id} className="brief-item" style={{ padding: "0.75rem", borderBottom: "1px solid var(--border-color)", marginBottom: 0 }}>
                    <div style={{ display: "flex", justifyContent: "space-between", alignItems: "baseline" }}>
                      <strong>{note.title}</strong>
                      <span className="badge">{note.status}</span>
                    </div>
                    {note.thesis_text && <p style={{ fontSize: "0.9rem", margin: "0.5rem 0 0 0" }}>{note.thesis_text.substring(0, 100)}{note.thesis_text.length > 100 ? "..." : ""}</p>}
                  </div>
                ))}
              </div>
            )}
          </Panel>

        </div>
      </>
    );
  } catch (error) {
    return (
      <>
        <PageHeader eyebrow="Source-backed evidence" title="Research Hub" />
        <ErrorState message="Could not load data for the research hub." />
      </>
    );
  }
}
