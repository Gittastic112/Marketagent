import { notFound } from "next/navigation";
import Link from "next/link";
import type { Company, DcfAssumptionSet, ValuationCompanyContext, ValuationModel } from "@/lib/api";
import { serverFetchApi, serverFetchApiResponse } from "@/lib/server-api";
import { PageHeader } from "@/components/page";
import { AdvancedWorkspace } from "@/components/advanced-workspace";
import { StaleDataBanner, MockDataState } from "@/components/ui/data-states";
import { EvidenceTrailDrawerWrapper } from "@/components/intelligence/EvidenceTrailDrawerWrapper";

export const dynamic = "force-dynamic";

export default async function ValuationModelDetailPage(props: { params: Promise<{ id: string; model_id: string }> }) {
  const params = await props.params;
  const companyId = parseInt(params.id, 10);
  const modelId = parseInt(params.model_id, 10);

  if (isNaN(companyId) || isNaN(modelId)) {
    notFound();
  }

  let company: Company;
  let context: ValuationCompanyContext | undefined = undefined;
  try {
    company = await serverFetchApi<Company>(`/companies/${companyId}`);
    try {
      context = await serverFetchApi<ValuationCompanyContext>(`/api/valuation/context/company/${companyId}`);
    } catch {
      // Ignore if missing
    }
  } catch {
    notFound();
  }

  const models = await serverFetchApi<ValuationModel[]>(`/companies/${companyId}/valuation-models`);
  const model = models.find((m) => m.id === modelId);

  if (!model) {
    notFound();
  }

  const assumptionsRes = await serverFetchApiResponse<DcfAssumptionSet[]>(`/valuation-models/${modelId}/assumptions`);
  const assumptions = assumptionsRes.data || [];
  // Get the most recent assumption set (since it's ordered by created_at desc)
  const latestAssumptionSet = assumptions.length > 0 ? assumptions[0] : undefined;
  const isMock = assumptionsRes.meta?.is_mock || assumptionsRes.meta?.source === "mock";

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

      {isMock && (
        <div style={{ marginBottom: "1.5rem" }}>
          <MockDataState message="These DCF assumptions are populated with mock data for demonstration purposes." />
        </div>
      )}

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

      <AdvancedWorkspace model={model} modelId={modelId} companyId={companyId} latestAssumptionSet={latestAssumptionSet} valuationContext={context} />
    </>
  );
}
