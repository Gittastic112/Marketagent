"use client";

import { useActionState } from "react";

import type { FormActionState } from "@/app/actions";

const initialState: FormActionState = { error: null };

type DeleteRecordAction = (state: FormActionState, formData: FormData) => Promise<FormActionState>;

export function DeleteRecordForm({
  action,
  recordId,
  label = "Delete"
}: {
  action: DeleteRecordAction;
  recordId: number;
  label?: string;
}) {
  const [state, formAction, pending] = useActionState(action, initialState);

  return (
    <form action={formAction} className="row-action">
      <input name="id" type="hidden" value={recordId} />
      {state.error ? (
        <div className="inline-error" role="alert">
          {state.error}
        </div>
      ) : null}
      <button className="danger-button" disabled={pending} type="submit">
        {pending ? "Deleting..." : label}
      </button>
    </form>
  );
}
