import Link from "next/link";
import { DataStateNotices, EmptyState, ErrorState, PageHeader, Panel } from "@/components/page";
import { serverFetchApiResponse } from "@/lib/server-api";
import { loadPortfolioValuations } from "@/lib/server-portfolio";
import { PartialDataNotice, DataFreshnessIndicator } from "@/components/ui/data-states";
import type { Company, Portfolio, PortfolioHolding } from "@/lib/api";
import { formatCurrency } from "@/lib/formatting";

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
    const [portfoliosRes, holdingsRes, companiesRes] = await Promise.all([
      serverFetchApiResponse<Portfolio[]>("/portfolios").catch(() => null),
      serverFetchApiResponse<PortfolioHolding[]>("/portfolio-holdings").catch(() => null),
      serverFetchApiResponse<Company[]>("/companies").catch(() => null)
    ]);
    const portfolios = portfoliosRes?.data || [];
    const holdings = holdingsRes?.data || [];
    const companies = companiesRes?.data || [];

    if (!portfoliosRes?.data) return <><PageHeader eyebrow="Portfolio research" title="Portfolios" /><ErrorState message="Your portfolios could not be loaded." errors={portfoliosRes?.errors} /></>;
    const portfoliosById = new Map(portfolios.map((portfolio) => [portfolio.id, portfolio]));
    const companiesById = new Map(companies.map((company) => [company.id, company]));

    const valuationsRes = await loadPortfolioValuations(portfolios);
    const valuations = valuationsRes.map(res => res?.data);
    const valuationsById = new Map(
      valuations.filter(Boolean).map((v) => [v!.portfolio_id, v!])
    );

    const getHoldingValuation = (holdingId: number, portfolioId: number) => {
      const val = valuationsById.get(portfolioId);
      if (!val) return null;
      return val.holdings.find(h => h.holding_id === holdingId) || null;
    };

    const missingHoldings = !holdingsRes?.data;

    return (
      <>
        <PageHeader eyebrow="Portfolio research" title="Portfolios" status={`${portfolios.length} portfolios`}
          description="Your positions, recorded activity and valuation context."
          actions={<Link prefetch={false} href="/portfolio/manage" className="secondary-button">Manage portfolios</Link>} />

        <DataStateNotices
          metas={[portfoliosRes?.meta, holdingsRes?.meta, companiesRes?.meta, ...valuationsRes.map((res) => res?.meta)]}
          mockMessage="One or more portfolio panels are using mock data. Do not treat those values as live portfolio intelligence."
        />
        {missingHoldings && <PartialDataNotice message="Holdings failed to load. The portfolio metrics below will be incomplete." />}

        {portfolios.length === 0 && (
          <Panel title="Welcome to Portfolio Intelligence">
            <EmptyState label="No portfolios exist yet." />
            <div style={{ textAlign: "center", marginTop: "1rem" }}>
              <Link prefetch={false} href="/portfolio/manage" className="btn btn-primary">
                Create your first portfolio
              </Link>
            </div>
          </Panel>
        )}

        {portfolios.length > 0 && (
          <Panel title="Portfolio Workspaces">
            <div className="brief-list">
              {portfolios.map((portfolio) => (
                <article className="brief-item" key={portfolio.id}>
                  <div className="page-header-title-row">
                    <div>
                      <h3>{portfolio.name}</h3>
                      <p className="muted">{portfolio.base_currency} base · {holdings.filter(holding => holding.portfolio_id === portfolio.id).length} recorded holdings</p>
                      <p className="portfolio-card-value">{valuationsById.get(portfolio.id)?.total_portfolio_value == null ? "Value not available" : formatCurrency(valuationsById.get(portfolio.id)!.total_portfolio_value, portfolio.base_currency)}</p>
                    </div>
                    <Link prefetch={false} className="secondary-button" href={`/portfolio/${portfolio.id}`}>
                      Open portfolio →
                    </Link>
                  </div>
                  {portfolio.description && <p className="muted">{portfolio.description}</p>}
                </article>
              ))}
            </div>
          </Panel>
        )}

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
                if (!hVal || hVal.market_value_base == null || hVal.weight_percent == null) continue;

                if (!company || !company.exposure_tags || company.exposure_tags.length === 0) {
                  untaggedValue += hVal.market_value_base;
                  untaggedPercent += hVal.weight_percent;
                } else {
                  for (const tag of company.exposure_tags) {
                    const current = tagExposures.get(tag.name) || { value: 0, percent: 0 };
                    tagExposures.set(tag.name, {
                      value: current.value + hVal.market_value_base,
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
                <p className="muted">Calculation from priced holdings in {portfolio.base_currency}. Tags can overlap, so tag weights need not total 100%.</p>
                {sortedTags.length === 0 && untaggedValue === 0 ? (
                  <p className="text-sm text-gray-500">No exposure data calculated.</p>
                ) : (
                  <div tabIndex={0} className="table-wrap">
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
          {missingHoldings ? <ErrorState message="Holdings could not be loaded." errors={holdingsRes?.errors} /> : holdings.length === 0 ? (
            <EmptyState label="No holdings yet." />
          ) : (
            <div tabIndex={0} className="table-wrap">
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
                    <th>Price as of</th>
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
                        {val?.valuation_status === "trusted" && val.intrinsic_value != null ? (
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
                        {val?.valuation_status === "trusted" ? (
                          <span className="badge badge-success">Trusted</span>
                        ) : val?.valuation_status === "stale" ? (
                          <span className="badge badge-warning" title={val.valuation_status_reason || val.stale_valuation_reason || "Valuation requires review"}>Stale</span>
                        ) : val?.valuation_status === "untrusted" ? (
                          <span className="badge badge-warning" title={val.valuation_status_reason || "Valuation output failed a trust gate"}>Untrusted</span>
                        ) : (
                          <span className="badge" title={val?.valuation_status_reason || "No completed Base DCF output"}>Unavailable</span>
                        )}
                      </td>
                      <td>{val?.market_price_as_of || "Not available"}</td>
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
  } catch {
    return (
      <>
        <PageHeader eyebrow="Portfolio" title="Portfolio" />
        <ErrorState message="Could not load portfolio records from the backend API." />
      </>
    );
  }
}
