import assert from "node:assert/strict";
import test from "node:test";
import { projectionColumns, projectionDescription } from "./valuation-projections.ts";
import { buildValuationOutputState, invalidDcfAssumptions } from "./valuation-output-state.ts";

test("bank projections label equity metrics, never operating cash flows", () => {
  const columns = projectionColumns("financial_services");
  assert.equal(columns.find(c => c.key === "fcff")?.label, "Excess return");
  assert.equal(columns.find(c => c.key === "wacc")?.label, "Cost of equity");
  assert.equal(columns.find(c => c.key === "invested_capital")?.label, "Opening book equity");
  assert.ok(!columns.some(c => c.key === "revenue" || c.key === "calendar_year"));
  assert.match(projectionDescription("financial_services"), /not a regulatory-capital/);
});

test("distressed projections disclose their survival basis; dates are not invented", () => {
  assert.match(projectionDescription("distressed"), /conditional on survival/);
  assert.match(projectionDescription("fcff_dcf"), /not calendar dates/);
  assert.equal(projectionColumns("fcff_dcf").find(c => c.key === "fcff")?.label, "FCFF");
});

test("equity-model display validates equity fields without irrelevant FCFF inputs", () => {
  const assumptions = { id: 3, starting_revenue: 0, starting_invested_capital: 0,
    book_value_of_equity: 100, net_income: 0, target_roe: 0, cost_of_equity: .08,
    terminal_growth_rate: 0, diluted_shares: 10, cash_flow_currency: "INR",
    outputs: { assumption_set_id: 3, intrinsic_value_per_share: 0, warnings_json: [] } };
  assert.equal(buildValuationOutputState(assumptions, "financial_services").blocked, false);
  assert.ok(invalidDcfAssumptions(assumptions).includes("starting_revenue"));
  assert.ok(invalidDcfAssumptions({ ...assumptions, target_roe: 10 }, "financial_services").includes("target_roe"));
  assert.ok(invalidDcfAssumptions({ ...assumptions, book_value_of_equity: 0 }, "financial_services").includes("book_value_of_equity"));
  assert.ok(invalidDcfAssumptions({ probability_of_failure: 2 }, "distressed").includes("probability_of_failure"));
});
