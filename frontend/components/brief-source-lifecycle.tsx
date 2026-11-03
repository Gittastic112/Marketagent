"use client";

import { useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { setBriefSourceArchived, type BriefSource } from "@/lib/api/brief-sources";

type Props = {
  source: BriefSource;
  disabled?: boolean;
  onBusyChange?: (busy: boolean) => void;
  onChanged?: (message: string) => void;
};

export function BriefSourceLifecycle({ source, disabled, onBusyChange, onChanged }: Props) {
  const router = useRouter();
  const [updated, setUpdated] = useState<BriefSource | null>(null);
  const [pending, setPending] = useState(false);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");
  const mounted = useRef(true);
  const inFlight = useRef(false);
  const current = updated?.id === source.id && updated.lifecycle_version > source.lifecycle_version ? updated : source;
  const archived = Boolean(current.archived_at);
  useEffect(() => { mounted.current = true; return () => { mounted.current = false; }; }, []);

  async function change() {
    if (inFlight.current) return;
    inFlight.current = true;
    setPending(true); setError(""); setMessage(""); onBusyChange?.(true);
    try {
      const result = await setBriefSourceArchived(current.id, !archived, current.lifecycle_version);
      if (!mounted.current) return;
      setUpdated(result);
      const notice = result.archived_at ? "Source archived. Original evidence and findings are retained. Find it using the Archived filter."
        : "Source restored to the active inbox. Its evidence and review status are unchanged.";
      setMessage(notice);
      if (onChanged) onChanged(notice); else router.refresh();
    } catch (e) {
      if (mounted.current) setError(e instanceof Error ? e.message : "Source organization could not be changed. Reload to check its current state.");
    } finally {
      inFlight.current = false;
      if (mounted.current) setPending(false);
      onBusyChange?.(false);
    }
  }

  return <div className="brief-lifecycle">
    <p className="muted">{archived
      ? `Archived ${new Date(current.archived_at!).toLocaleString("en-US", { timeZone: "UTC", timeZoneName: "short" })}. Evidence is retained; archiving is not deletion or approval.`
      : "Archive to remove this source from the active inbox. You can restore it later; evidence and findings are kept."}</p>
    <button className="btn btn-secondary" disabled={disabled || pending} onClick={() => void change()}>
      {pending ? "Updating source…" : archived ? "Restore source" : "Archive source"}
    </button>
    {message && <p role="status">{message}</p>}
    {error && <div role="alert" className="basis-note">{error} <button className="btn btn-secondary" disabled={pending || disabled}
      onClick={() => { setUpdated(null); setError(""); if (onChanged) onChanged("Reloaded the source list. Check its current state before retrying."); else router.refresh(); }}>Reload source state</button></div>}
  </div>;
}
