import Link from "next/link";
import { EmptyState, ErrorState, PageHeader, Panel } from "@/components/page";
import { fetchApi } from "@/lib/api";
import type { NarrativeCluster, NarrativeClaim, NarrativeMention, SocialPost } from "@/lib/api";
import { createNarrativeCluster, createNarrativeClaim, deleteNarrativeClusterWithState } from "@/app/actions";
import { DeleteRecordForm } from "@/components/delete-record-form";
import { TextField, TextAreaField } from "@/components/form-fields";

export const dynamic = "force-dynamic";

function formatDate(iso: string) {
  return new Date(iso).toLocaleDateString(undefined, { month: "short", day: "numeric", year: "numeric" });
}

export default async function NarrativesPage() {
  try {
    const [clusters, posts] = await Promise.all([
      fetchApi<NarrativeCluster[]>("/narrative-clusters"),
      fetchApi<SocialPost[]>("/social-posts").catch(() => []),
    ]);

    // Fetch claims and mentions for each cluster
    const clusterDetails = await Promise.all(
      clusters.map(async (cluster) => {
        const [claims, mentions] = await Promise.all([
          fetchApi<NarrativeClaim[]>(`/narrative-claims?cluster_id=${cluster.id}`).catch(() => []),
          fetchApi<NarrativeMention[]>(`/narrative-mentions?cluster_id=${cluster.id}`).catch(() => []),
        ]);
        return { cluster, claims, mentions };
      })
    );

    const postsById = new Map(posts.map((p) => [p.id, p]));

    return (
      <>
        <PageHeader eyebrow="Market Stories" title="Narrative Intelligence" status={`${clusters.length} active narratives`} />

        {/* Create New Narrative Cluster */}
        <Panel title="Track a New Narrative">
          <form action={createNarrativeCluster} className="form-grid">
            <TextField id="narrative-name" label="Narrative Name" name="name" placeholder="e.g. AI Capex Supercycle" required />
            <TextAreaField className="field field-wide" id="narrative-desc" label="Description" name="description" placeholder="Describe the market narrative or thesis being tracked" rows={2} />
            <div className="button-row">
              <button type="submit">Create Narrative</button>
            </div>
          </form>
        </Panel>

        {clusters.length === 0 ? (
          <Panel title="Narratives">
            <EmptyState label="No narratives being tracked yet. Create one above to start." />
          </Panel>
        ) : (
          <div style={{ display: "flex", flexDirection: "column", gap: "1.5rem" }}>
            {clusterDetails.map(({ cluster, claims, mentions }) => (
              <Panel key={cluster.id} title={cluster.name}>
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: "1rem" }}>
                  <div>
                    {cluster.description && (
                      <p style={{ color: "var(--text-secondary)", fontSize: "0.9rem", marginBottom: "0.5rem" }}>{cluster.description}</p>
                    )}
                    <div style={{ display: "flex", gap: "1rem", fontSize: "0.8rem", color: "var(--text-secondary)" }}>
                      <span>Created {formatDate(cluster.created_at)}</span>
                      <span>{claims.length} claim{claims.length !== 1 ? "s" : ""}</span>
                      <span>{mentions.length} mention{mentions.length !== 1 ? "s" : ""}</span>
                    </div>
                  </div>
                  <DeleteRecordForm action={deleteNarrativeClusterWithState} id={cluster.id} />
                </div>

                {/* Claims Section */}
                <div style={{ marginBottom: "1.5rem" }}>
                  <h4 style={{ fontSize: "0.85rem", fontWeight: 600, textTransform: "uppercase", letterSpacing: "0.05em", color: "var(--text-secondary)", marginBottom: "0.75rem" }}>
                    Claims & Evidence
                  </h4>
                  {claims.length === 0 ? (
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
                  <form action={async (data) => {
                    "use server";
                    const { createNarrativeClaim } = await import("@/app/actions");
                    data.set("cluster_id", cluster.id.toString());
                    await createNarrativeClaim(data);
                  }} style={{ display: "flex", gap: "0.5rem", marginTop: "0.75rem" }}>
                    <input type="hidden" name="cluster_id" value={cluster.id} />
                    <input
                      type="text"
                      name="claim_text"
                      placeholder="Add a claim (e.g. 'NVDA guiding $12B data center revenue')"
                      required
                      className="input"
                      style={{ flex: 1, fontSize: "0.85rem" }}
                    />
                    <button type="submit" className="secondary-button" style={{ fontSize: "0.85rem", whiteSpace: "nowrap" }}>+ Claim</button>
                  </form>
                </div>

                {/* Mentions Section */}
                <div>
                  <h4 style={{ fontSize: "0.85rem", fontWeight: 600, textTransform: "uppercase", letterSpacing: "0.05em", color: "var(--text-secondary)", marginBottom: "0.75rem" }}>
                    Linked Mentions
                  </h4>
                  {mentions.length === 0 ? (
                    <p style={{ fontSize: "0.85rem", color: "var(--text-secondary)", fontStyle: "italic" }}>No mentions linked yet. Import social posts and link them to this narrative.</p>
                  ) : (
                    <div className="brief-list">
                      {mentions.map((mention) => {
                        const post = postsById.get(mention.post_id);
                        return (
                          <div key={mention.id} className="brief-item" style={{ padding: "0.5rem 0", borderBottom: "1px solid var(--border-color)" }}>
                            {post ? (
                              <>
                                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "baseline" }}>
                                  <strong style={{ fontSize: "0.85rem" }}>{post.platform} - {post.author || "Unknown"}</strong>
                                  <span className="badge">{post.platform}</span>
                                </div>
                                {mention.context_text && <p style={{ fontSize: "0.85rem", margin: "0.25rem 0 0 0" }}>{mention.context_text}</p>}
                              </>
                            ) : (
                              <p style={{ fontSize: "0.85rem", color: "var(--text-secondary)" }}>Post #{mention.post_id} (context: {mention.context_text || "none"})</p>
                            )}
                            <span style={{ fontSize: "0.75rem", color: "var(--text-secondary)" }}>Added {formatDate(mention.created_at)}</span>
                          </div>
                        );
                      })}
                    </div>
                  )}
                </div>
              </Panel>
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
