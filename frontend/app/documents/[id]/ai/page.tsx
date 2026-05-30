import { triggerGenerateAiSummary } from "@/app/actions";
import { EmptyState, ErrorState, PageHeader, Panel } from "@/components/page";
import { fetchApi, listAiOutputs } from "@/lib/api";
import type { AiOutput, RawDocument } from "@/lib/api";
import Link from "next/link";

interface PageProps {
  params: Promise<{
    id: string;
  }>;
}

export default async function DocumentAiPage({ params }: PageProps) {
  const { id } = await params;
  const documentId = Number.parseInt(id, 10);

  try {
    const document = await fetchApi<RawDocument>(`/raw-documents/${documentId}`);
    const aiOutputs = await listAiOutputs(documentId);

    // Bind the server action with the documentId
    const triggerSummary = triggerGenerateAiSummary.bind(null, documentId);

    return (
      <>
        <div style={{ marginBottom: "1rem" }}>
          <Link href="/documents" style={{ color: "var(--brand-primary)", textDecoration: "none" }}>
            &larr; Back to Documents
          </Link>
        </div>
        <PageHeader eyebrow={`Document ${document.id}`} title={document.title} status={`${aiOutputs.length} AI summaries`} />
        
        <Panel title="Generate AI Summary">
          <form action={triggerSummary}>
            <p style={{ marginBottom: "1rem", color: "var(--text-secondary)" }}>
              Generates a summary of the raw document using an AI model. If no API key is configured, a mocked response is returned.
            </p>
            <button type="submit">Generate Summary</button>
          </form>
        </Panel>

        {aiOutputs.length === 0 ? (
          <EmptyState label="No AI summaries generated yet." />
        ) : (
          aiOutputs.map((output) => (
            <Panel key={output.id} title={`Summary by ${output.model_name}`}>
              <div style={{ display: "flex", gap: "2rem", flexDirection: "column" }}>
                <div>
                  <h4 style={{ marginBottom: "0.5rem", color: "var(--text-secondary)" }}>Metadata</h4>
                  <p><strong>Created:</strong> {new Date(output.created_at).toLocaleString()}</p>
                  <p><strong>Confidence:</strong> {output.confidence_label}</p>
                  <p><strong>Review Status:</strong> <span style={{ textTransform: "capitalize" }}>{output.human_review_status}</span></p>
                  <p><strong>Input Hash:</strong> {output.input_hash.substring(0, 12)}...</p>
                </div>
                
                <div>
                  <h4 style={{ marginBottom: "0.5rem", color: "var(--text-secondary)" }}>Output</h4>
                  <div style={{ 
                    maxHeight: "400px", 
                    overflow: "auto", 
                    padding: "1rem", 
                    background: "var(--surface-color)", 
                    border: "1px solid var(--border-color)", 
                    borderRadius: "8px",
                    whiteSpace: "pre-wrap"
                  }}>
                    {output.output_text}
                  </div>
                </div>

                {output.limitations && (
                  <div>
                    <h4 style={{ marginBottom: "0.5rem", color: "var(--warning-color)" }}>Limitations &amp; Disclaimers</h4>
                    <p style={{ color: "var(--text-secondary)", fontSize: "0.9rem" }}>{output.limitations}</p>
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
        <ErrorState message="Could not load document or AI outputs from the API." />
      </>
    );
  }
}
