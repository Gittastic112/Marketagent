import assert from "node:assert/strict";
import test from "node:test";
import { sensitivityAxis, sensitivityCell, sensitivityMethod } from "./sensitivity-table.ts";

test("zero, negative, decimal and rounded numeric keys retain saved values", () => {
  const values = { "0.0": { "0.0": 0, "0.01": -5.5 }, "0.1235": { "1.0": 4 } };
  assert.equal(sensitivityCell(values, {}, 0, 0).value, 0);
  assert.equal(sensitivityCell(values, {}, .01, 0).value, -5.5);
  assert.equal(sensitivityCell(values, {}, 1, .123456).value, 4);
});

test("malformed and unavailable cells cannot become prices", () => {
  for (const value of [undefined, null, NaN, Infinity, "12", false, {}, []]) {
    assert.equal(sensitivityCell({ "0": { "0": value } }, {}, 0, 0).value, null);
  }
  assert.equal(sensitivityCell({ "0": { "0": null } }, { "0": { "0": "TERMINAL_CONVERGENCE" } }, 0, 0).reason, "TERMINAL_CONVERGENCE");
  assert.equal(sensitivityCell({ "0": { "": 12 } }, {}, 0, 0).value, null);
  assert.equal(sensitivityCell({ "0": { "0": 12, "0.0": 99 } }, {}, 0, 0).value, null);
});

test("legacy methodology and invalid axes remain distinguishable", () => {
  assert.equal(sensitivityMethod({ name: "WACC" }), null);
  assert.equal(sensitivityMethod({ method: { version: "future-unverified" } }), null);
  assert.equal(sensitivityMethod({ method: { version: "fcff-sensitivity-v2" } })?.version, "fcff-sensitivity-v2");
  assert.deepEqual(sensitivityAxis([0, 0, -1, .02, null, "4", Infinity]), [0, -1, .02]);
  assert.deepEqual(sensitivityAxis({ values: [1] }), []);
});
