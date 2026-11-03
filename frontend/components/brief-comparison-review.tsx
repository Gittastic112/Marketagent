"use client";

import Link from "next/link";
import { useCallback, useState } from "react";
import { fetchComparisonHistory, saveComparisonReview, type BriefTriage, type ComparisonReview,
  type ReviewDisposition, type TriageGroup } from "@/lib/api/brief-triage";
import { useLatestResource } from "@/lib/use-latest-resource";

export const dispositionLabels: Record<ReviewDisposition, string> = {
  investigate: "Investigate further", keep_input: "Keep input for now",
  revisit_input: "Revisit valuation input", not_relevant: "Not relevant to this input",
};

function ReviewHistory({ companyId, field, includeMock }: { companyId: number; field: string; includeMock: boolean }) {
  const [beforeId, setBeforeId] = useState<number | undefined>();
  const loader = useCallback(() => fetchComparisonHistory(companyId, field, includeMock, beforeId), [companyId, field, includeMock, beforeId]);
  const history = useLatestResource(loader);
  return <div aria-busy={history.status === "loading"}>
    {history.status === "loading" && <p role="status">Loading review history…</p>}
    {history.status === "error" && <p role="alert">History unavailable: {history.error}. <button className="btn btn-secondary" onClick={() => void history.reload().catch(() => {})}>Retry history</button></p>}
    {history.data && <>
      {!history.data.length && <p>No more saved reviews in this scope.</p>}
      <ul className="compact-list">{history.data.map(review => <li key={review.id}>
        <Link prefetch={false} href={`/daily-brief/triage/reviews/${review.id}`}>Version {review.version} · {dispositionLabels[review.disposition]}</Link>
        <span className="muted"> · {new Date(review.created_at).toLocaleString()} · {review.is_current ? "Current evidence basis" : "Changed evidence basis"}</span>
      </li>)}</ul>
      <div className="section-intro">
        {beforeId !== undefined && <button className="btn btn-secondary" onClick={() => setBeforeId(undefined)}>Newest reviews</button>}
        {history.data.length === 20 && <button className="btn btn-secondary" onClick={() => setBeforeId(history.data!.at(-1)!.id)}>Older reviews</button>}
      </div>
    </>}
  </div>;
}

export function BriefComparisonReview({ comparison, group, latest, onSaved }: {
  comparison: BriefTriage; group: TriageGroup; latest?: ComparisonReview; onSaved: () => Promise<void>;
}) {
  const [disposition, setDisposition] = useState<ReviewDisposition>("investigate");
  const [notes, setNotes] = useState("");
  const [confirmed, setConfirmed] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const [blocked, setBlocked] = useState(false);
  const [showHistory, setShowHistory] = useState(false);
  async function save(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (saving || blocked || !confirmed) return;
    setSaving(true); setError("");
    try {
      await saveComparisonReview({ company_id: comparison.company_id, field: group.field,
        include_mock: comparison.include_mock, evidence_hash: comparison.evidence_hash, expected_version: latest?.version ?? 0,
        disposition, notes: notes.trim(), evidence_reviewed: true });
      await onSaved();
    } catch (failure) {
      setError(failure instanceof Error ? failure.message : "Review could not be saved");
      // A lost response can follow a successful commit. Refresh instead of an
      // automatic retry that could record the same decision twice.
      setBlocked(true);
    } finally { setSaving(false); }
  }
  return <section className="triage-analyst-review" aria-label={`${group.label} analyst review`}>
    <h4>Record your review</h4>
    <p className="muted">User Assumption. This records your decision on the displayed evidence only. It does not approve AI output, verify facts or change any valuation input.</p>
    {comparison.include_mock && <p className="basis-note">Mock-inclusive scope. This review is kept separate from the non-mock comparison.</p>}
    {latest && <div className="basis-note">
      <strong>{latest.is_current ? "Latest decision on this evidence" : "Evidence changed since the last review"}: {dispositionLabels[latest.disposition]}</strong>
      <p className="preserve-whitespace">{latest.notes}</p>
      <Link prefetch={false} href={`/daily-brief/triage/reviews/${latest.id}`}>Open saved evidence receipt · version {latest.version}</Link>
      {!latest.is_current && <p>The old decision is historical. Review the current sources again before recording a new decision.</p>}
    </div>}
    <form onSubmit={save}>
      <fieldset disabled={saving || blocked}>
        <label>Decision for {group.label}<select value={disposition} onChange={event => setDisposition(event.target.value as ReviewDisposition)}>
          {Object.entries(dispositionLabels).map(([value, label]) => <option value={value} key={value}>{label}</option>)}
        </select></label>
        <label>Rationale for {group.label}<textarea value={notes} onChange={event => { setNotes(event.target.value); setConfirmed(false); }} minLength={10} maxLength={2000} required rows={3} placeholder="Explain the period, scope and evidence behind your decision." /></label>
        <label className="triage-checkbox"><input type="checkbox" checked={confirmed} onChange={event => setConfirmed(event.target.checked)} />I reviewed the displayed passages, source dates and coverage gaps for this input.</label>
        <button className="btn btn-primary" type="submit" disabled={!confirmed || notes.trim().length < 10}>{saving ? "Saving review…" : "Save analyst review"}</button>
      </fieldset>
    </form>
    {error && <p role="alert">{error}. Use Refresh comparison before trying again. No automatic retry was sent.</p>}
    <button className="btn btn-secondary" aria-expanded={showHistory} onClick={() => setShowHistory(!showHistory)}>{showHistory ? "Hide review history" : "Show review history"}</button>
    {showHistory && <ReviewHistory companyId={comparison.company_id} field={group.field} includeMock={comparison.include_mock} />}
  </section>;
}
