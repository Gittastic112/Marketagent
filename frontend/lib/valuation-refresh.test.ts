import assert from "node:assert/strict";
import { test } from "node:test";
import { readFileSync } from "node:fs";
import { fetchValuationRefreshRun, fetchValuationRefreshStatus, queueValuationSourceRefresh } from "./api/valuation-refresh.ts";

test("refresh endpoints enqueue without a long-lived provider request and retain owned run identity", async () => {
  const original = globalThis.fetch;
  const calls: Array<{ url: string; method: string }> = [];
  globalThis.fetch = async (input, init) => {
    calls.push({ url: String(input), method: init?.method ?? "GET" });
    return new Response(JSON.stringify({ data: { id: 42, status: "queued" }, meta: {}, errors: [] }), { status: 202 });
  };
  try {
    assert.equal((await queueValuationSourceRefresh(3)).id, 42);
    await fetchValuationRefreshStatus(3);
    await fetchValuationRefreshRun(42);
    assert.equal(calls[0].method, "POST");
    assert.ok(calls[0].url.endsWith("/companies/3/valuation-source-refresh"));
    assert.ok(calls[1].url.endsWith("/companies/3/valuation-source-refresh"));
    assert.ok(calls[2].url.endsWith("/valuation-source-refresh/42"));
  } finally { globalThis.fetch = original; }
});

test("draft refresh keeps source failure, dates, review and pending-edit boundaries visible", () => {
  const panel = readFileSync(new URL("../components/valuation/source-refresh-panel.tsx", import.meta.url), "utf8");
  const draft = readFileSync(new URL("../components/valuation/autofill-draft-review.tsx", import.meta.url), "utf8");
  assert.match(panel, /await beforeQueue\(\)/);
  assert.match(panel, /cancelled/);
  assert.match(panel, /Status unavailable/);
  assert.match(panel, /Weekdays at 7:00 a.m. New York time/);
  assert.match(panel, /step.company_id === companyId/);
  assert.match(panel, /batch status includes other companies/);
  assert.match(panel, /const existing = resource.data\?\.latest_run/);
  assert.match(panel, /resumedRunId.current === existing.id/);
  assert.match(panel, /setRun\(existing\)/);
  assert.match(draft, /fieldset disabled=\{pipelineBusy\}/);
  assert.match(draft, /Open source evidence/);
  assert.match(draft, /stale, review required/);
});
