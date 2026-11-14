import Link from "next/link";
import type { ApiResponse } from "@/lib/api/contract";
import type { ValuationModelSummary } from "@/lib/api/valuation";
import { DataStateNotices, ErrorState, Panel } from "@/components/page";
import { formatCurrency, formatDataLabel } from "@/lib/formatting";

export function CompanyValuationSummary({ companyId, response }: {
  companyId: number;
  response: ApiResponse<ValuationModelSummary[]>;
}) {
  const failed = response.meta.status !== "success" || response.errors.length > 0 || !Array.isArray(response.data);
  const models = failed ? [] : [...(response.data || [])].sort((a, b) => b.updated_at.localeCompare(a.updated_at));
  const model = models[0];
  const estimateAvailable = model?.readiness === "calculated" && model.intrinsic_value_per_share != null
    && Number.isFinite(model.intrinsic_value_per_share) && /^[A-Z]{3}$/.test(model.cash_flow_currency || "");
  return <Panel title="Valuation and next steps">
    <div className="company-valuation-summary">
      {failed ? <ErrorState message="Saved models could not be loaded." errors={response.errors} /> : <>
        <DataStateNotices metas={[response.meta]} />
        {model ? <>
          <p className="muted">Most recently updated model</p>
          <Link prefetch={false} href={`/companies/${companyId}/valuation/${model.id}`}><strong>{model.name}</strong></Link>
          <p><span className="badge">{formatDataLabel(model.readiness)}</span></p>
          <p className="company-valuation-estimate">{estimateAvailable ? formatCurrency(model.intrinsic_value_per_share, model.cash_flow_currency!) : "Estimate unavailable"}</p>
          <p className="muted">{model.latest_run_at ? `Calculated ${model.latest_run_at.slice(0, 10)}` : "No saved calculation"}. {model.readiness_detail}</p>
          <p className="muted">Saved estimate with its original assumptions. Open the model to inspect dates, sources and limitations.</p>
        </> : <><p><strong>No saved valuation model.</strong></p><p className="muted">Review the company's financial basis and assumptions before calculating an estimate.</p></>}
      </>}
      <div className="button-row">
        <Link prefetch={false} className="primary-button" href={`/companies/${companyId}/valuation`}>{model ? "Open valuations" : "Review valuation setup"}</Link>
        <Link prefetch={false} className="secondary-button" href={`/companies/${companyId}/fundamentals`}>Review financial inputs</Link>
      </div>
      <Link prefetch={false} href={`/companies/${companyId}/thesis`}>Review thesis and decisions</Link>
    </div>
  </Panel>;
}
