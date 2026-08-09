"use client";

import { useState } from "react";
import Link from "next/link";

import { AiOutput, patchApi, postApi } from "@/lib/api";

type Props = {
  initialOutput: AiOutput;
};

export function AiOutputReviewControls({ initialOutput }: Props) {
  const [output, setOutput] = useState(initialOutput);
  const [quotes, setQuotes] = useState<Record<string, string>>({});
  const [notes, setNotes] = useState(initialOutput.review_notes ?? "");
  const [message, setMessage] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const citedSourceIds = Array.from(
    output.output_text.matchAll(/\[source_id:([^\]]+)\]/g),
    (match) => match[1].trim(),
  ).filter((source, index, sources) => source.startsWith("raw_document:") && sources.indexOf(source) === index);
  const allQuotesPresent = citedSourceIds.length > 0 && citedSourceIds.every((source) => quotes[source]?.trim());

  async function validateCitation() {
    if (!allQuotesPresent) return;
    setBusy(true);
    setMessage(null);
    try {
      const updated = await postApi<AiOutput>(`/ai-outputs/${output.id}/citations/validate`, {
        citations: citedSourceIds.map((source_id) => ({ source_id, quote: quotes[source_id].trim() })),
      });
      setOutput(updated);
      setMessage(updated.citation_validation_status === "valid" ? "Exact citation verified." : "Citation could not be verified.");
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Citation validation failed.");
    } finally {
      setBusy(false);
    }
  }

  async function review(status: "approved" | "rejected" | "needs_revision") {
    setBusy(true);
    setMessage(null);
    try {
      const updated = await patchApi<AiOutput>(`/ai-outputs/${output.id}/review`, {
        status,
        notes: notes.trim() || null,
      });
      setOutput(updated);
      setMessage(`Review saved as ${status.replace("_", " ")}.`);
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Review could not be saved.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <section aria-label="AI evidence and review" style={{ display: "grid", gap: "1rem" }}>
      <div>
        <h4 style={{ marginBottom: "0.5rem", color: "var(--text-secondary)" }}>Evidence</h4>
        <p><strong>Citation status:</strong> {output.citation_validation_status.replace("_", " ")}</p>
        {citedSourceIds.length === 0 ? (
          <p style={{ color: "var(--danger)" }}>Blocked: the output has no supported raw-document source markers.</p>
        ) : citedSourceIds.map((source) => (
          <label key={source} style={{ display: "grid", gap: "0.35rem", marginTop: "0.75rem" }}>
            Exact supporting passage for {source}
            <textarea
              value={quotes[source] ?? ""}
              onChange={(event) => setQuotes((current) => ({ ...current, [source]: event.target.value }))}
              rows={3}
              placeholder="Paste the exact supporting passage from the stored source"
            />
          </label>
        ))}
        <button type="button" disabled={busy || !allQuotesPresent} onClick={validateCitation}>
          Validate all cited sources
        </button>
        {output.citations_json.map((citation, index) => (
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
        <p><strong>Automated checks:</strong> {output.evaluation_json?.passed ? "passed" : "not passed"}</p>
        {output.evaluation_json && !output.evaluation_json.passed ? (
          <ul>
            {Object.entries(output.evaluation_json.checks)
              .filter(([name, passed]) => name !== "citations_required" && !passed)
              .map(([name]) => <li key={name}>{name.replaceAll("_", " ")}</li>)}
          </ul>
        ) : null}
        <label style={{ display: "grid", gap: "0.35rem", marginTop: "0.75rem" }}>
          Review notes
          <textarea value={notes} onChange={(event) => setNotes(event.target.value)} rows={3} />
        </label>
        <div style={{ display: "flex", flexWrap: "wrap", gap: "0.5rem" }}>
          <button type="button" disabled={busy || !output.evaluation_json?.passed} onClick={() => review("approved")}>Approve</button>
          <button type="button" disabled={busy || !notes.trim()} onClick={() => review("needs_revision")}>Request revision</button>
          <button type="button" disabled={busy || !notes.trim()} onClick={() => review("rejected")}>Reject</button>
        </div>
      </div>
      {message ? <p role="status">{message}</p> : null}
    </section>
  );
}
