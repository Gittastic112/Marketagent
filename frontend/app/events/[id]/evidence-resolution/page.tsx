import Link from "next/link";
import { Search } from "lucide-react";

import { EventEvidenceResolutionForm } from "@/components/event-evidence-resolution-form";
import { TextField } from "@/components/form-fields";
import { EmptyState, ErrorState, PageHeader, Panel, PartialDataNotice } from "@/components/page";
import { DataStateNotices } from "@/components/ui/data-states";
import type {
  EventEvidenceReference,
  EventEvidenceResolutionSearch,
  EventRecord,
} from "@/lib/api";
import { serverFetchApiResponse } from "@/lib/server-api";

export const dynamic = "force-dynamic";

type EvidenceResolutionPageProps = {
  params: Promise<{ id: string }>;
  searchParams: Promise<{ q?: string; saved?: string }>;
};

export default async function EvidenceResolutionPage({
  params,
  searchParams,
}: EvidenceResolutionPageProps) {
  const [{ id }, requested] = await Promise.all([params, searchParams]);
  const eventId = Number.parseInt(id, 10);
  if (!Number.isFinite(eventId)) {
    return <ErrorState message="The event identifier is invalid." />;
  }

  const [eventResponse, referencesResponse] = await Promise.all([
    serverFetchApiResponse<EventRecord>(`/events/${eventId}`),
    serverFetchApiResponse<EventEvidenceReference[]>(`/events/${eventId}/evidence-references`),
  ]);
  const event = eventResponse.data;
  if (!event) {
    return (
      <>
        <PageHeader eyebrow="Evidence review" title="Event unavailable" />
        <ErrorState
          message={eventResponse.errors[0]?.message ?? "The event was not found."}
          errors={eventResponse.errors}
        />
      </>
    );
  }

  const query = typeof requested.q === "string" ? requested.q : "";
  const queryIsValid = query.length >= 8 && query.length <= 300;
  const searchResponse = queryIsValid
    ? await serverFetchApiResponse<EventEvidenceResolutionSearch>(
        `/events/${eventId}/evidence-resolution/search?${new URLSearchParams({
          q: query,
          context_chars: "180",
          limit: "25",
        })}`,
      )
    : null;
  const result = searchResponse?.data ?? null;
  const references = referencesResponse.data ?? [];
  const suggestedQuery = event.description && event.description.length >= 8 && event.description.length <= 300
    ? event.description
    : "";

  return (
    <>
      <PageHeader
        eyebrow="Evidence review"
        title={event.title}
        status={`${references.length} reference${references.length === 1 ? "" : "s"}`}
      />
      <DataStateNotices
        metas={[eventResponse.meta, referencesResponse.meta, searchResponse?.meta]}
        partialMessage="Some event evidence metadata is unavailable."
      />

      {requested.saved === "1" ? (
        <div className="success-message" role="status" style={{ marginBottom: "1rem" }}>
          Exact source evidence linked to the event.
        </div>
      ) : null}

      <Panel title="Source Context">
        <div className="brief-list">
          <div className="brief-item">
            <strong>Event claim</strong>
            <p>{event.description || "No event description is stored."}</p>
          </div>
          <div className="brief-item">
            <strong>Linked source</strong>
            <p>
              {event.raw_document_id ? (
                <Link href={`/documents/${event.raw_document_id}/sections`}>
                  Document {event.raw_document_id}
                </Link>
              ) : "No source document is linked."}
            </p>
          </div>
        </div>
      </Panel>

      <Panel title="Find Exact Source Text">
        <form method="get" className="form-grid">
          <TextField
            id="q"
            label="Exact source phrase"
            maxLength={300}
            minLength={8}
            name="q"
            defaultValue={query || suggestedQuery}
            required
          />
          <div className="button-row">
            <button type="submit">
              <Search aria-hidden="true" size={16} />
              Search exact text
            </button>
          </div>
        </form>
        {query && !queryIsValid ? (
          <div className="inline-error" role="alert" style={{ marginTop: "1rem" }}>
            Exact search text must be between 8 and 300 characters.
          </div>
        ) : null}
      </Panel>

      {searchResponse && !result ? (
        <ErrorState
          message={searchResponse.errors[0]?.message ?? "The linked source could not be searched."}
          errors={searchResponse.errors}
        />
      ) : null}

      {result ? (
        <Panel title={`Exact Matches (${result.exact_match_count})`}>
          {result.is_truncated ? (
            <PartialDataNotice message={`Showing the first ${result.returned_match_count} exact occurrences.`} />
          ) : null}
          {result.matches.length === 0 ? (
            <EmptyState label="No exact case-sensitive occurrence was found in the linked source text." />
          ) : (
            <div className="brief-list">
              {result.matches.map((match) => (
                <div className="brief-item" key={`${match.start_char}-${match.end_char}`}>
                  <div className="meta-row" style={{ marginBottom: "0.6rem" }}>
                    <span>Occurrence {match.occurrence_index}</span>
                    <span>Characters {match.start_char}-{match.end_char}</span>
                  </div>
                  <div style={{ whiteSpace: "pre-wrap", overflowWrap: "anywhere", lineHeight: 1.7 }}>
                    <span style={{ color: "var(--text-secondary)" }}>{match.context_before}</span>
                    <mark>{match.quote}</mark>
                    <span style={{ color: "var(--text-secondary)" }}>{match.context_after}</span>
                  </div>
                  <EventEvidenceResolutionForm
                    eventId={result.event_id}
                    rawDocumentId={result.raw_document_id}
                    documentContentHash={result.document_content_hash}
                    query={result.query}
                    match={match}
                  />
                </div>
              ))}
            </div>
          )}
          <div className="notice" style={{ marginTop: "1rem" }}>
            Exact, case-sensitive source selection | Full source text is not returned by this workflow.
          </div>
        </Panel>
      ) : null}

      {references.length > 0 ? (
        <Panel title="Existing Evidence">
          <div className="brief-list">
            {references.map((reference) => (
              <div className="brief-item" key={reference.id}>
                <strong>{reference.origin.replaceAll("_", " ")}</strong>
                <p>{reference.quote || reference.source_section || `${reference.locator_type} locator`}</p>
                <div className="meta-row">
                  <span>{reference.confidence_label} locator confidence</span>
                  <span>Reference {reference.id}</span>
                </div>
              </div>
            ))}
          </div>
        </Panel>
      ) : null}

      <div className="button-row">
        <Link className="secondary-button" href="/data-health">Back to data health</Link>
        <Link className="secondary-button" href="/events">Open events</Link>
      </div>
    </>
  );
}
