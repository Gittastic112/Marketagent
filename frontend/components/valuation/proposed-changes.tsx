import type { ValuationPreview } from "@/lib/api/valuation-preview";
import { formatNumber } from "@/lib/formatting";

const display = (value: unknown) => value == null ? "Not supplied" : typeof value === "number"
  ? formatNumber(value, 8) : typeof value === "object" ? JSON.stringify(value) : String(value);

export function ProposedValuationChanges({ preview, pending, onSave }: {
  preview: ValuationPreview; pending: boolean; onSave: () => void;
}) {
  return <section className="panel panel-content" aria-label="Unsaved valuation preview">
    <h3 className="text-lg font-semibold">Compare before saving</h3>
    <p><strong>Unsaved preview</strong> for {preview.valuation_date || "an unspecified research date"}, based on saved version #{preview.base_assumption_set_id ?? "none"}.
      Source evidence has not been approved by this calculation.</p>
    {preview.missing_fields.length > 0 && <p role="alert">Required inputs missing: {preview.missing_fields.map(f => f.replaceAll("_", " ")).join(", ")}</p>}
    <div className="table-wrap" role="region" aria-label="Proposed input changes" tabIndex={0}>
      <table><thead><tr><th>Input</th><th>Saved</th><th>Proposed User Assumption</th></tr></thead>
        <tbody>{preview.changes.map(change => <tr key={change.field}><th scope="row">{change.field.replaceAll("_", " ")}</th>
          <td>{display(change.previous)}</td><td>{display(change.proposed)}</td></tr>)}</tbody></table>
    </div>
    {preview.changes.length === 0 && <p>No input values changed. A save still records the selected research date and reason.</p>}
    {preview.proposed_output && <div className="table-wrap" role="region" aria-label="Preview results" tabIndex={0}>
      <table><thead><tr><th>Calculation in {preview.currency || "unconfirmed currency"}</th><th>Previously saved</th><th>Proposed</th></tr></thead><tbody>
        {Object.entries(preview.proposed_output).map(([field, result]) => <tr key={field}>
          <th scope="row">{field.replaceAll("_", " ")}{field === "terminal_value_pct_of_ev" ? " (decimal share)" : ""}</th>
          <td>{display(preview.previous_output?.[field])}</td><td>{preview.ready ? display(result) : "Withheld: review blockers"}</td></tr>)}
      </tbody></table>
    </div>}
    {preview.diagnostics.length > 0 && <ul>{preview.diagnostics.map((item, i) => <li key={i}><strong>{item.severity}</strong>: {item.message}</li>)}</ul>}
    <details><summary>Preview basis and limits</summary><ul>{preview.limitations.map(limit => <li key={limit}>{limit}</li>)}</ul></details>
    <button className="primary-button" type="button" disabled={!preview.ready || pending} onClick={onSave}>{pending ? "Saving reviewed version..." : "Save this reviewed version"}</button>
  </section>;
}
