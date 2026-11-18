import assert from "node:assert/strict";
import test from "node:test";
import { runDataAdapter, runSourceAdapter } from "./api/adapter-actions.ts";
import { summarizeApiMetas } from "./data-state-meta.ts";

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
