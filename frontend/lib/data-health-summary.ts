import type { ProcessingRun } from "./api/operations.ts";

type RunTypeSummary = { count: number; createdCount: number; latest: ProcessingRun };

function laterRun(candidate: ProcessingRun, current: ProcessingRun | undefined) {
  if (!current) return true;
  const difference = Date.parse(candidate.started_at) - Date.parse(current.started_at);
  return difference > 0 || (difference === 0 && candidate.id > current.id);
}

/** Summarize the returned recent-run window once; these are not lifetime totals. */
export function summarizeProcessingRuns(runs: readonly ProcessingRun[]) {
  let successRuns = 0;
  let failedRuns = 0;
  let totalFetched = 0;
  let totalCreated = 0;
  let totalErrors = 0;
  const byType = new Map<string, RunTypeSummary>();
  const latestBySource = new Map<number, ProcessingRun>();

  for (const run of runs) {
    const status = run.status.toLowerCase();
    if (status === "success" || status === "completed") successRuns++;
    if (status === "failed" || status === "error") failedRuns++;
    totalFetched += run.fetched_count;
    totalCreated += run.created_count;
    totalErrors += run.error_count;

    const type = run.run_type || "unknown";
    const group = byType.get(type);
    if (group) {
      group.count++;
      group.createdCount += run.created_count;
      if (laterRun(run, group.latest)) group.latest = run;
    } else {
      byType.set(type, { count: 1, createdCount: run.created_count, latest: run });
    }
    const sourceId = run.source_id;
    if (sourceId !== null && laterRun(run, latestBySource.get(sourceId))) latestBySource.set(sourceId, run);
  }

  return { totalRuns: runs.length, successRuns, failedRuns, totalFetched, totalCreated, totalErrors, byType, latestBySource };
}
