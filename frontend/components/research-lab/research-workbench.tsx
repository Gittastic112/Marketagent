"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { Panel } from "@/components/page";
import { createResearchRun, getResearchCapabilities, getResearchRun, listResearchRuns, type ResearchKind, type ResearchRequestByKind, type ResearchRun } from "@/lib/api/research-lab";
import { createRequestGate } from "@/lib/latest-request";
import { useLatestResource } from "@/lib/use-latest-resource";
import { ResearchRunForm, RESEARCH_KIND_LABELS } from "./research-run-form";
import { ResearchRunResult } from "./research-run-result";

export function ResearchWorkbench() {
  const [kind, setKind] = useState<ResearchKind>("allocation");
  const [busy, setBusy] = useState(false);
  const [run, setRun] = useState<ResearchRun | null>(null);
  const [error, setError] = useState("");
  const resultRegion = useRef<HTMLDivElement>(null);
  const requests = useMemo(createRequestGate, []);
  const capabilities = useLatestResource(useCallback(getResearchCapabilities, []));
  const history = useLatestResource(useCallback(listResearchRuns, []));
  useEffect(() => () => requests.invalidate(), [requests]);
  useEffect(() => { if (run) resultRegion.current?.focus(); }, [run]);

  async function submit<K extends ResearchKind>(selected: K, payload: ResearchRequestByKind[K]) {
    const current = requests.begin();
    setBusy(true); setError(""); setRun(null);
    try {
      const result = await createResearchRun(selected, payload);
      if (current()) { setRun(result); void history.reload().catch(() => {}); }
    } catch (failure) {
      if (current()) setError(failure instanceof Error ? failure.message : "Research could not be completed. Check adapter configuration and inputs.");
    } finally { if (current()) setBusy(false); }
  }
  async function loadRun(id: number) {
    const current = requests.begin();
    setBusy(true); setError(""); setRun(null);
    try { const result = await getResearchRun(id); if (current()) setRun(result); }
    catch (failure) { if (current()) setError(failure instanceof Error ? failure.message : "The saved research run is unavailable."); }
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
          onClick={() => { requests.invalidate(); setError(""); setKind(value); }}>{label}</button>)}
      </div>
      <ResearchRunForm key={kind} kind={kind} busy={busy} onSubmit={submit} />
      {busy && <p role="status">Waiting for the saved research result…</p>}
      {error && <p role="alert">{error}</p>}
      {run && <div ref={resultRegion} tabIndex={-1}><ResearchRunResult key={run.run_id} run={run} /></div>}
    </Panel>
    <Panel title="Saved research runs" collapsible>
      {history.status === "loading" ? <p role="status">Loading saved research…</p> : history.status === "error" ? <p role="alert">Saved runs unavailable: {history.error}</p>
        : history.data?.length ? <div className="table-wrap" role="region" aria-label="Saved research runs" tabIndex={0}><table>
          <thead><tr><th scope="col">Run</th><th scope="col">Kind</th><th scope="col">Status</th><th scope="col">Created</th><th scope="col">Open</th></tr></thead>
          <tbody>{history.data.map(saved => <tr key={saved.run_id}><th scope="row">#{saved.run_id}</th><td>{saved.kind}</td><td>{saved.status}</td><td>{saved.created_at}</td>
            <td><button type="button" className="secondary-button" disabled={busy || !["complete", "success"].includes(saved.status)} onClick={() => void loadRun(saved.run_id)}>Open run {saved.run_id}</button></td></tr>)}</tbody>
        </table></div> : <p>No saved research runs. Submit an explicit dataset to begin.</p>}
      <button type="button" className="secondary-button" disabled={history.status === "loading"} onClick={() => void history.reload().catch(() => {})}>Refresh saved runs</button>
    </Panel>
  </div>;
}
