import { RetainedActionForm } from "@/components/retained-action-form";
import { deleteCompanyWithState, updateCompany, createExposureTag, deleteExposureTag, addCompanyExposureTag, removeCompanyExposureTag } from "@/app/actions";
import { CompanySetupWizard } from "@/components/company-setup-wizard";
import { DeleteRecordForm } from "@/components/delete-record-form";
import { CheckboxField, SelectField, TextField, TextAreaField } from "@/components/form-fields";
import { DataStateNotices, EmptyState, ErrorState, PageHeader, Panel } from "@/components/page";
import { serverFetchApiResponse } from "@/lib/server-api";
import type { Company, ExposureTag } from "@/lib/api";
import Link from "next/link";

export default async function CompaniesPage({ searchParams }: { searchParams: Promise<{ edit?: string; create?: string; q?: string; market?: string }> }) {
  const query = await searchParams;
  try {
    const [companiesRes, exposureTagsRes] = await Promise.all([
      serverFetchApiResponse<Company[]>("/companies"),
      serverFetchApiResponse<ExposureTag[]>("/exposure-tags")
    ]);

    const allCompanies = companiesRes.data || [];
    const search = (query.q || "").toLowerCase().trim();
    const companies = allCompanies.filter(company => (!query.market || company.market === query.market)
      && (!search || `${company.name} ${company.ticker}`.toLowerCase().includes(search)));
    const exposureTags = exposureTagsRes.data || [];

    return (
      <>
        <PageHeader eyebrow="Research universe" title="Companies" status={`${allCompanies.length} tracked`}
          description="Find a company, inspect its source evidence, and build a valuation."
          actions={<Link prefetch={false} href="/companies?create=1" className="primary-button">Add company</Link>} />

        <DataStateNotices
          metas={[companiesRes.meta, exposureTagsRes.meta]}
          mockMessage="Company or exposure tag data is mocked. Do not treat it as live watchlist coverage."
        />

        {query.create === "1" && <Panel title="Add Company" actions={<Link prefetch={false} href="/companies">Close</Link>}><CompanySetupWizard /></Panel>}
        <form method="get" className="watchlist-filters">
          <TextField id="company-search" name="q" label="Find a company" defaultValue={query.q || ""} placeholder="Name or ticker" />
          <SelectField id="company-market-filter" name="market" label="Market" defaultValue={query.market || ""}>
            <option value="">All markets</option><option value="US">United States</option><option value="IN">India</option>
          </SelectField>
          <button type="submit" className="secondary-button">Filter</button>
          {(query.q || query.market) && <Link prefetch={false} href="/companies">Clear filters</Link>}
        </form>
        <Panel title="Company Watchlist">
          {companiesRes.data === null ? <ErrorState message="The company list could not be loaded." errors={companiesRes.errors} /> : companies.length === 0 ? (
            <EmptyState label={allCompanies.length ? "No companies match these filters." : "No companies yet. Add a company to begin."} />
          ) : (
            <div className="table-wrap">
              <table className="watchlist-table">
                <thead>
                  <tr>
                    <th>Company</th>
                    <th>Listing</th>
                    <th>Sector</th>
                    <th>Tags</th>
                    <th>Status</th>
                    <th>Action</th>
                  </tr>
                </thead>
                <tbody>
                  {companies.map((company) => (
                    <tr key={company.id} id={`company-${company.id}`}>
                      <td>
                        <Link prefetch={false} href={`/companies/${company.id}`}><strong>{company.ticker}</strong></Link>
                        <span className="cell-secondary">{company.name}</span>
                        {company.local_symbol && company.local_symbol !== company.ticker ? <div className="muted">{company.local_symbol}</div> : null}
                      </td>
                      <td>{company.market ?? "-"} · {company.currency ?? "-"}<span className="cell-secondary">{company.primary_exchange ?? company.exchange ?? "-"}</span></td>
                      <td>{company.sector ?? "-"}</td>
                      <td>
                        <div className="flex flex-wrap gap-1 max-w-[150px]">
                          {company.exposure_tags?.map(tag => (
                            <span key={tag.id} className="bg-gray-100 text-xs px-1 rounded truncate" title={tag.name}>{tag.name}</span>
                          )) || "-"}
                        </div>
                      </td>
                      <td>
                        <span className="badge">{company.active ? "active" : "inactive"}</span>
                      </td>
                      <td>
                        <div className="watchlist-actions">
                          <Link prefetch={false} className="secondary-button" href={`/companies/${company.id}/setup`}>
                            Setup
                          </Link>
                          {query.edit !== String(company.id) ? <Link prefetch={false} className="secondary-button" href={`/companies?edit=${company.id}#company-${company.id}`}>Edit</Link> : <details className="edit-panel" open>
                            <summary>Edit</summary>
                            <RetainedActionForm label="Update company" action={updateCompany} className="inline-form">
                              <input name="id" type="hidden" value={company.id} />
                              <SelectField defaultValue={company.market ?? "US"} id={`market-${company.id}`} label="Market" name="market">
                                <option value="US">United States</option>
                                <option value="IN">India</option>
                              </SelectField>
                              <TextField defaultValue={company.primary_exchange ?? company.exchange ?? ""} id={`primary-exchange-${company.id}`} label="Primary Exchange" name="primary_exchange" />
                              <TextField defaultValue={company.local_symbol ?? company.ticker} id={`local-symbol-${company.id}`} label="Local Symbol" name="local_symbol" />
                              <TextField defaultValue={company.ticker} id={`ticker-${company.id}`} label="Ticker" name="ticker" required />
                              <TextField defaultValue={company.name} id={`name-${company.id}`} label="Name" name="name" required />
                              <TextField defaultValue={company.sector ?? ""} id={`sector-${company.id}`} label="Sector" name="sector" />
                              <TextField defaultValue={company.exchange ?? ""} id={`exchange-${company.id}`} label="Exchange" name="exchange" />
                              <TextField defaultValue={company.industry ?? ""} id={`industry-${company.id}`} label="Industry" name="industry" />
                              <TextField defaultValue={company.country ?? ""} id={`country-${company.id}`} label="Country" name="country" />
                              <TextField defaultValue={company.region ?? ""} id={`region-${company.id}`} label="Region" name="region" />
                              <TextField defaultValue={company.currency ?? ""} id={`currency-${company.id}`} label="Currency" name="currency" />
                              <SelectField defaultValue={company.asset_type ?? ""} id={`asset-type-${company.id}`} label="Asset Type" name="asset_type">
                                <option value="">Select type</option>
                                <option value="equity">equity</option>
                                <option value="etf">etf</option>
                                <option value="fund">fund</option>
                                <option value="cash">cash</option>
                                <option value="crypto">crypto</option>
                                <option value="other">other</option>
                              </SelectField>
                              <SelectField defaultValue={company.security_type ?? ""} id={`security-type-${company.id}`} label="Security Type" name="security_type">
                                <option value="">Select type</option>
                                <option value="common_stock">common_stock</option>
                                <option value="adr">adr</option>
                                <option value="etf">etf</option>
                                <option value="mutual_fund">mutual_fund</option>
                                <option value="preferred_stock">preferred_stock</option>
                                <option value="other">other</option>
                              </SelectField>
                              <SelectField defaultValue={company.market_cap_category ?? ""} id={`market-cap-${company.id}`} label="Market Cap" name="market_cap_category">
                                <option value="">Select cap</option>
                                <option value="mega_cap">mega_cap</option>
                                <option value="large_cap">large_cap</option>
                                <option value="mid_cap">mid_cap</option>
                                <option value="small_cap">small_cap</option>
                                <option value="micro_cap">micro_cap</option>
                                <option value="unknown">unknown</option>
                              </SelectField>
                              <TextField defaultValue={company.cik ?? ""} id={`cik-${company.id}`} label="CIK" name="cik" />
                              <TextField defaultValue={company.isin ?? ""} id={`isin-${company.id}`} label="ISIN" name="isin" />
                              <TextField defaultValue={company.regulatory_id ?? ""} id={`regulatory-id-${company.id}`} label="Regulatory ID" name="regulatory_id" />
                              <TextField defaultValue={company.regulatory_id_type ?? ""} id={`regulatory-id-type-${company.id}`} label="Regulatory ID Type" name="regulatory_id_type" />
                              <TextField defaultValue={company.aliases_json?.join(", ") ?? ""} id={`aliases-${company.id}`} label="Aliases" name="aliases" />
                              <TextField defaultValue={company.etf_provider ?? ""} id={`etf-provider-${company.id}`} label="ETF Provider" name="etf_provider" />
                              <CheckboxField checkboxLabel="ETF" defaultChecked={company.is_etf} id={`is-etf-${company.id}`} label="ETF" name="is_etf" />
                              <CheckboxField checkboxLabel="Active" defaultChecked={company.active} id={`active-${company.id}`} label="Status" name="active" />
                              <div className="button-row">
                                <button className="secondary-button" type="submit">Save</button>
                              </div>
                            </RetainedActionForm>
                          </details>}
                          <details className="edit-panel">
                            <summary>Tags</summary>
                            <div className="section-block">
                              <ul className="text-sm mb-2">
                                {company.exposure_tags?.map(tag => (
                                  <li key={tag.id} className="mb-1">
                                    {tag.name}
                                    <RetainedActionForm label="Remove company exposure tag" action={removeCompanyExposureTag} className="inline-form" style={{display: 'inline', marginLeft: '8px'}}>
                                      <input type="hidden" name="company_id" value={company.id} />
                                      <input type="hidden" name="tag_id" value={tag.id} />
                                      <button type="submit" className="text-red-500 text-xs" title="Remove tag">✕</button>
                                    </RetainedActionForm>
                                  </li>
                                ))}
                              </ul>
                              <RetainedActionForm label="Add company exposure tag" action={addCompanyExposureTag} className="inline-form mt-2">
                                <input type="hidden" name="company_id" value={company.id} />
                                <SelectField id={`add-tag-${company.id}`} label="Exposure tag" name="tag_id" required>
                                  <option value="">Add tag...</option>
                                  {exposureTags.filter(t => !company.exposure_tags?.some(ct => ct.id === t.id)).map((t) => (
                                    <option key={t.id} value={t.id}>{t.name}</option>
                                  ))}
                                </SelectField>
                                <button type="submit" className="secondary-button text-sm mt-1">Add</button>
                              </RetainedActionForm>
                            </div>
                          </details>
                          <DeleteRecordForm action={deleteCompanyWithState} recordId={company.id} />
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </Panel>
        <details className="disclosure"><summary>Manage exposure tags</summary>
        <Panel title="Add Exposure Tag">
          <RetainedActionForm label="Create exposure tag" resetOnSuccess action={createExposureTag} className="form-grid">
            <TextField id="tag_name" label="Tag Name" name="name" placeholder="AI Infrastructure" required />
            <TextAreaField className="field field-full" id="tag_desc" label="Description" name="description" />
            <div className="button-row">
              <button type="submit">Add Tag</button>
            </div>
          </RetainedActionForm>
          {exposureTags.length > 0 && (
            <div className="mt-4">
              <h4 className="text-sm font-medium mb-2">Existing Tags</h4>
              <div className="flex flex-wrap gap-2">
                {exposureTags.map(tag => (
                  <span key={tag.id} className="inline-flex items-center gap-1 bg-gray-100 px-2 py-1 rounded text-xs">
                    <span title={tag.description || ''}>{tag.name}</span>
                    <RetainedActionForm label="Delete exposure tag" action={deleteExposureTag} className="inline" style={{display: 'inline'}}>
                      <input type="hidden" name="id" value={tag.id} />
                      <button type="submit" className="text-red-500 hover:text-red-700 ml-1" title="Delete tag">×</button>
                    </RetainedActionForm>
                  </span>
                ))}
              </div>
            </div>
          )}
        </Panel>
        </details>
      </>
    );
  } catch {
    return (
      <>
        <PageHeader eyebrow="Watchlist" title="Companies" />
        <ErrorState message="Could not load companies from the backend API." />
      </>
    );
  }
}
