import { notFound } from "next/navigation";
import Link from "next/link";
import type { Company, DcfAssumptionSet, ValuationCompanyContext, ValuationModel } from "@/lib/api";
import { serverFetchApi, serverFetchApiResponse } from "@/lib/server-api";
import { ErrorState, NotConfiguredState, Panel } from "@/components/page";
import { updateValuationModelWithState } from "@/app/actions";
import { AdvancedWorkspace } from "@/components/advanced-workspace";
import { ValuationModelMetadataForm } from "@/components/valuation/valuation-model-metadata-form";
import { DataStateNotices, StaleDataBanner } from "@/components/ui/data-states";
import { EvidenceTrailDrawerWrapper } from "@/components/intelligence/EvidenceTrailDrawerWrapper";
import { ValuationVersionHistory } from "@/components/valuation/version-history";
import type { ValuationVersionReceipt } from "@/lib/api/valuation-preview";
import { ApiError } from "@/lib/api/contract";

export const dynamic = "force-dynamic";

export default async function ValuationModelDetailPage(props: { params: Promise<{ id: string; model_id: string }>; searchParams?: Promise<{ version?: string }> }) {
  const params = await props.params;
  const companyId = parseInt(params.id, 10);
  const modelId = parseInt(params.model_id, 10);

  if (isNaN(companyId) || isNaN(modelId)) {
    notFound();
  }

  const [companyResult, modelResult] = await Promise.allSettled([
    serverFetchApi<Company>(`/companies/${companyId}`),
    serverFetchApi<ValuationModel>(`/valuation-models/${modelId}`),
  ]);
  if (companyResult.status === "rejected" || modelResult.status === "rejected") {
    const failures = [companyResult, modelResult].filter(result => result.status === "rejected");
    if (failures.some(result => result.status === "rejected" && result.reason instanceof ApiError && result.reason.status === 404)) notFound();
    return <ErrorState message="The saved model could not be loaded. Reload to retry; no cached result is shown." />;
  }
  const company = companyResult.value;
  const model = modelResult.value;
  if (model.company_id !== companyId) {
    notFound();
  }

  const [contextResult, assumptionsResult, receiptsResult] = await Promise.allSettled([
    serverFetchApi<ValuationCompanyContext>(`/api/valuation/context/company/${companyId}`),
    serverFetchApiResponse<DcfAssumptionSet[]>(`/valuation-models/${modelId}/assumptions`),
    serverFetchApi<ValuationVersionReceipt[]>(`/valuation-models/${modelId}/version-receipts`),
  ]);
  const context = contextResult.status === "fulfilled" ? contextResult.value : undefined;
  const assumptionsRes = assumptionsResult.status === "fulfilled" ? assumptionsResult.value : null;
  const assumptions = assumptionsRes?.data || [];
  // Get the most recent assumption set (since it's ordered by created_at desc)
  const requested = (await props.searchParams)?.version;
  const latestAssumptionSet = requested ? assumptions.find(row => String(row.id) === requested) : assumptions[0];
  if (requested && assumptionsResult.status === "fulfilled" && !latestAssumptionSet) notFound();
  const historical = !!latestAssumptionSet && latestAssumptionSet.id !== assumptions[0]?.id;
  const updateModelAction = updateValuationModelWithState.bind(null, modelId.toString(), companyId.toString());

  return (
    <>
      <div className="saved-valuation-header">
        <div>
          <div className="saved-valuation-company">
            {company.name} ({company.ticker})
          </div>
          <h1>Intrinsic Valuation</h1>
          <div className="saved-valuation-meta">
            <span><strong style={{ color: "var(--text)" }}>Scenario:</strong> {model.name}</span>
            {latestAssumptionSet && (
              <span><strong style={{ color: "var(--text)" }}>Last saved:</strong> {new Date(latestAssumptionSet.created_at).toLocaleDateString()}</span>
            )}
          </div>
        </div>
        <div>
          <Link href={`/companies/${company.id}/valuation`} className="btn btn-outline">&larr; Back to Models</Link>
        </div>
      </div>

      <Panel title="Model details">
        <ValuationModelMetadataForm action={updateModelAction} name={model.name} description={model.description} />
      </Panel>
      <ValuationVersionHistory companyId={companyId} modelId={modelId} versions={assumptions}
        selectedId={latestAssumptionSet?.id} receipts={receiptsResult.status === "fulfilled" ? receiptsResult.value : null} />
      {historical && <p role="status">Viewing historical version #{latestAssumptionSet?.id}. <Link href={`/companies/${companyId}/valuation/${modelId}`}>Return to latest version</Link></p>}

      {assumptionsRes?.meta ? (
        <DataStateNotices
          metas={[assumptionsRes.meta]}
          mockMessage="These DCF assumptions are mock data and must not be used as investment evidence."
        />
      ) : null}

      {!context ? (
        <NotConfiguredState
          title="Market context unavailable"
          description="Currency and benchmark context could not be loaded. Saving is gated until the model currencies can be reviewed."
        />
      ) : null}

      {assumptionsResult.status === "rejected" || !assumptionsRes?.data ? (
        <ErrorState message="Could not load this model's assumptions or outputs. No cached valuation result is being shown." />
      ) : null}

      {latestAssumptionSet?.is_stale && (
        <div style={{ marginBottom: "1.5rem" }}>
          <StaleDataBanner
            message={latestAssumptionSet.stale_reason || "Recent events may have invalidated some assumptions."}
            lastUpdated={latestAssumptionSet.created_at}
          />
          {latestAssumptionSet.stale_event_id && (
             <EvidenceTrailDrawerWrapper eventId={latestAssumptionSet.stale_event_id} />
          )}
        </div>
      )}

      {assumptionsResult.status === "fulfilled" && assumptionsRes?.data ? (
        <AdvancedWorkspace
          key={`${companyId}:${modelId}:${requested || "latest"}`}
          model={model}
          modelId={modelId}
          companyId={companyId}
          latestAssumptionSet={latestAssumptionSet}
          valuationContext={context}
          readOnly={historical}
        />
      ) : null}
    </>
  );
}
