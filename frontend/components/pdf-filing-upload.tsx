"use client";

import { FormEvent, useRef, useState } from "react";
import { Upload } from "lucide-react";
import { useRouter } from "next/navigation";

import { postFormApi, type PdfFinancialExtractionResult } from "@/lib/api";


const MAX_PDF_BYTES = 40 * 1024 * 1024;

export function PdfFilingUpload({ companyId }: { companyId: number }) {
  const formRef = useRef<HTMLFormElement>(null);
  const router = useRouter();
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<PdfFinancialExtractionResult | null>(null);

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = event.currentTarget;
    const formData = new FormData(form);
    const file = formData.get("file");
    if (!(file instanceof File) || file.size === 0) {
      setError("Select a PDF filing.");
      return;
    }
    if (file.size > MAX_PDF_BYTES) {
      setError("PDF is too large. Maximum size is 40 MB.");
      return;
    }
    if (!file.name.toLowerCase().endsWith(".pdf")) {
      setError("Only PDF files are accepted.");
      return;
    }
    const publishedAt = formData.get("published_at");
    if (typeof publishedAt === "string" && publishedAt) {
      formData.set("published_at", `${publishedAt}T00:00:00Z`);
    } else {
      formData.delete("published_at");
    }

    setSubmitting(true);
    setError(null);
    setResult(null);
    try {
      const nextResult = await postFormApi<PdfFinancialExtractionResult>(
        `/api/companies/${companyId}/filings/pdf`,
        formData,
      );
      setResult(nextResult);
      formRef.current?.reset();
      router.refresh();
    } catch (uploadError) {
      setError(uploadError instanceof Error ? uploadError.message : "PDF upload failed.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <form ref={formRef} onSubmit={submit} className="form-grid">
      <label className="field field-full">
        <span>PDF filing</span>
        <input name="file" type="file" accept="application/pdf,.pdf" required disabled={submitting} />
      </label>
      <label className="field field-full">
        <span>Document type</span>
        <select name="document_type" defaultValue="annual_report" required disabled={submitting}>
          <option value="annual_report">Annual report</option>
          <option value="quarterly_result">Quarterly result</option>
          <option value="investor_presentation">Investor presentation</option>
          <option value="exchange_announcement">Exchange announcement</option>
          <option value="shareholding_pattern">Shareholding pattern</option>
          <option value="corporate_action">Corporate action</option>
        </select>
      </label>
      <label className="field field-full">
        <span>Title</span>
        <input name="title" type="text" maxLength={500} placeholder="FY2026 Annual Report" disabled={submitting} />
      </label>
      <label className="field field-full">
        <span>Published date</span>
        <input name="published_at" type="date" disabled={submitting} />
      </label>
      <label className="field field-full">
        <span>Official source URL</span>
        <input name="source_url" type="url" maxLength={1000} placeholder="https://nsearchives.nseindia.com/..." disabled={submitting} />
      </label>
      <label className="field field-full">
        <span>Target pages</span>
        <input name="page_ranges" type="text" maxLength={500} placeholder="465-470, 542" disabled={submitting} />
      </label>
      <div className="button-row field-full">
        <button type="submit" disabled={submitting}>
          <Upload aria-hidden="true" size={16} />
          {submitting ? "Processing PDF" : "Upload PDF"}
        </button>
      </div>
      {error ? <p className="field-full" role="alert" style={{ color: "var(--danger)", margin: 0 }}>{error}</p> : null}
      {result ? (
        <div className="field-full" role="status">
          <p style={{ margin: 0 }}>
            {result.scanned_page_count} of {result.page_count} pages scanned, {result.table_count} tables, {result.created_count} candidates.
          </p>
          {result.warnings.length ? (
            <p className="muted" style={{ marginBottom: 0 }}>{result.warnings.join(" / ")}</p>
          ) : null}
        </div>
      ) : null}
    </form>
  );
}
