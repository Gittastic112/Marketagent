"use client";

import { useState, type FormEvent } from "react";
import { useRouter } from "next/navigation";
import { extractRetainedPdfPages } from "@/lib/api/financials";

export function PdfPageExtraction({ documentId }: { documentId: number }) {
  const router = useRouter();
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  async function extract(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (busy) return;
    const pages = String(new FormData(event.currentTarget).get("pages") || "");
    setBusy(true); setError(null); setMessage(null);
    try {
      const result = await extractRetainedPdfPages(documentId, pages);
      setMessage(`${result.scanned_page_count} additional pages scanned; ${result.created_count} new candidates need review. ${result.warnings.join(" ")}`);
      router.refresh();
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Page extraction failed. You can retry.");
    } finally { setBusy(false); }
  }
  return <details className="notice">
    <summary>Extract additional PDF pages</summary>
    <p>Uses the retained original. Previously extracted pages and reviewed values are preserved. Select up to 75 pages.</p>
    <form onSubmit={extract}>
      <fieldset disabled={busy} style={{ border: 0, padding: 0 }}>
        <label className="field"><span>Additional pages</span><input name="pages" required maxLength={500} placeholder="12-18, 24" /></label>
        <button type="submit">{busy ? "Extracting pages" : "Extract selected pages"}</button>
      </fieldset>
      {error && <p role="alert">{error}</p>}{message && <p role="status">{message}</p>}
    </form>
  </details>;
}
