"use client";

import { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { createRequestGate } from "@/lib/latest-request";

import {
  applyCitationCandidate,
  applyManualCitationEdit,
  buildCitationValidationPayload,
  initialCitationDrafts,
  readableCitations,
  readableEvaluation,
} from "@/lib/ai-citation-suggestions";
import {
  type AiCitationSuggestion,
  type AiOutput,
  fetchAiCitationSuggestions,
  patchApi,
  postApi,
} from "@/lib/api";

type Props = {
  initialOutput: AiOutput;
};

export function AiOutputReviewControls({ initialOutput }: Props) {
  const router = useRouter();
  const requests = useMemo(() => createRequestGate(), [initialOutput.id]);
  useEffect(() => () => requests.invalidate(), [requests]);
  const [output, setOutput] = useState(initialOutput);
  const [drafts, setDrafts] = useState(() => initialCitationDrafts(initialOutput));
  const [suggestions, setSuggestions] = useState<AiCitationSuggestion[] | null>(null);
  const [suggestionError, setSuggestionError] = useState<string | null>(null);
  const [notes, setNotes] = useState(initialOutput.review_notes ?? "");
  const [message, setMessage] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const citedSourceIds = Array.from(
    output.output_text.matchAll(/\[source_id:([^\]]+)\]/g),
    (match) => match[1].trim(),
  ).filter((source, index, sources) => source.startsWith("raw_document:") && sources.indexOf(source) === index);
  const citationPayload = buildCitationValidationPayload(citedSourceIds, drafts);
  const evaluation = readableEvaluation(output);

  async function loadSuggestions() {
    const isCurrent = requests.begin();
    setBusy(true);
    setSuggestionError(null);
    try {
      const matches = await fetchAiCitationSuggestions(output.id);
      if (isCurrent()) setSuggestions(matches);
    } catch (error) {
      if (isCurrent()) setSuggestionError(
        error instanceof Error ? error.message : "Exact-passage suggestions are unavailable.",
      );
    } finally {
      if (isCurrent()) setBusy(false);
    }
  }

  async function validateCitation() {
    if (!citationPayload) return;
    const isCurrent = requests.begin();
    setBusy(true);
    setMessage(null);
    try {
      const updated = await postApi<AiOutput>(
        `/ai-outputs/${output.id}/citations/validate`,
        citationPayload,
      );
      if (!isCurrent()) return;
      setOutput(updated);
      setMessage(updated.citation_validation_status === "valid" ? "Exact citation verified." : "Citation could not be verified.");
    } catch (error) {
      if (isCurrent()) setMessage(error instanceof Error ? error.message : "Citation validation failed.");
    } finally {
      if (isCurrent()) setBusy(false);
    }
  }

  async function review(status: "approved" | "rejected" | "needs_revision") {
    const isCurrent = requests.begin();
    setBusy(true);
    setMessage(null);
    try {
      const updated = await patchApi<AiOutput>(`/ai-outputs/${output.id}/review`, {
        status,
        notes: notes.trim() || null,
      });
      if (!isCurrent()) return;
      setOutput(updated);
      setMessage(`Review saved as ${status.replace("_", " ")}.`);
      router.refresh();
    } catch (error) {
      if (isCurrent()) setMessage(error instanceof Error ? error.message : "Review could not be saved.");
    } finally {
      if (isCurrent()) setBusy(false);
    }
  }

  return (
    <section aria-label="AI evidence and review" style={{ display: "grid", gap: "1rem" }}>
      <div>
        <h4 style={{ marginBottom: "0.5rem", color: "var(--text-secondary)" }}>Evidence</h4>
        <p><strong>Citation status:</strong> {output.citation_validation_status.replace("_", " ")}</p>
        <p className="muted">
          Suggestions are deterministic lexical matches from stored text. Selecting one does not
          validate the claim or approve this output.
        </p>
        {output.is_mock ? <span className="badge badge-warn">Mock Data context</span> : null}
        <button
          className="btn btn-secondary"
          type="button"
          disabled={busy || citedSourceIds.length === 0}
          onClick={loadSuggestions}
        >
          {busy && suggestions === null ? "Finding passages..." : "Find exact passage candidates"}
        </button>
        {suggestionError ? <p role="alert">{suggestionError}</p> : null}
        {suggestions?.map((suggestion) => (
          <section
            aria-label={`Passage candidates for ${suggestion.source_id}`}
            key={suggestion.source_id}
            className="citation-suggestion-group"
          >
            <div className="briefing-card-heading">
              <div>
                <span className="eyebrow">Stored source candidate</span>
                <h5>{suggestion.source_title || suggestion.source_id}</h5>
              </div>
              <span className={`badge ${suggestion.status === "ready" ? "badge-outline" : "badge-warn"}`}>
                {suggestion.status.replaceAll("_", " ")}
              </span>
            </div>
            {suggestion.claim_text ? <p><strong>Generated claim:</strong> {suggestion.claim_text}</p> : null}
            {suggestion.candidates.length === 0 ? (
              <p className="muted">No exact-passage candidate is ready. Review the stored source manually.</p>
            ) : (
              <div className="citation-suggestion-list">
                {suggestion.candidates.map((candidate) => (
                  <article key={`${suggestion.source_id}-${candidate.start_char}-${candidate.end_char}`}>
                    <div className="briefing-meta-row">
                      <span>{candidate.confidence} match</span>
                      <span>{Math.round(candidate.score * 100)}% match score</span>
                      <span>{candidate.matched_term_count}/{candidate.claim_term_count} terms</span>
                    </div>
                    <blockquote>{candidate.quote}</blockquote>
                    <div className="button-row">
                      <button
                        className="btn btn-secondary"
                        type="button"
                        disabled={busy}
                        onClick={() => setDrafts((current) => applyCitationCandidate(
                          current,
                          suggestion.source_id,
                          candidate,
                        ))}
                      >
                        Use this passage
                      </button>
                      <Link className="text-link" href={candidate.internal_href}>Open stored source</Link>
                    </div>
                  </article>
                ))}
              </div>
            )}
            <ul className="compact-list">
              {suggestion.limitations.map((limitation) => <li key={limitation}>{limitation}</li>)}
            </ul>
          </section>
        ))}
        {citedSourceIds.length === 0 ? (
          <p style={{ color: "var(--danger)" }}>Blocked: the output has no supported raw-document source markers.</p>
        ) : citedSourceIds.map((source) => (
          <label key={source} style={{ display: "grid", gap: "0.35rem", marginTop: "0.75rem" }}>
            Exact supporting passage for {source}
            <textarea
              value={drafts[source]?.quote ?? ""}
              onChange={(event) => setDrafts((current) => applyManualCitationEdit(
                current,
                source,
                event.target.value,
              ))}
              rows={3}
              placeholder="Paste the exact supporting passage from the stored source"
            />
          </label>
        ))}
        <button
          className="btn btn-primary"
          type="button"
          disabled={busy || !citationPayload}
          onClick={validateCitation}
        >
          Validate all cited sources
        </button>
        {readableCitations(output).map((citation, index) => (
          <p key={`${citation.source_id}-${index}`} style={{ marginTop: "0.5rem" }}>
            <strong>{citation.status}:</strong> {citation.quote}
            {citation.reason ? ` (${citation.reason})` : ""}
            {citation.internal_href ? <> <Link href={citation.internal_href}>Open source</Link></> : null}
          </p>
        ))}
      </div>

      <div>
        <h4 style={{ marginBottom: "0.5rem", color: "var(--text-secondary)" }}>Human review</h4>
        <p><strong>Status:</strong> {output.human_review_status.replace("_", " ")}</p>
        <p><strong>Automated checks:</strong> {evaluation.passed ? "passed" : "not passed"}</p>
        <p className="muted">Automated scope: source citations and policy checks only. Interpretation quality is not evaluated. Review numbers, periods, causal claims and source-text instructions before approving; an exact quote does not prove the claim.</p>
        {output.evaluation_json && !evaluation.passed ? (
          <ul>
            {evaluation.failedChecks.map(name => <li key={name}>{name.replaceAll("_", " ")}</li>)}
          </ul>
        ) : null}
        <label style={{ display: "grid", gap: "0.35rem", marginTop: "0.75rem" }}>
          Review notes
          <textarea value={notes} onChange={(event) => setNotes(event.target.value)} rows={3} />
        </label>
        <div style={{ display: "flex", flexWrap: "wrap", gap: "0.5rem" }}>
          <button className="btn btn-primary" type="button" disabled={busy || !evaluation.passed} onClick={() => review("approved")}>Approve</button>
          <button className="btn btn-secondary" type="button" disabled={busy || !notes.trim()} onClick={() => review("needs_revision")}>Request revision</button>
          <button className="btn btn-secondary" type="button" disabled={busy || !notes.trim()} onClick={() => review("rejected")}>Reject</button>
        </div>
      </div>
      {message ? <p role="status">{message}</p> : null}
    </section>
  );
}
