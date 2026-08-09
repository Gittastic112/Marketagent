import {
  createFxRateObservation,
  createPortfolioBenchmark,
  deleteFxRateObservation,
  deletePortfolioBenchmark,
  updatePortfolioBenchmark,
} from "@/app/actions";
import { TextAreaField, TextField } from "@/components/form-fields";
import { EmptyState, Panel } from "@/components/page";
import type { FxRateObservation, Portfolio, PortfolioBenchmarkConfig } from "@/lib/api";


export function PortfolioPerformanceSetup({
  portfolio,
  benchmark,
  fxRates,
  today,
}: {
  portfolio: Portfolio;
  benchmark: PortfolioBenchmarkConfig | null;
  fxRates: FxRateObservation[];
  today: string;
}) {
  const benchmarkAction = benchmark ? updatePortfolioBenchmark : createPortfolioBenchmark;
  return (
    <Panel title="Performance Data Setup">
      <p style={{ color: "var(--text-secondary)", marginTop: 0 }}>
        Period returns require complete dated snapshots. Cross-currency portfolios also require historical FX, and opportunity cost requires one explicit benchmark.
      </p>
      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(320px, 1fr))", gap: "1.5rem" }}>
        <section>
          <h3 style={{ marginTop: 0 }}>Benchmark</h3>
          <form action={benchmarkAction} className="form-grid">
            <input name="portfolio_id" type="hidden" value={portfolio.id} />
            {benchmark && <input name="id" type="hidden" value={benchmark.id} />}
            <TextField defaultValue={benchmark?.ticker || ""} id="benchmark-ticker" label="Ticker" name="ticker" required />
            <TextField defaultValue={benchmark?.currency || portfolio.base_currency} id="benchmark-currency" label="Currency" name="currency" required />
            <TextField defaultValue={benchmark?.provider_name || "manual"} id="benchmark-provider" label="Provider" name="provider_name" required />
            <TextField defaultValue={benchmark?.provider_symbol || ""} id="benchmark-provider-symbol" label="Provider Symbol" name="provider_symbol" />
            <TextField defaultValue={benchmark?.effective_from || today} id="benchmark-effective" label="Effective From" name="effective_from" required type="date" />
            {benchmark && (
              <label style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
                <input defaultChecked={benchmark.active} name="active" type="checkbox" /> Active
              </label>
            )}
            <TextAreaField defaultValue={benchmark?.notes || ""} id="benchmark-notes" label="Notes" name="notes" />
            <div className="button-row">
              <button type="submit">{benchmark ? "Update Benchmark" : "Set Benchmark"}</button>
            </div>
          </form>
          {benchmark && (
            <form action={deletePortfolioBenchmark} style={{ marginTop: "0.75rem" }}>
              <input name="id" type="hidden" value={benchmark.id} />
              <input name="portfolio_id" type="hidden" value={portfolio.id} />
              <button className="button-secondary" type="submit">Remove Benchmark</button>
            </form>
          )}
        </section>

        <section>
          <h3 style={{ marginTop: 0 }}>Historical FX</h3>
          <form action={createFxRateObservation} className="form-grid">
            <input name="portfolio_id" type="hidden" value={portfolio.id} />
            <TextField id="fx-base" label="Base Currency" name="base_currency" placeholder="INR" required />
            <TextField defaultValue={portfolio.base_currency} id="fx-quote" label="Quote Currency" name="quote_currency" required />
            <TextField id="fx-rate" label="Quote Units per 1 Base Unit" name="rate" required step="0.0000000001" type="number" />
            <TextField defaultValue={today} id="fx-date" label="As Of Date" name="as_of_date" required type="date" />
            <TextField defaultValue="manual" id="fx-provider" label="Provider" name="provider_name" required />
            <TextField id="fx-source" label="Source URL" name="source_url" type="url" />
            <div className="button-row"><button type="submit">Record FX Observation</button></div>
          </form>
        </section>
      </div>

      <section style={{ marginTop: "1.5rem" }}>
        <h3>Available FX Observations</h3>
        {fxRates.length === 0 ? (
          <EmptyState label={`No historical FX observations involving ${portfolio.base_currency}. Add dated observations for every non-base holding and cash currency.`} />
        ) : (
          <div className="table-wrap">
            <table>
              <thead><tr><th>Pair</th><th>Date</th><th>Rate</th><th>Provider</th><th>Source</th><th>Action</th></tr></thead>
              <tbody>
                {fxRates.slice(0, 20).map((rate) => (
                  <tr key={rate.id}>
                    <td>{rate.base_currency}/{rate.quote_currency}</td>
                    <td>{rate.as_of_date}</td>
                    <td>{rate.rate}</td>
                    <td>{rate.provider_name}</td>
                    <td>{rate.source_url ? <a href={rate.source_url} rel="noreferrer" target="_blank">Open source</a> : "Not recorded"}</td>
                    <td>
                      <form action={deleteFxRateObservation}>
                        <input name="id" type="hidden" value={rate.id} />
                        <input name="portfolio_id" type="hidden" value={portfolio.id} />
                        <button className="button-secondary" type="submit">Delete</button>
                      </form>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>
    </Panel>
  );
}
