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
      setSuccessMsg(`Successfully extracted ${res.extracted_count} metrics. They are now pending review below.`);
      setFile(null);
      setTimeout(() => window.location.reload(), 1500);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to upload file");
    } finally {
      setLoading(false);
    }
  };

  return (
    <form onSubmit={handleUpload} className="mt-4 flex flex-col gap-2 p-4 border rounded-md bg-gray-50">
      <div className="flex flex-col gap-1">
        <label htmlFor={inputId} className="text-sm font-medium text-gray-700">Upload Screener.in Export (.xlsx)</label>
        <input
          id={inputId}
          type="file"
          accept=".xlsx"
          onChange={(e) => setFile(e.target.files?.[0] || null)}
          className="text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-md file:border-0 file:text-sm file:font-semibold file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100"
        />
      </div>

      {error && <p className="text-red-500 text-sm mt-1">{error}</p>}
      {successMsg && <p className="text-green-600 text-sm mt-1">{successMsg}</p>}

      <button
        type="submit"
        disabled={!file || loading}
        className="mt-2 inline-flex items-center justify-center rounded-md bg-blue-600 px-3 py-2 text-sm font-semibold text-white shadow-sm hover:bg-blue-500 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-blue-600 disabled:opacity-50 w-fit"
      >
        {loading ? "Uploading..." : "Upload & Parse"}
      </button>
    </form>
  );
}
