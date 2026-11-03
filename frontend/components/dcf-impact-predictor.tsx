"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import { mapEventToDcf, type DcfMappingResponse } from "@/lib/api/ai";
import { AI_DISCLOSURES } from "@/lib/ai-privacy";
import { createRequestGate } from "@/lib/latest-request";

export function DcfImpactPredictor({ eventId, eventText }: { eventId: number; eventText: string }) {
  const [loading, setLoading] = useState(false);
  const [consent, setConsent] = useState(false);
  const [result, setResult] = useState<DcfMappingResponse["data"]>(null);
  const [error, setError] = useState<string | null>(null);
  const gate = useMemo(createRequestGate, []);
  const busy = useRef(false);
  useEffect(() => {
    gate.invalidate(); busy.current = false; setLoading(false); setConsent(false); setResult(null); setError(null);
    return () => gate.invalidate();
  }, [eventId, eventText, gate]);

  async function predict() {
    if (!consent || busy.current) return;
    const current = gate.begin();
    busy.current = true; setLoading(true); setError(null); setResult(null);
    try {
      const response = await mapEventToDcf(eventId, eventText);
      if (!current()) return;
      const data = response.data;
      const evidence = data?.ai_output;
      if (!data || data.error || !evidence || evidence.execution_status !== "success"
        || evidence.reference_id !== eventId || !evidence.source_ids_json?.includes(`event:${eventId}`)
        || !Array.isArray(data.impacted_variables) || data.impacted_variables.length > 20
        || data.impacted_variables.some(item => !item || typeof item.variable_name !== "string"
          || typeof item.reasoning !== "string" || !["increase", "decrease", "unknown"].includes(item.impact_direction)
          || !["high", "medium", "low"].includes(item.confidence))) {
        throw new Error("The AI response could not be verified. No valuation inputs changed.");
      }
      setResult(data);
    } catch (failure) {
      if (current()) setError(failure instanceof Error ? failure.message : "AI interpretation unavailable. Try again explicitly.");
    } finally {if (current()) {busy.current = false; setLoading(false);}}
  }

  const evidence = result?.ai_output;
  return <section aria-label="Event AI interpretation" className="stack" style={{minWidth: 0, whiteSpace: "normal", overflowWrap: "anywhere"}}>
    <h4>AI DCF interpretation</h4>
    <p>Optional review suggestions. Interpretation quality is not evaluated. No valuation inputs are changed.</p>
    <label className="checkbox-label" style={{textTransform: "none"}}>
      <input type="checkbox" checked={consent} onChange={event => {
        gate.invalidate(); busy.current = false; setLoading(false); setResult(null); setError(null); setConsent(event.target.checked);
      }} />
      {AI_DISCLOSURES.eventMapping}
    </label>
    <button type="button" className="secondary-button" disabled={!consent || loading} onClick={predict}>
      {loading ? "Interpreting event…" : "Analyze DCF impact"}
    </button>
    {loading && <p role="status">Waiting for the AI provider. The request has not been confirmed.</p>}
    {error && <p role="alert">{error}</p>}
    {result && evidence && <div className="stack" aria-label="Event interpretation result">
      <p><strong>{evidence.is_mock ? "Mock Data · " : ""}AI Interpretation</strong> · Human review: {evidence.human_review_status}.</p>
      {evidence.is_blocked && <p role="status">Evidence checks have not verified these claims. Keep them outside trusted research until reviewed.</p>}
      {result.impacted_variables.length === 0 ? <p>The AI proposed no variables. This does not establish that the event has no valuation effect.</p> :
        <ul>{result.impacted_variables.map((impact, index) => <li key={index}>
          <strong>{impact.variable_name}</strong>: {impact.impact_direction} · Provider confidence: {impact.confidence}.
          <p>{impact.reasoning}</p>
        </li>)}</ul>}
      <p>Provider / model: {evidence.provider_name} / {evidence.model_name}. Generated: {evidence.created_at}.</p>
      <details><summary>Source and generation evidence</summary>
        <p>Prompt: {evidence.prompt_version}. Output: #{evidence.id}.</p>
        <p className="brief-source-hash">Input SHA-256: {evidence.input_hash}</p>
        <p>{evidence.limitations || "No additional provider limitations recorded."}</p>
      </details>
      <a href={`/events/${eventId}/evidence-resolution`}>Review the recorded event and source evidence</a>
    </div>}
  </section>;
}
