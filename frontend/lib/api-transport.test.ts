import assert from "node:assert/strict";
import { test } from "node:test";
import api, { ApiError, deleteApi, fetchApi, fetchApiResponse, fetchFinancialTrends, fetchMarketQuote, patchApi, postApi, putApi } from "./api.ts";
import { postBlobApi } from "./api/transport.ts";

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
    assert.equal(await (await postBlobApi("/export-test", {resource_types: ["companies"], export_format: "csv"})).text(), "a,b\n1,2");
    assert.deepEqual(JSON.parse(String(calls[0].body)), { resource_types: ["companies"], export_format: "csv" });
  });
  await withFetch(() => new Response(null, { status: 403 }), async () => {
    await assert.rejects(() => postBlobApi("/export-test", {}), /Export failed with status 403/);
  });
});

test("validation errors expose actionable field paths without echoing submitted data", async () => {
  await withFetch(() => Response.json({ detail: [{ loc: ["body", "dataset", "observations", 2, "returns"], msg: "Field required", input: "private-source-text" }] }, { status: 422 }), async () => {
    await assert.rejects(() => postApi("/test", {}), (error: unknown) => error instanceof ApiError
      && error.status === 422 && error.message === "dataset.observations.2.returns: Field required" && !error.message.includes("private-source-text"));
  });
});

test("failed operations retain safe processing-run details for both HTTP and envelope errors", async () => {
  for (const status of [200, 503]) {
    const detail = { code: "ADAPTER_TIMEOUT", message: "Source request timed out", processing_run_id: 42, retryable: true, input: "private-source-text" };
    await withFetch(() => Response.json({ data: null, meta: {}, errors: [detail] }, { status }), async () => {
      await assert.rejects(() => postApi("/test", {}), (error: unknown) => error instanceof ApiError
        && error.status === status && error.code === "ADAPTER_TIMEOUT" && error.processingRunId === 42 && error.retryable === true
        && !JSON.stringify(error).includes("private-source-text"));
    });
  }
});

test("error receipts reject malformed run identifiers without retaining private input", () => {
  for (const value of [-1, 0, true, "42", Number.MAX_SAFE_INTEGER + 1]) {
    const error = new ApiError("Unavailable", 503, { processing_run_id: value, retryable: "yes", input: "private" });
    assert.equal(error.processingRunId, undefined);
    assert.equal(error.retryable, undefined);
    assert.ok(!JSON.stringify(error).includes("private"));
  }
});
