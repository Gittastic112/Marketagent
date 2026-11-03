"use client";

import { useId, useState } from "react";
import { postApiFormData } from "@/lib/api";

interface CsvUploadFormProps {
  endpoint: string;
  label: string;
}

export function CsvUploadForm({ endpoint, label }: CsvUploadFormProps) {
  const fileInputId = useId();
  const [file, setFile] = useState<File | null>(null);
  const [status, setStatus] = useState<"idle" | "uploading" | "success" | "error">("idle");
  const [message, setMessage] = useState<string>("");

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!file) return;

    setStatus("uploading");
    setMessage("");

    const formData = new FormData();
    formData.append("file", file);

    try {
      const response = await postApiFormData<{ status: string; imported_count: number }>(endpoint, formData);
      setStatus("success");
      setMessage(`Successfully imported ${response.imported_count} records.`);
      setFile(null);
    } catch (err: unknown) {
      setStatus("error");
      setMessage(err instanceof Error ? err.message : "Failed to import CSV");
    }
  };

  return (
    <form onSubmit={handleSubmit} className="flex flex-col gap-2 p-3 bg-gray-50 border border-gray-200 rounded-md">
      <label className="text-sm font-medium" htmlFor={fileInputId}>{label}</label>
      <div className="flex items-center gap-2">
        <input
          id={fileInputId}
          type="file"
          accept=".csv"
          onChange={(e) => setFile(e.target.files?.[0] || null)}
          className="text-sm file:mr-4 file:py-1 file:px-3 file:rounded-md file:border-0 file:text-sm file:font-semibold file:bg-gray-200 file:text-gray-700 hover:file:bg-gray-300"
          required
        />
        <button
          type="submit"
          disabled={!file || status === "uploading"}
          className="secondary-button text-sm px-3 py-1"
        >
          {status === "uploading" ? "Uploading..." : "Upload"}
        </button>
      </div>
      {message && (
        <p aria-live="polite" className={`text-xs mt-1 ${status === "success" ? "text-green-600" : "text-red-600"}`}>
          {message}
        </p>
      )}
    </form>
  );
}
