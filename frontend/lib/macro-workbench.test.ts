import assert from "node:assert/strict";
import { test } from "node:test";

import { normalizeMacroWorkbenchTab, macroNumber, macroPeriodCount, macroBottomUpSegments, macroTopDownPeriods } from "./macro-workbench.ts";

test("macro workbench tab parser accepts planned tab ids", () => {
  assert.equal(normalizeMacroWorkbenchTab("sector"), "sector");
  assert.equal(normalizeMacroWorkbenchTab("scenario"), "scenario");
  assert.equal(normalizeMacroWorkbenchTab("top-down"), "top-down");
  assert.equal(normalizeMacroWorkbenchTab("bottom-up"), "bottom-up");
});

test("macro inputs preserve explicit zero and reject blank, invalid and nonfinite text", () => {
  assert.equal(macroNumber("0", "rate"), 0);
  assert.equal(macroNumber("-0.02", "rate"), -0.02);
  for (const value of ["", " ", "NaN", "Infinity", "0x10", "1e999"]) {
    assert.throws(() => macroNumber(value, "rate"), /finite number/);
  }
});

test("macro forms never discard incomplete segments or manufacture zero observations", () => {
  assert.throws(() => macroBottomUpSegments({segment_1_name: "Known", segment_1_value: "100"}), /Complete/);
  assert.throws(() => macroBottomUpSegments({segment_1_name: "Known", segment_1_sic: "1234", segment_1_value: ""}), /finite number/);
  assert.throws(() => macroTopDownPeriods({period_1: "2021"}), /finite number/);
  const segments = macroBottomUpSegments({segment_1_name: "Zero", segment_1_sic: "1234", segment_1_value: "0"});
  assert.equal(segments[0].segment_value, 0);
});

test("macro history form can expand within bounded periods", () => {
  assert.equal(macroPeriodCount(undefined), 3);
  assert.equal(macroPeriodCount("16"), 16);
  for (const value of ["2", "25", "3.5", "Infinity"]) assert.throws(() => macroPeriodCount(value));
});

test("macro workbench tab parser defaults invalid or missing tabs to series", () => {
  assert.equal(normalizeMacroWorkbenchTab(undefined), "series");
  assert.equal(normalizeMacroWorkbenchTab("unknown"), "series");
  assert.equal(normalizeMacroWorkbenchTab(["scenario", "sector"]), "scenario");
});
