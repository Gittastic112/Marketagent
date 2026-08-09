import { triggerParseFilingSections } from "@/app/actions";
import { EmptyState, ErrorState, PageHeader, Panel } from "@/components/page";
import type { EventEvidenceReference, FilingSection, FinancialExtractionCandidate, RawDocument } from "@/lib/api";
import {
  eventEvidenceGeometry,
  eventEvidenceHref,
  financialEvidenceLocatorLabel,
} from "@/lib/financial-evidence";
import { parseFilingDiff } from "@/lib/filing-diff";
import { serverFetchApiResponse } from "@/lib/server-api";
import { DataStateNotices } from "@/components/ui/data-states";
import type { ApiMeta } from "@/lib/api";
import Link from "next/link";

interface PageProps {
  params: Promise<{
    id: string;
  }>;
  searchParams: Promise<{
    candidate_id?: string | string[];
    evidence_reference?: string | string[];
  }>;
}

export default async function DocumentSectionsPage({ params, searchParams }: PageProps) {
  const { id } = await params;
  const query = await searchParams;
  const documentId = Number.parseInt(id, 10);
  const candidateIdValue = Array.isArray(query.candidate_id) ? query.candidate_id[0] : query.candidate_id;
  const candidateId = candidateIdValue ? Number.parseInt(candidateIdValue, 10) : null;
  const referenceIdValue = Array.isArray(query.evidence_reference)
    ? query.evidence_reference[0]
    : query.evidence_reference;
  const referenceId = referenceIdValue ? Number.parseInt(referenceIdValue, 10) : null;

  try {
    const documentRes = await serverFetchApiResponse<RawDocument>(`/raw-documents/${documentId}/summary`);
    const document = documentRes.data;
    const sectionsRes = await serverFetchApiResponse<FilingSection[]>(`/raw-documents/${documentId}/sections`);
    const sections = sectionsRes.data || [];

    let candidate: FinancialExtractionCandidate | null = null;
    let evidenceReference: EventEvidenceReference | null = null;
    const metas: ApiMeta[] = [];

    if (documentRes.meta) metas.push(documentRes.meta);
    if (sectionsRes.meta) metas.push(sectionsRes.meta);

    if (candidateId && Number.isFinite(candidateId)) {
      const candidateRes = await serverFetchApiResponse<FinancialExtractionCandidate>(`/api/financial-line-items/${candidateId}`).catch(() => null);
      if (candidateRes && candidateRes.data) {
        candidate = candidateRes.data;
        if (candidateRes.meta) metas.push(candidateRes.meta);
      }
    }
    const selectedCandidate = candidate?.raw_document_id === documentId ? candidate : null;

    if (referenceId && Number.isFinite(referenceId)) {
      const referenceRes = await serverFetchApiResponse<EventEvidenceReference>(`/evidence-references/${referenceId}`).catch(() => null);
      if (referenceRes && referenceRes.data) {
        evidenceReference = referenceRes.data;
        if (referenceRes.meta) metas.push(referenceRes.meta);
      }
    }
    const selectedReference = evidenceReference?.raw_document_id === documentId ? evidenceReference : null;

    // Bind the server action with the documentId
    const triggerParse = triggerParseFilingSections.bind(null, documentId);

    return (
      <>
        <div style={{ marginBottom: "1rem" }}>
          <Link href="/documents" style={{ color: "var(--brand-primary)", textDecoration: "none" }}>
            &larr; Back to Documents
          </Link>
        </div>
        <PageHeader eyebrow={`Document ${document?.id}`} title={document?.title || "Unknown"} status={`${sections.length} sections`} />

        <DataStateNotices
          metas={metas}
          mockMessage="One or more sections are using mock data. Treat affected source trails as placeholders."
        />

        {selectedCandidate ? (
          <Panel title={`Evidence: ${selectedCandidate.reported_label}`}>
            <div style={{ display: "grid", gap: "0.5rem" }}>
              <p><strong>Claim type:</strong> Source Summary</p>
              <p><strong>Reported value:</strong> {selectedCandidate.value.toLocaleString()} {selectedCandidate.unit || "unit missing"}</p>
              <p><strong>Location:</strong> {financialEvidenceLocatorLabel(selectedCandidate)}</p>
              <p><strong>Source text:</strong> {selectedCandidate.source_text}</p>
              <p><strong>Review status:</strong> {selectedCandidate.review_status.replaceAll("_", " ")}</p>
            </div>
          </Panel>
        ) : candidateId ? (
          <Panel title="Evidence unavailable">
            <p>The requested candidate does not exist or belongs to another document.</p>
          </Panel>
        ) : null}

        {selectedReference ? (
          <Panel title="Exact Event Evidence">
            <div style={{ display: "grid", gap: "0.5rem" }}>
              <p><strong>Locator:</strong> {selectedReference.locator_type.replaceAll("_", " ")}</p>
              {selectedReference.source_page ? <p><strong>Page:</strong> {selectedReference.source_page}</p> : null}
              {selectedReference.source_section ? <p><strong>Section:</strong> {selectedReference.source_section}</p> : null}
              {selectedReference.start_char !== null && selectedReference.end_char !== null ? (
                <p><strong>Characters:</strong> {selectedReference.start_char}-{selectedReference.end_char}</p>
              ) : null}
              <p><strong>Confidence:</strong> {selectedReference.confidence_label}</p>
              {selectedReference.quote ? (
                <blockquote style={{ margin: 0, padding: "0.75rem 1rem", borderLeft: "3px solid var(--brand-primary)" }}>
                  <mark>{selectedReference.quote}</mark>
                </blockquote>
              ) : (
                <p>No text quote is stored for this locator.</p>
              )}
              {eventEvidenceGeometry(selectedReference) ? (
                <Link className="secondary-button" href={eventEvidenceHref(selectedReference)}>
                  Open rendered region
                </Link>
              ) : selectedReference.locator_type === "pdf_region" ? (
                <p className="notice notice-warning">
                  Exact region geometry is unavailable. Use the stored PDF page as the fallback.
                </p>
              ) : null}
            </div>
          </Panel>
        ) : referenceId ? (
          <Panel title="Evidence unavailable">
            <p>The requested evidence reference does not exist or belongs to another document.</p>
          </Panel>
        ) : null}

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
            <div
              id={`section-${section.id}`}
              key={section.id}
              style={
                selectedCandidate?.source_section === section.item_name ||
                selectedCandidate?.source_section === section.title ||
                selectedReference?.source_section === section.item_name ||
                selectedReference?.source_section === section.title
                  ? { outline: "2px solid var(--brand-primary)", outlineOffset: "2px" }
                  : undefined
              }
            >
            <Panel title={`${section.item_name} - ${section.title || "No Title"}`}>
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
                    >
                      {parseFilingDiff(section.diffs_as_current[0].diff_html).map((segment, index) =>
                        segment.kind === "add" ? (
                          <ins className="diff-add" key={index}>{segment.text}</ins>
                        ) : segment.kind === "remove" ? (
                          <del className="diff-remove" key={index}>{segment.text}</del>
                        ) : (
                          <span key={index}>{segment.text}</span>
                        ),
                      )}
                    </div>
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
            </div>
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
