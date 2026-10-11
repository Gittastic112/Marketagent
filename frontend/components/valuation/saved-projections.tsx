import type { DcfAssumptionSet } from "@/lib/api/valuation";
import { projectionColumns, projectionDescription } from "@/lib/valuation-projections";
import { buildValuationOutputState, finiteOutput, outputMoney } from "@/lib/valuation-output-state";

export function SavedProjections({ assumptions, modelType = "fcff_dcf" }: {
  assumptions: DcfAssumptionSet; modelType?: string;
}) {
  const state = buildValuationOutputState(assumptions, modelType);
  const columns = projectionColumns(modelType);
  if (state.blocked) return <p role="status">Projections are unavailable until the saved output blockers are resolved.</p>;
  if (!assumptions.projection_years?.length) return <p>No saved projections are available.</p>;
  return <section aria-label="Saved model projections">
    <h3>Saved model projections</h3>
    <p>{projectionDescription(modelType)}</p>
    <p>Currency: {state.currency}. Amounts retain the saved monetary scale; use the same scale for money and shares. No millions/billions conversion is inferred.</p>
    <div className="table-wrap" role="region" aria-label="Scrollable projection table" tabIndex={0}>
      <table style={{ minWidth: "900px", whiteSpace: "nowrap" }}>
      <thead><tr><th scope="col">Projection year</th>{columns.map(column => <th scope="col" key={column.key}>{column.label}</th>)}</tr></thead>
      <tbody>{assumptions.projection_years.map(row => <tr key={row.year_index}>
        <th scope="row">Year {row.year_index}</th>
        {columns.map(column => {
          const value = row[column.key];
          return <td key={column.key}>{column.percent
            ? finiteOutput(value) && Number.isFinite(value * 100) ? `${(value * 100).toFixed(2)}%` : "Not available"
            : outputMoney(value, state)}</td>;
        })}
      </tr>)}</tbody>
    </table></div>
  </section>;
}
