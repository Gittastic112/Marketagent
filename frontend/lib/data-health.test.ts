import assert from "node:assert/strict";
import { existsSync, readFileSync, statSync } from "node:fs";
import { createRequire } from "node:module";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { test } from "node:test";
import { createElement } from "react";
import { renderToStaticMarkup } from "react-dom/server";
import ts from "typescript";
import { summarizeProcessingRuns } from "./data-health-summary.ts";
import { hasUsableData } from "./data-state-meta.ts";
import { errorResponse, type ApiResponse } from "./api/contract.ts";
import type { ProcessingRun } from "./api/operations.ts";

function run(id: number, overrides: Partial<ProcessingRun> = {}): ProcessingRun {
  return { id, run_type: "Mock Data ingestion", source_type: "mock", source_id: 1, company_id: null,
    started_at: "2026-10-01T12:00:00Z", finished_at: null, status: "success", fetched_count: 3,
    created_count: 2, skipped_duplicate_count: 1, error_count: 0, error_details_json: null,
    metadata_json: null, created_at: "2026-10-01T12:00:00Z", ...overrides };
}

test("health summaries retain zero counts and select latest attempts by time, not response order", () => {
  const runs = [
    run(1),
    run(2, {started_at: "2026-10-01T10:00:00-04:00", status: "COMPLETED"}),
    run(3, {started_at: "2026-10-01T13:00:00Z", status: "failed", created_count: 0, error_count: 2}),
    run(4, {run_type: "", source_id: null, status: "pending", fetched_count: 0, created_count: 0}),
    run(5, {source_id: 2, status: "error", created_count: 0, error_count: 1}),
  ];
  const before = structuredClone(runs);
  const summary = summarizeProcessingRuns(runs);
  assert.equal(summary.totalRuns, 5);
  assert.equal(summary.successRuns, 2);
  assert.equal(summary.failedRuns, 2);
  assert.equal(summary.totalFetched, 12);
  assert.equal(summary.totalCreated, 4);
  assert.equal(summary.totalErrors, 3);
  assert.equal(summary.byType.get("Mock Data ingestion")?.count, 4);
  assert.equal(summary.byType.get("Mock Data ingestion")?.latest.id, 2);
  assert.equal(summary.byType.get("unknown")?.createdCount, 0);
  assert.equal(summary.latestBySource.get(1)?.id, 2);
  assert.equal(summary.latestBySource.get(2)?.id, 5);
  assert.equal(summary.latestBySource.size, 2);
  assert.deepEqual(runs, before);
  assert.equal(summarizeProcessingRuns([run(2), run(1)]).latestBySource.get(1)?.id, 2);
});

test("health summaries index sources once rather than rescanning every run for every source", () => {
  let sourceReads = 0;
  const runs = Array.from({length: 100}, (_, id) => new Proxy(run(id, {source_id: id}), {
    get(target, property, receiver) {
      if (property === "source_id") sourceReads++;
      return Reflect.get(target, property, receiver);
    },
  }));
  const summary = summarizeProcessingRuns(runs);
  for (let id = 0; id < 1000; id++) summary.latestBySource.get(id);
  assert.equal(sourceReads, runs.length);
  assert.equal(summary.byType.get("Mock Data ingestion")?.count, 100);
  const empty = summarizeProcessingRuns([]);
  assert.equal(empty.totalRuns, 0);
  assert.equal(empty.totalErrors, 0);
  assert.equal(empty.latestBySource.size, 0);
  assert.equal(empty.byType.size, 0);
});

function loadWith(fetchResponse: (url: string, options?: {timeoutMs?: number}) => Promise<ApiResponse<unknown>>) {
  const module = {exports: {} as Record<string, any>};
  const code = ts.transpileModule(readFileSync(new URL("./server/data-health.ts", import.meta.url), "utf8"), {
    compilerOptions: {module: ts.ModuleKind.CommonJS, target: ts.ScriptTarget.ES2022},
  }).outputText;
  const require = (name: string) => {
    if (name === "server-only") return {};
    if (name === "@/lib/server-api") return {serverFetchApiResponse: fetchResponse};
    if (name === "@/lib/data-state-meta") return {hasUsableData};
    if (name === "@/lib/data-health-summary") return {summarizeProcessingRuns};
    throw new Error(`Unexpected dependency: ${name}`);
  };
  new Function("require", "module", "exports", code)(require, module, module.exports);
  return module.exports.loadDataHealth;
}

test("health loads only the selected audit and starts it before base requests finish", async () => {
  for (const mode of [null, "evidence", "coverage", "backfill"] as const) {
    const requests: {url: string; timeoutMs?: number}[] = [];
    const pending: Array<() => void> = [];
    const failure = errorResponse("NETWORK_ERROR", "Mock Data unavailable");
    const load = loadWith((url, options) => {
      requests.push({url, ...options});
      return new Promise(resolve => pending.push(() => resolve(failure)));
    });
    const result = load(mode, 51);
    // No timers: all requests must start while every response is still pending.
    assert.equal(requests.length, mode ? 7 : 6);
    assert.ok(requests.some(request => request.url.includes("after_id=51")));
    const audits = requests.filter(request => request.timeoutMs);
    assert.equal(audits.length, mode ? 1 : 0);
    if (mode) assert.equal(audits[0].timeoutMs, mode === "evidence" ? 60_000 : 30_000);
    pending.forEach(resolve => resolve());
    const data = await result;
    assert.equal(data.overviewMetas.length, 5);
    assert.ok(data.overviewMetas.every((meta: unknown) => meta === failure.meta));
    assert.equal(data.processingRunsRes, failure);
    assert.equal(data.sourcesRes, failure);
    assert.equal(data.providerHealthRes, failure);
    assert.equal(data.alertsRes, failure);
    assert.equal(data.evidenceIntegrityRes, mode === "evidence" ? failure : null);
    assert.equal(data.eventBackfillRes, mode === "backfill" ? failure : null);
    assert.equal(data.damodaranCoverageRes, mode === "coverage" ? failure : null);
  }
});

test("health requests never reuse another request's source or run data", async () => {
  let count = 0;
  const load = loadWith(async () => {
    count++;
    return errorResponse("NETWORK_ERROR", "Mock Data unavailable");
  });
  const first = await load(null, 0);
  const second = await load(null, 0);
  assert.equal(count, 12);
  assert.notEqual(first.latestBySource, second.latestBySource);
  assert.notEqual(first.byType, second.byType);
});

const frontendRoot = fileURLToPath(new URL("../", import.meta.url));
const nativeRequire = createRequire(import.meta.url);
function componentHtml(file: string, exportName: string, props: Record<string, unknown>) {
  const cache = new Map<string, any>();
  function load(relative: string): any {
    const candidate = path.resolve(frontendRoot, relative);
    const filename = [candidate, `${candidate}.tsx`, `${candidate}.ts`]
      .find(name => existsSync(name) && statSync(name).isFile())!;
    if (cache.has(filename)) return cache.get(filename);
    const module = {exports: {} as any};
    cache.set(filename, module.exports);
    const code = ts.transpileModule(readFileSync(filename, "utf8"), {compilerOptions: {
      module: ts.ModuleKind.CommonJS, target: ts.ScriptTarget.ES2022,
      jsx: ts.JsxEmit.ReactJSX, esModuleInterop: true,
    }}).outputText;
    const require = (name: string): any => {
      if (name === "@/app/actions") return {applyEventEvidenceBackfill: () => {throw new Error("Unexpected write");}};
      if (name === "next/link") return {__esModule: true, default: ({href, children}: any) => createElement("a", {href}, children)};
      return name.startsWith("@/") ? load(name.slice(2))
        : name.startsWith(".") ? load(path.resolve(path.dirname(filename), name)) : nativeRequire(name);
    };
    new Function("require", "module", "exports", code)(require, module, module.exports);
    return module.exports;
  }
  return renderToStaticMarkup(createElement(load(file)[exportName], props));
}

function success(data: unknown): ApiResponse<unknown> {
  return {data, meta: {status: "success", source: "internal", is_stale: false, last_updated: null,
    warnings: [], confidence: "unknown", processing_time_ms: null}, errors: []};
}
const diagnosticsFile = "components/data-health/health-diagnostics";
const diagnostics = {evidenceIntegrityRes: null, eventBackfillRes: null, damodaranCoverageRes: null,
  evidenceIntegrity: null, eventBackfill: null, damodaranCoverage: null};

test("fast health groups optional diagnostics without metric placeholders or unrequested result panels", () => {
  const summary = componentHtml(diagnosticsFile, "HealthDiagnosticSummary", diagnostics);
  assert.match(summary, /Optional diagnostics/);
  assert.equal((summary.match(/Not run/g) || []).length, 3);
  for (const mode of ["evidence", "coverage", "backfill"]) assert.match(summary, new RegExp(`href="/data-health\\?audit=${mode}"`));
  assert.doesNotMatch(summary, /health-metric-card|Unavailable|Evidence errors/);
  assert.equal(componentHtml(diagnosticsFile, "HealthDiagnostics", diagnostics), "");
});

test("requested diagnostic failures remain unavailable and other audits remain not run", () => {
  const failure = errorResponse("NETWORK_ERROR", "Mock Data audit outage");
  for (const [responseKey, message] of [
    ["evidenceIntegrityRes", "Evidence integrity report is unavailable"],
    ["damodaranCoverageRes", "Damodaran application coverage is unavailable"],
    ["eventBackfillRes", "The historical evidence preview is unavailable"],
  ]) {
    const props = {...diagnostics, [responseKey]: failure};
    const summary = componentHtml(diagnosticsFile, "HealthDiagnosticSummary", props);
    assert.match(summary, /Unavailable/);
    assert.equal((summary.match(/Not run/g) || []).length, 2);
    assert.doesNotMatch(summary, /health-metric-card/);
    const results = componentHtml(diagnosticsFile, "HealthDiagnostics", props);
    assert.match(results, new RegExp(message));
    assert.match(results, /Mock Data audit outage/);
    assert.doesNotMatch(results, /not run automatically|No evidence integrity issues|No unreferenced events/);
  }
});

test("completed evidence diagnostics retain measured zeros and actual empty certification results", () => {
  const evidenceIntegrity = {error_count: 0, warning_count: 0, checked_documents: 0, checked_assets: 0,
    checked_references: 0, checked_financial_candidates: 0, checked_financial_periods: 0,
    certified_financial_history_count: 0, certified_markets: [], financial_histories: [], issues: [],
    status: "healthy", financial_certification_status: "not_available"};
  const props = {...diagnostics, evidenceIntegrity, evidenceIntegrityRes: success(evidenceIntegrity)};
  const summary = componentHtml(diagnosticsFile, "HealthDiagnosticSummary", props);
  assert.equal((summary.match(/class="health-metric-value">0</g) || []).length, 7);
  assert.match(summary, /class="health-metric-value">None</);
  const results = componentHtml(diagnosticsFile, "HealthDiagnostics", props);
  assert.match(results, /No promoted financial histories are available for certification/);
  assert.match(results, /No evidence integrity issues detected/);
  assert.doesNotMatch(results, /Damodaran Application Coverage|Historical Event Evidence Backfill/);
  const backfill = {...diagnostics, eventBackfillRes: success({entries: []}), eventBackfill: {entries: []}};
  assert.match(componentHtml(diagnosticsFile, "HealthDiagnostics", backfill), /No unreferenced events are available in the current bounded batch/);
});

const providersFile = "components/data-health/provider-health";
const providerBase = {configured: false, market: "US", requirement_level: "core", status: "missing_key",
  freshness_label: "missing", recent_run_count: 0, consecutive_failures: 0};
test("provider setup gaps name their affected capabilities without blocking the whole application", () => {
  const providerHealth = [
    {...providerBase, provider_name: "SEC EDGAR", capability: "filings"},
    {...providerBase, provider_name: "Damodaran Benchmarks", capability: "benchmarks", market: "Global", status: "not_configured"},
  ];
  const summary = componentHtml(providersFile, "ProviderHealthSummary", {providerHealth,
    providerHealthRes: success(providerHealth), workingProviders: 0, missingCoreProviders: 2, missingOptionalProviders: 0, failingProviders: 0});
  assert.match(summary, /US filing ingestion/);
  assert.match(summary, /benchmark autofill/);
  assert.match(summary, /Capability setup gaps/);
  assert.doesNotMatch(summary, /gaps are blockers|data-tone="danger"/);
});

test("provider unavailable and successful empty states do not become healthy zero summaries", () => {
  const props = {providerHealth: [], workingProviders: 0, missingCoreProviders: 0, missingOptionalProviders: 0, failingProviders: 0};
  const unavailable = componentHtml(providersFile, "ProviderHealthSummary", {...props,
    providerHealthRes: errorResponse("NETWORK_ERROR", "Mock Data provider outage")});
  assert.match(unavailable, /Provider health could not be loaded/);
  assert.doesNotMatch(unavailable, /health-metric-value|No provider health information/);
  const empty = componentHtml(providersFile, "ProviderHealthSummary", {...props, providerHealthRes: success([])});
  assert.match(empty, /No provider health information available/);
  assert.doesNotMatch(empty, /health-metric-value|could not be loaded/);
});

test("provider details preserve mock, manual, configuration and recorded failure distinctions", () => {
  const providerHealth = [
    {...providerBase, provider_name: "Mock Data SEC", capability: "filings"},
    {...providerBase, provider_name: "Mock Data AI", capability: "ai_analysis", requirement_level: "optional", status: "mock"},
    {...providerBase, provider_name: "Mock Data India", capability: "filings", requirement_level: "manual", market: "IN", status: "manual_only"},
    {...providerBase, provider_name: "Mock Data prices", capability: "market_prices", requirement_level: "optional", status: "not_configured"},
    {...providerBase, provider_name: "Mock Data failed source", capability: "news", status: "failing",
      last_failure_at: "2026-11-05T00:00:00Z", failure_reason: "Mock Data fetch failed", consecutive_failures: 2},
  ];
  const html = componentHtml(providersFile, "ProviderHealthTable", {providerHealth, providerHealthRes: success(providerHealth)});
  for (const label of ["missing_key", "mock", "manual_only", "not_configured", "failing", "Mock Data fetch failed", "2 consecutive failures"]) assert.match(html, new RegExp(label));
  const failed = componentHtml(providersFile, "ProviderHealthTable", {providerHealth,
    providerHealthRes: {...errorResponse("NETWORK_ERROR", "Mock Data outage"), data: providerHealth}});
  assert.match(failed, /Provider health could not be loaded/);
  assert.doesNotMatch(failed, /Mock Data SEC|Mock Data AI/);
});
