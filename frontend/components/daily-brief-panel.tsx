import { ArrowUpRight } from "lucide-react";
import { Panel } from "@/components/page";
import type { DailyBriefPayload } from "@/lib/api";
import Link from "next/link";
import { BriefPublicCoverage } from "@/components/brief-public-coverage";

export function DailyBriefPanel({ dailyBrief }: { dailyBrief: DailyBriefPayload | null }) {
  return <Panel title="Daily Intelligence Brief" className="today-brief">
    {!dailyBrief ? <p className="muted">No brief available for today.</p> : <>
      <div className="today-brief-status">
        <span className="badge">Stored preview</span>
        {dailyBrief.contains_mock_data && <span className="badge">Mock Data</span>}
        {dailyBrief.contains_stale_data && <span className="badge">Stale evidence</span>}
      </div>
      <p className="today-brief-summary">{dailyBrief.summary}</p>
      {dailyBrief.high_materiality_events.length > 0 && <div className="today-brief-events">
        <h3>Selected headlines</h3>
        <p className="muted">Up to three headlines from the selected inputs.</p>
        {dailyBrief.high_materiality_events.slice(0, 3).map(event => <article key={event.event_id}>
          <Link href={`/events/${event.event_id}/evidence-resolution`}>{event.headline}<ArrowUpRight size={14} aria-hidden="true" /></Link>
          <p>{event.claim_type} · Evidence: {event.evidence_status === "source_linked" ? "Source linked" : "Manual record"}{event.source_name ? ` · ${event.source_name}` : ""} · {event.status}{event.source_published_at ? ` · Published ${event.source_published_at.slice(0, 10)}` : " · Publication date unknown"}</p>
        </article>)}
      </div>}
      <BriefPublicCoverage coverage={dailyBrief.public_coverage} compact />
      <Link href="/daily-brief" prefetch={false} className="today-text-link">Open Daily Brief <ArrowUpRight size={14} aria-hidden="true" /></Link>
    </>}
  </Panel>;
}
