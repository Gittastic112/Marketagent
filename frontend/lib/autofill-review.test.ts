import assert from "node:assert/strict";
import { test } from "node:test";

import {
  DISCOUNT_COMPONENT_FIELDS,
  provenanceLabel,
  reviewFieldValueIsValid,
  reviewFieldsForModel,
  unresolvedReviewFields,
} from "./autofill-review.ts";

test("review validation requires positive values for critical valuation inputs", () => {
  assert.equal(reviewFieldValueIsValid("starting_revenue", 0), false);
  assert.equal(reviewFieldValueIsValid("wacc_start", 0), false);
  assert.equal(reviewFieldValueIsValid("diluted_shares", "12"), true);
  assert.equal(reviewFieldValueIsValid("cash", 0), true);
  assert.equal(reviewFieldValueIsValid("current_market_price", 0), false);
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

test("missing amounts cannot be accepted as an explicit zero", () => {
  for (const value of [null, undefined, "", "  ", true, false]) {
    assert.equal(reviewFieldValueIsValid("cash", value), false);
    assert.equal(reviewFieldValueIsValid("current_market_price", value), value === null);
  }
  assert.equal(reviewFieldValueIsValid("cash", 0), true);
  assert.equal(reviewFieldValueIsValid("cash", "0"), true);
  assert.equal(reviewFieldValueIsValid("revenue_growth_years_json", { "1": NaN }), false);
});

test("clearing a required source-backed input blocks promotion even outside the review list", () => {
  const metadata = {promotion_ready: true, requires_review: false, placeholder_fields: [],
    review_fields: [], required_fields_by_model: {fcff_dcf: ["diluted_shares"]}, source_counts_by_type: {}};
  assert.deepEqual(unresolvedReviewFields(metadata, new Set(), {diluted_shares: null}), ["diluted_shares"]);
  assert.deepEqual(unresolvedReviewFields(metadata, new Set(), {diluted_shares: 100}), []);
});

test("unavailable comparison price needs explicit acknowledgement, without inventing an amount", () => {
  const metadata = { promotion_ready: false, requires_review: true,
    placeholder_fields: ["current_market_price"], review_fields: ["current_market_price"],
    source_counts_by_type: {} };
  assert.deepEqual(unresolvedReviewFields(metadata, new Set(), { current_market_price: null }), ["current_market_price"]);
  assert.deepEqual(unresolvedReviewFields(metadata, new Set(["current_market_price"]), { current_market_price: null }), []);
  assert.equal(reviewFieldValueIsValid("current_market_price", -1), false);
  assert.equal(reviewFieldValueIsValid("current_market_price", NaN), false);
  assert.equal(reviewFieldValueIsValid("current_market_price", Infinity), false);
  assert.equal(reviewFieldValueIsValid("current_market_price", [10]), false);
  assert.equal(reviewFieldValueIsValid("current_market_price", { price: 10 }), false);
  assert.equal(reviewFieldValueIsValid("diluted_shares", null), false);
});

test("provenance label supports structured and legacy provenance", () => {
  assert.equal(provenanceLabel({ label: "Normalized Financials" }), "Normalized Financials");
  assert.equal(provenanceLabel("Manual entry"), "Manual entry");
  assert.equal(provenanceLabel(undefined), "Unknown source");
});

test("unavailable funding components need review and explicit rates, while bank equity cost and claims remain required", () => {
  const values = { wacc_start: .14, wacc_terminal: .14, beta: null,
    risk_free_rate: .05, equity_risk_premium: .04, cost_of_equity: .09,
    pre_tax_cost_of_debt: .07, debt_to_capital: .2, equity_to_capital: .8 };
  const metadata = { promotion_ready: false, requires_review: true, placeholder_fields: [],
    review_fields: ["wacc_start", "wacc_terminal", "beta"], source_counts_by_type: {} };
  assert.deepEqual(unresolvedReviewFields(metadata, new Set(["wacc_start", "wacc_terminal"]), values), ["beta"]);
  assert.deepEqual(unresolvedReviewFields(metadata, new Set(metadata.review_fields), values), []);
  for (const rate of [null, 0, -1, NaN, Infinity, 1.1]) {
    assert.ok(unresolvedReviewFields(metadata, new Set(metadata.review_fields), {...values, wacc_start: rate}).includes("beta"));
  }
  const bank = {...metadata, review_fields_by_model: {financial_services: ["cost_of_equity"]}};
  assert.deepEqual(unresolvedReviewFields(bank, new Set(["cost_of_equity"]), {...values, cost_of_equity: null}, "financial_services"), ["cost_of_equity"]);
  for (const field of ["diluted_shares", "employee_options_value", "minority_interests", "debt"]) {
    assert.deepEqual(unresolvedReviewFields({...metadata, review_fields: [field]}, new Set([field, "beta"]), {...values, [field]: null}), [field]);
  }
});

test("clearing a sourced component adds explicit unavailable review immediately", () => {
  const metadata = {promotion_ready: true, requires_review: false, placeholder_fields: [],
    review_fields: [], source_counts_by_type: {}};
  const values = {wacc_start: .14, wacc_terminal: .14, beta: null,
    risk_free_rate: .05, equity_risk_premium: .04, cost_of_equity: .09,
    pre_tax_cost_of_debt: .07, debt_to_capital: .2, equity_to_capital: .8};
  assert.deepEqual(reviewFieldsForModel(metadata, "fcff_dcf", values), ["beta"]);
  assert.deepEqual(unresolvedReviewFields(metadata, new Set(), values), ["beta"]);
  assert.deepEqual(unresolvedReviewFields(metadata, new Set(["beta"]), values), []);
});

test("omitted legacy funding keys require the same explicit review as null components", () => {
  const metadata = {promotion_ready: true, requires_review: false, placeholder_fields: [],
    review_fields: [], source_counts_by_type: {}};
  const values = {wacc_start: .14, wacc_terminal: .14};
  assert.deepEqual(new Set(unresolvedReviewFields(metadata, new Set(), values)), DISCOUNT_COMPONENT_FIELDS);
  assert.deepEqual(unresolvedReviewFields(metadata, DISCOUNT_COMPONENT_FIELDS, values), []);
});

test("selected model uses its server-provided review inputs", () => {
  const metadata = {promotion_ready: false, requires_review: true, placeholder_fields: [],
    source_counts_by_type: {}, review_fields: ["starting_revenue", "wacc_start"],
    review_fields_by_model: {financial_services: ["book_value_of_equity", "target_roe", "net_income"]}};
  assert.deepEqual(reviewFieldsForModel(metadata), ["starting_revenue", "wacc_start"]);
  assert.deepEqual(unresolvedReviewFields(metadata, new Set(["book_value_of_equity", "target_roe", "net_income"]),
    {book_value_of_equity: 100, target_roe: .12, net_income: 10}, "financial_services"), []);
  assert.deepEqual(unresolvedReviewFields(metadata, new Set(["book_value_of_equity", "target_roe", "net_income"]),
    {book_value_of_equity: 0, target_roe: 12, net_income: null}, "financial_services"),
    ["book_value_of_equity", "target_roe", "net_income"]);
  assert.equal(reviewFieldValueIsValid("probability_of_failure", 1.1), false);
  assert.equal(reviewFieldValueIsValid("projection_years_count", 2.5), false);
});
