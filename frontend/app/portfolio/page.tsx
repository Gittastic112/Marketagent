import Link from "next/link";
import { EmptyState, ErrorState, MockDataState, PageHeader, Panel } from "@/components/page";
import { serverFetchApiResponse } from "@/lib/server-api";
import { StaleDataBanner, PartialDataNotice, DataFreshnessIndicator } from "@/components/ui/data-states";
import { summarizeApiMetas } from "@/lib/data-state-meta";
import type { Company, Portfolio, PortfolioHolding, PortfolioTransaction, PortfolioValuation, PortfolioAnalytics } from "@/lib/api";
import { PortfolioAnalyticsDashboard } from "@/components/portfolio-analytics";
import { CsvImporter } from "@/components/csv-importer";

export default async function PortfolioPage() {
  function numberText(value: number): string {
    return value.toLocaleString("en-US", { maximumFractionDigits: 6 });
  }

  function companyLabel(companyId: number | null, companiesById: Map<number, Company>): string {
    if (companyId === null) {
      return "-";
    }
    return companiesById.get(companyId)?.ticker ?? `#${companyId}`;
  }

  try {
    const [portfoliosRes, holdingsRes, transactionsRes, companiesRes] = await Promise.all([
      serverFetchApiResponse<Portfolio[]>("/portfolios").catch(() => null),
      serverFetchApiResponse<PortfolioHolding[]>("/portfolio-holdings").catch(() => null),
      serverFetchApiResponse<PortfolioTransaction[]>("/portfolio-transactions").catch(() => null),
      serverFetchApiResponse<Company[]>("/companies").catch(() => null)
    ]);
    const portfolios = portfoliosRes?.data || [];
    const holdings = holdingsRes?.data || [];
    const transactions = transactionsRes?.data || [];
    const companies = companiesRes?.data || [];

    const baseDataState = summarizeApiMetas([
      portfoliosRes?.meta,
      holdingsRes?.meta,
      transactionsRes?.meta,
      companiesRes?.meta
    ]);

    const today = new Date().toISOString().slice(0, 10);
    const portfoliosById = new Map(portfolios.map((portfolio) => [portfolio.id, portfolio]));
    const companiesById = new Map(companies.map((company) => [company.id, company]));

    const valuationsRes = await Promise.all(
      portfolios.map((portfolio) =>
        serverFetchApiResponse<PortfolioValuation>(`/portfolios/${portfolio.id}/valuation`).catch(() => null)
      )
    );
    const valuations = valuationsRes.map(res => res?.data);
    const valuationsById = new Map(
      valuations.filter(Boolean).map((v) => [v!.portfolio_id, v!])
    );

    const getHoldingValuation = (holdingId: number, portfolioId: number) => {
      const val = valuationsById.get(portfolioId);
      if (!val) return null;
      return val.holdings.find(h => h.holding_id === holdingId) || null;
    };

    const analyticsResponses = await Promise.all(
      portfolios.map((portfolio) =>
        serverFetchApiResponse<PortfolioAnalytics>(`/portfolios/${portfolio.id}/analytics`).catch(() => null)
      )
    );
    const analyticsResults = analyticsResponses.map(res => res?.data);
    const validAnalytics = analyticsResults.filter((a): a is PortfolioAnalytics => a !== null);

    const snapshotsRes = await Promise.all(
      portfolios.map((portfolio) =>
        serverFetchApiResponse<any[]>(`/portfolio-snapshots?portfolio_id=${portfolio.id}`).catch(() => null)
      )
    );
    const fullDataState = summarizeApiMetas([
      portfoliosRes?.meta,
      holdingsRes?.meta,
      transactionsRes?.meta,
      companiesRes?.meta,
      ...valuationsRes.map((res) => res?.meta),
      ...analyticsResponses.map((res) => res?.meta),
      ...snapshotsRes.map((res) => res?.meta)
    ]);
    const snapshotsResults = snapshotsRes.map(res => res?.data || []);

    const missingHoldings = !holdingsRes;
    const snapshotsById = new Map(portfolios.map((p, i) => [p.id, snapshotsResults[i]]));

    return (
      <>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-end" }}>
          <PageHeader eyebrow="Portfolio Intelligence" title="Overview" status={`${portfolios.length} portfolios`} />
          <div style={{ marginBottom: "2rem" }}>
            <Link href="/portfolio/manage" className="btn btn-outline">
              Manage Portfolios & Transactions
            </Link>
          </div>
        </div>

        {baseDataState.allStale && <StaleDataBanner />}
        {!baseDataState.allStale && fullDataState.someStale && <PartialDataNotice message="Some portfolio components are showing cached data because the backend is partially reachable." />}
        {missingHoldings && <PartialDataNotice message="Holdings failed to load. The portfolio metrics below will be incomplete." />}
        {fullDataState.hasMock && <MockDataState message="One or more portfolio panels are using mock data. Do not treat those values as live portfolio intelligence." />}

        {portfolios.length === 0 && (
          <Panel title="Welcome to Portfolio Intelligence">
            <EmptyState label="No portfolios exist yet." />
            <div style={{ textAlign: "center", marginTop: "1rem" }}>
              <Link href="/portfolio/manage" className="btn btn-primary">
                Create your first portfolio
              </Link>
            </div>
          </Panel>
        )}

        {validAnalytics.map(analytics => {
          const portfolioName = portfoliosById.get(analytics.portfolio_id)?.name ?? `#${analytics.portfolio_id}`;
          const snaps = snapshotsById.get(analytics.portfolio_id) || [];
          return (
            <Panel key={analytics.portfolio_id} title={`Analytics: ${portfolioName}`}>
              <PortfolioAnalyticsDashboard analytics={analytics} snapshots={snaps} />
            </Panel>
          );
        })}

        <Panel title="Exposure Summary">
          {portfolios.map(portfolio => {
            const portfolioHoldings = holdings.filter(h => h.portfolio_id === portfolio.id);
            if (portfolioHoldings.length === 0) return null;

            // Group by tag
            const tagExposures = new Map<string, { value: number, percent: number }>();
            let untaggedValue = 0;
            let untaggedPercent = 0;
            const val = valuationsById.get(portfolio.id);

            if (val) {
              for (const h of portfolioHoldings) {
                const company = companiesById.get(h.company_id!);
                const hVal = val.holdings.find(vh => vh.holding_id === h.id);
                if (!hVal || hVal.market_value == null || hVal.weight_percent == null) continue;

                if (!company || !company.exposure_tags || company.exposure_tags.length === 0) {
                  untaggedValue += hVal.market_value;
                  untaggedPercent += hVal.weight_percent;
                } else {
                  for (const tag of company.exposure_tags) {
                    const current = tagExposures.get(tag.name) || { value: 0, percent: 0 };
                    tagExposures.set(tag.name, {
                      value: current.value + hVal.market_value,
                      percent: current.percent + hVal.weight_percent
                    });
                  }
                }
              }
            }

            const sortedTags = Array.from(tagExposures.entries()).sort((a, b) => b[1].percent - a[1].percent);

            return (
              <div key={`exp-${portfolio.id}`} className="mb-8 last:mb-0">
                <h3 className="text-lg font-medium mb-4">{portfolio.name} Exposures</h3>
                {sortedTags.length === 0 && untaggedValue === 0 ? (
                  <p className="text-sm text-gray-500">No exposure data calculated.</p>
                ) : (
                  <div className="table-wrap">
                    <table>
                      <thead>
                        <tr>
                          <th>Exposure Tag</th>
                          <th className="text-right">Value ({portfolio.base_currency})</th>
                          <th className="text-right">Weight</th>
                        </tr>
                      </thead>
                      <tbody>
                        {sortedTags.map(([tagName, data]) => (
                          <tr key={tagName}>
                            <td>{tagName}</td>
                            <td className="text-right">{numberText(data.value)}</td>
                            <td className="text-right">{numberText(data.percent)}%</td>
                          </tr>
                        ))}
                        {untaggedValue > 0 && (
                          <tr className="text-gray-500">
                            <td><em>Untagged</em></td>
                            <td className="text-right">{numberText(untaggedValue)}</td>
                            <td className="text-right">{numberText(untaggedPercent)}%</td>
                          </tr>
                        )}
                      </tbody>
                    </table>
                  </div>
                )}
              </div>
            );
          })}
        </Panel>

        <Panel title="Holdings">
          <div style={{ marginBottom: "1rem" }}>
            <DataFreshnessIndicator meta={holdingsRes?.meta} source="Portfolio API" />
          </div>
          {holdings.length === 0 ? (
            <EmptyState label="No holdings yet." />
          ) : (
            <div className="table-wrap">
              <table>
                <thead>
                  <tr>
                    <th>Portfolio</th>
                    <th>Ticker</th>
                    <th>Company</th>
                    <th>Quantity</th>
                    <th>Average Cost</th>
                    <th>Market Price</th>
                    <th>Intrinsic Value</th>
                    <th>Market Value</th>
                    <th>Unrealized P&L</th>
                    <th>Weight</th>
                    <th>Thesis</th>
                    <th>Alerts</th>
                    <th>Valuation</th>
                    <th>As Of</th>
                  </tr>
                </thead>
                <tbody>
                  {holdings.map((holding) => {
                    const val = getHoldingValuation(holding.id, holding.portfolio_id);
                    return (
                    <tr key={holding.id}>
                      <td>{portfoliosById.get(holding.portfolio_id)?.name ?? `#${holding.portfolio_id}`}</td>
                      <td>{holding.ticker}</td>
                      <td>{companyLabel(holding.company_id, companiesById)}</td>
                      <td>{numberText(holding.quantity)}</td>
                      <td>
                        {holding.currency} {numberText(holding.average_cost)}
                      </td>
                      <td>
                        {val?.market_price != null ? (
                          <>
                            {holding.currency} {numberText(val.market_price)}
                            {val.is_stale_price && <span className="badge badge-warning" title="Stale price" style={{marginLeft: "4px"}}>⚠️</span>}
                          </>
                        ) : (
                          "-"
                        )}
                      </td>
                      <td>
                        {val?.intrinsic_value != null ? (
                          <span style={{ color: val.market_price != null && val.intrinsic_value > val.market_price ? "var(--color-green-700)" : "var(--color-red-700)" }}>
                            {holding.currency} {numberText(val.intrinsic_value)}
                          </span>
                        ) : "-"}
                      </td>
                      <td>
                        {val?.market_value != null ? `${holding.currency} ${numberText(val.market_value)}` : "-"}
                      </td>
                      <td>
                        {val?.unrealized_pnl != null ? (
                          <span style={{ color: val.unrealized_pnl >= 0 ? "var(--color-green-700)" : "var(--color-red-700)" }}>
                            {holding.currency} {numberText(val.unrealized_pnl)}
                            {val.unrealized_pnl_percent != null && ` (${numberText(val.unrealized_pnl_percent)}%)`}
                          </span>
                        ) : "-"}
                      </td>
                      <td>
                        {val?.weight_percent != null ? `${numberText(val.weight_percent)}%` : "-"}
                      </td>
                      <td>
                        {val?.thesis_status ? (
                          <span className={`badge ${val.thesis_status === 'active' ? 'badge-success' : 'badge-warning'}`}>{val.thesis_status}</span>
                        ) : "-"}
                      </td>
                      <td>
                        {val?.active_alerts_count ? (
                          <span className="badge badge-error" title={`${val.active_alerts_count} active alerts`}>
                            ⚠️ {val.active_alerts_count}
                          </span>
                        ) : "-"}
                      </td>
                      <td>
                        {val?.is_valuation_stale ? (
                           <span className="badge badge-warning" title={val.stale_valuation_reason || "Valuation broken by market event"}>⚠️ Stale</span>
                        ) : (
                           <span className="badge badge-success">Valid</span>
                        )}
                      </td>
                      <td>{holding.as_of_date}</td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          )}
        </Panel>
      </>
    );
  } catch (error: any) {
    console.error("PAGE RENDER ERROR:", error);
    return (
      <>
        <PageHeader eyebrow="Portfolio" title="Portfolio" />
        <ErrorState message={`Could not load portfolio records from the backend API. Error: ${error?.message || error}`} />
      </>
    );
  }
}
