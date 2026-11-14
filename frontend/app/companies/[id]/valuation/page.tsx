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

      <Panel title="Saved models">
        {!modelsAvailable ? (
          <><ErrorState message="Could not load valuation models." />
            <a className="secondary-button" href={`/companies/${companyId}/valuation`}>Try again</a></>
        ) : models.length === 0 ? (
          <div className="empty">
            <strong>No valuation models yet.</strong>
            <p>Start with the financial basis and assumptions below. Missing inputs stay explicit until they can be reviewed.</p>
          </div>
        ) : (
          <div className="table-wrap" tabIndex={0} role="region" aria-label="Saved valuation models">
            <table>
              <thead>
                <tr>
                  <th>Name</th>
                  <th>Type</th>
                  <th>Last calculation</th>
                  <th>Model readiness</th>
                  <th>Latest estimate</th>
                  <th>Saved input sets</th>
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
                      {model.description && <details className="valuation-model-description"><summary>Model description</summary><p>{model.description}</p></details>}
                    </td>
                    <td>{model.model_type.replaceAll("_", " ")}</td>
                    <td>{model.latest_run_at ? model.latest_run_at.slice(0, 10) : "Not calculated"}</td>
                    <td>
                      <strong>{modelReadiness(model).label}</strong>
                      <div style={{ color: "var(--text-muted)", fontSize: "0.8rem", marginTop: "0.2rem" }}>
                        {modelReadiness(model).detail}
                      </div>
                    </td>
                    <td>
                      {model.readiness === "calculated" && model.intrinsic_value_per_share != null
                        && Number.isFinite(model.intrinsic_value_per_share) && /^[A-Z]{3}$/.test(model.cash_flow_currency || "")
                        ? formatCurrency(model.intrinsic_value_per_share, model.cash_flow_currency!)
                        : model.intrinsic_value_per_share != null ? "Not reliable" : "Not available"}
                      <div style={{ color: "var(--text-muted)", fontSize: "0.75rem" }}>Estimate</div>
                    </td>
                    <td>{model.assumption_set_count}</td>
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

      <Panel title="Review inputs for a new model">
        <p>Review sourced financial inputs and explicit assumptions in a draft before saving a model. Existing saved versions retain their original basis.</p>
        <div className="button-row">
          <Link prefetch={false} href={`/companies/${companyId}/valuation/draft`} className="primary-button">Create Valuation Model</Link>
          <Link prefetch={false} href={`/companies/${companyId}/fundamentals`} className="secondary-button">Review financial inputs</Link>
        </div>
      </Panel>

      {context ? <Panel title="Market context" collapsible><MarketContextPanel context={context} /></Panel> : (
        <Panel title="Market context unavailable">
          <ErrorState message="Market context could not be loaded." />
          <p>Review market, country and currency before using discount-rate assumptions.</p>
          <div className="button-row"><a className="secondary-button" href={`/companies/${companyId}/valuation`}>Try again</a>
            <Link href={`/companies/${companyId}/setup`}>Review company setup</Link></div>
        </Panel>
      )}
      <Panel title="Industry and benchmark settings" collapsible>
        <p>Optional comparison inputs. Industry benchmarks are priors, not company facts.</p>
        <IndustryMappingSection company={company} />
      </Panel>
      <p><Link prefetch={false} href={`/companies/${companyId}/valuation/peers`}>Manage sourced peer sets</Link></p>
    </>
  );
}
