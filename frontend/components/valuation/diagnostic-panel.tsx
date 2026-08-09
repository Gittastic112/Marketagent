import React from "react";
import { AlertCircle, AlertTriangle, Info, ShieldAlert } from "lucide-react";

export interface DiagnosticWarning {
  severity: "info" | "watch" | "warning" | "critical" | "blocking";
  module: string;
  message: string;
  affectedAssumptions?: string[];
  suggestedFix?: string;
  formula?: string;
}

export function DiagnosticPanel({ warnings }: { warnings: DiagnosticWarning[] }) {
  if (!warnings || warnings.length === 0) {
    return (
      <div style={{ fontSize: "0.9rem", color: "var(--success)", display: "flex", alignItems: "center", gap: "0.5rem" }}>
        <span style={{ display: "inline-block", width: "8px", height: "8px", borderRadius: "50%", background: "var(--success)" }}></span>
        No critical model warnings.
      </div>
    );
  }

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "0.75rem" }}>
      {warnings.map((w, i) => {
        let borderColor = "var(--border-color)";
        let bgColor = "var(--panel-bg)";
        let icon = <Info size={16} />;

        switch (w.severity) {
          case "blocking":
          case "critical":
            borderColor = "var(--danger)";
            bgColor = "rgba(220,38,38,0.05)";
            icon = <ShieldAlert size={16} color="var(--danger)" />;
            break;
          case "warning":
            borderColor = "var(--warning)";
            bgColor = "rgba(245,158,11,0.05)";
            icon = <AlertTriangle size={16} color="var(--warning)" />;
            break;
          case "watch":
            borderColor = "var(--accent)";
            bgColor = "rgba(59,130,246,0.05)";
            icon = <AlertCircle size={16} color="var(--accent)" />;
            break;
          case "info":
          default:
            borderColor = "var(--text-muted)";
            bgColor = "var(--bg)";
            icon = <Info size={16} color="var(--text-muted)" />;
            break;
        }

        return (
          <div
            key={i}
            style={{
              fontSize: "0.85rem",
              padding: "1rem",
              background: bgColor,
              borderLeft: `4px solid ${borderColor}`,
              borderRadius: "0 6px 6px 0",
              color: "var(--text)",
              display: "flex",
              flexDirection: "column",
              gap: "0.5rem"
            }}
          >
            <div style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
              {icon}
              <strong style={{ textTransform: "uppercase", fontSize: "0.75rem", letterSpacing: "0.05em", color: borderColor }}>
                {w.module.replace(/_/g, " ")}
              </strong>
            </div>

            <span style={{ fontWeight: 500, lineHeight: 1.4 }}>{w.message}</span>

            {w.suggestedFix && (
              <div style={{ marginTop: "0.25rem", color: "var(--text-secondary)", fontStyle: "italic" }}>
                <strong>Fix:</strong> {w.suggestedFix}
              </div>
            )}

            {w.formula && (
              <div style={{
                marginTop: "0.5rem",
                padding: "0.5rem",
                background: "var(--bg)",
                border: "1px solid var(--border-color)",
                borderRadius: "4px",
                fontFamily: "monospace",
                fontSize: "0.8rem",
                color: "var(--text-secondary)"
              }}>
                {w.formula}
              </div>
            )}

            {w.affectedAssumptions && w.affectedAssumptions.length > 0 && (
              <div style={{ display: "flex", flexWrap: "wrap", gap: "0.25rem", marginTop: "0.5rem" }}>
                {w.affectedAssumptions.map((assump, idx) => (
                  <span
                    key={idx}
                    style={{
                      fontSize: "0.7rem",
                      background: "rgba(0,0,0,0.05)",
                      color: "var(--text-secondary)",
                      padding: "0.15rem 0.4rem",
                      borderRadius: "12px",
                      border: "1px solid rgba(0,0,0,0.1)"
                    }}
                  >
                    {assump.replace(/_/g, " ")}
                  </span>
                ))}
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
}
