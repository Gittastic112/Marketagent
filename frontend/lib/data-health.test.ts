import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { test } from "node:test";
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
