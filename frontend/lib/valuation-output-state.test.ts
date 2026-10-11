import assert from "node:assert/strict";
import test from "node:test";
import { readFileSync } from "node:fs";
import { buildValuationOutputState, invalidDcfAssumptions, outputMoney, outputGap } from "./valuation-output-state.ts";

const saved = () => ({ id: 1, cash_flow_currency: "USD", is_stale: false,
  outputs: { assumption_set_id: 1, warnings_json: [] as unknown, intrinsic_value_per_share: 120,
    fcfe_intrinsic_value_per_share: 110, ddm_intrinsic_value_per_share: 0,
    current_market_price: 100, upside_downside_pct: 0.2, model_quality_score: 95 } });

test("no saved output never invents a quality score or value", () => {
  const state = buildValuationOutputState(undefined);
  assert.equal(state.blocked, true);
  assert.equal(state.score, null);
  assert.equal(outputMoney(100, state), "Not available");
});
test("all saved monetary outputs share the stale gate", () => {
  const state = buildValuationOutputState({ ...saved(), is_stale: true });
  for (const value of [120, 110, 0, 5000, 10]) assert.equal(outputMoney(value, state), "Not shown");
  assert.equal(outputGap(state), "Not shown");
});
test("critical and blocking warnings gate all estimates", () => {
  for (const severity of ["critical", "blocking"]) {
    const s = saved(); s.outputs.warnings_json = [{ severity, module: "dcf", message: "Review" }];
    assert.equal(buildValuationOutputState(s).blocked, true);
  }
});
test("invalid saved units gate values", () => {
  const s = { ...saved(), current_operating_margin: 20 };
  assert.deepEqual(invalidDcfAssumptions(s), ["current_operating_margin"]);
  assert.equal(buildValuationOutputState(s).blocked, true);
});
test("nonfinite and nonnumeric supplied assumptions are invalid", () => {
  for (const value of [NaN, Infinity, "0.2", true]) {
    assert.ok(invalidDcfAssumptions({ current_operating_margin: value } as never).length);
  }
});
test("legacy and malformed diagnostics cannot imply a clean model", () => {
  for (const warnings_json of [["Old warning"], [null], [{ severity: "unknown" }], null]) {
    const s = saved(); s.outputs.warnings_json = warnings_json;
    const state = buildValuationOutputState(s);
    assert.equal(state.blocked, true);
    assert.ok(state.reasons.some(reason => reason.includes("diagnostic")));
  }
});
test("output identity must match the saved assumption set", () => {
  const s = saved(); s.outputs.assumption_set_id = 2;
  assert.equal(buildValuationOutputState(s).blocked, true);
});
test("saved output currency cannot be inferred from company or unsaved controls", () => {
  for (const cash_flow_currency of [null, "", "US", "123", "ＵＳＤ"]) {
    const state = buildValuationOutputState({ ...saved(), cash_flow_currency });
    assert.equal(state.currency, null);
    assert.equal(state.blocked, true);
  }
});
test("currency mismatch needs a saved explanation", () => {
  const s = { ...saved(), discount_rate_currency: "EUR" };
  assert.equal(buildValuationOutputState(s).blocked, true);
  assert.equal(buildValuationOutputState({ ...s, currency_override_note: "Reviewed FX basis" }).blocked, false);
});
test("zero and negative finite calculations survive formatting", () => {
  const state = buildValuationOutputState(saved());
  assert.equal(outputMoney(0, state), "$0.00");
  assert.equal(outputMoney(-10, state), "-$10.00");
});
test("missing and nonfinite method values remain individually unavailable", () => {
  const state = buildValuationOutputState(saved());
  for (const value of [null, undefined, NaN, Infinity]) assert.equal(outputMoney(value, state), "Not available");
  assert.equal(outputMoney(110, state), "$110.00");
});
test("stored quality score is bounded and never synthesized", () => {
  for (const model_quality_score of [null, undefined, NaN, Infinity, -1, 101]) {
    const s = saved(); s.outputs.model_quality_score = model_quality_score as number;
    assert.equal(buildValuationOutputState(s).score, null);
  }
  const s = saved(); s.outputs.model_quality_score = 0;
  assert.equal(buildValuationOutputState(s).score, 0);
});
test("comparison gap requires valid saved price, estimate and finite stored gap", () => {
  const s = saved();
  assert.equal(outputGap(buildValuationOutputState(s)), "20.0%");
  s.outputs.upside_downside_pct = 0;
  assert.equal(outputGap(buildValuationOutputState(s)), "0.0%");
  for (const price of [0, -1, NaN, Infinity]) {
    s.outputs.current_market_price = price;
    assert.equal(outputGap(buildValuationOutputState(s)), "Not available");
  }
});
test("workspace and cards consume shared state without fallback score or Market Fact", () => {
  const read = (path: string) => readFileSync(new URL(`../${path}`, import.meta.url), "utf8");
  const workspace = read("components/advanced-workspace.tsx");
  const cards = read("components/valuation/saved-output-cards.tsx");
  assert.match(workspace, /buildValuationOutputState\(latestAssumptionSet, model\?\.model_type\)/);
  assert.match(workspace, /<SavedValuationOutputCard/);
  assert.match(workspace, /<MultiMethodValuationCard/);
  assert.doesNotMatch(workspace + cards, /fallbackScore|Market Fact/);
  assert.match(workspace, /modelType=\{model\?\.model_type\}/);
  assert.match(cards, /Excess-return model/);
  assert.match(cards, /Distress-adjusted DCF/);
  for (const label of ["User Assumption", "Stored diagnostic score", "not a live quote", "not recalculated", "Unsaved edits", "Estimate per share", "Calculation, total equity", "outputMoney", "outputGap"]) assert.ok(cards.includes(label), label);
});

test("corrected forms can reach backend validation despite invalid historical inputs", () => {
  const workspace = readFileSync(new URL("../components/advanced-workspace.tsx", import.meta.url), "utf8");
  const submit = workspace.match(/<button type="submit"[^>]+>/)?.[0];
  assert.ok(submit);
  assert.doesNotMatch(submit, /invalidAssumptions/);
  assert.match(submit, /isPending \|\| !valuationContext \|\| !currencyCheck.canSave/);
  assert.match(workspace, /backend validates the submitted values/);
});
