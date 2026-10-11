import Link from "next/link";
import { redirect } from "next/navigation";

import { promoteValuationSetupDraft } from "@/app/actions";
import { AutofillDraftReview } from "@/components/valuation/autofill-draft-review";
import {
  type AutofillAssumptionDraft,
  type Company,
  type ValuationSetupDraft,
} from "@/lib/api";
import { serverFetchApi, serverPostApi } from "@/lib/server-api";

export default async function DraftValuationPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;
  const companyId = Number.parseInt(id, 10);
  const company = await serverFetchApi<Company>(`/companies/${companyId}`);

  let persistedDraft: ValuationSetupDraft;
  try {
    const response = await serverPostApi<ValuationSetupDraft>(
      `/companies/${companyId}/valuation-drafts`,
      {},
    );
    persistedDraft = ((response as { data?: ValuationSetupDraft }).data || response) as ValuationSetupDraft;
  } catch (error) {
    const message = error instanceof Error ? error.message : "Failed to generate draft assumptions.";
    return (
      <div className="page-container">
        <header className="page-header">
          <h1>Draft New Valuation Model: {company.name}</h1>
        </header>
        <section className="panel" style={{ padding: "20px" }}>
          <h2>Draft unavailable</h2>
          <p style={{ color: "var(--danger)" }}>{message}</p>
          <Link href={`/companies/${companyId}/valuation`} className="secondary-button">
            Back to Valuation Models
          </Link>
        </section>
      </div>
    );
  }

  async function createModelAction(formData: FormData) {
    "use server";
    const modelId = await promoteValuationSetupDraft(
      formData,
      persistedDraft.id,
      companyId.toString(),
    );
    redirect(`/companies/${companyId}/valuation/${modelId}`);
  }

  const draft: AutofillAssumptionDraft = {
    assumptions: persistedDraft.assumptions_json,
    provenance: persistedDraft.provenance_json,
    source_metadata: persistedDraft.source_metadata_json,
    warnings: persistedDraft.warnings_json,
  } as AutofillAssumptionDraft;

  return (
    <div className="page-container">
      <header className="page-header">
        <div>
          <h1>Draft New Valuation Model: {company.name}</h1>
          <p className="subtitle">Review source-backed assumptions and resolve placeholders before creating the model.</p>
        </div>
        <Link href={`/companies/${companyId}/valuation`} className="secondary-button">
          Cancel
        </Link>
      </header>
      <AutofillDraftReview
        key={persistedDraft.id}
        company={company}
        draft={draft}
        draftId={persistedDraft.id}
        initialReviewedFields={persistedDraft.reviewed_fields_json}
        initialEditedFields={persistedDraft.edited_fields_json}
        initialUpdatedAt={persistedDraft.updated_at}
        action={createModelAction}
      />
    </div>
  );
}
