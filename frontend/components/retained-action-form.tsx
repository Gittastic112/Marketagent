"use client";

import { useEffect, useMemo, useRef, useState, useTransition, type ComponentProps, type FormEvent } from "react";
import { createRequestGate } from "@/lib/latest-request";

type Props = Omit<ComponentProps<"form">, "action" | "onSubmit"> & {
  action: (data: FormData) => Promise<unknown>;
  label: string;
  resetOnSuccess?: boolean;
  successMessage?: string;
};

/** Preserve entries on failure and serialize server actions without changing their contracts. */
export function RetainedActionForm({action, label, resetOnSuccess = false, successMessage = "Completed.", children, ...props}: Props) {
  const [pending, startTransition] = useTransition();
  const [error, setError] = useState<string | null>(null);
  const [saved, setSaved] = useState(false);
  const busy = useRef(false);
  const gate = useMemo(createRequestGate, []);
  useEffect(() => () => gate.invalidate(), [gate]);
  function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (busy.current) return;
    const form = event.currentTarget;
    const data = new FormData(form);
    const current = gate.begin();
    busy.current = true; setError(null); setSaved(false);
    startTransition(async () => {
      try {
        const result = await action(data);
        if (!current()) return;
        const failure = result && typeof result === "object" && "error" in result && typeof result.error === "string" ? result.error : null;
        setError(failure);
        if (!failure) {if (resetOnSuccess) form.reset(); setSaved(true);}
      } catch {
        if (current()) setError("Request unavailable. Your entries are retained. Check whether it completed before retrying.");
      } finally {busy.current = false;}
    });
  }
  return <form {...props} onSubmit={submit} aria-label={label} onChange={() => setSaved(false)}>
    <fieldset aria-label={label} disabled={pending} style={{display: "contents"}}>
      {children}
    </fieldset>
    {error && <p role="alert">{error}</p>}
    {pending && <p role="status">Waiting for confirmation…</p>}
    {saved && <p role="status">{successMessage}</p>}
  </form>;
}
