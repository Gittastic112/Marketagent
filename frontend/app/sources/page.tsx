import { createSource, deleteSource, updateSource } from "@/app/actions";
import { EmptyState, ErrorState, PageHeader, Panel } from "@/components/page";
import { fetchApi } from "@/lib/api";
import type { Source } from "@/lib/api";

export default async function SourcesPage() {
  try {
    const sources = await fetchApi<Source[]>("/sources");

    return (
      <>
        <PageHeader eyebrow="Evidence inputs" title="Sources" status={`${sources.length} sources`} />
        <Panel title="Add Source">
          <form action={createSource} className="form-grid">
            <div className="field field-wide">
              <label htmlFor="name">Name</label>
              <input id="name" name="name" required />
            </div>
            <div className="field">
              <label htmlFor="source_type">Type</label>
              <input id="source_type" name="source_type" placeholder="manual" required />
            </div>
            <div className="field">
              <label htmlFor="reliability_score">Reliability</label>
              <input id="reliability_score" max="100" min="0" name="reliability_score" type="number" />
            </div>
            <div className="field field-wide">
              <label htmlFor="base_url">Base URL</label>
              <input id="base_url" name="base_url" type="url" />
            </div>
            <div className="button-row">
              <button type="submit">Add source</button>
            </div>
          </form>
        </Panel>
        <Panel title="Sources">
          {sources.length === 0 ? (
            <EmptyState label="No sources yet." />
          ) : (
            <div className="table-wrap">
              <table>
                <thead>
                  <tr>
                    <th>Name</th>
                    <th>Type</th>
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
                      <td>{source.reliability_score ?? "-"}</td>
                      <td>{source.base_url ?? "-"}</td>
                      <td>
                        <div className="action-stack">
                          <details className="edit-panel">
                            <summary>Edit</summary>
                            <form action={updateSource} className="inline-form">
                              <input name="id" type="hidden" value={source.id} />
                              <div className="field">
                                <label htmlFor={`source-name-${source.id}`}>Name</label>
                                <input defaultValue={source.name} id={`source-name-${source.id}`} name="name" required />
                              </div>
                              <div className="field">
                                <label htmlFor={`source-type-${source.id}`}>Type</label>
                                <input defaultValue={source.source_type} id={`source-type-${source.id}`} name="source_type" required />
                              </div>
                              <div className="field">
                                <label htmlFor={`source-reliability-${source.id}`}>Reliability</label>
                                <input defaultValue={source.reliability_score ?? ""} id={`source-reliability-${source.id}`} max="100" min="0" name="reliability_score" type="number" />
                              </div>
                              <div className="field">
                                <label htmlFor={`source-url-${source.id}`}>Base URL</label>
                                <input defaultValue={source.base_url ?? ""} id={`source-url-${source.id}`} name="base_url" type="url" />
                              </div>
                              <div className="button-row">
                                <button className="secondary-button" type="submit">Save</button>
                              </div>
                            </form>
                          </details>
                          <form action={deleteSource} className="row-action">
                            <input name="id" type="hidden" value={source.id} />
                            <button className="danger-button" type="submit">Delete</button>
                          </form>
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
