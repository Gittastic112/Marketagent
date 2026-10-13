import { RetainedActionForm } from "@/components/retained-action-form";
import { hasUsableData } from "@/lib/data-state-meta";
import {
  createNarrativeCluster,
  createSocialPost,
  deleteNarrativeClusterWithState,
  deleteSocialPostWithState,
  updateNarrativeCluster,
  updateSocialPost
} from "@/app/actions";
import { DeleteRecordForm } from "@/components/delete-record-form";
import { TextAreaField, TextField } from "@/components/form-fields";
import { EmptyState, ErrorState, PageHeader, Panel } from "@/components/page";
import { DataStateNotices } from "@/components/ui/data-states";
import { serverFetchApiResponse } from "@/lib/server-api";
import type { NarrativeCluster, SocialPost } from "@/lib/api";

export default async function SocialPage() {
  try {
    const [postsRes, clustersRes] = await Promise.all([
      serverFetchApiResponse<SocialPost[]>("/social-posts"),
      serverFetchApiResponse<NarrativeCluster[]>("/narrative-clusters")
    ]);
    const posts = postsRes.data || [];
    const clusters = clustersRes.data || [];

    return (
      <>
        <PageHeader eyebrow="Social & Narratives" title="Social Intelligence" status={`${hasUsableData(postsRes) ? `${posts.length} posts` : "Posts unavailable"}, ${hasUsableData(clustersRes) ? `${clusters.length} clusters` : "Clusters unavailable"}`} />
        <DataStateNotices
          metas={[postsRes.meta, clustersRes.meta]}
          mockMessage="Social or narrative data is mocked. Do not treat it as live social intelligence."
        />

        <div style={{ display: "flex", flexDirection: "column", gap: "2rem" }}>
          <section id="social-posts">
            <Panel title="Import Social Post">
              <RetainedActionForm label="Create social post" resetOnSuccess action={createSocialPost} className="form-grid">
                <TextField id="post-platform" label="Platform" name="platform" placeholder="e.g. Substack, SeekingAlpha" required />
                <TextField id="post-url" label="Source URL" name="source_url" required type="url" />
                <TextField id="post-author" label="Author" name="author" />
                <TextField id="post-published-at" label="Published At" name="published_at" type="datetime-local" />
                <TextAreaField className="field field-full" id="post-text" label="Raw Text" name="raw_text" required rows={4} />
                <div className="button-row">
                  <button type="submit">Import Post</button>
                </div>
              </RetainedActionForm>
            </Panel>

            <Panel title="Social Posts">
              {!hasUsableData(postsRes) ? <ErrorState message="Social posts could not be loaded. Reload to retry." /> : posts.length === 0 ? (
                <EmptyState label="No social posts imported yet." />
              ) : (
                <div className="table-wrap">
                  <table>
                    <thead>
                      <tr>
                        <th>Platform</th>
                        <th>Author</th>
                        <th>Snippet</th>
                        <th>Action</th>
                      </tr>
                    </thead>
                    <tbody>
                      {posts.map((post) => (
                        <tr key={post.id}>
                          <td>{post.platform}</td>
                          <td>{post.author ?? "-"}</td>
                          <td style={{ maxWidth: "300px", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }} title={post.raw_text}>
                            <a href={post.source_url} rel="noreferrer" target="_blank">
                              {post.raw_text.substring(0, 50)}...
                            </a>
                          </td>
                          <td>
                            <div className="action-stack">
                              <details className="edit-panel">
                                <summary>Edit</summary>
                                <RetainedActionForm label="Update social post" action={updateSocialPost} className="inline-form">
                                  <input name="id" type="hidden" value={post.id} />
                                  <TextField defaultValue={post.platform} id={`edit-platform-${post.id}`} label="Platform" name="platform" required />
                                  <TextField defaultValue={post.source_url} id={`edit-url-${post.id}`} label="Source URL" name="source_url" required type="url" />
                                  <TextField defaultValue={post.author ?? ""} id={`edit-author-${post.id}`} label="Author" name="author" />
                                  <TextAreaField className="field field-full" defaultValue={post.raw_text} id={`edit-text-${post.id}`} label="Raw Text" name="raw_text" required rows={3} />
                                  <div className="button-row">
                                    <button className="secondary-button" type="submit">Save</button>
                                  </div>
                                </RetainedActionForm>
                              </details>
                              <DeleteRecordForm action={deleteSocialPostWithState} recordId={post.id} />
                            </div>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </Panel>
          </section>

          <section id="narratives">
            <Panel title="Create Narrative Cluster">
              <RetainedActionForm label="Create narrative cluster" resetOnSuccess action={createNarrativeCluster} className="form-grid">
                <TextField id="cluster-name" label="Cluster Name" name="name" required />
                <TextAreaField className="field field-full" id="cluster-desc" label="Description" name="description" rows={2} />
                <div className="button-row">
                  <button type="submit">Create Cluster</button>
                </div>
              </RetainedActionForm>
            </Panel>

            <Panel title="Narrative Clusters">
              {!hasUsableData(clustersRes) ? <ErrorState message="Narrative clusters could not be loaded. Reload to retry." /> : clusters.length === 0 ? (
                <EmptyState label="No narrative clusters created yet." />
              ) : (
                <div className="table-wrap">
                  <table>
                    <thead>
                      <tr>
                        <th>Cluster Name</th>
                        <th>Description</th>
                        <th>Action</th>
                      </tr>
                    </thead>
                    <tbody>
                      {clusters.map((cluster) => (
                        <tr key={cluster.id}>
                          <td><strong>{cluster.name}</strong></td>
                          <td>{cluster.description ?? "-"}</td>
                          <td>
                            <div className="action-stack">
                              <details className="edit-panel">
                                <summary>Edit</summary>
                                <RetainedActionForm label="Update narrative cluster" action={updateNarrativeCluster} className="inline-form">
                                  <input name="id" type="hidden" value={cluster.id} />
                                  <TextField defaultValue={cluster.name} id={`edit-cluster-${cluster.id}`} label="Name" name="name" required />
                                  <TextAreaField className="field field-full" defaultValue={cluster.description ?? ""} id={`edit-cluster-desc-${cluster.id}`} label="Description" name="description" rows={2} />
                                  <div className="button-row">
                                    <button className="secondary-button" type="submit">Save</button>
                                  </div>
                                </RetainedActionForm>
                              </details>
                              <DeleteRecordForm action={deleteNarrativeClusterWithState} recordId={cluster.id} />
                            </div>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </Panel>
          </section>
        </div>
      </>
    );
  } catch (err) {
    return (
      <>
        <PageHeader eyebrow="Social & Narratives" title="Social Intelligence" />
        <ErrorState message="Could not load social posts and narratives from the backend API." />
      </>
    );
  }
}
