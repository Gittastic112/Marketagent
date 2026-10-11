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

export const dynamic = "force-dynamic";

export default async function ValuationModelDetailPage(props: { params: Promise<{ id: string; model_id: string }> }) {
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
    notFound();
  }
  const company = companyResult.value;
  const model = modelResult.value;
  if (model.company_id !== companyId) {
    notFound();
  }

  const [contextResult, assumptionsResult] = await Promise.allSettled([
    serverFetchApi<ValuationCompanyContext>(`/api/valuation/context/company/${companyId}`),
    serverFetchApiResponse<DcfAssumptionSet[]>(`/valuation-models/${modelId}/assumptions`),
  ]);
  const context = contextResult.status === "fulfilled" ? contextResult.value : undefined;
  const assumptionsRes = assumptionsResult.status === "fulfilled" ? assumptionsResult.value : null;
  const assumptions = assumptionsRes?.data || [];
  // Get the most recent assumption set (since it's ordered by created_at desc)
  const latestAssumptionSet = assumptions.length > 0 ? assumptions[0] : undefined;
  const updateModelAction = updateValuationModelWithState.bind(null, modelId.toString(), companyId.toString());

  return (
    <>
      <div style={{ marginBottom: "2rem", display: "flex", justifyContent: "space-between", alignItems: "flex-end", borderBottom: "1px solid var(--line)", paddingBottom: "1.5rem" }}>
        <div>
          <div style={{ fontSize: "1.1rem", fontWeight: 500, color: "var(--text-muted)", marginBottom: "0.25rem" }}>
            {company.name} ({company.ticker})
          </div>
          <h1 style={{ fontSize: "2rem", margin: 0, fontWeight: 700 }}>Intrinsic Valuation</h1>
          <div style={{ display: "flex", gap: "1rem", marginTop: "0.5rem", fontSize: "0.9rem", color: "var(--text-muted)" }}>
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
          key={`${companyId}:${modelId}`}
          model={model}
          modelId={modelId}
          companyId={companyId}
          latestAssumptionSet={latestAssumptionSet}
          valuationContext={context}
        />
      ) : null}
    </>
  );
}
