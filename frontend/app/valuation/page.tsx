import Link from "next/link";
import { DataFreshnessIndicator, PageHeader, Panel, ErrorState, EmptyState, MockDataState, StaleDataBanner } from "@/components/page";
import { serverFetchApiResponse } from "@/lib/server-api";
import type { Company } from "@/lib/api";

export default async function ValuationPage() {
  try {
    const companiesRes = await serverFetchApiResponse<Company[]>("/companies");
    const companies = companiesRes.data || [];
    const isStale = companiesRes.meta?.is_stale;
    const isMock = companiesRes.meta?.is_mock || companiesRes.meta?.source === "mock";

    return (
      <>
        <PageHeader eyebrow="Financial modeling" title="Valuation & DCF" />

        <div style={{ marginBottom: "2rem" }}>
          <Link href="/valuation/quick" className="btn btn-primary" style={{ padding: "0.75rem 1.5rem", fontSize: "1rem", fontWeight: 600 }}>
            ⚡ Start Quick Valuation
          </Link>
          <p style={{ marginTop: "0.5rem", fontSize: "0.9rem", color: "var(--text-secondary)" }}>
            Complete a baseline valuation in under 5 minutes.
          </p>
        </div>

        {isStale && <StaleDataBanner message="Showing cached company data because backend is unreachable." />}
        {isMock && <MockDataState message="Company rows are mock data. Do not use them as live market coverage." />}

        <Panel title="Valuation Models by Company">
          <div style={{ display: "flex", justifyContent: "space-between", gap: "1rem", alignItems: "flex-start", marginBottom: "1rem" }}>
            <p style={{ margin: 0, color: "var(--text-secondary)" }}>
              Select a company below to manage its DCF valuation models, financial metrics, and assumptions.
            </p>
            <DataFreshnessIndicator meta={companiesRes.meta ?? undefined} />
          </div>

          {companies.length === 0 ? (
            <EmptyState label="No companies exist yet." />
          ) : (
            <div className="table-wrap">
              <table>
                <thead>
                  <tr>
                    <th>Ticker</th>
                    <th>Name</th>
                    <th>Market</th>
                    <th>Currency</th>
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
                      <td>{company.market || "-"}</td>
                      <td>{company.currency || "-"}</td>
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
