import { EmptyState, ErrorState, PageHeader, Panel } from "@/components/page";
import { fetchApi } from "@/lib/api";
import type { AlertRecord, Company, DailyBrief, EventRecord, RawDocument, ThesisNote } from "@/lib/api";

async function loadOverview() {
  const [companies, documents, events, alerts, thesisNotes, dailyBrief] = await Promise.all([
    fetchApi<Company[]>("/companies"),
    fetchApi<RawDocument[]>("/raw-documents"),
    fetchApi<EventRecord[]>("/events"),
    fetchApi<AlertRecord[]>("/alerts"),
    fetchApi<ThesisNote[]>("/thesis-notes"),
    fetchApi<DailyBrief>("/daily-brief")
  ]);

  return { companies, documents, events, alerts, thesisNotes, dailyBrief };
}

export default async function HomePage() {
  try {
    const { companies, documents, events, alerts, thesisNotes, dailyBrief } = await loadOverview();

    return (
      <>
        <PageHeader eyebrow="Local dashboard" title="Overview" status={dailyBrief.date} />
        <section className="metric-grid">
          <Metric label="Companies" value={companies.length} />
          <Metric label="Documents" value={documents.length} />
          <Metric label="Events" value={events.length} />
          <Metric label="Alerts" value={alerts.length} />
        </section>
        <Panel title="Daily Brief">
          <div className="brief-list">
            <div className="brief-item">
              <h3>{dailyBrief.title}</h3>
              <p>{dailyBrief.summary}</p>
            </div>
          </div>
        </Panel>
        <Panel title="Active Thesis Notes">
          {thesisNotes.length === 0 ? (
            <EmptyState label="No thesis notes yet." />
          ) : (
            <div className="table-wrap">
              <table>
                <thead>
                  <tr>
                    <th>Title</th>
                    <th>Status</th>
                  </tr>
                </thead>
                <tbody>
                  {thesisNotes.map((note) => (
                    <tr key={note.id}>
                      <td>{note.title}</td>
                      <td>
                        <span className="badge">{note.status}</span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </Panel>
      </>
    );
  } catch {
    return (
      <>
        <PageHeader eyebrow="Local dashboard" title="Overview" />
        <ErrorState message="The frontend could not reach the backend API." />
      </>
    );
  }
}

function Metric({ label, value }: { label: string; value: number }) {
  return (
    <div className="metric">
      <div className="metric-label">{label}</div>
      <div className="metric-value">{value}</div>
    </div>
  );
}
