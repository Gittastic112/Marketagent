import { EmptyState, ErrorState, PageHeader, Panel } from "@/components/page";
import { fetchApi } from "@/lib/api";
import type { ThesisNote } from "@/lib/api";

export default async function ThesisNotesPage() {
  try {
    const thesisNotes = await fetchApi<ThesisNote[]>("/thesis-notes");

    return (
      <>
        <PageHeader eyebrow="Research memory" title="Thesis Notes" status={`${thesisNotes.length} notes`} />
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
