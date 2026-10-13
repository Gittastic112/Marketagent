"use client";

import { useEffect, useMemo, useState } from "react";
import type { DcfAssumptionSet } from "@/lib/api/valuation";
import { runNarrativeToNumbers, type NarrativeToNumbersResponse } from "@/lib/api/ai";
import { AI_DISCLOSURES } from "@/lib/ai-privacy";
import { createRequestGate } from "@/lib/latest-request";
import { AIExplanationEvidence } from "./ai-explanation-evidence";

export function NarrativeToNumbersPanel({ valuationId, scenario, currentAssumptions, onApplyAssumptions }: {
  valuationId: number; scenario: string; currentAssumptions: DcfAssumptionSet;
  onApplyAssumptions: (updates: Partial<DcfAssumptionSet>) => void;
}) {
  const [narrative, setNarrative] = useState(currentAssumptions.story_text || "");
  const [generating, setGenerating] = useState(false);
  const [suggestions, setSuggestions] = useState<NarrativeToNumbersResponse | null>(null);
  const [error, setError] = useState("");
  const [consent, setConsent] = useState(false);
  const [reviewed, setReviewed] = useState(false);
  const gate = useMemo(createRequestGate, []);
  useEffect(() => () => gate.invalidate(), [gate]);
  function invalidate() { gate.invalidate(); setSuggestions(null); setReviewed(false); setGenerating(false); setError(""); }

  async function generate() {
    if (!narrative.trim() || !consent || generating) return;
    const current = gate.begin();
    setGenerating(true); setError(""); setSuggestions(null); setReviewed(false);
    try {
      const result = await runNarrativeToNumbers(valuationId, scenario, {narrative_text: narrative,
        assumption_set_id: currentAssumptions.id, assumptions_updated_at: currentAssumptions.updated_at});
      if (!current()) return;
      const evidence = result.evidence;
      const horizon = currentAssumptions.projection_years_count;
      const finiteRate = (value: unknown, min: number, max: number) => typeof value === "number" && Number.isFinite(value) && value >= min && value <= max;
      if (!evidence?.is_current || !evidence.basis_verified || evidence.assumption_set_id !== currentAssumptions.id
        || Date.parse(evidence.assumptions_updated_at ?? "") !== Date.parse(currentAssumptions.updated_at)
        || !finiteRate(result.target_operating_margin, -1, 1)
        || !finiteRate(result.terminal_growth_rate, -0.99, 0.99)
        || !finiteRate(result.sales_to_capital_ratio, Number.MIN_VALUE, Number.MAX_VALUE)
        || !result.revenue_growth_years || !Object.keys(result.revenue_growth_years).length
        || horizon === undefined
        || Object.entries(result.revenue_growth_years).some(([year, rate]) =>
          !/^[1-9][0-9]*$/.test(year) || Number(year) > horizon || !finiteRate(rate, -0.99, 5))) {
        throw new Error("AI suggestions have an outdated basis or invalid numerical inputs. Review the saved version and retry explicitly.");
      }
      setSuggestions(result);
    } catch (failure) {
      if (current()) setError(failure instanceof Error ? failure.message : "Narrative mapping unavailable. Your inputs are unchanged.");
    } finally { if (current()) setGenerating(false); }
  }

  function apply() {
    if (!suggestions || !reviewed) return;
    onApplyAssumptions({story_text: narrative, target_operating_margin: suggestions.target_operating_margin,
      revenue_growth_years_json: suggestions.revenue_growth_years, sales_to_capital_ratio: suggestions.sales_to_capital_ratio,
      terminal_growth_rate: suggestions.terminal_growth_rate});
    setReviewed(false);
  }

  return <section aria-label="Narrative estimates" className="stack">
    <h3>Narrative to Numbers</h3>
    <p>Optional AI estimates from this narrative and saved assumptions #{currentAssumptions.id}. Unsaved numerical edits are excluded. Suggestions require your review and do not save a model.</p>
    <label htmlFor="ai-company-story">Narrative for AI estimates</label>
    <textarea id="ai-company-story" rows={6} maxLength={20000} value={narrative}
      onChange={event => {invalidate(); setNarrative(event.target.value);}} />
    <label><input type="checkbox" checked={consent} onChange={event => {invalidate(); setConsent(event.target.checked);}} /> {AI_DISCLOSURES.narrativeToNumbers}</label>
    <button type="button" className="btn btn-primary" disabled={generating || !narrative.trim() || !consent} onClick={() => void generate()}>
      {generating ? "Analyzing…" : "Map to Assumptions"}
    </button>
    {generating && <p role="status">Reading this narrative. Editing it invalidates the pending response.</p>}
    {error && <p role="alert">{error}</p>}
    {suggestions && <>
      <h4>{suggestions.ai_meta?.is_mock ? "Mock Data: " : ""}AI Estimated Assumptions</h4>
      <AIExplanationEvidence evidence={suggestions.evidence} />
      <dl>
        <div className="key-value"><dt>Target margin (decimal)</dt><dd>{suggestions.target_operating_margin} · {suggestions.target_operating_margin_reason}</dd></div>
        <div className="key-value"><dt>Sales-to-capital</dt><dd>{suggestions.sales_to_capital_ratio} · {suggestions.sales_to_capital_reason}</dd></div>
        <div className="key-value"><dt>Terminal growth (decimal)</dt><dd>{suggestions.terminal_growth_rate} · {suggestions.terminal_growth_reason}</dd></div>
      </dl>
      <p>Revenue growth by projection year (decimal rates):</p>
      <ul>{Object.entries(suggestions.revenue_growth_years).map(([year, rate]) => <li key={year}>Year {year}: {rate}</li>)}</ul>
      <p>{suggestions.revenue_growth_reason}</p>
      <label><input type="checkbox" checked={reviewed} onChange={event => setReviewed(event.target.checked)} /> I reviewed these estimates and want to replace the corresponding unsaved fields.</label>
      <button type="button" className="btn btn-secondary" disabled={!reviewed} onClick={apply}>Copy reviewed estimates to form</button>
    </>}
  </section>;
}
