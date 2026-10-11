import { finiteOutput, outputGap, outputMoney, type ValuationOutputState } from "@/lib/valuation-output-state";

const secondary = { color: "var(--text-secondary)", fontSize: "0.85rem", lineHeight: 1.5 };
const row = { padding: "0.75rem 0", borderBottom: "1px solid var(--line)" };

export function SavedValuationOutputCard({ state }: { state: ValuationOutputState }) {
  const out = state.output;
  const price = out?.current_market_price;
  // A stored price remains inspectable as a User Assumption, not a trusted output.
  const savedPrice = finiteOutput(price) && price > 0 && state.currency
    && out?.assumption_set_id === state.assumptionId
    ? new Intl.NumberFormat("en-US", { style: "currency", currency: state.currency }).format(price) : "Not available";
  return <section aria-label="Saved valuation output" className={`valuation-output-card ${state.blocked ? "is-blocked" : ""}`} style={{ minWidth: 0, overflowWrap: "anywhere" }}>
    <h3>Saved valuation output</h3>
    <p style={secondary}>Estimate from saved User Assumptions. Unsaved edits are not used.</p>
    {state.blocked && <div role="status" style={secondary}>{state.reasons.map(reason => <p key={reason}>{reason}</p>)}</div>}
    <dl>
      <div style={row}><dt>Intrinsic value <small>(Estimate per share)</small></dt>
        <dd className="valuation-output-value" style={{ margin: 0 }}>{outputMoney(out?.intrinsic_value_per_share, state)}</dd></div>
      {out?.base_dcf_value != null && <div style={row}><dt>Base DCF value <small>(Calculation, total equity)</small></dt>
        <dd style={{ margin: 0 }}>{outputMoney(out.base_dcf_value, state)}</dd></div>}
      {out?.pv_of_excess_returns != null && <div style={row}><dt>PV of excess returns <small>(Calculation, total equity)</small></dt>
        <dd style={{ margin: 0 }}>{outputMoney(out.pv_of_excess_returns, state)}</dd></div>}
      <div style={row}><dt>Saved comparison price <small>(User Assumption)</small></dt>
        <dd style={{ margin: 0 }}>{savedPrice}</dd>
        <p style={secondary}>This is not a live quote. Its source and market as-of time are not established by this saved output.</p></div>
      <div style={row}><dt>Gap to saved price <small>(Calculation)</small></dt>
        <dd style={{ margin: 0 }}>{outputGap(state)}</dd>
        <p style={secondary}>Stored intrinsic value / saved comparison price − 1. Not a forecast return.</p></div>
      <div style={row}><dt>Stored diagnostic score <small>(Calculation)</small></dt>
        <dd style={{ margin: 0 }}>{out && state.blocked ? "Not current" : state.score == null ? "Not available" : `${state.score}/100`}</dd>
        <p style={secondary}>Historical score, not recalculated on read and not a confidence rating. Review current diagnostics; a missing score is not replaced.</p>
        {state.blocked && state.score != null && <details><summary>Historical score, not current</summary><p>{state.score}/100 recorded with this output. It does not override the blockers above.</p></details>}
      </div>
    </dl>
    <details><summary>Saved output identity and time</summary>
      <p style={secondary}>Assumption set #{state.assumptionId ?? "Not available"}<br />Output #{out?.id ?? "Not available"}<br />
        Saved inputs updated: {state.savedAt ?? "Not available"}<br />Calculated: {state.calculatedAt ?? "Not available"}<br />
        Saved currency: {state.currency ?? "Not configured"}. Timestamps describe storage/calculation, not a market-price observation.</p>
    </details>
  </section>;
}

export function MultiMethodValuationCard({ state, modelType }: { state: ValuationOutputState; modelType?: string | null }) {
  const coreLabel = modelType === "financial_services" ? "Excess-return model" : modelType === "distressed" ? "Distress-adjusted DCF" : "FCFF (Core)";
  return <section aria-label="Saved multi-method valuation" className="valuation-output-card" style={{ minWidth: 0, overflowWrap: "anywhere" }}>
    <h3>Multi-method valuation</h3>
    <p style={secondary}>Estimate per share in {state.currency ?? "unconfigured currency"}, from the same saved assumption set. Model suitability still requires review.</p>
    {state.blocked && <p style={secondary}>Values are unavailable until the saved output blockers are resolved. See Saved valuation output.</p>}
    <dl>{([
      [coreLabel, state.output?.intrinsic_value_per_share],
      ["FCFE (Equity)", state.output?.fcfe_intrinsic_value_per_share],
      ["DDM (Dividends)", state.output?.ddm_intrinsic_value_per_share],
    ] as const).map(([label, value]) => <div key={label} style={row}>
      <dt>{label}</dt><dd style={{ margin: 0, fontWeight: 600 }}>{outputMoney(value, state)}</dd>
    </div>)}</dl>
    <p style={secondary}>Missing or non-finite method results are not available. These are stored calculations, not independent confirmations or investment recommendations.</p>
  </section>;
}
