import Link from "next/link";


interface BriefingEventCardProps {
  event_id: number;
  headline: string;
  priority?: string;
  ticker?: string | null;
  form_type?: string | null;
  status?: "New" | "Unresolved" | "Stale" | "Reviewed";
  raw_document_id?: number | null;
  source_name?: string | null;
  source_published_at?: string | null;
  claim_type?: "Source Summary" | "User Assumption";
  evidence_status?: "source_linked" | "manual";
}

function dateLabel(value?: string | null) {
  if (!value) return null;
  return new Date(value).toLocaleDateString();
}

export function BriefingEventCard({
  event_id,
  headline,
  priority,
  ticker,
  form_type,
  status = "New",
  raw_document_id,
  source_name,
  source_published_at,
  claim_type = "User Assumption",
  evidence_status = "manual",
}: BriefingEventCardProps) {
  return (
    <article className="brief-item briefing-event-card">
      <div className="briefing-card-heading">
        <div>
          <div className="briefing-kicker-row">
            <span className="badge badge-outline">{claim_type}</span>
            <span className={`badge briefing-status briefing-status-${status.toLowerCase()}`}>{status}</span>
          </div>
          <h3>{ticker ? `${ticker} · ` : ""}{headline}</h3>
        </div>
      </div>

      <div className="briefing-meta-row">
        {priority && <span>Priority: {priority}</span>}
        {form_type && <span>Type: {form_type}</span>}
        <span>Evidence: {evidence_status === "source_linked" ? "Source linked" : "Manual record"}</span>
        {source_name && <span>Source: {source_name}</span>}
        {dateLabel(source_published_at) && <span>Published: {dateLabel(source_published_at)}</span>}
      </div>

      <div className="button-row briefing-actions">
        <Link href={`/events/${event_id}/evidence-resolution`} className="btn btn-secondary">
          Review event evidence
        </Link>
        {raw_document_id && (
          <Link href={`/documents/${raw_document_id}/sections`} className="btn btn-secondary">
            Open source document
          </Link>
        )}
      </div>
    </article>
  );
}
