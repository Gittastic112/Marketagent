import React from "react";
import { Panel } from "@/components/page";
import type { DailyBriefPayload } from "@/lib/api";
import Link from "next/link";

interface DailyBriefPanelProps {
  dailyBrief: DailyBriefPayload | null;
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
    <Panel title="Daily Intelligence Brief">
      <div style={{ display: "flex", flexDirection: "column", gap: "1rem" }}>
        <p style={{ color: "var(--text-muted)", fontSize: "0.95rem" }}>
          {dailyBrief.high_materiality_events.length} high-materiality events and {dailyBrief.thesis_contradictions.length} thesis contradictions require review.
        </p>

        {dailyBrief.high_materiality_events.length > 0 && (
          <div>
            <h4 style={{ fontSize: "0.85rem", textTransform: "uppercase", letterSpacing: "0.05em", color: "var(--text-muted)", marginBottom: "0.5rem" }}>
              High-Materiality Events
            </h4>
            <div style={{ display: "flex", flexDirection: "column", gap: "0.5rem" }}>
              {dailyBrief.high_materiality_events.slice(0, 3).map((event) => (
                <Link
                  href={`/events/${event.event_id}`}
                  key={event.event_id}
                  className="btn btn-outline"
                  style={{
                    textAlign: "left",
                    padding: "0.75rem 1rem",
                    fontSize: "0.9rem",
                    justifyContent: "flex-start",
                    background: "var(--surface-hover)",
                    borderColor: "var(--line)",
                    color: "var(--text)",
                    textDecoration: "none",
                    display: "flex",
                    alignItems: "center"
                  }}
                >
                  <span style={{ color: "var(--accent)", marginRight: "0.5rem" }}>→</span>
                  {event.headline}
                </Link>
              ))}
            </div>
          </div>
        )}

        <div style={{ marginTop: "0.5rem" }}>
          <Link href="/daily-brief" className="btn btn-outline" style={{ fontSize: "0.85rem" }}>
            Open Daily Brief →
          </Link>
        </div>
      </div>
    </Panel>
  );
}
