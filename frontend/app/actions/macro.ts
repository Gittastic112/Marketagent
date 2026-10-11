"use server";

import { revalidatePath } from "next/cache";
import { ApiError } from "@/lib/api/contract";
import { serverDeleteApi, serverPatchApi, serverPostApi } from "@/lib/server-api";
import { getRequiredFormId } from "@/lib/form-payloads";
import { logAction, actionFormString, formActionError } from "./shared";
import type { FormActionState } from "./shared";

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

export async function applyFredMacroRegimeInputWithState(
  _state: FormActionState,
  _formData: FormData,
): Promise<FormActionState> {
  try {
    await serverPostApi("/market-regime/providers/fred/macro/apply", {});
    revalidatePath("/portfolio/regime");
    revalidatePath("/data-health");
    return { error: null };
  } catch (error) {
    return formActionError(error);
  }
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
