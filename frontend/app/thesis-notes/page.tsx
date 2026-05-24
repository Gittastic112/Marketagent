import { createThesisNote, deleteThesisNote, updateThesisNote } from "@/app/actions";
import { EmptyState, ErrorState, PageHeader, Panel } from "@/components/page";
import { fetchApi } from "@/lib/api";
import type { Company, ThesisNote } from "@/lib/api";

export default async function ThesisNotesPage() {
  try {
    const [thesisNotes, companies] = await Promise.all([
      fetchApi<ThesisNote[]>("/thesis-notes"),
      fetchApi<Company[]>("/companies")
    ]);

    return (
      <>
        <PageHeader eyebrow="Research memory" title="Thesis Notes" status={`${thesisNotes.length} notes`} />
        <Panel title="Add Thesis Note">
          <form action={createThesisNote} className="form-grid">
            <div className="field">
              <label htmlFor="company_id">Company</label>
              <select disabled={companies.length === 0} id="company_id" name="company_id" required>
                <option value="">Select company</option>
                {companies.map((company) => (
                  <option key={company.id} value={company.id}>
                    {company.ticker}
                  </option>
                ))}
              </select>
            </div>
            <div className="field">
              <label htmlFor="status">Status</label>
              <select defaultValue="active" id="status" name="status">
                <option value="active">active</option>
                <option value="inactive">inactive</option>
                <option value="archived">archived</option>
              </select>
            </div>
            <div className="field field-wide">
              <label htmlFor="title">Title</label>
              <input id="title" name="title" required />
            </div>
            <div className="field field-full">
              <label htmlFor="thesis_text">Thesis Text</label>
              <textarea id="thesis_text" name="thesis_text" required />
            </div>
            <div className="button-row">
              <button disabled={companies.length === 0} type="submit">Add thesis note</button>
            </div>
          </form>
        </Panel>
        <Panel title="Thesis Notes">
          {thesisNotes.length === 0 ? (
            <EmptyState label="No thesis notes yet." />
          ) : (
            <div className="table-wrap">
              <table>
                <thead>
                  <tr>
                    <th>Title</th>
                    <th>Company ID</th>
                    <th>Status</th>
                    <th>Text</th>
                    <th>Action</th>
                  </tr>
                </thead>
                <tbody>
                  {thesisNotes.map((note) => (
                    <tr key={note.id}>
                      <td>{note.title}</td>
                      <td>{note.company_id}</td>
                      <td>
                        <span className="badge">{note.status}</span>
                      </td>
                      <td>{note.thesis_text}</td>
                      <td>
                        <div className="action-stack">
                          <details className="edit-panel">
                            <summary>Edit</summary>
                            <form action={updateThesisNote} className="inline-form">
                              <input name="id" type="hidden" value={note.id} />
                              <div className="field">
                                <label htmlFor={`note-company-${note.id}`}>Company</label>
                                <select defaultValue={note.company_id} id={`note-company-${note.id}`} name="company_id" required>
                                  {companies.map((company) => (
                                    <option key={company.id} value={company.id}>
                                      {company.ticker}
                                    </option>
                                  ))}
                                </select>
                              </div>
                              <div className="field">
                                <label htmlFor={`note-status-${note.id}`}>Status</label>
                                <select defaultValue={note.status} id={`note-status-${note.id}`} name="status">
                                  <option value="active">active</option>
                                  <option value="inactive">inactive</option>
                                  <option value="archived">archived</option>
                                </select>
                              </div>
                              <div className="field field-full">
                                <label htmlFor={`note-title-${note.id}`}>Title</label>
                                <input defaultValue={note.title} id={`note-title-${note.id}`} name="title" required />
                              </div>
                              <div className="field field-full">
                                <label htmlFor={`note-text-${note.id}`}>Thesis Text</label>
                                <textarea defaultValue={note.thesis_text} id={`note-text-${note.id}`} name="thesis_text" required />
                              </div>
                              <div className="button-row">
                                <button className="secondary-button" type="submit">Save</button>
                              </div>
                            </form>
                          </details>
                          <form action={deleteThesisNote} className="row-action">
                            <input name="id" type="hidden" value={note.id} />
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
        <PageHeader eyebrow="Research memory" title="Thesis Notes" />
        <ErrorState message="Could not load thesis notes from the backend API." />
      </>
    );
  }
}
