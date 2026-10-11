"use server";

import { revalidatePath } from "next/cache";
import { redirect } from "next/navigation";
import { serverDeleteApi, serverPatchApi, serverPostApi } from "@/lib/server-api";
import { buildCompanyPayload, getRequiredFormId } from "@/lib/form-payloads";
import { logAction, actionFormString, deleteRecord, updateRecord, formActionError } from "./shared";
import type { FormActionState } from "./shared";

export async function createCompany(formData: FormData) {
  const company = await serverPostApi<{ id: number; }>("/companies", buildCompanyPayload(formData));
  revalidatePath("/");
  revalidatePath("/companies");
  return company;
}

export async function createCompanyWithState(_state: FormActionState, formData: FormData): Promise<FormActionState> {
  let createdId: number;
  try {
    const company = await createCompany(formData);
    createdId = company.id;
  } catch (error) {
    return formActionError(error);
  }
  redirect(`/companies/${createdId}`);
}

export async function updateCompany(formData: FormData) {
  await updateRecord("/companies", formData, buildCompanyPayload(formData), ["/", "/companies"]);
}

export async function lookupCompanyCik(formData: FormData) {
  const id = getRequiredFormId(formData);
  await serverPostApi(`/companies/${id}/lookup-cik`, {});
  revalidatePath("/companies");
  revalidatePath(`/companies/${id}`);
}

export async function startCompanySetup(formData: FormData) {
  const id = getRequiredFormId(formData);
  await serverPostApi("/api/company-setup/start", { company_id: Number(id) });
  revalidatePath(`/companies/${id}`);
  revalidatePath(`/companies/${id}/setup`);
}

export async function confirmCompanySetupIdentity(formData: FormData) {
  const id = getRequiredFormId(formData);
  await serverPostApi(`/api/company-setup/${id}/confirm-identity`, {});
  revalidatePath(`/companies/${id}`);
  revalidatePath(`/companies/${id}/setup`);
}

export async function updateCompanySetupStep(formData: FormData) {
  const id = getRequiredFormId(formData);
  const current_step = actionFormString(formData, "current_step");
  const filing_status = actionFormString(formData, "filing_status");
  const financial_extraction_status = actionFormString(formData, "financial_extraction_status");
  const industry_mapping_status = actionFormString(formData, "industry_mapping_status");
  const valuation_readiness_status = actionFormString(formData, "valuation_readiness_status");

  await serverPatchApi(`/api/company-setup/${id}/step`, {
    ...(current_step ? { current_step } : {}),
    ...(filing_status ? { filing_status } : {}),
    ...(financial_extraction_status ? { financial_extraction_status } : {}),
    ...(industry_mapping_status ? { industry_mapping_status } : {}),
    ...(valuation_readiness_status ? { valuation_readiness_status } : {}),
  });
  revalidatePath(`/companies/${id}`);
  revalidatePath(`/companies/${id}/setup`);
}

export async function deleteCompany(formData: FormData) {
  await deleteRecord("/companies", formData, ["/", "/companies", "/documents", "/events", "/alerts", "/thesis-notes"]);
}

export async function deleteCompanyWithState(_state: FormActionState, formData: FormData): Promise<FormActionState> {
  try {
    await deleteCompany(formData);
    return { error: null };
  } catch (error) {
    return formActionError(error);
  }
}

export async function createExposureTag(formData: FormData) {
  const payload = {
    name: actionFormString(formData, "name"),
    description: actionFormString(formData, "description") || null,
  };
  logAction(`creating exposure tag`);
  await serverPostApi(`/exposure-tags`, payload);
  revalidatePath("/companies");
  logAction(`created exposure tag; revalidated /companies`);
}

export async function deleteExposureTag(formData: FormData) {
  const id = getRequiredFormId(formData, "id");
  logAction(`deleting exposure tag ${id}`);
  await serverDeleteApi(`/exposure-tags/${id}`);
  revalidatePath("/companies");
  logAction(`deleted exposure tag ${id}; revalidated /companies`);
}

export async function deleteExposureTagWithState(_state: FormActionState, formData: FormData): Promise<FormActionState> {
  const id = getRequiredFormId(formData, "id");
  try {
    logAction(`deleting exposure tag ${id}`);
    await serverDeleteApi(`/exposure-tags/${id}`);
    revalidatePath("/companies");
    logAction(`deleted exposure tag ${id}; revalidated /companies`);
    return { error: null };
  } catch (error) {
    return formActionError(error);
  }
}

export async function addCompanyExposureTag(formData: FormData) {
  const companyId = getRequiredFormId(formData, "company_id");
  const payload = { tag_id: getRequiredFormId(formData, "tag_id") };
  logAction(`adding exposure tag to /companies/${companyId}`);
  await serverPostApi(`/companies/${companyId}/exposure-tags`, payload);
  revalidatePath(`/companies`);
  logAction(`added exposure tag to /companies/${companyId}; revalidated /companies`);
}

export async function removeCompanyExposureTag(formData: FormData) {
  const companyId = getRequiredFormId(formData, "company_id");
  const tagId = getRequiredFormId(formData, "tag_id");
  logAction(`removing exposure tag from /companies/${companyId}`);
  await serverDeleteApi(`/companies/${companyId}/exposure-tags/${tagId}`);
  revalidatePath(`/companies`);
  logAction(`removed exposure tag from /companies/${companyId}; revalidated /companies`);
}
