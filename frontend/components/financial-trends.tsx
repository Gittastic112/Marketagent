import type { ApiResponse } from "@/lib/api/contract";
import type { FinancialStatementPeriod } from "@/lib/api/financials";
import { DataStateNotices, EmptyState, ErrorState, Panel } from "@/components/page";
import { formatNumber } from "@/lib/formatting";

const metrics = ["Revenue", "Net Income", "EPS (Basic)", "Total Assets", "Total Liabilities"];

export function FinancialTrends({ response, companyId }: {
  response: ApiResponse<FinancialStatementPeriod[]>;
  companyId: number;
}) {
  const failed = response.errors.length > 0 || response.meta.status !== "success";
  const recent = failed ? [] : [...(response.data || [])]
    .sort((a, b) => b.year - a.year || (b.quarter ?? 0) - (a.quarter ?? 0)).slice(0, 5);

  return (
    <Panel title="Financial Trends">
      {failed ? <ErrorState message="Financial history could not be loaded." errors={response.errors} /> : <>
        <DataStateNotices metas={[response.meta]} />
        {recent.length === 0 ? <EmptyState label="No recorded financial periods." /> : <>
          <p className="muted">Recorded metrics may be unreviewed. Values retain their stored units without currency conversion or rescaling.</p>
          <div tabIndex={0} className="table-wrap">
            <table>
              <thead><tr><th>Period and basis</th>{metrics.map(name => <th key={name}>{name}</th>)}</tr></thead>
              <tbody>{recent.map(period => <tr key={period.id}>
                <td>{period.period_type === "quarterly" ? `Q${period.quarter} ${period.year}` : `FY ${period.year}`}
                  <div className="muted">Report date: {period.report_date}</div>
                  <div className="muted">{period.currency || "Currency unknown"} · Currency basis: {period.currency_source || "unknown"}
                    {" "}({period.currency_confidence || "unknown"} confidence)</div>
                </td>
                {metrics.map(name => {
                  const matches = period.metrics.filter(metric => metric.metric_name === name);
                  const metric = matches.length === 1 ? matches[0] : null;
                  return <td key={name}>{metric && Number.isFinite(metric.value)
                    ? <>{formatNumber(metric.value, 6)}<div className="muted">{metric.unit || "Unit unknown"}</div></>
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
