import assert from "node:assert/strict";
import test from "node:test";
import { receiptAuditCursor, receiptAuditHref } from "./peer-health-navigation.ts";

test("receipt cursor accepts only safe nonnegative integer query values", () => {
  assert.equal(receiptAuditCursor("123"), 123);
  for (const value of [undefined, "-1", "1.5", "1e3", "NaN", "9007199254740992", ["1", "2"]]) {
    assert.equal(receiptAuditCursor(value), 0);
  }
});

test("receipt pagination preserves supported diagnostic modes and restarts at zero", () => {
  assert.equal(receiptAuditHref(51, "coverage"), "/data-health?audit=coverage&peer_after=51");
  assert.equal(receiptAuditHref(0), "/data-health");
  assert.equal(receiptAuditHref(0, "evidence"), "/data-health?audit=evidence");
  assert.equal(receiptAuditHref(9, "unknown"), "/data-health?peer_after=9");
});
