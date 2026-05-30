"use server";

import { revalidatePath } from "next/cache";

import { ApiError, deleteApi, patchApi, postApi } from "@/lib/api";
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

async function createRecord(path: string, payload: unknown, pages: string[]) {
  logAction(`creating ${path}`);
  await postApi(path, payload);
  for (const page of pages) {
    revalidatePath(page);
  }
  logAction(`created ${path}; revalidated ${pages.join(", ")}`);
}

async function deleteRecord(path: string, formData: FormData, pages: string[]) {
  const id = getRequiredFormId(formData);
  logAction(`deleting ${path}/${id}`);
  await deleteApi(`${path}/${id}`);
  for (const page of pages) {
    revalidatePath(page);
  }
  logAction(`deleted ${path}/${id}; revalidated ${pages.join(", ")}`);
}

async function updateRecord(path: string, formData: FormData, payload: unknown, pages: string[]) {
  const id = getRequiredFormId(formData);
  logAction(`updating ${path}/${id}`);
  await patchApi(`${path}/${id}`, payload);
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
  await createRecord("/companies", buildCompanyPayload(formData), ["/", "/companies"]);
}

export async function createCompanyWithState(_state: FormActionState, formData: FormData): Promise<FormActionState> {
  try {
    await createCompany(formData);
    return { error: null };
  } catch (error) {
    return formActionError(error);
  }
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
    await postApi("/ingest/fred-series", { series_id });
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
  await createRecord("/ingest/sec-filings", buildSecFilingIngestionPayload(formData), ["/", "/documents", "/events", "/alerts", "/daily-brief"]);
}

export async function fetchRecentSecFilings(formData: FormData) {
  await createRecord("/ingest/sec-filings/recent", buildSecFilingIngestionPayload(formData), ["/", "/documents", "/events", "/alerts", "/daily-brief"]);
}

export async function lookupCompanyCik(formData: FormData) {
  const id = getRequiredFormId(formData);
  await postApi(`/companies/${id}/lookup-cik`, {});
  revalidatePath("/companies");
  revalidatePath(`/companies/${id}`);
}

export async function updateRawDocument(formData: FormData) {
  await updateRecord("/raw-documents", formData, buildRawDocumentPayload(formData), ["/", "/documents", "/daily-brief"]);
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

export async function createFinancialStatementPeriod(formData: FormData, companyId: string) {
  await createRecord(`/companies/${companyId}/financial-periods`, buildFinancialStatementPeriodPayload(formData), [`/companies/${companyId}`]);
}

export async function createFinancialMetric(formData: FormData, periodId: string, companyId: string) {
  await createRecord(`/financial-periods/${periodId}/metrics`, buildFinancialMetricPayload(formData), [`/companies/${companyId}`]);
}

export async function deleteFinancialStatementPeriod(formData: FormData, companyId: string) {
  const periodId = getRequiredFormId(formData);
  logAction(`deleting /financial-periods/${periodId}`);
  await deleteApi(`/financial-periods/${periodId}`);
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
  await deleteApi(`/valuation-models/${modelId}`);
  revalidatePath(`/companies/${companyId}`);
  logAction(`deleted /valuation-models/${modelId}; revalidated /companies/${companyId}`);
}

export async function triggerParseFilingSections(rawDocumentId: number) {
  logAction(`triggering parse for /raw-documents/${rawDocumentId}`);
  await postApi(`/raw-documents/${rawDocumentId}/parse`, {});
  revalidatePath(`/documents/${rawDocumentId}/sections`);
  logAction(`triggered parse for /raw-documents/${rawDocumentId}; revalidated /documents/${rawDocumentId}/sections`);
}

export async function triggerGenerateAiSummary(rawDocumentId: number) {
  logAction(`triggering AI summary for /raw-documents/${rawDocumentId}`);
  await postApi(`/raw-documents/${rawDocumentId}/ai-summary`, {});
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
  await createRecord("/narrative-clusters", buildNarrativeClusterPayload(formData), ["/social"]);
}

export async function updateNarrativeCluster(formData: FormData) {
  await updateRecord("/narrative-clusters", formData, buildNarrativeClusterPayload(formData), ["/social"]);
}

export async function deleteNarrativeCluster(formData: FormData) {
  await deleteRecord("/narrative-clusters", formData, ["/social"]);
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
  await createRecord("/narrative-claims", buildNarrativeClaimPayload(formData), ["/social"]);
}

export async function updateNarrativeClaim(formData: FormData) {
  await updateRecord("/narrative-claims", formData, buildNarrativeClaimPayload(formData), ["/social"]);
}

export async function deleteNarrativeClaim(formData: FormData) {
  await deleteRecord("/narrative-claims", formData, ["/social"]);
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
  await createRecord("/narrative-mentions", buildNarrativeMentionPayload(formData), ["/social"]);
}

export async function updateNarrativeMention(formData: FormData) {
  await updateRecord("/narrative-mentions", formData, buildNarrativeMentionPayload(formData), ["/social"]);
}

export async function deleteNarrativeMention(formData: FormData) {
  await deleteRecord("/narrative-mentions", formData, ["/social"]);
}

export async function deleteNarrativeMentionWithState(_state: FormActionState, formData: FormData): Promise<FormActionState> {
  try {
    await deleteNarrativeMention(formData);
    return { error: null };
  } catch (error) {
    return formActionError(error);
  }
}

export async function createThesisAssumption(formData: FormData, thesisNoteId: string) {
  await createRecord(`/thesis-notes/${thesisNoteId}/assumptions`, buildThesisAssumptionPayload(formData), [`/thesis-notes/${thesisNoteId}`]);
}

export async function updateThesisAssumption(formData: FormData, thesisNoteId: string) {
  const id = getRequiredFormId(formData);
  logAction(`updating /thesis-assumptions/${id}`);
  await patchApi(`/thesis-assumptions/${id}`, buildThesisAssumptionPayload(formData));
  revalidatePath(`/thesis-notes/${thesisNoteId}`);
  logAction(`updated /thesis-assumptions/${id}; revalidated /thesis-notes/${thesisNoteId}`);
}

export async function deleteThesisAssumption(formData: FormData, thesisNoteId: string) {
  const id = getRequiredFormId(formData);
  logAction(`deleting /thesis-assumptions/${id}`);
  await deleteApi(`/thesis-assumptions/${id}`);
  revalidatePath(`/thesis-notes/${thesisNoteId}`);
  logAction(`deleted /thesis-assumptions/${id}; revalidated /thesis-notes/${thesisNoteId}`);
}

export async function createThesisChange(formData: FormData, thesisNoteId: string) {
  await createRecord(`/thesis-notes/${thesisNoteId}/changes`, buildThesisChangePayload(formData), [`/thesis-notes/${thesisNoteId}`]);
}

export async function addEventCorroboration(formData: FormData) {
  const eventId = getRequiredFormId(formData, "event_id");
  const payload = { target_event_id: parseInt(getRequiredFormId(formData, "target_event_id"), 10) };
  logAction(`adding corroboration to /events/${eventId}`);
  await postApi(`/events/${eventId}/corroborations`, payload);
  revalidatePath("/events");
  logAction(`added corroboration to /events/${eventId}; revalidated /events`);
}

export async function removeEventCorroboration(formData: FormData) {
  const eventId = getRequiredFormId(formData, "event_id");
  const targetId = getRequiredFormId(formData, "target_event_id");
  logAction(`removing corroboration from /events/${eventId}`);
  await deleteApi(`/events/${eventId}/corroborations/${targetId}`);
  revalidatePath("/events");
  logAction(`removed corroboration from /events/${eventId}; revalidated /events`);
}

export async function addEventContradiction(formData: FormData) {
  const eventId = getRequiredFormId(formData, "event_id");
  const payload = { target_event_id: parseInt(getRequiredFormId(formData, "target_event_id"), 10) };
  logAction(`adding contradiction to /events/${eventId}`);
  await postApi(`/events/${eventId}/contradictions`, payload);
  revalidatePath("/events");
  logAction(`added contradiction to /events/${eventId}; revalidated /events`);
}

export async function removeEventContradiction(formData: FormData) {
  const eventId = getRequiredFormId(formData, "event_id");
  const targetId = getRequiredFormId(formData, "target_event_id");
  logAction(`removing contradiction from /events/${eventId}`);
  await deleteApi(`/events/${eventId}/contradictions/${targetId}`);
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
  await patchApi(`/scoring-config`, payload);
  revalidatePath("/settings");
  logAction(`updated scoring config; revalidated /settings`);
}

export async function createMacroSeries(formData: FormData) {
  const payload = {
    name: getRequiredFormString(formData, "name"),
    description: formData.get("description") as string | null,
    units: formData.get("units") as string | null,
    frequency: formData.get("frequency") as string | null,
  };
  logAction(`creating macro series`);
  await postApi(`/macro`, payload);
  revalidatePath("/macro");
  logAction(`created macro series; revalidated /macro`);
}

export async function createMacroObservation(formData: FormData) {
  const seriesId = getRequiredFormId(formData, "series_id");
  const payload = {
    date_recorded: getRequiredFormString(formData, "date_recorded"),
    value: parseFloat(getRequiredFormString(formData, "value")),
  };
  logAction(`creating macro observation for series ${seriesId}`);
  await postApi(`/macro/${seriesId}/observations`, payload);
  revalidatePath("/macro");
  logAction(`created macro observation for series ${seriesId}; revalidated /macro`);
}

export async function deleteMacroSeriesWithState(state: ActionState, formData: FormData) {
  const id = getRequiredFormId(formData, "id");
  try {
    logAction(`deleting macro series ${id}`);
    await deleteApi(`/macro/${id}`);
    revalidatePath("/macro");
    logAction(`deleted macro series ${id}; revalidated /macro`);
    return { success: true };
  } catch (error) {
    return { success: false, error: error instanceof Error ? error.message : "Unknown error" };
  }
}

export async function createExposureTag(formData: FormData) {
  const payload = {
    name: getRequiredFormString(formData, "name"),
    description: formData.get("description") as string | null,
  };
  logAction(`creating exposure tag`);
  await postApi(`/exposure-tags`, payload);
  revalidatePath("/companies");
  logAction(`created exposure tag; revalidated /companies`);
}

export async function deleteExposureTagWithState(state: ActionState, formData: FormData) {
  const id = getRequiredFormId(formData, "id");
  try {
    logAction(`deleting exposure tag ${id}`);
    await deleteApi(`/exposure-tags/${id}`);
    revalidatePath("/companies");
    logAction(`deleted exposure tag ${id}; revalidated /companies`);
    return { success: true };
  } catch (error) {
    return { success: false, error: error instanceof Error ? error.message : "Unknown error" };
  }
}

export async function addCompanyExposureTag(formData: FormData) {
  const companyId = getRequiredFormId(formData, "company_id");
  const payload = { tag_id: parseInt(getRequiredFormId(formData, "tag_id"), 10) };
  logAction(`adding exposure tag to /companies/${companyId}`);
  await postApi(`/companies/${companyId}/exposure-tags`, payload);
  revalidatePath(`/companies`);
  logAction(`added exposure tag to /companies/${companyId}; revalidated /companies`);
}

export async function removeCompanyExposureTag(formData: FormData) {
  const companyId = getRequiredFormId(formData, "company_id");
  const tagId = getRequiredFormId(formData, "tag_id");
  logAction(`removing exposure tag from /companies/${companyId}`);
  await deleteApi(`/companies/${companyId}/exposure-tags/${tagId}`);
  revalidatePath(`/companies`);
  logAction(`removed exposure tag from /companies/${companyId}; revalidated /companies`);
}
