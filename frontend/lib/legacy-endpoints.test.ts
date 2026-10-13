import assert from "node:assert/strict";
import { test } from "node:test";
import { ApiError } from "./api/contract.ts";
import { deleteScoringConfig, exportData } from "./api/operations.ts";
import { fetchDebtRatioPrior, fetchDividendPayoutPrior, fetchDividendYieldPrior } from "./api/valuation-priors.ts";
import { fetchMarketQuote } from "./api/market.ts";

test("market quote compatibility uses mounted routes with encoded identities", async () => {
  const original = globalThis.fetch;
  const paths: string[] = [];
  globalThis.fetch = (async url => {
    const parsed = new URL(String(url));
    paths.push(parsed.pathname + parsed.search);
    return Response.json({data:null, meta:{}, errors:[]});
  }) as typeof fetch;
  try {
    await fetchMarketQuote("BRK B");
    await fetchMarketQuote("AAPL", {currency:"USD"});
    await fetchMarketQuote("RELIANCE", {market:"IN", exchange:"NSE", currency:"INR"});
    assert.deepEqual(paths, ["/api/market/quote/BRK%20B", "/api/market/quote/AAPL", "/api/market/quote?market=IN&exchange=NSE&ticker=RELIANCE&currency=INR"]);
  } finally {globalThis.fetch = original;}
});

test("legacy regression helpers call the mounted API routes and preserve explicit zeros", async () => {
  const original = globalThis.fetch;
  const calls: Array<{path: string; method?: string; body: unknown}> = [];
  globalThis.fetch = (async (url, init) => {
    calls.push({path: new URL(String(url)).pathname, method: init?.method, body: JSON.parse(String(init?.body))});
    return Response.json({data: {claim_type: "Estimate", prior_value: 0}, meta: {}, errors: []});
  }) as typeof fetch;
  try {
    const debt = {effective_tax_rate: 0, expected_eps_growth: 0, institutional_holdings: 0, company_age_years: 0};
    const yieldInput = {effective_tax_rate: 0, expected_eps_growth: 0, company_age_years: 0, beta: 0};
    const payout = {beta: 0, return_on_equity: 0};
    assert.equal((await fetchDebtRatioPrior(debt)).prior_value, 0);
    await fetchDividendYieldPrior(yieldInput);
    await fetchDividendPayoutPrior(payout);
    assert.deepEqual(calls, [
      {path: "/api/priors/debt-ratio", method: "POST", body: debt},
      {path: "/api/priors/dividend-yield", method: "POST", body: yieldInput},
      {path: "/api/priors/dividend-payout", method: "POST", body: payout},
    ]);
  } finally {globalThis.fetch = original;}
});

test("unsupported operations retain their compatibility exports but make no request", async () => {
  const original = globalThis.fetch;
  let calls = 0;
  globalThis.fetch = (async () => {calls++; return new Response(null, {status: 204});}) as typeof fetch;
  try {
    await assert.rejects(deleteScoringConfig(1), (error: unknown) => error instanceof ApiError && error.status === 501 && /Not available yet/.test(error.message));
    await assert.rejects(exportData(["companies"], "csv"), (error: unknown) => error instanceof ApiError && error.status === 501 && /Not available yet/.test(error.message));
    assert.equal(calls, 0);
  } finally {globalThis.fetch = original;}
});
