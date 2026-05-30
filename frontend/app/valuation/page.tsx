import Link from "next/link";
import { PageHeader, Panel, ErrorState, EmptyState } from "@/components/page";
import { fetchApi } from "@/lib/api";
import type { Company } from "@/lib/api";

export default async function ValuationPage() {
  try {
    const companies = await fetchApi<Company[]>("/companies");

    return (
      <>
        <PageHeader eyebrow="Financial modeling" title="Valuation & DCF" />
        
        <Panel title="Valuation Models by Company">
          <p style={{ marginBottom: "1rem", color: "var(--text-secondary)" }}>
            Select a company below to manage its DCF valuation models, financial metrics, and assumptions.
          </p>

          {companies.length === 0 ? (
            <EmptyState label="No companies exist yet." />
          ) : (
            <div className="table-wrap">
              <table>
                <thead>
                  <tr>
                    <th>Ticker</th>
                    <th>Name</th>
                    <th>Sector</th>
                    <th>Market Cap</th>
                    <th>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {companies.map((company) => (
                    <tr key={company.id}>
                      <td>
                        <strong>{company.ticker}</strong>
                      </td>
                      <td>{company.name}</td>
                      <td>{company.sector || "-"}</td>
                      <td>{company.market_cap_category || "-"}</td>
                      <td>
                        <div className="action-stack" style={{ flexDirection: "row", gap: "0.5rem" }}>
                          <Link className="btn btn-primary" href={`/companies/${company.id}/valuation`} style={{ padding: "0.25rem 0.75rem", fontSize: "0.875rem" }}>
                            DCF Models
                          </Link>
                          <Link className="secondary-button" href={`/companies/${company.id}/fundamentals`} style={{ padding: "0.25rem 0.75rem", fontSize: "0.875rem" }}>
                            Fundamentals
                          </Link>
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
  } catch (error) {
    return (
      <>
        <PageHeader eyebrow="Financial modeling" title="Valuation & DCF" />
        <ErrorState message="Could not load companies for valuation hub." />
      </>
    );
  }
}
