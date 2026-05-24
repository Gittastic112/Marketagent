import { EmptyState, ErrorState, PageHeader, Panel } from "@/components/page";
import { fetchApi } from "@/lib/api";
import type { Company } from "@/lib/api";

export default async function CompaniesPage() {
  try {
    const companies = await fetchApi<Company[]>("/companies");

    return (
      <>
        <PageHeader eyebrow="Watchlist" title="Companies" status={`${companies.length} tracked`} />
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
