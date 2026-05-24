import { createEvent, deleteEvent, extractEvents, updateEvent } from "@/app/actions";
import { EmptyState, ErrorState, PageHeader, Panel } from "@/components/page";
import { fetchApi } from "@/lib/api";
import type { Company, EventRecord, RawDocument } from "@/lib/api";

export default async function EventsPage() {
  try {
    const [events, companies, documents] = await Promise.all([
      fetchApi<EventRecord[]>("/events"),
      fetchApi<Company[]>("/companies"),
      fetchApi<RawDocument[]>("/raw-documents")
    ]);

    return (
      <>
        <PageHeader eyebrow="Normalized signal" title="Events" status={`${events.length} events`} />
        <Panel title="Extract Events">
          <form action={extractEvents} className="brief-list">
            <div className="brief-item">
              <div className="button-row">
                <button type="submit">Extract events</button>
              </div>
            </div>
          </form>
        </Panel>
        <Panel title="Add Event">
          <form action={createEvent} className="form-grid">
            <div className="field">
              <label htmlFor="company_id">Company</label>
              <select id="company_id" name="company_id">
                <option value="">Unlinked</option>
                {companies.map((company) => (
                  <option key={company.id} value={company.id}>
                    {company.ticker}
                  </option>
                ))}
              </select>
            </div>
            <div className="field">
              <label htmlFor="raw_document_id">Document</label>
              <select id="raw_document_id" name="raw_document_id">
                <option value="">Unlinked</option>
                {documents.map((document) => (
                  <option key={document.id} value={document.id}>
                    {document.title}
                  </option>
                ))}
              </select>
            </div>
            <div className="field">
              <label htmlFor="event_type">Type</label>
              <input id="event_type" name="event_type" placeholder="filing" required />
            </div>
            <div className="field">
              <label htmlFor="information_speed">Speed</label>
              <input id="information_speed" name="information_speed" placeholder="fast" required />
            </div>
            <div className="field field-wide">
              <label htmlFor="title">Title</label>
              <input id="title" name="title" required />
            </div>
            <div className="field">
              <label htmlFor="credibility_score">Credibility</label>
              <input id="credibility_score" max="100" min="0" name="credibility_score" type="number" />
            </div>
            <div className="field">
              <label htmlFor="novelty_score">Novelty</label>
              <input id="novelty_score" max="100" min="0" name="novelty_score" type="number" />
            </div>
            <div className="field">
              <label htmlFor="impact_score">Impact</label>
              <input id="impact_score" max="100" min="0" name="impact_score" type="number" />
            </div>
            <div className="field">
              <label htmlFor="priority_score">Priority</label>
              <input id="priority_score" max="100" min="0" name="priority_score" type="number" />
            </div>
            <div className="field field-full">
              <label htmlFor="description">Description</label>
              <textarea id="description" name="description" />
            </div>
            <div className="button-row">
              <button type="submit">Add event</button>
            </div>
          </form>
        </Panel>
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
                    <th>Action</th>
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
                      <td>
                        <div className="action-stack">
                          <details className="edit-panel">
                            <summary>Edit</summary>
                            <form action={updateEvent} className="inline-form">
                              <input name="id" type="hidden" value={event.id} />
                              <div className="field">
                                <label htmlFor={`event-company-${event.id}`}>Company</label>
                                <select defaultValue={event.company_id ?? ""} id={`event-company-${event.id}`} name="company_id">
                                  <option value="">Unlinked</option>
                                  {companies.map((company) => (
                                    <option key={company.id} value={company.id}>
                                      {company.ticker}
                                    </option>
                                  ))}
                                </select>
                              </div>
                              <div className="field">
                                <label htmlFor={`event-doc-${event.id}`}>Document</label>
                                <select defaultValue={event.raw_document_id ?? ""} id={`event-doc-${event.id}`} name="raw_document_id">
                                  <option value="">Unlinked</option>
                                  {documents.map((document) => (
                                    <option key={document.id} value={document.id}>
                                      {document.title}
                                    </option>
                                  ))}
                                </select>
                              </div>
                              <div className="field">
                                <label htmlFor={`event-type-${event.id}`}>Type</label>
                                <input defaultValue={event.event_type} id={`event-type-${event.id}`} name="event_type" required />
                              </div>
                              <div className="field">
                                <label htmlFor={`event-speed-${event.id}`}>Speed</label>
                                <input defaultValue={event.information_speed} id={`event-speed-${event.id}`} name="information_speed" required />
                              </div>
                              <div className="field field-full">
                                <label htmlFor={`event-title-${event.id}`}>Title</label>
                                <input defaultValue={event.title} id={`event-title-${event.id}`} name="title" required />
                              </div>
                              <div className="field">
                                <label htmlFor={`event-cred-${event.id}`}>Credibility</label>
                                <input defaultValue={event.credibility_score ?? ""} id={`event-cred-${event.id}`} max="100" min="0" name="credibility_score" type="number" />
                              </div>
                              <div className="field">
                                <label htmlFor={`event-novelty-${event.id}`}>Novelty</label>
                                <input defaultValue={event.novelty_score ?? ""} id={`event-novelty-${event.id}`} max="100" min="0" name="novelty_score" type="number" />
                              </div>
                              <div className="field">
                                <label htmlFor={`event-impact-${event.id}`}>Impact</label>
                                <input defaultValue={event.impact_score ?? ""} id={`event-impact-${event.id}`} max="100" min="0" name="impact_score" type="number" />
                              </div>
                              <div className="field">
                                <label htmlFor={`event-priority-${event.id}`}>Priority</label>
                                <input defaultValue={event.priority_score ?? ""} id={`event-priority-${event.id}`} max="100" min="0" name="priority_score" type="number" />
                              </div>
                              <div className="field field-full">
                                <label htmlFor={`event-desc-${event.id}`}>Description</label>
                                <textarea defaultValue={event.description ?? ""} id={`event-desc-${event.id}`} name="description" />
                              </div>
                              <div className="button-row">
                                <button className="secondary-button" type="submit">Save</button>
                              </div>
                            </form>
                          </details>
                          <form action={deleteEvent} className="row-action">
                            <input name="id" type="hidden" value={event.id} />
                            <button className="danger-button" type="submit">Delete</button>
                          </form>
                        </div>
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
        <PageHeader eyebrow="Normalized signal" title="Events" />
        <ErrorState message="Could not load events from the backend API." />
      </>
    );
  }
}
