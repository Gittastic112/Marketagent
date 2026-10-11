import "server-only";

import { revalidatePath } from "next/cache";
import { ApiError } from "@/lib/api/contract";
import { serverDeleteApi, serverPatchApi, serverPostApi } from "@/lib/server-api";
import { getRequiredFormId } from "@/lib/form-payloads";

const DEBUG_LOGS_ENABLED = process.env.NEXT_PUBLIC_DEBUG_LOGS === "true";

export type FormActionState = {
  error: string | null;
};

export function logAction(message: string) {
  if (DEBUG_LOGS_ENABLED) {
    console.log(`[action] ${message}`);
  }
}

export function actionFormString(formData: FormData, key: string): string {
  const value = formData.get(key);
  return typeof value === "string" ? value.trim() : "";
}

export async function createRecord(path: string, payload: unknown, pages: string[]) {
  logAction(`creating ${path}`);
  await serverPostApi(path, payload);
  for (const page of pages) {
    revalidatePath(page);
  }
  logAction(`created ${path}; revalidated ${pages.join(", ")}`);
}

export async function deleteRecord(path: string, formData: FormData, pages: string[]) {
  const id = getRequiredFormId(formData);
  logAction(`deleting ${path}/${id}`);
  await serverDeleteApi(`${path}/${id}`);
  for (const page of pages) {
    revalidatePath(page);
  }
  logAction(`deleted ${path}/${id}; revalidated ${pages.join(", ")}`);
}

export async function updateRecord(path: string, formData: FormData, payload: unknown, pages: string[]) {
  const id = getRequiredFormId(formData);
  logAction(`updating ${path}/${id}`);
  await serverPatchApi(`${path}/${id}`, payload);
  for (const page of pages) {
    revalidatePath(page);
  }
  logAction(`updated ${path}/${id}; revalidated ${pages.join(", ")}`);
}

export function formActionError(error: unknown): FormActionState {
  if (error instanceof ApiError) {
    return { error: error.message };
  }
  return { error: "The request failed. Check the fields and try again." };
}
