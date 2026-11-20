"use client";

import {useRef, useState} from "react";
import {useRouter} from "next/navigation";
import {priceDecisionChoices, previewPriceDecision, recordPriceDecision, type DecisionChoices, type DecisionDraft, type DecisionContext} from "@/lib/api/price-decisions";
import type {PricePin} from "@/lib/api/price-timeline";

export function PricePinDecision({pin}:{pin:PricePin}) {
  const router=useRouter();
  const [choices,setChoices]=useState<DecisionChoices|null>(null);
  const [target,setTarget]=useState(""), [original,setOriginal]=useState(""), [revision,setRevision]=useState("");
  const [version,setVersion]=useState(""), [decision,setDecision]=useState<DecisionDraft["decision"]>("no_change");
  const [reason,setReason]=useState(""), [message,setMessage]=useState(""), [busy,setBusy]=useState(false);
  const [review,setReview]=useState<{body:DecisionDraft; hash:string; id:string; context:DecisionContext}|null>(null);
  const lock=useRef(false);
  async function run(action:()=>Promise<void>) {
    if(lock.current)return; lock.current=true;setBusy(true);setMessage("");
    try {await action();} catch(err){setMessage(err instanceof Error?err.message:"Request failed. Retry this decision.");}
    finally{lock.current=false;setBusy(false);}
  }
  const selected=original && choices ? choices.originals[Number(original)] : null;
  async function preview() {
    const body:DecisionDraft={assumption_id:Number(target),original:selected?{kind:"raw_document",id:selected.document_id,event_id:selected.event_id??null,revision_id:Number(revision)||null}:null,
      valuation_version_id:Number(version)||null,decision,reason:reason.trim()};
    const result=await previewPriceDecision(pin.thesis_note_id,pin.id,body);
    setReview({body,hash:result.context_hash,id:crypto.randomUUID(),context:result.context});
  }
  async function save() {
    if(!review)return;
    await recordPriceDecision(pin.thesis_note_id,pin.id,{...review.body,context_hash:review.hash,request_id:review.id});
    setReview(null);setChoices(null);setReason("");setMessage("Decision saved to thesis history.");router.refresh();
  }
  return <div className="price-note-form">
    {!choices ? <button type="button" disabled={busy} onClick={()=>run(async()=>setChoices(await priceDecisionChoices(pin.thesis_note_id,pin.id)))}>Review this observation</button> :
      <fieldset disabled={busy} onChange={()=>setReview(null)}><legend>Decision about the thesis</legend>
        <label>Thesis assumption<select value={target} onChange={e=>setTarget(e.target.value)}><option value="">Choose an assumption</option>
          {choices.assumptions.map(a=><option key={a.id} value={a.id}>{a.label}</option>)}</select></label>
        {!choices.assumptions.length && <p>Add an assumption to this thesis to record a decision.</p>}
        <label>Original evidence<select value={original} onChange={e=>{setOriginal(e.target.value);setRevision("");}}><option value="">No matched original</option>
          {choices.originals.map((o,i)=><option key={i} value={String(i)}>{o.title} · {o.published} · {o.close_context}</option>)}</select></label>
        {selected && <><a href={`/documents/${selected.document_id}/sections?price_series=${pin.anchor.key}&price_date=${pin.anchor.date}&note_id=${pin.thesis_note_id}&pin=${pin.id}`} target="_blank" rel="noreferrer">Inspect original</a>
          <label>Financial revision<select value={revision} onChange={e=>setRevision(e.target.value)}><option value="">Document only</option>
          {choices.revisions.filter(r=>r.document_id===selected.document_id).map(r=><option key={r.id} value={r.id}>{r.label}</option>)}</select></label></>}
        <label>Related valuation version<select value={version} onChange={e=>setVersion(e.target.value)}><option value="">No valuation linked</option>
          {choices.versions.map(v=><option key={v.id} value={v.id}>{v.label} · version {v.id}</option>)}</select></label>
        {choices.partial && <p>Only the newest matching records are shown.</p>}
        <label>Decision<select value={decision} onChange={e=>setDecision(e.target.value as DecisionDraft["decision"])}>
          <option value="no_change">Retain assumption</option><option value="propose_change">Propose a change</option><option value="blocked">More evidence needed</option></select></label>
        <label>Reason for the decision<textarea maxLength={2000} value={reason} onChange={e=>setReason(e.target.value)} /></label>
        <button type="button" disabled={!target || !reason.trim()} onClick={()=>run(preview)}>Preview thesis decision</button>
        {review && <div role="status"><p>{review.context.assumption.description} · {review.context.anchor.date} · {review.context.anchor.currency} {review.context.anchor.price}</p>
          <p>{review.context.original ? review.context.original.title+" · "+review.context.original.temporal_scope.replaceAll("_"," ") : "No matched original reviewed"} · {review.body.decision.replaceAll("_"," ")}</p>
          <p>{review.context.reason}</p><button type="button" onClick={()=>run(save)}>Save to thesis history</button></div>}
      </fieldset>}
    <p role="status">{message}</p>
  </div>;
}
