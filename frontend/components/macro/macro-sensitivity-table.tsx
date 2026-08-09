import type { MacroSectorSensitivity } from "@/lib/api";

function formatNumber(value: number | null | undefined, digits = 4) {
  if (value === null || value === undefined || Number.isNaN(value)) {
    return "-";
  }
  return value.toLocaleString("en-US", { maximumFractionDigits: digits });
}

export function MacroSensitivityTable({ result }: { result: MacroSectorSensitivity }) {
  return (
    <div className="table-wrap">
      <table>
        <tbody>
          <tr>
            <th>Industry</th>
            <td>{result.industry_name}</td>
          </tr>
          <tr>
            <th>Source</th>
            <td>{result.source_file}</td>
          </tr>
          <tr>
            <th>Context</th>
            <td>{result.market} / {result.country} / {result.classification_system}</td>
          </tr>
          <tr>
            <th>Currency Context</th>
            <td>{result.currency_context ?? "-"}</td>
          </tr>
          <tr>
            <th>Raw Duration</th>
            <td>{formatNumber(result.raw_duration)}</td>
          </tr>
          <tr>
            <th>Duration Magnitude</th>
            <td>{formatNumber(result.duration_magnitude)}</td>
          </tr>
          <tr>
            <th>Interpretation</th>
            <td>{result.duration_interpretation}</td>
          </tr>
          <tr>
            <th>Firm Value Coefficients</th>
            <td>
              Duration {formatNumber(result.firm_value_duration)}, Cyclicality {formatNumber(result.firm_value_cyclicality)}, Inflation {formatNumber(result.firm_value_inflation)}, Currency {formatNumber(result.firm_value_currency)}
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  );
}
