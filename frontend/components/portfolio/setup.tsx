import { capturePortfolioSnapshot, createPortfolioCashBalance, deletePortfolioCashBalanceWithState, deletePortfolioSnapshotWithState, updatePortfolioCashBalance } from "@/app/actions";
import { snapshotReplayLabel } from "@/lib/portfolio-replay";
import { DeleteRecordForm } from "@/components/delete-record-form";
import { TextField } from "@/components/form-fields";
import { DataStateNotices, EmptyState, ErrorState, Panel } from "@/components/page";
import { PortfolioPerformanceSetup } from "@/components/portfolio-performance-setup";
import { PortfolioRealInputReadinessPanel } from "@/components/portfolio-real-input-readiness-panel";
import { PortfolioEvidenceImporter } from "@/components/portfolio/portfolio-evidence-importer";
import type { FxRateObservation, Portfolio, PortfolioBenchmarkConfig, PortfolioCashBalance, PortfolioRealInputReadiness, PortfolioSnapshot } from "@/lib/api/portfolio";
import { formatNumber } from "@/lib/formatting";
import { serverFetchApiResponse } from "@/lib/server-api";

const numberText = (value: number) => formatNumber(value, 6);

export async function PortfolioSetup({ portfolio }: { portfolio: Portfolio }) {
  const portfolioId = portfolio.id;
  const today = new Date().toISOString().slice(0, 10);
  const [cashBalancesRes, snapshotsRes, benchmarksRes, directFxRes, inverseFxRes, readinessRes] = await Promise.all([
    serverFetchApiResponse<PortfolioCashBalance[]>(`/portfolio-cash-balances?portfolio_id=${portfolioId}`),
    serverFetchApiResponse<PortfolioSnapshot[]>(`/portfolio-snapshots?portfolio_id=${portfolioId}`),
    serverFetchApiResponse<PortfolioBenchmarkConfig[]>(`/portfolio-benchmarks?portfolio_id=${portfolioId}`),
    serverFetchApiResponse<FxRateObservation[]>(`/fx-rates?quote_currency=${encodeURIComponent(portfolio.base_currency)}`),
    serverFetchApiResponse<FxRateObservation[]>(`/fx-rates?base_currency=${encodeURIComponent(portfolio.base_currency)}`),
    serverFetchApiResponse<PortfolioRealInputReadiness>(`/portfolios/${portfolioId}/real-input-readiness`),
  ]);
  const cashBalances = cashBalancesRes.data || [];
  const snapshots = snapshotsRes.data || [];
  const fxRates = [...(directFxRes.data || []), ...(inverseFxRes.data || [])]
    .filter((rate, index, rows) => rows.findIndex(row => row.id === rate.id) === index)
    .sort((a, b) => b.as_of_date.localeCompare(a.as_of_date));
  return <>
    <DataStateNotices metas={[cashBalancesRes.meta, snapshotsRes.meta, benchmarksRes.meta, directFxRes.meta, inverseFxRes.meta]} />
    <PortfolioRealInputReadinessPanel meta={readinessRes.meta} report={readinessRes.data} />
    <details className="disclosure"><summary>Import evidence bundle</summary><PortfolioEvidenceImporter portfolioId={portfolioId} /></details>
    {benchmarksRes.data && directFxRes.data && inverseFxRes.data
      ? <PortfolioPerformanceSetup benchmark={benchmarksRes.data[0] || null} fxRates={fxRates} portfolio={portfolio} today={today} />
      : <ErrorState message="Benchmark / FX setup could not be loaded. Retry before changing configuration." />}
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

            {cashBalancesRes.data === null ? <ErrorState message="Cash balances could not be loaded." errors={cashBalancesRes.errors} /> : cashBalances.length === 0 ? (
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
              Capture replays recorded activity through the selected date and uses dated prices and FX. Stored status describes the capture time; later activity corrections make dependent performance provisional until recaptured. Missing history remains visibly unverified.
            </p>
            <form action={capturePortfolioSnapshot} className="form-grid" style={{ marginBottom: "1rem" }}>
              <input name="portfolio_id" type="hidden" value={portfolio.id} />
              <TextField defaultValue={today} id="snapshot-capture-date" label="Capture Date" name="as_of_date" required type="date" />
              <div className="button-row"><button type="submit">Capture Snapshot</button></div>
            </form>

            {snapshotsRes.data === null ? <ErrorState message="Snapshots could not be loaded." errors={snapshotsRes.errors} /> : snapshots.length === 0 ? (
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
                        <td><strong>{snap.calculation_status.replaceAll("_", " ")}</strong><span className="cell-secondary">{snapshotReplayLabel(snap)}</span></td>
                        <td>{snap.total_portfolio_value != null ? `${snap.base_currency || portfolio.base_currency} ${numberText(snap.total_portfolio_value)}` : "Not available"}</td>
                        <td>{snap.total_market_value != null ? numberText(snap.total_market_value) : "-"}</td>
                        <td>{snap.total_cost_basis != null ? numberText(snap.total_cost_basis) : "-"}</td>
                        <td>{snap.total_cash != null ? numberText(snap.total_cash) : "-"}</td>
                        <td>{snap.priced_holdings_count}/{snap.holdings_count} holdings priced</td>
                        <td>
                          {[...snap.missing_price_tickers_json.map((ticker) => `Price: ${ticker}`), ...snap.missing_fx_pairs_json.map((pair) => `FX: ${pair}`)].join(", ") || (snapshotReplayLabel(snap) === "Recorded activity reconciled" ? "None" : "Review activity coverage")}
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


  </>;
}
