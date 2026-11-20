import Link from "next/link";
import { notFound } from "next/navigation";

import { createValuationSetupDraft } from "@/app/actions";
import { RetainedActionForm } from "@/components/retained-action-form";
import { AutofillDraftReview } from "@/components/valuation/autofill-draft-review";
import {
  type AutofillAssumptionDraft,
  type Company,
  type ValuationSetupDraft,
} from "@/lib/api";
import { serverFetchApi } from "@/lib/server-api";

export default async function DraftValuationPage({
  params,
  searchParams,
}: {
  params: Promise<{ id: string }>;
  searchParams: Promise<{ model_type?: string; valuation_date?: string; draft?: string }>;
}) {
  const { id } = await params;
  const query = await searchParams;
  const requestedModelType = query.model_type;
  const modelType = ["fcff_dcf", "financial_services", "distressed"].includes(requestedModelType || "") ? requestedModelType! : "fcff_dcf";
  const companyId = Number(id);
  if (!/^[1-9]\d*$/.test(id) || !Number.isSafeInteger(companyId)) notFound();
  const company = await serverFetchApi<Company>(`/companies/${companyId}`);

  let persistedDraft: ValuationSetupDraft | null;
  try {
    persistedDraft = await serverFetchApi<ValuationSetupDraft | null>(
      query.draft && /^[1-9]\d*$/.test(query.draft) ? `/valuation-drafts/${query.draft}` : `/companies/${companyId}/valuation-drafts/current`,
    );
  } catch {
    return (
      <div className="page-container">
        <header className="page-header">
          <h1>Draft New Valuation Model: {company.name}</h1>
        </header>
        <section className="panel" style={{ padding: "20px" }}>
          <h2>Draft unavailable</h2>
          <p role="alert">Saved drafts could not be loaded. Try again before creating a new draft.</p>
          <Link href={`/companies/${companyId}/valuation`} className="secondary-button">
            Back to Valuation Models
          </Link>
        </section>
      </div>
    );
  }

  if (persistedDraft && persistedDraft.company_id !== companyId) notFound();
  if (persistedDraft?.promoted_model_id) return <section className="panel panel-content"><h1>First model saved</h1>
    <Link href={`/companies/${companyId}/valuation/${persistedDraft.promoted_model_id}`}>Open the saved valuation</Link></section>;
  if (!persistedDraft) return (
    <div className="page-container">
      <header className="page-header"><h1>Start a valuation: {company.name}</h1></header>
      <section className="panel" style={{ padding: "20px" }}>
        <h2>No active draft</h2>
        <p>Create a draft from the available financial history and benchmark inputs. You will review the sources, missing inputs and assumptions before saving a model.</p>
        <RetainedActionForm label="Create valuation draft" action={createValuationSetupDraft.bind(null, id)}>
          <button type="submit" className="primary-button">Create draft</button>
        </RetainedActionForm>
        <Link className="secondary-button" href={`/companies/${companyId}/valuation`}>Back to saved models</Link>
      </section>
    </div>
  );
  const draftId = persistedDraft.id;

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
          <h1>Review valuation draft: {company.name}</h1>
          <p className="subtitle">Your saved inputs are unchanged. Use Refresh when you want to check for newer source inputs, then review the assumptions before creating a model.</p>
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
        initialModelType={modelType}
        initialResearchDate={query.valuation_date && /^\d{4}-\d\d-\d\d$/.test(query.valuation_date) ? query.valuation_date : undefined}
      />
    </div>
  );
}
