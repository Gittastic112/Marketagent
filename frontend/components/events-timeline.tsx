import React from "react";
import { Panel } from "@/components/page";
import type { EventRecord } from "@/lib/api";
import Link from "next/link";

interface EventsTimelineProps {
  events: EventRecord[];
}

export function EventsTimeline({ events }: EventsTimelineProps) {
  if (!events || events.length === 0) {
    return (
      <Panel title="Recent Events">
        <div style={{ color: "var(--text-muted)" }}>No recent events to display.</div>
      </Panel>
    );
  }

  // Take top 5
  const displayEvents = events.slice(0, 5);

  return (
    <Panel title="Recent Events">
      <div style={{ display: "flex", flexDirection: "column", gap: "1rem" }}>
        {displayEvents.map((event) => (
          <div key={event.id} style={{ 
            display: "flex", 
            flexDirection: "column", 
            gap: "0.25rem",
            paddingBottom: "1rem",
            borderBottom: "1px solid var(--border)",
            lastChild: { borderBottom: "none", paddingBottom: 0 }
          }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start" }}>
              <div style={{ fontWeight: 600, color: "var(--text)" }}>
                {event.company_id ? (
                  <Link href={`/companies/${event.company_id}`} style={{ color: "var(--accent)", marginRight: "0.5rem" }}>
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
              <span className="badge badge-outline" style={{ fontSize: "0.7rem", padding: "0.1rem 0.3rem" }}>
                {event.event_type}
              </span>
              <span>Speed: {event.information_speed}</span>
            </div>

            {event.description && (
              <p style={{ fontSize: "0.9rem", color: "var(--text-muted)", marginTop: "0.25rem", display: "-webkit-box", WebkitLineClamp: 2, WebkitBoxOrient: "vertical", overflow: "hidden" }}>
                {event.description}
              </p>
            )}
          </div>
        ))}
        
        <div style={{ marginTop: "0.5rem", textAlign: "center" }}>
          <Link href="/research" className="btn btn-outline" style={{ fontSize: "0.85rem", width: "100%" }}>
            View All Events
          </Link>
        </div>
      </div>
    </Panel>
  );
}
