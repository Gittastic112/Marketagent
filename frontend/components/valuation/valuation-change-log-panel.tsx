"use client";

import { useEffect, useState } from "react";
import { ValuationAssumptionChangeLog, getValuationChangeLogs, resolveStaleValuation } from "@/lib/api";

export function ValuationChangeLogPanel({ modelId, assumptionSetId }: { modelId: number; assumptionSetId: number }) {
  const [logs, setLogs] = useState<ValuationAssumptionChangeLog[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function load() {
      try {
        const data = await getValuationChangeLogs(modelId, assumptionSetId);
        setLogs(data);
      } catch (err: any) {
        setError(err.message || "Failed to load change logs");
      } finally {
        setIsLoading(false);
      }
    }
    load();
  }, [modelId, assumptionSetId]);

  const handleResolve = async () => {
    try {
      setError(null);
      await resolveStaleValuation(modelId, assumptionSetId);
      window.location.reload(); // Quick refresh to clear banners
    } catch (err: any) {
      setError(`Failed to resolve staleness: ${err.message}`);
    }
  };

  if (isLoading) return <div>Loading change logs...</div>;
  if (error && logs.length === 0) return <div role="alert" style={{ color: "red" }}>{error}</div>;

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "1.5rem" }}>
      <div>
        <h3 style={{ margin: "0 0 0.5rem 0" }}>Assumption History & Change Ledger</h3>
        <p style={{ margin: 0, color: "var(--text-secondary)", fontSize: "0.9rem" }}>
          Track the drift in your assumptions over time. This ledger captures both manual model updates and event-driven AI challenges.
        </p>
      </div>

      <button
        type="button"
        onClick={handleResolve}
        style={{
          alignSelf: "flex-start",
          padding: "0.5rem 1rem",
          background: "var(--panel-bg)",
          border: "1px solid var(--border-color)",
          cursor: "pointer",
          borderRadius: "4px"
        }}
      >
        Mark as Reviewed (Clear Stale Warning)
      </button>
      {error ? <p role="alert" style={{ color: "var(--danger)" }}>{error}</p> : null}

      {logs.length === 0 ? (
        <div style={{ padding: "2rem", textAlign: "center", border: "1px dashed var(--border-color)", borderRadius: "8px" }}>
          No assumption changes recorded for this version.
        </div>
      ) : (
        <div style={{ display: "flex", flexDirection: "column", gap: "1rem" }}>
          {logs.map(log => {
            const isManualDiff = !log.rationale;
            return (
              <div key={log.id} style={{
                border: "1px solid var(--border-color)",
                borderRadius: "6px",
                padding: "1rem",
                background: isManualDiff ? "var(--bg)" : "var(--panel-bg-alt, #fafafa)",
                borderLeft: isManualDiff ? "4px solid var(--border-color)" : "4px solid var(--accent)"
              }}>
                <div style={{ display: "flex", justifyContent: "space-between", marginBottom: "0.5rem" }}>
                  <strong>
                    {isManualDiff ? "Manual Update" : "AI Proposed Change"}: <code>{log.parameter_name}</code>
                  </strong>
                  <span style={{ fontSize: "0.8rem", color: "var(--text-muted)" }}>{new Date(log.created_at).toLocaleString()}</span>
                </div>
                <div style={{ display: "flex", gap: "2rem", marginBottom: "0.5rem" }}>
                  <div><span style={{ color: "var(--text-secondary)" }}>Old Value:</span> <span style={{ textDecoration: "line-through" }}>{log.old_value || "None"}</span></div>
                  <div><span style={{ color: "var(--text-secondary)" }}>New Value:</span> <strong style={{ color: isManualDiff ? "var(--text)" : "var(--accent)" }}>{log.new_value || "None"}</strong></div>
                </div>
                {!isManualDiff && (
                  <div style={{ fontSize: "0.95rem", lineHeight: 1.4, marginTop: "0.5rem", padding: "0.75rem", background: "var(--panel-bg)", borderRadius: "4px" }}>
                    <strong>Rationale:</strong> {log.rationale}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
