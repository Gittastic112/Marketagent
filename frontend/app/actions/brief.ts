"use server";

import { revalidatePath } from "next/cache";
import type { DailyBriefSchedule, DailyBriefScheduleRunResult } from "@/lib/api/daily-brief";
import { serverPatchApi, serverPostApi, serverPutApi } from "@/lib/server-api";
import { getRequiredFormId } from "@/lib/form-payloads";
import { logAction, actionFormString, createRecord, formActionError } from "./shared";
import type { FormActionState } from "./shared";

export async function generateDailyBrief() {
  await createRecord("/daily-brief", {}, ["/daily-brief"]);
}

export async function markDailyBriefReviewed(formData: FormData) {
  const id = getRequiredFormId(formData);
  logAction(`marking /daily-brief/${id} as reviewed`);
  await serverPatchApi(`/daily-brief/${id}/review`, {});
  revalidatePath("/daily-brief");
  logAction(`marked /daily-brief/${id} as reviewed; revalidated /daily-brief`);
}

export async function updateDailyBriefScheduleWithState(
  _state: FormActionState,
  formData: FormData,
): Promise<FormActionState> {
  try {
    await serverPutApi<DailyBriefSchedule>("/daily-brief-schedule", {
      enabled: formData.get("enabled") === "on",
      timezone: actionFormString(formData, "timezone") || "UTC",
      local_time: actionFormString(formData, "local_time") || "07:00",
      days_of_week: formData.getAll("days_of_week").map((value) => Number(value)),
    });
    revalidatePath("/daily-brief");
    return { error: null };
  } catch (error) {
    return formActionError(error);
  }
}

export async function runDueDailyBriefSchedule() {
  await serverPostApi<DailyBriefScheduleRunResult>("/daily-brief-schedule/run-due", {});
  revalidatePath("/daily-brief");
  revalidatePath("/data-health");
}
