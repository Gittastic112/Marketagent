import { EmptyState, ErrorState, Panel } from "@/components/page";
import { snapshotReplayLabel } from "@/lib/portfolio-replay";
import type {
  PortfolioOpportunityCost,
  PortfolioPerformance,
  PortfolioPeriodAttribution,
  PortfolioSnapshot,
} from "@/lib/api";


function money(value: number | null, currency: string | null) {
  if (value == null) return "Not available";
  return `${currency || ""} ${value.toLocaleString("en-US", { maximumFractionDigits: 2 })}`.trim();
}

function percent(value: number | null) {
  return value == null ? "Not available" : `${(value * 100).toFixed(2)}%`;
}

function Metric({ label, value, detail }: { label: string; value: string; detail?: string }) {
  return (
    <div style={{ border: "1px solid var(--border)", borderRadius: "8px", padding: "1rem", background: "var(--surface)" }}>
      <div style={{ color: "var(--text-secondary)", fontSize: "0.8rem" }}>{label}</div>
      <div style={{ fontSize: "1.2rem", fontWeight: 600, marginTop: "0.25rem" }}>{value}</div>
      {detail && <p className="cell-secondary" style={{ margin: "0.35rem 0 0" }}>{detail}</p>}
    </div>
  );
}

export function PortfolioPerformancePanel({
  snapshots,
  startDate,
  endDate,
  performance,
  attribution,
  opportunityCost,
  requestFailed = false,
}: {
  snapshots: PortfolioSnapshot[];
  startDate: string | null;
  endDate: string | null;
  performance: PortfolioPerformance | null;
  attribution: PortfolioPeriodAttribution | null;
  opportunityCost: PortfolioOpportunityCost | null;
  requestFailed?: boolean;
}) {
  const completeSnapshots = snapshots.filter((snapshot) => snapshot.calculation_status === "complete");
  return (
    <Panel title="Period Performance & Attribution">
      {completeSnapshots.some(snapshot => snapshotReplayLabel(snapshot) !== "Recorded activity reconciled") && <p className="basis-note">Legacy history: replay unverified. Returns from these stored snapshots remain provisional until recorded activity is reconciled.</p>}
      {completeSnapshots.length < 2 ? (
        <EmptyState label="Capture at least two complete snapshots on different dates before calculating period performance." />
      ) : (
        <>
          <form className="form-grid" method="get" style={{ marginBottom: "1.5rem" }}>
            <input type="hidden" name="tab" value="performance" />
            <label className="field"><span>Start Date</span><input defaultValue={startDate || ""} name="start_date" required type="date" /></label>
            <label className="field"><span>End Date</span><input defaultValue={endDate || ""} name="end_date" required type="date" /></label>
            <div className="button-row"><button type="submit">Calculate Period</button></div>
          </form>

          {requestFailed ? <ErrorState message="Performance data could not be loaded. Retry Calculate Period." /> : !performance || !attribution ? (
            <EmptyState label="The selected period is unavailable. Choose two complete snapshot dates with the end date after the start date." />
          ) : (
            <>
              <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))", gap: "0.75rem" }}>
                <Metric label={`TWR: selected period (${performance.time_weighted_return.calculation_status})`}
                  value={percent(performance.time_weighted_return.return_decimal)}
                  detail={`Period: ${performance.time_weighted_return.start_date || "Not available"} to ${performance.time_weighted_return.end_date}. Not annualized.`} />
                <Metric label={`MWR: annualized (${performance.money_weighted_return.calculation_status})`}
                  value={percent(performance.money_weighted_return.return_decimal)}
                  detail={`Since first cash flow: ${performance.money_weighted_return.start_date || "Not available"} to ${performance.money_weighted_return.end_date}.`} />
                <Metric label="Portfolio Change" value={money(attribution.total_change, attribution.base_currency)} />
                <Metric label="Price Movement" value={money(attribution.price_movement, attribution.base_currency)} />
                <Metric label="FX Impact" value={money(attribution.fx_impact, attribution.base_currency)} />
                <Metric label="Position Change" value={money(attribution.position_change, attribution.base_currency)} />
                <Metric label="External Cash Flow" value={money(attribution.external_cash_flow, attribution.base_currency)} />
                <Metric label="Internal Cash Change" value={money(attribution.internal_cash_change, attribution.base_currency)} />
                <Metric label="Reconciliation Residual" value={money(attribution.unexplained_change, attribution.base_currency)} />
                <Metric
                  label={`Opportunity Cost (${opportunityCost?.calculation_status || "not available"})`}
                  value={money(opportunityCost?.opportunity_cost ?? null, attribution.base_currency)}
                />
              </div>

              <div style={{ marginTop: "1rem", padding: "1rem", border: "1px solid var(--border)", borderRadius: "8px" }}>
                <strong>Attribution confidence: {attribution.confidence}</strong>
                <div style={{ color: "var(--text-secondary)", marginTop: "0.35rem" }}>{attribution.formula}</div>
                {attribution.blockers.length > 0 && <div style={{ color: "var(--danger)", marginTop: "0.5rem" }}>Blockers: {attribution.blockers.join(", ")}</div>}
                {[...performance.time_weighted_return.warnings, ...performance.money_weighted_return.warnings, ...attribution.warnings, ...(opportunityCost?.warnings || [])]
                  .filter((warning, index, rows) => rows.indexOf(warning) === index)
                  .map((warning) => <div key={warning} style={{ color: "var(--warning)", marginTop: "0.35rem" }}>⚠ {warning}</div>)}
              </div>

              {attribution.holdings.length > 0 && (
                <div className="table-wrap" style={{ marginTop: "1rem" }}>
                  <table>
                    <thead><tr><th>Holding</th><th>Price</th><th>FX</th><th>Position</th><th>Total</th><th>Status</th></tr></thead>
                    <tbody>
                      {attribution.holdings.map((holding) => (
                        <tr key={holding.key}>
                          <td>{holding.ticker || holding.key}</td>
                          <td>{money(holding.price_movement, attribution.base_currency)}</td>
                          <td>{money(holding.fx_impact, attribution.base_currency)}</td>
                          <td>{money(holding.position_change, attribution.base_currency)}</td>
                          <td>{money(holding.total_contribution, attribution.base_currency)}</td>
                          <td>{holding.calculation_status}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}

              <details style={{ marginTop: "1rem" }}>
                <summary>Calculation sources</summary>
                <p>Snapshots: {attribution.source_snapshot_ids.join(", ") || "None"}</p>
                <p>Transactions: {attribution.source_transaction_ids.join(", ") || "None"}</p>
                <p>Benchmark prices: {opportunityCost?.source_market_price_ids.join(", ") || "None"}</p>
              </details>
            </>
          )}
        </>
      )}
    </Panel>
  );
}
