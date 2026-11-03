import Link from "next/link";
import { PeerReceiptHealthPanel } from "@/components/peer-receipt-health-panel";
import { EmptyState, ErrorState, PageHeader, Panel } from "@/components/page";
import { DataStateNotices } from "@/components/ui/data-states";
import { RuntimeReadinessPanel } from "@/components/runtime-readiness-panel";
import type { DataHealthData } from "@/lib/server/data-health";
import { hasUsableData } from "@/lib/data-state-meta";
import { HealthDiagnostics, HealthDiagnosticSummary } from "./health-diagnostics";
import { ProviderHealthSummary, ProviderHealthTable } from "./provider-health";
import { OperationsSummary, ProcessingHealthTables } from "./processing-health";

export function HealthOverview(data: DataHealthData) {
  const { auditMode, runtimeReadinessRes, peerReceiptHealthRes, processingRunsRes, alertsRes, overviewMetas, unreviewedContradictions, totalRuns } = data;
  return (
    <>
      <PageHeader eyebrow="System Health" title="Data Health" status={hasUsableData(processingRunsRes) ? `${totalRuns} recent runs` : "Runs unavailable"} />

      <section className="health-command-bar" aria-label="Health check mode and diagnostics">
        <div>
          <strong className="health-command-title">{auditMode ? `${auditMode[0].toUpperCase()}${auditMode.slice(1)} diagnostic` : "Fast health check"}</strong>
          <p className="health-command-description">
            {auditMode === "evidence"
              ? "Verifies stored asset bytes, hashes, exact references, and PDF-region geometry. This intentionally takes longer."
              : auditMode === "coverage"
                ? "Reconciles typed Damodaran datasets with the current application coverage inventory."
                : auditMode === "backfill"
                  ? "Previews bounded exact-span evidence candidates without applying any writes."
                  : "Loads operational health without launching expensive integrity audits."}
          </p>
        </div>
        <div className="health-command-actions">
          {auditMode ? <Link prefetch={false} className="secondary-button" href="/data-health">Fast health check</Link> : null}
          <Link prefetch={false} className="secondary-button" href="/data-health?audit=evidence">Run deep evidence audit</Link>
          <Link prefetch={false} className="secondary-button" href="/data-health?audit=coverage">Check benchmark coverage</Link>
          <Link prefetch={false} className="secondary-button" href="/data-health?audit=backfill">Preview evidence backfill</Link>
        </div>
      </section>

      <DataStateNotices
        metas={overviewMetas}
        staleMessage="Some stored health information is older than its freshness threshold."
        partialMessage="Some stored health information is older than its freshness threshold."
        unavailableMessage="Requested health summaries could not be loaded; available panels remain usable."
        mockMessage="Data health rows are mocked. Treat provider status as placeholder information."
      />

      <RuntimeReadinessPanel
        readiness={hasUsableData(runtimeReadinessRes) ? runtimeReadinessRes.data : null}
        errors={runtimeReadinessRes.errors}
      />

      <PeerReceiptHealthPanel response={hasUsableData(peerReceiptHealthRes) ? peerReceiptHealthRes : { ...peerReceiptHealthRes, data: null }} audit={auditMode} />
      <OperationsSummary {...data} />

      <ProviderHealthSummary {...data} />

      <HealthDiagnosticSummary {...data} />

      <Panel title="Unreviewed Contradiction Alerts" className="danger-panel">
        {!hasUsableData(alertsRes) ? <ErrorState message="Contradiction alerts could not be loaded." errors={alertsRes.errors} /> : unreviewedContradictions.length === 0 ? (
          <EmptyState label="No unreviewed contradictions found." />
        ) : (
          <div tabIndex={0} className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>ID</th>
                  <th>Company ID</th>
                  <th>Title</th>
                  <th>Summary</th>
                  <th>Action</th>
                </tr>
              </thead>
              <tbody>
                {unreviewedContradictions.map((alert) => (
                  <tr key={alert.id}>
                    <td>{alert.id}</td>
                    <td>{alert.company_id ?? "Unlinked"}</td>
                    <td>{alert.title}</td>
                    <td>{alert.summary}</td>
                    <td>
                      <Link href={`/alerts/${alert.id}`} className="btn btn-secondary">Review</Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Panel>

      <HealthDiagnostics {...data} />

      <ProviderHealthTable {...data} />

      <ProcessingHealthTables {...data} />
    </>
  );
}
