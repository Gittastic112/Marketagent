import { notFound } from "next/navigation";
import Link from "next/link";
import type { Company, ValuationCompanyContext, ValuationModelSummary } from "@/lib/api";
import { serverFetchApi } from "@/lib/server-api";
import { ApiError } from "@/lib/api/contract";
import { deleteValuationModelWithState } from "@/app/actions";
import { DeleteRecordForm } from "@/components/delete-record-form";
import { ErrorState, PageHeader, Panel } from "@/components/page";
import { MarketContextPanel } from "@/components/valuation/market-context-panel";
import { formatCurrency } from "@/lib/formatting";
import { IndustryMappingSection } from "./industry-mapping-section";

export const dynamic = "force-dynamic";

function modelReadiness(model: ValuationModelSummary): { label: string; detail: string } {
  const labels: Record<ValuationModelSummary["readiness"], string> = {
    setup_incomplete: "Setup incomplete",
    review_required: "Review required",
    calculation_unavailable: "Calculation unavailable",
    blocked: "Blocked",
    calculated: "Calculated",
  };
  return { label: labels[model.readiness], detail: model.readiness_detail };
}

export default async function ValuationPage(props: { params: Promise<{ id: string }> }) {
  const params = await props.params;
  const companyId = Number(params.id);
  if (!Number.isInteger(companyId) || companyId <= 0) {
    notFound();
  }

  let company: Company;
  try {
    company = await serverFetchApi<Company>(`/companies/${companyId}`);
    if (!company) throw new Error("Company response is unavailable");
  } catch (error) {
    if (error instanceof ApiError && error.status === 404) notFound();
    return <><PageHeader eyebrow="Company" title="Valuation Models" />
      <ErrorState message="Company information could not be loaded." />
      <div className="button-row"><a className="secondary-button" href={`/companies/${companyId}/valuation`}>Try again</a>
        <Link href="/companies">Back to companies</Link></div></>;
  }

  const [contextResult, modelsResult] = await Promise.allSettled([
    serverFetchApi<ValuationCompanyContext>(`/api/valuation/context/company/${companyId}`),
    serverFetchApi<ValuationModelSummary[]>(`/companies/${companyId}/valuation-model-summaries`),
  ]);
  const context = contextResult.status === "fulfilled" ? contextResult.value : null;
  const modelsAvailable = modelsResult.status === "fulfilled" && Array.isArray(modelsResult.value);
  const models = modelsAvailable ? modelsResult.value : [];
  const deleteModelAction = deleteValuationModelWithState.bind(null, companyId.toString());

  return (
    <>
      <div className="valuation-page-titlebar">
        <PageHeader eyebrow={company.ticker} title="Valuation Models" status={modelsAvailable ? `${models.length} model${models.length !== 1 ? "s" : ""}` : "Models unavailable"} />
        <Link href={`/companies/${company.id}`} className="secondary-button">&larr; Back to Company</Link>
      </div>

      <IndustryMappingSection company={company} />
      <Link prefetch={false} href={`/companies/${companyId}/valuation/peers`} className="secondary-button">Manage sourced peer sets</Link>

      {context ? (
        <MarketContextPanel context={context} />
      ) : (
        <Panel title="Market Context">
          <ErrorState message="Market context could not be loaded." />
          <p>Model creation remains available. Review market, country and currency before using discount-rate assumptions.</p>
          <div className="button-row"><a className="secondary-button" href={`/companies/${companyId}/valuation`}>Try again</a>
            <Link href={`/companies/${companyId}/setup`}>Review company setup</Link></div>
        </Panel>
      )}

      <Panel title="Create New Model">
        <div style={{ display: "flex", flexDirection: "column", gap: "1rem" }}>
          <p style={{ color: "var(--text-secondary)", margin: 0 }}>
            Start with source-backed defaults, confirm them once, and edit only the assumptions you want to change.
          </p>
          <div>
            <Link href={`/companies/${companyId}/valuation/draft`} className="primary-button" style={{ display: "inline-block", textDecoration: "none", padding: "0.75rem 1.5rem", background: "var(--accent)", color: "white", borderRadius: "4px", fontWeight: 600 }}>
              Create Valuation Model
            </Link>
          </div>
        </div>
      </Panel>

      <Panel title="Valuation Models">
        {!modelsAvailable ? (
          <><ErrorState message="Could not load valuation models." />
            <a className="secondary-button" href={`/companies/${companyId}/valuation`}>Try again</a></>
        ) : models.length === 0 ? (
          <div className="empty">
            <strong>No valuation models yet.</strong>
            <p>Create a reviewed draft above to establish assumptions, provenance, diagnostics, and the first calculated output.</p>
          </div>
        ) : (
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>Name</th>
                  <th>Description</th>
                  <th>Type</th>
                  <th>Model readiness</th>
                  <th>Latest estimate</th>
                  <th>Runs</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {models.map((model) => (
                  <tr key={model.id}>
                    <td>
                      <Link href={`/companies/${companyId}/valuation/${model.id}`} style={{ color: "var(--accent)", fontWeight: 600 }}>
                        {model.name}
                      </Link>
                    </td>
                    <td>{model.description ?? "—"}</td>
                    <td>{model.model_type.replaceAll("_", " ")}</td>
                    <td>
                      <strong>{modelReadiness(model).label}</strong>
                      <div style={{ color: "var(--text-muted)", fontSize: "0.8rem", marginTop: "0.2rem" }}>
                        {modelReadiness(model).detail}
                      </div>
                    </td>
                    <td>
                      {model.readiness === "calculated" && model.intrinsic_value_per_share != null
                        ? formatCurrency(model.intrinsic_value_per_share, model.cash_flow_currency || context?.default_currency || "USD")
                        : model.intrinsic_value_per_share != null ? "Not reliable" : "Not available"}
                      <div style={{ color: "var(--text-muted)", fontSize: "0.75rem" }}>Estimate</div>
                    </td>
                    <td>{model.assumption_set_count} sets</td>
                    <td>
                      <DeleteRecordForm action={deleteModelAction} label="Delete model" recordId={model.id} />
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Panel>
    </>
  );
}
