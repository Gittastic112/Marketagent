"use server";

import { revalidatePath } from "next/cache";
import { redirect } from "next/navigation";

import { ApiError } from "@/lib/api";
import type { AutofillAssumptionDraft } from "@/lib/api";
import { serverDeleteApi, serverPatchApi, serverPostApi } from "@/lib/server-api";
import { unresolvedReviewFields } from "@/lib/autofill-review";
import {
  buildAlertPayload,
  buildAlertReviewPayload,
  buildCompanyPayload,
  buildEventPayload,
  buildPortfolioHoldingPayload,
  buildPortfolioPayload,
  buildPortfolioTransactionPayload,
  buildPortfolioCashBalancePayload,
  buildPortfolioSnapshotPayload,
  buildRawDocumentPayload,
  buildRawDocumentMetadataPayload,
  buildRssIngestionPayload,
  buildSecFilingIngestionPayload,
  buildSourcePayload,
  buildThesisNotePayload,
  buildMarketPricePayload,
  buildFinancialStatementPeriodPayload,
  buildFinancialMetricPayload,
  buildSocialPostPayload,
  buildSentimentScorePayload,
  buildNarrativeClusterPayload,
  buildNarrativeClaimPayload,
  buildNarrativeMentionPayload,
  buildValuationModelPayload,
  buildDcfAssumptionSetPayload,
  buildThesisAssumptionPayload,
  buildThesisChangePayload,
  getRequiredFormId
} from "@/lib/form-payloads";

const DEBUG_LOGS_ENABLED = process.env.NEXT_PUBLIC_DEBUG_LOGS === "true";

export type FormActionState = {
  error: string | null;
};

function logAction(message: string) {
  if (DEBUG_LOGS_ENABLED) {
    console.log(`[action] ${message}`);
  }
}

function actionFormString(formData: FormData, key: string): string {
  const value = formData.get(key);
  return typeof value === "string" ? value.trim() : "";
}

async function createRecord(path: string, payload: unknown, pages: string[]) {
  logAction(`creating ${path}`);
  await serverPostApi(path, payload);
  for (const page of pages) {
    revalidatePath(page);
  }
  logAction(`created ${path}; revalidated ${pages.join(", ")}`);
}

async function deleteRecord(path: string, formData: FormData, pages: string[]) {
  const id = getRequiredFormId(formData);
  logAction(`deleting ${path}/${id}`);
  await serverDeleteApi(`${path}/${id}`);
  for (const page of pages) {
    revalidatePath(page);
  }
  logAction(`deleted ${path}/${id}; revalidated ${pages.join(", ")}`);
}

async function updateRecord(path: string, formData: FormData, payload: unknown, pages: string[]) {
  const id = getRequiredFormId(formData);
  logAction(`updating ${path}/${id}`);
  await serverPatchApi(`${path}/${id}`, payload);
  for (const page of pages) {
    revalidatePath(page);
  }
  logAction(`updated ${path}/${id}; revalidated ${pages.join(", ")}`);
}

function formActionError(error: unknown): FormActionState {
  if (error instanceof ApiError) {
    return { error: error.message };
  }
  return { error: "The request failed. Check the fields and try again." };
}

export async function createCompany(formData: FormData) {
  const company = await serverPostApi<{ id: number }>("/companies", buildCompanyPayload(formData));
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

export async function importFredSeries(formData: FormData) {
  const series_id = String(formData.get("series_id") || "").trim();

  if (!series_id) {
    throw new Error("FRED Series ID is required.");
  }

  try {
    await serverPostApi("/ingest/fred-series", { series_id });
    revalidatePath("/macro");
  } catch (error) {
    if (error instanceof ApiError) {
      throw new Error(`Failed to import FRED series: ${error.message}`);
    }
    throw error;
  }
}

export async function createSource(formData: FormData) {
  await createRecord("/sources", buildSourcePayload(formData), ["/sources"]);
}

export async function updateSource(formData: FormData) {
  await updateRecord("/sources", formData, buildSourcePayload(formData), ["/sources"]);
}

export async function createRawDocument(formData: FormData) {
  await createRecord("/raw-documents", buildRawDocumentPayload(formData), ["/", "/documents", "/daily-brief"]);
}

export async function applyEventEvidenceBackfill() {
  await serverPostApi("/data-health/event-evidence-backfill", {
    dry_run: false,
    limit: 100,
  });
  revalidatePath("/data-health");
  revalidatePath("/events");
  revalidatePath("/alerts");
}

export async function resolveEventEvidenceWithState(
  _state: FormActionState,
  formData: FormData,
): Promise<FormActionState> {
  let eventId: number;
  try {
    eventId = getRequiredFormId(formData, "event_id");
    const exactString = (key: string) => {
      const value = formData.get(key);
      return typeof value === "string" ? value : "";
    };
    const nonNegativeInteger = (key: string) => {
      const value = Number(exactString(key));
      if (!Number.isInteger(value) || value < 0) {
        throw new Error(`Invalid form field: ${key}`);
      }
      return value;
    };
    await serverPostApi(`/events/${eventId}/evidence-resolution`, {
      raw_document_id: getRequiredFormId(formData, "raw_document_id"),
      start_char: nonNegativeInteger("start_char"),
      end_char: getRequiredFormId(formData, "end_char"),
      quote: exactString("quote"),
      search_query: exactString("search_query"),
      occurrence_index: getRequiredFormId(formData, "occurrence_index"),
      document_content_hash: exactString("document_content_hash"),
    });
    revalidatePath("/data-health");
    revalidatePath(`/events/${eventId}/evidence-resolution`);
    revalidatePath("/events");
    revalidatePath("/alerts");
  } catch (error) {
    return formActionError(error);
  }
  redirect(`/events/${eventId}/evidence-resolution?saved=1`);
}

export async function importRssXml(formData: FormData) {
  await createRecord("/ingest/rss", buildRssIngestionPayload(formData), ["/", "/documents", "/events", "/alerts", "/daily-brief"]);
}

export async function fetchRssFeed(formData: FormData) {
  await createRecord("/ingest/rss-feed", buildRssIngestionPayload(formData), ["/", "/documents", "/events", "/alerts", "/daily-brief"]);
}

export async function fetchActiveRssFeeds() {
  await createRecord("/ingest/rss-feeds/active", {}, ["/", "/sources", "/documents", "/events", "/alerts", "/daily-brief"]);
}

export async function importSecFilings(formData: FormData) {
  const companyId = getRequiredFormId(formData, "company_id");
  await createRecord("/ingest/sec-filings", buildSecFilingIngestionPayload(formData), ["/", "/documents", "/events", "/alerts", "/daily-brief"]);
  revalidatePath(`/companies/${companyId}`);
  revalidatePath(`/companies/${companyId}/filings`);
  revalidatePath(`/companies/${companyId}/fundamentals`);
}

export async function fetchRecentSecFilings(formData: FormData) {
  await createRecord("/ingest/sec-filings/recent", buildSecFilingIngestionPayload(formData), ["/", "/documents", "/events", "/alerts", "/daily-brief"]);
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

export async function createManualCompanyFilingLink(formData: FormData) {
  const id = getRequiredFormId(formData);
  const publishedAt = actionFormString(formData, "published_at");

  await serverPostApi(`/api/companies/${id}/filings/manual-link`, {
    document_type: actionFormString(formData, "document_type"),
    title: actionFormString(formData, "title"),
    url: actionFormString(formData, "url") || null,
    published_at: publishedAt ? `${publishedAt}T00:00:00Z` : null,
    raw_text: actionFormString(formData, "raw_text") || null,
  });
  revalidatePath(`/companies/${id}`);
  revalidatePath(`/companies/${id}/setup`);
  revalidatePath(`/companies/${id}/filings`);
  revalidatePath("/documents");
}

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

export async function updateRawDocument(formData: FormData) {
  await updateRecord("/raw-documents", formData, buildRawDocumentMetadataPayload(formData), ["/", "/documents", "/daily-brief"]);
}

export async function createEvent(formData: FormData) {
  await createRecord("/events", buildEventPayload(formData), ["/", "/events", "/daily-brief"]);
}

export async function updateEvent(formData: FormData) {
  await updateRecord("/events", formData, buildEventPayload(formData), ["/", "/events", "/daily-brief"]);
}

export async function extractEvents() {
  await createRecord("/extract/events", {}, ["/", "/events", "/daily-brief"]);
}

export async function createAlert(formData: FormData) {
  await createRecord("/alerts", buildAlertPayload(formData), ["/", "/alerts", "/daily-brief"]);
}

export async function generateAlerts() {
  await createRecord("/generate/alerts", {}, ["/", "/alerts", "/daily-brief"]);
}

export async function updateAlert(formData: FormData) {
  await updateRecord("/alerts", formData, buildAlertPayload(formData), ["/", "/alerts", "/daily-brief"]);
}

export async function reviewAlert(formData: FormData) {
  await updateRecord("/alerts", formData, buildAlertReviewPayload(formData), ["/", "/alerts", "/daily-brief"]);
}

export async function createThesisNote(formData: FormData) {
  await createRecord("/thesis-notes", buildThesisNotePayload(formData), ["/", "/thesis-notes", "/daily-brief"]);
}

export async function updateThesisNote(formData: FormData) {
  await updateRecord("/thesis-notes", formData, buildThesisNotePayload(formData), ["/", "/thesis-notes", "/daily-brief"]);
}

export async function createPortfolio(formData: FormData) {
  await createRecord("/portfolios", buildPortfolioPayload(formData), ["/portfolio"]);
}

export async function updatePortfolio(formData: FormData) {
  await updateRecord("/portfolios", formData, buildPortfolioPayload(formData), ["/portfolio"]);
}

export async function createPortfolioHolding(formData: FormData) {
  await createRecord("/portfolio-holdings", buildPortfolioHoldingPayload(formData), ["/portfolio"]);
}

export async function updatePortfolioHolding(formData: FormData) {
  await updateRecord("/portfolio-holdings", formData, buildPortfolioHoldingPayload(formData), ["/portfolio"]);
}

export async function createPortfolioTransaction(formData: FormData) {
  await createRecord("/portfolio-transactions", buildPortfolioTransactionPayload(formData), ["/portfolio"]);
}

export async function updatePortfolioTransaction(formData: FormData) {
  await updateRecord("/portfolio-transactions", formData, buildPortfolioTransactionPayload(formData), ["/portfolio"]);
}

export async function createPortfolioCashBalance(formData: FormData) {
  await createRecord("/portfolio-cash-balances", buildPortfolioCashBalancePayload(formData), ["/portfolio"]);
}

export async function updatePortfolioCashBalance(formData: FormData) {
  await updateRecord("/portfolio-cash-balances", formData, buildPortfolioCashBalancePayload(formData), ["/portfolio"]);
}

export async function createPortfolioSnapshot(formData: FormData) {
  await createRecord("/portfolio-snapshots", buildPortfolioSnapshotPayload(formData), ["/portfolio"]);
}

export async function updatePortfolioSnapshot(formData: FormData) {
  await updateRecord("/portfolio-snapshots", formData, buildPortfolioSnapshotPayload(formData), ["/portfolio"]);
}

export async function deletePortfolioCashBalance(formData: FormData) {
  await deleteRecord("/portfolio-cash-balances", formData, ["/portfolio"]);
}

export async function deletePortfolioCashBalanceWithState(_state: FormActionState, formData: FormData): Promise<FormActionState> {
  try {
    await deletePortfolioCashBalance(formData);
    return { error: null };
  } catch (error) {
    return formActionError(error);
  }
}

export async function deletePortfolioSnapshot(formData: FormData) {
  await deleteRecord("/portfolio-snapshots", formData, ["/portfolio"]);
}

export async function deletePortfolioSnapshotWithState(_state: FormActionState, formData: FormData): Promise<FormActionState> {
  try {
    await deletePortfolioSnapshot(formData);
    return { error: null };
  } catch (error) {
    return formActionError(error);
  }
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

export async function deleteSource(formData: FormData) {
  await deleteRecord("/sources", formData, ["/sources", "/documents"]);
}

export async function deleteSourceWithState(_state: FormActionState, formData: FormData): Promise<FormActionState> {
  try {
    await deleteSource(formData);
    return { error: null };
  } catch (error) {
    return formActionError(error);
  }
}

export async function deleteRawDocument(formData: FormData) {
  await deleteRecord("/raw-documents", formData, ["/", "/documents", "/events", "/daily-brief"]);
}

export async function deleteRawDocumentWithState(_state: FormActionState, formData: FormData): Promise<FormActionState> {
  try {
    await deleteRawDocument(formData);
    return { error: null };
  } catch (error) {
    return formActionError(error);
  }
}

export async function deleteEvent(formData: FormData) {
  await deleteRecord("/events", formData, ["/", "/events", "/alerts", "/daily-brief"]);
}

export async function deleteEventWithState(_state: FormActionState, formData: FormData): Promise<FormActionState> {
  try {
    await deleteEvent(formData);
    return { error: null };
  } catch (error) {
    return formActionError(error);
  }
}

export async function deleteAlert(formData: FormData) {
  await deleteRecord("/alerts", formData, ["/", "/alerts", "/daily-brief"]);
}

export async function deleteAlertWithState(_state: FormActionState, formData: FormData): Promise<FormActionState> {
  try {
    await deleteAlert(formData);
    return { error: null };
  } catch (error) {
    return formActionError(error);
  }
}

export async function deleteThesisNote(formData: FormData) {
  await deleteRecord("/thesis-notes", formData, ["/", "/thesis-notes", "/daily-brief"]);
}

export async function deleteThesisNoteWithState(_state: FormActionState, formData: FormData): Promise<FormActionState> {
  try {
    await deleteThesisNote(formData);
    return { error: null };
  } catch (error) {
    return formActionError(error);
  }
}

export async function deletePortfolio(formData: FormData) {
  await deleteRecord("/portfolios", formData, ["/portfolio"]);
}

export async function deletePortfolioWithState(_state: FormActionState, formData: FormData): Promise<FormActionState> {
  try {
    await deletePortfolio(formData);
    return { error: null };
  } catch (error) {
    return formActionError(error);
  }
}

export async function deletePortfolioHolding(formData: FormData) {
  await deleteRecord("/portfolio-holdings", formData, ["/portfolio"]);
}

export async function deletePortfolioHoldingWithState(
  _state: FormActionState,
  formData: FormData
): Promise<FormActionState> {
  try {
    await deletePortfolioHolding(formData);
    return { error: null };
  } catch (error) {
    return formActionError(error);
  }
}

export async function deletePortfolioTransaction(formData: FormData) {
  await deleteRecord("/portfolio-transactions", formData, ["/portfolio"]);
}

export async function deletePortfolioTransactionWithState(
  _state: FormActionState,
  formData: FormData
): Promise<FormActionState> {
  try {
    await deletePortfolioTransaction(formData);
    return { error: null };
  } catch (error) {
    return formActionError(error);
  }
}

export async function createMarketPrice(formData: FormData) {
  await createRecord("/market-prices", buildMarketPricePayload(formData), ["/market-prices", "/portfolio"]);
}

export async function updateMarketPrice(formData: FormData) {
  await updateRecord("/market-prices", formData, buildMarketPricePayload(formData), ["/market-prices", "/portfolio"]);
}

export async function deleteMarketPrice(formData: FormData) {
  await deleteRecord("/market-prices", formData, ["/market-prices", "/portfolio"]);
}

export async function deleteMarketPriceWithState(
  _state: FormActionState,
  formData: FormData
): Promise<FormActionState> {
  try {
    await deleteMarketPrice(formData);
    return { error: null };
  } catch (error) {
    return formActionError(error);
  }
}

export async function saveDailyBrief() {
  await createRecord("/daily-brief", {}, ["/daily-brief"]);
}

export async function markDailyBriefReviewed(formData: FormData) {
  const id = getRequiredFormId(formData);
  logAction(`marking /daily-brief/${id} as reviewed`);
  await serverPatchApi(`/daily-brief/${id}/review`, {});
  revalidatePath("/daily-brief");
  logAction(`marked /daily-brief/${id} as reviewed; revalidated /daily-brief`);
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

export async function createValuationModel(formData: FormData, companyId: string) {
  await createRecord(`/companies/${companyId}/valuation-models`, buildValuationModelPayload(formData), [`/companies/${companyId}`]);
}

export async function createDcfAssumptionSet(formData: FormData, modelId: string, companyId: string) {
  await createRecord(`/valuation-models/${modelId}/assumptions`, buildDcfAssumptionSetPayload(formData), [`/companies/${companyId}`]);
}

export async function deleteValuationModel(formData: FormData, companyId: string) {
  const modelId = getRequiredFormId(formData);
  logAction(`deleting /valuation-models/${modelId}`);
  await serverDeleteApi(`/valuation-models/${modelId}`);
  revalidatePath(`/companies/${companyId}`);
  logAction(`deleted /valuation-models/${modelId}; revalidated /companies/${companyId}`);
}

export async function triggerParseFilingSections(rawDocumentId: number) {
  logAction(`triggering parse for /raw-documents/${rawDocumentId}`);
  await serverPostApi(`/raw-documents/${rawDocumentId}/parse`, {});
  revalidatePath(`/documents/${rawDocumentId}/sections`);
  logAction(`triggered parse for /raw-documents/${rawDocumentId}; revalidated /documents/${rawDocumentId}/sections`);
}

export async function triggerGenerateAiSummary(rawDocumentId: number, formData: FormData) {
  if (formData.get("privacy_disclosure_version") !== "v1") {
    throw new Error("Review and acknowledge the AI data disclosure before continuing.");
  }
  logAction(`triggering AI summary for /raw-documents/${rawDocumentId}`);
  await serverPostApi(`/raw-documents/${rawDocumentId}/ai-summary`, {
    privacy_disclosure_version: "v1",
  });
  revalidatePath(`/documents/${rawDocumentId}/ai`);
  logAction(`triggered AI summary for /raw-documents/${rawDocumentId}; revalidated /documents/${rawDocumentId}/ai`);
}

export async function createSocialPost(formData: FormData) {
  await createRecord("/social-posts", buildSocialPostPayload(formData), ["/social"]);
}

export async function updateSocialPost(formData: FormData) {
  await updateRecord("/social-posts", formData, buildSocialPostPayload(formData), ["/social"]);
}

export async function deleteSocialPost(formData: FormData) {
  await deleteRecord("/social-posts", formData, ["/social"]);
}

export async function deleteSocialPostWithState(_state: FormActionState, formData: FormData): Promise<FormActionState> {
  try {
    await deleteSocialPost(formData);
    return { error: null };
  } catch (error) {
    return formActionError(error);
  }
}

export async function createSentimentScore(formData: FormData) {
  await createRecord("/sentiment-scores", buildSentimentScorePayload(formData), ["/social"]);
}

export async function updateSentimentScore(formData: FormData) {
  await updateRecord("/sentiment-scores", formData, buildSentimentScorePayload(formData), ["/social"]);
}

export async function deleteSentimentScore(formData: FormData) {
  await deleteRecord("/sentiment-scores", formData, ["/social"]);
}

export async function deleteSentimentScoreWithState(_state: FormActionState, formData: FormData): Promise<FormActionState> {
  try {
    await deleteSentimentScore(formData);
    return { error: null };
  } catch (error) {
    return formActionError(error);
  }
}

export async function createNarrativeCluster(formData: FormData) {
  await createRecord("/narrative-clusters", buildNarrativeClusterPayload(formData), ["/social", "/narratives"]);
}

export async function updateNarrativeCluster(formData: FormData) {
  await updateRecord("/narrative-clusters", formData, buildNarrativeClusterPayload(formData), ["/social", "/narratives"]);
}

export async function deleteNarrativeCluster(formData: FormData) {
  await deleteRecord("/narrative-clusters", formData, ["/social", "/narratives"]);
}

export async function deleteNarrativeClusterWithState(_state: FormActionState, formData: FormData): Promise<FormActionState> {
  try {
    await deleteNarrativeCluster(formData);
    return { error: null };
  } catch (error) {
    return formActionError(error);
  }
}

export async function createNarrativeClaim(formData: FormData) {
  await createRecord("/narrative-claims", buildNarrativeClaimPayload(formData), ["/social", "/narratives"]);
}

export async function updateNarrativeClaim(formData: FormData) {
  await updateRecord("/narrative-claims", formData, buildNarrativeClaimPayload(formData), ["/social", "/narratives"]);
}

export async function deleteNarrativeClaim(formData: FormData) {
  await deleteRecord("/narrative-claims", formData, ["/social", "/narratives"]);
}

export async function deleteNarrativeClaimWithState(_state: FormActionState, formData: FormData): Promise<FormActionState> {
  try {
    await deleteNarrativeClaim(formData);
    return { error: null };
  } catch (error) {
    return formActionError(error);
  }
}

export async function createNarrativeMention(formData: FormData) {
  await createRecord("/narrative-mentions", buildNarrativeMentionPayload(formData), ["/social", "/narratives"]);
}

export async function updateNarrativeMention(formData: FormData) {
  await updateRecord("/narrative-mentions", formData, buildNarrativeMentionPayload(formData), ["/social", "/narratives"]);
}

export async function deleteNarrativeMention(formData: FormData) {
  await deleteRecord("/narrative-mentions", formData, ["/social", "/narratives"]);
}

export async function deleteNarrativeMentionWithState(_state: FormActionState, formData: FormData): Promise<FormActionState> {
  try {
    await deleteNarrativeMention(formData);
    return { error: null };
  } catch (error) {
    return formActionError(error);
  }
}

export async function extractNarratives(formData: FormData) {
  if (formData.get("privacy_disclosure_version") !== "v1") {
    throw new Error("Review and acknowledge the AI data disclosure before continuing.");
  }
  await createRecord(
    "/extract",
    { privacy_disclosure_version: "v1" },
    ["/narratives", "/social"],
  );
}

export async function createThesisAssumption(formData: FormData, thesisNoteId: string) {
  await createRecord(`/thesis-notes/${thesisNoteId}/assumptions`, buildThesisAssumptionPayload(formData), [`/thesis-notes/${thesisNoteId}`]);
}

export async function updateThesisAssumption(formData: FormData, thesisNoteId: string) {
  const id = getRequiredFormId(formData);
  logAction(`updating /thesis-assumptions/${id}`);
  await serverPatchApi(`/thesis-assumptions/${id}`, buildThesisAssumptionPayload(formData));
  revalidatePath(`/thesis-notes/${thesisNoteId}`);
  logAction(`updated /thesis-assumptions/${id}; revalidated /thesis-notes/${thesisNoteId}`);
}

export async function deleteThesisAssumption(formData: FormData, thesisNoteId: string) {
  const id = getRequiredFormId(formData);
  logAction(`deleting /thesis-assumptions/${id}`);
  await serverDeleteApi(`/thesis-assumptions/${id}`);
  revalidatePath(`/thesis-notes/${thesisNoteId}`);
  logAction(`deleted /thesis-assumptions/${id}; revalidated /thesis-notes/${thesisNoteId}`);
}

export async function createThesisChange(formData: FormData, thesisNoteId: string) {
  await createRecord(`/thesis-notes/${thesisNoteId}/changes`, buildThesisChangePayload(formData), [`/thesis-notes/${thesisNoteId}`]);
}

export async function addEventCorroboration(formData: FormData) {
  const eventId = getRequiredFormId(formData, "event_id");
  const payload = { target_event_id: getRequiredFormId(formData, "target_event_id") };
  logAction(`adding corroboration to /events/${eventId}`);
  await serverPostApi(`/events/${eventId}/corroborations`, payload);
  revalidatePath("/events");
  logAction(`added corroboration to /events/${eventId}; revalidated /events`);
}

export async function removeEventCorroboration(formData: FormData) {
  const eventId = getRequiredFormId(formData, "event_id");
  const targetId = getRequiredFormId(formData, "target_event_id");
  logAction(`removing corroboration from /events/${eventId}`);
  await serverDeleteApi(`/events/${eventId}/corroborations/${targetId}`);
  revalidatePath("/events");
  logAction(`removed corroboration from /events/${eventId}; revalidated /events`);
}

export async function addEventContradiction(formData: FormData) {
  const eventId = getRequiredFormId(formData, "event_id");
  const payload = { target_event_id: getRequiredFormId(formData, "target_event_id") };
  logAction(`adding contradiction to /events/${eventId}`);
  await serverPostApi(`/events/${eventId}/contradictions`, payload);
  revalidatePath("/events");
  logAction(`added contradiction to /events/${eventId}; revalidated /events`);
}

export async function removeEventContradiction(formData: FormData) {
  const eventId = getRequiredFormId(formData, "event_id");
  const targetId = getRequiredFormId(formData, "target_event_id");
  logAction(`removing contradiction from /events/${eventId}`);
  await serverDeleteApi(`/events/${eventId}/contradictions/${targetId}`);
  revalidatePath("/events");
  logAction(`removed contradiction from /events/${eventId}; revalidated /events`);
}

export async function updateScoringConfig(formData: FormData) {
  const payload = {
    weight_credibility: parseFloat(formData.get("weight_credibility") as string),
    weight_novelty: parseFloat(formData.get("weight_novelty") as string),
    weight_impact: parseFloat(formData.get("weight_impact") as string),
    weight_speed: parseFloat(formData.get("weight_speed") as string),
  };
  logAction(`updating scoring config`);
  await serverPatchApi(`/scoring-config`, payload);
  revalidatePath("/settings");
  logAction(`updated scoring config; revalidated /settings`);
}

export async function createMacroSeries(formData: FormData) {
  const payload = {
    name: actionFormString(formData, "name"),
    description: actionFormString(formData, "description") || null,
    units: actionFormString(formData, "units") || null,
    frequency: actionFormString(formData, "frequency") || null,
  };
  logAction(`creating macro series`);
  await serverPostApi(`/macro`, payload);
  revalidatePath("/macro");
  logAction(`created macro series; revalidated /macro`);
}

export async function createMacroObservation(formData: FormData) {
  const seriesId = getRequiredFormId(formData, "series_id");
  const payload = {
    date_recorded: actionFormString(formData, "date_recorded"),
    value: Number(actionFormString(formData, "value")),
  };
  logAction(`creating macro observation for series ${seriesId}`);
  await serverPostApi(`/macro/${seriesId}/observations`, payload);
  revalidatePath("/macro");
  logAction(`created macro observation for series ${seriesId}; revalidated /macro`);
}

export async function deleteMacroSeriesWithState(_state: FormActionState, formData: FormData): Promise<FormActionState> {
  const id = getRequiredFormId(formData, "id");
  try {
    logAction(`deleting macro series ${id}`);
    await serverDeleteApi(`/macro/${id}`);
    revalidatePath("/macro");
    logAction(`deleted macro series ${id}; revalidated /macro`);
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

export async function createVariantPerception(formData: FormData, companyId: string) {
  const payload = {
    company_id: parseInt(companyId, 10),
    market_belief: getRequiredFormId(formData, "market_belief"),
    my_belief: getRequiredFormId(formData, "my_belief"),
    what_would_close_the_gap: formData.get("what_would_close_the_gap") as string | null,
    confidence: formData.get("confidence") as string || "Medium"
  };
  await serverPostApi("/variant-perceptions", payload);
  revalidatePath(`/companies/${companyId}/decisions`);
}

export async function createEvidenceLedgerItem(formData: FormData, companyId: string) {
  const payload = {
    company_id: parseInt(companyId, 10),
    evidence_text: getRequiredFormId(formData, "evidence_text"),
    effect: formData.get("effect") as string || "Supports",
    confidence: "Medium",
    date_discovered: getRequiredFormId(formData, "date_discovered")
  };
  await serverPostApi("/evidence", payload);
  revalidatePath(`/companies/${companyId}/decisions`);
}

export async function createDecisionLogItem(formData: FormData, companyId: string) {
  const price = formData.get("price_at_time");
  const payload = {
    company_id: parseInt(companyId, 10),
    decision_type: formData.get("decision_type") as string || "Hold",
    rationale: getRequiredFormId(formData, "rationale"),
    price_at_time: price ? parseFloat(price as string) : null,
    emotional_state: formData.get("emotional_state") as string || null,
    alternatives_considered: formData.get("alternatives_considered") as string || null,
  };
  await serverPostApi("/decisions", payload);
  revalidatePath(`/companies/${companyId}/decisions`);
}

export async function createOutcomeReview(formData: FormData, decisionId: string, companyId: string) {
  const payload = {
    what_happened: getRequiredFormId(formData, "what_happened"),
    wrong_assumption: formData.get("wrong_assumption") as string || null,
    information_unavailable_or_misinterpreted: formData.get("information_unavailable_or_misinterpreted") === "on",
    valuation_wrong: formData.get("valuation_wrong") === "on",
    thesis_wrong: formData.get("thesis_wrong") === "on",
    timing_wrong: formData.get("timing_wrong") === "on",
    sizing_wrong: formData.get("sizing_wrong") === "on",
  };
  await serverPostApi(`/decisions/${decisionId}/review`, payload);
  revalidatePath(`/companies/${companyId}/decisions`);
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

export async function triggerEventClassification(formData: FormData) {
  const eventId = getRequiredFormId(formData, "event_id");
  const companyId = getRequiredFormId(formData, "company_id");
  logAction(`classifying event ${eventId} for thesis impacts`);
  if (formData.get("privacy_disclosure_version") !== "v1") {
    throw new Error("Review and acknowledge the AI data disclosure before continuing.");
  }
  await serverPostApi(`/events/${eventId}/classify-impact`, {
    privacy_disclosure_version: "v1",
  });
  revalidatePath(`/companies/${companyId}`);
  revalidatePath(`/companies/${companyId}/thesis`);
  logAction(`classified event ${eventId}`);
}

export async function createValuationModelWithAssumptions(formData: FormData, companyId: string) {
  logAction(`creating valuation model with assumptions for company ${companyId}`);

  const payload = buildDcfAssumptionSetPayload(formData);
  const draftResponse = await serverPostApi<AutofillAssumptionDraft>(
    `/companies/${companyId}/valuation-models/autofill`,
    { base_assumptions: {} },
  );
  const draft = ((draftResponse as { data?: AutofillAssumptionDraft }).data || draftResponse) as AutofillAssumptionDraft;
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
  logAction(`promoting valuation setup draft ${draftId} for company ${companyId}`);
  const payload = buildDcfAssumptionSetPayload(formData);
  const editedFields = new Set(
    formData.getAll("edited_field").filter((value): value is string => typeof value === "string"),
  );
  const assumptionsPatch = Object.fromEntries(
    Object.entries(payload).filter(([key]) => editedFields.has(key)),
  );
  const reviewedFields = formData
    .getAll("reviewed_field")
    .filter((value): value is string => typeof value === "string");
  const savedDraft = await serverPatchApi<{ updated_at: string }>(`/valuation-drafts/${draftId}`, {
    assumptions_patch: assumptionsPatch,
    reviewed_fields: reviewedFields,
    expected_updated_at: actionFormString(formData, "draft_updated_at") || null,
  });
  const modelResponse = await serverPostApi<{ id: number }>(`/valuation-drafts/${draftId}/promote`, {
    name: actionFormString(formData, "name"),
    description: actionFormString(formData, "description") || null,
    model_type: actionFormString(formData, "model_type") || "fcff_dcf",
    expected_updated_at: savedDraft.updated_at,
  });
  const model = ((modelResponse as { data?: { id: number } }).data || modelResponse) as { id: number };
  revalidatePath(`/companies/${companyId}/valuation`);
  return model.id;
}
