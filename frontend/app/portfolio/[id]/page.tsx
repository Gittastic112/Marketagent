import Link from "next/link";
import { notFound } from "next/navigation";

import {
  createPortfolioCashBalance,
  createPortfolioSnapshot,
  deletePortfolioCashBalanceWithState,
  deletePortfolioSnapshotWithState,
  updatePortfolioCashBalance,
  updatePortfolioSnapshot
} from "@/app/actions";
import { DeleteRecordForm } from "@/components/delete-record-form";
import { SelectField, TextAreaField, TextField } from "@/components/form-fields";
import { EmptyState, ErrorState, PageHeader, Panel } from "@/components/page";
import { fetchApi } from "@/lib/api";
import type {
  Portfolio,
  PortfolioCashBalance,
  PortfolioHolding,
  PortfolioSnapshot,
  PortfolioTransaction
} from "@/lib/api";

function numberText(value: number): string {
  return value.toLocaleString("en-US", { maximumFractionDigits: 6 });
}

export default async function PortfolioDetailPage({ params }: { params: { id: string } }) {
  const portfolioId = parseInt(params.id, 10);
  if (isNaN(portfolioId)) {
    notFound();
  }

  let portfolio: Portfolio;
  try {
    portfolio = await fetchApi<Portfolio>(`/portfolios/${portfolioId}`);
  } catch {
    notFound();
  }

  const [holdings, transactions, cashBalances, snapshots] = await Promise.all([
    fetchApi<PortfolioHolding[]>(`/portfolio-holdings?portfolio_id=${portfolioId}`),
    fetchApi<PortfolioTransaction[]>(`/portfolio-transactions?portfolio_id=${portfolioId}`),
    fetchApi<PortfolioCashBalance[]>(`/portfolio-cash-balances?portfolio_id=${portfolioId}`),
    fetchApi<PortfolioSnapshot[]>(`/portfolio-snapshots?portfolio_id=${portfolioId}`)
  ]);

  const today = new Date().toISOString().slice(0, 10);

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
          <Panel title="Snapshots">
            <details style={{ marginBottom: "1rem" }}>
              <summary>Add Snapshot</summary>
              <form action={createPortfolioSnapshot} className="form-grid">
                <input name="portfolio_id" type="hidden" value={portfolio.id} />
                <TextField defaultValue={today} id="snapshot-date" label="Snapshot Date" name="snapshot_date" required type="date" />
                <TextField id="snapshot-market-value" label="Total Market Value" min="0" name="total_market_value" step="0.000001" type="number" />
                <TextField id="snapshot-cost-basis" label="Total Cost Basis" min="0" name="total_cost_basis" step="0.000001" type="number" />
                <TextField id="snapshot-cash" label="Total Cash" name="total_cash" step="0.000001" type="number" />
                <TextAreaField className="field field-wide" id="snapshot-payload" label="Payload (JSON)" name="payload_json" />
                <div className="button-row">
                  <button type="submit">Add Snapshot</button>
                </div>
              </form>
            </details>

            {snapshots.length === 0 ? (
              <EmptyState label="No snapshots yet." />
            ) : (
              <div className="table-wrap">
                <table>
                  <thead>
                    <tr>
                      <th>Date</th>
                      <th>Market Value</th>
                      <th>Cost Basis</th>
                      <th>Cash</th>
                      <th>Action</th>
                    </tr>
                  </thead>
                  <tbody>
                    {snapshots.map((snap) => (
                      <tr key={snap.id}>
                        <td>{snap.snapshot_date}</td>
                        <td>{snap.total_market_value != null ? numberText(snap.total_market_value) : "-"}</td>
                        <td>{snap.total_cost_basis != null ? numberText(snap.total_cost_basis) : "-"}</td>
                        <td>{snap.total_cash != null ? numberText(snap.total_cash) : "-"}</td>
                        <td>
                          <div className="action-stack">
                            <details className="edit-panel">
                              <summary>Edit</summary>
                              <form action={updatePortfolioSnapshot} className="inline-form">
                                <input name="id" type="hidden" value={snap.id} />
                                <TextField defaultValue={snap.snapshot_date} id={`snap-date-${snap.id}`} label="Date" name="snapshot_date" required type="date" />
                                <TextField defaultValue={snap.total_market_value?.toString() ?? ""} id={`snap-mv-${snap.id}`} label="Market Value" min="0" name="total_market_value" step="0.000001" type="number" />
                                <TextField defaultValue={snap.total_cost_basis?.toString() ?? ""} id={`snap-cb-${snap.id}`} label="Cost Basis" min="0" name="total_cost_basis" step="0.000001" type="number" />
                                <TextField defaultValue={snap.total_cash?.toString() ?? ""} id={`snap-cash-${snap.id}`} label="Cash" name="total_cash" step="0.000001" type="number" />
                                <TextAreaField className="field field-full" defaultValue={snap.payload_json ? JSON.stringify(snap.payload_json) : ""} id={`snap-payload-${snap.id}`} label="Payload JSON" name="payload_json" />
                                <div className="button-row">
                                  <button className="secondary-button" type="submit">Save</button>
                                </div>
                              </form>
                            </details>
                            <DeleteRecordForm action={deletePortfolioSnapshotWithState} recordId={snap.id} />
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

        <section id="holdings">
          <Panel title="Holdings">
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
                        <td>{holding.as_of_date}</td>
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
