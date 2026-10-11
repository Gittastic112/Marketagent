"use client";

import Link from "next/link";
import { useCallback, useEffect, useRef, useState } from "react";
import { Panel } from "@/components/page";
import { BriefSourceLibrary } from "@/components/brief-source-library";
import { analyzeBriefSource, pasteBriefSource, uploadBriefSource, type BriefSource } from "@/lib/api/brief-sources";
import type { Company } from "@/lib/api/companies";
import { fetchApi } from "@/lib/api/transport";
import { AI_PRIVACY_DISCLOSURE_VERSION } from "@/lib/ai-privacy";
import { useLatestResource } from "@/lib/use-latest-resource";

export function BriefSourceInbox() {
  const companyLoader = useCallback(() => fetchApi<Company[]>("/companies"), []);
  const catalog = useLatestResource(companyLoader);
  const companies = catalog.data ?? [];
  const [mode, setMode] = useState<"text" | "pdf">("text");
  const [refreshToken, setRefreshToken] = useState(0);
  const [savedSource, setSavedSource] = useState<BriefSource | null>(null);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");
  const [busy, setBusy] = useState<number | "upload" | "organize" | null>(null);
  const [consent, setConsent] = useState(false);
  const mounted = useRef(true);

  useEffect(() => { mounted.current = true; return () => { mounted.current = false; }; }, []);
  async function save(form: HTMLFormElement) {
    setBusy("upload"); setError(""); setMessage(""); setSavedSource(null);
    const data = new FormData(form);
    try {
      let source: BriefSource;
      if (mode === "pdf") {
        const file = data.get("file");
        if (!(file instanceof File) || !file.size || file.size > 12 * 1024 * 1024) throw new Error("Choose a PDF up to 12 MB.");
        for (const field of ["source_url", "as_of_date", "page_ranges"]) if (!data.get(field)) data.delete(field);
        source = await uploadBriefSource(data);
      } else {
        source = await pasteBriefSource({ company_id: Number(data.get("company_id")), title: String(data.get("title")),
          text: String(data.get("text")), source_url: String(data.get("source_url") || "") || null,
          as_of_date: String(data.get("as_of_date") || "") || null });
      }
      if (mounted.current) {
        setSavedSource(source); setRefreshToken(current => current + 1);
        setMessage(source.archived_at ? "This source already exists in your archive. It has not been restored or scanned. Open it below to inspect or restore it."
          : "Source saved privately. Review the extracted text, then scan when ready. Current search filters are preserved."); form.reset();
      }
    } catch (e) { if (mounted.current) setError(e instanceof Error ? e.message : "Source could not be saved."); }
    finally { if (mounted.current) setBusy(null); }
  }
  async function analyze(id: number) {
    setBusy(id); setError(""); setSavedSource(null); setMessage("Scanning the selected source. This may take up to a minute.");
    try {
      await analyzeBriefSource(id, AI_PRIVACY_DISCLOSURE_VERSION);
      if (mounted.current) setMessage("Scan complete. Review the source-backed suggestions. The list reflects your current filters.");
    } catch (e) {
      if (mounted.current) { setError(e instanceof Error ? e.message : "Analysis unavailable. Retry explicitly."); setMessage(""); }
    } finally { if (mounted.current) { setBusy(null); setRefreshToken(current => current + 1); } }
  }

  return <Panel title="Research inbox" actions={<span className="badge badge-outline">Private sources → reviewable inputs</span>}>
    <p>Add an article, earnings note or PDF. AI ranks what matters and links the evidence to valuation inputs worth reviewing.</p>
    <p><Link className="btn btn-secondary" prefetch={false} href="/daily-brief/triage">Compare findings across sources →</Link></p>
    {catalog.status === "loading" && <p role="status">Loading companies…</p>}
    {catalog.status === "error" && <div role="alert" className="basis-note">Companies unavailable: {catalog.error} <button className="btn btn-secondary" onClick={() => void catalog.reload().catch(() => {})}>Retry companies</button></div>}
      <div className="brief-intake-layout">
        <form onSubmit={event => { event.preventDefault(); void save(event.currentTarget); }} className="brief-intake-form">
          <fieldset disabled={busy !== null || companies.length === 0}>
            <legend className="sr-only">Add a private research source</legend>
            <div className="brief-intake-grid">
              <label>Company<select name="company_id" required defaultValue=""><option value="" disabled>Select company</option>{companies.map(company => <option key={company.id} value={company.id}>{company.ticker} · {company.name}</option>)}</select></label>
              <label>Source title<input name="title" required maxLength={240} placeholder="Earnings release, article or research note" /></label>
              <label>Source date, if known<input name="as_of_date" type="date" max={new Date().toISOString().slice(0, 10)} /></label>
              <label>Source URL, optional<input name="source_url" type="url" maxLength={1000} placeholder="https://…" /></label>
            </div>
            <label>Input format<select value={mode} onChange={event => setMode(event.target.value as "text" | "pdf")}><option value="text">Paste text</option><option value="pdf">Upload PDF</option></select></label>
            {mode === "text" ? <label>Source text<textarea name="text" required minLength={40} maxLength={60000} rows={6} placeholder="Paste the original text here, including its context and date where possible." /></label>
              : <><label>PDF file<input name="file" type="file" accept="application/pdf,.pdf" required /></label><label>Pages to extract, optional<input name="page_ranges" maxLength={200} placeholder="For example: 1-4,8" /></label><p className="muted">Up to 12 MB, 20 selected pages and 60,000 extracted characters. Text-based PDFs only. No OCR or chart interpretation.</p></>}
            <button className="btn btn-primary" type="submit">{busy === "upload" ? "Saving source…" : "Save source privately"}</button>
          </fieldset>
        </form>
        <aside className="brief-intake-note"><h3>Evidence first. Changes stay yours.</h3><ol><li>Save and inspect the original source.</li><li>Explicitly scan its text with the configured AI provider.</li><li>Review ranked findings and exact passages.</li><li>Open the relevant draft field and decide whether to edit it.</li></ol>
          <p>Saving does not send anything to AI. Scanning sends only this source&apos;s extracted text, source date, company name/ticker and a field-name catalog. It does not send stored holdings, thesis notes or valuation values.</p>
          <label className="brief-consent"><input type="checkbox" checked={consent} onChange={event => setConsent(event.target.checked)} />I understand this data will be sent to the configured AI provider when I select Scan.</label>
          <Link prefetch={false} href="/data-health">Check AI connection and data health →</Link>
        </aside>
      </div>
      {catalog.status === "ready" && !companies.length && <p className="basis-note">Add a company before importing research.</p>}
    {error && <div role="alert" className="basis-note">{error}</div>}
    {message && <p role="status">{message}</p>}
    {savedSource && <p><Link prefetch={false} href={`/daily-brief/sources/${savedSource.id}`}>Inspect saved source: {savedSource.title}</Link></p>}
    <BriefSourceLibrary companies={companies} consent={consent} busy={busy} refreshToken={refreshToken} onScan={analyze}
      onOrganizeBusy={pending => { if (mounted.current) setBusy(pending ? "organize" : null); }}
      onOrganized={notice => { if (mounted.current) { setMessage(notice); setError(""); setSavedSource(null); setRefreshToken(current => current + 1); } }} />
  </Panel>;
}
