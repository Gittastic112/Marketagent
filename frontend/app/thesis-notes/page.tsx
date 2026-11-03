import { RetainedActionForm } from "@/components/retained-action-form";
import { hasUsableData } from "@/lib/data-state-meta";
import Link from "next/link";
import { createThesisNote, deleteThesisNoteWithState, updateThesisNote } from "@/app/actions";
import { DeleteRecordForm } from "@/components/delete-record-form";
import { SelectField, TextAreaField, TextField } from "@/components/form-fields";
import { EmptyState, ErrorState, PageHeader, Panel } from "@/components/page";
import { DataStateNotices, ReviewStateBadge } from "@/components/ui/data-states";
import { serverFetchApiResponse } from "@/lib/server-api";
import type { Company, ThesisNote } from "@/lib/api";

export default async function ThesisNotesPage() {
  try {
    const [notesRes, companiesRes] = await Promise.all([
      serverFetchApiResponse<ThesisNote[]>("/thesis-notes"),
      serverFetchApiResponse<Company[]>("/companies")
    ]);
    const thesisNotes = notesRes.data || [];
    const companies = companiesRes.data || [];
    const companiesById = new Map(companies.map((c) => [c.id, c]));

    return (
      <>
        <PageHeader eyebrow="Research memory" title="Thesis Notes" status={hasUsableData(notesRes) ? `${thesisNotes.length} notes` : "Thesis notes unavailable"} />
        <DataStateNotices
          metas={[notesRes.meta, companiesRes.meta]}
          partialMessage="Company linkages failed to load. Thesis notes may display missing company names."
          mockMessage="Thesis note data is mocked. Treat affected thesis state as placeholder material."
        />
        <Panel title="Add Thesis Note">
          <RetainedActionForm label="Create thesis note" resetOnSuccess action={createThesisNote} className="form-grid">
            <SelectField disabled={companies.length === 0} id="company_id" label="Company" name="company_id" required>
              <option value="">Select company</option>
              {companies.map((company) => (
                <option key={company.id} value={company.id}>
                  {company.ticker}
                </option>
              ))}
            </SelectField>
            <SelectField defaultValue="active" id="status" label="Status" name="status">
              <option value="active">active</option>
              <option value="inactive">inactive</option>
              <option value="archived">archived</option>
            </SelectField>
            <TextField className="field field-wide" id="title" label="Title" name="title" required />
            <TextAreaField className="field field-full" id="thesis_text" label="Thesis Text" name="thesis_text" required />
            <div className="button-row">
              <button disabled={companies.length === 0} type="submit">Add thesis note</button>
            </div>
          </RetainedActionForm>
        </Panel>
        <Panel title="Thesis Notes">
          {!hasUsableData(notesRes) ? <ErrorState message="Thesis notes could not be loaded. Reload to retry." /> : thesisNotes.length === 0 ? (
            <EmptyState label="No thesis notes yet." />
          ) : (
            <div className="table-wrap">
              <table>
                <thead>
                  <tr>
                    <th>Title</th>
                    <th>Company</th>
                    <th>Status</th>
                    <th>Drift</th>
                    <th>Review</th>
                    <th>Text</th>
                    <th>Action</th>
                  </tr>
                </thead>
                <tbody>
                  {thesisNotes.map((note) => {
                    const ticker = companiesById.get(note.company_id)?.ticker ?? `#${note.company_id}`;
                    const driftBadge = note.thesis_drift_score > 0.5 ? "badge badge-warn" : "badge";
                    return (
                      <tr key={note.id}>
                        <td>
                          <Link href={`/thesis-notes/${note.id}`} style={{ color: "var(--accent)", fontWeight: 600 }}>
                            {note.title}
                          </Link>
                        </td>
                        <td>{ticker}</td>
                        <td>
                          <span className="badge">{note.status}</span>
                        </td>
                        <td>
                          <span className={driftBadge}>{note.thesis_drift_score.toFixed(2)}</span>
                        </td>
                        <td>
                          <ReviewStateBadge state={note.thesis_drift_score > 0.5 ? "needs_review" : "unreviewed"} />
                        </td>
                        <td style={{ maxWidth: "260px", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                          {note.thesis_text}
                        </td>
                        <td>
                          <div className="action-stack">
                            <details className="edit-panel">
                              <summary>Edit</summary>
                              <RetainedActionForm label="Update thesis note" action={updateThesisNote} className="inline-form">
                                <input name="id" type="hidden" value={note.id} />
                                <SelectField defaultValue={note.company_id} id={`note-company-${note.id}`} label="Company" name="company_id" required>
                                  {companies.map((company) => (
                                    <option key={company.id} value={company.id}>
                                      {company.ticker}
                                    </option>
                                  ))}
                                </SelectField>
                                <SelectField defaultValue={note.status} id={`note-status-${note.id}`} label="Status" name="status">
                                  <option value="active">active</option>
                                  <option value="inactive">inactive</option>
                                  <option value="archived">archived</option>
                                </SelectField>
                                <TextField className="field field-full" defaultValue={note.title} id={`note-title-${note.id}`} label="Title" name="title" required />
                                <TextAreaField className="field field-full" defaultValue={note.thesis_text} id={`note-text-${note.id}`} label="Thesis Text" name="thesis_text" required />
                                <div className="button-row">
                                  <button className="secondary-button" type="submit">Save</button>
                                </div>
                              </RetainedActionForm>
                            </details>
                            <DeleteRecordForm action={deleteThesisNoteWithState} recordId={note.id} />
                          </div>
                        </td>
                      </tr>
                    );
                  })}
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
        <PageHeader eyebrow="Research memory" title="Thesis Notes" />
        <ErrorState message="Could not load thesis notes from the backend API." />
      </>
    );
  }
}
