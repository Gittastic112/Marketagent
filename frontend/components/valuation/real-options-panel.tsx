"use client";

import { useEffect, useMemo, useState } from "react";
import { calculateSavedRealOption, type SavedRealOptionRequest, type SavedRealOptionResponse } from "@/lib/api/real-options";
import type { DcfAssumptionSet } from "@/lib/api/valuation";
import { createRequestGate } from "@/lib/latest-request";
import { optionNumber, savedOptionResultUsable } from "@/lib/real-options-state";
import { buildValuationOutputState } from "@/lib/valuation-output-state";
import { TextField, SelectField } from "@/components/form-fields";

const criteria = {
  has_underlying_asset: "Identifiable underlying asset",
  has_finite_life: "Finite option life",
  has_clear_exercise_price: "Clear exercise cost",
  has_asymmetric_payoff: "Asymmetric payoff",
  has_exclusivity: "Defensible exclusivity",
  can_estimate_volatility: "Supportable volatility estimate",
  can_estimate_underlying_value: "Supportable underlying value estimate",
};
const fields = {
  underlying_asset_value: ["Underlying value (total common-equity amount)", "0.000001", "1000000000000000000"],
  exercise_price: ["Exercise cost (total common-equity amount)", "0.000001", "1000000000000000000"],
  option_life_years: ["Option life (years)", "0.000001", "100"],
  risk_free_rate: ["Risk-free rate (decimal, option currency)", "-0.5", "1"],
  volatility: ["Volatility (annual decimal)", "0.000001", "5"],
  dividend_yield_or_cost_of_delay: ["Dividend yield or cost of delay (decimal)", "0", "1"],
  exclusivity_score: ["Exclusivity multiplier (0 to 1)", "0", "1"],
} as const;
type NumericField = keyof typeof fields;

export function RealOptionsPanel({ assumptions, modelType }: { assumptions: DcfAssumptionSet; modelType: string }) {
  const state = buildValuationOutputState(assumptions);
  const [eligibility, setEligibility] = useState(Object.fromEntries(Object.keys(criteria).map(k => [k, false])) as SavedRealOptionRequest["eligibility"]);
  const [values, setValues] = useState(Object.fromEntries(Object.keys(fields).map(k => [k, ""])) as Record<NumericField, string>);
  const [type, setType] = useState<"call" | "put">("call");
  const [confirmed, setConfirmed] = useState(false);
  const [counted, setCounted] = useState(false);
  const [pending, setPending] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<SavedRealOptionResponse | null>(null);
  const gate = useMemo(() => createRequestGate(), []);
  useEffect(() => () => gate.invalidate(), [gate]);
  const invalidate = () => { gate.invalidate(); setResult(null); setError(null); setPending(false); };
  const blocked = state.blocked || modelType !== "fcff_dcf" || !state.currency;
  const ready = !blocked && confirmed && Object.values(eligibility).every(Boolean);
  const submit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!ready || !state.currency) return;
    const isCurrent = gate.begin();
    setResult(null); setError(null); setPending(true);
    try {
      const numbers = Object.fromEntries(Object.entries(values).map(([k, v]) => [k, optionNumber(v, fields[k as NumericField][0])])) as Record<NumericField, number>;
      const response = await calculateSavedRealOption(assumptions.id, { ...numbers, option_type: type,
        assumptions_updated_at: assumptions.updated_at, currency: state.currency, eligibility,
        confirm_incremental_equity_basis: confirmed, is_already_counted: counted });
      if (isCurrent()) {
        if (!savedOptionResultUsable(response, assumptions, modelType)) throw new Error("Option result does not match the saved basis or contains invalid values. Reload and retry.");
        setResult(response);
      }
    } catch (cause) {
      if (isCurrent()) setError(cause instanceof Error ? cause.message : "Real Options unavailable. Review inputs and retry.");
    } finally { if (isCurrent()) setPending(false); }
  };
  const money = (value: number) => `${value.toLocaleString(undefined, { maximumFractionDigits: 6 })} ${state.currency}`;
  return <section aria-label="Real Options analysis">
    <h2>Real Options</h2>
    <p>Calculation from saved User Assumptions, not a live quote or verified company fact. Unsaved DCF edits are excluded. Results are not saved.</p>
    <p>Saved assumption #{assumptions.id}. Currency: {state.currency ?? "Not configured"}. Diluted shares: {assumptions.diluted_shares ?? "Not configured"}. Updated: {assumptions.updated_at}.</p>
    {state.reasons.map(reason => <p role="alert" key={reason}>{reason}</p>)}
    {modelType !== "fcff_dcf" && <p role="alert">Not available yet for distressed or financial-services integration.</p>}
    <form onSubmit={submit} style={{ display: "grid", gap: "1rem", maxWidth: "650px" }}>
      <fieldset disabled={Boolean(blocked)}>
        <legend>Eligibility confirmations (User Assumptions, not a suitability score)</legend>
        {Object.entries(criteria).map(([key, label]) => <label key={key} style={{ display: "block" }}>
          <input type="checkbox" checked={eligibility[key as keyof typeof eligibility]} onChange={event => {
            invalidate(); setEligibility({ ...eligibility, [key]: event.target.checked });
          }} /> {label}
        </label>)}
      </fieldset>
      <SelectField id="option_type" label="Option type" value={type} onChange={event => { invalidate(); setType(event.target.value as "call" | "put"); }}>
        <option value="call">Call</option><option value="put">Put</option>
      </SelectField>
      {Object.entries(fields).map(([key, [label, min, max]]) => <TextField key={key} id={`option_${key}`} label={label}
        type="number" required step="any" min={min} max={max} value={values[key as NumericField]}
        onChange={event => { invalidate(); setValues({ ...values, [key]: event.target.value }); }} />)}
      <label><input type="checkbox" checked={confirmed} onChange={event => { invalidate(); setConfirmed(event.target.checked); }} /> I confirm the underlying value and exercise cost represent incremental common-equity amounts in {state.currency ?? "the saved currency"}, in the same total monetary scale as the DCF, not per-share or enterprise/project values. The rate uses this currency.</label>
      <label><input type="checkbox" checked={counted} onChange={event => { invalidate(); setCounted(event.target.checked); }} /> This option is already counted in the base DCF. Do not add it again.</label>
      <p>Only confirm an incremental equity claim you can support. A generic project option cannot automatically be added to company equity. Black-Scholes and the exclusivity multiplier are simplified modeling choices.</p>
      <button type="submit" disabled={!ready || pending}>{pending ? "Calculating..." : "Calculate Real Option Value"}</button>
    </form>
    {error && <p role="alert">{error}</p>}
    {result && <div aria-label="Real Options result">
      <h3>Calculation results</h3>
      <p>Base equity (total): {money(result.base_equity_value)}. Base estimate per share: {money(result.base_value_per_share)}.</p>
      <p>Raw option (total): {money(result.raw_option_value)}. Adjusted option (total): {money(result.adjusted_option_value)}.</p>
      <p>Option estimate per share: {money(result.option_value_per_share)}.</p>
      <p>Combined equity (total): {money(result.option_adjusted_equity_value)}. Combined estimate per share: {money(result.option_adjusted_intrinsic_value)}.</p>
      <p>Saved output: {result.output_created_at}. Calculated: {result.calculated_at}. Shares used: {result.diluted_shares}.</p>
      <details><summary>Input fingerprint</summary><code style={{ overflowWrap: "anywhere" }}>{result.input_sha256}</code></details>
      <ul>{result.warnings.map((warning, index) => <li key={index}>{warning}</li>)}</ul>
    </div>}
  </section>;
}
