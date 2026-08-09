import { notFound } from "next/navigation";
import Link from "next/link";
import type { Company, ValuationCompanyContext, ValuationModel } from "@/lib/api";
import { serverFetchApi } from "@/lib/server-api";
import { deleteValuationModel } from "@/app/actions";
import { EmptyState, PageHeader, Panel } from "@/components/page";
import { MarketContextPanel } from "@/components/valuation/market-context-panel";
import { IndustryMappingSection } from "./industry-mapping-section";

export const dynamic = "force-dynamic";

export default async function ValuationPage(props: { params: Promise<{ id: string }> }) {
  const params = await props.params;
  const companyId = parseInt(params.id, 10);
  if (isNaN(companyId)) {
    notFound();
  }

  let company: Company;
  let context: ValuationCompanyContext | null = null;
  try {
    company = await serverFetchApi<Company>(`/companies/${companyId}`);
    try {
      context = await serverFetchApi<ValuationCompanyContext>(`/api/valuation/context/company/${companyId}`);
    } catch {
      // Ignored if missing
    }
  } catch {
    notFound();
  }

  const models = await serverFetchApi<ValuationModel[]>(`/companies/${companyId}/valuation-models`);

  return (
    <>
      <div className="valuation-page-titlebar">
        <PageHeader eyebrow={company.ticker} title="Valuation Models" status={`${models.length} model${models.length !== 1 ? "s" : ""}`} />
        <Link href={`/companies/${company.id}`} className="secondary-button">&larr; Back to Company</Link>
      </div>

      <IndustryMappingSection company={company} />

      {context && <MarketContextPanel context={context} />}

      <Panel title="Create New Model">
        <div style={{ display: "flex", flexDirection: "column", gap: "1rem" }}>
          <p style={{ color: "var(--text-secondary)", margin: 0 }}>
            Start with source-backed defaults, confirm them once, and edit only the assumptions you want to change.
          </p>
          <div>
            <Link href={`/companies/${companyId}/valuation/draft`} className="primary-button" style={{ display: "inline-block", textDecoration: "none", padding: "0.75rem 1.5rem", background: "var(--accent)", color: "white", borderRadius: "4px", fontWeight: 600 }}>
              Create Valuation Model
            </Link>
          </div>
        </div>
      </Panel>

      <Panel title="Valuation Models">
        {models.length === 0 ? (
          <EmptyState label="No valuation models created yet." />
        ) : (
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>Name</th>
                  <th>Description</th>
                  <th>Scenarios</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {models.map((model) => (
                  <tr key={model.id}>
                    <td>
                      <Link href={`/companies/${companyId}/valuation/${model.id}`} style={{ color: "var(--accent)", fontWeight: 600 }}>
                        {model.name}
                      </Link>
                    </td>
                    <td>{model.description ?? "—"}</td>
                    <td>{model.assumption_sets?.length ?? 0} sets</td>
                    <td>
                      <form action={async (data) => {
                        "use server";
                        await deleteValuationModel(data, companyId.toString());
                      }}>
                        <input type="hidden" name="id" value={model.id} />
                        <button type="submit" className="secondary-button" style={{ color: "var(--error)", fontSize: "0.8rem" }}>
                          Delete
                        </button>
                      </form>
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
}
