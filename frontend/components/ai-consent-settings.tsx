"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { Panel } from "@/components/page";
import {
  fetchAIConsent, fetchAIConsentHistory, saveAIConsentDecision,
  type AIConsentAction, type AIConsentDecision, type AIConsentState,
} from "@/lib/api/ai-consent";
import { createRequestGate } from "@/lib/latest-request";
import { useLatestResource } from "@/lib/use-latest-resource";

const statusLabels = {
  not_granted: "Not allowed", granted: "Allowed", refused: "Refused", revoked: "Revoked", outdated: "Review required",
};

export function AIConsentSettings() {
  const loader = useCallback(async () => {
    const [overview, history] = await Promise.all([fetchAIConsent(), fetchAIConsentHistory()]);
    return {overview, history};
  }, []);
  const resource = useLatestResource(loader);
  const [confirmed, setConfirmed] = useState<Record<string, boolean>>({});
  const [pending, setPending] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const [older, setOlder] = useState<AIConsentDecision[]>([]);
  const [olderCursor, setOlderCursor] = useState<number | null | undefined>(undefined);
  const busy = useRef(false);
  const gate = useMemo(createRequestGate, []);
  useEffect(() => () => gate.invalidate(), [gate]);

  async function reload() {
    setConfirmed({}); setOlder([]); setOlderCursor(undefined);
    await resource.reload();
  }

  async function decide(action: AIConsentAction, state: AIConsentState) {
    if (busy.current || resource.status !== "ready" || (state === "granted" && !confirmed[action.action_key])) return;
    const current = gate.begin();
    busy.current = true; setPending(true); setError(null); setNotice(null);
    try {
      await saveAIConsentDecision({provider_name: action.provider_name, action_key: action.action_key,
        state, disclosure_version: action.disclosure_version, scope_hash: action.scope_hash,
        expected_revision: action.current_revision});
      if (!current()) return;
      await reload();
      if (current()) setNotice(`${action.label}: ${statusLabels[state]}. This saved a permission decision; it did not send data to AI.`);
    } catch (failure) {
      if (!current()) return;
      const message = failure instanceof Error ? failure.message : "Permission could not be saved.";
      // Fetch server truth after a stale-tab conflict or an uncertain write response.
      try {await reload();} catch { /* The resource exposes unavailable state. */ }
      if (current()) setError(message);
    } finally {
      if (current()) {busy.current = false; setPending(false);}
    }
  }

  async function loadOlder(cursor: number) {
    if (busy.current) return;
    const current = gate.begin();
    busy.current = true; setPending(true); setError(null);
    try {
      const page = await fetchAIConsentHistory(cursor);
      if (current()) {setOlder(rows => [...rows, ...page.items]); setOlderCursor(page.next_cursor);}
    } catch (failure) {
      if (current()) setError(failure instanceof Error ? failure.message : "Older decisions could not be loaded.");
    } finally {
      if (current()) {busy.current = false; setPending(false);}
    }
  }

  const data = resource.status === "ready" ? resource.data : null;
  const cursor = olderCursor === undefined ? data?.history.next_cursor : olderCursor;
  const history = data ? [...data.history.items, ...older] : [];
  return <section id="ai-permissions" aria-label="AI permissions" style={{minWidth: 0, overflowWrap: "anywhere"}}>
    <Panel title="AI permissions">
      <p>Choose which actions may send your data to Gemini. Nothing is allowed until you explicitly grant it here.
        Each feature still asks you to acknowledge its disclosure when you use it.</p>
      <p>Revoking stops future sends. It cannot recall information already sent or cancel an already dispatched request.
        Mock Data stays local and does not grant external access.</p>
      {resource.status === "loading" && <p role="status">Loading current permissions…</p>}
      {resource.status === "error" && <p role="alert">Permissions are unavailable. {resource.error}</p>}
      {error && <p role="alert">{error}</p>}
      {notice && <p role="status">{notice}</p>}
      <button type="button" className="secondary-button" disabled={pending || resource.status === "loading"}
        onClick={() => {setError(null); setNotice(null); void reload().catch(() => {});}}>Reload permissions</button>
      {data && <div className="stack" style={{marginTop: "1rem"}}>
        {data.overview.actions.length === 0 && <p>No external AI actions are available.</p>}
        {data.overview.actions.map(action => <section key={action.action_key} aria-label={action.label} className="basis-note">
          <h3>{action.label}</h3>
          <p><strong>{statusLabels[action.state]}</strong> · Provider: Gemini · Disclosure: {action.disclosure_version}</p>
          <p>{action.description}</p>
          {action.latest_decision && <p>Last decision: {new Date(action.latest_decision.created_at).toLocaleString()}.</p>}
          <label className="checkbox-label" style={{textTransform: "none"}}>
            <input type="checkbox" checked={Boolean(confirmed[action.action_key])} disabled={pending}
              onChange={event => setConfirmed(values => ({...values, [action.action_key]: event.target.checked}))} />
            I allow Gemini to receive this action&apos;s listed data on future requests that I explicitly acknowledge.
          </label>
          <div style={{display: "flex", flexWrap: "wrap", gap: "0.5rem", marginTop: "0.75rem"}}>
            <button type="button" disabled={pending || action.state === "granted" || !confirmed[action.action_key]}
              onClick={() => void decide(action, "granted")}>Allow</button>
            <button type="button" className="secondary-button" disabled={pending || action.state === "refused"}
              onClick={() => void decide(action, "refused")}>Refuse</button>
            <button type="button" className="secondary-button" disabled={pending || !["granted", "outdated"].includes(action.state)}
              onClick={() => void decide(action, "revoked")}>Revoke</button>
          </div>
        </section>)}
        <details><summary>Permission history</summary>
          {history.length === 0 ? <p>No decisions recorded. Previous AI output does not grant permission.</p> :
            <ol>{history.map(row => <li key={row.id} style={{marginBottom: "0.75rem"}}>
              <strong>{data.overview.actions.find(action => action.action_key === row.action_key)?.label || row.action_key}</strong>: {statusLabels[row.state]}
              <p>{row.provider_name} · {new Date(row.created_at).toLocaleString()} · Decision #{row.id}, revision {row.revision}, disclosure {row.disclosure_version}.</p>
              <details><summary>Recorded data scope</summary><p>{row.external_data_classes.join(", ")}</p><p>Scope fingerprint: {row.scope_hash}</p></details>
            </li>)}</ol>}
          {cursor != null && <button type="button" className="secondary-button" disabled={pending} onClick={() => void loadOlder(cursor)}>Load older decisions</button>}
        </details>
        <details><summary>Permission limits</summary><ul>{data.overview.limitations.map(item => <li key={item}>{item}</li>)}</ul></details>
      </div>}
    </Panel>
  </section>;
}
