"use client";

import { useState } from "react";
import type { DcfMappingResponse } from "@/lib/api";

export function DcfImpactPredictor({ eventId, eventText }: { eventId: number; eventText: string }) {
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<DcfMappingResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handlePredict = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch("/api/backend/ai/research/map-event-to-dcf", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          event_text: eventText,
          event_id: eventId,
        }),
      });

      if (!res.ok) {
        const body = await res.json().catch(() => null);
        const message = body?.errors?.[0]?.message;
        throw new Error(message || `Failed to predict DCF impact (Status ${res.status})`);
      }

      const response: DcfMappingResponse = await res.json();
      if (!response.data) {
        throw new Error(response.errors[0]?.message || "The AI response did not contain a result.");
      }
      setResult(response);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "An unknown error occurred.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="section-block mt-4">
      <h4>AI DCF Impact Prediction</h4>
      <p className="text-sm text-gray-500 mb-2">
        Use the AI Research Assistant to map this event to standard DCF valuation variables.
      </p>

      {error && <div className="notice notice-error mb-2">{error}</div>}

      {result?.data?.impacted_variables ? (
        <div style={{ marginTop: "1rem" }}>
          {result.data.impacted_variables.length === 0 ? (
            <p className="text-sm text-gray-500">No DCF variables were identified as impacted by this event.</p>
          ) : (
            <ul style={{ paddingLeft: "1.2rem", fontSize: "0.85rem" }}>
              {result.data.impacted_variables.map((impact, idx) => (
                <li key={idx} style={{ marginBottom: "0.5rem" }}>
                  <strong>{impact.variable_name}</strong>
                  <span className={`badge ${impact.impact_direction === 'increase' ? 'badge-success' : impact.impact_direction === 'decrease' ? 'badge-error' : 'badge-warning'}`} style={{ margin: "0 0.5rem" }}>
                    {impact.impact_direction}
                  </span>
                  <span className="text-gray-500">({impact.confidence} confidence)</span>
                  <p style={{ margin: "0.2rem 0 0 0", color: "var(--text-secondary)" }}>{impact.reasoning}</p>
                </li>
              ))}
            </ul>
          )}

          <div style={{ marginTop: "1rem", fontSize: "0.75rem", color: "var(--text-secondary)" }}>
            Model: {result.data.model_name} | {result.meta.is_mock ? "Mock Data" : "Live Generation"}
          </div>
        </div>
      ) : (
        <button
          onClick={handlePredict}
          disabled={loading}
          className="secondary-button text-sm"
        >
          {loading ? "Analyzing..." : "Analyze DCF Impact"}
        </button>
      )}
    </div>
  );
}
