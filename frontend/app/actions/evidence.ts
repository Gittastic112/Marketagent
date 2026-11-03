"use server";

import { revalidatePath } from "next/cache";
import { redirect } from "next/navigation";
import { serverDeleteApi, serverPostApi } from "@/lib/server-api";
import { buildAlertPayload, buildAlertReviewPayload, buildEventPayload, buildRawDocumentPayload, buildRawDocumentMetadataPayload, buildRssIngestionPayload, buildSecFilingIngestionPayload, buildSourcePayload, getRequiredFormId } from "@/lib/form-payloads";
import { logAction, actionFormString, createRecord, deleteRecord, updateRecord, formActionError } from "./shared";
import type { FormActionState } from "./shared";

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
