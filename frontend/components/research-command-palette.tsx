"use client";

import Link from "next/link";
import { useCallback, useEffect, useId, useMemo, useRef, useState, type KeyboardEvent } from "react";
import { Search, X } from "lucide-react";
import { lookupCompanyByTicker, type CompanyLookup } from "@/lib/api/companies";
import type { ApiResponse } from "@/lib/api/contract";
import type { EvidenceSearchResult } from "@/lib/api/evidence";
import { fetchResearchCompanies, searchStoredEvidence } from "@/lib/api/research-search";
import { createRequestGate } from "@/lib/latest-request";
import { useLatestResource } from "@/lib/use-latest-resource";
import { matchingResearchCompanies, researchResultHref } from "@/lib/research-search";
import { DataStateNotices } from "@/components/ui/data-states";

type Scope = "companies" | "evidence" | "lookup";

export function ResearchCommandPalette() {
  const [open, setOpen] = useState(false);
  useEffect(() => {
    function shortcut(event: globalThis.KeyboardEvent) {
      if ((event.metaKey || event.ctrlKey) && event.key.toLowerCase() === "k" && !event.altKey) {
        event.preventDefault(); setOpen(value => !value);
      }
    }
    document.addEventListener("keydown", shortcut);
    return () => document.removeEventListener("keydown", shortcut);
  }, []);
  return <>
    <button type="button" className="secondary-button topbar-search-link" aria-label="Search companies and evidence" title="Search companies and evidence (Ctrl or Command K)" onClick={() => setOpen(true)}>
      <Search size={16} aria-hidden="true" /><span>Search</span><kbd aria-hidden="true">⌘/Ctrl K</kbd>
    </button>
    {open && <ResearchSearchDialog onClose={() => setOpen(false)} />}
  </>;
}

function ResearchSearchDialog({ onClose }: { onClose: () => void }) {
  const id = useId();
  const dialog = useRef<HTMLDialogElement>(null);
  const [scope, setScope] = useState<Scope>("companies");
  const [query, setQuery] = useState("");
  const [market, setMarket] = useState("");
  const [exchange, setExchange] = useState("");
  const [evidence, setEvidence] = useState<{ query: string; response?: ApiResponse<EvidenceSearchResult[]>; error?: string } | null>(null);
  const [lookup, setLookup] = useState<{ signature: string; data?: CompanyLookup; error?: string } | null>(null);
  const requests = useMemo(createRequestGate, []);
  const lookupRequests = useMemo(createRequestGate, []);
  const companyLoader = useCallback(fetchResearchCompanies, []);
  const companies = useLatestResource(companyLoader);
  const matches = matchingResearchCompanies(companies.data?.data ?? [], query, market);
  const lookupSignature = JSON.stringify([query.trim(), market || "US", exchange.trim()]);
  const activeLookup = lookup?.signature === lookupSignature ? lookup : null;

  useEffect(() => {
    const previous = document.activeElement as HTMLElement | null;
    const element = dialog.current;
    element?.showModal();
    return () => { element?.close(); previous?.focus(); requests.invalidate(); lookupRequests.invalidate(); };
  }, [requests, lookupRequests]);

  useEffect(() => {
    if (scope !== "evidence" || query.trim().length < 2) return;
    const current = requests.begin();
    const timer = window.setTimeout(async () => {
      try {
        const response = await searchStoredEvidence(query);
        if (current()) setEvidence({ query, response });
      } catch (error) {
        if (current()) setEvidence({ query, error: error instanceof Error ? error.message : "Stored evidence search unavailable." });
      }
    }, 250);
    return () => { window.clearTimeout(timer); requests.invalidate(); };
  }, [scope, query, requests]);

  function changeQuery(value: string) {
    requests.invalidate(); lookupRequests.invalidate(); setEvidence(null); setLookup(null); setQuery(value);
  }
  function changeScope(value: Scope) {
    requests.invalidate(); lookupRequests.invalidate(); setEvidence(null); setLookup(null); setScope(value);
  }
  async function lookupTicker() {
    if (!query.trim() || (activeLookup && !activeLookup.data && !activeLookup.error)) return;
    const signature = lookupSignature;
    const current = lookupRequests.begin();
    setLookup({ signature });
    try {
      const data = await lookupCompanyByTicker(query.trim(), { market: market || "US", exchange: exchange.trim() || null });
      if (current()) setLookup({ signature, data });
    } catch (error) {
      if (current()) setLookup({ signature, error: error instanceof Error ? error.message : "Company lookup unavailable." });
    }
  }
  function moveThroughResults(event: KeyboardEvent<HTMLDialogElement>) {
    if (!["ArrowDown", "ArrowUp"].includes(event.key)) return;
    const target = event.target as HTMLElement;
    if (target.id !== `${id}-query` && !target.hasAttribute("data-search-result")) return;
    const links = Array.from(dialog.current?.querySelectorAll<HTMLAnchorElement>("[data-search-result]") ?? []);
    if (!links.length) return;
    event.preventDefault();
    const index = links.indexOf(document.activeElement as HTMLAnchorElement);
    links[index < 0 ? (event.key === "ArrowDown" ? 0 : links.length - 1)
      : (index + (event.key === "ArrowDown" ? 1 : -1) + links.length) % links.length].focus();
  }
  const currentEvidence = evidence?.query === query ? evidence : null;
  const evidenceError = currentEvidence?.error || currentEvidence?.response?.errors?.[0]?.message;
  const records = currentEvidence?.response?.data ?? [];
  const companyError = companies.error || companies.data?.errors?.[0]?.message;
  const lookupData = activeLookup?.data;
  const addParams = new URLSearchParams({ create: "1", ticker: lookupData?.ticker ?? "", market: (lookupData?.market ?? market) || "US",
    exchange: lookupData?.primary_exchange ?? lookupData?.exchange ?? exchange });

  return <dialog ref={dialog} className="research-command-dialog" aria-labelledby={`${id}-title`}
    onCancel={event => { event.preventDefault(); onClose(); }} onKeyDown={moveThroughResults}
    onClick={event => { if (event.target === dialog.current) onClose(); }}>
    <div className="research-command-body">
      <div className="section-intro"><h2 id={`${id}-title`}>Find research</h2>
        <button type="button" className="secondary-button" aria-label="Close search" onClick={onClose}><X size={18} aria-hidden="true" /></button></div>
      <div className="button-row" role="group" aria-label="Search scope">
        {([ ["companies", "Companies"], ["evidence", "Stored evidence"], ["lookup", "Look up ticker"] ] as const).map(([value, label]) =>
          <button key={value} type="button" className="secondary-button" aria-pressed={scope === value} onClick={() => changeScope(value)}>{label}</button>)}
      </div>
      <div className="field"><label htmlFor={`${id}-query`}>{scope === "lookup" ? "Ticker to look up" : "Search terms"}</label>
        <input id={`${id}-query`} autoFocus type="search" value={query} maxLength={scope === "lookup" ? 40 : 200}
          placeholder={scope === "companies" ? "Name, ticker, exchange or ISIN" : scope === "evidence" ? "Search stored evidence (at least 2 characters)" : "Ticker"}
          onChange={event => changeQuery(event.target.value)} /></div>
      {scope !== "evidence" && <div className="form-grid">
        <div className="field"><label htmlFor={`${id}-market`}>Market</label><select id={`${id}-market`} value={market}
          onChange={event => { lookupRequests.invalidate(); setLookup(null); setMarket(event.target.value); }}>
          <option value="">{scope === "lookup" ? "United States (default)" : "All markets"}</option><option value="US">United States</option><option value="IN">India</option>
        </select></div>
        {scope === "lookup" && <div className="field"><label htmlFor={`${id}-exchange`}>Exchange (optional)</label>
          <input id={`${id}-exchange`} value={exchange} maxLength={80} onChange={event => { lookupRequests.invalidate(); setLookup(null); setExchange(event.target.value); }} /></div>}
      </div>}
      <div className="research-command-results" aria-live="polite">
        {scope === "companies" && <>
          {companies.status === "loading" ? <p role="status">Loading tracked companies…</p> : companyError || !companies.data?.data
            ? <p role="alert">Company search unavailable: {companyError || "No response received."}</p> : <>
              <DataStateNotices metas={[companies.data.meta]} />
              <p>{matches.length} tracked company match(es). Listing identity is shown for ambiguous tickers.</p>
              <ul>{matches.slice(0, 30).map(company => <li key={company.id}><Link data-search-result href={`/companies/${company.id}`} prefetch={false} onClick={onClose}>
                <strong>{company.ticker} · {company.name}</strong><span>{company.market || "Market unavailable"} · {company.primary_exchange || company.exchange || "Exchange unavailable"} · {company.currency || "Currency unavailable"}</span>
              </Link></li>)}</ul>
              {!matches.length && <p>No tracked company matches. Use Look up ticker to review another listing.</p>}
              {matches.length > 30 && <p>Showing the first 30 matches. Refine the query or open the company list.</p>}
            </>}
          <Link href={`/companies?${new URLSearchParams({ q: query, market })}`} prefetch={false} onClick={onClose}>Open company list</Link>
        </>}
        {scope === "evidence" && <>
          {query.trim().length < 2 ? <p>Enter at least two characters to search documents, events, thesis notes and saved research.</p>
            : !currentEvidence ? <p role="status">Searching stored evidence…</p>
              : evidenceError || !currentEvidence.response?.data ? <p role="alert">Stored evidence unavailable: {evidenceError || "No response received."}</p> : <>
                <DataStateNotices metas={[currentEvidence.response.meta]} />
                <p>{records.length} stored result(s). Source dates and review state remain attached.</p>
                <ul>{records.slice(0, 30).map(record => { const href = researchResultHref(record.href); return <li key={`${record.result_type}-${record.record_id}`}>
                  {href ? <Link data-search-result href={href} prefetch={false} onClick={onClose}><strong>{record.title}</strong>
                    <span>{record.result_type.replaceAll("_", " ")} · {record.claim_type} · {record.scope}{record.is_mock ? " · Mock Data" : ""}</span>
                    <span>{record.source_name || "Stored source"} · {record.source_timestamp || "Source date unavailable"}{record.review_status === "approved" ? " · Human reviewed" : ""}</span>
                    {record.excerpt && <span>{record.excerpt}</span>}</Link> : <p>{record.title}: source navigation unavailable.</p>}
                </li>; })}</ul>
                {!records.length && <p>No stored research matches these terms.</p>}
              </>}
          <Link href={`/search?${new URLSearchParams({ q: query })}`} prefetch={false} onClick={onClose}>Open full evidence search</Link>
        </>}
        {scope === "lookup" && <>
          <p>Explicit lookup uses the configured company provider. It does not add a company or retrieve a live quote.</p>
          <button type="button" disabled={!query.trim() || Boolean(activeLookup && !activeLookup.data && !activeLookup.error)} onClick={() => void lookupTicker()}>
            {activeLookup && !activeLookup.data && !activeLookup.error ? "Looking up…" : "Look up listing"}</button>
          {activeLookup?.error && <p role="alert">{activeLookup.error}</p>}
          {lookupData && <div className="basis-note"><h3>{lookupData.name} ({lookupData.ticker})</h3>
            <p>{lookupData.market || market || "US"} · {lookupData.primary_exchange || lookupData.exchange || "Exchange unavailable"} · {lookupData.currency || "Currency unavailable"}</p>
            <p>Source: {lookupData.source || "Configured company lookup"}</p>
            {lookupData.warnings?.map((warning, index) => <p key={index}>{warning}</p>)}
            <Link data-search-result href={`/companies?${addParams}`} prefetch={false} onClick={onClose}>Review in Add company</Link>
          </div>}
        </>}
      </div>
      <p className="research-command-help">↑ ↓ move through results · Enter opens · Escape closes</p>
    </div>
  </dialog>;
}
