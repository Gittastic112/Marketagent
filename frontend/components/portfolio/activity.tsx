import { DataStateNotices, EmptyState, ErrorState, Panel } from "@/components/page";
import type { Portfolio, PortfolioAttributionRead, PortfolioTransaction } from "@/lib/api/portfolio";
import { formatCurrency, formatNumber } from "@/lib/formatting";
import { serverFetchApiResponse } from "@/lib/server-api";

export async function PortfolioActivity({ portfolio }: { portfolio: Portfolio }) {
  const [transactionsRes, attributionRes] = await Promise.all([
    serverFetchApiResponse<PortfolioTransaction[]>(`/portfolio-transactions?portfolio_id=${portfolio.id}`),
    serverFetchApiResponse<PortfolioAttributionRead>(`/portfolios/${portfolio.id}/attribution`),
  ]);
  const attribution = attributionRes.data;
  return <>
    <DataStateNotices metas={[transactionsRes.meta, attributionRes.meta]} />
    <Panel title="Transactions">
      {!transactionsRes.data ? <ErrorState errors={transactionsRes.errors} /> : transactionsRes.data.length === 0 ? <EmptyState label="No recorded transactions." /> : <div className="table-wrap"><table>
        <thead><tr><th>Date</th><th>Ticker</th><th>Type</th><th className="numeric">Quantity</th><th className="numeric">Price</th><th className="numeric">Fees</th><th>Notes / basis</th></tr></thead>
        <tbody>{transactionsRes.data.map(tx => <tr key={tx.id}><td>{tx.transaction_date}</td><td><strong>{tx.ticker}</strong></td><td>{tx.transaction_type.replaceAll("_", " ")}</td><td className="numeric">{formatNumber(tx.quantity, 6)}</td><td className="numeric">{formatCurrency(tx.price, tx.currency)}</td><td className="numeric">{formatCurrency(tx.fees, tx.currency)}</td><td>{tx.notes || "Not supplied"}</td></tr>)}</tbody>
      </table></div>}
    </Panel>
    {attribution && <Panel title="Recorded Activity & Unrealized Change">
      <p className="muted">Partial calculation as of {attribution.as_of_date}. Transaction activity remains separated by currency.</p>
      {attribution.warnings.map(warning => <p className="basis-note" key={warning}>{warning}</p>)}
      <div className="key-value"><span>Unrealized change since average cost</span><strong>{attribution.total_unrealized_pnl == null ? "Not available" : formatCurrency(attribution.total_unrealized_pnl, attribution.base_currency)}</strong></div>
      <p className="muted">Opportunity cost: Requires a selected benchmark series. FX impact: Requires historical FX rates. See Performance & risk for dated calculations.</p>
      <div className="table-wrap"><table>
        <thead><tr><th>Currency</th><th>Purchases</th><th>Sales</th><th>Dividends</th><th>Deposits</th><th>Withdrawals</th><th>Fees</th><th>Taxes</th></tr></thead>
        <tbody>{Object.entries(attribution.activity_by_currency).map(([currency, activity]) => <tr key={currency}><td>{currency}</td>{[activity.purchases, activity.sales, activity.dividends, activity.deposits, activity.withdrawals, activity.fees, activity.taxes].map((amount, index) => <td className="numeric" key={index}>{formatNumber(amount)}</td>)}</tr>)}</tbody>
      </table></div>
    </Panel>}
  </>;
}
