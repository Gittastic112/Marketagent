import { deleteCompanyWithState, updateCompany, createExposureTag, deleteExposureTag, addCompanyExposureTag, removeCompanyExposureTag } from "@/app/actions";
import { CompanySetupWizard } from "@/components/company-setup-wizard";
import { DeleteRecordForm } from "@/components/delete-record-form";
import { CheckboxField, SelectField, TextField, TextAreaField } from "@/components/form-fields";
import { EmptyState, ErrorState, MockDataState, PageHeader, Panel, StaleDataBanner } from "@/components/page";
import { serverFetchApiResponse } from "@/lib/server-api";
import { summarizeApiMetas } from "@/lib/data-state-meta";
import type { Company, ExposureTag } from "@/lib/api";
import Link from "next/link";

export default async function CompaniesPage() {
  try {
    const [companiesRes, exposureTagsRes] = await Promise.all([
      serverFetchApiResponse<Company[]>("/companies"),
      serverFetchApiResponse<ExposureTag[]>("/exposure-tags")
    ]);

    const companies = companiesRes.data || [];
    const exposureTags = exposureTagsRes.data || [];
    const dataState = summarizeApiMetas([companiesRes.meta, exposureTagsRes.meta]);

    return (
      <>
        <PageHeader eyebrow="Watchlist" title="Companies" status={`${companies.length} tracked`} />

        {dataState.someStale && <StaleDataBanner message="Showing cached data because backend is unreachable." />}
        {dataState.hasMock && <MockDataState message="Company or exposure tag data is mocked. Do not treat it as live watchlist coverage." />}

        <Panel title="Add Company">
          <CompanySetupWizard />
        </Panel>
        <Panel title="Add Exposure Tag">
          <form action={createExposureTag} className="form-grid">
            <TextField id="tag_name" label="Tag Name" name="name" placeholder="AI Infrastructure" required />
            <TextAreaField className="field field-full" id="tag_desc" label="Description" name="description" />
            <div className="button-row">
              <button type="submit">Add Tag</button>
            </div>
          </form>
          {exposureTags.length > 0 && (
            <div className="mt-4">
              <h4 className="text-sm font-medium mb-2">Existing Tags</h4>
              <div className="flex flex-wrap gap-2">
                {exposureTags.map(tag => (
                  <span key={tag.id} className="inline-flex items-center gap-1 bg-gray-100 px-2 py-1 rounded text-xs">
                    <span title={tag.description || ''}>{tag.name}</span>
                    <form action={deleteExposureTag} className="inline" style={{display: 'inline'}}>
                      <input type="hidden" name="id" value={tag.id} />
                      <button type="submit" className="text-red-500 hover:text-red-700 ml-1" title="Delete tag">×</button>
                    </form>
                  </span>
                ))}
              </div>
            </div>
          )}
        </Panel>
        <Panel title="Company Watchlist">
          {companies.length === 0 ? (
            <EmptyState label="No companies yet." />
          ) : (
            <div className="table-wrap">
              <table>
                <thead>
                  <tr>
                    <th>Market</th>
                    <th>Symbol</th>
                    <th>Name</th>
                    <th>Sector</th>
                    <th>Country</th>
                    <th>Currency</th>
                    <th>Asset</th>
                    <th>Exchange</th>
                    <th>Aliases</th>
                    <th>Tags</th>
                    <th>Status</th>
                    <th>Action</th>
                  </tr>
                </thead>
                <tbody>
                  {companies.map((company) => (
                    <tr key={company.id}>
                      <td>{company.market ?? "-"}</td>
                      <td>
                        <Link href={`/companies/${company.id}`}>{company.ticker}</Link>
                        {company.local_symbol && company.local_symbol !== company.ticker ? <div className="muted">{company.local_symbol}</div> : null}
                      </td>
                      <td>{company.name}</td>
                      <td>{company.sector ?? "-"}</td>
                      <td>{company.country ?? "-"}</td>
                      <td>{company.currency ?? "-"}</td>
                      <td>{company.asset_type ?? "-"}</td>
                      <td>{company.primary_exchange ?? company.exchange ?? "-"}</td>
                      <td>{company.aliases_json?.join(", ") || "-"}</td>
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
                        <div className="action-stack">
                          <Link className="secondary-button" href={`/companies/${company.id}/setup`}>
                            Setup
                          </Link>
                          <details className="edit-panel">
                            <summary>Edit</summary>
                            <form action={updateCompany} className="inline-form">
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
                            </form>
                          </details>
                          <details className="edit-panel">
                            <summary>Tags</summary>
                            <div className="section-block">
                              <ul className="text-sm mb-2">
                                {company.exposure_tags?.map(tag => (
                                  <li key={tag.id} className="mb-1">
                                    {tag.name}
                                    <form action={removeCompanyExposureTag} className="inline-form" style={{display: 'inline', marginLeft: '8px'}}>
                                      <input type="hidden" name="company_id" value={company.id} />
                                      <input type="hidden" name="tag_id" value={tag.id} />
                                      <button type="submit" className="text-red-500 text-xs" title="Remove tag">✕</button>
                                    </form>
                                  </li>
                                ))}
                              </ul>
                              <form action={addCompanyExposureTag} className="inline-form mt-2">
                                <input type="hidden" name="company_id" value={company.id} />
                                <SelectField id={`add-tag-${company.id}`} label="" name="tag_id" required>
                                  <option value="">Add tag...</option>
                                  {exposureTags.filter(t => !company.exposure_tags?.some(ct => ct.id === t.id)).map((t) => (
                                    <option key={t.id} value={t.id}>{t.name}</option>
                                  ))}
                                </SelectField>
                                <button type="submit" className="secondary-button text-sm mt-1">Add</button>
                              </form>
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
