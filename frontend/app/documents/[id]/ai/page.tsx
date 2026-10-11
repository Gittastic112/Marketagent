import { triggerGenerateAiSummary } from "@/app/actions";
import { EmptyState, ErrorState, PageHeader, Panel } from "@/components/page";
import { serverFetchApiResponse } from "@/lib/server-api";
import { DataStateNotices } from "@/components/ui/data-states";
import type { ApiMeta, AiOutput, RawDocument } from "@/lib/api";
import Link from "next/link";
import { AI_DISCLOSURES, AI_PRIVACY_DISCLOSURE_VERSION } from "@/lib/ai-privacy";
import { AiOutputReviewControls } from "@/components/ai-output-review-controls";

interface PageProps {
  params: Promise<{
    id: string;
  }>;
}

export default async function DocumentAiPage({ params }: PageProps) {
  const { id } = await params;
  const documentId = Number.parseInt(id, 10);

  try {
    const documentRes = await serverFetchApiResponse<RawDocument>(`/raw-documents/${documentId}/summary`);
    const document = documentRes.data;
    const aiOutputsRes = await serverFetchApiResponse<AiOutput[]>(`/raw-documents/${documentId}/ai-outputs`);
    const aiOutputs = aiOutputsRes.data || [];

    const metas: ApiMeta[] = [];
    if (documentRes.meta) metas.push(documentRes.meta);
    if (aiOutputsRes.meta) metas.push(aiOutputsRes.meta);

    // Bind the server action with the documentId
    const triggerSummary = triggerGenerateAiSummary.bind(null, documentId);

    return (
      <>
        <div style={{ marginBottom: "1rem" }}>
          <Link href="/documents" style={{ color: "var(--brand-primary)", textDecoration: "none" }}>
            &larr; Back to Documents
          </Link>
        </div>
        <PageHeader eyebrow={`Document ${document?.id}`} title={document?.title || "Unknown"} status={`${aiOutputs.length} AI summaries`} />
        <DataStateNotices
          metas={metas}
          mockMessage="One or more AI outputs are using mock data. Treat affected summaries as placeholders."
        />

        <Panel title="Generate AI Summary">
          <form action={triggerSummary}>
            <p style={{ marginBottom: "1rem", color: "var(--text-secondary)" }}>
              AI must be configured unless explicit demo mode is enabled. Provider failures are shown as failures and never replaced by mock text.
            </p>
            <label style={{ display: "flex", gap: "0.5rem", alignItems: "flex-start", marginBottom: "1rem" }}>
              <input
                type="checkbox"
                name="privacy_disclosure_version"
                value={AI_PRIVACY_DISCLOSURE_VERSION}
                required
              />
              <span>{AI_DISCLOSURES.documentSummary}</span>
            </label>
            <button type="submit">Generate Summary</button>
          </form>
        </Panel>

        {aiOutputs.length === 0 ? (
          <EmptyState label="No AI summaries generated yet." />
        ) : (
          aiOutputs.map((output) => (
            <div key={output.id} id={`ai-output-${output.id}`} className="anchored-record">
            <Panel title={`${output.is_mock ? "Mock Data" : "Summary"} by ${output.model_name}`}>
              <div style={{ display: "flex", gap: "2rem", flexDirection: "column" }}>
                <div>
                  <h4 style={{ marginBottom: "0.5rem", color: "var(--text-secondary)" }}>Metadata</h4>
                  <p><strong>Created:</strong> {new Date(output.created_at).toLocaleString()}</p>
                  <p><strong>Confidence:</strong> {output.confidence_label}</p>
                  <p><strong>Provider:</strong> {output.provider_name}</p>
                  <p><strong>Source scope:</strong> {output.source_scope}</p>
                  <p><strong>Transmission:</strong> {output.transmission_scope}</p>
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

                <AiOutputReviewControls initialOutput={output} />
              </div>
            </Panel>
            </div>
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
