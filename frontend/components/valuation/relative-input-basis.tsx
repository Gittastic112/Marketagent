import type { SavedRelativeInputBasis } from "@/lib/api";

const LABELS: Record<string, string> = {
  revenue: "Revenue", ebit: "EBIT", ebitda: "EBITDA", netIncome: "Net income",
  bookEquity: "Book equity", investedCapital: "Invested capital", debt: "Debt", cash: "Cash",
  dilutedShares: "Diluted shares",
};

export function RelativeInputBasis({ basis }: { basis: SavedRelativeInputBasis }) {
  return <section aria-label="Saved relative valuation input basis" className="relative-input-basis">
    <h3>Saved input basis</h3>
    <p>{basis.isMock && <strong>Mock Data. </strong>}User Assumptions from model {basis.modelId}, assumption set {basis.assumptionSetId}.
      {" "}<a href={`/companies/${basis.companyId}/valuation/${basis.modelId}`}>Review saved model</a>.</p>
    <p>Saved: {basis.savedAt || "Unknown"}. Last changed: {basis.updatedAt || "Unknown"}.</p>
    <p>Currency: {basis.currency || "Not configured"}. Monetary and share values retain their saved scale.
      Per-share output requires matching monetary and share scales. No currency or unit conversion is applied.</p>
    <p>Unsaved form edits are not used. Save the model first, then review its new input snapshot.</p>
    {basis.blockers.length > 0 && <div role="alert"><strong>Calculation blocked</strong>
      <ul>{basis.blockers.map(reason => <li key={reason}>{reason}</li>)}</ul></div>}
    <details>
      <summary>Inspect all company inputs and calculation basis</summary>
      <div className="relative-table-scroll" tabIndex={0} role="region" aria-label="Company input values and provenance">
        <table><thead><tr><th>Input</th><th>Saved value</th><th>Claim type</th><th>Basis</th></tr></thead>
          <tbody>{Object.entries(basis.fields).map(([key, field]) => <tr key={key}>
            <td>{LABELS[key] || key}</td><td>{field.value == null ? "Not available" : String(field.value)}</td>
            <td>{field.claimType}</td><td>{field.reason} {field.sourceFields.join(", ")}</td>
          </tr>)}</tbody></table>
      </div>
    </details>
    <details><summary>Company-input coverage by method</summary>
      <ul>{basis.methodInputs.map(method => <li key={method.method}>
        <strong>{method.method.toUpperCase()}</strong>: {method.reason}
        {method.hasPositiveBase && !method.hasPerShareInputs && " Per-share output is unavailable because cash/debt or diluted shares are missing."}
      </li>)}</ul>
    </details>
    <ul>{basis.warnings.map(warning => <li key={warning}>{warning}</li>)}</ul>
  </section>;
}
