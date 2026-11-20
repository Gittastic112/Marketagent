"use server";

import { revalidatePath } from "next/cache";
import { redirect } from "next/navigation";
import type { AutofillAssumptionDraft } from "@/lib/api/valuation-drafts";
import { serverDeleteApi, serverPatchApi, serverPostApi } from "@/lib/server-api";
import { unresolvedReviewFields } from "@/lib/autofill-review";
import { buildValuationModelPayload, buildDcfAssumptionSetPayload, getRequiredFormId } from "@/lib/form-payloads";
import { logAction, actionFormString, createRecord, formActionError } from "./shared";
import type { FormActionState } from "./shared";

export async function createValuationSetupDraft(companyId: string, _formData: FormData): Promise<FormActionState> {
  if (!/^[1-9]\d*$/.test(companyId) || !Number.isSafeInteger(Number(companyId))) {
    return { error: "A valid company is required." };
  }
  try {
    await serverPostApi(`/companies/${companyId}/valuation-drafts`, {});
    revalidatePath(`/companies/${companyId}/valuation/draft`);
    return { error: null };
  } catch (error) {
    return formActionError(error);
  }
}

export async function createValuationModel(formData: FormData, companyId: string) {
  await createRecord(`/companies/${companyId}/valuation-models`, buildValuationModelPayload(formData), [`/companies/${companyId}`]);
}

export async function createDcfAssumptionSet(formData: FormData, modelId: string, companyId: string) {
  await createRecord(`/valuation-models/${modelId}/assumptions`, buildDcfAssumptionSetPayload(formData), [`/companies/${companyId}`]);
}

export async function createDcfAssumptionSetWithState(
  formData: FormData,
  modelId: string,
  companyId: string,
): Promise<FormActionState> {
  try {
    await createDcfAssumptionSet(formData, modelId, companyId);
    return { error: null };
  } catch (error) {
    return formActionError(error);
  }
}

export async function deleteValuationModel(formData: FormData, companyId: string) {
  const modelId = getRequiredFormId(formData);
  logAction(`deleting /valuation-models/${modelId}`);
  await serverDeleteApi(`/valuation-models/${modelId}`);
  revalidatePath(`/companies/${companyId}`);
  logAction(`deleted /valuation-models/${modelId}; revalidated /companies/${companyId}`);
}

export async function deleteValuationModelWithState(
  companyId: string,
  _state: FormActionState,
  formData: FormData,
): Promise<FormActionState> {
  try {
    await deleteValuationModel(formData, companyId);
    return { error: null };
  } catch (error) {
    return formActionError(error);
  }
}

export async function updateValuationModelWithState(
  modelId: string,
  companyId: string,
  _state: FormActionState,
  formData: FormData,
): Promise<FormActionState> {
  try {
    const name = actionFormString(formData, "name");
    if (!name) return { error: "Model name is required." };
    await serverPatchApi(`/valuation-models/${modelId}`, {
      name,
      description: actionFormString(formData, "description") || null,
    });
    revalidatePath(`/companies/${companyId}/valuation`);
    revalidatePath(`/companies/${companyId}/valuation/${modelId}`);
    return { error: null };
  } catch (error) {
    return formActionError(error);
  }
}

export async function createValuationModelWithAssumptions(formData: FormData, companyId: string) {
  logAction(`creating valuation model with assumptions for company ${companyId}`);

  const payload = buildDcfAssumptionSetPayload(formData);
  const draftResponse = await serverPostApi<AutofillAssumptionDraft>(
    `/companies/${companyId}/valuation-models/autofill`,
    { base_assumptions: {} },
  );
  const draft = ((draftResponse as { data?: AutofillAssumptionDraft; }).data || draftResponse) as AutofillAssumptionDraft;
  const reviewedFields = new Set(
    formData.getAll("reviewed_field").filter((value): value is string => typeof value === "string"),
  );
  const unresolved = unresolvedReviewFields(
    draft.source_metadata,
    reviewedFields,
    payload,
  );
  if (unresolved.length > 0) {
    throw new Error(`Assumption review is incomplete: ${unresolved.join(", ")}`);
  }

  // 1. Create model
  const name = actionFormString(formData, "name");
  const description = actionFormString(formData, "description");
  const model_type = actionFormString(formData, "model_type");

  const modelRes = await serverPostApi(`/companies/${companyId}/valuation-models`, { name, description, model_type });
  const model = (modelRes as any).data || modelRes;

  // 2. Create assumption set using the draft values provided
  await serverPostApi(`/valuation-models/${model.id}/assumptions`, payload);

  revalidatePath(`/companies/${companyId}`);
  logAction(`created valuation model ${model.id} with assumptions`);

  // Return the created model ID so the client can redirect
  return model.id;
}


export async function promoteValuationSetupDraft(formData: FormData, draftId: number, companyId: string) {
  // The initial preview already persisted draft edits. An identical retry only confirms its frozen command.
  const command = {
    name: actionFormString(formData, "name"), description: actionFormString(formData, "description") || null,
    model_type: actionFormString(formData, "model_type") || "fcff_dcf",
    expected_updated_at: actionFormString(formData, "draft_updated_at"),
    valuation_date: actionFormString(formData, "valuation_date"),
    preview_hash: actionFormString(formData, "preview_hash"), submission_id: actionFormString(formData, "submission_id"),
    reason: actionFormString(formData, "reason"),
  };
  const result = await serverPostApi<{model_id:number}>(`/valuation-drafts/${draftId}/confirm`, command);
  revalidatePath(`/companies/${companyId}/valuation`);
  return result.model_id;
}
