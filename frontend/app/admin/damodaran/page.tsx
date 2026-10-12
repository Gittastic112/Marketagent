"use client";

import { useState, useEffect } from "react";
import { PageHeader, Panel, ErrorState, LoadingState } from "@/components/page";
import { fetchApiResponse, postApi, postFormApi, type ApiErrorDetail } from "@/lib/api";

type DamodaranFile = {
  id: number;
  filename: string;
  dataset_code: string;
  country: string | null;
  region: string | null;
  created_at: string;
  source_sha256: string | null;
  source_byte_size: number | null;
  source_as_of: string | null;
  date_confidence: string;
  canonical_source_path: string | null;
  import_kind: string;
  is_active: boolean;
  superseded_at: string | null;
  row_count: number | null;
  notes: string | null;
};

export default function AdminDamodaranPage() {
  const [files, setFiles] = useState<DamodaranFile[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<ApiErrorDetail[] | null>(null);

  // Upload Form State
  const [uploading, setUploading] = useState(false);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const [uploadSuccess, setUploadSuccess] = useState<string | null>(null);
  const [rollbackTarget, setRollbackTarget] = useState<number | null>(null);
  const [rollbackMessage, setRollbackMessage] = useState<string | null>(null);
  const [rollbackError, setRollbackError] = useState<string | null>(null);

  // Form fields
  const [fileToUpload, setFileToUpload] = useState<File | null>(null);
  const [datasetCode, setDatasetCode] = useState("implied_erp");

  useEffect(() => {
    fetchFiles();
  }, []);

  const fetchFiles = async () => {
    setLoading(true);
    try {
      const res = await fetchApiResponse<DamodaranFile[]>("/api/admin/damodaran/files");
      setFiles(res.data || []);
      setError(res.errors?.length ? res.errors : null);
    } catch (err: unknown) {
      setError([{ code: "damodaran_files_failed", message: err instanceof Error ? err.message : "Failed to fetch files" }]);
    } finally {
      setLoading(false);
    }
  };

  const handleUpload = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!fileToUpload) return;

    setUploading(true);
    setUploadError(null);
    setUploadSuccess(null);

    const formData = new FormData();
    formData.append("file", fileToUpload);
    formData.append("dataset_code", datasetCode);

    try {
      await postFormApi(`/api/admin/damodaran/import`, formData);

      setUploadSuccess(`Parsed and recorded metadata for ${fileToUpload.name}. Typed benchmark rows were not imported.`);
      setFileToUpload(null);
      fetchFiles(); // Refresh list
    } catch (err: unknown) {
      setUploadError(err instanceof Error ? err.message : "Failed to inspect workbook");
    } finally {
      setUploading(false);
    }
  };

  const handleRollback = async (fileId: number) => {
    try {
      setRollbackError(null);
      await postApi(`/api/admin/damodaran/${fileId}/rollback`, {});
      setRollbackMessage(`Import #${fileId} was rolled back.`);
      setRollbackTarget(null);
      await fetchFiles();
    } catch (err: unknown) {
      setRollbackError(`Failed to rollback: ${err instanceof Error ? err.message : "Unknown error"}`);
    }
  };

  return (
    <div className="flex flex-col gap-6 w-full max-w-5xl mx-auto py-8">
      <PageHeader eyebrow="Administration" title="Damodaran Source Versions" />

      <Panel title="Inspect Workbook Metadata">
        <p className="text-sm text-gray-500 mb-4">
          Parse an Excel workbook and record its hash, source date, and sheet metadata. This form does not load typed benchmark rows; use a reviewed source-specific importer for application data.
        </p>

        {uploadError && (
          <div className="bg-red-50 text-red-700 p-3 rounded mb-4 text-sm">
            {uploadError}
          </div>
        )}

        {uploadSuccess && (
          <div className="bg-green-50 text-green-700 p-3 rounded mb-4 text-sm">
            {uploadSuccess}
          </div>
        )}

        <form onSubmit={handleUpload} className="flex flex-col gap-4">
          <div className="flex flex-col gap-1">
            <label className="text-sm font-medium" htmlFor="damodaran-dataset-code">Dataset Type</label>
            <select
              id="damodaran-dataset-code"
              value={datasetCode}
              onChange={(e) => setDatasetCode(e.target.value)}
              className="border border-gray-300 rounded p-2 text-sm w-full max-w-xs"
            >
              <option value="implied_erp">Implied ERP (implied_erp.xls)</option>
              <option value="country_risk">Country Risk (ctryprem.xls)</option>
              <option value="default_spreads">Default Spreads (ratings.xls)</option>
              <option value="industry_betas">Industry Betas (betas.xls)</option>
            </select>
          </div>

          <div className="flex flex-col gap-1">
            <label className="text-sm font-medium" htmlFor="damodaran-workbook">Excel File</label>
            <input
              id="damodaran-workbook"
              type="file"
              accept=".xls,.xlsx"
              onChange={(e) => setFileToUpload(e.target.files?.[0] || null)}
              className="border border-gray-300 rounded p-2 text-sm w-full max-w-md"
            />
          </div>

          <button
            type="submit"
            disabled={!fileToUpload || uploading}
            className="bg-blue-600 hover:bg-blue-700 text-white font-medium py-2 px-4 rounded w-fit disabled:opacity-50"
          >
            {uploading ? "Parsing..." : "Parse Workbook"}
          </button>
        </form>
      </Panel>

      <Panel title="Import History">
        {loading ? (
          <LoadingState message="Loading import history..." />
        ) : error ? (
          <ErrorState message="Failed to load import history" errors={error} />
        ) : files.length === 0 ? (
          <p className="text-sm text-gray-500 italic p-4">No datasets have been imported yet.</p>
        ) : (
          <div tabIndex={0} className="overflow-x-auto">
            <table className="w-full text-sm text-left border-collapse">
              <thead className="bg-gray-50 text-gray-700">
                <tr>
                  <th className="px-4 py-3 border-b font-medium">Date Imported</th>
                  <th className="px-4 py-3 border-b font-medium">Dataset</th>
                  <th className="px-4 py-3 border-b font-medium">Source</th>
                  <th className="px-4 py-3 border-b font-medium">Version</th>
                  <th className="px-4 py-3 border-b font-medium">Actions</th>
                </tr>
              </thead>
              <tbody>
                {files.map((f) => (
                  <tr key={f.id} className="border-b hover:bg-gray-50">
                    <td className="px-4 py-3">{new Date(f.created_at).toLocaleString()}</td>
                    <td className="px-4 py-3">
                      <strong>#{f.id} {f.dataset_code}</strong>
                      <div className="text-gray-500">{f.country || f.region || "Global"}</div>
                    </td>
                    <td className="px-4 py-3 text-gray-600">
                      <strong>{f.filename}</strong>
                      <div className="text-gray-500">{f.canonical_source_path || "No canonical path"}</div>
                      <div className="font-mono text-xs text-gray-500">{f.source_sha256 ? f.source_sha256.slice(0, 16) : "No source hash"}</div>
                    </td>
                    <td className="px-4 py-3 text-gray-600">
                      <strong>{f.is_active ? "Active" : "Inactive"} | {f.import_kind.replaceAll("_", " ")}</strong>
                      <div className="text-gray-500">Source {f.source_as_of || "unknown"} | {f.date_confidence}</div>
                      <div className="text-gray-500">{f.row_count === null ? "No typed rows" : `${f.row_count.toLocaleString()} typed rows`}</div>
                    </td>
                    <td className="px-4 py-3">
                      {f.import_kind === "metadata_only" && !f.is_active ? (
                        <button
                          onClick={() => {
                            setRollbackTarget(f.id);
                            setRollbackMessage(null);
                            setRollbackError(null);
                          }}
                          className="text-red-600 hover:text-red-800 font-medium"
                        >
                          Delete metadata
                        </button>
                      ) : (
                        <span className="text-gray-500">Preserved</span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
        {rollbackTarget !== null ? (
          <div role="alertdialog" aria-labelledby="rollback-title" className="mt-4 border border-red-200 bg-red-50 p-3 text-sm text-red-800">
            <strong id="rollback-title">Delete metadata upload #{rollbackTarget}?</strong>
            <p>This removes only the inactive metadata record.</p>
            <div className="flex gap-2">
              <button type="button" onClick={() => handleRollback(rollbackTarget)} className="font-medium">Confirm delete</button>
              <button type="button" onClick={() => setRollbackTarget(null)} className="font-medium">Cancel</button>
            </div>
          </div>
        ) : null}
        {rollbackMessage ? <p role="status" className="mt-4 text-sm text-green-700">{rollbackMessage}</p> : null}
        {rollbackError ? <p role="alert" className="mt-4 text-sm text-red-700">{rollbackError}</p> : null}
      </Panel>
    </div>
  );
}
