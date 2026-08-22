import Link from "next/link";
import { PageHeader, Panel, ErrorState, EmptyState } from "@/components/page";
import { DataStateNotices } from "@/components/ui/data-states";
import { serverFetchApiResponse } from "@/lib/server-api";
import type { RawDocument, EventRecord, ThesisNote } from "@/lib/api";

function formatDate(isoString: string) {
  return new Date(isoString).toLocaleDateString(undefined, { month: 'short', day: 'numeric', year: 'numeric' });
}

export default async function ResearchPage() {
  try {
    const [documentsRes, eventsRes, thesisNotesRes] = await Promise.all([
      serverFetchApiResponse<RawDocument[]>("/raw-documents/summaries").catch(() => ({ data: [], meta: null })),
      serverFetchApiResponse<EventRecord[]>("/events").catch(() => ({ data: [], meta: null })),
      serverFetchApiResponse<ThesisNote[]>("/thesis-notes").catch(() => ({ data: [], meta: null }))
    ]);
    const documents = documentsRes.data || [];
    const events = eventsRes.data || [];
    const thesisNotes = thesisNotesRes.data || [];

    const recentDocuments = documents.slice(0, 5);
    const recentEvents = events.slice(0, 5);
    const recentThesisNotes = thesisNotes.slice(0, 5);

    return (
      <>
        <PageHeader eyebrow="Source-backed evidence" title="Research Hub" />
        <DataStateNotices
          metas={[documentsRes.meta, eventsRes.meta, thesisNotesRes.meta]}
          mockMessage="One or more research panels are using mock data. Treat affected evidence as placeholder material."
        />

        <div className="research-actions">
          <Link prefetch={false} href="/research/sessions" className="secondary-button" style={{ backgroundColor: "var(--accent-color)", color: "white" }}>AI Sessions</Link>
          <Link prefetch={false} href="/documents" className="secondary-button">All Documents</Link>
          <Link prefetch={false} href="/events" className="secondary-button">All Events</Link>
          <Link prefetch={false} href="/thesis-notes" className="secondary-button">All Thesis Notes</Link>
          <Link prefetch={false} href="/daily-brief" className="secondary-button">Daily Briefs</Link>
        </div>

        <div className="metric-grid research-grid">

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

                    <div style={{ marginTop: "0.5rem" }}>
                      <Link prefetch={false} href={`/documents/${doc.id}/sections`} style={{ fontSize: "0.85rem", marginRight: "0.75rem" }}>View Sections</Link>
                      <Link prefetch={false} href={`/documents/${doc.id}/ai`} style={{ fontSize: "0.85rem" }}>AI Summaries</Link>
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
