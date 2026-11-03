import { DataStateNotices, ErrorState, Panel } from "@/components/page";
import { PortfolioPerformancePanel } from "@/components/portfolio-performance-panel";
import { PortfolioRiskReturnPanel } from "@/components/portfolio-risk-return-panel";
import type { Portfolio, PortfolioAnalytics, PortfolioOpportunityCost, PortfolioPerformance, PortfolioPeriodAttribution, PortfolioRiskReturn, PortfolioSnapshot } from "@/lib/api/portfolio";
import { formatNumber } from "@/lib/formatting";
import { portfolioDate } from "@/lib/portfolio-period";
import { serverFetchApiResponse } from "@/lib/server-api";

export async function PortfolioPerformanceView({ portfolio, query }: {
  portfolio: Portfolio;
  query: Record<string, string | string[] | undefined>;
}) {
  const portfolioId = portfolio.id;
  const snapshotsRes = await serverFetchApiResponse<PortfolioSnapshot[]>(`/portfolio-snapshots?portfolio_id=${portfolioId}`);
  if (!snapshotsRes.data) return <ErrorState message="Snapshots could not be loaded. No performance has been calculated." errors={snapshotsRes.errors} />;
  const snapshots = snapshotsRes.data;
  const dates = snapshots.filter(row => row.calculation_status === "complete").map(row => row.snapshot_date).sort();
  const startDate = portfolioDate(query.start_date) || dates[0] || null;
  const endDate = portfolioDate(query.end_date) || dates.at(-1) || null;
  const validPeriod = Boolean(startDate && endDate && startDate < endDate);
  const asOf = endDate || new Date().toISOString().slice(0, 10);
  const [performanceRes, attributionRes, opportunityRes, riskRes, analyticsRes] = await Promise.all([
    validPeriod ? serverFetchApiResponse<PortfolioPerformance>(`/portfolios/${portfolioId}/performance?start_date=${startDate}&end_date=${endDate}`) : null,
    validPeriod ? serverFetchApiResponse<PortfolioPeriodAttribution>(`/portfolios/${portfolioId}/period-attribution?start_date=${startDate}&end_date=${endDate}`) : null,
    validPeriod ? serverFetchApiResponse<PortfolioOpportunityCost>(`/portfolios/${portfolioId}/opportunity-cost?start_date=${startDate}&end_date=${endDate}`) : null,
    serverFetchApiResponse<PortfolioRiskReturn>(`/portfolios/${portfolioId}/risk-return-comparison?as_of_date=${asOf}`),
    serverFetchApiResponse<PortfolioAnalytics>(`/portfolios/${portfolioId}/analytics`),
  ]);
  const analytics = analyticsRes.data;
  return <>
    <DataStateNotices metas={[snapshotsRes.meta, performanceRes?.meta, attributionRes?.meta, opportunityRes?.meta, riskRes.meta, analyticsRes.meta]} />
    <PortfolioPerformancePanel snapshots={snapshots} startDate={startDate} endDate={endDate}
      requestFailed={[performanceRes, attributionRes].some(result => result && (result.errors.length > 0 || result.meta.status !== "success"))}
      performance={performanceRes?.data ?? null} attribution={attributionRes?.data ?? null} opportunityCost={opportunityRes?.data ?? null} />
    <PortfolioRiskReturnPanel comparison={riskRes.data} requestFailed={riskRes.errors.length > 0 || riskRes.meta.status !== "success"} />
    {analytics && <Panel title="Current concentration & exposure">
      <p className="muted">Calculation as of {analytics.as_of_date}. Current holdings, separate from the selected return period.</p>
      <p>Concentration (HHI): <strong>{formatNumber(analytics.concentration_score, 3)}</strong></p>
      {analytics.diversification_warnings.map(warning => <p key={warning} className="basis-note">{warning}</p>)}
      <div className="exposure-grid">{[["Sector", analytics.sector_exposure], ["Asset type", analytics.asset_type_exposure], ["Currency", analytics.currency_exposure]].map(([label, values]) => <div key={String(label)}>
        <h3>{String(label)}</h3>
        {Object.entries(values).length ? Object.entries(values).map(([name, weight]) => <div className="key-value" key={name}><span>{name}</span><strong>{formatNumber(Number(weight), 1)}%</strong></div>) : <p className="muted">Not available</p>}
      </div>)}</div>
    </Panel>}
  </>;
}
