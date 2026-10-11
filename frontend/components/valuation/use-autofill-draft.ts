"use client";

import { createRequestGate } from "@/lib/latest-request";

import { useEffect, useMemo, useState } from "react";
import { fetchApi } from "@/lib/api/transport";
import type { ValuationSetupDraft } from "@/lib/api/valuation-drafts";
import type { AutofillAssumptionDraft } from "@/lib/api/valuation-drafts";
import type { Company } from "@/lib/api/companies";
import { archiveValuationDraft, refreshValuationDraft, resetValuationDraftFields, updateValuationDraft } from "@/lib/api/valuation-drafts";
import { reviewFieldValueIsValid, unresolvedReviewFields } from "@/lib/autofill-review";
import { FIELD_GROUPS } from "./autofill-draft-fields";

export type AutofillDraftReviewProps = {
  company: Company;
  draft: AutofillAssumptionDraft;
  draftId: number;
  initialReviewedFields: string[];
  initialEditedFields: string[];
  initialUpdatedAt: string;
  action: (formData: FormData) => void | Promise<void>;
};

export function useAutofillDraft({
  company,
  draft,
  draftId,
  initialReviewedFields,
  initialEditedFields,
  initialUpdatedAt,
  action,
}: AutofillDraftReviewProps) {
  const requests = useMemo(createRequestGate, []);
  useEffect(() => () => requests.invalidate(), [requests]);
  useEffect(() => {
    const revealField = () => {
      const key = window.location.hash.slice(1);
      const allowed = key === "revenue-growth" || FIELD_GROUPS.some(group => group.fields.some(field => field.key === key));
      if (!allowed) return;
      const field = document.getElementById(key);
      let parent = field?.parentElement;
      while (parent) {
        if (parent instanceof HTMLDetailsElement) parent.open = true;
        parent = parent.parentElement;
      }
      field?.scrollIntoView({ block: "center" });
      field?.focus({ preventScroll: true });
    };
    revealField();
    window.addEventListener("hashchange", revealField);
    return () => window.removeEventListener("hashchange", revealField);
  }, [draftId]);

  const [values, setValues] = useState<Record<string, unknown>>({ ...draft.assumptions });

  const [reviewedFields, setReviewedFields] = useState<Set<string>>(new Set(initialReviewedFields));

  const [editedFields, setEditedFields] = useState<Set<string>>(new Set(initialEditedFields));

  const [sourceMetadata, setSourceMetadata] = useState(draft.source_metadata);

  const [provenance, setProvenance] = useState(draft.provenance);

  const [warnings, setWarnings] = useState(draft.warnings);

  const [saveState, setSaveState] = useState<"idle" | "saving" | "saved" | "error">("idle");

  const [saveMessage, setSaveMessage] = useState("");

  const [pipelineBusy, setPipelineBusy] = useState(false);

  const [archiveConfirmationOpen, setArchiveConfirmationOpen] = useState(false);

  const [defaultsAccepted, setDefaultsAccepted] = useState(false);

  const [bulkAcceptedFields, setBulkAcceptedFields] = useState<Set<string>>(new Set());

  const [updatedAt, setUpdatedAt] = useState(initialUpdatedAt);

  const [growthText, setGrowthText] = useState(
    JSON.stringify(draft.assumptions.revenue_growth_years_json ?? {}, null, 2),
  );

  const reviewFields = useMemo(
    () => new Set(sourceMetadata.review_fields),
    [sourceMetadata.review_fields],
  );

  const unresolvedFields = unresolvedReviewFields(
    sourceMetadata,
    reviewedFields,
    values,
  );

  const invalidDefaultFields = [...reviewFields].filter(
    (field) => !reviewFieldValueIsValid(field, values[field]),
  );

  const promotionReady = unresolvedFields.length === 0;

  function updateValue(key: string, nextValue: unknown) {
    setValues((current) => ({ ...current, [key]: nextValue }));
    setSaveState("idle");
    setSaveMessage("");
    setDefaultsAccepted(false);
    setBulkAcceptedFields(new Set());
    setEditedFields((current) => new Set(current).add(key));
    setReviewedFields((current) => {
      const next = new Set(current);
      next.delete(key);
      return next;
    });
  }

  function acceptCurrentDefaults(checked: boolean) {
    setDefaultsAccepted(checked);
    if (checked) {
      const newlyAccepted = [...reviewFields].filter(
        (field) => reviewFieldValueIsValid(field, values[field]) && !reviewedFields.has(field),
      );
      setBulkAcceptedFields(new Set(newlyAccepted));
      setReviewedFields((current) => new Set([...current, ...newlyAccepted]));
      return;
    }
    setReviewedFields((current) => {
      const next = new Set(current);
      bulkAcceptedFields.forEach((field) => next.delete(field));
      return next;
    });
    setBulkAcceptedFields(new Set());
  }

  function toggleReviewed(key: string, checked: boolean) {
    setReviewedFields((current) => {
      const next = new Set(current);
      if (checked) next.add(key);
      else next.delete(key);
      return next;
    });
  }

  async function persistDraft(isCurrent: () => boolean = requests.begin()) {
    const assumptionsPatch = Object.fromEntries(
      [...editedFields].map((field) => [field, values[field]]),
    );
    const saved = await updateValuationDraft(
      draftId,
      assumptionsPatch,
      [...reviewedFields],
      updatedAt,
    );
    if (!isCurrent()) throw new Error("Draft request is no longer active");
    setUpdatedAt(saved.updated_at);
    setSourceMetadata(saved.source_metadata_json);
    setProvenance(saved.provenance_json);
    setWarnings(saved.warnings_json);
    return saved;
  }

  async function saveDraft() {
    const isCurrent = requests.begin();
    setSaveState("saving");
    setSaveMessage("");
    try {
      await persistDraft(isCurrent);
      if (!isCurrent()) return;
      setSaveState("saved");
      setSaveMessage("Draft saved");
    } catch (error) {
      if (!isCurrent()) return;
      setSaveState("error");
      setSaveMessage(error instanceof Error ? error.message : "Save failed");
    }
  }

  async function loadRefreshedDraft() {
    const isCurrent = requests.begin();
    const saved = await fetchApi<ValuationSetupDraft>(`/valuation-drafts/${draftId}`);
    if (!isCurrent()) return;
    setValues(saved.assumptions_json);
    setUpdatedAt(saved.updated_at);
    setReviewedFields(new Set(saved.reviewed_fields_json));
    setEditedFields(new Set(saved.edited_fields_json));
    setSourceMetadata(saved.source_metadata_json);
    setProvenance(saved.provenance_json);
    setWarnings(saved.warnings_json);
    setDefaultsAccepted(false);
    setBulkAcceptedFields(new Set());
    setSaveState("idle");
    setSaveMessage("Source refresh finished. Review the updated draft and any incomplete steps.");
  }

  async function refreshSources() {
    const isCurrent = requests.begin();
    setSaveState("saving");
    setSaveMessage("");
    try {
      const saved = await persistDraft(isCurrent);
      if (!isCurrent()) return;
      await refreshValuationDraft(draftId, saved.updated_at);
      if (!isCurrent()) return;
      window.location.reload();
    } catch (error) {
      if (!isCurrent()) return;
      setSaveState("error");
      setSaveMessage(error instanceof Error ? error.message : "Refresh failed");
    }
  }

  async function resetField(key: string) {
    const isCurrent = requests.begin();
    setSaveState("saving");
    setSaveMessage("");
    try {
      const saved = await persistDraft(isCurrent);
      if (!isCurrent()) return;
      await resetValuationDraftFields(draftId, [key], saved.updated_at);
      if (!isCurrent()) return;
      window.location.reload();
    } catch (error) {
      if (!isCurrent()) return;
      setSaveState("error");
      setSaveMessage(error instanceof Error ? error.message : "Reset failed");
    }
  }

  async function archiveDraft() {
    const isCurrent = requests.begin();
    setSaveState("saving");
    setSaveMessage("");
    try {
      await archiveValuationDraft(draftId, updatedAt);
      if (!isCurrent()) return;
      window.location.assign(`/companies/${company.id}/valuation`);
    } catch (error) {
      if (!isCurrent()) return;
      setSaveState("error");
      setSaveMessage(error instanceof Error ? error.message : "Archive failed");
      setArchiveConfirmationOpen(false);
    }
  }
  return { company, draft, action, values, reviewedFields, editedFields, sourceMetadata, provenance, warnings, saveState, saveMessage, pipelineBusy, setPipelineBusy, archiveConfirmationOpen, setArchiveConfirmationOpen, defaultsAccepted, updatedAt, growthText, setGrowthText, reviewFields, unresolvedFields, invalidDefaultFields, promotionReady, updateValue, acceptCurrentDefaults, toggleReviewed, persistDraft, saveDraft, loadRefreshedDraft, refreshSources, resetField, archiveDraft };
}
