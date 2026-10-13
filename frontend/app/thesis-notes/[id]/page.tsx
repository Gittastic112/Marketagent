import { RetainedActionForm } from "@/components/retained-action-form";
import Link from "next/link";
import { createThesisAssumption, createThesisChange, deleteThesisAssumption, updateThesisAssumption } from "@/app/actions";
import { DeleteRecordForm } from "@/components/delete-record-form";
import { SelectField, TextAreaField, TextField } from "@/components/form-fields";
import { EmptyState, ErrorState, PageHeader, Panel } from "@/components/page";
import { DataStateNotices } from "@/components/ui/data-states";
import { serverFetchApiResponse } from "@/lib/server-api";
import type { Company, ThesisNote } from "@/lib/api";

async function createAssumptionAction(formData: FormData) {
  "use server";
  const thesisNoteId = formData.get("thesis_note_id") as string;
  await createThesisAssumption(formData, thesisNoteId);
}

async function updateAssumptionAction(formData: FormData) {
  "use server";
  const thesisNoteId = formData.get("thesis_note_id") as string;
  await updateThesisAssumption(formData, thesisNoteId);
}

async function deleteAssumptionAction(formData: FormData) {
  "use server";
  const thesisNoteId = formData.get("thesis_note_id") as string;
  await deleteThesisAssumption(formData, thesisNoteId);
}

async function createChangeAction(formData: FormData) {
  "use server";
  const thesisNoteId = formData.get("thesis_note_id") as string;
  await createThesisChange(formData, thesisNoteId);
}

const CONFIDENCE_LEVELS = ["low", "medium", "high"] as const;

function confidenceOptions() {
  return CONFIDENCE_LEVELS.map((level) => (
    <option key={level} value={level}>
      {level}
    </option>
  ));
}

function confidenceBadgeClass(level: string): string {
  if (level === "high") return "badge";
  if (level === "low") return "badge badge-warn";
  return "badge";
}

type ThesisNoteDetailProps = {
  params: Promise<{ id: string }>;
};

export default async function ThesisNoteDetailPage({ params }: ThesisNoteDetailProps) {
  try {
    const { id } = await params;
    const noteId = Number(id);
    const [noteRes, companiesRes] = await Promise.all([
      serverFetchApiResponse<ThesisNote>(`/thesis-notes/${noteId}`),
      serverFetchApiResponse<Company[]>("/companies")
    ]);
    const note = noteRes.data!;
    const companies = companiesRes.data || [];

    const company = companies.find((c) => c.id === note.company_id);
    const companyTicker = company?.ticker ?? `Company #${note.company_id}`;

    return (
      <>
        <PageHeader
          eyebrow={companyTicker}
          title={note.title}
          status={`Status: ${note.status} · Drift: ${note.thesis_drift_score.toFixed(2)}`}
        />
        <DataStateNotices
          metas={[noteRes.meta, companiesRes.meta]}
          partialMessage="Company linkages failed to load. The company name may not display correctly."
          mockMessage="This thesis detail view includes mock data. Treat affected assumptions as placeholders."
        />

        <div style={{ marginBottom: "12px" }}>
          <Link href="/thesis-notes" style={{ color: "var(--accent)", fontSize: "14px" }}>
            ← Back to Thesis Notes
          </Link>
        </div>

        {/* Thesis text */}
        <Panel title="Thesis">
          <div className="brief-list">
            <div className="brief-item">
              <p>{note.thesis_text}</p>
            </div>
          </div>
        </Panel>

        {/* Assumptions */}
        <Panel title="Assumptions">
          <RetainedActionForm label="Create assumption" resetOnSuccess action={createAssumptionAction} className="form-grid">
            <input name="thesis_note_id" type="hidden" value={note.id} />
            <TextAreaField className="field field-wide" id="new-assumption-desc" label="Description" name="description" required rows={2} />
            <SelectField defaultValue="medium" id="new-assumption-orig" label="Original Confidence" name="original_confidence">
              {confidenceOptions()}
            </SelectField>
            <SelectField defaultValue="medium" id="new-assumption-curr" label="Current Confidence" name="current_confidence">
              {confidenceOptions()}
            </SelectField>
            <div className="button-row">
              <button type="submit">Add Assumption</button>
            </div>
          </RetainedActionForm>
          {note.assumptions.length === 0 ? (
            <EmptyState label="No assumptions recorded yet." />
          ) : (
            <div className="table-wrap">
              <table>
                <thead>
                  <tr>
                    <th>Description</th>
                    <th>Original</th>
                    <th>Current</th>
                    <th>Action</th>
                  </tr>
                </thead>
                <tbody>
                  {note.assumptions.map((a) => (
                    <tr key={a.id}>
                      <td>{a.description}</td>
                      <td>
                        <span className={confidenceBadgeClass(a.original_confidence)}>{a.original_confidence}</span>
                      </td>
                      <td>
                        <span className={confidenceBadgeClass(a.current_confidence)}>{a.current_confidence}</span>
                      </td>
                      <td>
                        <div className="action-stack">
                          <details className="edit-panel">
                            <summary>Edit</summary>
                            <RetainedActionForm label="Update assumption" action={updateAssumptionAction} className="inline-form">
                              <input name="id" type="hidden" value={a.id} />
                              <input name="thesis_note_id" type="hidden" value={note.id} />
                              <TextAreaField className="field field-full" defaultValue={a.description} id={`edit-desc-${a.id}`} label="Description" name="description" required rows={2} />
                              <SelectField defaultValue={a.original_confidence} id={`edit-orig-${a.id}`} label="Original Confidence" name="original_confidence">
                                {confidenceOptions()}
                              </SelectField>
                              <SelectField defaultValue={a.current_confidence} id={`edit-curr-${a.id}`} label="Current Confidence" name="current_confidence">
                                {confidenceOptions()}
                              </SelectField>
                              <div className="button-row">
                                <button className="secondary-button" type="submit">Save</button>
                              </div>
                            </RetainedActionForm>
                          </details>
                          <RetainedActionForm label="Delete assumption" action={deleteAssumptionAction}>
                            <input name="id" type="hidden" value={a.id} />
                            <input name="thesis_note_id" type="hidden" value={note.id} />
                            <button className="danger-button" type="submit">Delete</button>
                          </RetainedActionForm>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </Panel>

        {/* Changes / Drift Log */}
        <Panel title="Change Log (Thesis Drift)">
          <RetainedActionForm label="Create change" resetOnSuccess action={createChangeAction} className="form-grid">
            <input name="thesis_note_id" type="hidden" value={note.id} />
            <TextAreaField className="field field-wide" id="new-change-summary" label="Change Summary" name="change_summary" required rows={2} />
            <TextField id="new-change-drift" label="Drift Score" name="drift_score" placeholder="0.0" type="number" />
            <div className="button-row">
              <button type="submit">Log Change</button>
            </div>
          </RetainedActionForm>
          {note.changes.length === 0 ? (
            <EmptyState label="No changes logged yet." />
          ) : (
            <div className="table-wrap">
              <table>
                <thead>
                  <tr>
                    <th>Change Summary</th>
                    <th>Drift</th>
                    <th>Date</th>
                  </tr>
                </thead>
                <tbody>
                  {note.changes.map((c) => (
                    <tr key={c.id}>
                      <td>{c.change_summary}</td>
                      <td>{c.drift_score.toFixed(2)}</td>
                      <td>{new Date(c.created_at).toLocaleDateString()}</td>
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
        <PageHeader eyebrow="Research memory" title="Thesis Note" />
        <ErrorState message="Could not load this thesis note." />
      </>
    );
  }
}
