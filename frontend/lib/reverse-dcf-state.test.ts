import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { reverseDcfRequest, reverseDcfResultUsable } from "./reverse-dcf-state.ts";
import type { DcfAssumptionSet, ReverseDcfResponse } from "./api/valuation.ts";

const assumptions = { id: 7, updated_at: "2026-09-10T00:00:00Z", cash_flow_currency: "INR", diluted_shares: 10,
  outputs: { assumption_set_id: 7, warnings_json: [] } } as unknown as DcfAssumptionSet;
const request = reverseDcfRequest(7, "target_operating_margin", "120", "");
const result: ReverseDcfResponse = { assumption_set_id: 7, assumptions_updated_at: assumptions.updated_at,
  currency: "INR", model_type: "fcff_dcf", comparison_price: 120, diluted_shares: 10,
  target_parameter: "target_operating_margin", original_value: 0, implied_value: 0.2,
  intrinsic_value_at_implied: 120.001, price_residual: 0.001, converged: true, diagnostics: [] };

test("reverse price is explicit, finite and positive; omitted shares remain omitted", () => {
  assert.equal(request.current_market_price, 120);
  assert.equal("diluted_shares" in request, false);
  for (const invalid of ["", "0", "-1", "Infinity", "invalid"]) {
    assert.throws(() => reverseDcfRequest(7, "target_operating_margin", invalid, ""));
    if (invalid) assert.throws(() => reverseDcfRequest(7, "target_operating_margin", "120", invalid));
  }
});
test("reverse output requires convergence and exact saved/request identity", () => {
  assert.equal(reverseDcfResultUsable(result, request, assumptions, "fcff_dcf"), true);
  for (const patch of [{converged:false}, {assumption_set_id:8}, {currency:"USD"}, {model_type:"distressed"},
    {comparison_price:100}, {diluted_shares:1}, {assumptions_updated_at:"old"}, {price_residual:1},
    {implied_value:Infinity}, {diagnostics:[{severity:"critical" as const, module:"dcf",message:"Review", affectedAssumptions:[], suggestedFix:null, formula:null}]}]) {
    assert.equal(reverseDcfResultUsable({...result,...patch}, request, assumptions, "fcff_dcf"), false);
  }
  assert.equal(reverseDcfResultUsable(result, request, {...assumptions,is_stale:true}, "fcff_dcf"), false);
});
test("reverse panel is on-demand, input-scoped and does not submit the DCF form", () => {
  const panel = readFileSync(new URL("../components/valuation/reverse-dcf-panel.tsx", import.meta.url), "utf8");
  const workspace = readFileSync(new URL("../components/advanced-workspace.tsx", import.meta.url), "utf8");
  assert.match(panel, /createRequestGate/);
  assert.match(panel, /gate.invalidate\(\)/);
  assert.match(panel, /if \(isCurrent\(\)\)/);
  assert.match(workspace, /activeSection === "reverse_dcf" && latestAssumptionSet/);
  assert.doesNotMatch(panel, /100\.00|Market Price \(\$\)/);
  assert.equal((workspace.match(/id="net_income"/g) ?? []).length, 1);
  assert.equal((workspace.match(/id="book_value_of_equity"/g) ?? []).length, 1);
});
