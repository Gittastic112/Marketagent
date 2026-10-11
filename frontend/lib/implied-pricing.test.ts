import assert from "node:assert/strict";
import test from "node:test";
import { readFileSync } from "node:fs";
import type { ImpliedPricingBasis } from "./api.ts";
import { pricingRows } from "./implied-pricing.ts";

const basis = (value: number | null, reason: string | null = null): ImpliedPricingBasis => ({
  version: 1, claimType: "Calculation", assumptionSetId: 1, outputCreatedAt: null,
  assumptionsUpdatedAt: null, isStale: false, note: "Saved assumptions",
  methods: [{ field: "implied_pe", label: "P/E", value, numerator: 0, denominator: 10,
    sourceFields: ["net_income"], formula: "equity / income", reason }],
});

test("zero and negative finite DCF ratios remain visible", () => {
  assert.equal(pricingRows(basis(0), false)[0].display, "0.0x");
  assert.equal(pricingRows(basis(-2), false)[0].display, "-2.0x");
});
test("missing and nonfinite ratios are unavailable", () => {
  for (const value of [null, NaN, Infinity, -Infinity]) {
    assert.equal(pricingRows(basis(value), false)[0].display, "Not available");
  }
});
test("backend reasons override numbers", () => {
  const result = pricingRows(basis(99, "Unsupported denominator"), false)[0];
  assert.equal(result.display, "Not available");
  assert.equal(result.reason, "Unsupported denominator");
});
test("stale or untrusted output hides every ratio", () => {
  assert.equal(pricingRows(basis(20), true)[0].display, "Not available");
  assert.equal(pricingRows({ ...basis(20), isStale: true }, false)[0].display, "Not available");
});
test("missing and unknown basis versions never use legacy ratios", () => {
  for (const value of [null, undefined, { ...basis(99), version: 2 }]) assert.deepEqual(pricingRows(value, false), []);
});
test("workspace uses the guarded panel, not legacy ratio fields", () => {
  const text = readFileSync(new URL("../components/advanced-workspace.tsx", import.meta.url), "utf8");
  assert.match(text, /<ImpliedPricingPanel/);
  assert.match(text, /blocked=\{outputTrustBlocked \|\| Boolean\(latestAssumptionSet\?\.is_stale\)\}/);
  assert.doesNotMatch(text, /out\??\.implied_(pe|ev_ebitda|ev_sales|ev_ebit)/);
});
test("sidebar discloses formulas, provenance, unavailable states and saved boundary", () => {
  const text = readFileSync(new URL("../components/valuation/implied-pricing-panel.tsx", import.meta.url), "utf8");
  for (const token of ["User Assumptions", "Unsaved form edits", "method.formula", "method.reason", "sourceFields", "outputCreatedAt", "assumptionsUpdatedAt", "<details>"]) assert.ok(text.includes(token), token);
  assert.match(text, /var\(--text-secondary\)/);
  assert.doesNotMatch(text, /className="text-muted"/);
});
