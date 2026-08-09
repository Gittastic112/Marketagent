import assert from "node:assert/strict";
import { test } from "node:test";

import { normalizeMacroWorkbenchTab } from "./macro-workbench.ts";

test("macro workbench tab parser accepts planned tab ids", () => {
  assert.equal(normalizeMacroWorkbenchTab("sector"), "sector");
  assert.equal(normalizeMacroWorkbenchTab("scenario"), "scenario");
  assert.equal(normalizeMacroWorkbenchTab("top-down"), "top-down");
  assert.equal(normalizeMacroWorkbenchTab("bottom-up"), "bottom-up");
});

test("macro workbench tab parser defaults invalid or missing tabs to series", () => {
  assert.equal(normalizeMacroWorkbenchTab(undefined), "series");
  assert.equal(normalizeMacroWorkbenchTab("unknown"), "series");
  assert.equal(normalizeMacroWorkbenchTab(["scenario", "sector"]), "scenario");
});
