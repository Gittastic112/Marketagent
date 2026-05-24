import assert from "node:assert/strict";
import { test } from "node:test";

import { patchApi } from "./api.ts";

test("patchApi sends a JSON PATCH request and returns the parsed response", async () => {
  const calls: Array<{ url: string; init: RequestInit }> = [];
  const originalFetch = globalThis.fetch;

  globalThis.fetch = (async (url: string | URL | Request, init?: RequestInit) => {
    calls.push({ url: String(url), init: init ?? {} });
    return new Response(JSON.stringify({ id: 7, name: "Updated" }), {
      status: 200,
      headers: { "Content-Type": "application/json" }
    });
  }) as typeof fetch;

  try {
    const result = await patchApi<{ id: number; name: string }>("/companies/7", { name: "Updated" });

    assert.deepEqual(result, { id: 7, name: "Updated" });
    assert.equal(calls[0].url, "http://127.0.0.1:8000/companies/7");
    assert.equal(calls[0].init.method, "PATCH");
    assert.deepEqual(calls[0].init.headers, { "Content-Type": "application/json" });
    assert.equal(calls[0].init.body, JSON.stringify({ name: "Updated" }));
  } finally {
    globalThis.fetch = originalFetch;
  }
});
