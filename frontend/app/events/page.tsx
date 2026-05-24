import { EmptyState, ErrorState, PageHeader, Panel } from "@/components/page";
import { fetchApi } from "@/lib/api";
import type { EventRecord } from "@/lib/api";

export default async function EventsPage() {
  try {
    const events = await fetchApi<EventRecord[]>("/events");

    return (
      <>
        <PageHeader eyebrow="Normalized signal" title="Events" status={`${events.length} events`} />
        <Panel title="Events">
          {events.length === 0 ? (
            <EmptyState label="No events yet." />
          ) : (
            <div className="table-wrap">
              <table>
                <thead>
                  <tr>
                    <th>Title</th>
                    <th>Type</th>
                    <th>Speed</th>
                    <th>Credibility</th>
                    <th>Novelty</th>
                    <th>Impact</th>
                    <th>Priority</th>
                  </tr>
                </thead>
                <tbody>
                  {events.map((event) => (
                    <tr key={event.id}>
                      <td>{event.title}</td>
                      <td>{event.event_type}</td>
                      <td>{event.information_speed}</td>
                      <td>{event.credibility_score ?? "-"}</td>
                      <td>{event.novelty_score ?? "-"}</td>
                      <td>{event.impact_score ?? "-"}</td>
                      <td>{event.priority_score ?? "-"}</td>
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
        <PageHeader eyebrow="Normalized signal" title="Events" />
        <ErrorState message="Could not load events from the backend API." />
      </>
    );
  }
}
