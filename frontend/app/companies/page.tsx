import { createCompany, deleteCompany, updateCompany } from "@/app/actions";
import { EmptyState, ErrorState, PageHeader, Panel } from "@/components/page";
import { fetchApi } from "@/lib/api";
import type { Company } from "@/lib/api";

export default async function CompaniesPage() {
  try {
    const companies = await fetchApi<Company[]>("/companies");

    return (
      <>
        <PageHeader eyebrow="Watchlist" title="Companies" status={`${companies.length} tracked`} />
        <Panel title="Add Company">
          <form action={createCompany} className="form-grid">
            <div className="field">
              <label htmlFor="ticker">Ticker</label>
              <input id="ticker" name="ticker" required />
            </div>
            <div className="field field-wide">
              <label htmlFor="name">Name</label>
              <input id="name" name="name" required />
            </div>
            <div className="field">
              <label htmlFor="exchange">Exchange</label>
              <input id="exchange" name="exchange" placeholder="NASDAQ" />
            </div>
            <div className="field">
              <label htmlFor="sector">Sector</label>
              <input id="sector" name="sector" />
            </div>
            <div className="field">
              <label htmlFor="industry">Industry</label>
              <input id="industry" name="industry" />
            </div>
            <div className="field">
              <label htmlFor="cik">CIK</label>
              <input id="cik" name="cik" />
            </div>
            <div className="field">
              <label>Status</label>
              <div className="checkbox-row">
                <input defaultChecked id="active" name="active" type="checkbox" />
                <span>Active</span>
              </div>
            </div>
            <div className="button-row">
              <button type="submit">Add company</button>
            </div>
          </form>
        </Panel>
        <Panel title="Company Watchlist">
          {companies.length === 0 ? (
            <EmptyState label="No companies yet." />
          ) : (
            <div className="table-wrap">
              <table>
                <thead>
                  <tr>
                    <th>Ticker</th>
                    <th>Name</th>
                    <th>Sector</th>
                    <th>Exchange</th>
                    <th>Status</th>
                    <th>Action</th>
                  </tr>
                </thead>
                <tbody>
                  {companies.map((company) => (
                    <tr key={company.id}>
                      <td>{company.ticker}</td>
                      <td>{company.name}</td>
                      <td>{company.sector ?? "-"}</td>
                      <td>{company.exchange ?? "-"}</td>
                      <td>
                        <span className="badge">{company.active ? "active" : "inactive"}</span>
                      </td>
                      <td>
                        <div className="action-stack">
                          <details className="edit-panel">
                            <summary>Edit</summary>
                            <form action={updateCompany} className="inline-form">
                              <input name="id" type="hidden" value={company.id} />
                              <div className="field">
                                <label htmlFor={`ticker-${company.id}`}>Ticker</label>
                                <input defaultValue={company.ticker} id={`ticker-${company.id}`} name="ticker" required />
                              </div>
                              <div className="field">
                                <label htmlFor={`name-${company.id}`}>Name</label>
                                <input defaultValue={company.name} id={`name-${company.id}`} name="name" required />
                              </div>
                              <div className="field">
                                <label htmlFor={`sector-${company.id}`}>Sector</label>
                                <input defaultValue={company.sector ?? ""} id={`sector-${company.id}`} name="sector" />
                              </div>
                              <div className="field">
                                <label htmlFor={`exchange-${company.id}`}>Exchange</label>
                                <input defaultValue={company.exchange ?? ""} id={`exchange-${company.id}`} name="exchange" />
                              </div>
                              <div className="field">
                                <label htmlFor={`industry-${company.id}`}>Industry</label>
                                <input defaultValue={company.industry ?? ""} id={`industry-${company.id}`} name="industry" />
                              </div>
                              <div className="field">
                                <label htmlFor={`cik-${company.id}`}>CIK</label>
                                <input defaultValue={company.cik ?? ""} id={`cik-${company.id}`} name="cik" />
                              </div>
                              <div className="field">
                                <label>Status</label>
                                <div className="checkbox-row">
                                  <input defaultChecked={company.active} id={`active-${company.id}`} name="active" type="checkbox" />
                                  <span>Active</span>
                                </div>
                              </div>
                              <div className="button-row">
                                <button className="secondary-button" type="submit">Save</button>
                              </div>
                            </form>
                          </details>
                          <form action={deleteCompany} className="row-action">
                            <input name="id" type="hidden" value={company.id} />
                            <button className="danger-button" type="submit">Delete</button>
                          </form>
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
