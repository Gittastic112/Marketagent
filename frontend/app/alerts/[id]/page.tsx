import Link from "next/link";

import { EvidenceTrailDrawerWrapper } from "@/components/intelligence/EvidenceTrailDrawerWrapper";
import { ErrorState, PageHeader, Panel } from "@/components/page";
import { DataStateNotices } from "@/components/ui/data-states";
import type { AlertRecord, EvidenceTrail } from "@/lib/api";
import { serverFetchApiResponse } from "@/lib/server-api";

type AlertDetailPageProps = {
  params: Promise<{ id: string }>;
};

export default async function AlertDetailPage({ params }: AlertDetailPageProps) {
  const { id } = await params;
  const alertId = Number.parseInt(id, 10);
  if (!Number.isFinite(alertId)) {
    return <ErrorState message="The alert identifier is invalid." />;
  }

  const [alertResponse, evidenceResponse] = await Promise.all([
    serverFetchApiResponse<AlertRecord>(`/alerts/${alertId}`),
    serverFetchApiResponse<EvidenceTrail>(`/alerts/${alertId}/evidence-trail`),
  ]);
  const alert = alertResponse.data;
  const evidence = evidenceResponse.data;

  if (!alert) {
    return (
      <>
        <PageHeader eyebrow="Review queue" title="Alert unavailable" />
        <ErrorState
          message={alertResponse.errors[0]?.message ?? "The alert was not found or belongs to another user."}
          errors={alertResponse.errors}
        />
      </>
    );
  }

  return (
    <>
      <PageHeader
        eyebrow="Alert review"
        title={alert.title}
        status={`${alert.severity} severity | ${alert.confidence_bucket} confidence`}
      />
      <DataStateNotices
        metas={[alertResponse.meta, evidenceResponse.meta]}
        partialMessage="The alert loaded, but some evidence metadata is unavailable."
      />

      <Panel title="Review Context">
        <div className="brief-list">
          <div className="brief-item">
            <strong>What changed</strong>
            <p>{alert.what_changed || alert.summary || "Not recorded."}</p>
          </div>
          <div className="brief-item">
            <strong>Why it matters</strong>
            <p>{alert.why_it_matters || "Not recorded."}</p>
          </div>
          <div className="brief-item">
            <strong>Review state</strong>
            <p>
              {alert.review_status}
              {alert.reviewed_at ? ` | Reviewed ${new Date(alert.reviewed_at).toLocaleString()}` : ""}
            </p>
            {alert.review_notes ? <p className="muted">{alert.review_notes}</p> : null}
          </div>
        </div>
      </Panel>

      <Panel title="Evidence Traceability">
        {evidence ? (
          <div className="brief-list">
            <div className="brief-item">
              <div className="button-row" style={{ flexWrap: "wrap" }}>
                <span className="badge badge-outline">{evidence.claim_type}</span>
                <span className="badge badge-outline">{evidence.evidence_status} evidence</span>
                <span className="badge badge-outline">{evidence.confidence} confidence</span>
                <span className="badge badge-outline">{evidence.locator.precision}-level locator</span>
              </div>
              <p>{evidence.claim_excerpt || "No supporting claim context is stored."}</p>
              {evidence.document ? (
                <p className="muted">
                  Source: {evidence.source?.name ?? "Unknown source"} | {evidence.document.title}
                </p>
              ) : (
                <p className="muted">No source document is linked.</p>
              )}
              <EvidenceTrailDrawerWrapper alertId={alert.id} />
            </div>
          </div>
        ) : (
          <ErrorState
            message={evidenceResponse.errors[0]?.message ?? "Evidence metadata is unavailable."}
            errors={evidenceResponse.errors}
          />
        )}
      </Panel>

      <div className="button-row">
        <Link className="secondary-button" href="/alerts">Back to alerts</Link>
        {alert.company_id ? (
          <Link className="secondary-button" href={`/companies/${alert.company_id}`}>Open company</Link>
        ) : null}
      </div>
    </>
  );
}
