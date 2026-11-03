import "server-only";

import { serverFetchApiResponse } from "@/lib/server-api";
import { hasUsableData } from "@/lib/data-state-meta";
import { summarizeProcessingRuns } from "@/lib/data-health-summary";
import type { DamodaranCoverageReport, EventEvidenceBackfillReport, EvidenceIntegrityReport, PeerReviewReceiptHealth } from "@/lib/api/health";
import type { ProcessingRun, ProviderHealth, RuntimeReadiness } from "@/lib/api/operations";
import type { Source } from "@/lib/api/companies";
import type { Alert } from "@/lib/api/evidence";

export type HealthAuditMode = "evidence" | "coverage" | "backfill" | null;

export async function loadDataHealth(auditMode: HealthAuditMode, peerAfter: number) {
  const [runtimeReadinessRes, processingRunsRes, sourcesRes, providerHealthRes, alertsRes, peerReceiptHealthRes,
    evidenceIntegrityRes, eventBackfillRes, damodaranCoverageRes] = await Promise.all([
    serverFetchApiResponse<RuntimeReadiness>("/api/readiness"),
    serverFetchApiResponse<ProcessingRun[]>("/processing-runs"),
    serverFetchApiResponse<Source[]>("/sources"),
    serverFetchApiResponse<ProviderHealth[]>("/api/providers/health"),
    serverFetchApiResponse<Alert[]>("/alerts"),
    serverFetchApiResponse<PeerReviewReceiptHealth>(`/data-health/peer-review-receipts?limit=50&after_id=${peerAfter}`),
    auditMode === "evidence"
      ? serverFetchApiResponse<EvidenceIntegrityReport>("/data-health/evidence-integrity?deep=true", { timeoutMs: 60_000 }) : null,
    auditMode === "backfill"
      ? serverFetchApiResponse<EventEvidenceBackfillReport>("/data-health/event-evidence-backfill?limit=100", { timeoutMs: 30_000 }) : null,
    auditMode === "coverage"
      ? serverFetchApiResponse<DamodaranCoverageReport>("/data-health/damodaran-coverage", { timeoutMs: 30_000 }) : null,
  ]);

  const processingRuns = hasUsableData(processingRunsRes) ? processingRunsRes.data : [];
  const sources = hasUsableData(sourcesRes) ? sourcesRes.data : [];
  const providerHealth = hasUsableData(providerHealthRes) ? providerHealthRes.data : [];
  const evidenceIntegrity = hasUsableData(evidenceIntegrityRes) ? evidenceIntegrityRes.data : null;
  const eventBackfill = hasUsableData(eventBackfillRes) ? eventBackfillRes.data : null;
  const damodaranCoverage = hasUsableData(damodaranCoverageRes) ? damodaranCoverageRes.data : null;
  const alerts = hasUsableData(alertsRes) ? alertsRes.data : [];

  const overviewMetas = [
    processingRunsRes,
    sourcesRes,
    providerHealthRes,
    alertsRes,
    peerReceiptHealthRes,
  ].map((response) => response.meta);

  const unreviewedContradictions = alerts.filter((a: Alert) => a.alert_type === "contradiction" && a.review_status === "unreviewed");

  const sourcesById = new Map(sources.map(s => [s.id, s]));

  const workingProviders = providerHealth.filter((provider) => provider.status === "working").length;

  const missingCoreProviders = providerHealth.filter((provider) =>
    provider.requirement_level === "core" && (provider.status === "missing_key" || provider.status === "not_configured")
  ).length;

  const missingOptionalProviders = providerHealth.filter((provider) =>
    provider.requirement_level === "optional" && (provider.status === "missing_key" || provider.status === "not_configured")
  ).length;

  const failingProviders = providerHealth.filter((provider) => provider.status === "failing").length;

  return {
    auditMode, runtimeReadinessRes, peerReceiptHealthRes, evidenceIntegrityRes, eventBackfillRes, damodaranCoverageRes,
    processingRunsRes, sourcesRes, providerHealthRes, alertsRes,
    processingRuns, sources, providerHealth, evidenceIntegrity, eventBackfill, damodaranCoverage,
    overviewMetas, unreviewedContradictions, sourcesById,
    ...summarizeProcessingRuns(processingRuns),
    workingProviders, missingCoreProviders, missingOptionalProviders, failingProviders,
  };
}

export type DataHealthData = Awaited<ReturnType<typeof loadDataHealth>>;
