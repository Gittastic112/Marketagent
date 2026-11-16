"use client";

import { useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { reviewThesisImpact, type EventThesisImpact } from "@/lib/api/evidence";

export function ThesisImpactReview({ impact }: { impact: EventThesisImpact }) {
  const router = useRouter();
  const [reason, setReason] = useState("");
  const [busy, setBusy] = useState(false);
  const pending = useRef(false);
  const [message, setMessage] = useState<string | null>(null);
  async function record(decision: "no_change" | "blocked") {
    if (pending.current || !reason.trim()) return;
    pending.current = true;
    setBusy(true); setMessage(null);
    try {
      await reviewThesisImpact(impact.id, decision, reason.trim(), impact.review_status);
      setMessage(decision === "no_change" ? "Review recorded. Thesis unchanged." : "Blocker recorded. Evidence remains in the review queue.");
      setReason(""); router.refresh();
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Review could not be saved. Your reason is retained.");
    } finally {pending.current = false; setBusy(false);}
  }
  return <details><summary>Record evidence review</summary>
    <label>Review reason<textarea value={reason} maxLength={2000} disabled={busy}
      onChange={event => setReason(event.target.value)} rows={2} /></label>
    <div className="button-row">
      <button type="button" disabled={busy || !reason.trim()} onClick={() => void record("no_change")}>Reviewed; no thesis change</button>
      <button type="button" disabled={busy || !reason.trim()} onClick={() => void record("blocked")}>Record blocker</button>
    </div>
    {message && <p role="status">{message}</p>}
  </details>;
}
