"use client";

import { useEffect, useState } from "react";
import { getDcfScenarios, DcfScenarioOutput } from "@/lib/api";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { formatCurrency, formatPercent } from "@/lib/formatting";
import { Loader2, AlertCircle } from "lucide-react";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";

interface ScenarioRangePanelProps {
  modelId: number;
  assumptionId: number;
  currentMarketPrice?: number | null;
}

export function ScenarioRangePanel({ modelId, assumptionId, currentMarketPrice }: ScenarioRangePanelProps) {
  const [scenarios, setScenarios] = useState<DcfScenarioOutput[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let mounted = true;
    async function load() {
      setLoading(true);
      try {
        const data = await getDcfScenarios(modelId, assumptionId);
        if (mounted) {
          setScenarios(data);
          setError(null);
        }
      } catch (err: any) {
        if (mounted) setError(err.message || "Failed to load scenarios");
      } finally {
        if (mounted) setLoading(false);
      }
    }
    load();
    return () => { mounted = false; };
  }, [modelId, assumptionId]);

  if (loading) {
    return (
      <div className="flex items-center justify-center p-12">
        <Loader2 className="h-8 w-8 animate-spin text-gray-400" />
        <span className="ml-3 text-sm text-gray-500">Generating scenario range...</span>
      </div>
    );
  }

  if (error) {
    return (
      <Alert>
        <AlertCircle className="h-4 w-4" />
        <AlertTitle>Error</AlertTitle>
        <AlertDescription>{error}</AlertDescription>
      </Alert>
    );
  }

  // Sort scenarios by intrinsic value
  const sortedScenarios = [...scenarios].sort((a, b) =>
    (b.output.intrinsic_value_per_share || 0) - (a.output.intrinsic_value_per_share || 0)
  );

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white">Valuation Range</h3>
          <p className="text-sm text-gray-500 dark:text-gray-400">
            Comparing automated scenarios generated from your base assumptions.
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {sortedScenarios.map((scenario) => {
          const val = scenario.output.intrinsic_value_per_share || 0;
          let diffPct = null;
          let isUndervalued = false;
          if (currentMarketPrice && currentMarketPrice > 0) {
            diffPct = (val - currentMarketPrice) / currentMarketPrice;
            isUndervalued = val > currentMarketPrice;
          }

          return (
            <Card key={scenario.scenario_name} className="overflow-hidden border border-gray-200 dark:border-gray-800">
              <CardHeader className="bg-gray-50 dark:bg-gray-900 py-3 border-b border-gray-200 dark:border-gray-800">
                <CardTitle className="text-md font-semibold text-gray-900 dark:text-gray-100">
                  {scenario.scenario_name}
                </CardTitle>
                <CardDescription className="text-xs line-clamp-2" title={scenario.description}>
                  {scenario.description}
                </CardDescription>
              </CardHeader>
              <CardContent className="p-4 flex flex-col items-center justify-center space-y-2">
                <div className="text-3xl font-bold tracking-tight text-gray-900 dark:text-white tabular-nums">
                  {formatCurrency(val, "INR", 0)}
                </div>
                {diffPct !== null && (
                  <div className={`text-sm font-medium ${isUndervalued ? 'text-green-600' : 'text-red-600'}`}>
                    {diffPct > 0 ? "+" : ""}{formatPercent(diffPct, 1)} vs Market
                  </div>
                )}
              </CardContent>
            </Card>
          )
        })}
      </div>
    </div>
  );
}
