"use client";

import { useId, useState } from "react";
import { uploadScreenerExport } from "@/lib/api";

export function ScreenerUpload({ companyId }: { companyId: number }) {
  const inputId = useId();
  const [file, setFile] = useState<File | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);

  const handleUpload = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!file) return;

    setLoading(true);
    setError(null);
    setSuccessMsg(null);

    try {
      const res = await uploadScreenerExport(companyId, file);
      setSuccessMsg(res.status === "original_restored"
        ? "Original workbook restored. Existing candidates and reviewed values were preserved."
        : res.extracted_count === 0 ? "Original workbook saved. No supported metrics were extracted."
        : `Original workbook saved. ${res.extracted_count} extracted metrics are pending review below.`);
      setFile(null);
      setTimeout(() => window.location.reload(), 1500);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to upload file");
    } finally {
      setLoading(false);
    }
  };

  return (
    <form onSubmit={handleUpload} className="mt-4 flex flex-col gap-2 p-4 border rounded-md bg-muted">
      <div className="flex flex-col gap-1">
        <label htmlFor={inputId} className="text-sm font-medium text-foreground">Upload Screener.in Export (.xlsx)</label>
        <input
          id={inputId}
          type="file"
          accept=".xlsx"
          onChange={(e) => setFile(e.target.files?.[0] || null)}
          className="text-sm text-muted-foreground file:mr-4 file:py-2 file:px-4 file:rounded-md file:border-0 file:text-sm file:font-semibold file:bg-[var(--accent-light)] file:text-[var(--accent)] hover:file:bg-[var(--accent-light)]"
        />
      </div>

      {error && <p className="text-[var(--danger)] text-sm mt-1">{error}</p>}
      {successMsg && <p className="text-[var(--success)] text-sm mt-1">{successMsg}</p>}

      <button
        type="submit"
        disabled={!file || loading}
        className="mt-2 inline-flex items-center justify-center rounded-md bg-[var(--accent)] px-3 py-2 text-sm font-semibold text-white shadow-sm hover:bg-[var(--accent)] focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[var(--accent)] disabled:opacity-50 w-fit"
      >
        {loading ? "Uploading..." : "Upload & Parse"}
      </button>
    </form>
  );
}
