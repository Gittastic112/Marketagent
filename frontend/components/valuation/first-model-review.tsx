"use client";

import { useRef, useState } from "react";
import { getDatedInputs, type DatedInputs } from "@/lib/api/dated-inputs";
import { chooseDraftSources, previewFirstModel, confirmFirstModel, type DraftSource, type FirstCommand, type FirstPreview } from "@/lib/api/first-valuation";
import type { ValuationSetupDraft } from "@/lib/api/valuation-drafts";
import { formatNumber } from "@/lib/formatting";

const fields: Record<string, string> = { revenue: "starting_revenue", net_income: "net_income", debt: "debt", cash: "cash",
  minority_interests: "minority_interests", preferred_stock: "preferred_stock", employee_options_value: "employee_options_value",
  change_in_nwc: "change_in_nwc", depreciation: "depreciation", capex: "capex", diluted_shares: "diluted_shares" };
type Props = { companyId: number; draftId: number; modelType: string; formEpoch: number;
  initialDay?: string; busy: boolean; setBusy: (value: boolean) => void;
  persist: () => Promise<ValuationSetupDraft>; accept: (draft: ValuationSetupDraft) => void;
  proposal?: ValuationSetupDraft["source_metadata_json"]["dated_source_proposal"] };

export function FirstModelReview({companyId, draftId, modelType, formEpoch, initialDay, proposal, busy, setBusy, persist, accept}: Props) {
  const [day, setDay] = useState(initialDay || proposal?.valuation_date || new Intl.DateTimeFormat("sv-SE", {timeZone:"America/New_York"}).format(new Date()));
  const [report, setReport] = useState<DatedInputs | null>(null);
  const [selected, setSelected] = useState<DraftSource[]>(proposal?.selections ?? []);
  const [reason, setReason] = useState("");
  const [message, setMessage] = useState("");
  const [ready, setReady] = useState<{result:FirstPreview; command:FirstCommand; id:string; epoch:number; reason:string} | null>(null);
  const formRef = useRef<HTMLElement>(null);
  const pending = useRef(false);
  const unchanged = ready && ready.epoch === formEpoch && ready.command.valuation_date === day && ready.reason === reason.trim();
  async function run(fn: () => Promise<void>) {
    if (pending.current) return;
    pending.current = true; setBusy(true); setMessage("");
    try { await fn(); }
    catch (error) { setMessage(error instanceof Error ? error.message : "Request failed. Retry the same action."); }
    finally { pending.current = false; setBusy(false); }
  }
  async function apply() {
    const saved = await persist();
    const attached = await chooseDraftSources(draftId, saved.updated_at, day, selected);
    accept(attached); setReady(null); setMessage("Source selection saved to this draft.");
  }
  async function preview() {
    const form = formRef.current?.closest("form");
    if (!form) return;
    const name = form.querySelector<HTMLInputElement>('[name="name"]')?.value.trim() ?? "";
    const description = form.querySelector<HTMLInputElement>('[name="description"]')?.value.trim() || null;
    if (!name || !day) { setMessage("Enter a model name and research date."); return; }
    setReady(null);
    const saved = await persist();
    const command = {name, description, valuation_date: day, model_type: modelType, expected_updated_at: saved.updated_at};
    const result = await previewFirstModel(draftId, command);
    setReady({result, command, id:crypto.randomUUID(), epoch:formEpoch, reason:reason.trim()});
  }
  async function confirm() {
    if (!ready || !unchanged || !ready.result.ready || !reason.trim()) return;
    const url = new URL(window.location.href);
    url.searchParams.set("draft", String(draftId)); window.history.replaceState(null, "", url);
    const saved = await confirmFirstModel(draftId, {...ready.command, preview_hash:ready.result.preview_hash,
      submission_id:ready.id, reason:ready.reason});
    window.location.assign(`/companies/${companyId}/valuation/${saved.model_id}`);
  }
  const unapplied = JSON.stringify(selected) !== JSON.stringify(proposal?.selections ?? []);
  return <section className="panel panel-content" ref={formRef} aria-label="First valuation preview">
    <h2>Preview your first valuation</h2>
    <label>Research date<input type="date" value={day} disabled={busy} onChange={e=>{setDay(e.target.value);setReport(null);setReady(null);}} /></label>
    <details><summary>Choose dated financial evidence</summary>
      <button type="button" disabled={busy || !day} onClick={()=>run(async()=>{setReport(await getDatedInputs(companyId,day));})}>Inspect dated sources</button>
      {report && <>{report.rows.filter(r=>fields[r.metric] && r.sources.length).map(row=><label key={row.metric}>{row.label}
        <select value={selected.find(s=>s.target_field===fields[row.metric])?.id ?? ""} disabled={busy}
          onChange={e=>{const rest=selected.filter(s=>s.target_field!==fields[row.metric]);setSelected(e.target.value ?
            [...rest,{kind:"source_fact_revision",target_field:fields[row.metric],id:Number(e.target.value)}] : rest);setReady(null);}}>
          <option value="">Use the draft assumption</option>{row.sources.map(s=><option key={s.revision_id} value={s.revision_id}>
            Revision {s.revision_number} · {s.value} {s.unit} · {s.publication_date ?? "publication unknown"} · {s.availability.replaceAll("_"," ")}
          </option>)}</select></label>)}
        {!report.rows.some(r=>fields[r.metric] && r.sources.length) && <p>No preserved financial revisions are available for this date.</p>}</>}
      {selected.length > 0 && <button type="button" disabled={busy} onClick={()=>{setSelected([]);setReady(null);}}>Clear source selections</button>}
      {(report || unapplied) && <button type="button" disabled={busy || !day} onClick={()=>run(apply)}>Apply source selection</button>}
      {proposal?.bindings.map(b=><p key={b.ref.target_field}>{b.ref.target_field.replaceAll("_"," ")} · {b.reason || b.conversion} {b.source && <a href={b.source.href}>Inspect original revision {b.source.revision_number}</a>}</p>)}
    </details>
    <label>Reason for this first version<input value={reason} maxLength={2000} disabled={busy} onChange={e=>{setReason(e.target.value);setReady(null);}} /></label>
    <button type="button" className="secondary-button" disabled={busy || unapplied || !day} onClick={()=>run(preview)}>Preview first valuation</button>
    {ready && unchanged && <div role="status">{ready.result.proposed_output ? <dl>
      {Object.entries(ready.result.proposed_output).slice(0,3).map(([key,value])=><div key={key}><dt>{key.replaceAll("_"," ")}</dt><dd>{value == null ? "Unavailable" : `${ready.result.currency ?? ""} ${formatNumber(value,2)}`}</dd></div>)}
    </dl> : <ul>{ready.result.blockers.map(x=><li key={x}>{x.replaceAll("_"," ")}</li>)}</ul>}
      {ready.result.diagnostics.map((w,i)=><p key={i}>{typeof w.message === "string" ? w.message : "Review diagnostic"}</p>)}</div>}
    <button type="button" className="primary-button" disabled={busy || !unchanged || !ready?.result.ready || !reason.trim()} onClick={()=>run(confirm)}>Confirm and Create Model</button>
    <p role="status">{message}</p>
  </section>;
}
