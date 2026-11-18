"use client";

import { useEffect, useId, useRef, useState } from "react";
import { useRouter } from "next/navigation";

import { EmptyState, Panel } from "@/components/page";
import { LoadingState } from "@/components/ui/data-states";
import { createRequestGate } from "@/lib/latest-request";
import { applyPortfolioEvidence, previewPortfolioEvidence, type EvidenceApplyResult, type EvidencePreview } from "@/lib/api/portfolio-evidence";
import { EvidenceReviewTable } from "./evidence-review-table";

export function PortfolioEvidenceImporter({ portfolioId }: { portfolioId: number }) {
  return <PortfolioEvidenceImportSession key={portfolioId} portfolioId={portfolioId} />;
}

function PortfolioEvidenceImportSession({ portfolioId }: { portfolioId: number }) {
  const router = useRouter();
  const requests = useRef(createRequestGate());
  useEffect(() => () => requests.current.invalidate(), []);
  const inputId = useId();
  const fileInput = useRef<HTMLInputElement>(null);
  const [file, setFile] = useState<File | null>(null);
  const [preview, setPreview] = useState<EvidencePreview | null>(null);
  const [result, setResult] = useState<EvidenceApplyResult | null>(null);
  const [phase, setPhase] = useState<"idle" | "previewing" | "applying">("idle");
  const [error, setError] = useState<string | null>(null);

  function selectFile(selected: File | null) {
    requests.current.invalidate();
    setPhase("idle");
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
    if (!file || phase !== "idle") return;
    if (file.size > 2 * 1024 * 1024) { setError("The evidence CSV exceeds the 2 MiB limit."); return; }
    const isCurrent = requests.current.begin();
    setPhase("previewing");
    setPreview(null);
    setResult(null);
    setError(null);
    try {
      const data = await previewPortfolioEvidence(portfolioId, file);
      if (data.scope.portfolio_id !== portfolioId) {
        throw new Error("The returned preview belongs to another portfolio. Select the file and preview again.");
      }
      if (isCurrent()) setPreview(data);
    } catch (caught) {
      if (isCurrent()) setError(caught instanceof Error ? caught.message : "The evidence bundle could not be previewed.");
    } finally {
      if (isCurrent()) setPhase("idle");
    }
  }

  async function applyFile() {
    if (!file || !preview?.can_apply || phase !== "idle") return;
    const isCurrent = requests.current.begin();
    setPhase("applying");
    setError(null);
    try {
      const data = await applyPortfolioEvidence(portfolioId, file, preview.content_sha256);
      if (!isCurrent()) return;
      if (data.content_sha256 !== preview.content_sha256) throw new Error("The returned receipt does not match the previewed file. Reload the portfolio before retrying.");
      setResult(data);
      setFile(null);
      setPreview(null);
      if (fileInput.current) fileInput.current.value = "";
      router.refresh();
    } catch (caught) {
      if (isCurrent()) setError(caught instanceof Error ? caught.message : "The evidence bundle could not be applied.");
    } finally {
      if (isCurrent()) setPhase("idle");
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
            <span className={`badge ${preview.error_count ? "badge-danger" : "badge-success"}`}>
              {preview.can_apply ? "Ready to apply" : preview.error_count ? "Blocked" : "Already imported"}
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

          <EvidenceReviewTable key={preview.content_sha256} rows={preview.rows} />

          {preview.error_count ? (
            <p role="status" style={{ color: "var(--danger)", fontWeight: 600 }}>
              Apply is disabled. Correct every error and preview the revised file.
            </p>
          ) : null}
          {!preview.error_count && !preview.create_count ? <p role="status">Every row is an exact stored duplicate. No new facts need to be applied.</p> : null}
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
