import assert from "node:assert/strict";
import test from "node:test";
import { backendTimeoutMs } from "./backend-timeout.ts";

test("explicit generation has a persistence margin while ordinary requests stay bounded", () => {
  assert.equal(backendTimeoutMs("POST", "research/sessions/12/messages"), 60_000);
  assert.equal(backendTimeoutMs("POST", "brief-sources/12/analyze"), 60_000);
  for (const [method, path] of [["GET", "research/sessions/12/messages"], ["POST", "research/sessions"],
    ["POST", "research/sessions/12/messages/extra"], ["GET", "companies"]]) {
    assert.equal(backendTimeoutMs(method, path), 15_000);
  }
});

test("adapter submissions allow their execution budgets only on the registered commands", () => {
  for (const kind of ["allocation", "simulation", "report", "peers"]) {
    assert.equal(backendTimeoutMs("POST", `api/research-lab/${kind}`), 60_000);
  }
  for (const route of ["api/companies/3/source-adapters/documents/7/extract", "api/companies/3/source-adapters/sec-facts",
    "api/source-adapters/fred-vintage", "api/companies/3/source-adapters/transcript"]) {
    assert.equal(backendTimeoutMs("POST", route), 120_000);
    assert.equal(backendTimeoutMs("GET", route), 15_000);
  }
  for (const route of ["api/data-adapters/nse_mcp/history", "api/data-adapters/identity/openfigi", "api/data-adapters/calendars/schedule"]) {
    assert.equal(backendTimeoutMs("POST", route), 150_000);
    assert.equal(backendTimeoutMs("GET", route), 15_000);
  }
  for (const route of ["api/research-lab/runs", "api/research-lab/report/extra", "api/source-adapters/unknown",
    "api/data-adapters/unknown/history", "api/companies/3/source-adapters/documents/7/extract/extra"]) {
    assert.equal(backendTimeoutMs("POST", route), 15_000);
  }
});
