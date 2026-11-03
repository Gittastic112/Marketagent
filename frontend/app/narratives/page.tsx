import { RetainedActionForm } from "@/components/retained-action-form";
import Link from "next/link";
import { EmptyState, ErrorState, PageHeader, Panel } from "@/components/page";
import { DataStateNotices, PrototypeBadge } from "@/components/ui/data-states";
import { serverFetchApiResponse } from "@/lib/server-api";
import { hasUsableData } from "@/lib/data-state-meta";
import type { NarrativeCluster, NarrativeClaim, NarrativeMention, EventRecord } from "@/lib/api";
import { createNarrativeCluster, createNarrativeClaim, deleteNarrativeClusterWithState, extractNarratives } from "@/app/actions";
import { DeleteRecordForm } from "@/components/delete-record-form";
import { TextField, TextAreaField } from "@/components/form-fields";
import { AI_DISCLOSURES, AI_PRIVACY_DISCLOSURE_VERSION } from "@/lib/ai-privacy";

export const dynamic = "force-dynamic";

function formatDate(iso: string) {
  return new Date(iso).toLocaleDateString(undefined, { month: "short", day: "numeric", year: "numeric" });
}

export default async function NarrativesPage() {
  try {
    const [clustersRes, eventsRes, claimsRes, mentionsRes] = await Promise.all([
      serverFetchApiResponse<NarrativeCluster[]>("/narrative-clusters"),
      serverFetchApiResponse<EventRecord[]>("/events"),
      serverFetchApiResponse<NarrativeClaim[]>("/narrative-claims"),
      serverFetchApiResponse<NarrativeMention[]>("/narrative-mentions"),
    ]);
    const clusters = clustersRes.data || [];
    const events = eventsRes.data || [];
    const narrativeMetas = [clustersRes.meta, eventsRes.meta, claimsRes.meta, mentionsRes.meta];
    const claimsByCluster = Map.groupBy(claimsRes.data || [], (claim) => claim.cluster_id);
    const mentionsByCluster = Map.groupBy(mentionsRes.data || [], (mention) => mention.cluster_id);
    const clusterDetails = clusters.map((cluster) => ({
      cluster,
      claims: claimsByCluster.get(cluster.id) || [],
      mentions: mentionsByCluster.get(cluster.id) || [],
    }));

    const eventsById = new Map(events.map((e) => [e.id, e]));

    return (
      <>
        <PageHeader eyebrow="Market Stories" title="Narrative Intelligence" badge={<PrototypeBadge />} status={hasUsableData(clustersRes) ? `${clusters.length} active narratives` : "Narratives unavailable"} />
        <DataStateNotices
          metas={narrativeMetas}
          mockMessage="One or more narrative panels are using mock data. Treat affected narrative claims as placeholders."
        />

        {/* Action Panel */}
        <Panel title="Automated Extraction">
          <div className="narrative-extraction-layout">
            <div>
              <h3 style={{ margin: "0 0 0.5rem 0" }}>Automated Extraction</h3>
              <p style={{ margin: 0, color: "var(--text-secondary)", fontSize: "0.9rem" }}>
                Extract narratives from recent events using AI.
              </p>
            </div>
            <RetainedActionForm label="Extract narratives" action={extractNarratives}>
              <label style={{ display: "flex", gap: "0.5rem", maxWidth: "28rem", marginBottom: "0.75rem", fontSize: "0.85rem" }}>
                <input
                  type="checkbox"
                  name="privacy_disclosure_version"
                  value={AI_PRIVACY_DISCLOSURE_VERSION}
                  required
                />
                <span>{AI_DISCLOSURES.narrativeExtraction}</span>
              </label>
              <button type="submit" className="button">Run Narrative Extraction</button>
            </RetainedActionForm>
          </div>
        </Panel>

        {/* Create New Narrative Cluster */}
        <Panel title="Track a New Narrative">
          <RetainedActionForm label="Create narrative cluster" resetOnSuccess action={createNarrativeCluster} className="form-grid">
            <TextField id="narrative-name" label="Narrative Name" name="name" placeholder="e.g. AI Capex Supercycle" required />
            <TextAreaField className="field field-wide" id="narrative-desc" label="Description" name="description" placeholder="Describe the market narrative or thesis being tracked" rows={2} />
            <div className="button-row">
              <button type="submit">Create Narrative</button>
            </div>
          </RetainedActionForm>
        </Panel>

        {!hasUsableData(clustersRes) ? <ErrorState message="Narratives could not be loaded. Reload to retry." /> : clusters.length === 0 ? (
          <Panel title="Narratives">
            <EmptyState label="No narratives being tracked yet. Create one above to start." />
          </Panel>
        ) : (
          <div style={{ display: "flex", flexDirection: "column", gap: "1.5rem" }}>
            {clusterDetails.map(({ cluster, claims, mentions }) => (
              <div key={cluster.id} id={`narrative-${cluster.id}`} className="anchored-record">
              <Panel title={cluster.name}>
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: "1rem" }}>
                  <div>
                    {cluster.description && (
                      <p style={{ color: "var(--text-secondary)", fontSize: "0.9rem", marginBottom: "0.5rem" }}>{cluster.description}</p>
                    )}
                    <div style={{ display: "flex", gap: "1rem", fontSize: "0.8rem", color: "var(--text-secondary)" }}>
                      <span>Created {formatDate(cluster.created_at)}</span>
                      <span>{hasUsableData(claimsRes) ? `${claims.length} claims` : "Claims unavailable"}</span>
                      <span>{hasUsableData(mentionsRes) ? `${mentions.length} mentions` : "Mentions unavailable"}</span>
                    </div>
                  </div>
                  <DeleteRecordForm action={deleteNarrativeClusterWithState} recordId={cluster.id} />
                </div>

                {/* Claims Section */}
                <div style={{ marginBottom: "1.5rem" }}>
                  <h4 style={{ fontSize: "0.85rem", fontWeight: 600, textTransform: "uppercase", letterSpacing: "0.05em", color: "var(--text-secondary)", marginBottom: "0.75rem" }}>
                    Claims & Evidence
                  </h4>
                  {!hasUsableData(claimsRes) ? <ErrorState message="Claims could not be loaded. Reload to retry." /> : claims.length === 0 ? (
                    <p style={{ fontSize: "0.85rem", color: "var(--text-secondary)", fontStyle: "italic" }}>No claims recorded yet.</p>
                  ) : (
                    <div className="brief-list">
                      {claims.map((claim) => (
                        <div key={claim.id} className="brief-item" style={{ padding: "0.5rem 0", borderBottom: "1px solid var(--border-color)" }}>
                          <p style={{ margin: 0 }}>{claim.claim_text}</p>
                          <span style={{ fontSize: "0.75rem", color: "var(--text-secondary)" }}>Added {formatDate(claim.created_at)}</span>
                        </div>
                      ))}
                    </div>
                  )}

                  {/* Add Claim Form */}
                  <RetainedActionForm label="Review and save record" action={async (data) => {
                    "use server";
                    const { createNarrativeClaim } = await import("@/app/actions");
                    data.set("cluster_id", cluster.id.toString());
                    await createNarrativeClaim(data);
                  }} className="narrative-claim-form">
                    <input type="hidden" name="cluster_id" value={cluster.id} />
                    <label className="sr-only" htmlFor={`narrative-claim-${cluster.id}`}>Claim text for {cluster.name}</label>
                    <input
                      id={`narrative-claim-${cluster.id}`}
                      type="text"
                      name="claim_text"
                      placeholder="Add a claim (e.g. 'NVDA guiding $12B data center revenue')"
                      required
                      className="input"
                      style={{ flex: 1, fontSize: "0.85rem" }}
                    />
                    <button type="submit" className="secondary-button" style={{ fontSize: "0.85rem", whiteSpace: "nowrap" }}>+ Claim</button>
                  </RetainedActionForm>
                </div>

                {/* Mentions Section */}
                <div>
                  <h4 style={{ fontSize: "0.85rem", fontWeight: 600, textTransform: "uppercase", letterSpacing: "0.05em", color: "var(--text-secondary)", marginBottom: "0.75rem" }}>
                    Linked Mentions
                  </h4>
                  {!hasUsableData(mentionsRes) ? <ErrorState message="Mentions could not be loaded. Reload to retry." /> : mentions.length === 0 ? (
                    <p style={{ fontSize: "0.85rem", color: "var(--text-secondary)", fontStyle: "italic" }}>No mentions linked yet. Import events and link them to this narrative.</p>
                  ) : (
                    <div className="brief-list">
                      {mentions.map((mention) => {
                        const event = eventsById.get(mention.event_id);
                        return (
                          <div key={mention.id} className="brief-item" style={{ padding: "0.5rem 0", borderBottom: "1px solid var(--border-color)" }}>
                            {event ? (
                              <>
                                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "baseline" }}>
                                  <strong style={{ fontSize: "0.85rem" }}>{event.event_type} - {event.title}</strong>
                                  <span className="badge">{event.impact_score}/10</span>
                                </div>
                                {mention.context_text && <p style={{ fontSize: "0.85rem", margin: "0.25rem 0 0 0" }}>{mention.context_text}</p>}
                              </>
                            ) : (
                              <p style={{ fontSize: "0.85rem", color: "var(--text-secondary)" }}>Event #{mention.event_id} {hasUsableData(eventsRes) ? `(context: ${mention.context_text || "none"})` : "could not be loaded. Reload to retry."}</p>
                            )}
                            <span style={{ fontSize: "0.75rem", color: "var(--text-secondary)" }}>Added {formatDate(mention.created_at)}</span>
                          </div>
                        );
                      })}
                    </div>
                  )}
                </div>
              </Panel>
              </div>
            ))}
          </div>
        )}
      </>
    );
  } catch {
    return (
      <>
        <PageHeader eyebrow="Market Stories" title="Narrative Intelligence" />
        <ErrorState message="Could not load narrative data from the backend." />
      </>
    );
  }
}
