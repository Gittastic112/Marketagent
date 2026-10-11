"use server";

import { revalidatePath } from "next/cache";
import { serverDeleteApi, serverPatchApi, serverPostApi } from "@/lib/server-api";
import { buildThesisNotePayload, buildSocialPostPayload, buildSentimentScorePayload, buildNarrativeClusterPayload, buildNarrativeClaimPayload, buildNarrativeMentionPayload, buildThesisAssumptionPayload, buildThesisChangePayload, getRequiredFormId } from "@/lib/form-payloads";
import { logAction, createRecord, deleteRecord, updateRecord, formActionError } from "./shared";
import type { FormActionState } from "./shared";

export async function createThesisNote(formData: FormData) {
  await createRecord("/thesis-notes", buildThesisNotePayload(formData), ["/", "/thesis-notes", "/daily-brief"]);
}

export async function updateThesisNote(formData: FormData) {
  await updateRecord("/thesis-notes", formData, buildThesisNotePayload(formData), ["/", "/thesis-notes", "/daily-brief"]);
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
