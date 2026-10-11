import assert from "node:assert/strict";
import test from "node:test";
import { hasReadySelection, isPeerSetCalculationReady } from "./relative-valuation-selection.ts";

test("only a loaded selection present in the current options is usable", () => {
  assert.equal(hasReadySelection("ready", ["Banks"], "Banks"), true);
  for (const status of ["loading", "error"]) {
    assert.equal(hasReadySelection(status, ["Banks"], "Banks"), false);
  }
  assert.equal(hasReadySelection("ready", ["Retail"], "Banks"), false);
  assert.equal(hasReadySelection("ready", [], "Banks"), false);
  assert.equal(hasReadySelection("ready", [""], ""), false);
});

const eligible: Parameters<typeof isPeerSetCalculationReady>[0] = {
  isActive: true,
  reviewStatus: "reviewed",
  reviewReceipt: {
    diagnosticsSha256: "hash", warningCodes: [], diagnosticsAsOf: "2026-09-06",
    matchesCurrentDiagnostics: true,
  },
  calculationEligibility: {
    canCalculate: true, receiptStatus: "current", usableMethods: ["pe"], blockers: [], asOf: "2026-09-06",
  },
};

test("a reviewed current eligible set is usable", () => {
  assert.equal(isPeerSetCalculationReady(eligible), true);
});
test("archived sets cannot be selected", () => {
  assert.equal(isPeerSetCalculationReady({ ...eligible, isActive: false }), false);
});
test("draft sets cannot be selected", () => {
  assert.equal(isPeerSetCalculationReady({ ...eligible, reviewStatus: "draft" }), false);
});
test("stale receipts cannot be selected", () => {
  assert.equal(isPeerSetCalculationReady({ ...eligible,
    reviewReceipt: { ...eligible.reviewReceipt!, matchesCurrentDiagnostics: false } }), false);
});
test("server eligibility blockers cannot be bypassed by a current receipt", () => {
  assert.equal(isPeerSetCalculationReady({ ...eligible,
    calculationEligibility: { ...eligible.calculationEligibility!, canCalculate: false } }), false);
});
test("missing eligibility fails closed", () => {
  assert.equal(isPeerSetCalculationReady({ ...eligible, calculationEligibility: undefined }), false);
});
