import "server-only";

import { serverFetchApiResponse } from "@/lib/server-api";
import type { DamodaranCoverageReport, EventEvidenceBackfillReport, EvidenceIntegrityReport, PeerReviewReceiptHealth, ProcessingRun, ProviderHealth, RuntimeReadiness, Source, Alert } from "@/lib/api";

export type HealthAuditMode = "evidence" | "coverage" | "backfill" | null;

export async function loadDataHealth(auditMode: HealthAuditMode, peerAfter: number) {
  const [runtimeReadinessRes, processingRunsRes, sourcesRes, providerHealthRes, alertsRes, peerReceiptHealthRes] = await Promise.all([
    serverFetchApiResponse<RuntimeReadiness>("/api/readiness"),
    serverFetchApiResponse<ProcessingRun[]>("/processing-runs"),
    serverFetchApiResponse<Source[]>("/sources"),
    serverFetchApiResponse<ProviderHealth[]>("/api/providers/health"),
    serverFetchApiResponse<Alert[]>("/alerts"),
    serverFetchApiResponse<PeerReviewReceiptHealth>(`/data-health/peer-review-receipts?limit=50&after_id=${peerAfter}`),
  ]);

  const evidenceIntegrityRes = auditMode === "evidence"
    ? await serverFetchApiResponse<EvidenceIntegrityReport>("/data-health/evidence-integrity?deep=true", { timeoutMs: 60_000 })
    : null;

  const eventBackfillRes = auditMode === "backfill"
    ? await serverFetchApiResponse<EventEvidenceBackfillReport>("/data-health/event-evidence-backfill?limit=100", { timeoutMs: 30_000 })
    : null;

  const damodaranCoverageRes = auditMode === "coverage"
    ? await serverFetchApiResponse<DamodaranCoverageReport>("/data-health/damodaran-coverage", { timeoutMs: 30_000 })
    : null;

  const processingRuns = processingRunsRes.data || [];

  const sources = sourcesRes.data || [];

  const providerHealth = providerHealthRes.data || [];

  const evidenceIntegrity = evidenceIntegrityRes?.data ?? null;

  const eventBackfill = eventBackfillRes?.data ?? null;

  const damodaranCoverage = damodaranCoverageRes?.data ?? null;

  const alerts = alertsRes.data || [];

  const overviewMetas = [
    processingRunsRes,
    sourcesRes,
    providerHealthRes,
    alertsRes,
    peerReceiptHealthRes,
  ].filter((response) => response.data !== null).map((response) => response.meta);

  const unreviewedContradictions = alerts.filter((a: Alert) => a.alert_type === "contradiction" && a.review_status === "unreviewed");

  const sourcesById = new Map(sources.map(s => [s.id, s]));

  const totalRuns = processingRuns.length;

  const successRuns = processingRuns.filter(r => r.status === "success" || r.status === "completed").length;

  const failedRuns = processingRuns.filter(r => r.status === "failed" || r.status === "error").length;

  const totalFetched = processingRuns.reduce((sum, r) => sum + r.fetched_count, 0);

  const totalCreated = processingRuns.reduce((sum, r) => sum + r.created_count, 0);

  const totalErrors = processingRuns.reduce((sum, r) => sum + r.error_count, 0);

  const workingProviders = providerHealth.filter((provider) => provider.status === "working").length;

  const missingCoreProviders = providerHealth.filter((provider) =>
    provider.requirement_level === "core" && (provider.status === "missing_key" || provider.status === "not_configured")
  ).length;

  const missingOptionalProviders = providerHealth.filter((provider) =>
    provider.requirement_level === "optional" && (provider.status === "missing_key" || provider.status === "not_configured")
  ).length;

  const failingProviders = providerHealth.filter((provider) => provider.status === "failing").length;

  const byType = new Map<string, ProcessingRun[]>();

  for (const run of processingRuns) {
    const type = run.run_type || "unknown";
    if (!byType.has(type)) byType.set(type, []);
    byType.get(type)!.push(run);
  }
  return { auditMode, runtimeReadinessRes, peerReceiptHealthRes, evidenceIntegrityRes, eventBackfillRes, damodaranCoverageRes, processingRuns, sources, providerHealth, evidenceIntegrity, eventBackfill, damodaranCoverage, alerts, overviewMetas, unreviewedContradictions, sourcesById, totalRuns, successRuns, failedRuns, totalFetched, totalCreated, totalErrors, workingProviders, missingCoreProviders, missingOptionalProviders, failingProviders, byType };
}
