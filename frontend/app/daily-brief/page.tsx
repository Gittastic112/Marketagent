import { saveDailyBrief } from "@/app/actions";
import { EmptyState, ErrorState, PageHeader, Panel } from "@/components/page";
import { fetchApi } from "@/lib/api";
import type { DailyBrief, SavedDailyBrief } from "@/lib/api";

export default async function DailyBriefPage() {
  try {
    const [brief, savedBriefs] = await Promise.all([
      fetchApi<DailyBrief>("/daily-brief"),
      fetchApi<SavedDailyBrief[]>("/daily-brief-history")
    ]);

    return (
      <>
        <PageHeader eyebrow="Daily output" title={brief.title} status={brief.date} />
        <Panel title="Summary">
          <div className="brief-list">
            <div className="brief-item">
              <p>{brief.summary}</p>
              <form action={saveDailyBrief} className="button-row">
                <button type="submit">Save brief</button>
              </form>
            </div>
          </div>
        </Panel>
        <Panel title="Saved Briefs">
          {savedBriefs.length === 0 ? (
            <EmptyState label="No saved briefs yet." />
          ) : (
            <div className="table-wrap">
              <table>
                <thead>
                  <tr>
                    <th>Date</th>
                    <th>Summary</th>
                    <th>Saved</th>
                  </tr>
                </thead>
                <tbody>
                  {savedBriefs.map((savedBrief) => (
                    <tr key={savedBrief.id}>
                      <td>{savedBrief.brief_date}</td>
                      <td>{savedBrief.summary}</td>
                      <td>{new Date(savedBrief.created_at).toLocaleString()}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </Panel>
        <Panel title="Top Events">
          {brief.top_events.length === 0 ? (
            <EmptyState label="No events in the brief." />
          ) : (
            <div className="brief-list">
              {brief.top_events.map((event) => (
                <article className="brief-item" key={event.id}>
                  <h3>{event.title}</h3>
                  <p>{event.description ?? "No description recorded."}</p>
                  <div className="meta-row">
                    <span>{event.company ?? "Unlinked company"}</span>
                    <span>{event.event_type}</span>
                    <span>{event.information_speed}</span>
                    <span>Priority {event.priority_score ?? "-"}</span>
                    <span>{event.source ?? "No source linked"}</span>
                  </div>
                </article>
              ))}
            </div>
          )}
        </Panel>
        <Panel title="Alerts">
          {brief.alerts.length === 0 ? (
            <EmptyState label="No alerts in the brief." />
          ) : (
            <div className="brief-list">
              {brief.alerts.map((alert) => (
                <article className="brief-item" key={alert.id}>
                  <h3>{alert.title}</h3>
                  <p>{alert.summary ?? "No summary recorded."}</p>
                  <div className="meta-row">
                    <span>{alert.company ?? "Unlinked company"}</span>
                    <span>{alert.severity}</span>
                    <span>{alert.confidence_bucket}</span>
                    <span>{alert.review_status}</span>
                  </div>
                </article>
              ))}
            </div>
          )}
        </Panel>
        <Panel title="Follow Up">
          <div className="brief-list">
            {brief.follow_up_questions.map((question) => (
              <div className="brief-item" key={question}>
                <p>{question}</p>
              </div>
            ))}
          </div>
        </Panel>
      </>
    );
  } catch {
    return (
      <>
        <PageHeader eyebrow="Daily output" title="Daily Intelligence Brief" />
        <ErrorState message="Could not load the daily brief from the backend API." />
      </>
    );
  }
}
