import {fetchApi, postApi} from "./transport.ts";
import type {PricePin} from "./price-timeline.ts";

export type DecisionChoices = { assumptions: {id:number; label:string}[]; originals: {document_id:number; event_id?:number|null; title:string; published:string; close_context:string}[];
  revisions: {id:number; document_id:number; label:string}[]; versions:{id:number; label:string}[]; partial:boolean };
export type DecisionDraft = {assumption_id:number; original: {kind:"raw_document"; id:number; event_id:number|null; revision_id:number|null}|null;
  valuation_version_id:number|null; decision:"no_change"|"propose_change"|"blocked"; reason:string };
export type DecisionContext = {anchor:PricePin["anchor"]; assumption:{description:string}; original: {id:number; title:string; temporal_scope:string;
  published:string|null; revision:{id:number; candidate_id:number; number:number}|null}|null; reason:string; decision:string;
  valuation_version:{id:number;model_id:number}|null};
const path=(note:number,pin:number)=>`/thesis-notes/${note}/price-pins/${pin}`;
export const priceDecisionChoices=(note:number,pin:number)=>fetchApi<DecisionChoices>(path(note,pin)+"/decision-options");
export const previewPriceDecision=(note:number,pin:number,body:DecisionDraft)=>
  postApi<{context_hash:string;context:DecisionContext}>(path(note,pin)+"/decision-preview",body);
export const recordPriceDecision=(note:number,pin:number,body:DecisionDraft & {context_hash:string;request_id:string})=>
  postApi<{change_id:number;replayed:boolean}>(path(note,pin)+"/decisions",body);
