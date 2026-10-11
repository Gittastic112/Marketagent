"use server";

import { revalidatePath } from "next/cache";
import { serverDeleteApi, serverPostApi } from "@/lib/server-api";
import { buildFinancialStatementPeriodPayload, buildFinancialMetricPayload, getRequiredFormId } from "@/lib/form-payloads";
import { logAction, createRecord } from "./shared";

export async function extractFinancialCandidatesFromFiling(formData: FormData) {
  const companyId = getRequiredFormId(formData, "company_id");
  const filingId = getRequiredFormId(formData, "filing_id");
  logAction(`extracting financial candidates from filing ${filingId}`);
  await serverPostApi(`/api/filings/${filingId}/extract-financials`, {});
  revalidatePath(`/companies/${companyId}`);
  revalidatePath(`/companies/${companyId}/filings`);
  revalidatePath(`/companies/${companyId}/fundamentals`);
}

export async function extractXbrlFromCompany(formData: FormData) {
  const companyId = getRequiredFormId(formData, "company_id");
  logAction(`extracting XBRL financial candidates for company ${companyId}`);
  await serverPostApi(`/api/companies/${companyId}/extract-xbrl`, {});
  revalidatePath(`/companies/${companyId}`);
  revalidatePath(`/companies/${companyId}/filings`);
  revalidatePath(`/companies/${companyId}/fundamentals`);
}

export async function createFinancialStatementPeriod(formData: FormData, companyId: string) {
  await createRecord(`/companies/${companyId}/financial-periods`, buildFinancialStatementPeriodPayload(formData), [`/companies/${companyId}`]);
}

export async function createFinancialMetric(formData: FormData, periodId: string, companyId: string) {
  await createRecord(`/financial-periods/${periodId}/metrics`, buildFinancialMetricPayload(formData), [`/companies/${companyId}`]);
}

export async function deleteFinancialStatementPeriod(formData: FormData, companyId: string) {
  const periodId = getRequiredFormId(formData);
  logAction(`deleting /financial-periods/${periodId}`);
  await serverDeleteApi(`/financial-periods/${periodId}`);
  revalidatePath(`/companies/${companyId}`);
  logAction(`deleted /financial-periods/${periodId}; revalidated /companies/${companyId}`);
}

export async function normalizeFinancialPeriodAction(formData: FormData) {
  const companyId = getRequiredFormId(formData, "company_id");
  const periodId = getRequiredFormId(formData, "period_id");
  logAction(`normalizing /companies/${companyId}/financial-statements/${periodId}`);
  await serverPostApi(`/api/companies/${companyId}/financial-statements/${periodId}/normalize`, {});
  revalidatePath(`/companies/${companyId}`);
  revalidatePath(`/companies/${companyId}/fundamentals`);
  revalidatePath(`/companies/${companyId}/setup`);
  logAction(`normalized /companies/${companyId}/financial-statements/${periodId}`);
}

export async function backfillNormalizedFinancialsAction(formData: FormData) {
  const companyId = getRequiredFormId(formData, "company_id");
  await serverPostApi(`/api/companies/${companyId}/financial-statements/normalized/backfill`, { dry_run: false });
  revalidatePath(`/companies/${companyId}/fundamentals`);
  revalidatePath(`/companies/${companyId}/valuation`);
}
