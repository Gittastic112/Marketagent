"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import { createRequestGate } from "@/lib/latest-request";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { ExternalLink } from "lucide-react";
import {
  FinancialExtractionCandidate,
  reviewFinancialCandidate,
  reviewFinancialCandidatePeriod,
  overrideFinancialCandidate,
  promoteFinancialCandidates,
  listExtractedFinancialCandidates,
} from "@/lib/api/financials";
import { financialEvidenceClaimType, financialEvidenceHref, financialEvidenceLocatorLabel, financialOverrideNotice } from "@/lib/financial-evidence";

export function FinancialCandidateReview({
  initialCandidates,
  companyId,
}: {
  initialCandidates: FinancialExtractionCandidate[];
  companyId: number;
}) {
  const router = useRouter();
  const promotionNoticeKey = `financial-candidate-promotion-${companyId}`;
  const [candidates, setCandidates] = useState(initialCandidates);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [editingId, setEditingId] = useState<number | null>(null);
  const [editValue, setEditValue] = useState<number | "">("");
  const [editUnit, setEditUnit] = useState("");
  const [periodId, setPeriodId] = useState<number | null>(null);
  const [periodEnd, setPeriodEnd] = useState("");
  const [periodNote, setPeriodNote] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const gate = useMemo(createRequestGate, [companyId]);
  const busy = useRef(false);
  useEffect(() => () => gate.invalidate(), [gate]);

  const unreviewedCount = candidates.filter((c) => c.review_status === "needs_review").length;
  const canPromote = candidates.some((c) => c.review_status === "reviewed" || c.review_status === "overridden");

  useEffect(() => {
    const storedNotice = window.sessionStorage.getItem(promotionNoticeKey);
    if (storedNotice) {
      setNotice(storedNotice);
      window.sessionStorage.removeItem(promotionNoticeKey);
    }
  }, [promotionNoticeKey]);

  async function handleReview(candidateId: number, status: "needs_review" | "reviewed" | "rejected") {
    if (busy.current) return;
    const candidate = candidates.find(item => item.id === candidateId);
    if (!candidate) return;
    busy.current = true; setIsSubmitting(true);
    const current = gate.begin();
    try {
      setError(null);
      const updated = await reviewFinancialCandidate(candidateId, status, candidate.updated_at);
      if (!current()) return;
      setCandidates(rows => rows.map((c) => (c.id === candidateId ? updated : c)));
      router.refresh();
    } catch (err) {
      if (current()) setError(err instanceof Error ? err.message : "Failed to update status");
    } finally {busy.current = false; if (current()) setIsSubmitting(false);}
  }

  async function handleOverride(candidateId: number) {
    if (busy.current || typeof editValue !== "number" || !Number.isFinite(editValue) || !editUnit.trim()) return;
    const candidate = candidates.find(item => item.id === candidateId);
    if (!candidate) return;
    busy.current = true; setIsSubmitting(true);
    const current = gate.begin();
    try {
      setError(null);
      const updated = await overrideFinancialCandidate(candidateId, editValue, editUnit.trim(), candidate.updated_at);
      if (!current()) return;
      setCandidates(rows => rows.map((c) => (c.id === candidateId ? updated : c)));
      setEditingId(null);
      setEditValue("");
      setEditUnit("");
      router.refresh();
    } catch (err) {
      if (current()) setError(err instanceof Error ? err.message : "Failed to override value");
    } finally {busy.current = false; if (current()) setIsSubmitting(false);}
  }

  async function handlePromote() {
    if (busy.current) return;
    busy.current = true;
    const current = gate.begin();
    setIsSubmitting(true);
    try {
      setError(null);
      setNotice(null);
      const result = await promoteFinancialCandidates(companyId, candidates.filter(c => c.review_status === "reviewed" || c.review_status === "overridden"));
      if (!current()) return;
      const successMessage = `Successfully promoted ${result.promoted_count} candidates.`;
      window.sessionStorage.setItem(promotionNoticeKey, successMessage);
      window.location.reload();
    } catch (err) {
      if (current()) setError(err instanceof Error ? err.message : "Failed to promote candidates");
    } finally {
      busy.current = false;
      if (current()) setIsSubmitting(false);
    }
  }

  async function savePeriod(candidate: FinancialExtractionCandidate) {
    if (busy.current || !periodEnd || periodNote.trim().length < 10) return;
    busy.current = true; setIsSubmitting(true); setError(null);
    const current = gate.begin();
    try {
      const updated = await reviewFinancialCandidatePeriod(candidate.id, periodEnd, periodNote, candidate.updated_at);
      if (!current()) return;
      setCandidates(rows => rows.map(row => row.id === updated.id ? updated : row));
      setPeriodId(null); setPeriodEnd(""); setPeriodNote("");
      setNotice("Period confirmation saved separately from the original extraction. Value review is unchanged.");
      router.refresh();
    } catch (err) {if (current()) setError(err instanceof Error ? err.message : "Period confirmation unavailable. Your entries are retained.");}
    finally {busy.current = false; if (current()) setIsSubmitting(false);}
  }

  async function reloadCandidates() {
    if (busy.current) return;
    busy.current = true; setIsSubmitting(true);
    const current = gate.begin();
    try {
      const rows = await listExtractedFinancialCandidates(companyId);
      if (!current()) return;
      setCandidates(rows); setEditingId(null); setEditValue(""); setEditUnit(""); setPeriodId(null); setPeriodEnd(""); setPeriodNote(""); setError(null);
      setNotice("Current candidates loaded. Review their source, value and unit before continuing.");
      router.refresh();
    } catch (err) {if (current()) setError(err instanceof Error ? err.message : "Candidates unavailable. Retry explicitly.");}
    finally {busy.current = false; if (current()) setIsSubmitting(false);}
  }

  if (candidates.length === 0) {
    return (
      <div className="space-y-4">
        {error ? <p className="text-sm text-[var(--danger)]" role="alert">{error}</p> : null}
        {notice ? <p className="text-sm text-[var(--success)]" role="status">{notice}</p> : null}
        <p className="text-sm text-muted-foreground">
          No candidates awaiting review. Add or select a filing to extract more source entries.
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <fieldset disabled={isSubmitting} style={{display: "contents"}}>
      <legend className="sr-only">Review extracted financial evidence</legend>
      {unreviewedCount > 0 && (
        <div className="rounded-md bg-yellow-50 p-4">
          <div className="flex">
            <div>
              <h3 className="text-sm font-medium text-yellow-800">Review Required</h3>
              <div className="mt-2 text-sm text-yellow-700">
                <p>
                  There {unreviewedCount === 1 ? "is" : "are"} {unreviewedCount} extraction{" "}
                  {unreviewedCount === 1 ? "candidate that needs" : "candidates that need"} review before{" "}
                  {unreviewedCount === 1 ? "it can" : "they can"} be promoted.
                </p>
              </div>
            </div>
          </div>
        </div>
      )}

      {error ? <div role="alert" className="text-sm text-[var(--danger)]">{error} <button type="button" className="btn btn-secondary" onClick={() => void reloadCandidates()}>Reload candidates (discard unsaved correction)</button></div> : null}
      {notice ? <p className="text-sm text-[var(--success)]" role="status">{notice}</p> : null}
      <p className="text-sm text-muted-foreground">Promotion accepts annual evidence with an exact source period-end date. Interim, YTD, missing dates and conflicting stored periods are held without changing history. Reviewing a value does not resolve its period identity.</p>

      <div className="-mx-4 -my-2 overflow-x-auto sm:-mx-6 lg:-mx-8" role="region" aria-label="Extracted financial candidates" tabIndex={0}>
        <div className="inline-block min-w-full py-2 align-middle sm:px-6 lg:px-8">
          <table className="min-w-full divide-y divide-border">
            <thead>
              <tr>
                <th scope="col" className="py-3.5 pl-4 pr-3 text-left text-sm font-semibold text-foreground">Metric</th>
                <th scope="col" className="px-3 py-3.5 text-left text-sm font-semibold text-foreground">Value</th>
                <th scope="col" className="px-3 py-3.5 text-left text-sm font-semibold text-foreground">Period</th>
                <th scope="col" className="px-3 py-3.5 text-left text-sm font-semibold text-foreground">Review Status</th>
                <th scope="col" className="px-3 py-3.5 text-left text-sm font-semibold text-foreground">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border">
              {candidates.map((candidate) => (
                <tr key={candidate.id}>
                  <td className="py-4 pl-4 pr-3 text-sm font-medium text-foreground" style={{ minWidth: "18rem", maxWidth: "32rem", overflowWrap: "anywhere" }}>
                    {candidate.metric_code.replaceAll("_", " ")}
                    <br />
                    <span className="text-xs font-normal text-muted-foreground">{financialEvidenceClaimType(candidate)}</span>
                    {financialOverrideNotice(candidate) && <p className="text-xs font-normal text-[var(--warning)] dark:text-[var(--warning)]">{financialOverrideNotice(candidate)}</p>}
                    <br />
                    <span className="text-xs font-normal text-muted-foreground">From: &quot;{candidate.source_text}&quot;</span>
                    <br />
                    <span className="text-xs font-normal text-muted-foreground">
                      {financialEvidenceLocatorLabel(candidate)}
                    </span>
                    <Link
                      href={financialEvidenceHref(candidate)}
                      target={candidate.source_locator_json?.type === "pdf_table_cell" ? "_blank" : undefined}
                      rel={candidate.source_locator_json?.type === "pdf_table_cell" ? "noopener noreferrer" : undefined}
                      className="mt-1 inline-flex items-center gap-1 text-xs font-medium text-[var(--accent)] hover:text-[var(--accent)]"
                    >
                      Open evidence
                      <ExternalLink aria-hidden="true" size={13} />
                    </Link>
                    {candidate.extraction_warnings ? (
                      <span className="mt-1 block text-xs font-normal text-[var(--warning)]">
                        {candidate.extraction_warnings.split(";").join(" / ")}
                      </span>
                    ) : null}
                  </td>
                  <td className="whitespace-nowrap px-3 py-4 text-sm text-foreground">
                    {editingId === candidate.id ? (
                      <div className="flex flex-wrap items-center gap-2">
                        <input
                          type="number"
                          step="any"
                          aria-label="Corrected value"
                          value={editValue}
                          onChange={(e) => setEditValue(e.target.value === "" ? "" : Number(e.target.value))}
                          className="block w-24 rounded-md border-0 py-1.5 text-foreground shadow-sm ring-1 ring-inset ring-border placeholder:text-muted-foreground focus:ring-2 focus:ring-inset focus:ring-[var(--accent)] sm:text-sm sm:leading-6"
                        />
                        <input
                          type="text"
                          aria-label="Reporting unit"
                          placeholder="e.g. INR crore"
                          value={editUnit}
                          onChange={(e) => setEditUnit(e.target.value)}
                          className="block w-32 rounded-md border-0 py-1.5 text-foreground shadow-sm ring-1 ring-inset ring-border placeholder:text-muted-foreground focus:ring-2 focus:ring-inset focus:ring-[var(--accent)] sm:text-sm sm:leading-6"
                        />
                        <button
                          onClick={() => handleOverride(candidate.id)}
                          disabled={typeof editValue !== "number" || !Number.isFinite(editValue) || !editUnit.trim()}
                          className="text-xs font-medium text-[var(--accent)] hover:text-[var(--accent)]"
                        >
                          Save
                        </button>
                        <button
                          onClick={() => {
                            setEditingId(null);
                            setEditValue("");
                            setEditUnit("");
                          }}
                          className="text-xs font-medium text-muted-foreground hover:text-muted-foreground"
                        >
                          Cancel
                        </button>
                      </div>
                    ) : (
                      <span>
                        {candidate.value.toLocaleString()} {candidate.unit || "unit missing"}
                      </span>
                    )}
                  </td>
                  <td className="px-3 py-4 text-sm text-muted-foreground">
                    <div>FY {candidate.fiscal_year ?? "unknown"} · {candidate.period_type || "Unknown basis"}</div>
                    <div>{typeof candidate.source_locator_json?.end === "string" ? `Ends ${candidate.source_locator_json.end}` : "Source extraction has no end date"}</div>
                    {typeof candidate.source_locator_json?.start === "string" && <div>Starts {candidate.source_locator_json.start}</div>}
                    {(() => {
                      const review = candidate.source_locator_json?.period_review;
                      return review && typeof review === "object" && "end" in review && typeof review.end === "string" ?
                        <div>User Assumption · Confirmed end {review.end}{"source_note" in review && typeof review.source_note === "string" && <div>{review.source_note}</div>}</div> : null;
                    })()}
                    {candidate.period_type === "annual" && candidate.fiscal_year !== null && !candidate.source_locator_json?.end && (
                      periodId === candidate.id ? <div style={{minWidth: "13rem"}}>
                        <label htmlFor={`period-end-${candidate.id}`}>Exact period end</label>
                        <input id={`period-end-${candidate.id}`} type="date" value={periodEnd} onChange={event => setPeriodEnd(event.target.value)} />
                        <label htmlFor={`period-note-${candidate.id}`}>Source location and explanation</label>
                        <textarea id={`period-note-${candidate.id}`} value={periodNote} onChange={event => setPeriodNote(event.target.value)} maxLength={1000} />
                        <p>Use the exact date from the source. Do not infer December 31 from the fiscal year.</p>
                        <button type="button" onClick={() => void savePeriod(candidate)} disabled={!periodEnd || periodNote.trim().length < 10}>Save period confirmation</button>
                        <button type="button" onClick={() => setPeriodId(null)}>Cancel period confirmation</button>
                      </div> : <button type="button" onClick={() => {
                        const review = candidate.source_locator_json?.period_review;
                        setPeriodId(candidate.id);
                        setPeriodEnd(review && typeof review === "object" && "end" in review && typeof review.end === "string" ? review.end : "");
                        setPeriodNote(review && typeof review === "object" && "source_note" in review && typeof review.source_note === "string" ? review.source_note : "");
                      }}>{candidate.source_locator_json?.period_review ? "Edit period confirmation" : "Confirm period end"}</button>
                    )}
                  </td>
                  <td className="whitespace-nowrap px-3 py-4 text-sm">
                    <span
                      className={`inline-flex items-center rounded-md px-2 py-1 text-xs font-medium ring-1 ring-inset ${
                        candidate.review_status === "reviewed" || candidate.review_status === "overridden"
                          ? "bg-[var(--success-bg)] text-[var(--success)] ring-[var(--success)]/20"
                          : candidate.review_status === "rejected"
                          ? "bg-[var(--danger-bg)] text-[var(--danger)] ring-[var(--danger)]/10"
                          : "bg-yellow-50 text-yellow-800 ring-yellow-600/20"
                      }`}
                    >
                      {candidate.review_status.replaceAll("_", " ")}
                    </span>
                  </td>
                  <td className="whitespace-nowrap px-3 py-4 text-sm text-muted-foreground">
                    {candidate.review_status === "needs_review" && editingId !== candidate.id && (
                      <div className="flex gap-3">
                        <button
                          onClick={() => {
                            if (!candidate.unit) {
                              setEditingId(candidate.id);
                              setEditValue(candidate.value);
                              setEditUnit("");
                              return;
                            }
                            void handleReview(candidate.id, "reviewed");
                          }}
                          className="text-[var(--success)] hover:text-[var(--success)] font-medium"
                        >
                          {candidate.unit ? "Accept" : "Add unit"}
                        </button>
                        <button
                          onClick={() => handleReview(candidate.id, "rejected")}
                          className="text-[var(--danger)] hover:text-[var(--danger)] font-medium"
                        >
                          Reject
                        </button>
                        <button
                          onClick={() => {
                            setEditingId(candidate.id);
                            setEditValue(candidate.value);
                            setEditUnit(candidate.unit || "");
                          }}
                          className="text-[var(--accent)] hover:text-[var(--accent)] font-medium"
                        >
                          Override
                        </button>
                      </div>
                    )}
                    {["reviewed", "overridden", "rejected"].includes(candidate.review_status) && editingId !== candidate.id && (
                       <div className="flex gap-3">
                         <button
                           onClick={() => handleReview(candidate.id, "needs_review")}
                           className="text-muted-foreground hover:text-foreground font-medium"
                         >
                           Undo
                         </button>
                       </div>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      <div className="flex justify-end border-t border-border pt-4">
        <button
          type="button"
          disabled={!canPromote || isSubmitting}
          onClick={handlePromote}
          className={`rounded-md bg-[var(--accent)] px-3 py-2 text-sm font-semibold text-white shadow-sm hover:bg-[var(--accent)] focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[var(--accent)] ${
            (!canPromote || isSubmitting) ? "opacity-50 cursor-not-allowed" : ""
          }`}
        >
          {isSubmitting ? "Saving review..." : "Promote Reviewed Candidates"}
        </button>
      </div>
      </fieldset>
    </div>
  );
}
