import Link from "next/link";
import { Suspense } from "react";
import { CompanyResearchCards } from "@/components/company-research-cards";
import { DataStateNotices, EmptyState, ErrorState, Panel } from "@/components/page";
import type { Portfolio, PortfolioValuation } from "@/lib/api/portfolio";
import { formatCurrency, formatNumber } from "@/lib/formatting";
import { serverFetchApiResponse } from "@/lib/server-api";

export async function PortfolioOverview({ portfolio }: { portfolio: Portfolio }) {
  const response = await serverFetchApiResponse<PortfolioValuation>(`/portfolios/${portfolio.id}/valuation`);
  const value = response.data;
  if (!value) return <ErrorState message="Portfolio values could not be loaded." errors={response.errors} />;
  const money = (amount: number | null | undefined) => amount == null ? "Not available" : formatCurrency(amount, value.base_currency);
  return <>
    <DataStateNotices metas={[response.meta]} />
    <div className="section-intro"><span className="badge">Calculation</span><span>Valued as of {value.as_of_date} using stored prices. Individual price dates are shown below; not a live quote.</span></div>
    <section className="metric-grid portfolio-metrics" aria-label="Portfolio summary">
      <div className="metric metric-featured"><div className="metric-label">Portfolio value</div><div className="metric-value">{money(value.total_portfolio_value)}</div><div className="metric-detail">Positions and cash · {value.base_currency}</div></div>
      <div className="metric"><div className="metric-label">Cost basis</div><div className="metric-value">{money(value.total_cost_basis)}</div><div className="metric-detail">Recorded average costs</div></div>
      <div className="metric"><div className="metric-label">Unrealized change</div><div className="metric-value">{money(value.total_unrealized_pnl)}</div><div className="metric-detail">Since average cost, not total return</div></div>
      <div className="metric"><div className="metric-label">Cash</div><div className="metric-value">{money(value.total_cash_value)}</div><div className="metric-detail">Stored balances converted to {value.base_currency}</div></div>
    </section>
    {value.missing_fx_pairs.length > 0 && <p className="basis-note">Missing FX: {value.missing_fx_pairs.join(", ")}. Aggregate values remain unavailable.</p>}
    <Panel title="Holdings" actions={<Link prefetch={false} href={`/portfolio/${portfolio.id}?tab=performance`}>Performance & risk →</Link>}>
      {value.holdings.length === 0 ? <EmptyState label="No active holdings. Add positions from Manage holdings." /> : <div className="table-wrap"><table>
        <caption className="sr-only">Holdings valued in {value.base_currency}; each price retains its own date and source.</caption>
        <thead><tr><th>Company</th><th className="numeric">Shares</th><th className="numeric">Price</th><th className="numeric">Value ({value.base_currency})</th><th className="numeric">Weight</th><th className="numeric">Unrealized change</th><th>Price evidence</th></tr></thead>
        <tbody>{value.holdings.map(holding => <tr key={holding.holding_id}>
          <td>{holding.company_id ? <Link href={`/companies/${holding.company_id}`}>{holding.ticker}</Link> : <strong>{holding.ticker}</strong>}</td>
          <td className="numeric">{formatNumber(holding.quantity, 6)}</td>
          <td className="numeric">{holding.market_price == null ? "Not available" : formatCurrency(holding.market_price, holding.currency)}</td>
          <td className="numeric">{money(holding.market_value_base)}</td>
          <td className="numeric">{holding.weight_percent == null ? "Not available" : `${formatNumber(holding.weight_percent, 1)}%`}</td>
          <td className="numeric">{money(holding.unrealized_pnl_base)}</td>
          <td><span className="cell-primary">{holding.market_price_as_of || "No price"}{holding.market_price != null && holding.is_stale_price && <span className="badge badge-warn">Stale</span>}</span><span className="cell-secondary">{holding.market_price_provider || "No source"}{holding.market_price_id ? ` · #${holding.market_price_id}` : ""}</span></td>
        </tr>)}</tbody>
      </table></div>}
    </Panel>
    <Suspense fallback={<p role="status">Loading company research…</p>}><CompanyResearchCards companyIds={value.holdings.flatMap(holding => holding.company_id ? [holding.company_id] : [])} /></Suspense>
    <div className="next-actions">
      <Link prefetch={false} href={`/portfolio/${portfolio.id}?tab=performance`}><strong>Understand performance</strong><span>Dated returns, attribution and risk calculations</span></Link>
      <Link prefetch={false} href={`/portfolio/${portfolio.id}?tab=setup`}><strong>Review data & setup</strong><span>Evidence quality, snapshots, benchmarks and FX</span></Link>
    </div>
  </>;
}
