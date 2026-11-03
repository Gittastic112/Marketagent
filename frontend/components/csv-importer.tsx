"use client";

import { useId, useRef, useState } from "react";
import { Panel } from "@/components/page";
import { unwrapCsvTransferResponse } from "@/lib/csv-transfer";

type ImportError = {
  row_index: number;
  field: string | null;
  message: string;
};

type ImportPreviewRow = {
  row_index: number;
  data: Record<string, any>;
  is_valid: boolean;
  errors: ImportError[];
};

type ImportPreviewResponse = {
  is_preview: boolean;
  total_rows: number;
  valid_count: number;
  error_count: number;
  rows: ImportPreviewRow[];
};

type CsvImporterProps = {
  title: string;
  endpoint: string; // e.g. "/import/market-prices"
};

function transferErrorMessage(payload: any, fallback: string): string {
  if (Array.isArray(payload?.errors) && typeof payload.errors[0]?.message === "string") {
    return payload.errors[0].message;
  }
  if (typeof payload?.detail?.message === "string") return payload.detail.message;
  if (typeof payload?.detail === "string") return payload.detail;
  return fallback;
}

export function CsvImporter({ title, endpoint }: CsvImporterProps) {
  const [file, setFile] = useState<File | null>(null);
  const [preview, setPreview] = useState<ImportPreviewResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const fileInputId = useId();

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = e.target.files?.[0] || null;
    setFile(selectedFile);
    setPreview(null);
    setErrorMsg(null);
    setSuccessMsg(null);
  };

  const handlePreview = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!file) return;

    setLoading(true);
    setErrorMsg(null);
    setSuccessMsg(null);

    const formData = new FormData();
    formData.append("file", file);

    try {
      const res = await fetch(`/api/backend${endpoint}?preview=true`, {
        method: "POST",
        body: formData,
      });

      if (!res.ok) {
        const errorData = await res.json().catch(() => ({}));
        throw new Error(transferErrorMessage(errorData, "Upload failed"));
      }

      const data = unwrapCsvTransferResponse<ImportPreviewResponse>(
        await res.json(),
      );
      setPreview(data);
    } catch (err: any) {
      setErrorMsg(err.message || "An unexpected error occurred.");
    } finally {
      setLoading(false);
    }
  };

  const handleConfirm = async () => {
    if (!file) return;

    setLoading(true);
    setErrorMsg(null);

    const formData = new FormData();
    formData.append("file", file);

    try {
      const res = await fetch(`/api/backend${endpoint}?preview=false`, {
        method: "POST",
        body: formData,
      });

      if (!res.ok) {
        const errorData = await res.json().catch(() => ({}));
        throw new Error(transferErrorMessage(errorData, "Import failed"));
      }

      const data = unwrapCsvTransferResponse<{ imported_count: number }>(
        await res.json(),
      );
      setSuccessMsg(`Successfully imported ${data.imported_count} records.`);
      setFile(null);
      setPreview(null);
      if (fileInputRef.current) {
        fileInputRef.current.value = "";
      }
    } catch (err: any) {
      setErrorMsg(err.message || "An unexpected error occurred during import.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <Panel title={title}>
      <form onSubmit={handlePreview} className="form-grid">
        <div className="field">
          <label htmlFor={fileInputId}>CSV File</label>
          <input
            id={fileInputId}
            type="file"
            accept=".csv"
            onChange={handleFileChange}
            ref={fileInputRef}
            disabled={loading}
          />
        </div>
        <div className="button-row">
          <button type="submit" disabled={!file || loading}>
            {loading && !preview ? "Analyzing..." : "Preview Import"}
          </button>
        </div>
      </form>

      {errorMsg && (
        <div className="error-message" style={{ marginTop: "1rem", color: "var(--error-color)" }}>
          <strong>Error:</strong> {errorMsg}
        </div>
      )}

      {successMsg && (
        <div className="success-message" style={{ marginTop: "1rem", color: "var(--success-color)", fontWeight: "bold" }}>
          {successMsg}
        </div>
      )}

      {preview && (
        <div className="preview-results" style={{ marginTop: "1.5rem" }}>
          <h4 style={{ marginBottom: "1rem" }}>Preview Results</h4>
          <div className="stats-row" style={{ display: "flex", gap: "1rem", marginBottom: "1rem" }}>
            <span>Total Rows: {preview.total_rows}</span>
            <span style={{ color: "var(--success-color)" }}>Valid: {preview.valid_count}</span>
            <span style={{ color: preview.error_count > 0 ? "var(--error-color)" : "inherit" }}>
              Errors: {preview.error_count}
            </span>
          </div>

          {preview.error_count > 0 ? (
            <div className="errors-list" style={{ background: "var(--background-alt)", padding: "1rem", borderRadius: "4px" }}>
              <h5 style={{ color: "var(--error-color)", marginBottom: "0.5rem" }}>Row Errors</h5>
              <ul style={{ paddingLeft: "1.5rem", color: "var(--error-color)", fontSize: "0.875rem" }}>
                {preview.rows.filter((r) => !r.is_valid).map((row, idx) => (
                  <li key={idx} style={{ marginBottom: "0.25rem" }}>
                    Row {row.row_index}: {row.errors.map((e) => `[${e.field || "general"}] ${e.message}`).join(", ")}
                  </li>
                ))}
              </ul>
              <p style={{ marginTop: "1rem", fontSize: "0.875rem" }}>
                Please fix these errors in your CSV and try uploading again.
              </p>
            </div>
          ) : (
            <div className="button-row" style={{ marginTop: "1rem" }}>
              <button onClick={handleConfirm} disabled={loading} className="btn-primary">
                {loading ? "Importing..." : "Confirm Import"}
              </button>
            </div>
          )}
        </div>
      )}
    </Panel>
  );
}
