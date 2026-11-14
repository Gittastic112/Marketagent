"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import { Panel } from "@/components/page";
import { discoverCompanyFilings, type FilingDiscovery } from "@/lib/api/documents";
import { createRequestGate } from "@/lib/latest-request";
import { sourceLink } from "@/lib/source-link";

export function FilingDiscoveryPanel({ overview }: { overview: FilingDiscovery }) {
  const [result, setResult] = useState<FilingDiscovery | null>(null);
  const [pending, setPending] = useState(false);
  const [failed, setFailed] = useState(false);
  const busy = useRef(false);
  const gate = useMemo(createRequestGate, []);
  useEffect(() => () => gate.invalidate(), [gate]);
  async function discover() {
    if (busy.current) return;
    busy.current = true;
    const current = gate.begin();
    setPending(true); setFailed(false); setResult(null);
    try {
      const next = await discoverCompanyFilings(overview.company_id);
      if (current()) setResult(next);
    } catch {
      if (current()) setFailed(true);
    } finally {
      busy.current = false;
      if (current()) setPending(false);
    }
  }
  const manualSource = overview.official_manual_source;
  return <Panel title="Find filings">
    <p>Source: {overview.provider_name}</p>
    <p className="muted">{overview.next_action}</p>
    {overview.manual_required ? <>
      <p>Automated filing discovery is not configured for this market.</p>
      {manualSource && sourceLink(manualSource.url) && <>
        <a href={sourceLink(manualSource.url)!} target="_blank" rel="noopener noreferrer">Official issuer reports</a>
        <p className="muted">Source selection checked {manualSource.checked_on}. Matched NSE ISIN {manualSource.security_isin}. Target annual years: {manualSource.target_years.join(", ")}.</p>
        <ul>{manualSource.required_documents.map(requirement => <li key={requirement}>{requirement}</li>)}</ul>
        <p>Upload the original PDF or add an excerpt with its exact page link below. Keep reporting period, currency, scale and standalone/consolidated basis explicit. Source selection does not approve a financial value.</p>
      </>}
    </> : <>
      <button type="button" className="secondary-button" disabled={pending} onClick={discover}>
        {pending ? "Checking filings…" : "Check for filings"}
      </button>
      <div aria-live="polite">
        {pending ? <p role="status">Contacting {overview.provider_name}…</p> : failed ?
          <p role="alert">Filing check unavailable. Try again. Stored filings are still listed below.</p> : result ? <>
            <p>Fact · {result.provider_name} · Checked {result.checked_at ? new Date(result.checked_at).toLocaleString("en-US") : "time unavailable"}. Results are a discovery preview; financial values still require review.</p>
            {result.filings.length ? <div className="table-wrap"><table>
              <thead><tr><th>Form</th><th>Filed</th><th>Report date</th><th>Accession</th><th>Source</th></tr></thead>
              <tbody>{result.filings.map(filing => <tr key={filing.accession_number}>
                <td>{filing.form_type}</td><td>{filing.filing_date}</td><td>{filing.report_date || "Not supplied"}</td>
                <td><code>{filing.accession_number}</code></td>
                <td>{sourceLink(filing.filing_url) ? <a href={sourceLink(filing.filing_url)!} target="_blank" rel="noopener noreferrer">Open filing</a> : "No URL"}</td>
              </tr>)}</tbody>
            </table></div> : <p>No filing candidates returned by this check.</p>}
          </> : <p>No provider check has been requested on this page.</p>}
      </div>
    </>}
  </Panel>;
}
