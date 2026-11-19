"use client";

import { useCallback, useEffect, useId, useMemo, useState } from "react";
import Link from "next/link";
import { Panel } from "@/components/page";
import { getSourceAdapterCapabilities, getExtractionDocuments, runSourceAdapter, type SourceAction, type SourceAdapterResult, type SourceRequestByAction } from "@/lib/api/adapter-actions";
import { fetchResearchCompanies } from "@/lib/api/research-search";
import { createRequestGate } from "@/lib/latest-request";
import { useLatestResource } from "@/lib/use-latest-resource";
import { parseResearchJson, researchNumber } from "@/lib/research-lab-input";
import { ResearchJsonInput } from "./json-input";
import { AdapterReceipt } from "./adapter-receipt";
import { AdapterFailure } from "./adapter-failure";

const ACTIONS: Record<SourceAction, string> = { "sec-facts": "SEC annual facts", "india-filings": "India filing metadata", transcript: "Earnings transcript", extract: "Stored PDF extraction", "fred-vintage": "FRED vintage observations" };

export function SourceAdapterPanel() {
  const id = useId();
  const [action, setAction] = useState<SourceAction>("sec-facts");
  const [companyId, setCompanyId] = useState("");
  const [companyDrafts, setCompanyDrafts] = useState<Record<string, string>>({});
  const records = companyDrafts[companyId] ?? "";
  const setRecords = (value: string) => setCompanyDrafts(drafts => ({ ...drafts, [companyId]: value }));
  const [transcriptProvider, setTranscriptProvider] = useState<SourceRequestByAction["transcript"]["provider"]>("earningscall");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<Error | null>(null);
  const [result, setResult] = useState<SourceAdapterResult | null>(null);
  const candidateDocumentId = result?.raw_document_ids?.length === 1 ? result.raw_document_ids[0] : null;
  const requests = useMemo(createRequestGate, []);
  const companies = useLatestResource(useCallback(fetchResearchCompanies, []));
  const capabilities = useLatestResource(useCallback(getSourceAdapterCapabilities, []));
  useEffect(() => () => requests.invalidate(), [requests]);
  function reset() { requests.invalidate(); setError(null); setResult(null); }

  async function submit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault(); if (busy) return;
    const data = new FormData(event.currentTarget);
    const text = (name: string) => String(data.get(name) ?? "").trim();
    const current = requests.begin();
    setBusy(true); setError(null); setResult(null);
    try {
      let payload: SourceRequestByAction[SourceAction];
      if (action === "sec-facts") payload = { max_years: researchNumber(text("max_years"), "Maximum years"), ...(text("as_of") ? { as_of: text("as_of") } : {}) };
      else if (action === "india-filings") payload = { exchange: text("exchange") as SourceRequestByAction["india-filings"]["exchange"], records: parseResearchJson<SourceRequestByAction["india-filings"]["records"]>(records, "Filing metadata", "array") };
      else if (action === "transcript") payload = { provider: text("provider") as SourceRequestByAction["transcript"]["provider"], fiscal_year: researchNumber(text("fiscal_year"), "Fiscal year"), fiscal_quarter: researchNumber(text("fiscal_quarter"), "Fiscal quarter"), level: researchNumber(text("level"), "Transcript level"), ...(text("exchange") ? { exchange: text("exchange") } : {}) };
      else if (action === "extract") payload = { adapter: text("adapter") as SourceRequestByAction["extract"]["adapter"], pages: text("pages").split(",").map(page => researchNumber(page, "Page number")) };
      else payload = { series_id: text("series_id"), as_of: text("as_of"), observation_start: text("observation_start"), observation_end: text("observation_end"), mode: text("mode") as SourceRequestByAction["fred-vintage"]["mode"], max_pages: researchNumber(text("max_pages"), "Maximum pages") };
      const receipt = await runSourceAdapter(action, payload, companyId ? Number(companyId) : undefined, text("document_id") ? Number(text("document_id")) : undefined);
      if (current()) setResult(receipt);
    } catch (failure) { if (current()) setError(failure instanceof Error ? failure : new Error("The source action could not complete.")); }
    finally { if (current()) setBusy(false); }
  }

  return <Panel title="Source and document adapters" collapsible>
    <p>Run a specific source action explicitly. Imported documents and financial candidates retain review gates; these actions do not approve facts or overwrite valuation assumptions. Provider credentials stay on the server.</p>
    <details><summary>Source adapter readiness</summary>
      {capabilities.status === "loading" ? <p role="status">Checking source adapters…</p> : capabilities.status === "error" ? <p role="alert">{capabilities.error}</p>
        : <ul>{capabilities.data?.map(adapter => <li key={adapter.adapter}><strong>{adapter.adapter}:</strong> {adapter.status.replaceAll("_", " ")}{adapter.dependency_version ? ` · ${adapter.dependency_version}` : ""}. {(adapter.warnings ?? []).join(" ")}</li>)}</ul>}
      <button className="secondary-button" type="button" disabled={capabilities.status === "loading"} onClick={() => void capabilities.reload().catch(() => {})}>Refresh source adapter readiness</button>
    </details>
    <div className="field"><label htmlFor={`${id}-action`}>Source action</label><select id={`${id}-action`} value={action} disabled={busy} onChange={event => { reset(); setAction(event.target.value as SourceAction); }}>
      {Object.entries(ACTIONS).map(([value, label]) => <option key={value} value={value}>{label}</option>)}</select></div>
    {action !== "fred-vintage" && <div className="field"><label htmlFor={`${id}-company`}>Company for source evidence</label>
      <select id={`${id}-company`} value={companyId} disabled={busy} onChange={event => { reset(); setCompanyId(event.target.value); }}><option value="">Select a tracked company</option>
        {companies.data?.data?.map(company => <option key={company.id} value={company.id}>{company.ticker} · {company.name} · {company.market}/{company.primary_exchange || company.exchange || "unknown"}</option>)}</select>
      {companies.status === "error" || companies.data?.errors.length ? <p role="alert">Tracked companies unavailable. Refresh the page and try again.</p> : null}
    </div>}
    <form key={`${action}:${companyId}`} onSubmit={submit} onChange={() => { if (!busy) reset(); }} aria-label={`${ACTIONS[action]} adapter inputs`}>
      <fieldset disabled={busy || (action !== "fred-vintage" && !companyId)} className="research-lab-fieldset">
        <legend>{ACTIONS[action]} inputs</legend>
        {action === "sec-facts" && <><p>Extract supported annual SEC facts into the existing candidate review workflow. Unsupported periods stay excluded.</p><div className="form-grid">
          <div className="field"><label htmlFor={`${id}-asof`}>As-of cutoff (optional)</label><input id={`${id}-asof`} name="as_of" type="date" /></div>
          <div className="field"><label htmlFor={`${id}-years`}>Maximum years</label><input id={`${id}-years`} name="max_years" type="number" min={1} max={10} defaultValue={5} required /></div></div></>}
        {action === "india-filings" && <><div className="field"><label htmlFor={`${id}-exchange`}>Metadata exchange</label><select id={`${id}-exchange`} name="exchange"><option>NSE</option><option>BSE</option></select></div>
          <ResearchJsonInput label="Official filing metadata JSON" value={records} onChange={setRecords} description="Paste official metadata for this company from the selected exchange. Draft text stays with this company while this page is open. Intake does not scrape the exchange or certify attachment contents." /></>}
        {action === "transcript" && <div className="form-grid">
          <div className="field"><label htmlFor={`${id}-provider`}>Transcript provider</label><select id={`${id}-provider`} name="provider" value={transcriptProvider} onChange={event => setTranscriptProvider(event.target.value as SourceRequestByAction["transcript"]["provider"])}><option value="earningscall">EarningsCall</option><option value="fmp">FMP</option></select></div>
          <div className="field"><label htmlFor={`${id}-year`}>Fiscal year</label><input id={`${id}-year`} name="fiscal_year" type="number" min={1990} max={2100} required /></div>
          <div className="field"><label htmlFor={`${id}-quarter`}>Fiscal quarter</label><select id={`${id}-quarter`} name="fiscal_quarter">{[1, 2, 3, 4].map(quarter => <option key={quarter}>{quarter}</option>)}</select></div>
          <div className="field"><label htmlFor={`${id}-transcript-exchange`}>Provider exchange (optional)</label><input id={`${id}-transcript-exchange`} name="exchange" maxLength={20} pattern="[A-Z0-9_.-]+" /></div>
          <div className="field"><label htmlFor={`${id}-level`}>Transcript detail level</label><select key={transcriptProvider} id={`${id}-level`} name="level">{(transcriptProvider === "fmp" ? [1] : [1, 2, 3, 4]).map(level => <option key={level}>{level}</option>)}</select>{transcriptProvider === "fmp" && <p>FMP supports detail level 1 only.</p>}</div>
        </div>}
        {action === "extract" && <><ExtractionDocumentPicker companyId={Number(companyId)} />
          <div className="form-grid"><div className="field"><label htmlFor={`${id}-extractor`}>Extraction adapter</label><select id={`${id}-extractor`} name="adapter"><option value="camelot">Camelot</option><option value="docling">Docling</option><option value="marker">Marker</option></select></div>
            <div className="field"><label htmlFor={`${id}-pages`}>Pages (comma-separated, 1-based)</label><input id={`${id}-pages`} name="pages" placeholder="1, 2, 3" required /></div></div>
          <p>At most 20 selected pages. A stored PDF asset and the configured extraction profile are required. Result text and tables remain unreviewed source candidates.</p></>}
        {action === "fred-vintage" && <div className="form-grid">
          <div className="field"><label htmlFor={`${id}-series`}>FRED series ID</label><input id={`${id}-series`} name="series_id" maxLength={80} required /></div>
          <div className="field"><label htmlFor={`${id}-vintage`}>Public-information cutoff</label><input id={`${id}-vintage`} name="as_of" type="date" required /></div>
          <div className="field"><label htmlFor={`${id}-start`}>Observation start</label><input id={`${id}-start`} name="observation_start" type="date" required /></div>
          <div className="field"><label htmlFor={`${id}-end`}>Observation end</label><input id={`${id}-end`} name="observation_end" type="date" required /></div>
          <div className="field"><label htmlFor={`${id}-mode`}>Vintage mode</label><select id={`${id}-mode`} name="mode"><option value="as_of">Latest eligible revision as of cutoff</option><option value="initial_release">Initial release</option></select></div>
          <div className="field"><label htmlFor={`${id}-maxpages`}>Maximum pages</label><input id={`${id}-maxpages`} name="max_pages" type="number" min={1} max={10} defaultValue={5} required /></div>
        </div>}
        <button type="submit">{busy ? "Running source action…" : `Run ${ACTIONS[action].toLowerCase()}`}</button>
      </fieldset>
    </form>
    {busy && <p role="status">Waiting for the source processing receipt…</p>}
    <AdapterFailure error={error} />
    {result && companyId && !!result.candidate_ids?.length && <section aria-label="Source candidate review">
      <p>{result.candidate_ids.length} candidate(s) need review. <Link href={`/companies/${companyId}/fundamentals`} prefetch={false}>Review company candidates</Link></p>
      {candidateDocumentId !== null && <details><summary>Inspect individual candidate evidence</summary><ul>
        {result.candidate_ids.map(candidateId => <li key={candidateId}><Link prefetch={false}
          href={`/documents/${candidateDocumentId}/${action === "extract" ? "financial-evidence" : "sections"}?candidate_id=${candidateId}`}>Inspect candidate #{candidateId}</Link></li>)}
      </ul></details>}
    </section>}
    {result?.adapter === "alfred" && <section aria-label="Economic series basis">
      <h3>Economic series basis</h3>
      {Object.entries(result.details?.series_basis ?? {}).length ? <ul>
        {Object.entries(result.details?.series_basis ?? {}).map(([vintage, basis]) => {
          const entry = basis as { units?: string; frequency?: string; seasonal_adjustment?: string };
          return <li key={vintage}>{vintage} · {entry.units} · {entry.frequency} · {entry.seasonal_adjustment}</li>;
        })}
      </ul> : <p>Vintage units, frequency or seasonal basis are unavailable.</p>}
    </section>}
    {result && <AdapterReceipt provider={result.adapter} runId={result.processing_run_id ?? null} observedAt={result.observed_at} status={result.status ?? "source response"}
      documents={result.raw_document_ids ?? []} warnings={result.warnings ?? []} result={{ fetched_count: result.fetched_count, created_count: result.created_count,
        duplicate_count: result.duplicate_count, candidate_ids: result.candidate_ids, details: result.details }} />}
  </Panel>;
}

function ExtractionDocumentPicker({ companyId }: { companyId: number }) {
  const id = useId();
  const documents = useLatestResource(useCallback(() => companyId ? getExtractionDocuments(companyId) : Promise.resolve({ items: [], total: 0 }), [companyId]));
  return <div className="field"><label htmlFor={id}>Stored source document</label><select id={id} name="document_id" defaultValue="" required>
    <option value="">Select a stored document with a PDF asset</option>{documents.data?.items.map(document => <option key={document.id} value={document.id}>#{document.id} · {document.title}</option>)}</select>
    {documents.status === "loading" && <p role="status">Loading company documents…</p>}
    {documents.status === "error" && <p role="alert">Documents unavailable: {documents.error}</p>}
    {documents.data && <p>Showing the latest {documents.data.items.length} of {documents.data.total} company documents. The server verifies the selected PDF asset.</p>}
  </div>;
}
