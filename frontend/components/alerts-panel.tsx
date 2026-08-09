"use client";

import React, { useState } from "react";
import { Panel } from "@/components/page";
import type { AlertRecord, Company } from "@/lib/api";
import Link from "next/link";
import { ScoreBreakdown } from "./score-breakdown";
import { EvidenceTrailDrawer } from "./intelligence/EvidenceTrailDrawer";

interface AlertsPanelProps {
  alerts: AlertRecord[];
  companiesById: Map<number, Company>;
}

export function AlertsPanel({ alerts, companiesById }: AlertsPanelProps) {
  const [selectedAlertId, setSelectedAlertId] = useState<number | null>(null);

  // Only show active alerts
  const activeAlerts = alerts.filter(a => a.review_status === "unreviewed" || a.review_status === "needs_follow_up");

  if (activeAlerts.length === 0) {
    return (
      <Panel title="Active Alerts">
        <div style={{ color: "var(--text-muted)" }}>
          No active alerts. Run ingestion or add a company to generate source-backed alerts.
          <div className="button-row" style={{ marginTop: "10px" }}>
            <Link className="btn btn-outline" href="/data">Run ingestion</Link>
            <Link className="btn btn-outline" href="/companies">Add company</Link>
          </div>
        </div>
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
                <div style={{ display: "flex", gap: "0.5rem", alignItems: "center" }}>
                  <ScoreBreakdown score={alert.portfolio_priority_score} explanation={alert.score_explanation_json} />
                  <span className="badge" style={{ backgroundColor: severityColor, color: "#fff", border: "none" }}>
                    {alert.severity}
                  </span>
                </div>
              </div>
              {alert.summary && (
                <p style={{ fontSize: "0.85rem", color: "var(--text-muted)", margin: 0 }}>{alert.summary}</p>
              )}
              <div style={{ marginTop: "0.25rem" }}>
                <button
                  onClick={() => setSelectedAlertId(alert.id)}
                  className="btn btn-outline"
                  style={{ fontSize: "0.75rem", padding: "0.15rem 0.4rem" }}
                  type="button"
                >
                  View Evidence Trail
                </button>
              </div>
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

      {selectedAlertId ? (
        <EvidenceTrailDrawer
          alertId={selectedAlertId}
          isOpen
          onClose={() => setSelectedAlertId(null)}
        />
      ) : null}
    </Panel>
  );
}
