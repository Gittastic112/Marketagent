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

test("older successful sections show freshness guidance without claiming partial availability", () => {
  const Component = load("components/ui/data-states").DataStateNotices;
  const message = "The source was last checked last week.";
  const html = renderToStaticMarkup(createElement(Component, {
    metas: [success({}, { is_stale: true, warnings: [message] }).meta, success({}).meta],
    partialMessage: message,
  }));
  assert.match(html, /Older source data/);
  assert.doesNotMatch(html, /Partial Data|Data unavailable/);
  assert.equal(html.split(message).length - 1, 1);
});

test("data notes retain every distinct warning without repeating or alarming on ordinary metadata", () => {
  const Component = load("components/ui/data-states").DataStateNotices;
  const html = renderToStaticMarkup(createElement(Component, {
    metas: [success({}, { warnings: ["Review the source date.", " Review the source date. ", "Some inputs were supplied manually."] }).meta],
  }));
  assert.equal(html.split("Review the source date.").length - 1, 1);
  assert.match(html, /Data notes/);
  assert.match(html, /Show 1 more data note/);
  assert.match(html, /Some inputs were supplied manually/);
  assert.doesNotMatch(html, /Warnings:/);
});

test("brief previews explain exact stored-event counts and keep the original limits", () => {
  const Component = load("components/brief-public-coverage").BriefPublicCoverage;
  const counts = { status: "partial", eligible_count: 20, included_count: 3, excluded_count: 17, cap: 3, exclusion_reasons: { event_cap: 17 } };
  const html = renderToStaticMarkup(createElement(Component, { compact: true, coverage: {
    version: "public-brief-coverage-v1", status: "partial", selection_basis: "dashboard_preview",
    captured_at: "2026-11-04T12:00:00Z", window_start_exclusive: null, window_end_inclusive: "2026-11-04T12:00:00Z",
    events: counts, failed_runs: counts, inspection_actions: counts,
    limitations: ["Stored counts do not verify source claims."],
  } }));
  assert.match(html, /Selected event inputs: 3 of 20/);
  assert.match(html, /17 excluded \(event cap\)/);
  assert.match(html, /Stored counts do not verify source claims/);
  assert.doesNotMatch(html, /Stored-input selection: partial|class="basis-note"/);
  const historical = renderToStaticMarkup(createElement(Component, { coverage: null }));
  assert.match(historical, /Selection counts were not recorded/);
  assert.doesNotMatch(historical, /Selected event inputs: 0|complete coverage/i);
});

test("compact brief distinguishes selected inputs from the three displayed headlines", () => {
  const Component = load("components/daily-brief-panel").DailyBriefPanel;
  const counts = { status: "partial", eligible_count: 20, included_count: 10, excluded_count: 10, cap: 10, exclusion_reasons: { event_cap: 10 } };
  const html = renderToStaticMarkup(createElement(Component, { dailyBrief: {
    summary: "Mock Data briefing", public_coverage: {
      version: "public-brief-coverage-v1", status: "partial", selection_basis: "dashboard_preview",
      captured_at: "2026-11-04T12:00:00Z", window_start_exclusive: null, window_end_inclusive: "2026-11-04T12:00:00Z",
      events: counts, failed_runs: counts, inspection_actions: counts, limitations: [],
    },
    high_materiality_events: Array.from({ length: 10 }, (_, index) => ({
      event_id: index + 1, headline: `Mock headline ${index + 1}`, claim_type: "Mock Data",
      evidence_status: "manual_record", status: "unreviewed", source_name: null, source_published_at: null,
    })),
  } }));
  assert.match(html, /Selected event inputs: 10 of 20/);
  assert.match(html, /Up to three headlines from the selected inputs/);
  assert.equal((html.match(/evidence-resolution/g) ?? []).length, 3);
  assert.match(html, /Mock headline 3/);
  assert.doesNotMatch(html, /Mock headline 4|Showing 10/);
});

test("company quote preserves currency, zero, source times and unknown delay", () => {
  const html = market(success(quote, { is_mock: true, is_stale: true }));
  for (const text of ["INR", "1,250", "0.00%", "Mock Data", "Older source data", "2026-09-30T10:00:00Z", "2026-10-01T10:00:00Z", "Delay unknown"]) assert.ok(html.includes(text), text);
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
