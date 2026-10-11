import assert from "node:assert/strict";
import { test } from "node:test";
import api, { ApiError, deleteApi, exportData, fetchApi, fetchApiResponse, fetchFinancialTrends, fetchMarketQuote, patchApi, postApi, putApi } from "./api.ts";

async function withFetch(response: () => Response, run: (calls: RequestInit[]) => Promise<void>) {
  const original = globalThis.fetch;
  const calls: RequestInit[] = [];
  globalThis.fetch = (async (_url, init) => { calls.push(init ?? {}); return response(); }) as typeof fetch;
  try { await run(calls); } finally { globalThis.fetch = original; }
}

test("JSON methods share error semantics and preserve zero and false payloads", async () => {
  for (const [method, request] of [["POST", postApi], ["PATCH", patchApi], ["PUT", putApi]] as const) {
    await withFetch(() => Response.json({ data: 0, meta: {}, errors: [] }), async (calls) => {
      assert.equal(await request("/test", false), 0);
      assert.equal(calls[0].method, method);
      assert.equal(calls[0].body, "false");
    });
    await withFetch(() => Response.json({ errors: [{ message: "Rejected" }] }, { status: 422 }), async () => {
      await assert.rejects(() => request("/test", 0), (e: unknown) => e instanceof ApiError && e.status === 422 && e.message === "Rejected");
    });
  }
});

test("DELETE accepts a bodyless 204 and GET retains the legacy payload contract", async () => {
  await withFetch(() => new Response(null, { status: 204 }), async () => {
    assert.equal(await deleteApi("/test"), undefined);
  });
  await withFetch(() => Response.json({ id: 4 }), async (calls) => {
    assert.deepEqual(await fetchApi("/test"), { id: 4 });
    assert.equal(calls[0].cache, "no-store");
    assert.equal(calls[0].method, undefined);
  });
});

test("metadata reads retain error envelopes and distinguish parse failure", async () => {
  const envelope = { data: null, meta: { status: "error", is_stale: false }, errors: [{ code: "OWNERSHIP" }] };
  await withFetch(() => Response.json(envelope, { status: 403 }), async () => {
    assert.deepEqual(await fetchApiResponse("/test"), envelope);
  });
  await withFetch(() => new Response("not JSON"), async () => {
    const result = await fetchApiResponse("/test");
    assert.equal(result.errors[0].code, "PARSE_ERROR");
    assert.equal(result.meta.is_stale, false);
  });
});

test("default compatibility client returns the envelope without unwrapping", async () => {
  const envelope = { data: { id: 4 }, meta: { status: "success" }, errors: [] };
  await withFetch(() => Response.json(envelope), async () => {
    assert.deepEqual(await api.get("/test"), envelope);
    assert.deepEqual(await api.post("/test", { id: 4 }), envelope);
  });
});

test("only market and trend 404s use their established empty values", async () => {
  await withFetch(() => new Response(null, { status: 404 }), async (calls) => {
    assert.equal(await fetchMarketQuote("TEST"), null);
    assert.deepEqual(await fetchFinancialTrends("TEST"), []);
    assert.deepEqual(calls[0].headers, { Accept: "application/json" });
    await assert.rejects(() => fetchApi("/missing"), ApiError);
  });
  await withFetch(() => Response.json({ detail: "Provider failed" }, { status: 503 }), async () => {
    await assert.rejects(() => fetchMarketQuote("TEST"), /Provider failed/);
    await assert.rejects(() => fetchFinancialTrends("TEST"), /Provider failed/);
  });
});

test("exports preserve binary bytes and their separate failure contract", async () => {
  await withFetch(() => new Response("a,b\n1,2"), async (calls) => {
    assert.equal(await (await exportData(["companies"], "csv")).text(), "a,b\n1,2");
    assert.deepEqual(JSON.parse(String(calls[0].body)), { resource_types: ["companies"], export_format: "csv" });
  });
  await withFetch(() => new Response(null, { status: 403 }), async () => {
    await assert.rejects(() => exportData([], "csv"), /Export failed with status 403/);
  });
});
