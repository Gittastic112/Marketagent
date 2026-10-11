import assert from "node:assert/strict";
import { test } from "node:test";

import {
  provenanceLabel,
  reviewFieldValueIsValid,
  unresolvedReviewFields,
} from "./autofill-review.ts";

test("review validation requires positive values for critical valuation inputs", () => {
  assert.equal(reviewFieldValueIsValid("starting_revenue", 0), false);
  assert.equal(reviewFieldValueIsValid("wacc_start", 0), false);
  assert.equal(reviewFieldValueIsValid("diluted_shares", "12"), true);
  assert.equal(reviewFieldValueIsValid("cash", 0), true);
  assert.equal(reviewFieldValueIsValid("current_market_price", 0), true);
  assert.equal(reviewFieldValueIsValid("cash", -1), false);
  assert.equal(reviewFieldValueIsValid("current_operating_margin", -0.1), true);
  assert.equal(reviewFieldValueIsValid("target_operating_margin", 31.3), false);
  assert.equal(reviewFieldValueIsValid("wacc_terminal", 1.08), false);
  assert.equal(reviewFieldValueIsValid("debt_to_capital", 1.2), false);
  assert.equal(reviewFieldValueIsValid("beta", 2), true);
  assert.equal(reviewFieldValueIsValid("cross_holdings", 0), true);
  assert.equal(reviewFieldValueIsValid("operating_leases", -1), false);
  assert.equal(reviewFieldValueIsValid("cash_flow_currency", "INR"), true);
  assert.equal(reviewFieldValueIsValid("discount_rate_currency", "US"), false);
});

test("unresolved review fields require both a valid value and explicit review", () => {
  const metadata = {
    promotion_ready: false,
    requires_review: true,
    placeholder_fields: ["starting_revenue", "cash"],
    review_fields: ["starting_revenue", "cash"],
    source_counts_by_type: { missing_actual_default: 2 },
  };

  assert.deepEqual(
    unresolvedReviewFields(metadata, new Set(["cash"]), { starting_revenue: 1000, cash: 0 }),
    ["starting_revenue"],
  );
  assert.deepEqual(
    unresolvedReviewFields(metadata, new Set(["starting_revenue", "cash"]), { starting_revenue: 0, cash: 0 }),
    ["starting_revenue"],
  );
});

test("provenance label supports structured and legacy provenance", () => {
  assert.equal(provenanceLabel({ label: "Normalized Financials" }), "Normalized Financials");
  assert.equal(provenanceLabel("Manual entry"), "Manual entry");
  assert.equal(provenanceLabel(undefined), "Unknown source");
});
