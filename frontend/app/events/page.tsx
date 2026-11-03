import { RetainedActionForm } from "@/components/retained-action-form";
import { hasUsableData } from "@/lib/data-state-meta";
import { createEvent, deleteEventWithState, extractEvents, updateEvent, addEventCorroboration, removeEventCorroboration, addEventContradiction, removeEventContradiction } from "@/app/actions";
import { DeleteRecordForm } from "@/components/delete-record-form";
import { SelectField, TextAreaField, TextField } from "@/components/form-fields";
import { EmptyState, ErrorState, PageHeader, Panel } from "@/components/page";
import { ScoreExplanationView } from "@/components/score-explanation";
import { ScoreBreakdown } from "@/components/score-breakdown";
import { DcfImpactPredictor } from "@/components/dcf-impact-predictor";
import { DataStateNotices, ConfidenceIndicator, SourceBadge } from "@/components/ui/data-states";
import { serverFetchApiResponse } from "@/lib/server-api";
import type { Company, EventRecord, RawDocument, ScoringConfig } from "@/lib/api";

export default async function EventsPage() {
  try {
    const [eventsRes, companiesRes, documentsRes, scoringConfigRes] = await Promise.all([
      serverFetchApiResponse<EventRecord[]>("/events"),
      serverFetchApiResponse<Company[]>("/companies"),
      serverFetchApiResponse<RawDocument[]>("/raw-documents/summaries"),
      serverFetchApiResponse<ScoringConfig>("/scoring-config")
    ]);
    const events = eventsRes.data || [];
    const companies = companiesRes.data || [];
    const documents = documentsRes.data || [];

    return (
      <>
        <PageHeader eyebrow="Normalized signal" title="Events" status={hasUsableData(eventsRes) ? `${events.length} events` : "Events unavailable"} />
        <DataStateNotices
          metas={[eventsRes.meta, companiesRes.meta, documentsRes.meta, scoringConfigRes.meta]}
          mockMessage="One or more event inputs are using mock data. Treat affected scores and signals as placeholders."
        />
        <Panel title="Extract Events">
          <RetainedActionForm label="Extract events" action={extractEvents} className="brief-list">
            <div className="brief-item">
              <div className="button-row">
                <button type="submit">Extract events</button>
              </div>
            </div>
          </RetainedActionForm>
        </Panel>
        <Panel title="Add Event">
          <RetainedActionForm label="Create event" resetOnSuccess action={createEvent} className="form-grid">
            <SelectField id="company_id" label="Company" name="company_id">
              <option value="">Unlinked</option>
              {companies.map((company) => (
                <option key={company.id} value={company.id}>
                  {company.ticker}
                </option>
              ))}
            </SelectField>
            <SelectField id="raw_document_id" label="Document" name="raw_document_id">
              <option value="">Unlinked</option>
              {documents.map((document) => (
                <option key={document.id} value={document.id}>
                  {document.title}
                </option>
              ))}
            </SelectField>
            <TextField id="event_type" label="Type" name="event_type" placeholder="filing" required />
            <TextField id="information_speed" label="Speed" name="information_speed" placeholder="fast" required />
            <TextField className="field field-wide" id="title" label="Title" name="title" required />
            <TextField id="credibility_score" label="Credibility" max="100" min="0" name="credibility_score" type="number" />
            <TextField id="novelty_score" label="Novelty" max="100" min="0" name="novelty_score" type="number" />
            <TextField id="impact_score" label="Impact" max="100" min="0" name="impact_score" type="number" />
            <TextField id="priority_score" label="Priority" max="100" min="0" name="priority_score" type="number" />
            <TextAreaField className="field field-full" id="description" label="Description" name="description" />
            <div className="button-row">
              <button type="submit">Add event</button>
            </div>
          </RetainedActionForm>
        </Panel>
        <Panel title="Events">
          {!hasUsableData(eventsRes) ? <ErrorState message="Events could not be loaded. Reload to retry." /> : events.length === 0 ? (
            <EmptyState label="No events yet." />
          ) : (
            <div className="table-wrap">
              <table>
                <thead>
                  <tr>
                    <th>Title</th>
                    <th>Type</th>
                    <th>Speed</th>
                    <th>Source</th>
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
                      <td>
                        <SourceBadge source={
                          documents.find(d => d.id === event.raw_document_id)?.document_type?.replace("_", " ") || "manual"
                        } />
                      </td>
                      <td>
                        <div style={{ display: "flex", flexDirection: "column", gap: "0.25rem" }}>
                          <span>{event.credibility_score ?? "-"}</span>
                          <ConfidenceIndicator level={
                            event.credibility_score === null ? "none" :
                            event.credibility_score >= 70 ? "high" :
                            event.credibility_score >= 40 ? "medium" : "low"
                          } />
                        </div>
                      </td>
                      <td>{event.novelty_score ?? "-"}</td>
                      <td>{event.impact_score ?? "-"}</td>
                      <td>{event.priority_score ?? "-"}</td>
                      <td>
                        <div className="action-stack">
                          <details className="edit-panel">
                            <summary>Score Breakdown</summary>
                            <ScoreBreakdown score={event.priority_score ?? 0} explanation={event.score_explanation_json} />
                            <div style={{ marginTop: "0.75rem" }}>
                              <ScoreExplanationView explanation={event.score_explanation_json} />
                            </div>
                          </details>
                          <details className="edit-panel">
                            <summary>Edit</summary>
                            <RetainedActionForm label="Update event" action={updateEvent} className="inline-form">
                              <input name="id" type="hidden" value={event.id} />
                              <SelectField defaultValue={event.company_id ?? ""} id={`event-company-${event.id}`} label="Company" name="company_id">
                                <option value="">Unlinked</option>
                                {companies.map((company) => (
                                  <option key={company.id} value={company.id}>
                                    {company.ticker}
                                  </option>
                                ))}
                              </SelectField>
                              <SelectField defaultValue={event.raw_document_id ?? ""} id={`event-doc-${event.id}`} label="Document" name="raw_document_id">
                                <option value="">Unlinked</option>
                                {documents.map((document) => (
                                  <option key={document.id} value={document.id}>
                                    {document.title}
                                  </option>
                                ))}
                              </SelectField>
                              <TextField defaultValue={event.event_type} id={`event-type-${event.id}`} label="Type" name="event_type" required />
                              <TextField defaultValue={event.information_speed} id={`event-speed-${event.id}`} label="Speed" name="information_speed" required />
                              <TextField className="field field-full" defaultValue={event.title} id={`event-title-${event.id}`} label="Title" name="title" required />
                              <TextField defaultValue={event.credibility_score ?? ""} id={`event-cred-${event.id}`} label="Credibility" max="100" min="0" name="credibility_score" type="number" />
                              <TextField defaultValue={event.novelty_score ?? ""} id={`event-novelty-${event.id}`} label="Novelty" max="100" min="0" name="novelty_score" type="number" />
                              <TextField defaultValue={event.impact_score ?? ""} id={`event-impact-${event.id}`} label="Impact" max="100" min="0" name="impact_score" type="number" />
                              <TextField defaultValue={event.priority_score ?? ""} id={`event-priority-${event.id}`} label="Priority" max="100" min="0" name="priority_score" type="number" />
                              <TextAreaField className="field field-full" defaultValue={event.description ?? ""} id={`event-desc-${event.id}`} label="Description" name="description" />
                              <div className="button-row">
                                <button className="secondary-button" type="submit">Save</button>
                              </div>
                            </RetainedActionForm>
                          </details>
                          <details className="edit-panel event-ai-panel">
                            <summary>DCF Impact Prediction</summary>
                            <DcfImpactPredictor eventId={event.id} eventText={`${event.title}\n${event.description || ""}`} />
                          </details>
                          <details className="edit-panel">
                            <summary>Corroboration & Contradiction</summary>
                            <div className="section-block">
                              <h4>Corroborating Events</h4>
                              {event.corroborates && event.corroborates.length > 0 ? (
                                <ul className="text-sm">
                                  {event.corroborates.map((c) => (
                                    <li key={c.id}>
                                      {c.title}
                                      <RetainedActionForm label="Remove event corroboration" action={removeEventCorroboration} className="inline-form" style={{display: 'inline', marginLeft: '8px'}}>
                                        <input type="hidden" name="event_id" value={event.id} />
                                        <input type="hidden" name="target_event_id" value={c.id} />
                                        <button type="submit" className="text-red-500" title="Remove link">✕</button>
                                      </RetainedActionForm>
                                    </li>
                                  ))}
                                </ul>
                              ) : (
                                <p className="text-sm text-gray-500">No corroborating events.</p>
                              )}
                              <RetainedActionForm label="Add event corroboration" action={addEventCorroboration} className="inline-form mt-2">
                                <input type="hidden" name="event_id" value={event.id} />
                                <SelectField id={`add-corr-${event.id}`} label="" name="target_event_id" required>
                                  <option value="">Select event...</option>
                                  {events.filter((e) => e.id !== event.id).map((e) => (
                                    <option key={e.id} value={e.id}>{e.title}</option>
                                  ))}
                                </SelectField>
                                <button type="submit" className="secondary-button text-sm">Add Corroboration</button>
                              </RetainedActionForm>
                            </div>

                            <div className="section-block mt-4">
                              <h4>Contradicting Events</h4>
                              {event.contradicts && event.contradicts.length > 0 ? (
                                <ul className="text-sm">
                                  {event.contradicts.map((c) => (
                                    <li key={c.id}>
                                      {c.title}
                                      <RetainedActionForm label="Remove event contradiction" action={removeEventContradiction} className="inline-form" style={{display: 'inline', marginLeft: '8px'}}>
                                        <input type="hidden" name="event_id" value={event.id} />
                                        <input type="hidden" name="target_event_id" value={c.id} />
                                        <button type="submit" className="text-red-500" title="Remove link">✕</button>
                                      </RetainedActionForm>
                                    </li>
                                  ))}
                                </ul>
                              ) : (
                                <p className="text-sm text-gray-500">No contradicting events.</p>
                              )}
                              <RetainedActionForm label="Add event contradiction" action={addEventContradiction} className="inline-form mt-2">
                                <input type="hidden" name="event_id" value={event.id} />
                                <SelectField id={`add-contra-${event.id}`} label="" name="target_event_id" required>
                                  <option value="">Select event...</option>
                                  {events.filter((e) => e.id !== event.id).map((e) => (
                                    <option key={e.id} value={e.id}>{e.title}</option>
                                  ))}
                                </SelectField>
                                <button type="submit" className="secondary-button text-sm">Add Contradiction</button>
                              </RetainedActionForm>
                            </div>
                          </details>
                          <DeleteRecordForm action={deleteEventWithState} recordId={event.id} />
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
