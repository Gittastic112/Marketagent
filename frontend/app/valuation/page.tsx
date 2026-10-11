import Link from "next/link";
import { DataStateNotices, PageHeader, Panel, ErrorState, EmptyState } from "@/components/page";
import { serverFetchApiResponse } from "@/lib/server-api";
import type { Company } from "@/lib/api";

export default async function ValuationPage() {
  try {
    const companiesRes = await serverFetchApiResponse<Company[]>("/companies");
    const companies = companiesRes.data || [];

    return (
      <>
        <PageHeader eyebrow="Financial modeling" title="Valuation & DCF"
          description="Start with sourced facts, review the assumptions, and explore what drives value."
          actions={<Link prefetch={false} href="/valuation/quick" className="primary-button">Start Quick Valuation</Link>} />

        <DataStateNotices
          metas={[companiesRes.meta]}
          mockMessage="Company rows are mock data. Do not use them as live market coverage."
        />

        <Panel title="Valuation Models by Company">
          <p className="section-intro">Choose a company to review its financial evidence and saved models. These are stored company records, not live quotes.</p>

          {companiesRes.data === null ? <ErrorState message="Companies could not be loaded." errors={companiesRes.errors} /> : companies.length === 0 ? (
            <EmptyState label="No companies exist yet." />
          ) : (
            <div className="table-wrap">
              <table>
                <thead>
                  <tr>
                    <th>Company</th>
                    <th>Listing</th>
                    <th>Sector</th>
                    <th>Market Cap</th>
                    <th>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {companies.map((company) => (
                    <tr key={company.id}>
                      <td>
                        <Link prefetch={false} href={`/companies/${company.id}/valuation`}><strong>{company.ticker}</strong></Link>
                        <span className="cell-secondary">{company.name}</span>
                      </td>
                      <td>{company.market || "-"} · {company.currency || "-"}</td>
                      <td>{company.sector || "-"}</td>
                      <td>{company.market_cap_category || "-"}</td>
                      <td>
                        <div className="action-stack" style={{ flexDirection: "row", gap: "0.5rem" }}>
                          <Link prefetch={false} className="secondary-button" href={`/companies/${company.id}/valuation`}>
                            DCF Models
                          </Link>
                          <Link prefetch={false} className="secondary-button" href={`/companies/${company.id}/fundamentals`}>
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
  } catch {
    return (
      <>
        <PageHeader eyebrow="Financial modeling" title="Valuation & DCF" />
        <ErrorState message="Could not load companies for valuation hub." />
      </>
    );
  }
}
