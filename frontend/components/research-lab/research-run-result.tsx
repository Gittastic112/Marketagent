"use client";

import dynamic from "next/dynamic";
import { useState } from "react";
import type { ResearchRun } from "@/lib/api/research-lab";
import { formatPercent } from "@/lib/formatting";
import { numericRecord } from "@/lib/research-lab-input";
import type { ResearchCurvePoint } from "./research-curve";

const ResearchCurve = dynamic(() => import("./research-curve"), { ssr: false, loading: () => <p role="status">Loading chart…</p> });
const PERCENT_METRICS = new Set(["annualized_volatility", "annual_expected_return", "total_return", "annualized_return", "max_drawdown", "win_rate", "tracking_error_annualized", "gross_turnover"]);

function metricValue(key: string, value: unknown): string {
  if (typeof value !== "number" || !Number.isFinite(value)) return "Unavailable";
  return PERCENT_METRICS.has(key) ? formatPercent(value, 2) : value.toLocaleString(undefined, { maximumFractionDigits: 4 });
}

function record(value: unknown): Record<string, unknown> | null {
  return value && typeof value === "object" && !Array.isArray(value) ? value as Record<string, unknown> : null;
}

export function ResearchRunResult({ run }: { run: ResearchRun }) {
  const [page, setPage] = useState(0);
  const weights = numericRecord(run.result.weights) ?? numericRecord(run.result.final_weights);
  const metrics = record(run.result.metrics);
  const curve = Array.isArray(run.result.equity_curve) ? run.result.equity_curve.filter((point): point is ResearchCurvePoint => {
    const row = record(point);
    return Boolean(row && typeof row.date === "string" && [row.wealth_index, row.return_decimal, row.drawdown].every(value => typeof value === "number" && Number.isFinite(value)));
  }) : [];
  const candidates = Array.isArray(run.result.candidates) ? run.result.candidates.map(record).filter((row): row is Record<string, unknown> => row !== null) : [];
  const pageCount = Math.max(1, Math.ceil(curve.length / 50));
  const currentPage = Math.min(page, pageCount - 1);
  const exported = `/api/backend/api/research-lab/runs/${run.run_id}`;
  return <section className="research-run-result" aria-label="Saved research result">
    <div className="section-intro"><h3>Saved {run.kind} run #{run.run_id}</h3><span className="badge">Hypothetical research</span></div>
    <p>This result describes the saved run, not a live preview of changes in the form. It does not modify actual holdings or approve source evidence.</p>
    <dl className="research-run-provenance">
      <div><dt>Adapter</dt><dd>{run.manifest.adapter} · {run.manifest.adapter_version}</dd></div>
      <div><dt>Saved</dt><dd><time dateTime={run.manifest.created_at}>{run.manifest.created_at}</time></dd></div>
      <div><dt>Source assertion</dt><dd>{run.manifest.source_assertion.replaceAll("_", " ")}</dd></div>
      <div><dt>Knowledge policy</dt><dd>{run.manifest.knowledge_policy.replaceAll("_", " ")}</dd></div>
      {typeof run.result.base_currency === "string" && <div><dt>Base currency</dt><dd>{run.result.base_currency}</dd></div>}
      {typeof run.result.return_basis === "string" && <div><dt>Return basis</dt><dd>{run.result.return_basis.replaceAll("_", " ")}</dd></div>}
      {typeof run.result.source_label === "string" && <div><dt>Input description</dt><dd>{run.result.source_label}</dd></div>}
    </dl>
    {!!run.warnings?.length && <div className="basis-note"><h4>Limitations and diagnostics</h4><ul>{run.warnings.map((warning, index) => <li key={index}>{warning}</li>)}</ul></div>}
    {weights && <div className="table-wrap" role="region" aria-label="Hypothetical allocation weights" tabIndex={0}>
      <table><caption>{run.kind === "allocation" ? "Proposed weights" : "Final simulated weights"} · Calculations</caption><thead><tr><th scope="col">Asset key</th><th scope="col">Weight</th></tr></thead>
        <tbody>{Object.entries(weights).map(([key, weight]) => <tr key={key}><th scope="row">{key}</th><td>{formatPercent(weight, 2)}</td></tr>)}</tbody></table>
    </div>}
    {metrics && <div className="table-wrap" role="region" aria-label="Research calculation metrics" tabIndex={0}>
      <table><caption>Saved calculation metrics</caption><thead><tr><th scope="col">Metric</th><th scope="col">Value</th></tr></thead>
        <tbody>{Object.entries(metrics).map(([key, value]) => <tr key={key}><th scope="row">{key.replaceAll("_", " ")}</th><td>{metricValue(key, value)}</td></tr>)}</tbody></table>
    </div>}
    {!!curve.length && <>
      <h4>Hypothetical wealth index</h4><p className="basis-note">Initial capital basis: 1. Source: saved run #{run.run_id}; {curve[0].date} to {curve.at(-1)?.date}. Calculated by {run.manifest.adapter}; saved {run.manifest.created_at}.</p>
      <ResearchCurve points={curve} />
      <details><summary>Inspect return and drawdown observations ({curve.length})</summary>
        <div className="table-wrap" role="region" aria-label="Saved research return observations" tabIndex={0}><table>
          <thead><tr><th scope="col">Date</th><th scope="col">Wealth index</th><th scope="col">Period return</th><th scope="col">Drawdown</th></tr></thead>
          <tbody>{curve.slice(currentPage * 50, (currentPage + 1) * 50).map(point => <tr key={point.date}><th scope="row">{point.date}</th><td>{point.wealth_index.toFixed(6)}</td><td>{formatPercent(point.return_decimal, 3)}</td><td>{formatPercent(point.drawdown, 3)}</td></tr>)}</tbody>
        </table></div>
        <div className="button-row"><button type="button" className="secondary-button" disabled={currentPage === 0} onClick={() => setPage(currentPage - 1)}>Previous observations</button>
          <span>Page {currentPage + 1} of {pageCount}</span><button type="button" className="secondary-button" disabled={currentPage + 1 >= pageCount} onClick={() => setPage(currentPage + 1)}>Next observations</button></div>
      </details>
    </>}
    {run.kind === "peers" && <>
      <p>{candidates.length} candidate(s) returned{run.result.truncated === true ? "; results are truncated. Refine the filters." : "."} Discovery does not add or review a peer set.</p>
      {!!candidates.length && <div className="table-wrap" role="region" aria-label="Peer discovery candidates" tabIndex={0}><table>
        <thead><tr>{["Symbol", "Name", "Country", "Sector", "Industry", "Exchange"].map(label => <th scope="col" key={label}>{label}</th>)}</tr></thead>
        <tbody>{candidates.map((candidate, index) => <tr key={index}>{[candidate.symbol ?? candidate.ticker, candidate.name, candidate.country, candidate.sector, candidate.industry, candidate.exchange].map((value, column) =>
          <td key={column}>{typeof value === "string" ? value : "Unavailable"}</td>)}</tr>)}</tbody>
      </table></div>}
    </>}
    <div className="button-row"><a className="secondary-button" href={`${exported}/export`} download>Download saved inputs and result (JSON)</a>
      {run.kind === "report" && <a className="secondary-button" href={`${exported}/report.html`} download>Download research report (HTML)</a>}</div>
    <details><summary>Exact manifest and result</summary><p>Input SHA-256: <code>{run.manifest.input_sha256}</code></p><p>Output SHA-256: <code>{run.manifest.output_sha256}</code></p>
      <pre className="research-json-result">{JSON.stringify({ manifest: run.manifest, result: run.result }, null, 2)}</pre></details>
  </section>;
}
