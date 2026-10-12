"use client";

import { DcfSensitivityTable } from "@/lib/api";
import { formatCurrency, formatPercent } from "@/lib/formatting";
import { sensitivityAxis, sensitivityCell, sensitivityMethod } from "@/lib/sensitivity-table";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { AlertCircle } from "lucide-react";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";

interface SensitivityTablesPanelProps {
  tables: DcfSensitivityTable[];
  currentMarketPrice?: number | null;
  currency?: string;
}

export function SensitivityTablesPanel({ tables, currentMarketPrice, currency = "USD" }: SensitivityTablesPanelProps) {
  if (!tables || tables.length === 0) {
    return (
      <Alert>
        <AlertCircle className="h-4 w-4" />
        <AlertTitle>No Data</AlertTitle>
        <AlertDescription>Sensitivity tables have not been generated for this assumption set.</AlertDescription>
      </Alert>
    );
  }

  // Helper to determine cell color based on upside/downside
  const getCellClass = (val: number) => {
    if (typeof currentMarketPrice !== "number" || !Number.isFinite(currentMarketPrice) || currentMarketPrice <= 0) return "bg-gray-50 dark:bg-gray-800 text-gray-900 dark:text-gray-100";
    const diff = (val - currentMarketPrice) / currentMarketPrice;
    if (diff > 0.2) return "bg-green-100 dark:bg-green-900/40 text-green-800 dark:text-green-300 font-medium";
    if (diff > 0.05) return "bg-green-50 dark:bg-green-900/20 text-green-700 dark:text-green-400";
    if (diff < -0.2) return "bg-red-100 dark:bg-red-900/40 text-red-800 dark:text-red-300 font-medium";
    if (diff < -0.05) return "bg-red-50 dark:bg-red-900/20 text-red-700 dark:text-red-400";
    return "bg-gray-50 dark:bg-gray-800 text-gray-900 dark:text-gray-100";
  };

  const renderTable = (table: DcfSensitivityTable) => {
    const xName = table.x_axis_json?.name || "X-Axis";
    const xValues = sensitivityAxis(table.x_axis_json?.values);
    const yName = table.y_axis_json?.name || "Y-Axis";
    const yValues = sensitivityAxis(table.y_axis_json?.values);
    const values = table.values_json || {};
    const errors = table.x_axis_json?.cell_errors;
    const method = sensitivityMethod(table.x_axis_json);
    const reasons = [...new Set(yValues.flatMap(y => xValues.map(x => sensitivityCell(values, errors, x, y).reason)).filter((reason): reason is string => Boolean(reason)))];

    // Helper to format axis labels based on typical magnitude
    const formatLabel = (name: string, val: number) => {
      if (name.toLowerCase().includes("ratio") || name.toLowerCase().includes("beta")) {
        return val.toFixed(2);
      }
      // Defaults to percentage for rates, margins, WACC, etc.
      return formatPercent(val, 2);
    };

    return (
      <Card key={table.table_type} className="sensitivity-card overflow-hidden border border-gray-200 dark:border-gray-800">
        <CardHeader className="bg-gray-50 dark:bg-gray-900 py-3 border-b border-gray-200 dark:border-gray-800">
          <CardTitle className="text-sm font-semibold text-gray-900 dark:text-gray-100">
            {yName} vs {xName}
          </CardTitle>
          <CardDescription className="text-xs">Calculated value per share ({currency}). Saved assumption set #{table.assumption_set_id}.</CardDescription>
          <p className="text-xs text-muted-foreground">
            {method ? "Canonical FCFF sensitivity v2. Funding shocks preserve saved WACC differences and terminal ROIC." : "Historical calculation: its sensitivity method is unverified. Save a new reviewed calculation to use the current method."}
            {table.created_at && Number.isFinite(Date.parse(table.created_at)) && ` Calculated ${new Date(table.created_at).toLocaleString()}.`}
          </p>
          {method && Array.isArray(method.defaulted_fields) && method.defaulted_fields.length > 0 && <p className="text-xs text-muted-foreground">Some absent inputs use documented legacy defaults; review the saved assumptions before relying on these results.</p>}
        </CardHeader>
        <CardContent className="p-0">
          <div className="sensitivity-table-wrap">
            <table className="sensitivity-matrix w-full text-xs text-right border-collapse">
              <caption className="sr-only">{yName} versus {xName}, calculated {currency} per share from saved assumptions</caption>
              <thead>
                <tr>
                  <th className="p-2 border-r border-b border-gray-200 dark:border-gray-800 bg-gray-100 dark:bg-gray-950 font-medium text-gray-500 text-center align-middle whitespace-nowrap">
                    {yName} \ {xName}
                  </th>
                  {xValues.map((x: number) => (
                    <th scope="col" key={x} className="p-2 border-b border-gray-200 dark:border-gray-800 bg-gray-50 dark:bg-gray-900 font-medium text-gray-700 dark:text-gray-300 whitespace-nowrap">
                      {formatLabel(xName, x)}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {yValues.map((y: number) => {
                  return (
                    <tr key={y}>
                      <th scope="row" className="p-2 border-r border-gray-200 dark:border-gray-800 bg-gray-50 dark:bg-gray-900 font-medium text-gray-700 dark:text-gray-300 text-left whitespace-nowrap">
                        {formatLabel(yName, y)}
                      </th>
                      {xValues.map((x: number) => {
                        const { value: val, reason } = sensitivityCell(values, errors, x, y);

                        return (
                          <td key={x} title={reason || undefined} aria-label={val === null ? `Not available: ${reason}` : undefined} className={`p-2 border-t border-gray-100 dark:border-gray-800/50 tabular-nums ${val === null ? "sensitivity-missing" : getCellClass(val)}`}>
                            {val === null ? "N/A" : formatCurrency(val, currency, 0)}
                          </td>
                        );
                      })}
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
          {(!xValues.length || !yValues.length) && <p className="p-3 text-sm">The saved grid has no valid axes. Save a new reviewed calculation.</p>}
          {reasons.length > 0 && <details className="p-3 text-xs"><summary className="cursor-pointer">Why some cells are unavailable</summary><ul className="mt-2 list-disc pl-4">{reasons.map(reason => <li key={reason}>{reason}</li>)}</ul></details>}
        </CardContent>
      </Card>
    );
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white">Sensitivity Matrices</h3>
          <p className="text-sm text-gray-500 dark:text-gray-400">
            Evaluating the intrinsic value per share across key parameter intersections.
            {typeof currentMarketPrice === "number" && Number.isFinite(currentMarketPrice) && currentMarketPrice > 0 && " Colors compare calculated values with the saved assumed market price. They do not establish investment value or a recommendation."}
          </p>
        </div>
      </div>

      <div className="sensitivity-grid">
        {tables.map((table) => renderTable(table))}
      </div>
    </div>
  );
}
