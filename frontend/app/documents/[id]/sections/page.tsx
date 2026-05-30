import { triggerParseFilingSections } from "@/app/actions";
import { EmptyState, ErrorState, PageHeader, Panel } from "@/components/page";
import { fetchApi, listFilingSections } from "@/lib/api";
import type { FilingSection, RawDocument } from "@/lib/api";
import Link from "next/link";

interface PageProps {
  params: Promise<{
    id: string;
  }>;
}

export default async function DocumentSectionsPage({ params }: PageProps) {
  const { id } = await params;
  const documentId = Number.parseInt(id, 10);

  try {
    const document = await fetchApi<RawDocument>(`/raw-documents/${documentId}`);
    const sections = await listFilingSections(documentId);

    // Bind the server action with the documentId
    const triggerParse = triggerParseFilingSections.bind(null, documentId);

    return (
      <>
        <div style={{ marginBottom: "1rem" }}>
          <Link href="/documents" style={{ color: "var(--brand-primary)", textDecoration: "none" }}>
            &larr; Back to Documents
          </Link>
        </div>
        <PageHeader eyebrow={`Document ${document.id}`} title={document.title} status={`${sections.length} sections`} />
        
        <Panel title="Parse Document">
          <form action={triggerParse}>
            <p style={{ marginBottom: "1rem", color: "var(--text-secondary)" }}>
              Extracts standard sections (e.g., &quot;Item 1A&quot;) and computes text diffs against the previous comparable filing.
            </p>
            <button type="submit">Run Parser &amp; Diff Engine</button>
          </form>
        </Panel>

        {sections.length === 0 ? (
          <EmptyState label="No sections parsed yet. Click 'Run Parser' above." />
        ) : (
          sections.map((section) => (
            <Panel key={section.id} title={`${section.item_name} - ${section.title || "No Title"}`}>
              <div style={{ display: "flex", gap: "2rem", flexDirection: "column" }}>
                <div>
                  <h4 style={{ marginBottom: "0.5rem", color: "var(--text-secondary)" }}>Section Metrics</h4>
                  <p><strong>Word count:</strong> {section.word_count}</p>
                  <p><strong>Extracted:</strong> {new Date(section.created_at).toLocaleString()}</p>
                </div>
                
                {section.diffs_as_current.length > 0 && section.diffs_as_current[0].diff_html ? (
                  <div>
                    <h4 style={{ marginBottom: "0.5rem", color: "var(--text-secondary)" }}>Changes since prior filing</h4>
                    <p style={{ marginBottom: "1rem" }}>
                      <strong>Added words:</strong> <span style={{ color: "var(--success-color)" }}>+{section.diffs_as_current[0].added_words}</span> | 
                      <strong> Removed words:</strong> <span style={{ color: "var(--error-color)" }}>-{section.diffs_as_current[0].removed_words}</span>
                    </p>
                    <div 
                      className="html-diff-view"
                      style={{ 
                        maxHeight: "400px", 
                        overflow: "auto", 
                        padding: "1rem", 
                        background: "var(--surface-color)", 
                        border: "1px solid var(--border-color)", 
                        borderRadius: "8px",
                        whiteSpace: "pre-wrap",
                        fontFamily: "monospace"
                      }}
                      dangerouslySetInnerHTML={{ __html: section.diffs_as_current[0].diff_html }} 
                    />
                  </div>
                ) : (
                  <div>
                    <h4 style={{ marginBottom: "0.5rem", color: "var(--text-secondary)" }}>Raw Text Content</h4>
                    <div style={{ 
                      maxHeight: "400px", 
                      overflow: "auto", 
                      padding: "1rem", 
                      background: "var(--surface-color)", 
                      border: "1px solid var(--border-color)", 
                      borderRadius: "8px",
                      whiteSpace: "pre-wrap",
                      fontFamily: "monospace"
                    }}>
                      {section.text_content}
                    </div>
                  </div>
                )}
              </div>
            </Panel>
          ))
        )}
      </>
    );
  } catch {
    return (
      <>
        <PageHeader eyebrow="Error" title="Document Not Found" />
        <ErrorState message="Could not load document or sections from the API." />
      </>
    );
  }
}
