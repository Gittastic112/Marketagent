import { notFound } from "next/navigation";
import Link from "next/link";

import { confirmCompanySetupIdentity, startCompanySetup, updateCompanySetupStep } from "@/app/actions";
import { PageHeader, Panel } from "@/components/page";
import { SelectField } from "@/components/form-fields";
import type { Company, CompanySetupWorkflow } from "@/lib/api";
import { serverFetchApi } from "@/lib/server-api";

function statusBadge(status: string) {
  const colors: Record<string, string> = {
    reviewed: "var(--success)",
    configured: "var(--success)",
    ready: "var(--success)",
    manual_only: "var(--warning)",
    needs_review: "var(--warning)",
    missing: "var(--warning)",
    blocked: "var(--error)",
    local_only: "var(--text-secondary)",
  };
  const color = colors[status] ?? "var(--text-secondary)";
  return (
    <span className="badge" style={{ backgroundColor: "var(--surface-muted)", border: `1px solid ${color}`, color }}>
      {status.replaceAll("_", " ")}
    </span>
  );
}

async function loadSetup(companyId: number) {
  try {
    return await serverFetchApi<CompanySetupWorkflow>(`/api/company-setup/${companyId}`);
  } catch {
    return null;
  }
}

export default async function CompanySetupPage(props: { params: Promise<{ id: string }> }) {
  const params = await props.params;
  const companyId = Number(params.id);
  if (!Number.isFinite(companyId)) {
    notFound();
  }

  let company: Company;
  try {
    company = await serverFetchApi<Company>(`/companies/${companyId}`);
  } catch {
    notFound();
  }

  const workflow = await loadSetup(companyId);

  return (
    <>
      <PageHeader eyebrow="Company Setup" title={company.name} status={`${company.market ?? "US"} / ${company.primary_exchange ?? company.exchange ?? "-"}`} />

      <div className="button-row" style={{ marginBottom: "1.5rem" }}>
        <Link className="secondary-button" href={`/companies/${company.id}`}>Back to company</Link>
        <Link className="secondary-button" href={`/companies/${company.id}/filings`}>Filings</Link>
        <Link className="secondary-button" href={`/companies/${company.id}/fundamentals`}>Financials</Link>
        <Link className="secondary-button" href={`/companies/${company.id}/valuation`}>Valuation</Link>
      </div>

      {!workflow ? (
        <Panel title="Start Setup">
          <p className="muted" style={{ marginTop: 0 }}>
            Create a setup checklist for identity, source readiness, filings, financial review, industry mapping, and valuation readiness.
          </p>
          <form action={startCompanySetup}>
            <input name="id" type="hidden" value={company.id} />
            <button type="submit">Start setup</button>
          </form>
        </Panel>
      ) : (
        <div style={{ display: "grid", gridTemplateColumns: "minmax(0, 1fr) 360px", gap: "1.5rem", alignItems: "start" }}>
          <div style={{ display: "flex", flexDirection: "column", gap: "1.5rem" }}>
            <Panel title="Workflow Status">
              <div className="table-wrap">
                <table>
                  <tbody>
                    <tr><th>Current step</th><td>{statusBadge(workflow.current_step)}</td></tr>
                    <tr><th>Identity</th><td>{statusBadge(workflow.identity_status)}</td></tr>
                    <tr><th>Sources</th><td>{statusBadge(workflow.source_status)}</td></tr>
                    <tr><th>Filings</th><td>{statusBadge(workflow.filing_status)}</td></tr>
                    <tr><th>Financial extraction</th><td>{statusBadge(workflow.financial_extraction_status)}</td></tr>
                    <tr><th>Industry mapping</th><td>{statusBadge(workflow.industry_mapping_status)}</td></tr>
                    <tr><th>Valuation readiness</th><td>{statusBadge(workflow.valuation_readiness_status)}</td></tr>
                    <tr><th>Security posture</th><td>{statusBadge(workflow.security_review_status)}</td></tr>
                  </tbody>
                </table>
              </div>
              <p className="muted" style={{ marginBottom: 0 }}>{workflow.next_recommended_step}</p>
              {workflow.filing_status !== "reviewed" ? (
                <div className="button-row" style={{ marginTop: "1rem" }}>
                  <Link className="secondary-button" href={`/companies/${company.id}/filings`}>Review filings</Link>
                </div>
              ) : null}
            </Panel>

            <Panel title="Source Readiness">
              <div className="table-wrap">
                <table>
                  <thead>
                    <tr>
                      <th>Provider</th>
                      <th>Capability</th>
                      <th>Market</th>
                      <th>Status</th>
                      <th>Action</th>
                    </tr>
                  </thead>
                  <tbody>
                    {workflow.source_readiness.map((source) => (
                      <tr key={`${source.provider_name}-${source.capability}`}>
                        <td>
                          <strong>{source.provider_name}</strong>
                          <div className="muted" style={{ fontSize: "0.82rem" }}>{source.notes}</div>
                        </td>
                        <td>{source.capability}</td>
                        <td>{source.market}</td>
                        <td>{statusBadge(source.status)}</td>
                        <td className="muted">{source.action_required ?? "No action needed"}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </Panel>
          </div>

          <div style={{ display: "flex", flexDirection: "column", gap: "1.5rem" }}>
            <Panel title="Identity Review">
              <dl style={{ margin: 0, display: "grid", gap: "0.5rem", fontSize: "0.9rem" }}>
                <div><dt className="muted">Ticker</dt><dd style={{ margin: 0 }}>{company.ticker}</dd></div>
                <div><dt className="muted">Local symbol</dt><dd style={{ margin: 0 }}>{company.local_symbol ?? "-"}</dd></div>
                <div><dt className="muted">Exchange</dt><dd style={{ margin: 0 }}>{company.primary_exchange ?? company.exchange ?? "-"}</dd></div>
                <div><dt className="muted">CIK</dt><dd style={{ margin: 0 }}>{company.cik ?? "-"}</dd></div>
                <div><dt className="muted">ISIN</dt><dd style={{ margin: 0 }}>{company.isin ?? "-"}</dd></div>
              </dl>
              <form action={confirmCompanySetupIdentity} style={{ marginTop: "1rem" }}>
                <input name="id" type="hidden" value={company.id} />
                <button type="submit">Confirm identity</button>
              </form>
            </Panel>

            <Panel title="Update Setup">
              <form action={updateCompanySetupStep} className="form-grid">
                <input name="id" type="hidden" value={company.id} />
                <SelectField defaultValue={workflow.current_step} id="current_step" label="Current step" name="current_step">
                  <option value="identity">Identity</option>
                  <option value="source_setup">Source setup</option>
                  <option value="filing_fetch">Filing fetch</option>
                  <option value="financial_extraction">Financial extraction</option>
                  <option value="financial_review">Financial review</option>
                  <option value="industry_mapping">Industry mapping</option>
                  <option value="assumption_review">Assumption review</option>
                  <option value="valuation_run">Valuation run</option>
                </SelectField>
                <SelectField defaultValue={workflow.filing_status} id="filing_status" label="Filings" name="filing_status">
                  <option value="missing">Missing</option>
                  <option value="needs_review">Needs review</option>
                  <option value="reviewed">Reviewed</option>
                </SelectField>
                <SelectField defaultValue={workflow.financial_extraction_status} id="financial_extraction_status" label="Financial extraction" name="financial_extraction_status">
                  <option value="missing">Missing</option>
                  <option value="needs_review">Needs review</option>
                  <option value="reviewed">Reviewed</option>
                </SelectField>
                <SelectField defaultValue={workflow.industry_mapping_status} id="industry_mapping_status" label="Industry mapping" name="industry_mapping_status">
                  <option value="missing">Missing</option>
                  <option value="needs_review">Needs review</option>
                  <option value="reviewed">Reviewed</option>
                </SelectField>
                <SelectField defaultValue={workflow.valuation_readiness_status} id="valuation_readiness_status" label="Valuation readiness" name="valuation_readiness_status">
                  <option value="blocked">Blocked</option>
                  <option value="needs_review">Needs review</option>
                  <option value="ready">Ready</option>
                </SelectField>
                <div className="button-row field-full">
                  <button type="submit">Save setup</button>
                </div>
              </form>
            </Panel>
          </div>
        </div>
      )}
    </>
  );
}
