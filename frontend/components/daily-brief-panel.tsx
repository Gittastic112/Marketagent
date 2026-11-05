import React from "react";
import { Panel } from "@/components/page";
import type { DailyBriefPayload } from "@/lib/api";
import Link from "next/link";
import { BriefPublicCoverage } from "@/components/brief-public-coverage";

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
          {dailyBrief.summary}
        </p>
        <BriefPublicCoverage coverage={dailyBrief.public_coverage} compact />

        {dailyBrief.high_materiality_events.length > 0 && (
          <div>
            <h4 style={{ fontSize: "0.85rem", textTransform: "uppercase", letterSpacing: "0.05em", color: "var(--text-muted)", marginBottom: "0.5rem" }}>
              High-Materiality Events
            </h4>
            <p className="muted" style={{ fontSize: "var(--font-size-sm)" }}>Up to three headlines from the selected inputs.</p>
            <div style={{ display: "flex", flexDirection: "column", gap: "0.5rem" }}>
              {dailyBrief.high_materiality_events.slice(0, 3).map((event) => (
                <div key={event.event_id}>
                <Link
                  href={`/events/${event.event_id}/evidence-resolution`}
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
                <p className="muted" style={{ fontSize: "var(--font-size-sm)", margin: "0.4rem 0 0" }}>{event.claim_type} · Evidence: {event.evidence_status === "source_linked" ? "Source linked" : "Manual record"}{event.source_name ? ` · ${event.source_name}` : ""} · {event.status}{event.source_published_at ? ` · Published ${event.source_published_at.slice(0, 10)}` : " · Publication date unknown"}</p>
                </div>
              ))}
            </div>
          </div>
        )}

        <div style={{ marginTop: "0.5rem" }}>
          <Link href="/daily-brief" prefetch={false} className="btn btn-outline" style={{ fontSize: "0.85rem" }}>
            Open Daily Brief →
          </Link>
        </div>
      </div>
    </Panel>
  );
}
