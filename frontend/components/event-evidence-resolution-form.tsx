"use client";

import { useActionState } from "react";
import { CheckCircle2 } from "lucide-react";

import {
  resolveEventEvidenceWithState,
  type FormActionState,
} from "@/app/actions";
import type { EventEvidenceSearchMatch } from "@/lib/api";

const initialState: FormActionState = { error: null };

export function EventEvidenceResolutionForm({
  eventId,
  rawDocumentId,
  documentContentHash,
  query,
  match,
}: {
  eventId: number;
  rawDocumentId: number;
  documentContentHash: string;
  query: string;
  match: EventEvidenceSearchMatch;
}) {
  const [state, formAction, pending] = useActionState(
    resolveEventEvidenceWithState,
    initialState,
  );

  return (
    <form action={formAction} style={{ marginTop: "0.75rem" }}>
      <input name="event_id" type="hidden" value={eventId} />
      <input name="raw_document_id" type="hidden" value={rawDocumentId} />
      <input name="start_char" type="hidden" value={match.start_char} />
      <input name="end_char" type="hidden" value={match.end_char} />
      <input name="quote" type="hidden" value={match.quote} />
      <input name="search_query" type="hidden" value={query} />
      <input name="occurrence_index" type="hidden" value={match.occurrence_index} />
      <input name="document_content_hash" type="hidden" value={documentContentHash} />
      {state.error ? <div className="inline-error" role="alert">{state.error}</div> : null}
      <button
        disabled={pending}
        title="Link this exact source span to the event"
        type="submit"
      >
        <CheckCircle2 aria-hidden="true" size={16} />
        {pending ? "Validating..." : "Use exact span"}
      </button>
    </form>
  );
}
