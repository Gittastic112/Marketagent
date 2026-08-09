import Link from "next/link";
import { notFound } from "next/navigation";

import {
  capturePortfolioSnapshot,
  createPortfolioCashBalance,
  deletePortfolioCashBalanceWithState,
  deletePortfolioSnapshotWithState,
  updatePortfolioCashBalance
} from "@/app/actions";
import { DeleteRecordForm } from "@/components/delete-record-form";
import { TextField } from "@/components/form-fields";
import { EmptyState, PageHeader, Panel } from "@/components/page";
import { PortfolioPerformanceSetup } from "@/components/portfolio-performance-setup";
import type {
  FxRateObservation,
  Portfolio,
  PortfolioAnalytics,
  PortfolioAttributionRead,
  PortfolioBenchmarkConfig,
  PortfolioCashBalance,
  PortfolioHolding,
  PortfolioSnapshot,
  PortfolioTransaction
} from "@/lib/api";
import { serverFetchApi, serverFetchApiResponse } from "@/lib/server-api";
import { DataFreshnessIndicator } from "@/components/ui/data-states";

function numberText(value: number): string {
  return value.toLocaleString("en-US", { maximumFractionDigits: 6 });
}

export default async function PortfolioDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const portfolioId = parseInt(id, 10);
  if (isNaN(portfolioId)) {
    notFound();
  }

  let portfolio: Portfolio;
  try {
    portfolio = await serverFetchApi<Portfolio>(`/portfolios/${portfolioId}`);
  } catch {
    notFound();
  }

  const [holdingsRes, transactions, cashBalances, snapshots, analytics, attribution, benchmarkConfigs, directFx, inverseFx] = await Promise.all([
    serverFetchApiResponse<PortfolioHolding[]>(`/portfolio-holdings?portfolio_id=${portfolioId}`).catch(() => ({ data: [], meta: null })),
    serverFetchApi<PortfolioTransaction[]>(`/portfolio-transactions?portfolio_id=${portfolioId}`).catch(() => []),
    serverFetchApi<PortfolioCashBalance[]>(`/portfolio-cash-balances?portfolio_id=${portfolioId}`).catch(() => []),
    serverFetchApi<PortfolioSnapshot[]>(`/portfolio-snapshots?portfolio_id=${portfolioId}`).catch(() => []),
    serverFetchApi<PortfolioAnalytics>(`/portfolios/${portfolioId}/analytics`).catch(() => null),
    serverFetchApi<PortfolioAttributionRead>(`/portfolios/${portfolioId}/attribution`).catch(() => null),
    serverFetchApi<PortfolioBenchmarkConfig[]>(`/portfolio-benchmarks?portfolio_id=${portfolioId}`).catch(() => []),
    serverFetchApi<FxRateObservation[]>(`/fx-rates?quote_currency=${encodeURIComponent(portfolio.base_currency)}`).catch(() => []),
    serverFetchApi<FxRateObservation[]>(`/fx-rates?base_currency=${encodeURIComponent(portfolio.base_currency)}`).catch(() => [])
  ]);
  const holdings = holdingsRes.data || [];

  const today = new Date().toISOString().slice(0, 10);
  const fxRates = [...directFx, ...inverseFx]
    .filter((rate, index, rows) => rows.findIndex((candidate) => candidate.id === rate.id) === index)
    .sort((a, b) => b.as_of_date.localeCompare(a.as_of_date));

  return (
    <>
      <div className="breadcrumb">
        <Link href="/portfolio">← Back to Portfolios</Link>
      </div>

      <PageHeader
        eyebrow="Portfolio Details"
        title={portfolio.name}
        status={`${portfolio.base_currency}`}
      />

      {portfolio.description && (
        <div className="portfolio-description" style={{ marginBottom: "2rem" }}>
          <p>{portfolio.description}</p>
        </div>
      )}

      <section style={{ marginBottom: "2rem" }}>
        <PortfolioPerformanceSetup
          benchmark={benchmarkConfigs[0] || null}
          fxRates={fxRates}
          portfolio={portfolio}
          today={today}
        />
      </section>

      {analytics && (
        <section id="analytics" style={{ marginBottom: "2rem" }}>
          <Panel title="Portfolio Risk, Activity & Attribution">
            <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(300px, 1fr))", gap: "1rem" }}>
              {/* High-level stats */}
              <div style={{ padding: "1rem", backgroundColor: "var(--surface)", border: "1px solid var(--border)", borderRadius: "8px" }}>
                <h4 style={{ margin: "0 0 0.5rem 0", fontSize: "0.9rem", color: "var(--text-secondary)" }}>Risk & Concentration</h4>
                <div style={{ fontSize: "1.5rem", fontWeight: 600 }}>
                  {analytics.concentration_score !== null
                    ? analytics.concentration_score.toFixed(3)
                    : "N/A"}
                  <span style={{ fontSize: "0.8rem", color: "var(--text-secondary)", fontWeight: "normal", marginLeft: "0.5rem" }}>HHI Score</span>
                </div>
                {analytics.diversification_warnings?.length > 0 && (
                  <div style={{ marginTop: "0.5rem" }}>
                    {analytics.diversification_warnings.map((w, i) => (
                      <div key={i} style={{ color: "var(--warning)", fontSize: "0.8rem", marginTop: "0.2rem" }}>⚠️ {w}</div>
                    ))}
                  </div>
                )}
              </div>

              <div style={{ padding: "1rem", backgroundColor: "var(--surface)", border: "1px solid var(--border)", borderRadius: "8px" }}>
                <h4 style={{ margin: "0 0 0.5rem 0", fontSize: "0.9rem", color: "var(--text-secondary)" }}>Opportunity Cost & FX</h4>
                <div style={{ marginBottom: "0.5rem" }}>
                  <span style={{ fontSize: "1.2rem", fontWeight: 600 }}>
                    {analytics.opportunity_cost !== null
                      ? numberText(analytics.opportunity_cost)
                      : "Not configured"}
                  </span>
                  <div style={{ fontSize: "0.8rem", color: "var(--text-secondary)", marginTop: "0.25rem" }}>Requires a selected benchmark series.</div>
                </div>
                <div>
                  <span style={{ fontSize: "1.2rem", fontWeight: 600 }}>
                    {analytics.fx_impact !== null && analytics.fx_impact !== undefined
                      ? numberText(analytics.fx_impact)
                      : "Not configured"}
                  </span>
                  <div style={{ fontSize: "0.8rem", color: "var(--text-secondary)", marginTop: "0.25rem" }}>Requires historical FX rates.</div>
                </div>
              </div>
            </div>

            <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))", gap: "1rem", marginTop: "1rem" }}>
              <div style={{ padding: "1rem", backgroundColor: "var(--surface)", border: "1px solid var(--border)", borderRadius: "8px" }}>
                <h4 style={{ margin: "0 0 0.5rem 0", fontSize: "0.9rem", color: "var(--text-secondary)" }}>Sector Exposure</h4>
                {Object.entries(analytics.sector_exposure || {}).map(([sector, weight]) => (
                  <div key={sector} style={{ display: "flex", justifyContent: "space-between", fontSize: "0.85rem", marginBottom: "0.2rem" }}>
                    <span>{sector}</span>
                    <strong style={{ marginLeft: "1rem" }}>{weight.toFixed(1)}%</strong>
                  </div>
                ))}
              </div>

              <div style={{ padding: "1rem", backgroundColor: "var(--surface)", border: "1px solid var(--border)", borderRadius: "8px" }}>
                <h4 style={{ margin: "0 0 0.5rem 0", fontSize: "0.9rem", color: "var(--text-secondary)" }}>Asset Type Exposure</h4>
                {Object.entries(analytics.asset_type_exposure || {}).map(([asset, weight]) => (
                  <div key={asset} style={{ display: "flex", justifyContent: "space-between", fontSize: "0.85rem", marginBottom: "0.2rem" }}>
                    <span>{asset}</span>
                    <strong style={{ marginLeft: "1rem" }}>{weight.toFixed(1)}%</strong>
                  </div>
                ))}
              </div>

              <div style={{ padding: "1rem", backgroundColor: "var(--surface)", border: "1px solid var(--border)", borderRadius: "8px" }}>
                <h4 style={{ margin: "0 0 0.5rem 0", fontSize: "0.9rem", color: "var(--text-secondary)" }}>Currency Exposure</h4>
                {Object.entries(analytics.currency_exposure || {}).map(([currency, weight]) => (
                  <div key={currency} style={{ display: "flex", justifyContent: "space-between", fontSize: "0.85rem", marginBottom: "0.2rem" }}>
                    <span>{currency}</span>
                    <strong style={{ marginLeft: "1rem" }}>{weight.toFixed(1)}%</strong>
                  </div>
                ))}
              </div>

              {attribution && attribution.attribution_by_geography && (
                <div style={{ padding: "1rem", backgroundColor: "var(--surface)", border: "1px solid var(--border)", borderRadius: "8px" }}>
                  <h4 style={{ margin: "0 0 0.5rem 0", fontSize: "0.9rem", color: "var(--text-secondary)" }}>Geography Exposure</h4>
                  {Object.entries(attribution.attribution_by_geography).map(([geo, weight]) => (
                    <div key={geo} style={{ display: "flex", justifyContent: "space-between", fontSize: "0.85rem", marginBottom: "0.2rem" }}>
                      <span>{geo}</span>
                      <strong style={{ marginLeft: "1rem" }}>{weight.toFixed(1)}%</strong>
                    </div>
                  ))}
                </div>
              )}
            </div>

            {attribution && (
              <div style={{ marginTop: "2rem" }}>
                <h3 style={{ fontSize: "1.1rem", marginBottom: "0.5rem" }}>Recorded Activity & Unrealized Change</h3>
                <p style={{ color: "var(--text-secondary)", marginTop: 0 }}>
                  Partial calculation as of {attribution.as_of_date}. Transaction activity remains separated by currency.
                </p>
                {attribution.warnings.length > 0 && (
                  <div style={{ marginBottom: "1rem" }}>
                    {attribution.warnings.map((warning) => (
                      <div key={warning} style={{ color: "var(--warning)", fontSize: "0.85rem", marginTop: "0.25rem" }}>⚠️ {warning}</div>
                    ))}
                  </div>
                )}
                <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(150px, 1fr))", gap: "1rem" }}>
                  <div style={{ padding: "1rem", backgroundColor: "var(--surface)", border: "1px solid var(--border)", borderRadius: "8px" }}>
                    <div style={{ fontSize: "0.8rem", color: "var(--text-secondary)", marginBottom: "0.2rem" }}>Unrealized Change Since Average Cost</div>
                    <div style={{ fontSize: "1.2rem", fontWeight: 600 }}>
                      {attribution.components.price_movement !== null
                        ? `${attribution.base_currency} ${numberText(attribution.components.price_movement)}`
                        : "Not available"}
                    </div>
                  </div>
                  <div style={{ padding: "1rem", backgroundColor: "var(--surface)", border: "1px solid var(--border)", borderRadius: "8px" }}>
                    <div style={{ fontSize: "0.8rem", color: "var(--text-secondary)", marginBottom: "0.2rem" }}>FX Impact</div>
                    <div style={{ fontSize: "1.2rem", fontWeight: 600 }}>
                      {attribution.components.fx_impact !== null
                        ? `${attribution.base_currency} ${numberText(attribution.components.fx_impact)}`
                        : "Not configured"}
                    </div>
                  </div>
                  <div style={{ padding: "1rem", backgroundColor: "var(--surface)", border: "1px solid var(--border)", borderRadius: "8px", borderLeft: "4px solid var(--primary)" }}>
                    <div style={{ fontSize: "0.8rem", color: "var(--text-secondary)", marginBottom: "0.2rem" }}>Total Unrealized P&amp;L</div>
                    <div style={{ fontSize: "1.2rem", fontWeight: 600 }}>
                      {attribution.total_unrealized_pnl !== null
                        ? `${attribution.base_currency} ${numberText(attribution.total_unrealized_pnl)}`
                        : "Not available"}
                    </div>
                  </div>
                </div>

                {Object.entries(attribution.activity_by_currency).length > 0 ? (
                  <div className="table-wrap" style={{ marginTop: "1rem" }}>
                    <table>
                      <thead>
                        <tr>
                          <th>Currency</th>
                          <th>Purchases</th>
                          <th>Sales</th>
                          <th>Dividends</th>
                          <th>Deposits</th>
                          <th>Withdrawals</th>
                          <th>Fees</th>
                          <th>Taxes</th>
                        </tr>
                      </thead>
                      <tbody>
                        {Object.entries(attribution.activity_by_currency).map(([currency, activity]) => (
                          <tr key={currency}>
                            <td><strong>{currency}</strong></td>
                            <td>{numberText(activity.purchases)}</td>
                            <td>{numberText(activity.sales)}</td>
                            <td>{numberText(activity.dividends)}</td>
                            <td>{numberText(activity.deposits)}</td>
                            <td>{numberText(activity.withdrawals)}</td>
                            <td>{numberText(activity.fees)}</td>
                            <td>{numberText(activity.taxes)}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                ) : (
                  <EmptyState label="No recorded transactions are available for this attribution date." />
                )}
              </div>
            )}
          </Panel>
        </section>
      )}

      <div style={{ display: "flex", gap: "2rem", flexDirection: "column" }}>
        {/* Cash Balances Section */}
        <section id="cash">
          <Panel title="Cash Balances">
            <details style={{ marginBottom: "1rem" }}>
              <summary>Add Cash Balance</summary>
              <form action={createPortfolioCashBalance} className="form-grid">
                <input name="portfolio_id" type="hidden" value={portfolio.id} />
                <TextField defaultValue={portfolio.base_currency} id="cash-currency" label="Currency" name="currency" required />
                <TextField id="cash-amount" label="Amount" name="amount" required step="0.000001" type="number" />
                <TextField defaultValue={today} id="cash-as-of-date" label="As Of Date" name="as_of_date" required type="date" />
                <div className="button-row">
                  <button type="submit">Add Cash</button>
                </div>
              </form>
            </details>

            {cashBalances.length === 0 ? (
              <EmptyState label="No cash balances yet." />
            ) : (
              <div className="table-wrap">
                <table>
                  <thead>
                    <tr>
                      <th>Currency</th>
                      <th>Amount</th>
                      <th>As Of Date</th>
                      <th>Action</th>
                    </tr>
                  </thead>
                  <tbody>
                    {cashBalances.map((cash) => (
                      <tr key={cash.id}>
                        <td>{cash.currency}</td>
                        <td>{numberText(cash.amount)}</td>
                        <td>{cash.as_of_date}</td>
                        <td>
                          <div className="action-stack">
                            <details className="edit-panel">
                              <summary>Edit</summary>
                              <form action={updatePortfolioCashBalance} className="inline-form">
                                <input name="id" type="hidden" value={cash.id} />
                                <TextField defaultValue={cash.currency} id={`cash-currency-${cash.id}`} label="Currency" name="currency" required />
                                <TextField defaultValue={cash.amount.toString()} id={`cash-amount-${cash.id}`} label="Amount" name="amount" required step="0.000001" type="number" />
                                <TextField defaultValue={cash.as_of_date} id={`cash-date-${cash.id}`} label="As Of Date" name="as_of_date" required type="date" />
                                <div className="button-row">
                                  <button className="secondary-button" type="submit">Save</button>
                                </div>
                              </form>
                            </details>
                            <DeleteRecordForm action={deletePortfolioCashBalanceWithState} recordId={cash.id} />
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </Panel>
        </section>

        {/* Snapshots Section */}
        <section id="snapshots">
          <Panel title="Point-in-Time Snapshots">
            <p style={{ color: "var(--text-secondary)", marginTop: 0 }}>
              Capture derives totals from stored holdings, prices, cash, and historical FX. Incomplete captures remain visible but are blocked from precise performance calculations.
            </p>
            <form action={capturePortfolioSnapshot} className="form-grid" style={{ marginBottom: "1rem" }}>
              <input name="portfolio_id" type="hidden" value={portfolio.id} />
              <TextField defaultValue={today} id="snapshot-capture-date" label="Capture Date" name="as_of_date" required type="date" />
              <div className="button-row"><button type="submit">Capture Snapshot</button></div>
            </form>

            {snapshots.length === 0 ? (
              <EmptyState label="No point-in-time snapshots yet. Capture at least two dates to calculate period performance." />
            ) : (
              <div className="table-wrap">
                <table>
                  <thead>
                    <tr>
                      <th>Date</th>
                      <th>Status</th>
                      <th>Total Value</th>
                      <th>Market Value</th>
                      <th>Cost Basis</th>
                      <th>Cash</th>
                      <th>Coverage</th>
                      <th>Blockers</th>
                      <th>Action</th>
                    </tr>
                  </thead>
                  <tbody>
                    {[...snapshots].sort((a, b) => b.snapshot_date.localeCompare(a.snapshot_date)).map((snap) => (
                      <tr key={snap.id}>
                        <td>{snap.snapshot_date}</td>
                        <td><strong>{snap.calculation_status.replaceAll("_", " ")}</strong></td>
                        <td>{snap.total_portfolio_value != null ? `${snap.base_currency || portfolio.base_currency} ${numberText(snap.total_portfolio_value)}` : "Not available"}</td>
                        <td>{snap.total_market_value != null ? numberText(snap.total_market_value) : "-"}</td>
                        <td>{snap.total_cost_basis != null ? numberText(snap.total_cost_basis) : "-"}</td>
                        <td>{snap.total_cash != null ? numberText(snap.total_cash) : "-"}</td>
                        <td>{snap.priced_holdings_count}/{snap.holdings_count} holdings priced</td>
                        <td>
                          {[...snap.missing_price_tickers_json.map((ticker) => `Price: ${ticker}`), ...snap.missing_fx_pairs_json.map((pair) => `FX: ${pair}`)].join(", ") || "None"}
                        </td>
                        <td>
                          <DeleteRecordForm action={deletePortfolioSnapshotWithState} recordId={snap.id} />
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </Panel>
        </section>

        <section id="holdings">
          <Panel title="Holdings">
            <div style={{ marginBottom: "1rem" }}>
              <DataFreshnessIndicator meta={holdingsRes.meta ?? undefined} source="Portfolio API" />
            </div>
            {holdings.length === 0 ? (
              <EmptyState label="No holdings found for this portfolio." />
            ) : (
              <div className="table-wrap">
                <table>
                  <thead>
                    <tr>
                      <th>Ticker</th>
                      <th>Quantity</th>
                      <th>Avg Cost</th>
                      <th>Currency</th>
                      <th>As Of</th>
                    </tr>
                  </thead>
                  <tbody>
                    {holdings.map((holding) => (
                      <tr key={holding.id}>
                        <td>{holding.ticker}</td>
                        <td>{numberText(holding.quantity)}</td>
                        <td>{numberText(holding.average_cost)}</td>
                        <td>{holding.currency}</td>
                        <td>
                          {holding.as_of_date}
                          {holding.as_of_date !== today && (
                            <span style={{ color: "var(--warning)", marginLeft: "0.5rem", fontSize: "0.8rem", padding: "0.1rem 0.4rem", border: "1px solid var(--warning)", borderRadius: "4px" }}>Stale Price</span>
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </Panel>
        </section>

        <section id="transactions">
          <Panel title="Transactions">
            {transactions.length === 0 ? (
              <EmptyState label="No transactions found for this portfolio." />
            ) : (
              <div className="table-wrap">
                <table>
                  <thead>
                    <tr>
                      <th>Ticker</th>
                      <th>Type</th>
                      <th>Quantity</th>
                      <th>Price</th>
                      <th>Fees</th>
                      <th>Date</th>
                      <th>Notes</th>
                    </tr>
                  </thead>
                  <tbody>
                    {transactions.map((tx) => (
                      <tr key={tx.id}>
                        <td>{tx.ticker}</td>
                        <td>{tx.transaction_type}</td>
                        <td>{numberText(tx.quantity)}</td>
                        <td>{numberText(tx.price)}</td>
                        <td>{numberText(tx.fees)}</td>
                        <td>{tx.transaction_date}</td>
                        <td>{tx.notes ?? "-"}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </Panel>
        </section>
      </div>
    </>
  );
}
