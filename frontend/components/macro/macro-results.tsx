import type { MacroScenarioResult, MacroSensitivityResult } from "@/lib/api/macro";

const FACTORS = [
  ["duration", "Duration"], ["cyclicality", "Cyclicality"],
  ["inflation_sensitivity", "Inflation sensitivity"], ["currency_sensitivity", "Currency sensitivity"],
] as const;

function value(number: number | null | undefined, percent = false) {
  if (number == null || !Number.isFinite(number)) return "Not available";
  return percent ? (number * 100).toFixed(2) + "%" : number.toLocaleString("en-US", {maximumFractionDigits: 4});
}

function Notes({warnings, formula}: {warnings: string[] | null; formula?: string}) {
  return <details><summary>Method and data notes</summary>
    {formula ? <p className="muted">{formula}</p> : null}
    <ul>{(warnings ?? []).map(note => <li key={note}>{note}</li>)}</ul>
  </details>;
}

export function ScenarioResult({result}: {result: MacroScenarioResult}) {
  const incomplete = result.estimated_value_impact_pct == null || result.estimated_operating_income_impact_pct == null;
  return <div className="brief-list">
    <p className="muted">Calculation using sector benchmarks and your selected shocks.</p>
    {incomplete ? <p>Complete impact requires the missing coefficients or currency direction below. Covered contributions describe only the available factors.</p> : null}
    <div className="table-wrap" tabIndex={0} aria-label="Macro scenario results">
      <table><thead><tr><th>Outcome</th><th>Estimated impact</th><th>Covered contribution</th><th>Still needed</th></tr></thead>
        <tbody>
          <tr><th>Firm value</th><td>{value(result.estimated_value_impact_pct, true)}</td><td>{value(result.covered_value_impact_pct, true)}</td><td>{(result.missing_value_factors ?? []).join(", ") || "No missing active factors"}</td></tr>
          <tr><th>Operating income</th><td>{value(result.estimated_operating_income_impact_pct, true)}</td><td>{value(result.covered_operating_income_impact_pct, true)}</td><td>{(result.missing_operating_income_factors ?? []).join(", ") || "No missing active factors"}</td></tr>
        </tbody></table>
    </div>
    <p className="muted">Source: {result.source_file} · {result.market} / {result.country} · SIC {result.sic_code}. Benchmark presence does not verify company exposure.</p>
    <Notes warnings={result.warnings} formula={result.formula} />
  </div>;
}

export function BottomUpResult({result}: {result: MacroSensitivityResult}) {
  return <div className="brief-list">
    <p className="muted">Calculation · {result.basis}</p>
    <p>Full-company estimates require coefficients for all segment value. A covered contribution is a partial sum.</p>
    <div className="table-wrap" tabIndex={0} aria-label="Bottom-up sensitivity coverage">
      <table><thead><tr><th>Factor</th><th>Company estimate</th><th>Covered contribution</th><th>Value coverage</th></tr></thead>
        <tbody>{FACTORS.map(([key, label]) => <tr key={key}>
          <th>{key === "duration" ? "Rate coefficient (source convention)" : label}</th><td>{value(result.firm_value?.[key])}</td>
          <td>{value(result.covered_contributions?.[key])}</td><td>{value(result.metric_coverage?.[key], true)}</td>
        </tr>)}</tbody></table>
    </div>
    {result.segment_exposures?.length ? <details><summary>Segment sources</summary><ul>{result.segment_exposures.map((segment, index) =>
      <li key={index}>{segment.name}: SIC {segment.sic_code}, {value(segment.weight, true)} of submitted value. Source: {segment.source_file}.</li>)}</ul></details> : null}
    <Notes warnings={result.warnings} formula={result.formula} />
  </div>;
}

export function TopDownResult({result}: {result: MacroSensitivityResult}) {
  return <div className="brief-list">
    <p>Calculation from {result.observation_count} period changes. Constant macro series cannot establish a coefficient.</p>
    <div className="table-wrap" tabIndex={0} aria-label="Top-down sensitivity results">
      <table><thead><tr><th>Factor</th><th>Firm value</th><th>Operating income</th></tr></thead>
        <tbody>{FACTORS.map(([key, label]) => <tr key={key}><th>{key === "duration" ? "Signed duration (negative rate slope)" : label}</th>
          <td>{value(result.firm_value[key])}</td><td>{value(result.operating_income[key])}</td></tr>)}</tbody></table>
    </div>
    <Notes warnings={result.warnings} formula={result.formula} />
  </div>;
}
