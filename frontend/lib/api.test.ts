import assert from "node:assert/strict";
import { test } from "node:test";

import {
  ApiError,
  archiveValuationDraft,
  deleteApi,
  extractFinancialsFromFiling,
  extractXbrl,
  fetchValuationContext,
  generateValuationMemo,
  lookupCompanyByTicker,
  patchApi,
  putApi,
  postFormApi,
  postApi,
  resetValuationDraftFields,
  runBottomUpMacroSensitivity,
  runMacroScenario,
  runTopDownMacroSensitivity
} from "./api.ts";

const EXPECTED_SERVER_API_BASE_URL =
  process.env.API_BASE_URL ?? process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://127.0.0.1:8000";

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
    assert.equal(calls[0].url, `${EXPECTED_SERVER_API_BASE_URL}/companies/7`);
    assert.equal(calls[0].init.method, "PATCH");
    assert.deepEqual(calls[0].init.headers, { "Content-Type": "application/json" });
    assert.equal(calls[0].init.body, JSON.stringify({ name: "Updated" }));
  } finally {
    globalThis.fetch = originalFetch;
  }
});

test("putApi sends a JSON PUT request and unwraps the response envelope", async () => {
  const calls: Array<{ url: string; init: RequestInit }> = [];
  const originalFetch = globalThis.fetch;
  globalThis.fetch = (async (url: string | URL | Request, init?: RequestInit) => {
    calls.push({ url: String(url), init: init ?? {} });
    return new Response(JSON.stringify({ data: { id: 9 }, meta: {}, errors: [] }), {
      status: 200,
      headers: { "Content-Type": "application/json" },
    });
  }) as typeof fetch;

  try {
    assert.deepEqual(await putApi("/companies/2/industry-allocations", { allocations: [] }), { id: 9 });
    assert.equal(calls[0].url, `${EXPECTED_SERVER_API_BASE_URL}/companies/2/industry-allocations`);
    assert.equal(calls[0].init.method, "PUT");
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

test("valuation draft lifecycle helpers carry optimistic concurrency versions", async () => {
  const calls: Array<{ url: string; body: unknown }> = [];
  const originalFetch = globalThis.fetch;
  globalThis.fetch = (async (url: string | URL | Request, init?: RequestInit) => {
    calls.push({ url: String(url), body: JSON.parse(String(init?.body)) });
    return new Response(JSON.stringify({ id: 4, updated_at: "2026-07-20T10:01:00Z" }), {
      status: 200,
      headers: { "Content-Type": "application/json" },
    });
  }) as typeof fetch;

  try {
    await resetValuationDraftFields(4, ["cash"], "2026-07-20T10:00:00Z");
    await archiveValuationDraft(4, "2026-07-20T10:01:00Z");

    assert.equal(calls[0].url, `${EXPECTED_SERVER_API_BASE_URL}/valuation-drafts/4/reset`);
    assert.deepEqual(calls[0].body, {
      fields: ["cash"],
      expected_updated_at: "2026-07-20T10:00:00Z",
    });
    assert.equal(calls[1].url, `${EXPECTED_SERVER_API_BASE_URL}/valuation-drafts/4/archive`);
    assert.deepEqual(calls[1].body, {
      expected_updated_at: "2026-07-20T10:01:00Z",
    });
  } finally {
    globalThis.fetch = originalFetch;
  }
});

test("financial extraction helpers use registered api-prefixed routes", async () => {
  const calls: string[] = [];
  const originalFetch = globalThis.fetch;
  globalThis.fetch = (async (url: string | URL | Request) => {
    calls.push(String(url));
    return new Response(JSON.stringify({ data: {}, meta: {}, errors: [] }), {
      status: 200,
      headers: { "Content-Type": "application/json" },
    });
  }) as typeof fetch;

  try {
    await extractFinancialsFromFiling(12);
    await extractXbrl(7);

    assert.deepEqual(calls, [
      `${EXPECTED_SERVER_API_BASE_URL}/api/filings/12/extract-financials`,
      `${EXPECTED_SERVER_API_BASE_URL}/api/companies/7/extract-xbrl`,
    ]);
  } finally {
    globalThis.fetch = originalFetch;
  }
});

test("postFormApi sends multipart data through the browser proxy without forcing a content type", async () => {
  const calls: Array<{ url: string; init: RequestInit }> = [];
  const originalFetch = globalThis.fetch;
  Object.defineProperty(globalThis, "window", { value: {}, configurable: true });
  globalThis.fetch = (async (url: string | URL | Request, init?: RequestInit) => {
    calls.push({ url: String(url), init: init ?? {} });
    return new Response(JSON.stringify({ data: { imported: 1 }, meta: {}, errors: [] }), {
      status: 200,
      headers: { "Content-Type": "application/json" },
    });
  }) as typeof fetch;
  const form = new FormData();
  form.append("dataset_code", "implied_erp");

  try {
    await postFormApi("/api/admin/damodaran/import", form);

    assert.equal(calls[0].url, "/api/backend/api/admin/damodaran/import");
    assert.equal(calls[0].init.method, "POST");
    assert.equal(calls[0].init.body, form);
    assert.equal(calls[0].init.headers, undefined);
  } finally {
    Reflect.deleteProperty(globalThis, "window");
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
    assert.equal(calls[0], `${EXPECTED_SERVER_API_BASE_URL}/companies/lookup?ticker=BRK.B`);
  } finally {
    globalThis.fetch = originalFetch;
  }
});

test("lookupCompanyByTicker carries explicit market and exchange context", async () => {
  const calls: string[] = [];
  const originalFetch = globalThis.fetch;

  globalThis.fetch = (async (url: string | URL | Request) => {
    calls.push(String(url));
    return new Response(JSON.stringify({ market: "IN", exchange: "NSE", ticker: "RELIANCE", local_symbol: "RELIANCE", name: "Reliance Industries", source: "local" }), {
      status: 200,
      headers: { "Content-Type": "application/json" }
    });
  }) as typeof fetch;

  try {
    const result = await lookupCompanyByTicker("RELIANCE", { market: "IN", exchange: "NSE" });

    assert.equal(result.market, "IN");
    assert.equal(result.local_symbol, "RELIANCE");
    assert.equal(
      calls[0],
      `${EXPECTED_SERVER_API_BASE_URL}/companies/lookup?market=IN&exchange=NSE&ticker=RELIANCE`,
    );
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

test("fetchApi parses new ApiResponse envelope shape correctly", async () => {
  const originalFetch = globalThis.fetch;

  globalThis.fetch = (async () =>
    new Response(JSON.stringify({
      data: { id: 42, name: "EnvelopeTest" },
      meta: { status: "success", is_stale: false, warnings: [], confidence: "high", source: "internal", last_updated: "2026-06-12" },
      errors: []
    }), {
      status: 200,
      headers: { "Content-Type": "application/json" }
    })) as typeof fetch;

  try {
    const { fetchApi } = await import("./api.ts");
    const result = await fetchApi<{ id: number; name: string }>("/test");
    assert.deepEqual(result, { id: 42, name: "EnvelopeTest" });
  } finally {
    globalThis.fetch = originalFetch;
  }
});

test("fetchApi throws ApiError when envelope contains errors array", async () => {
  const originalFetch = globalThis.fetch;

  globalThis.fetch = (async () =>
    new Response(JSON.stringify({
      data: null,
      meta: { status: "error", is_stale: false, warnings: [], confidence: "high", source: "internal", last_updated: "2026-06-12" },
      errors: [{ code: "TEST_ERROR", message: "Envelope error occurred" }]
    }), {
      status: 400,
      headers: { "Content-Type": "application/json" }
    })) as typeof fetch;

  try {
    const { fetchApi } = await import("./api.ts");
    await assert.rejects(
      () => fetchApi("/test-error"),
      (error: unknown) => {
        assert.ok(error instanceof ApiError);
        assert.equal(error.status, 400);
        assert.equal(error.message, "Envelope error occurred");
        return true;
      }
    );
  } finally {
    globalThis.fetch = originalFetch;
  }
});

test("runMacroScenario posts country-aware macro shock payload", async () => {
  const calls: Array<{ url: string; init: RequestInit }> = [];
  const originalFetch = globalThis.fetch;

  globalThis.fetch = (async (url: string | URL | Request, init?: RequestInit) => {
    calls.push({ url: String(url), init: init ?? {} });
    return new Response(JSON.stringify({
      data: {
        method: "sector_macro_sensitivity",
        market: "IN",
        country: "India",
        sic_code: "5311",
        estimated_value_impact_pct: -0.0301009,
        warnings: []
      },
      meta: { status: "success", is_stale: false, warnings: [], confidence: "medium", source: "internal", last_updated: "2026-06-18" },
      errors: []
    }), {
      status: 200,
      headers: { "Content-Type": "application/json" }
    });
  }) as typeof fetch;

  try {
    const result = await runMacroScenario({
      market: "IN",
      country: "India",
      sic_code: "5311",
      rate_shock: 0.01,
      gdp_shock: 0,
      inflation_shock: 0,
      currency_shock: 0,
      currencyVariableDirection: "stronger_usd"
    });

    assert.equal(result.estimated_value_impact_pct, -0.0301009);
    assert.equal(calls[0].url, `${EXPECTED_SERVER_API_BASE_URL}/api/valuation/macro/scenario`);
    assert.equal(calls[0].init.method, "POST");
    assert.equal(calls[0].init.body, JSON.stringify({
      market: "IN",
      country: "India",
      sic_code: "5311",
      rate_shock: 0.01,
      gdp_shock: 0,
      inflation_shock: 0,
      currency_shock: 0,
      currencyVariableDirection: "stronger_usd"
    }));
  } finally {
    globalThis.fetch = originalFetch;
  }
});

test("macro sensitivity helpers translate UI fields to backend contracts", async () => {
  const calls: Array<{ url: string; body: unknown }> = [];
  const originalFetch = globalThis.fetch;
  globalThis.fetch = (async (url: string | URL | Request, init?: RequestInit) => {
    calls.push({ url: String(url), body: JSON.parse(String(init?.body)) });
    return new Response(JSON.stringify({
      data: { method: "test", observation_count: 3, firm_value: {}, operating_income: {}, confidence_label: "low", warnings: [] },
      meta: { status: "success", is_stale: false, warnings: [], confidence: "medium", source: "internal", last_updated: null },
      errors: [],
    }), { status: 200, headers: { "Content-Type": "application/json" } });
  }) as typeof fetch;

  try {
    await runBottomUpMacroSensitivity({
      market: "IN",
      country: "India",
      segments: [{ segment_name: "Retail", sic_code: "5311", segment_weight: 0.6 }],
    });
    await runTopDownMacroSensitivity({
      periods: [{
        period_label: "2024",
        operating_income: 100,
        market_cap: 800,
        total_debt: 200,
        change_in_long_term_bond_rate: 0.01,
        gdp_growth: 0.06,
        inflation_change: 0.01,
        currency_change: -0.02,
      }],
    });

    assert.deepEqual(calls[0], {
      url: `${EXPECTED_SERVER_API_BASE_URL}/api/valuation/macro/bottom-up`,
      body: {
        market: "IN",
        country: "India",
        segments: [{ name: "Retail", sicCode: "5311", value: 0.6 }],
      },
    });
    assert.deepEqual(calls[1], {
      url: `${EXPECTED_SERVER_API_BASE_URL}/api/valuation/macro/top-down`,
      body: {
        frequency: "annual",
        periods: [{
          period: "2024",
          operating_income: 100,
          market_cap: 800,
          total_debt: 200,
          change_in_long_term_bond_rate: 0.01,
          gdp_growth: 0.06,
          inflation_change: 0.01,
          currency_change: -0.02,
        }],
      },
    });
  } finally {
    globalThis.fetch = originalFetch;
  }
});

test("fetchValuationContext calls the country-aware valuation context endpoint", async () => {
  const calls: string[] = [];
  const originalFetch = globalThis.fetch;

  globalThis.fetch = (async (url: string | URL | Request) => {
    calls.push(String(url));
    return new Response(JSON.stringify({
      data: {
        company_id: 7,
        market: "IN",
        country: "India",
        default_currency: "INR",
        cash_flow_currency: "INR",
        discount_rate_currency: "INR",
        available_benchmark_countries: ["India", "United States"],
        recommended_benchmark_country: "India",
        benchmark_source: "Damodaran/local benchmarks",
        warnings: []
      },
      meta: { status: "success", is_stale: false, warnings: [], confidence: "medium", source: "internal", last_updated: "2026-06-18" },
      errors: []
    }), {
      status: 200,
      headers: { "Content-Type": "application/json" }
    });
  }) as typeof fetch;

  try {
    const result = await fetchValuationContext(7);

    assert.equal(result.market, "IN");
    assert.equal(result.default_currency, "INR");
    assert.equal(calls[0], `${EXPECTED_SERVER_API_BASE_URL}/api/valuation/context/company/7`);
  } finally {
    globalThis.fetch = originalFetch;
  }
});

test("generateValuationMemo posts to the registered valuation AI memo endpoint", async () => {
  const calls: Array<{ url: string; init: RequestInit }> = [];
  const originalFetch = globalThis.fetch;

  globalThis.fetch = (async (url: string | URL | Request, init?: RequestInit) => {
    calls.push({ url: String(url), init: init ?? {} });
    return new Response(JSON.stringify({
      data: { memo_markdown: "Memo" },
      meta: { status: "success", is_stale: false, warnings: [], confidence: "medium", source: "internal", last_updated: "2026-06-18" },
      errors: []
    }), {
      status: 200,
      headers: { "Content-Type": "application/json" }
    });
  }) as typeof fetch;

  try {
    const result = await generateValuationMemo(7, "Base");

    assert.equal(result.memo_markdown, "Memo");
    assert.equal(calls[0].url, `${EXPECTED_SERVER_API_BASE_URL}/valuation/7/scenarios/Base/ai/memo`);
    assert.equal(calls[0].init.method, "POST");
    assert.equal(calls[0].init.body, JSON.stringify({ privacy_disclosure_version: "v1" }));
  } finally {
    globalThis.fetch = originalFetch;
  }
});
