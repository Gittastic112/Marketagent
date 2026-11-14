import type { ApiResponse } from "@/lib/api/contract";
import type { FinancialStatementPeriod } from "@/lib/api/financials";
import { DataStateNotices, EmptyState, ErrorState, Panel } from "@/components/page";
import { formatDataLabel, formatNumber } from "@/lib/formatting";

const metrics = ["Revenue", "Net Income", "EPS (Basic)", "Total Assets", "Total Liabilities"];
const overviewMetrics = ["Revenue", "Operating income", "Net income", "Depreciation amortization", "Capex"];
const metricKey = (name: string) => {
  const key = name.replaceAll("_", " ").toLowerCase();
  // Promoted records use these canonical codes. Narrower source scopes stay separate.
  if (key === "ebit") return "operating income";
  if (key === "depreciation") return "depreciation amortization";
  return key;
};

export function FinancialTrends({ response, companyId, compact = false }: {
  response: ApiResponse<FinancialStatementPeriod[]>;
  companyId: number;
  compact?: boolean;
}) {
  const failed = response.errors.length > 0 || response.meta.status !== "success";
  const recent = failed ? [] : [...(response.data || [])]
    .sort((a, b) => b.year - a.year || (b.quarter ?? 0) - (a.quarter ?? 0)).slice(0, 5);
  const hasMetric = (name: string) => recent.some(period => period.metrics.some(metric => metricKey(metric.metric_name) === metricKey(name)));
  const columns = compact ? overviewMetrics.filter(hasMetric) : metrics;
  const missingSummary = compact ? overviewMetrics.slice(0, 3).filter(name => !hasMetric(name)) : [];

  return (
    <Panel title="Financial Trends">
      {failed ? <ErrorState message="Financial history could not be loaded." errors={response.errors} /> : <>
        <DataStateNotices metas={[response.meta]} />
        {recent.length === 0 ? <EmptyState label="No recorded financial periods." /> : <>
          <p className="muted">Recorded metrics may be unreviewed. {compact
            ? "Large currency amounts are rounded for display; inspect a value for its exact amount. Source units are preserved."
            : "Values retain their stored units without currency conversion or rescaling."}</p>
          {missingSummary.length > 0 && <p className="basis-note">Summary gaps: {missingSummary.join(", ")}. Review financial sources for the missing inputs.</p>}
          <div tabIndex={0} className="table-wrap" role="region" aria-label="Financial trends by period">
            <table className="financial-trends-table">
              <thead><tr><th>Period and basis</th>{columns.map(name => <th key={name}>{name === "Depreciation amortization" ? "D&A" : name}</th>)}</tr></thead>
              <tbody>{recent.map(period => <tr key={period.id}>
                <td>{period.period_type === "quarterly" ? `${period.quarter ? `Q${period.quarter}` : "Quarter unknown"} ${period.year}` : `FY ${period.year}`}
                  <div className="muted">Report date: {period.report_date}</div>
                  <div className="muted">{period.currency || "Currency unknown"} · Currency basis: {formatDataLabel(period.currency_source || "unknown")}
                    {" "}({period.currency_confidence || "unknown"} confidence)</div>
                </td>
                {columns.map(name => {
                  const matches = period.metrics.filter(metric =>
                    metricKey(metric.metric_name) === metricKey(name));
                  const metric = matches.length === 1 ? matches[0] : null;
                  const shortened = compact && metric && /^[A-Z]{3}$/.test(metric.unit || "") && Math.abs(metric.value) >= 1_000_000;
                  return <td key={name} className="numeric">{metric && Number.isFinite(metric.value)
                    ? <>{shortened ? <details className="financial-exact-value"><summary>{new Intl.NumberFormat("en-US", { notation: "compact", maximumFractionDigits: 2 }).format(metric.value)}</summary><span>Exact: {formatNumber(metric.value, 6)}</span></details> : formatNumber(metric.value, 6)}<div className="muted">{metric.unit || "Unit unknown"}</div></>
                    : matches.length > 1 ? "Conflicting records" : "Not available"}</td>;
                })}
              </tr>)}</tbody>
            </table>
          </div>
        </>}
      </>}
      <a href={`/companies/${companyId}/fundamentals`}>Review financial sources and normalized coverage</a>
    </Panel>
  );
}
