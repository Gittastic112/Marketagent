"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import Link from "next/link";
import { Panel } from "@/components/page";
import { createResearchRun, getResearchCapabilities, getResearchRun, listResearchRuns, type ResearchKind, type ResearchRequestByKind, type ResearchRun } from "@/lib/api/research-lab";
import { createRequestGate } from "@/lib/latest-request";
import { useLatestResource } from "@/lib/use-latest-resource";
import { ResearchRunForm, RESEARCH_KIND_LABELS } from "./research-run-form";
import { ResearchRunResult } from "./research-run-result";
import { AdapterFailure } from "./adapter-failure";

export function ResearchWorkbench() {
  const [kind, setKind] = useState<ResearchKind>("allocation");
  const [busy, setBusy] = useState(false);
  const [run, setRun] = useState<ResearchRun | null>(null);
  const [error, setError] = useState<Error | null>(null);
  const [historyCursors, setHistoryCursors] = useState<number[]>([]);
  const beforeRunId = historyCursors.at(-1);
  const resultRegion = useRef<HTMLDivElement>(null);
  const requests = useMemo(createRequestGate, []);
  const capabilities = useLatestResource(useCallback(getResearchCapabilities, []));
  const history = useLatestResource(useCallback(() => listResearchRuns(beforeRunId), [beforeRunId]));
  useEffect(() => () => requests.invalidate(), [requests]);
  useEffect(() => { if (run) resultRegion.current?.focus(); }, [run]);

  async function submit<K extends ResearchKind>(selected: K, payload: ResearchRequestByKind[K]) {
    const current = requests.begin();
    setBusy(true); setError(null); setRun(null);
    try {
      const result = await createResearchRun(selected, payload);
      if (current()) {
        setRun(result);
        setHistoryCursors([]);
        if (beforeRunId === undefined) void history.reload().catch(() => {});
      }
    } catch (failure) {
      if (current()) setError(failure instanceof Error ? failure : new Error("Research could not be completed. Check adapter configuration and inputs."));
    } finally { if (current()) setBusy(false); }
  }
  async function loadRun(id: number) {
    const current = requests.begin();
    setBusy(true); setError(null); setRun(null);
    try {
      const result = await getResearchRun(id);
      if (current()) {
        setKind(result.kind);
        setRun(result);
      }
    }
    catch (failure) { if (current()) setError(failure instanceof Error ? failure : new Error("The saved research run is unavailable.")); }
    finally { if (current()) setBusy(false); }
  }

  return <div className="research-lab-workbench">
    <Panel title="Research adapters" collapsible>
      {capabilities.status === "loading" ? <p role="status">Checking installed adapters…</p> : capabilities.status === "error" ? <p role="alert">Adapter status unavailable: {capabilities.error}</p> : capabilities.data && <>
        <div className="table-wrap" role="region" aria-label="Research adapter availability" tabIndex={0}><table><thead><tr><th scope="col">Adapter</th><th scope="col">Status</th><th scope="col">Version / requirement</th></tr></thead>
          <tbody>{capabilities.data.adapters.map(adapter => <tr key={adapter.id}><th scope="row">{adapter.label}</th><td>{adapter.available ? "Available" : "Not configured"}</td><td>{adapter.version || adapter.reason || "Version not reported"}</td></tr>)}</tbody></table></div>
        {(capabilities.data.warnings ?? []).map((warning, index) => <p key={index}>{warning}</p>)}
      </>}
      <button type="button" className="secondary-button" onClick={() => void capabilities.reload().catch(() => {})} disabled={capabilities.status === "loading"}>Refresh adapter status</button>
    </Panel>
    <Panel title="Portfolio and research laboratory">
      <p className="basis-note">User-supplied datasets remain unverified. Results are hypothetical Calculations and Estimates, not trading instructions. Actual holdings, reviewed valuation inputs and source approvals are unchanged.</p>
      <div className="button-row" role="group" aria-label="Research task">
        {(Object.entries(RESEARCH_KIND_LABELS) as Array<[ResearchKind, string]>).map(([value, label]) => <button type="button" key={value} className="secondary-button" disabled={busy} aria-pressed={kind === value}
          onClick={() => {
            if (value !== kind) {
              requests.invalidate();
              setRun(null);
              setError(null);
              setKind(value);
            }
          }}>{label}</button>)}
      </div>
      <ResearchRunForm key={kind} kind={kind} busy={busy} onSubmit={submit} />
      {busy && <p role="status">Waiting for the saved research result…</p>}
      <AdapterFailure error={error} />
      {run && <div ref={resultRegion} tabIndex={-1}><ResearchRunResult key={run.run_id} run={run} /></div>}
    </Panel>
    <Panel title="Saved research runs" collapsible>
      <p>Page {historyCursors.length + 1}, up to 25 runs, newest first. Older pages retain their position when new runs arrive.</p>
      {history.status === "loading" ? <p role="status">Loading saved research…</p> : history.status === "error" ? <p role="alert">Saved runs unavailable: {history.error}</p>
        : history.data?.length ? <div className="table-wrap" role="region" aria-label="Saved research runs" tabIndex={0}><table>
          <thead><tr><th scope="col">Run</th><th scope="col">Kind</th><th scope="col">Status</th><th scope="col">Created</th><th scope="col">Open</th></tr></thead>
          <tbody>{history.data.map(saved => <tr key={saved.run_id}><th scope="row">#{saved.run_id}</th><td>{saved.kind}</td><td>{saved.status}</td><td>{saved.created_at}</td>
            <td>{["complete", "success"].includes(saved.status)
              ? <button type="button" className="secondary-button" disabled={busy} onClick={() => void loadRun(saved.run_id)}>Open run {saved.run_id}</button>
              : <Link href="/data-health" prefetch={false}>Inspect processing history for run {saved.run_id}</Link>}</td></tr>)}</tbody>
        </table></div> : <p>{beforeRunId ? "No older research runs." : "No saved research runs. Submit an explicit dataset to begin."}</p>}
      <div className="button-row">
        <button type="button" className="secondary-button" disabled={busy || history.status === "loading" || !historyCursors.length} onClick={() => setHistoryCursors(cursors => cursors.slice(0, -1))}>Newer research runs</button>
        <button type="button" className="secondary-button" disabled={busy || history.status !== "ready" || history.data?.length !== 25} onClick={() => {
          const lastId = history.data?.at(-1)?.run_id;
          if (lastId) setHistoryCursors(cursors => [...cursors, lastId]);
        }}>Older research runs</button>
        <button type="button" className="secondary-button" disabled={busy || history.status === "loading"} onClick={() => {
          setHistoryCursors([]);
          if (beforeRunId === undefined) void history.reload().catch(() => {});
        }}>Refresh saved runs</button>
      </div>
    </Panel>
  </div>;
}
