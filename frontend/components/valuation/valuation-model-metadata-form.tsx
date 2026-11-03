"use client";

import { useActionState } from "react";

import type { FormActionState } from "@/app/actions";

const initialState: FormActionState = { error: null };

type MetadataAction = (state: FormActionState, formData: FormData) => Promise<FormActionState>;

export function ValuationModelMetadataForm({
  action,
  name,
  description,
}: {
  action: MetadataAction;
  name: string;
  description: string | null;
}) {
  const [state, formAction, pending] = useActionState(action, initialState);

  return (
    <form action={formAction} style={{ display: "grid", gap: "1rem", maxWidth: "720px" }}>
      <label>
        <span style={{ display: "block", fontWeight: 600, marginBottom: "0.35rem" }}>Model name</span>
        <input name="name" defaultValue={name} required />
      </label>
      <label>
        <span style={{ display: "block", fontWeight: 600, marginBottom: "0.35rem" }}>Description</span>
        <textarea name="description" defaultValue={description ?? ""} rows={2} />
      </label>
      {state.error ? <div className="inline-error" role="alert">{state.error}</div> : null}
      <div>
        <button type="submit" className="secondary-button" disabled={pending}>
          {pending ? "Saving..." : "Save model details"}
        </button>
      </div>
    </form>
  );
}
