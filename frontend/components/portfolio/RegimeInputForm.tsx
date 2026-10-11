"use client";

import { useState } from "react";
import { submitMarketRegimeInput, MarketRegimeInputCreate } from "@/lib/api";
import { useRouter } from "next/navigation";

export function RegimeInputForm() {
  const [metricName, setMetricName] = useState<MarketRegimeInputCreate["metric_name"]>("options");
  const [value, setValue] = useState("");
  const [asOfDate, setAsOfDate] = useState(new Date().toISOString().split("T")[0]);
  const [inputType, setInputType] = useState<MarketRegimeInputCreate["input_type"]>("manual");
  const [sourceName, setSourceName] = useState("");
  const [sourceUrl, setSourceUrl] = useState("");
  const [methodology, setMethodology] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState<string | null>(null);
  const router = useRouter();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);
    setSubmitError(null);
    try {
      await submitMarketRegimeInput({
        metric_name: metricName,
        value: parseFloat(value),
        as_of_date: asOfDate,
        source_url: sourceUrl.trim() || null,
        source_name: sourceName.trim(),
        input_type: inputType,
        methodology: methodology.trim(),
      });
      setValue("");
      router.refresh();
    } catch (error) {
      setSubmitError(error instanceof Error ? error.message : "Failed to submit regime input.");
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} style={{ display: "flex", flexDirection: "column", gap: "1rem" }}>
      {submitError ? <p role="alert" style={{ color: "var(--danger)", margin: 0 }}>{submitError}</p> : null}
      <div>
        <label htmlFor="metric-name" style={{ display: "block", marginBottom: "0.5rem" }}>Metric Name</label>
        <select
          id="metric-name"
          value={metricName}
          onChange={(e) => setMetricName(e.target.value as MarketRegimeInputCreate["metric_name"])}
          style={{ padding: "0.5rem", borderRadius: "4px", width: "100%", background: "var(--bg-secondary)", color: "var(--text-primary)", border: "1px solid var(--border-color)" }}
        >
          <option value="options">Options (Weight 30%)</option>
          <option value="liquidity">Liquidity (Weight 25%)</option>
          <option value="volume">Volume (Weight 15%)</option>
          <option value="breadth">Breadth (Weight 15%)</option>
          <option value="macro">Macro (Weight 15%)</option>
        </select>
      </div>
      <div>
        <label htmlFor="normalized-score" style={{ display: "block", marginBottom: "0.5rem" }}>Normalized Score (-100 to 100)</label>
        <input
          id="normalized-score"
          max="100"
          min="-100"
          type="number"
          step="any"
          required
          value={value}
          onChange={(e) => setValue(e.target.value)}
          style={{ padding: "0.5rem", borderRadius: "4px", width: "100%", background: "var(--bg-secondary)", color: "var(--text-primary)", border: "1px solid var(--border-color)" }}
        />
      </div>
      <div>
        <label htmlFor="input-type" style={{ display: "block", marginBottom: "0.5rem" }}>Input Type</label>
        <select
          id="input-type"
          value={inputType}
          onChange={(e) => setInputType(e.target.value as MarketRegimeInputCreate["input_type"])}
          style={{ padding: "0.5rem", borderRadius: "4px", width: "100%", background: "var(--bg-secondary)", color: "var(--text-primary)", border: "1px solid var(--border-color)" }}
        >
          <option value="manual">Manual user assumption</option>
          <option value="provider">Provider-backed observation</option>
        </select>
      </div>
      <div>
        <label htmlFor="source-name" style={{ display: "block", marginBottom: "0.5rem" }}>Source Name</label>
        <input
          id="source-name"
          minLength={2}
          required
          value={sourceName}
          onChange={(e) => setSourceName(e.target.value)}
          style={{ padding: "0.5rem", borderRadius: "4px", width: "100%", background: "var(--bg-secondary)", color: "var(--text-primary)", border: "1px solid var(--border-color)" }}
        />
      </div>
      <div>
        <label htmlFor="source-url" style={{ display: "block", marginBottom: "0.5rem" }}>Source URL {inputType === "provider" ? "(required)" : "(optional)"}</label>
        <input
          id="source-url"
          required={inputType === "provider"}
          type="url"
          value={sourceUrl}
          onChange={(e) => setSourceUrl(e.target.value)}
          style={{ padding: "0.5rem", borderRadius: "4px", width: "100%", background: "var(--bg-secondary)", color: "var(--text-primary)", border: "1px solid var(--border-color)" }}
        />
      </div>
      <div>
        <label htmlFor="methodology" style={{ display: "block", marginBottom: "0.5rem" }}>Normalization Methodology</label>
        <textarea
          id="methodology"
          minLength={10}
          required
          value={methodology}
          onChange={(e) => setMethodology(e.target.value)}
          style={{ minHeight: "90px", padding: "0.5rem", borderRadius: "4px", width: "100%", background: "var(--bg-secondary)", color: "var(--text-primary)", border: "1px solid var(--border-color)" }}
        />
      </div>
      <div>
        <label htmlFor="as-of-date" style={{ display: "block", marginBottom: "0.5rem" }}>As Of Date</label>
        <input
          id="as-of-date"
          type="date"
          required
          value={asOfDate}
          onChange={(e) => setAsOfDate(e.target.value)}
          style={{ padding: "0.5rem", borderRadius: "4px", width: "100%", background: "var(--bg-secondary)", color: "var(--text-primary)", border: "1px solid var(--border-color)" }}
        />
      </div>
      <button
        type="submit"
        disabled={isSubmitting}
        style={{ padding: "0.5rem 1rem", borderRadius: "4px", background: "var(--primary-color)", color: "white", border: "none", cursor: "pointer" }}
      >
        {isSubmitting ? "Submitting..." : "Submit Metric"}
      </button>
    </form>
  );
}
