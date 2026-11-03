"use client";

import { useAutofillDraft } from "./use-autofill-draft";
import type { AutofillDraftReviewProps } from "./use-autofill-draft";
import { AutofillDraftReviewView } from "./autofill-draft-view";

export function AutofillDraftReview(props: AutofillDraftReviewProps) {
  return <AutofillDraftReviewSession key={`${props.company.id}:${props.draftId}`} {...props} />;
}

function AutofillDraftReviewSession(props: AutofillDraftReviewProps) {
  const state = useAutofillDraft(props);
  return <AutofillDraftReviewView {...state} />;
}
