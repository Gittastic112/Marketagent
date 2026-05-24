import { createAlert, deleteAlert, updateAlert } from "@/app/actions";
import { EmptyState, ErrorState, PageHeader, Panel } from "@/components/page";
import { fetchApi } from "@/lib/api";
import type { AlertRecord, Company, EventRecord } from "@/lib/api";

export default async function AlertsPage() {
  try {
    const [alerts, companies, events] = await Promise.all([
      fetchApi<AlertRecord[]>("/alerts"),
      fetchApi<Company[]>("/companies"),
      fetchApi<EventRecord[]>("/events")
    ]);

    return (
      <>
        <PageHeader eyebrow="Review queue" title="Alerts" status={`${alerts.length} alerts`} />
        <Panel title="Add Alert">
          <form action={createAlert} className="form-grid">
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
              <label htmlFor="event_id">Event</label>
              <select id="event_id" name="event_id">
                <option value="">Unlinked</option>
                {events.map((event) => (
                  <option key={event.id} value={event.id}>
                    {event.title}
                  </option>
                ))}
              </select>
            </div>
            <div className="field">
              <label htmlFor="alert_type">Type</label>
              <input id="alert_type" name="alert_type" placeholder="thesis_watch" required />
            </div>
            <div className="field">
              <label htmlFor="severity">Severity</label>
              <select defaultValue="low" id="severity" name="severity">
                <option value="low">low</option>
                <option value="medium">medium</option>
                <option value="high">high</option>
              </select>
            </div>
            <div className="field field-wide">
              <label htmlFor="title">Title</label>
              <input id="title" name="title" required />
            </div>
            <div className="field">
              <label htmlFor="confidence_bucket">Confidence</label>
              <select defaultValue="low" id="confidence_bucket" name="confidence_bucket">
                <option value="low">low</option>
                <option value="medium">medium</option>
                <option value="high">high</option>
              </select>
            </div>
            <div className="field">
              <label htmlFor="review_status">Review</label>
              <select defaultValue="unreviewed" id="review_status" name="review_status">
                <option value="unreviewed">unreviewed</option>
                <option value="reviewed">reviewed</option>
                <option value="dismissed">dismissed</option>
              </select>
            </div>
            <div className="field field-full">
              <label htmlFor="summary">Summary</label>
              <textarea id="summary" name="summary" />
            </div>
            <div className="field field-full">
              <label htmlFor="why_it_matters">Why It Matters</label>
              <textarea id="why_it_matters" name="why_it_matters" />
            </div>
            <div className="button-row">
              <button type="submit">Add alert</button>
            </div>
          </form>
        </Panel>
        <Panel title="Alerts">
          {alerts.length === 0 ? (
            <EmptyState label="No alerts yet." />
          ) : (
            <div className="table-wrap">
              <table>
                <thead>
                  <tr>
                    <th>Title</th>
                    <th>Type</th>
                    <th>Severity</th>
                    <th>Confidence</th>
                    <th>Review</th>
                    <th>Action</th>
                  </tr>
                </thead>
                <tbody>
                  {alerts.map((alert) => (
                    <tr key={alert.id}>
                      <td>{alert.title}</td>
                      <td>{alert.alert_type}</td>
                      <td>{alert.severity}</td>
                      <td>{alert.confidence_bucket}</td>
                      <td>
                        <span className="badge">{alert.review_status}</span>
                      </td>
                      <td>
                        <div className="action-stack">
                          <details className="edit-panel">
                            <summary>Edit</summary>
                            <form action={updateAlert} className="inline-form">
                              <input name="id" type="hidden" value={alert.id} />
                              <div className="field">
                                <label htmlFor={`alert-company-${alert.id}`}>Company</label>
                                <select defaultValue={alert.company_id ?? ""} id={`alert-company-${alert.id}`} name="company_id">
                                  <option value="">Unlinked</option>
                                  {companies.map((company) => (
                                    <option key={company.id} value={company.id}>
                                      {company.ticker}
                                    </option>
                                  ))}
                                </select>
                              </div>
                              <div className="field">
                                <label htmlFor={`alert-event-${alert.id}`}>Event</label>
                                <select defaultValue={alert.event_id ?? ""} id={`alert-event-${alert.id}`} name="event_id">
                                  <option value="">Unlinked</option>
                                  {events.map((event) => (
                                    <option key={event.id} value={event.id}>
                                      {event.title}
                                    </option>
                                  ))}
                                </select>
                              </div>
                              <div className="field">
                                <label htmlFor={`alert-type-${alert.id}`}>Type</label>
                                <input defaultValue={alert.alert_type} id={`alert-type-${alert.id}`} name="alert_type" required />
                              </div>
                              <div className="field">
                                <label htmlFor={`alert-severity-${alert.id}`}>Severity</label>
                                <select defaultValue={alert.severity} id={`alert-severity-${alert.id}`} name="severity">
                                  <option value="low">low</option>
                                  <option value="medium">medium</option>
                                  <option value="high">high</option>
                                </select>
                              </div>
                              <div className="field field-full">
                                <label htmlFor={`alert-title-${alert.id}`}>Title</label>
                                <input defaultValue={alert.title} id={`alert-title-${alert.id}`} name="title" required />
                              </div>
                              <div className="field">
                                <label htmlFor={`alert-confidence-${alert.id}`}>Confidence</label>
                                <select defaultValue={alert.confidence_bucket} id={`alert-confidence-${alert.id}`} name="confidence_bucket">
                                  <option value="low">low</option>
                                  <option value="medium">medium</option>
                                  <option value="high">high</option>
                                </select>
                              </div>
                              <div className="field">
                                <label htmlFor={`alert-review-${alert.id}`}>Review</label>
                                <select defaultValue={alert.review_status} id={`alert-review-${alert.id}`} name="review_status">
                                  <option value="unreviewed">unreviewed</option>
                                  <option value="reviewed">reviewed</option>
                                  <option value="dismissed">dismissed</option>
                                </select>
                              </div>
                              <div className="field field-full">
                                <label htmlFor={`alert-summary-${alert.id}`}>Summary</label>
                                <textarea defaultValue={alert.summary ?? ""} id={`alert-summary-${alert.id}`} name="summary" />
                              </div>
                              <div className="field field-full">
                                <label htmlFor={`alert-why-${alert.id}`}>Why It Matters</label>
                                <textarea defaultValue={alert.why_it_matters ?? ""} id={`alert-why-${alert.id}`} name="why_it_matters" />
                              </div>
                              <div className="button-row">
                                <button className="secondary-button" type="submit">Save</button>
                              </div>
                            </form>
                          </details>
                          <form action={deleteAlert} className="row-action">
                            <input name="id" type="hidden" value={alert.id} />
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
        <PageHeader eyebrow="Review queue" title="Alerts" />
        <ErrorState message="Could not load alerts from the backend API." />
      </>
    );
  }
}
