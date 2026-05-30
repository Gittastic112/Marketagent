import assert from "node:assert/strict";
import { test } from "node:test";

import { ApiError, deleteApi, lookupCompanyByTicker, patchApi, postApi } from "./api.ts";

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

test("postApi preserves backend error detail", async () => {
  const originalFetch = globalThis.fetch;

  globalThis.fetch = (async () =>
    new Response(JSON.stringify({ detail: "Company ticker AAPL already exists" }), {
      status: 409,
      headers: { "Content-Type": "application/json" }
    })) as typeof fetch;

  try {
    await assert.rejects(
      () => postApi("/companies", { ticker: "AAPL", name: "Duplicate" }),
      (error: unknown) => {
        assert.ok(error instanceof ApiError);
        assert.equal(error.status, 409);
        assert.equal(error.message, "Company ticker AAPL already exists");
        return true;
      }
    );
  } finally {
    globalThis.fetch = originalFetch;
  }
});

test("deleteApi preserves backend error detail", async () => {
  const originalFetch = globalThis.fetch;

  globalThis.fetch = (async () =>
    new Response(JSON.stringify({ detail: "Company cannot be deleted while it has linked records." }), {
      status: 409,
      headers: { "Content-Type": "application/json" }
    })) as typeof fetch;

  try {
    await assert.rejects(
      () => deleteApi("/companies/1"),
      (error: unknown) => {
        assert.ok(error instanceof ApiError);
        assert.equal(error.status, 409);
        assert.equal(error.message, "Company cannot be deleted while it has linked records.");
        return true;
      }
    );
  } finally {
    globalThis.fetch = originalFetch;
  }
});

test("lookupCompanyByTicker calls the SEC-backed company lookup endpoint", async () => {
  const calls: string[] = [];
  const originalFetch = globalThis.fetch;

  globalThis.fetch = (async (url: string | URL | Request) => {
    calls.push(String(url));
    return new Response(JSON.stringify({ ticker: "BRK.B", name: "Berkshire Hathaway Inc.", cik: "0001067983" }), {
      status: 200,
      headers: { "Content-Type": "application/json" }
    });
  }) as typeof fetch;

  try {
    const result = await lookupCompanyByTicker("BRK.B");

    assert.deepEqual(result, { ticker: "BRK.B", name: "Berkshire Hathaway Inc.", cik: "0001067983" });
    assert.equal(calls[0], "http://127.0.0.1:8000/companies/lookup?ticker=BRK.B");
  } finally {
    globalThis.fetch = originalFetch;
  }
});

test("lookupCompanyByTicker uses the frontend proxy when called from the browser", async () => {
  const calls: string[] = [];
  const originalFetch = globalThis.fetch;

  Object.defineProperty(globalThis, "window", {
    value: {},
    configurable: true
  });

  globalThis.fetch = (async (url: string | URL | Request) => {
    calls.push(String(url));
    return new Response(JSON.stringify({ ticker: "PLTR", name: "Palantir Technologies Inc.", cik: "0001321655" }), {
      status: 200,
      headers: { "Content-Type": "application/json" }
    });
  }) as typeof fetch;

  try {
    const result = await lookupCompanyByTicker("PLTR");

    assert.deepEqual(result, { ticker: "PLTR", name: "Palantir Technologies Inc.", cik: "0001321655" });
    assert.equal(calls[0], "/api/backend/companies/lookup?ticker=PLTR");
  } finally {
    Reflect.deleteProperty(globalThis, "window");
    globalThis.fetch = originalFetch;
  }
});
