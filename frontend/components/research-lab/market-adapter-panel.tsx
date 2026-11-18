"use client";

import { useEffect, useId, useMemo, useState } from "react";
import { Panel } from "@/components/page";
import { runDataAdapter, providersForMarketAction, type DataAdapterExecution, type DataRequestByAction, type MarketAdapterAction, type MarketAdapterProvider } from "@/lib/api/adapter-actions";
import { DataStateNotices } from "@/components/ui/data-states";
import { createRequestGate } from "@/lib/latest-request";
import { parseResearchJson } from "@/lib/research-lab-input";
import { ResearchJsonInput } from "./json-input";
import { AdapterReceipt } from "./adapter-receipt";
import { AdapterFailure } from "./adapter-failure";

const ACTIONS: Record<MarketAdapterAction, string> = {
  quote: "Market quote", history: "Dated price history", "dated-quote": "NSE dated observation", "corporate-actions": "Corporate actions",
  reference: "Massive security reference", identity: "OpenFIGI identity candidates", calendar: "Exchange calendar",
};

export function MarketAdapterPanel() {
  const id = useId();
  const [action, setAction] = useState<MarketAdapterAction>("quote");
  const [provider, setProvider] = useState<MarketAdapterProvider>("fmp");
  const [overrides, setOverrides] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<Error | null>(null);
  const [execution, setExecution] = useState<DataAdapterExecution | null>(null);
  const requests = useMemo(createRequestGate, []);
  useEffect(() => () => requests.invalidate(), [requests]);
  const providers = providersForMarketAction(action);
  const selectedProvider = providers.includes(provider) ? provider : providers[0] ?? provider;
  const marketInput = action !== "identity" && action !== "calendar";
  const dateRange = ["history", "corporate-actions", "calendar"].includes(action);
  const receipt = execution?.receipt;
  function resetReceipt() { requests.invalidate(); setExecution(null); setError(null); }

  async function submit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault(); if (busy) return;
    const data = new FormData(event.currentTarget);
    const text = (name: string) => String(data.get(name) ?? "").trim();
    const current = requests.begin();
    setBusy(true); setError(null); setExecution(null);
    try {
      let payload: DataRequestByAction[MarketAdapterAction];
      if (action === "identity") {
        payload = { id_type: text("id_type") as DataRequestByAction["identity"]["id_type"], id_value: text("id_value"), include_unlisted_equities: data.get("include_unlisted") === "on",
          ...(text("exchange_code") ? { exchange_code: text("exchange_code") } : {}), ...(text("mic_code") ? { mic_code: text("mic_code") } : {}) };
      } else if (action === "calendar") {
        payload = { exchange: text("calendar_exchange") as DataRequestByAction["calendar"]["exchange"], start_date: text("start_date"), end_date: text("end_date"),
          ...(overrides.trim() ? { overrides: parseResearchJson<DataRequestByAction["calendar"]["overrides"]>(overrides, "Calendar overrides", "array") } : {}) };
      } else {
        const identity = { market: text("market"), ticker: text("ticker"), ...(text("exchange") ? { exchange: text("exchange") } : {}), ...(text("currency") ? { currency: text("currency") } : {}) };
        if (action === "history") payload = { ...identity, start_date: text("start_date"), end_date: text("end_date"), adjustment: text("adjustment") as DataRequestByAction["history"]["adjustment"] };
        else if (action === "corporate-actions") payload = { ...identity, start_date: text("start_date"), end_date: text("end_date") };
        else if (action === "dated-quote") payload = { ...identity, requested_date: text("requested_date") };
        else payload = identity;
      }
      const result = await runDataAdapter(selectedProvider, action, payload);
      if (current()) setExecution(result);
    } catch (failure) { if (current()) setError(failure instanceof Error ? failure : new Error("The data adapter could not complete.")); }
    finally { if (current()) setBusy(false); }
  }

  return <Panel title="Market, identity and calendar adapters" collapsible>
    <p>Choose a provider and run an explicit request. Availability depends on server configuration and provider entitlement. Sources and response hashes are retained in Processing Runs. Corporate actions remain evidence; they are not applied to holdings automatically.</p>
    <div className="form-grid">
      <div className="field"><label htmlFor={`${id}-action`}>Data action</label><select id={`${id}-action`} value={action} disabled={busy}
        onChange={event => { resetReceipt(); setAction(event.target.value as MarketAdapterAction); }}>
        {Object.entries(ACTIONS).map(([value, label]) => <option key={value} value={value}>{label}</option>)}</select></div>
      {marketInput && <div className="field"><label htmlFor={`${id}-provider`}>Explicit provider</label><select id={`${id}-provider`} value={selectedProvider} disabled={busy || action === "dated-quote" || action === "reference"}
        onChange={event => { resetReceipt(); setProvider(event.target.value as MarketAdapterProvider); }}>
        {providers.map(value => <option key={value} value={value}>{{ fmp: "FMP", massive: "Massive", nse_mcp: "Official NSE MCP" }[value]}</option>)}</select></div>}
    </div>
    <form key={`${action}:${selectedProvider}`} onSubmit={submit} onChange={() => { if (!busy) resetReceipt(); }} aria-label={`${ACTIONS[action]} adapter inputs`}>
      <fieldset className="research-lab-fieldset" disabled={busy}><legend>{ACTIONS[action]} inputs</legend>
        {marketInput && <div className="form-grid">
          <div className="field"><label htmlFor={`${id}-ticker`}>Ticker or local symbol</label><input id={`${id}-ticker`} name="ticker" maxLength={40} required /></div>
          <div className="field"><label htmlFor={`${id}-market`}>Market</label><select id={`${id}-market`} name="market" defaultValue={selectedProvider === "nse_mcp" ? "IN" : "US"}><option value="US">United States</option><option value="IN">India</option></select></div>
          <div className="field"><label htmlFor={`${id}-exchange`}>Exchange (optional)</label><input id={`${id}-exchange`} name="exchange" maxLength={40} defaultValue={selectedProvider === "nse_mcp" ? "NSE" : ""} /></div>
          <div className="field"><label htmlFor={`${id}-currency`}>Currency (optional)</label><input id={`${id}-currency`} name="currency" maxLength={3} pattern="[A-Za-z]{3}" defaultValue={selectedProvider === "nse_mcp" ? "INR" : ""} /></div>
        </div>}
        {dateRange && <div className="form-grid">
          <div className="field"><label htmlFor={`${id}-start`}>Requested start date</label><input id={`${id}-start`} name="start_date" type="date" required /></div>
          <div className="field"><label htmlFor={`${id}-end`}>Requested end date</label><input id={`${id}-end`} name="end_date" type="date" required /></div>
        </div>}
        {action === "history" && <div className="field"><label htmlFor={`${id}-adjustment`}>Requested price adjustment</label><select id={`${id}-adjustment`} name="adjustment">
          <option value="provider">Provider basis (inspect returned basis)</option><option value="unadjusted">Unadjusted</option><option value="split_adjusted">Split adjusted</option></select>
          <p>Coverage describes requested API windows, not certified historical investability or complete total returns.</p></div>}
        {action === "dated-quote" && <div className="field"><label htmlFor={`${id}-requested`}>Requested observation date</label><input id={`${id}-requested`} name="requested_date" type="date" required />
          <p>A returned prior session remains distinct from the requested date; inspect previous_session_substitution in the receipt.</p></div>}
        {action === "identity" && <div className="form-grid">
          <div className="field"><label htmlFor={`${id}-idtype`}>Identifier type</label><select id={`${id}-idtype`} name="id_type">{["TICKER", "ID_ISIN", "ID_CUSIP", "ID_SEDOL", "ID_BB_GLOBAL"].map(type => <option key={type}>{type}</option>)}</select></div>
          <div className="field"><label htmlFor={`${id}-idvalue`}>Identifier value</label><input id={`${id}-idvalue`} name="id_value" maxLength={100} required /></div>
          <div className="field"><label htmlFor={`${id}-exchange-code`}>OpenFIGI exchange code (optional)</label><input id={`${id}-exchange-code`} name="exchange_code" maxLength={12} /></div>
          <div className="field"><label htmlFor={`${id}-mic`}>MIC (optional alternative to exchange code)</label><input id={`${id}-mic`} name="mic_code" maxLength={4} /></div>
          <label><input type="checkbox" name="include_unlisted" /> Include unlisted equities</label>
          <p>Ambiguous candidates require review. This lookup does not overwrite a company identity.</p>
        </div>}
        {action === "calendar" && <>
          <div className="field"><label htmlFor={`${id}-calendar`}>Exchange calendar</label><select id={`${id}-calendar`} name="calendar_exchange"><option value="XNYS">NYSE</option><option value="XNAS">NASDAQ</option><option value="XNSE">NSE</option><option value="XBOM">BSE</option></select></div>
          <ResearchJsonInput label="Calendar overrides JSON" value={overrides} onChange={setOverrides} required={false} rows={5}
            description="Optional sourced session overrides: date, closed or timezone-aware opens_at/closes_at, HTTPS source_url and reason. Library calendars can miss exceptional sessions; inspect returned coverage and warnings." />
        </>}
        <button type="submit">{busy ? "Requesting source data…" : `Run ${ACTIONS[action].toLowerCase()}`}</button>
      </fieldset>
    </form>
    {busy && <p role="status">Waiting for the source receipt…</p>}<AdapterFailure error={error} />
    {receipt && execution && <>
      <DataStateNotices metas={[execution.meta]} showWarnings={false} staleMessage="This source observation exceeds the adapter freshness threshold. Check its source timestamp and market session before use." />
      <AdapterReceipt provider={receipt.provider} runId={receipt.processing_run_id} observedAt={receipt.observed_at}
        status={"coverage" in receipt.result && typeof receipt.result.coverage === "string" ? receipt.result.coverage : execution.meta.status}
        documents={receipt.source_document_ids ?? []} warnings={[...new Set([...(receipt.warnings ?? []), ...execution.meta.warnings])]} result={receipt.result} />
    </>}
  </Panel>;
}
