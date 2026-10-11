"use client";

import { useId, useRef, useState } from "react";
import { useRouter } from "next/navigation";

import { EmptyState, Panel } from "@/components/page";
import { LoadingState } from "@/components/ui/data-states";
import type { ApiResponse } from "@/lib/api";


type EvidenceRowError = {
  row_index: number;
  field: string;
  message: string;
};

type EvidencePreviewRow = {
  row_index: number;
  record_type: string | null;
  action: "create" | "skip" | "error";
  message: string;
  errors: EvidenceRowError[];
};

type EvidencePreview = {
  is_preview: true;
  filename: string;
  content_sha256: string;
  byte_size: number;
  total_rows: number;
  create_count: number;
  skip_count: number;
  error_count: number;
  market_price_count: number;
  fx_rate_count: number;
  can_apply: boolean;
  claim_type: "Fact";
  contains_mock_data: false;
  scope: {
    portfolio_id: number;
    portfolio_name: string;
    holding_tickers: string[];
    benchmark_ticker: string | null;
    allowed_fx_pairs: string[];
  };
  rows: EvidencePreviewRow[];
};

type EvidenceApplyResult = {
  status: "completed";
  processing_run_id: number;
  content_sha256: string;
  created_count: number;
  market_prices_created: number;
  fx_rates_created: number;
  skipped_duplicate_count: number;
  contains_mock_data: false;
  claim_type: "Fact";
};

function responseError(payload: unknown, fallback: string): string {
  if (!payload || typeof payload !== "object") return fallback;
  const body = payload as {
    detail?: string | { message?: string };
    errors?: Array<{ message?: string }>;
  };
  if (typeof body.detail === "string") return body.detail;
  if (typeof body.detail?.message === "string") return body.detail.message;
  if (typeof body.errors?.[0]?.message === "string") return body.errors[0].message;
  return fallback;
}

function actionBadge(action: EvidencePreviewRow["action"]) {
  const className = action === "create" ? "badge-success" : action === "skip" ? "badge-warn" : "badge-danger";
  return <span className={`badge ${className}`}>{action}</span>;
}

export function PortfolioEvidenceImporter({ portfolioId }: { portfolioId: number }) {
  const router = useRouter();
  const inputId = useId();
  const fileInput = useRef<HTMLInputElement>(null);
  const [file, setFile] = useState<File | null>(null);
  const [preview, setPreview] = useState<EvidencePreview | null>(null);
  const [result, setResult] = useState<EvidenceApplyResult | null>(null);
  const [phase, setPhase] = useState<"idle" | "previewing" | "applying">("idle");
  const [error, setError] = useState<string | null>(null);

  function selectFile(selected: File | null) {
    setFile(selected);
    setPreview(null);
    setResult(null);
    setError(null);
  }

  function clearFile() {
    selectFile(null);
    if (fileInput.current) fileInput.current.value = "";
  }

  async function previewFile(event: React.FormEvent) {
    event.preventDefault();
    if (!file) return;
    setPhase("previewing");
    setPreview(null);
    setResult(null);
    setError(null);
    const formData = new FormData();
    formData.append("file", file);
    try {
      const response = await fetch(
        `/api/backend/portfolios/${portfolioId}/evidence-bundle/preview`,
        { method: "POST", body: formData },
      );
      const payload = (await response.json().catch(() => null)) as ApiResponse<EvidencePreview> | null;
      if (!response.ok || !payload?.data) {
        throw new Error(responseError(payload, "The evidence bundle could not be previewed."));
      }
      setPreview(payload.data);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "The evidence bundle could not be previewed.");
    } finally {
      setPhase("idle");
    }
  }

  async function applyFile() {
    if (!file || !preview?.can_apply) return;
    setPhase("applying");
    setError(null);
    const formData = new FormData();
    formData.append("file", file);
    formData.append("expected_sha256", preview.content_sha256);
    try {
      const response = await fetch(
        `/api/backend/portfolios/${portfolioId}/evidence-bundle/apply`,
        { method: "POST", body: formData },
      );
      const payload = (await response.json().catch(() => null)) as ApiResponse<EvidenceApplyResult> | null;
      if (!response.ok || !payload?.data) {
        throw new Error(responseError(payload, "The evidence bundle could not be applied."));
      }
      setResult(payload.data);
      setFile(null);
      setPreview(null);
      if (fileInput.current) fileInput.current.value = "";
      router.refresh();
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "The evidence bundle could not be applied.");
    } finally {
      setPhase("idle");
    }
  }

  const busy = phase !== "idle";
  return (
    <Panel title="Source-labeled price and FX evidence">
      <p style={{ color: "var(--text-secondary)", lineHeight: 1.55, marginTop: 0 }}>
        Bulk-load genuine historical prices and FX observations needed by the real-input smoke. Every row is a user-supplied <strong>Fact</strong> and must name its upstream provider, source URL, and source timestamp. The app validates provenance and conflicts, but does not independently verify the provider.
      </p>
      <div style={{ alignItems: "center", display: "flex", flexWrap: "wrap", gap: "0.75rem", marginBottom: "1rem" }}>
        <a
          className="button-secondary"
          href={`/api/backend/portfolios/${portfolioId}/evidence-bundle/template`}
        >
          Download CSV template
        </a>
        <span style={{ color: "var(--text-secondary)", fontSize: "0.82rem" }}>
          Limits: UTF-8 CSV, 2 MiB, 5,000 rows. Exact duplicates are skipped. Conflicts block the whole apply.
        </span>
      </div>

      <form className="form-grid" onSubmit={previewFile}>
        <div className="field">
          <label htmlFor={inputId}>Evidence CSV</label>
          <input
            accept=".csv,text/csv"
            disabled={busy}
            id={inputId}
            onChange={(event) => selectFile(event.target.files?.[0] || null)}
            ref={fileInput}
            type="file"
          />
        </div>
        <div className="button-row">
          <button disabled={!file || busy} type="submit">
            {phase === "previewing" ? "Validating..." : "Preview evidence"}
          </button>
        </div>
      </form>

      {phase === "previewing" ? <LoadingState message="Validating ownership, provenance, duplicates, and conflicts..." /> : null}

      {error ? (
        <div aria-live="polite" role="alert" style={{ background: "var(--danger-bg)", border: "1px solid var(--danger)", borderRadius: "8px", color: "var(--danger)", marginTop: "1rem", padding: "0.9rem" }}>
          <strong>Evidence import error:</strong> {error}
        </div>
      ) : null}

      {result ? (
        <div aria-live="polite" style={{ background: "var(--success-bg)", border: "1px solid var(--success)", borderRadius: "8px", marginTop: "1rem", padding: "0.9rem" }}>
          <strong>Import completed.</strong> Created {result.market_prices_created} market price(s) and {result.fx_rates_created} FX observation(s); skipped {result.skipped_duplicate_count} exact duplicate(s). ProcessingRun {result.processing_run_id} retains the bundle hash and audit counts.
        </div>
      ) : null}

      {!file && !preview && !result && phase === "idle" ? (
        <EmptyState label="No evidence file selected. Download the template, retain only genuine portfolio or benchmark facts, then preview it." />
      ) : null}

      {preview ? (
        <section aria-labelledby="evidence-preview-title" style={{ marginTop: "1.25rem" }}>
          <div style={{ alignItems: "flex-start", display: "flex", flexWrap: "wrap", gap: "0.75rem", justifyContent: "space-between" }}>
            <div>
              <h3 id="evidence-preview-title" style={{ margin: 0 }}>Server preview</h3>
              <p style={{ color: "var(--text-secondary)", fontSize: "0.82rem", margin: "0.35rem 0 0", overflowWrap: "anywhere" }}>
                {preview.filename}, {preview.byte_size.toLocaleString()} bytes, SHA-256 {preview.content_sha256}
              </p>
            </div>
            <span className={`badge ${preview.can_apply ? "badge-success" : "badge-danger"}`}>
              {preview.can_apply ? "Ready to apply" : "Blocked"}
            </span>
          </div>

          <div style={{ display: "grid", gap: "0.65rem", gridTemplateColumns: "repeat(auto-fit, minmax(140px, 1fr))", marginTop: "1rem" }}>
            {[
              ["Rows", preview.total_rows],
              ["Create", preview.create_count],
              ["Skip exact", preview.skip_count],
              ["Errors", preview.error_count],
              ["Prices", preview.market_price_count],
              ["FX", preview.fx_rate_count],
            ].map(([label, value]) => (
              <div key={label} style={{ background: "var(--surface)", border: "1px solid var(--border)", borderRadius: "8px", padding: "0.75rem" }}>
                <span style={{ color: "var(--text-secondary)", display: "block", fontSize: "0.75rem" }}>{label}</span>
                <strong style={{ fontSize: "1.1rem" }}>{value}</strong>
              </div>
            ))}
          </div>

          <p style={{ color: "var(--text-secondary)", fontSize: "0.82rem", lineHeight: 1.5 }}>
            Scope: holdings {preview.scope.holding_tickers.join(", ") || "none"}; benchmark {preview.scope.benchmark_ticker || "not configured"}; FX pairs {preview.scope.allowed_fx_pairs.join(", ") || "none required"}.
          </p>

          <div className="table-wrap">
            <table>
              <thead><tr><th>CSV row</th><th>Type</th><th>Action</th><th>Result</th></tr></thead>
              <tbody>
                {preview.rows.map((row) => (
                  <tr key={row.row_index}>
                    <td>{row.row_index}</td>
                    <td>{row.record_type || "Invalid"}</td>
                    <td>{actionBadge(row.action)}</td>
                    <td>
                      {row.errors.length
                        ? row.errors.map((item) => `${item.field}: ${item.message}`).join("; ")
                        : row.message}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {preview.error_count ? (
            <p role="status" style={{ color: "var(--danger)", fontWeight: 600 }}>
              Apply is disabled. Correct every error and preview the revised file.
            </p>
          ) : null}
          <div className="button-row">
            <button disabled={!preview.can_apply || busy} onClick={applyFile} type="button">
              {phase === "applying" ? "Applying atomically..." : `Apply ${preview.create_count} fact(s)`}
            </button>
            <button className="button-secondary" disabled={busy} onClick={clearFile} type="button">
              Clear preview
            </button>
          </div>
          {phase === "applying" ? <LoadingState message="Revalidating the exact file and writing all accepted facts atomically..." /> : null}
        </section>
      ) : null}
    </Panel>
  );
}
