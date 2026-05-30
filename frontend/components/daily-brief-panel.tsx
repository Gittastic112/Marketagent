import React from "react";
import { Panel } from "@/components/page";
import type { DailyBrief } from "@/lib/api";
import Link from "next/link";

interface DailyBriefPanelProps {
  dailyBrief: DailyBrief | null;
}

export function DailyBriefPanel({ dailyBrief }: DailyBriefPanelProps) {
  if (!dailyBrief) {
    return (
      <Panel title="Daily Intelligence Brief">
        <div style={{ color: "var(--text-muted)" }}>No brief available for today.</div>
      </Panel>
    );
  }

  return (
    <Panel title={dailyBrief.title || "Daily Intelligence Brief"}>
      <div style={{ display: "flex", flexDirection: "column", gap: "1rem" }}>
        <p style={{ color: "var(--text-muted)", fontSize: "0.95rem" }}>
          {dailyBrief.summary}
        </p>

        {dailyBrief.follow_up_questions && dailyBrief.follow_up_questions.length > 0 && (
          <div>
            <h4 style={{ fontSize: "0.85rem", textTransform: "uppercase", letterSpacing: "0.05em", color: "var(--text-muted)", marginBottom: "0.5rem" }}>
              Suggested Investigation
            </h4>
            <ul style={{ paddingLeft: "1.2rem", fontSize: "0.9rem", color: "var(--accent)" }}>
              {dailyBrief.follow_up_questions.map((question, idx) => (
                <li key={idx} style={{ marginBottom: "0.25rem" }}>{question}</li>
              ))}
            </ul>
          </div>
        )}

        <div style={{ marginTop: "0.5rem" }}>
          <Link href="/research" className="btn btn-outline" style={{ fontSize: "0.85rem" }}>
            Investigate Events →
          </Link>
        </div>
      </div>
    </Panel>
  );
}
