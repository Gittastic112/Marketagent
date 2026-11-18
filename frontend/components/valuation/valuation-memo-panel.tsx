"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { generateValuationMemo, fetchValuationMemo, type ValuationMemoResponse } from "@/lib/api/ai";
import type { DcfAssumptionSet } from "@/lib/api/valuation";
import { AI_DISCLOSURES } from "@/lib/ai-privacy";
import { createRequestGate } from "@/lib/latest-request";
import { useLatestResource } from "@/lib/use-latest-resource";
import { memoBasisError, memoSessionKey, valuationMemoExport, type MemoSelection } from "@/lib/valuation-memo";
import { AIExplanationEvidence } from "./ai-explanation-evidence";
import { MemoMarkdown } from "./memo-markdown";

type MemoPanelProps = {
  valuationId: number; assumptions: DcfAssumptionSet; blocked: boolean;
};

export function ValuationMemoPanel(props: MemoPanelProps) {
  const selection: MemoSelection = { valuationId: props.valuationId, assumptionSetId: props.assumptions.id,
    scenario: props.assumptions.scenario, assumptionsUpdatedAt: props.assumptions.updated_at,
    outputId: props.assumptions.outputs?.id };
  return <ValuationMemoSession key={memoSessionKey(selection)} {...props} />;
}

function ValuationMemoSession({ valuationId, assumptions, blocked }: MemoPanelProps) {
  const validate = useCallback((result: ValuationMemoResponse) => {
    const problem = memoBasisError(result, { valuationId, assumptionSetId: assumptions.id,
      scenario: assumptions.scenario, assumptionsUpdatedAt: assumptions.updated_at, outputId: assumptions.outputs?.id });
    if (problem) throw new Error(problem);
    return result;
  }, [valuationId, assumptions.id, assumptions.scenario, assumptions.updated_at, assumptions.outputs?.id]);
  const loader = useCallback(() => fetchValuationMemo(valuationId, assumptions.scenario, assumptions.id).then(validate),
    [valuationId, assumptions.scenario, assumptions.id, validate]);
  const stored = useLatestResource(loader);
  const [generated, setGenerated] = useState<ValuationMemoResponse | null>(null);
  const [attempted, setAttempted] = useState(false);
  const [generating, setGenerating] = useState(false);
  const [error, setError] = useState("");
  const [consent, setConsent] = useState(false);
  const gate = useMemo(createRequestGate, []);
  useEffect(() => () => gate.invalidate(), [gate]);
  const memo = attempted ? generated : stored.data;
  const sourceAnchorPrefix = `memo-${valuationId}-${assumptions.id}-${memo?.evidence?.ai_output_id ?? "legacy"}`;

  async function generate() {
    if (!consent || generating || blocked) return;
    const current = gate.begin();
    setGenerating(true); setAttempted(true); setGenerated(null); setError("");
    try {
      const result = await generateValuationMemo(valuationId, assumptions.scenario, {
        assumption_set_id: assumptions.id, assumptions_updated_at: assumptions.updated_at,
      });
      if (current()) setGenerated(validate(result));
    } catch (failure) {
      if (current()) setError(failure instanceof Error ? failure.message : "Memo generation unavailable. Reload stored memo before retrying.");
    } finally { if (current()) setGenerating(false); }
  }

  function download() {
    if (!memo?.memo_markdown) return;
    const artifact = valuationMemoExport(memo);
    const url = URL.createObjectURL(new Blob([artifact.content], {type: artifact.mimeType}));
    const link = document.createElement("a");
    link.href = url; link.download = artifact.filename;
    link.click(); window.setTimeout(() => URL.revokeObjectURL(url), 1000);
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
      <AIExplanationEvidence evidence={memo.evidence} sourceAnchorPrefix={sourceAnchorPrefix} />
      <p className="basis-note">Source markers link only to this memo’s registered inputs. External links are model-provided and have not been verified. Embedded HTML and images are omitted.</p>
      <MemoMarkdown markdown={memo.memo_markdown} sourceIds={memo.evidence?.source_ids ?? []} sourceAnchorPrefix={sourceAnchorPrefix} />
      <button type="button" className="btn btn-secondary" onClick={download}>Download memo with evidence</button>
    </> : !generating && !error && stored.status === "ready" && <p>No memo generated for this saved version. Generation requires explicit consent.</p>}
  </section>;
}
