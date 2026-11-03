import type { ValuationAIEvidence } from "@/lib/api/ai";

export function AIExplanationEvidence({ evidence }: { evidence?: ValuationAIEvidence }) {
  if (!evidence) return <p role="status" className="basis-note">Legacy output: saved version and AI provenance are not verified. Do not use it as current valuation evidence.</p>;
  return <section aria-label="AI explanation evidence" className="basis-note">
    <p><strong>{evidence.is_mock ? "Mock Data · " : ""}AI Interpretation</strong> · Review: {evidence.review_status.replaceAll("_", " ")}.</p>
    <p>Interpretation quality is not evaluated. Exact source references do not establish numerical or financial correctness.</p>
    {(!evidence.is_current || !evidence.basis_verified) && <p role="status">Historical or unverified basis. Review the current saved calculation before using this explanation.</p>}
    <dl>
      <div className="key-value"><dt>Saved assumptions</dt><dd>#{evidence.assumption_set_id} · {evidence.scenario} · {evidence.assumptions_updated_at ?? "Update time unavailable"}</dd></div>
      <div className="key-value"><dt>Calculation</dt><dd>#{evidence.output_id ?? "Not available"} · {evidence.currency ?? "Currency unavailable"} · {evidence.output_calculated_at ?? "Date unavailable"}</dd></div>
      <div className="key-value"><dt>AI provider / model</dt><dd>{evidence.provider_name} / {evidence.model_name}</dd></div>
      <div className="key-value"><dt>Generated</dt><dd>{evidence.generated_at}</dd></div>
      <div className="key-value"><dt>Prompt / output</dt><dd>{evidence.prompt_version} · #{evidence.ai_output_id}</dd></div>
    </dl>
    <details><summary>Input references and limitations</summary>
      <p className="brief-source-hash">Input SHA-256: {evidence.input_hash}</p>
      <ul>{evidence.source_ids.map(source => <li key={source}>{source}</li>)}</ul>
      <p>Saved inputs and comparison price are User Assumptions. Saved model outputs are Calculations. Unsaved numerical edits are excluded.</p>
      <p>{evidence.limitations ?? "No additional provider limitations recorded."}</p>
      <p>Provider confidence: {evidence.confidence_label || "Not supplied"}. This is not a verified probability or investment recommendation.</p>
    </details>
  </section>;
}
