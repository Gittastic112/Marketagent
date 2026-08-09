"use client";

import { useState } from "react";
import { submitMarketRegimeInput, MarketRegimeInputCreate } from "@/lib/api";
import { useRouter } from "next/navigation";

export function RegimeInputForm() {
  const [metricName, setMetricName] = useState("options");
  const [value, setValue] = useState("");
  const [asOfDate, setAsOfDate] = useState(new Date().toISOString().split("T")[0]);
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
        source_url: null,
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
        <label style={{ display: "block", marginBottom: "0.5rem" }}>Metric Name</label>
        <select
          value={metricName}
          onChange={(e) => setMetricName(e.target.value)}
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
        <label style={{ display: "block", marginBottom: "0.5rem" }}>Value</label>
        <input
          type="number"
          step="any"
          required
          value={value}
          onChange={(e) => setValue(e.target.value)}
          style={{ padding: "0.5rem", borderRadius: "4px", width: "100%", background: "var(--bg-secondary)", color: "var(--text-primary)", border: "1px solid var(--border-color)" }}
        />
      </div>
      <div>
        <label style={{ display: "block", marginBottom: "0.5rem" }}>As Of Date</label>
        <input
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
