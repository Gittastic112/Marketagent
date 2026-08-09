import assert from "node:assert/strict";
import { test } from "node:test";

import { buildCurrencyConsistencyCheck } from "./valuation-context.ts";

test("currency consistency check blocks mismatched risk-free and cash-flow currencies without override note", () => {
  const check = buildCurrencyConsistencyCheck({
    companyMarket: "IN",
    companyCurrency: "INR",
    cashFlowCurrency: "INR",
    discountRateCurrency: "USD",
    overrideNote: ""
  });

  assert.equal(check.canSave, false);
  assert.equal(check.severity, "blocking");
  assert.match(check.message, /risk-free currency/i);
  assert.match(check.message, /INR/);
  assert.match(check.message, /USD/);
});

test("currency consistency check allows mismatched currencies when override note explains it", () => {
  const check = buildCurrencyConsistencyCheck({
    companyMarket: "IN",
    companyCurrency: "INR",
    cashFlowCurrency: "INR",
    discountRateCurrency: "USD",
    overrideNote: "Using USD cash flows converted from INR forecasts."
  });

  assert.equal(check.canSave, true);
  assert.equal(check.severity, "warning");
  assert.match(check.message, /explicit override/i);
});

test("currency consistency check warns when India company valuation currency is USD", () => {
  const check = buildCurrencyConsistencyCheck({
    companyMarket: "IN",
    companyCurrency: "INR",
    cashFlowCurrency: "USD",
    discountRateCurrency: "USD",
    overrideNote: ""
  });

  assert.equal(check.canSave, true);
  assert.equal(check.severity, "warning");
  assert.match(check.message, /India company/i);
});
