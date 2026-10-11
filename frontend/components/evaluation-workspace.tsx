"use client";

import { useEffect, useRef, useState } from "react";
import Link from "next/link";
import { TextAreaField, TextField } from "@/components/form-fields";
import { Panel } from "@/components/page";
import { createRequestGate } from "@/lib/latest-request";
import { executeFinancialEvaluation, getEvaluationBasis, type EvaluationBasis, type EvaluationRun } from "@/lib/api/evaluation";

const percent = (value: number | null) => typeof value === "number" && Number.isFinite(value) ? `${(value * 100).toFixed(1)}%` : "Not available";

export function EvaluationWorkspace({ initialRuns }: { initialRuns: EvaluationRun[] }) {
  const [runs, setRuns] = useState(initialRuns);
  const [documentId, setDocumentId] = useState("");
  const [basis, setBasis] = useState<EvaluationBasis | null>(null);
  const [pending, setPending] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const gate = useRef(createRequestGate());
  const form = useRef<HTMLFormElement>(null);
  useEffect(() => () => gate.current.invalidate(), []);

  async function loadBasis() {
    const current = gate.current.begin();
    setBasis(null); setError(null); setPending(true);
    try {
      const id = Number(documentId);
      if (!Number.isInteger(id) || id <= 0) throw new Error("Choose a valid stored document ID.");
      const value = await getEvaluationBasis(id);
      if (current()) setBasis(value);
    } catch (e) { if (current()) setError(e instanceof Error ? e.message : "Source basis unavailable."); }
    finally { if (current()) setPending(false); }
  }

  async function execute(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!basis || pending) return;
    const data = new FormData(event.currentTarget);
    const current = gate.current.begin();
    setPending(true); setError(null);
    try {
      const raw = String(data.get("expected") ?? "");
      if (new TextEncoder().encode(raw).length > 100_000) throw new Error("Reference JSON must be no larger than 100 KB.");
      const expected = JSON.parse(raw);
      if (!Array.isArray(expected) || !expected.length || expected.length > 200) throw new Error("Provide 1 to 200 independently reviewed reference rows.");
      const result = await executeFinancialEvaluation({
        run_name: String(data.get("run_name")), document_id: basis.document_id,
        source_text_sha256: basis.source_text_sha256, reference_reviewed: true,
        reference_is_complete: true, is_mock: data.get("data_kind") === "mock" || basis.is_mock, expected,
      });
      if (current()) setRuns(previous => [result, ...previous].slice(0, 10));
    } catch (e) { if (current()) setError(e instanceof Error ? e.message : "Evaluation failed. No success is assumed."); }
    finally { if (current()) setPending(false); }
  }

  return <>
    <Panel title="Run a financial extraction evaluation">
      <p>Compare the local text extractor with a complete, separately reviewed reference for one stored document. This does not certify PDF parsing, XBRL, AI claims or forecast accuracy. It makes no external API calls and does not promote financial facts.</p>
      <p><Link href="/documents">Open source documents</Link> to inspect the stored text and line numbers. Do not use the extractor's predictions as the reference.</p>
      <TextField id="evaluation_document" label="Stored source document ID" type="number" min="1" value={documentId} disabled={pending} onChange={event => {
        gate.current.invalidate(); setDocumentId(event.target.value); setBasis(null); setError(null); form.current?.reset();
      }} />
      <button type="button" onClick={loadBasis} disabled={pending}>{pending ? "Working..." : "Load source basis"}</button>
      {error && <p role="alert" className="inline-error">{error}</p>}
      {basis && <form key={basis.source_text_sha256} ref={form} onSubmit={execute} className="form-grid" style={{ gridTemplateColumns: "minmax(0, 1fr)" }}>
        <p>{basis.title} · {basis.line_count} lines · {basis.extractor_version}{basis.is_mock ? " · Mock Data" : " · Source status requires your review"}</p>
        <TextField id="evaluation_name" name="run_name" label="Evaluation name" maxLength={200} required disabled={pending} />
        <TextAreaField id="evaluation_expected" name="expected" label="Reviewed reference rows (JSON array)" rows={10} required disabled={pending}
          placeholder='[{"metric_code":"revenue","value":100,"unit":"USD","fiscal_year":2025,"period_type":"annual","source_line_number":1}]' />
        <p>The example is syntax only, not company data. Include every expected metric/period in the document; partial references distort precision and recall. Missing extracted units count as errors.</p>
        <label>Reference data classification <select name="data_kind" defaultValue="" required disabled={pending}>
          <option value="" disabled>Choose explicitly</option><option value="mock">Mock Data / test fixture</option>
          <option value="genuine" disabled={basis.is_mock}>Genuine source, reviewed by me</option>
        </select></label>
        <label><input type="checkbox" name="reference_reviewed" required disabled={pending} /> I reviewed the values, units, periods and source lines independently.</label>
        <label><input type="checkbox" name="reference_complete" required disabled={pending} /> This reference is complete for the document being evaluated.</label>
        <button type="submit" disabled={pending}>{pending ? "Evaluating..." : "Run local evaluation"}</button>
      </form>}
    </Panel>
    <Panel title="My latest evaluation runs">
      {!runs.length && <p>No evaluation runs yet.</p>}
      {runs.map(run => <article key={run.id} style={{ marginBottom: "1.5rem", overflowWrap: "anywhere" }}>
        <h3>{run.run_name}</h3><p>{run.status} · {run.completed_at ?? run.created_at}</p>
        {!run.report_json ? <p>Not executed. No result or score is available.</p> : <>
          <p>{run.report_json.is_mock ? "Mock Data" : "Reviewer-declared genuine source"} · Calculation against User Assumptions, not independent certification.</p>
          <p>Exact-match precision: {percent(run.report_json.precision)} · Recall: {percent(run.report_json.recall)}</p>
          <p>{run.report_json.true_positive_count} exact matches / {run.report_json.predicted_count} predictions / {run.report_json.expected_count} expected rows.</p>
          <details><summary>Results, source identity and limitations</summary>
            <p>{run.report_json.formula}</p>
            <p>Numeric: {percent(run.report_json.numeric_accuracy)} · Units: {percent(run.report_json.unit_accuracy)} · Periods: {percent(run.report_json.period_accuracy)} · Locators: {percent(run.report_json.source_locator_accuracy)}</p>
            <p>Document #{run.report_json.document_id} · Source text SHA-256: {run.report_json.source_text_sha256}<br />Reference SHA-256: {run.report_json.reference_sha256}<br />{run.report_json.extractor_version} / {run.report_json.evaluator_version}</p>
            <ul>{run.report_json.limitations.map(item => <li key={item}>{item}</li>)}</ul>
            <pre style={{ whiteSpace: "pre-wrap" }}>{JSON.stringify(run.report_json.comparisons, null, 2)}</pre>
          </details>
        </>}
      </article>)}
    </Panel>
  </>;
}
