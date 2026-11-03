import Link from "next/link";
import { ErrorState, Panel } from "@/components/page";
import type { CompanyResearchProfile } from "@/lib/api/company-research";
import { serverFetchApiResponse } from "@/lib/server-api";

export async function CompanyResearchCards({ companyIds }: { companyIds: number[] }) {
  const ids = [...new Set(companyIds)].filter(id => id > 0).slice(0, 50);
  if (!ids.length) return null;
  const query = new URLSearchParams(ids.map(id => ["company_id", String(id)]));
  const response = await serverFetchApiResponse<CompanyResearchProfile[]>(`/company-research/profiles?${query}`);
  return <Panel title="Company research" actions={<span className="badge badge-outline">Business · evidence · valuation</span>}>
    {!response.data ? <ErrorState message="Company information is unavailable." errors={response.errors} /> : <div className="company-research-grid">{response.data.map(company => <article className="company-research-card" key={company.id}>
      <div className="section-intro"><span className="badge">{company.ticker}</span><span className="muted">{company.primary_exchange || company.exchange || "Exchange unknown"} · {company.currency || "Currency unknown"}</span></div>
      <h3><Link prefetch={false} href={`/companies/${company.id}`}>{company.name}</Link></h3>
      <p className="muted">{[company.sector, company.industry, company.country].filter(Boolean).join(" · ") || "Industry and country not recorded"}</p>
      {company.excerpt ? <><span className="badge badge-outline">Stored business excerpt</span><p className="company-business-excerpt">{company.excerpt}…</p><p className="muted">{company.document_title} · {company.published_at ? company.published_at.slice(0, 10) : "Source date unknown"}. Parser-selected excerpt, not independently reviewed.</p><Link prefetch={false} href={company.source_href!}>Read full business section →</Link></>
        : <p className="basis-note">Business description not available yet. <Link prefetch={false} href={`/companies/${company.id}/filings`}>Import and parse an annual filing</Link> to add source-backed context.</p>}
      <nav className="company-research-links" aria-label={`${company.ticker} research links`}>
        <Link prefetch={false} href={`/companies/${company.id}`}>Overview</Link><Link prefetch={false} href={`/companies/${company.id}/valuation/peers`}>Comps</Link><Link prefetch={false} href={`/companies/${company.id}/valuation/draft`}>Valuation inputs</Link><Link prefetch={false} href={`/companies/${company.id}/filings`}>Filings</Link>
      </nav>
    </article>)}</div>}
    <p className="muted">Stored identity and filing context, not a real-time company-information feed.</p>
  </Panel>;
}
