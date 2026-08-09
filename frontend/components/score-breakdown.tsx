"use client";

import React, { useState } from "react";
import { ScoreExplanation } from "@/lib/api";

interface ScoreBreakdownProps {
  score: number;
  explanation: ScoreExplanation | null;
}

export function ScoreBreakdown({ score, explanation }: ScoreBreakdownProps) {
  const [isOpen, setIsOpen] = useState(false);

  // If there's no explanation JSON, just show the score.
  if (!explanation || !explanation.inputs) {
    return (
      <span className="badge" style={{ backgroundColor: "var(--surface-muted)", color: "var(--text)" }}>
        Score: {score}
      </span>
    );
  }

  // Determine color based on score magnitude
  let colorVar = "var(--text)";
  let bgVar = "var(--surface-muted)";
  if (score >= 80) {
    colorVar = "var(--error)";
    bgVar = "var(--error-bg)";
  } else if (score >= 50) {
    colorVar = "var(--warning)";
    bgVar = "var(--warning-bg)";
  } else if (score > 0) {
    colorVar = "var(--success)";
    bgVar = "var(--success-bg)";
  }

  return (
    <div style={{ position: "relative", display: "inline-block" }}>
      <button
        className="badge"
        style={{
          backgroundColor: bgVar,
          color: colorVar,
          cursor: "pointer",
          border: "1px solid currentColor",
          padding: "0.2rem 0.5rem",
          display: "inline-flex",
          alignItems: "center",
          gap: "0.25rem"
        }}
        onClick={(e) => {
          e.preventDefault();
          setIsOpen(!isOpen);
        }}
        title="View Score Details"
      >
        <span>{score.toFixed(1)}</span>
        <span style={{ opacity: 0.7, fontSize: "0.8em" }}>ⓘ</span>
      </button>

      {isOpen && (
        <div style={{
          position: "absolute",
          top: "100%",
          left: 0,
          marginTop: "0.5rem",
          zIndex: 50,
          width: "350px",
          backgroundColor: "var(--surface)",
          border: "1px solid var(--border)",
          borderRadius: "0.5rem",
          padding: "1rem",
          boxShadow: "0 10px 25px rgba(0,0,0,0.1)",
          fontSize: "0.85rem",
          color: "var(--text)"
        }}>
          <div style={{ display: "flex", justifyContent: "space-between", marginBottom: "0.5rem" }}>
            <strong style={{ textTransform: "capitalize" }}>{explanation.score_name.replace(/_/g, " ")}</strong>
            <span style={{ fontWeight: 600 }}>{explanation.value.toFixed(1)}</span>
          </div>

          <div style={{ display: "flex", gap: "0.5rem", marginBottom: "1rem", fontSize: "0.75rem" }}>
            <span className="badge" style={{ backgroundColor: "var(--surface-muted)" }}>{explanation.label}</span>
            <span className="badge" style={{ backgroundColor: "var(--surface-muted)" }}>{explanation.direction}</span>
          </div>

          <p style={{ margin: "0 0 1rem 0", color: "var(--muted)", lineHeight: 1.4 }}>
            {explanation.summary}
          </p>

          <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "0.8rem", textAlign: "left" }}>
            <thead>
              <tr style={{ borderBottom: "1px solid var(--border)" }}>
                <th style={{ padding: "0.25rem 0", fontWeight: 500, color: "var(--muted)" }}>Input</th>
                <th style={{ padding: "0.25rem 0", fontWeight: 500, color: "var(--muted)" }}>Val</th>
                <th style={{ padding: "0.25rem 0", fontWeight: 500, color: "var(--muted)" }}>Wgt</th>
                <th style={{ padding: "0.25rem 0", fontWeight: 500, color: "var(--muted)" }}>Contrib</th>
              </tr>
            </thead>
            <tbody>
              {explanation.inputs.map((inp, idx) => (
                <tr key={idx} style={{ borderBottom: "1px solid var(--border-light)" }} title={inp.explanation}>
                  <td style={{ padding: "0.4rem 0" }}>{inp.name.replace(/_score/g, "").replace(/_/g, " ")}</td>
                  <td style={{ padding: "0.4rem 0" }}>{inp.value.toFixed(1)}</td>
                  <td style={{ padding: "0.4rem 0" }}>{(inp.weight * 100).toFixed(0)}%</td>
                  <td style={{ padding: "0.4rem 0", fontWeight: 500 }}>{inp.contribution.toFixed(1)}</td>
                </tr>
              ))}
            </tbody>
          </table>

          <div style={{ marginTop: "1rem", textAlign: "right" }}>
            <button
              className="btn btn-outline"
              style={{ fontSize: "0.75rem", padding: "0.2rem 0.5rem" }}
              onClick={() => setIsOpen(false)}
            >
              Close
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
