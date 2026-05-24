import { EmptyState, ErrorState, PageHeader, Panel } from "@/components/page";
import { fetchApi } from "@/lib/api";
import type { RawDocument } from "@/lib/api";

export default async function DocumentsPage() {
  try {
    const documents = await fetchApi<RawDocument[]>("/raw-documents");

    return (
      <>
        <PageHeader eyebrow="Source material" title="Raw Documents" status={`${documents.length} stored`} />
        <Panel title="Documents">
          {documents.length === 0 ? (
            <EmptyState label="No raw documents yet." />
          ) : (
            <div className="table-wrap">
              <table>
                <thead>
                  <tr>
                    <th>Title</th>
                    <th>Type</th>
                    <th>Company ID</th>
                    <th>Source ID</th>
                    <th>Hash</th>
                  </tr>
                </thead>
                <tbody>
                  {documents.map((document) => (
                    <tr key={document.id}>
                      <td>{document.title}</td>
                      <td>{document.document_type}</td>
                      <td>{document.company_id ?? "-"}</td>
                      <td>{document.source_id}</td>
                      <td>{document.content_hash}</td>
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
        <PageHeader eyebrow="Source material" title="Raw Documents" />
        <ErrorState message="Could not load raw documents from the backend API." />
      </>
    );
  }
}
