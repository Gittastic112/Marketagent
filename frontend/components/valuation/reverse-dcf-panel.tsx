"use client";

import { useEffect, useMemo, useState } from "react";
import { solveReverseDcf, type DcfAssumptionSet, type ReverseDcfRequest, type ReverseDcfResponse } from "@/lib/api/valuation";
import { createRequestGate } from "@/lib/latest-request";
import { reverseDcfRequest, reverseDcfResultUsable } from "@/lib/reverse-dcf-state";
import { buildValuationOutputState, finiteOutput } from "@/lib/valuation-output-state";
import { SelectField, TextField } from "@/components/form-fields";
import { DiagnosticPanel } from "./diagnostic-panel";

export function ReverseDcfPanel({ assumptions, modelType }: { assumptions: DcfAssumptionSet; modelType: string }) {
  const state = buildValuationOutputState(assumptions);
  const [price, setPrice] = useState(assumptions.current_market_price != null && assumptions.current_market_price > 0 ? String(assumptions.current_market_price) : "");
  const [shares, setShares] = useState("");
  const [parameter, setParameter] = useState<ReverseDcfRequest["target_parameter"]>("target_operating_margin");
  const [pending, setPending] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<{ request: ReverseDcfRequest; response: ReverseDcfResponse } | null>(null);
  const gate = useMemo(() => createRequestGate(), []);
  useEffect(() => () => gate.invalidate(), [gate]);
  const invalidate = () => { gate.invalidate(); setResult(null); setError(null); setPending(false); };
  const supported = ["fcff_dcf", "distressed"].includes(modelType);
  const blocked = state.blocked || !supported;
  const submit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (blocked) return;
    const isCurrent = gate.begin();
    setResult(null); setError(null); setPending(true);
    try {
      const request = reverseDcfRequest(assumptions.id, parameter, price, shares);
      const response = await solveReverseDcf(request);
      if (isCurrent()) setResult({ request, response });
    } catch (cause) {
      if (isCurrent()) setError(cause instanceof Error ? cause.message : "Reverse DCF unavailable. Retry after reviewing inputs.");
    } finally {
      if (isCurrent()) setPending(false);
    }
  };
  const response = result?.response;
  const usable = result && reverseDcfResultUsable(result.response, result.request, assumptions, modelType);
  const number = (value: unknown) => finiteOutput(value) ? value.toLocaleString(undefined, { maximumFractionDigits: 6 }) : "Not available";
  return <section aria-label="Reverse DCF analysis">
    <h2>Reverse DCF</h2>
    <p>Calculation from saved User Assumptions and an explicit comparison price, not a live quote or market forecast. Unsaved model edits are excluded. Currency: {state.currency ?? "Not configured"}.</p>
    <p>Saved assumption #{assumptions.id}. Updated: {assumptions.updated_at}. Shares: {assumptions.diluted_shares ?? "Not configured"}.</p>
    {state.reasons.map(reason => <p key={reason} role="alert">{reason}</p>)}
    {!supported && <p role="alert">Not available yet for financial-services excess-return models.</p>}
    <form onSubmit={submit} style={{ display: "grid", gap: "1rem", maxWidth: "500px" }}>
      <SelectField id="reverse_parameter" label="Parameter to solve for" value={parameter} onChange={event => { invalidate(); setParameter(event.target.value as typeof parameter); }}>
        <option value="target_operating_margin">Target operating margin</option>
        <option value="revenue_growth">Flat growth across every projection year</option>
        <option value="wacc_start">Initial WACC (terminal WACC remains saved)</option>
        <option value="terminal_growth_rate">Terminal growth</option>
      </SelectField>
      <TextField id="reverse_price" label={`Comparison price (${state.currency ?? "currency not configured"}, User Assumption)`} type="number" step="any" min="0.000001" required value={price}
        onChange={event => { invalidate(); setPrice(event.target.value); }} />
      <TextField id="reverse_shares" label="Diluted shares (optional override, same share scale as saved model)" type="number" step="any" min="0.000001" value={shares}
        onChange={event => { invalidate(); setShares(event.target.value); }} />
      <button type="submit" disabled={blocked || pending}>{pending ? "Solving..." : "Solve Reverse DCF"}</button>
    </form>
    {error && <p role="alert">{error}</p>}
    {response && <div aria-label="Reverse DCF result" style={{ marginTop: "1rem" }}>
      <p>Original saved parameter{parameter === "revenue_growth" ? " (mean across all projection years, including zero for omitted years)" : ""}: {number(response.original_value)}</p>
      <p>Implied parameter (decimal): <strong>{usable ? number(response.implied_value) : "Not available"}</strong></p>
      {!usable && <p role="status">No usable converged result for these inputs. Review diagnostics; no approximate boundary value is presented as a solution.</p>}
      {usable && <>
        <p>Calculated price: {number(response.intrinsic_value_at_implied)} {response.currency}. Requested price: {number(response.comparison_price)} {response.currency}.</p>
        <p>Price residual: {number(response.price_residual)} {response.currency}. Tolerance: 0.01 currency units. Shares used: {number(response.diluted_shares)}.</p>
      </>}
      <p>Calculated: {response.calculated_at ?? "Not available"}. Model: {response.model_type ?? "Not available"}. This result is not saved and does not change the assumption set.</p>
      <DiagnosticPanel warnings={response.diagnostics.map(w => ({ ...w, suggestedFix: w.suggestedFix ?? undefined, formula: w.formula ?? undefined }))} />
    </div>}
  </section>;
}
