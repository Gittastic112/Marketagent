import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { test } from "node:test";
import type { DcfAssumptionSet } from "./api/valuation.ts";
import type { SavedRealOptionResponse } from "./api/real-options.ts";
import { optionNumber, savedOptionResultUsable } from "./real-options-state.ts";

const time = "2026-09-15T00:00:00";
const saved = { id: 7, updated_at: time, cash_flow_currency: "INR", discount_rate_currency: "INR", diluted_shares: 10,
  outputs: { assumption_set_id: 7, created_at: time, equity_value: 1000, intrinsic_value_per_share: 100, warnings_json: [] } } as unknown as DcfAssumptionSet;
const result: SavedRealOptionResponse = { assumption_set_id: 7, assumptions_updated_at: time, output_created_at: time,
  calculated_at: time, currency: "INR", model_type: "fcff_dcf", input_sha256: "a".repeat(64), diluted_shares: 10,
  base_equity_value: 1000, base_value_per_share: 100, raw_option_value: 10, adjusted_option_value: 0,
  option_value_per_share: 0, option_adjusted_equity_value: 1000, option_adjusted_intrinsic_value: 100, warnings: [] };

test("option inputs preserve zero and reject blank/nonfinite text", () => {
  assert.equal(optionNumber("0", "exclusivity"), 0);
  for (const text of ["", " ", "NaN", "Infinity", "oops"]) assert.throws(() => optionNumber(text, "value"));
});

test("saved option result retains zero with exact identity/currency and finite units", () => {
  assert.equal(savedOptionResultUsable(result, saved, "fcff_dcf"), true);
  for (const patch of [{ assumption_set_id: 8 }, { currency: "USD" }, { diluted_shares: 1 },
    { base_equity_value: 100 }, { assumptions_updated_at: "older" }, { output_created_at: "older" },
    { option_value_per_share: Infinity }, { input_sha256: "" }, { calculated_at: "invalid" }]) {
    assert.equal(savedOptionResultUsable({ ...result, ...patch }, saved, "fcff_dcf"), false);
  }
});

test("saved option UI gates stale, critical and unsupported models", () => {
  assert.equal(savedOptionResultUsable(result, { ...saved, is_stale: true }, "fcff_dcf"), false);
  assert.equal(savedOptionResultUsable(result, saved, "distressed"), false);
  assert.equal(savedOptionResultUsable(result, { ...saved, outputs: { ...saved.outputs!, warnings_json: [
    { severity: "critical", module: "test", message: "blocked", affectedAssumptions: [], suggestedFix: null, formula: null },
  ] } }, "fcff_dcf"), false);
});

test("real option form mounts outside DCF form on demand and invalidates requests", () => {
  const workspace = readFileSync(new URL("../components/advanced-workspace.tsx", import.meta.url), "utf8");
  const panel = readFileSync(new URL("../components/valuation/real-options-panel.tsx", import.meta.url), "utf8");
  assert.ok(workspace.indexOf("<RealOptionsPanel") > workspace.indexOf("</form>"));
  assert.match(workspace, /activeSection === "real_options" && latestAssumptionSet/);
  assert.match(workspace, /display: activeSection === "real_options" \|\| activeSection === "reverse_dcf" \? "none"/);
  assert.match(panel, /createRequestGate/);
  assert.match(panel, /useEffect\(\(\) => \(\) => gate.invalidate\(\)/);
  assert.match(panel, /event.preventDefault\(\)/);
  assert.match(panel, /setResult\(null\); setError\(null\); setPending\(true\)/);
  assert.match(panel, /if \(isCurrent\(\)\)/);
  assert.doesNotMatch(panel, /baseDcfValue|parseFloat|Override Gate/);
  assert.match(panel, /state.currency/);
});
