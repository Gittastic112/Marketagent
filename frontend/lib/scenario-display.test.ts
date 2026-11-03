import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import type { DcfAssumptionSet, DcfScenarioOutput } from "./api.ts";
import { scenarioDisplay } from "./scenario-display.ts";
const inputs = { id: 1, cash_flow_currency: "USD", is_stale: false } as DcfAssumptionSet;
const scenario = (value: number | null, warnings: unknown[] = []): DcfScenarioOutput => ({
  scenario_name: String(value), description: "Test scenario",
  output: { assumption_set_id: 1, intrinsic_value_per_share: value, current_market_price: 100,
    upside_downside_pct: 0.123, warnings_json: warnings } as DcfScenarioOutput["output"],
});
test("scenario values use saved currency, not hardcoded INR", () => {
  assert.equal(scenarioDisplay([scenario(120)], inputs)[0].value, "$120.00");
});
test("scenario gap is the backend calculation, not browser recomputation", () => {
  assert.equal(scenarioDisplay([scenario(120)], inputs)[0].gap, "12.3%");
});
test("missing scenarios sort last without becoming zero", () => {
  const result = scenarioDisplay([scenario(null), scenario(-1), scenario(0), scenario(10)], inputs);
  assert.deepEqual(result.map(x => x.sortValue), [10, 0, -1, null]);
  assert.equal(result[1].value, "$0.00");
  assert.equal(result[3].value, "Not available");
});
test("stale and critically warned scenarios cannot become usable estimates", () => {
  const critical = scenario(999, [{ severity: "critical", module: "dcf", message: "Blocked" }]);
  assert.equal(scenarioDisplay([critical], inputs)[0].value, "Not shown");
  assert.equal(scenarioDisplay([scenario(100)], { ...inputs, is_stale: true })[0].gap, "Not shown");
});
test("unknown currency and nonfinite scenario values are unavailable", () => {
  assert.equal(scenarioDisplay([scenario(100)], { ...inputs, cash_flow_currency: null })[0].value, "Not shown");
  assert.equal(scenarioDisplay([scenario(Infinity)], inputs)[0].value, "Not available");
});
test("bank scenarios validate equity inputs instead of irrelevant operating-company fields", () => {
  const bank = { ...inputs, book_value_of_equity: 100, diluted_shares: 10,
    net_income: 0, target_roe: 0, cost_of_equity: .1, terminal_growth_rate: 0,
    starting_revenue: 0, starting_invested_capital: 0, sales_to_capital_ratio: 0 };
  assert.equal(scenarioDisplay([scenario(0)], bank, "financial_services")[0].value, "$0.00");
  assert.equal(scenarioDisplay([scenario(100)], { ...bank, book_value_of_equity: 0 }, "financial_services")[0].value, "Not shown");
});
test("scenario loading is scoped, on-demand and recoverable without form submission", () => {
  const read = (path: string) => readFileSync(new URL(`../${path}`, import.meta.url), "utf8");
  const panel = read("components/valuation/scenario-range-panel.tsx");
  const workspace = read("components/advanced-workspace.tsx");
  assert.match(panel, /useLatestResource/);
  assert.match(panel, /assumptions.updated_at/);
  assert.match(panel, /scenarioDisplay\(resource.data \?\? \[\], assumptions, modelType\)/);
  assert.match(workspace, /<ScenarioRangePanel[^>]*modelType=\{model\?\.model_type\}/);
  assert.match(panel, /type="button"/);
  assert.match(panel, /No scenarios returned/);
  assert.doesNotMatch(panel, /"INR"|\|\| 0|isUndervalued|diffPct/);
  assert.match(workspace, /activeSection === "scenario_range" && !outputTrustBlocked/);
});
