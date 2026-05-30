import { notFound } from "next/navigation";
import Link from "next/link";
import { fetchApi, Company, listValuationModels } from "@/lib/api";
import { deleteValuationModel } from "@/app/actions";
import { TextField, TextAreaField } from "@/components/form-fields";
import { EmptyState, PageHeader, Panel } from "@/components/page";
import { DeleteRecordForm } from "@/components/delete-record-form";

export const dynamic = "force-dynamic";

export default async function ValuationPage(props: { params: Promise<{ id: string }> }) {
  const params = await props.params;
  const companyId = parseInt(params.id, 10);
  if (isNaN(companyId)) {
    notFound();
  }

  let company: Company;
  try {
    company = await fetchApi<Company>(`/companies/${companyId}`);
  } catch {
    notFound();
  }

  const models = await listValuationModels(companyId);

  return (
    <>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-end" }}>
        <PageHeader eyebrow={company.ticker} title="Valuation Models" status={`${models.length} model${models.length !== 1 ? "s" : ""}`} />
        <div style={{ marginBottom: "2rem" }}>
          <Link href={`/companies/${company.id}`} className="secondary-button">&larr; Back to Company</Link>
        </div>
      </div>

      <Panel title="Create New Model">
        <form action={async (data) => {
          "use server";
          const { createValuationModel } = await import("@/app/actions");
          await createValuationModel(data, companyId.toString());
        }} className="form-grid">
          <input type="hidden" name="company_id" value={companyId} />
          <TextField id="model-name" label="Model Name" name="name" placeholder="e.g. Base DCF 2026" required />
          <TextField id="model-desc" label="Description" name="description" placeholder="Optional description" />
          <div className="button-row">
            <button type="submit">Create Model</button>
          </div>
        </form>
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
