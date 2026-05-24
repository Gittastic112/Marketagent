"use server";

import { revalidatePath } from "next/cache";

import { deleteApi, patchApi, postApi } from "@/lib/api";
import {
  buildAlertPayload,
  buildCompanyPayload,
  buildEventPayload,
  buildRawDocumentPayload,
  buildRssIngestionPayload,
  buildSecFilingIngestionPayload,
  buildSourcePayload,
  buildThesisNotePayload,
  getRequiredFormId
} from "@/lib/form-payloads";

const DEBUG_LOGS_ENABLED = process.env.NEXT_PUBLIC_DEBUG_LOGS !== "false";

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

export async function createCompany(formData: FormData) {
  await createRecord("/companies", buildCompanyPayload(formData), ["/", "/companies"]);
}

export async function updateCompany(formData: FormData) {
  await updateRecord("/companies", formData, buildCompanyPayload(formData), ["/", "/companies"]);
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
  await createRecord("/ingest/rss", buildRssIngestionPayload(formData), ["/", "/documents", "/daily-brief"]);
}

export async function importSecFilings(formData: FormData) {
  await createRecord("/ingest/sec-filings", buildSecFilingIngestionPayload(formData), ["/", "/documents", "/daily-brief"]);
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

export async function updateAlert(formData: FormData) {
  await updateRecord("/alerts", formData, buildAlertPayload(formData), ["/", "/alerts", "/daily-brief"]);
}

export async function createThesisNote(formData: FormData) {
  await createRecord("/thesis-notes", buildThesisNotePayload(formData), ["/", "/thesis-notes", "/daily-brief"]);
}

export async function updateThesisNote(formData: FormData) {
  await updateRecord("/thesis-notes", formData, buildThesisNotePayload(formData), ["/", "/thesis-notes", "/daily-brief"]);
}

export async function deleteCompany(formData: FormData) {
  await deleteRecord("/companies", formData, ["/", "/companies", "/documents", "/events", "/alerts", "/thesis-notes"]);
}

export async function deleteSource(formData: FormData) {
  await deleteRecord("/sources", formData, ["/sources", "/documents"]);
}

export async function deleteRawDocument(formData: FormData) {
  await deleteRecord("/raw-documents", formData, ["/", "/documents", "/events", "/daily-brief"]);
}

export async function deleteEvent(formData: FormData) {
  await deleteRecord("/events", formData, ["/", "/events", "/alerts", "/daily-brief"]);
}

export async function deleteAlert(formData: FormData) {
  await deleteRecord("/alerts", formData, ["/", "/alerts", "/daily-brief"]);
}

export async function deleteThesisNote(formData: FormData) {
  await deleteRecord("/thesis-notes", formData, ["/", "/thesis-notes", "/daily-brief"]);
}

export async function saveDailyBrief() {
  await createRecord("/daily-brief", {}, ["/daily-brief"]);
}
