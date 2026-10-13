"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { generateValuationMemo, fetchValuationMemo, type ValuationMemoResponse } from "@/lib/api/ai";
import type { DcfAssumptionSet } from "@/lib/api/valuation";
import { AI_DISCLOSURES } from "@/lib/ai-privacy";
import { createRequestGate } from "@/lib/latest-request";
import { useLatestResource } from "@/lib/use-latest-resource";
import { AIExplanationEvidence } from "./ai-explanation-evidence";

export function ValuationMemoPanel({ valuationId, assumptions, blocked }: {
  valuationId: number; assumptions: DcfAssumptionSet; blocked: boolean;
}) {
  const loader = useCallback(() => fetchValuationMemo(valuationId, assumptions.scenario, assumptions.id),
    [valuationId, assumptions.scenario, assumptions.id]);
  const stored = useLatestResource(loader);
  const [generated, setGenerated] = useState<ValuationMemoResponse | null>(null);
  const [attempted, setAttempted] = useState(false);
  const [generating, setGenerating] = useState(false);
  const [error, setError] = useState("");
  const [consent, setConsent] = useState(false);
  const gate = useMemo(createRequestGate, []);
  useEffect(() => () => gate.invalidate(), [gate]);
  const memo = attempted ? generated : stored.data;

  async function generate() {
    if (!consent || generating || blocked) return;
    const current = gate.begin();
    setGenerating(true); setAttempted(true); setGenerated(null); setError("");
    try {
      const result = await generateValuationMemo(valuationId, assumptions.scenario, {
        assumption_set_id: assumptions.id, assumptions_updated_at: assumptions.updated_at,
      });
      if (current()) setGenerated(result);
    } catch (failure) {
      if (current()) setError(failure instanceof Error ? failure.message : "Memo generation unavailable. Reload stored memo before retrying.");
    } finally { if (current()) setGenerating(false); }
  }

  function download() {
    if (!memo?.memo_markdown) return;
    const content = `AI Interpretation${memo.is_mock ? " · Mock Data" : ""}\nInterpretation quality is not evaluated.\n\nEvidence:\n${JSON.stringify(memo.evidence ?? {status: "legacy_unverified"}, null, 2)}\n\n${memo.memo_markdown}`;
    const url = URL.createObjectURL(new Blob([content], {type: "text/plain;charset=utf-8"}));
    const link = document.createElement("a");
    link.href = url; link.download = `valuation-${valuationId}-assumptions-${assumptions.id}-memo.txt`;
    link.click(); URL.revokeObjectURL(url);
  }

  return <section aria-label="Valuation memo" className="stack">
    <h3>Valuation Memo</h3>
    <p>Optional AI interpretation of saved assumptions #{assumptions.id}, scenario {assumptions.scenario}. Unsaved edits are excluded. Generating a memo does not save or approve valuation inputs.</p>
    {blocked && <p role="status" className="basis-note">Generation unavailable. Review saved input and calculation diagnostics, then save a valid version.</p>}
    <label><input type="checkbox" checked={consent} onChange={event => setConsent(event.target.checked)} /> {AI_DISCLOSURES.valuationMemo}</label>
    <div className="section-intro">
      <button type="button" className="btn btn-primary" disabled={generating || !consent || blocked || stored.status === "loading"} onClick={() => void generate()}>
        {generating ? "Writing memo…" : memo?.memo_markdown ? "Regenerate Memo" : "Generate Memo"}
      </button>
      <button type="button" className="btn btn-secondary" disabled={generating || stored.status === "loading"} onClick={() => {
        gate.invalidate(); setAttempted(false); setGenerated(null); setError(""); void stored.reload().catch(() => {});
      }}>Reload stored memo</button>
    </div>
    {!attempted && stored.status === "loading" && <p role="status">Loading stored memo…</p>}
    {!attempted && stored.status === "error" && <p role="alert">Stored memo unavailable: {stored.error}</p>}
    {error && <p role="alert">{error}</p>}
    {generating && <p role="status">Generating an unreviewed AI explanation. Your saved model is unchanged.</p>}
    {memo?.memo_markdown ? <>
      <AIExplanationEvidence evidence={memo.evidence} />
      <div className="preserve-whitespace" aria-label="Memo text">{memo.memo_markdown}</div>
      <button type="button" className="btn btn-secondary" onClick={download}>Download memo with evidence</button>
    </> : !generating && !error && stored.status === "ready" && <p>No memo generated for this saved version. Generation requires explicit consent.</p>}
  </section>;
}
