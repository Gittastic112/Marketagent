"use client";

import { useState } from "react";
import Link from "next/link";

import { AiOutput, patchApi, postApi } from "@/lib/api";

type Props = {
  initialOutput: AiOutput;
};

export function AiOutputReviewControls({ initialOutput }: Props) {
  const [output, setOutput] = useState(initialOutput);
  const [quote, setQuote] = useState("");
  const [notes, setNotes] = useState(initialOutput.review_notes ?? "");
  const [message, setMessage] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const rawDocumentSource = output.source_ids_json.find((source) => source.startsWith("raw_document:"));

  async function validateCitation() {
    if (!rawDocumentSource || !quote.trim()) return;
    setBusy(true);
    setMessage(null);
    try {
      const updated = await postApi<AiOutput>(`/ai-outputs/${output.id}/citations/validate`, {
        citations: [{ source_id: rawDocumentSource, quote: quote.trim() }],
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
        <label style={{ display: "grid", gap: "0.35rem", marginTop: "0.75rem" }}>
          Exact supporting passage
          <textarea
            value={quote}
            onChange={(event) => setQuote(event.target.value)}
            rows={3}
            placeholder="Paste one exact passage from the stored source"
          />
        </label>
        <button type="button" disabled={busy || !rawDocumentSource || !quote.trim()} onClick={validateCitation}>
          Validate citation
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
        <label style={{ display: "grid", gap: "0.35rem", marginTop: "0.75rem" }}>
          Review notes
          <textarea value={notes} onChange={(event) => setNotes(event.target.value)} rows={3} />
        </label>
        <div style={{ display: "flex", flexWrap: "wrap", gap: "0.5rem" }}>
          <button type="button" disabled={busy} onClick={() => review("approved")}>Approve</button>
          <button type="button" disabled={busy || !notes.trim()} onClick={() => review("needs_revision")}>Request revision</button>
          <button type="button" disabled={busy || !notes.trim()} onClick={() => review("rejected")}>Reject</button>
        </div>
      </div>
      {message ? <p role="status">{message}</p> : null}
    </section>
  );
}
