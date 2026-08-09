"use client";

import { DcfSensitivityTable } from "@/lib/api";
import { formatCurrency, formatPercent } from "@/lib/formatting";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { ScrollArea } from "@/components/ui/scroll-area";
import { AlertCircle } from "lucide-react";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";

interface SensitivityTablesPanelProps {
  tables: DcfSensitivityTable[];
  currentMarketPrice?: number | null;
}

export function SensitivityTablesPanel({ tables, currentMarketPrice }: SensitivityTablesPanelProps) {
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
    if (!currentMarketPrice) return "bg-gray-50 dark:bg-gray-800 text-gray-900 dark:text-gray-100";
    const diff = (val - currentMarketPrice) / currentMarketPrice;
    if (diff > 0.2) return "bg-green-100 dark:bg-green-900/40 text-green-800 dark:text-green-300 font-medium";
    if (diff > 0.05) return "bg-green-50 dark:bg-green-900/20 text-green-700 dark:text-green-400";
    if (diff < -0.2) return "bg-red-100 dark:bg-red-900/40 text-red-800 dark:text-red-300 font-medium";
    if (diff < -0.05) return "bg-red-50 dark:bg-red-900/20 text-red-700 dark:text-red-400";
    return "bg-gray-50 dark:bg-gray-800 text-gray-900 dark:text-gray-100";
  };

  const renderTable = (table: DcfSensitivityTable) => {
    const xName = table.x_axis_json?.name || "X-Axis";
    const xValues = table.x_axis_json?.values || [];
    const yName = table.y_axis_json?.name || "Y-Axis";
    const yValues = table.y_axis_json?.values || [];
    const values = table.values_json || {};

    // Helper to format axis labels based on typical magnitude
    const formatLabel = (name: string, val: number) => {
      if (name.toLowerCase().includes("ratio") || name.toLowerCase().includes("beta")) {
        return val.toFixed(2);
      }
      // Defaults to percentage for rates, margins, WACC, etc.
      return formatPercent(val, 2);
    };

    return (
      <Card key={table.table_type} className="overflow-hidden border border-gray-200 dark:border-gray-800">
        <CardHeader className="bg-gray-50 dark:bg-gray-900 py-3 border-b border-gray-200 dark:border-gray-800">
          <CardTitle className="text-sm font-semibold text-gray-900 dark:text-gray-100">
            {yName} vs {xName}
          </CardTitle>
          <CardDescription className="text-xs">Intrinsic Value Per Share</CardDescription>
        </CardHeader>
        <CardContent className="p-0">
          <div className="overflow-x-auto">
            <table className="w-full text-xs text-right border-collapse">
              <thead>
                <tr>
                  <th className="p-2 border-r border-b border-gray-200 dark:border-gray-800 bg-gray-100 dark:bg-gray-950 font-medium text-gray-500 text-center align-middle whitespace-nowrap">
                    {yName} \ {xName}
                  </th>
                  {xValues.map((x: number) => (
                    <th key={x} className="p-2 border-b border-gray-200 dark:border-gray-800 bg-gray-50 dark:bg-gray-900 font-medium text-gray-700 dark:text-gray-300 whitespace-nowrap">
                      {formatLabel(xName, x)}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {yValues.map((y: number) => {
                  const yStr = y.toFixed(4).replace(/\.?0+$/, "");
                  return (
                    <tr key={y}>
                      <td className="p-2 border-r border-gray-200 dark:border-gray-800 bg-gray-50 dark:bg-gray-900 font-medium text-gray-700 dark:text-gray-300 text-left whitespace-nowrap">
                        {formatLabel(yName, y)}
                      </td>
                      {xValues.map((x: number) => {
                        const xStr = x.toFixed(4).replace(/\.?0+$/, "");
                        // The values dictionary from backend might have slight floating point key differences, try direct match first
                        let val = 0;
                        if (values[yStr] && values[yStr][xStr] !== undefined) {
                          val = values[yStr][xStr];
                        } else {
                           // Fallback to closest match if floating point string keys are slightly off
                           const actualYKey = Object.keys(values).find(k => Math.abs(parseFloat(k) - y) < 0.0001);
                           if (actualYKey) {
                               const actualXKey = Object.keys(values[actualYKey]).find(k => Math.abs(parseFloat(k) - x) < 0.0001);
                               if (actualXKey) val = values[actualYKey][actualXKey];
                           }
                        }

                        return (
                          <td key={x} className={`p-2 border-t border-gray-100 dark:border-gray-800/50 tabular-nums ${getCellClass(val)}`}>
                            {formatCurrency(val, "INR", 0)}
                          </td>
                        );
                      })}
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
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
            {currentMarketPrice && " Green indicates undervaluation, red indicates overvaluation."}
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-2 gap-4">
        {tables.map((table) => renderTable(table))}
      </div>
    </div>
  );
}
