import assert from "node:assert/strict";
import test from "node:test";
import { providersForMarketAction, runDataAdapter, runSourceAdapter } from "./api/adapter-actions.ts";
import { ApiError } from "./api/contract.ts";
import { listResearchRuns } from "./api/research-lab.ts";
import { summarizeApiMetas } from "./data-state-meta.ts";

test("unsupported provider actions fail before a request and dated actions use eligible providers", async () => {
  assert.deepEqual(providersForMarketAction("corporate-actions"), ["massive", "nse_mcp"]);
  assert.deepEqual(providersForMarketAction("dated-quote"), ["nse_mcp"]);
  assert.deepEqual(providersForMarketAction("reference"), ["massive"]);
  const original = globalThis.fetch;
  let requests = 0;
  globalThis.fetch = (async () => { requests++; return Response.json({}); }) as typeof fetch;
  try {
    await assert.rejects(() => runDataAdapter("fmp", "corporate-actions", { market: "US", ticker: "MOCK", start_date: "2025-01-01", end_date: "2025-01-02" }), /provider/i);
    assert.equal(requests, 0);
  } finally { globalThis.fetch = original; }
});

test("failed adapter envelopes retain only safe audit details and history uses a stable cursor", async () => {
  const original = globalThis.fetch;
  globalThis.fetch = (async () => Response.json({ data: null, meta: {}, errors: [{
    code: "SOURCE_UNAVAILABLE", message: "Source unavailable", processing_run_id: 42, retryable: true, private_input: "private",
  }] })) as typeof fetch;
  try {
    await assert.rejects(() => runDataAdapter("fmp", "quote", { market: "US", ticker: "MOCK" }), error => {
      assert.ok(error instanceof ApiError);
      assert.equal(error.processingRunId, 42);
      assert.equal(error.retryable, true);
      assert.ok(!JSON.stringify(error).includes("private"));
      return true;
    });
    let url = "";
    globalThis.fetch = (async input => { url = String(input); return Response.json({ data: [], meta: {}, errors: [] }); }) as typeof fetch;
    await listResearchRuns(123);
    assert.ok(url.endsWith("/api/research-lab/runs?limit=25&before_run_id=123"));
  } finally { globalThis.fetch = original; }
});

test("source and market actions map to explicit registered routes with unchanged payloads", async () => {
  const original = globalThis.fetch;
  const requests: Array<{ url: string; body: unknown }> = [];
  globalThis.fetch = (async (url, init) => {
    requests.push({ url: String(url), body: JSON.parse(String(init?.body)) });
    return Response.json({ data: { processing_run_id: 1 }, meta: {}, errors: [] });
  }) as typeof fetch;
  try {
    await runSourceAdapter("extract", { adapter: "camelot", pages: [2, 4] }, 7, 9);
    await runSourceAdapter("fred-vintage", { series_id: "GDP", as_of: "2025-01-01", observation_start: "2024-01-01", observation_end: "2025-01-01" });
    await runDataAdapter("nse_mcp", "dated-quote", { ticker: "TEST", market: "IN", requested_date: "2025-01-01" });
    await runDataAdapter("fmp", "identity", { id_type: "ID_ISIN", id_value: "TEST" });
    await runDataAdapter("massive", "calendar", { exchange: "XNYS", start_date: "2025-01-01", end_date: "2025-01-02" });
    assert.ok(requests[0].url.endsWith("/api/companies/7/source-adapters/documents/9/extract"));
    assert.deepEqual(requests[0].body, { adapter: "camelot", pages: [2, 4] });
    assert.ok(requests[1].url.endsWith("/api/source-adapters/fred-vintage"));
    assert.ok(requests[2].url.endsWith("/api/data-adapters/nse_mcp/dated-quote"));
    assert.ok(requests[3].url.endsWith("/api/data-adapters/identity/openfigi"));
    assert.ok(requests[4].url.endsWith("/api/data-adapters/calendars/schedule"));
    assert.throws(() => runSourceAdapter("extract", { adapter: "camelot", pages: [2] }, 7), /stored document/);
    assert.throws(() => runSourceAdapter("sec-facts", {}), /company/);
  } finally { globalThis.fetch = original; }
});

test("market adapter receipts retain envelope-only quote freshness and warnings", async () => {
  const original = globalThis.fetch;
  const warning = "Quote timestamp exceeds the 20-minute inspection freshness threshold; the market may be closed.";
  const meta = { status: "success", last_updated: "2025-01-01T10:00:00Z", source: "fmp", is_stale: true, warnings: [warning], confidence: "medium", processing_time_ms: null };
  globalThis.fetch = (async () => Response.json({ data: { provider: "fmp", processing_run_id: 7, warnings: [] }, meta, errors: [] })) as typeof fetch;
  try {
    const execution = await runDataAdapter("fmp", "quote", { market: "US", ticker: "MOCK" });
    assert.deepEqual(execution.meta, meta);
    assert.equal(summarizeApiMetas([execution.meta]).someStale, true);
    assert.deepEqual(execution.meta.warnings, [warning]);
    globalThis.fetch = (async () => Response.json({ data: null, meta, errors: [{ code: "UNAVAILABLE", message: "Source unavailable" }] })) as typeof fetch;
    await assert.rejects(() => runDataAdapter("fmp", "quote", { market: "US", ticker: "MOCK" }), /Source unavailable/);
  } finally { globalThis.fetch = original; }
});
