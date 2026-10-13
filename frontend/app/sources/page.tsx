import { RetainedActionForm } from "@/components/retained-action-form";
import { hasUsableData } from "@/lib/data-state-meta";
import { createSource, deleteSourceWithState, fetchActiveRssFeeds, fetchRssFeed, updateSource } from "@/app/actions";
import { DeleteRecordForm } from "@/components/delete-record-form";
import { CheckboxField, TextField } from "@/components/form-fields";
import { EmptyState, ErrorState, PageHeader, Panel } from "@/components/page";
import { DataStateNotices } from "@/components/ui/data-states";
import { serverFetchApiResponse } from "@/lib/server-api";
import type { Source } from "@/lib/api";

export default async function SourcesPage() {
  try {
    const sourcesRes = await serverFetchApiResponse<Source[]>("/sources");
    const sources = sourcesRes.data || [];
    const activeRssCount = sources.filter((source) => source.source_type === "rss" && source.active && source.base_url).length;

    return (
      <>
        <PageHeader eyebrow="Evidence inputs" title="Sources" status={hasUsableData(sourcesRes) ? `${sources.length} sources` : "Sources unavailable"} />
        <DataStateNotices
          metas={[sourcesRes.meta]}
          mockMessage="Source configuration is mocked. Configure real sources before using ingestion outputs."
        />
        <Panel title="RSS Feed Runs">
          <RetainedActionForm label="Fetch active rss feeds" action={fetchActiveRssFeeds} className="button-row">
            <button disabled={activeRssCount === 0} type="submit">Fetch active RSS feeds</button>
          </RetainedActionForm>
        </Panel>
        <Panel title="Add Source">
          <RetainedActionForm label="Create source" resetOnSuccess action={createSource} className="form-grid">
            <TextField className="field field-wide" id="name" label="Name" name="name" required />
            <TextField id="source_type" label="Type" name="source_type" placeholder="manual" required />
            <TextField id="reliability_score" label="Reliability" max="100" min="0" name="reliability_score" type="number" />
            <TextField className="field field-wide" id="base_url" label="Base URL" name="base_url" type="url" />
            <CheckboxField checkboxLabel="Active" className="field field-wide" defaultChecked id="active" label="Status" name="active" />
            <div className="button-row">
              <button type="submit">Add source</button>
            </div>
          </RetainedActionForm>
        </Panel>
        <Panel title="Sources">
          {!hasUsableData(sourcesRes) ? <ErrorState message="Sources could not be loaded. Reload to retry." /> : sources.length === 0 ? (
            <EmptyState label="No sources yet." />
          ) : (
            <div className="table-wrap">
              <table>
                <thead>
                  <tr>
                    <th>Name</th>
                    <th>Type</th>
                    <th>Status</th>
                    <th>Reliability</th>
                    <th>Base URL</th>
                    <th>Action</th>
                  </tr>
                </thead>
                <tbody>
                  {sources.map((source) => (
                    <tr key={source.id}>
                      <td>{source.name}</td>
                      <td>{source.source_type}</td>
                      <td>{source.active ? "Active" : "Inactive"}</td>
                      <td>{source.reliability_score ?? "-"}</td>
                      <td>{source.base_url ?? "-"}</td>
                      <td>
                        <div className="action-stack">
                          <details className="edit-panel">
                            <summary>Edit</summary>
                            <RetainedActionForm label="Update source" action={updateSource} className="inline-form">
                              <input name="id" type="hidden" value={source.id} />
                              <TextField defaultValue={source.name} id={`source-name-${source.id}`} label="Name" name="name" required />
                              <TextField defaultValue={source.source_type} id={`source-type-${source.id}`} label="Type" name="source_type" required />
                              <TextField defaultValue={source.reliability_score ?? ""} id={`source-reliability-${source.id}`} label="Reliability" max="100" min="0" name="reliability_score" type="number" />
                              <TextField defaultValue={source.base_url ?? ""} id={`source-url-${source.id}`} label="Base URL" name="base_url" type="url" />
                              <CheckboxField checkboxLabel="Active" defaultChecked={source.active} id={`source-active-${source.id}`} label="Status" name="active" />
                              <div className="button-row">
                                <button className="secondary-button" type="submit">Save</button>
                              </div>
                            </RetainedActionForm>
                          </details>
                          {source.source_type === "rss" && source.base_url ? (
                            <RetainedActionForm label="Fetch rss feed" action={fetchRssFeed} className="row-action">
                              <input name="source_id" type="hidden" value={source.id} />
                              <button className="secondary-button" disabled={!source.active} type="submit">Fetch feed</button>
                            </RetainedActionForm>
                          ) : null}
                          <DeleteRecordForm action={deleteSourceWithState} recordId={source.id} />
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </Panel>
      </>
    );
  } catch {
    return (
      <>
        <PageHeader eyebrow="Evidence inputs" title="Sources" />
        <ErrorState message="Could not load sources from the backend API." />
      </>
    );
  }
}
