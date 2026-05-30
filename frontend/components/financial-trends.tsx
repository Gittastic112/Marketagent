import { FinancialPeriod } from "@/lib/api";
import { Panel } from "@/components/page";

export function FinancialTrends({ trends }: { trends: FinancialPeriod[] }) {
  if (!trends || trends.length === 0) {
    return (
      <Panel title="Financial Trends">
        <div className="text-sm text-[var(--color-neutral-500)] p-4 text-center border border-dashed border-[var(--border-color)] rounded-lg">
          No financial data available.
        </div>
      </Panel>
    );
  }

  // Display top 5 recent periods
  const recentTrends = trends.slice(0, 5);

  return (
    <Panel title="Financial Trends">
      <div className="overflow-x-auto">
        <table className="min-w-full text-sm text-left">
          <thead className="bg-[var(--surface-color)] border-b border-[var(--border-color)]">
            <tr>
              <th className="px-4 py-2 font-medium text-[var(--color-neutral-600)]">Period</th>
              <th className="px-4 py-2 font-medium text-[var(--color-neutral-600)] text-right">Revenue</th>
              <th className="px-4 py-2 font-medium text-[var(--color-neutral-600)] text-right">Net Income</th>
              <th className="px-4 py-2 font-medium text-[var(--color-neutral-600)] text-right">EPS</th>
              <th className="px-4 py-2 font-medium text-[var(--color-neutral-600)] text-right">Assets</th>
              <th className="px-4 py-2 font-medium text-[var(--color-neutral-600)] text-right">Liabilities</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-[var(--border-color)]">
            {recentTrends.map((period, idx) => {
              const label = period.period_type === "quarterly" ? `Q${period.quarter} ${period.year}` : `FY ${period.year}`;
              
              const revenue = period.metrics.find(m => m.metric_name === "Revenue")?.value;
              const netIncome = period.metrics.find(m => m.metric_name === "Net Income")?.value;
              const eps = period.metrics.find(m => m.metric_name === "EPS (Basic)")?.value;
              const assets = period.metrics.find(m => m.metric_name === "Total Assets")?.value;
              const liabilities = period.metrics.find(m => m.metric_name === "Total Liabilities")?.value;
              
              const formatValue = (val: number | undefined) => {
                if (val === undefined) return "—";
                if (Math.abs(val) >= 1e9) return `$${(val / 1e9).toFixed(2)}B`;
                if (Math.abs(val) >= 1e6) return `$${(val / 1e6).toFixed(2)}M`;
                return `$${val.toFixed(2)}`;
              };

              return (
                <tr key={idx} className="hover:bg-[var(--surface-color)]">
                  <td className="px-4 py-3 font-medium">{label}</td>
                  <td className="px-4 py-3 text-right">{formatValue(revenue)}</td>
                  <td className="px-4 py-3 text-right">{formatValue(netIncome)}</td>
                  <td className="px-4 py-3 text-right">{eps !== undefined ? `$${eps.toFixed(2)}` : "—"}</td>
                  <td className="px-4 py-3 text-right">{formatValue(assets)}</td>
                  <td className="px-4 py-3 text-right">{formatValue(liabilities)}</td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </Panel>
  );
}
