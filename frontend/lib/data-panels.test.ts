import assert from "node:assert/strict";
import { readFileSync, existsSync } from "node:fs";
import { createRequire } from "node:module";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { test } from "node:test";
import { createElement } from "react";
import { renderToStaticMarkup } from "react-dom/server";
import ts from "typescript";
import { errorResponse, type ApiResponse } from "./api/contract.ts";

const root = fileURLToPath(new URL("../", import.meta.url));
const nativeRequire = createRequire(import.meta.url);
const cache = new Map<string, Record<string, any>>();

// Render the real server components and shared data-state notices. No DOM
// library or snapshot of the implementation is needed for these output claims.
function load(relative: string): Record<string, any> {
  const candidate = path.resolve(root, relative);
  const full = [candidate, `${candidate}.tsx`, `${candidate}.ts`].find(existsSync)!;
  if (cache.has(full)) return cache.get(full)!;
  const module = { exports: {} as Record<string, any> };
  cache.set(full, module.exports);
  const code = ts.transpileModule(readFileSync(full, "utf8"), {
    compilerOptions: { module: ts.ModuleKind.CommonJS, target: ts.ScriptTarget.ES2022,
      jsx: ts.JsxEmit.ReactJSX, esModuleInterop: true },
  }).outputText;
  const require = (name: string) => name.startsWith("@/") ? load(name.slice(2))
    : name.startsWith(".") ? load(path.resolve(path.dirname(full), name)) : nativeRequire(name);
  new Function("require", "module", "exports", code)(require, module, module.exports);
  return module.exports;
}

function success<T>(data: T, overrides = {}): ApiResponse<T> {
  return { data, meta: { status: "success", source: "internal", is_stale: false,
    last_updated: null, warnings: [], confidence: "unknown", processing_time_ms: null,
    ...overrides }, errors: [] };
}

const quote = { current_price: 1250, change_percent: 0, market_cap: 0, pe_ratio: 0,
  currency: "INR", provider_name: "Mock Data provider", source_timestamp: "2026-09-30T10:00:00Z",
  observed_at: "2026-10-01T10:00:00Z", last_updated: "2026-10-01T10:00:00Z",
  price_type: "quote", delay_minutes: null, warnings: ["Mock Data only"] };

function market(response: ApiResponse<any>) {
  return renderToStaticMarkup(createElement(load("components/company-market-header").CompanyMarketHeader, { response }));
}
function financial(response: ApiResponse<any>) {
  return renderToStaticMarkup(createElement(load("components/financial-trends").FinancialTrends, { response, companyId: 17 }));
}

test("company quote preserves currency, zero, source times and unknown delay", () => {
  const html = market(success(quote, { is_mock: true, is_stale: true }));
  for (const text of ["INR", "1,250", "0.00%", "Mock Data", "Stale", "2026-09-30T10:00:00Z", "2026-10-01T10:00:00Z", "Delay unknown"]) assert.ok(html.includes(text), text);
  assert.doesNotMatch(html, /\$1,250|>Live</);
  assert.match(market(success({ ...quote, current_price: 0 })), /INR 0/);
  assert.match(market(success({ ...quote, currency: null })), /Currency unknown/);
});

test("company quote distinguishes missing, failed and unconfigured responses", () => {
  assert.match(market(success(null)), /No stored quote/);
  const failed = market({ ...errorResponse("NETWORK_ERROR", "Connection unavailable"), data: quote });
  assert.match(failed, /Price data could not be loaded/);
  assert.doesNotMatch(failed, /1,250|No stored quote|Stale/);
  assert.match(market(errorResponse("NOT_CONFIGURED", "Select a price provider")), /Select a price provider/);
  assert.match(market(success({ ...quote, current_price: null })), /Price not available/);
});

test("recorded financial metrics retain exact units and report date without USD inference", () => {
  const html = financial(success([{ id: 1, year: 2026, quarter: null, period_type: "annual", report_date: "2026-05-31",
    currency: "INR", currency_source: "manual", currency_confidence: "user_asserted",
    metrics: [{ metric_name: "Revenue", value: 1250, unit: "INR million" },
      { metric_name: "Net Income", value: 0, unit: "INR million" },
      { metric_name: "EPS (Basic)", value: 3.5, unit: "INR/share" },
      { metric_name: "Total Assets", value: 600, unit: null }] }], { is_mock: true }));
  for (const text of ["1,250", "INR million", "INR/share", "2026-05-31", "Unit unknown", "Mock Data", "unreviewed", "/companies/17/fundamentals"]) assert.ok(html.includes(text), text);
  assert.doesNotMatch(html, /\$|1250\.00B/);
});

test("financial request failure never becomes an empty-history claim", () => {
  assert.match(financial(success([])), /No recorded financial periods/);
  const failed = financial(errorResponse("NETWORK_ERROR", "Connection unavailable"));
  assert.match(failed, /Financial history could not be loaded/);
  assert.doesNotMatch(failed, /No recorded financial periods|No financial data/);
});

test("duplicate financial metrics are withheld rather than choosing a value", () => {
  const html = financial(success([{ id: 1, year: 2026, report_date: "2026-05-31", metrics: [
    { metric_name: "Revenue", value: 123456, unit: "USD" },
    { metric_name: "Revenue", value: 987654, unit: "INR" },
  ] }]));
  assert.match(html, /Conflicting records/);
  assert.doesNotMatch(html, /123,456|987,654/);
});

test("portfolio transport failures give retry guidance without claiming missing evidence", () => {
  const performance = load("components/portfolio-performance-panel").PortfolioPerformancePanel;
  const props = {snapshots:[{calculation_status:"complete"}, {calculation_status:"complete"}],
    startDate:"2026-05-02",endDate:"2026-05-06",performance:null,attribution:null,opportunityCost:null};
  const failed = renderToStaticMarkup(createElement(performance, {...props, requestFailed:true}));
  assert.match(failed, /Performance data could not be loaded. Retry Calculate Period/);
  assert.doesNotMatch(failed, /Choose two complete snapshot dates/);
  assert.match(renderToStaticMarkup(createElement(performance, props)), /Choose two complete snapshot dates/);
  const risk = load("components/portfolio-risk-return-panel").PortfolioRiskReturnPanel;
  const unavailable = renderToStaticMarkup(createElement(risk, {comparison:null, requestFailed:true}));
  assert.match(unavailable, /Risk comparison could not be loaded/);
  assert.doesNotMatch(unavailable, /Add dated market prices/);
});
