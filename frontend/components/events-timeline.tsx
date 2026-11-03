"use client";

import React, { useState } from "react";
import { Panel } from "@/components/page";
import type { EventRecord } from "@/lib/api";
import Link from "next/link";
import { EvidenceTrailDrawer } from "./intelligence/EvidenceTrailDrawer";

interface EventsTimelineProps {
  events: EventRecord[];
}

export function EventsTimeline({ events }: EventsTimelineProps) {
  const [selectedEventId, setSelectedEventId] = useState<number | null>(null);

  if (!events || events.length === 0) {
    return (
      <Panel title="Important Changes / Narrative Shifts">
        <div style={{ color: "var(--text-muted)" }}>
          No events have been extracted. Add source documents or run ingestion to populate the timeline.
          <div className="button-row" style={{ marginTop: "10px" }}>
            <Link className="btn btn-outline" href="/data">Review data sources</Link>
            <Link className="btn btn-outline" href="/documents">Add documents</Link>
          </div>
        </div>
      </Panel>
    );
  }

  // Take top 5
  const displayEvents = events.slice(0, 5);

  return (
    <Panel title="Important Changes / Narrative Shifts">
      <div style={{ display: "flex", flexDirection: "column", gap: "1rem" }}>
        {displayEvents.map((event, index) => (
          <div key={event.id} style={{
            display: "flex",
            flexDirection: "column",
            gap: "0.25rem",
            paddingBottom: index === displayEvents.length - 1 ? 0 : "1rem",
            borderBottom: index === displayEvents.length - 1 ? "none" : "1px solid var(--border)",
          }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start" }}>
              <div style={{ fontWeight: 600, color: "var(--text)" }}>
                {event.company_id ? (
                  <Link href={`/companies/${event.company_id}`} style={{ color: "var(--accent)", marginRight: "0.5rem", textDecoration: "underline" }}>
                    {event.company_id} {/* Ideally we'd map company_id to ticker here */}
                  </Link>
                ) : null}
                {event.title}
              </div>
              <div style={{ display: "flex", gap: "0.25rem" }}>
                <span className="badge badge-outline" title="Priority Score">{event.priority_score ?? 0}</span>
              </div>
            </div>

            <div style={{ fontSize: "0.85rem", color: "var(--text-muted)", display: "flex", gap: "0.5rem", alignItems: "center" }}>
              <span className="badge badge-outline" style={{ fontSize: "var(--font-size-xs)", padding: "0.1rem 0.3rem" }}>
                {event.event_type}
              </span>
              <span>Speed: {event.information_speed}</span>
            </div>

            {event.description && (
              <p style={{ fontSize: "0.9rem", color: "var(--text-muted)", marginTop: "0.25rem", display: "-webkit-box", WebkitLineClamp: 2, WebkitBoxOrient: "vertical", overflow: "hidden" }}>
                {event.description}
              </p>
            )}

            <div style={{ marginTop: "0.5rem" }}>
              <button
                onClick={() => setSelectedEventId(event.id)}
                className="btn btn-outline"
                style={{ fontSize: "0.75rem", padding: "0.2rem 0.5rem" }}
                type="button"
              >
                View Evidence Trail
              </button>
            </div>
          </div>
        ))}

        <div style={{ marginTop: "0.5rem", textAlign: "center" }}>
          <Link href="/events" className="btn btn-outline" style={{ fontSize: "0.85rem", width: "100%" }}>
            View All Events
          </Link>
        </div>
      </div>

      {selectedEventId && (
        <EvidenceTrailDrawer
          eventId={selectedEventId}
          isOpen={!!selectedEventId}
          onClose={() => setSelectedEventId(null)}
        />
      )}
    </Panel>
  );
}
