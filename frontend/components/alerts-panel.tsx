import React from "react";
import { Panel } from "@/components/page";
import type { AlertRecord, Company } from "@/lib/api";
import Link from "next/link";

interface AlertsPanelProps {
  alerts: AlertRecord[];
  companiesById: Map<number, Company>;
}

export function AlertsPanel({ alerts, companiesById }: AlertsPanelProps) {
  // Only show active alerts
  const activeAlerts = alerts.filter(a => a.review_status === "unreviewed" || a.review_status === "needs_follow_up");

  if (activeAlerts.length === 0) {
    return (
      <Panel title="Active Alerts">
        <div style={{ color: "var(--text-muted)" }}>No active alerts. You're all caught up!</div>
      </Panel>
    );
  }

  return (
    <Panel title={`Active Alerts (${activeAlerts.length})`}>
      <div style={{ display: "flex", flexDirection: "column", gap: "0.75rem" }}>
        {activeAlerts.slice(0, 5).map((alert) => {
          const ticker = alert.company_id ? companiesById.get(alert.company_id)?.ticker : null;
          
          let severityColor = "var(--text-muted)";
          if (alert.severity === "high" || alert.severity === "critical") severityColor = "var(--error)";
          if (alert.severity === "medium") severityColor = "var(--warn)";

          return (
            <div key={alert.id} style={{
              padding: "0.75rem",
              borderRadius: "0.25rem",
              border: `1px solid ${severityColor}40`,
              backgroundColor: `${severityColor}0a`,
              display: "flex",
              flexDirection: "column",
              gap: "0.25rem"
            }}>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start" }}>
                <Link href={`/alerts/${alert.id}`} style={{ fontWeight: 600, color: "var(--text)", textDecoration: "none" }}>
                  {ticker && <span style={{ color: "var(--accent)", marginRight: "0.5rem" }}>{ticker}</span>}
                  {alert.title}
                </Link>
                <span className="badge" style={{ backgroundColor: severityColor, color: "#fff", border: "none" }}>
                  {alert.severity}
                </span>
              </div>
              {alert.summary && (
                <p style={{ fontSize: "0.85rem", color: "var(--text-muted)", margin: 0 }}>{alert.summary}</p>
              )}
            </div>
          );
        })}

        {activeAlerts.length > 5 && (
          <div style={{ marginTop: "0.5rem", textAlign: "center" }}>
            <Link href="/alerts" className="btn btn-outline" style={{ fontSize: "0.85rem", width: "100%" }}>
              View All Alerts
            </Link>
          </div>
        )}
      </div>
    </Panel>
  );
}
