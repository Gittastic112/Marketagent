import { RetainedActionForm } from "@/components/retained-action-form";
import { triggerParseFilingSections } from "@/app/actions";
import { EmptyState, ErrorState, PageHeader, Panel } from "@/components/page";
import type { DocumentAsset, EventEvidenceReference, FilingSection, FinancialExtractionCandidate, RawDocument } from "@/lib/api";
import { ApiError } from "@/lib/api/contract";
import {
  eventEvidenceGeometry,
  eventEvidenceHref,
  financialEvidenceClaimType,
  financialEvidenceLocatorLabel,
  financialOverrideNotice,
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
    const evidenceClaim = selectedCandidate ? financialEvidenceClaimType(selectedCandidate) : null;
    const scopeNotes = selectedCandidate?.source_locator_json?.reviewed_limitations;
    const reviewNotes = Array.isArray(scopeNotes) ? scopeNotes.filter((note): note is string => typeof note === "string") : [];
    const sourceDate = selectedCandidate?.source_locator_json?.end;
    const originalText = selectedCandidate?.source_text ?? "";
    const repeatedScope = ` Review scope: ${reviewNotes.join(" ")}`;
    const sourceText = reviewNotes.length && originalText.endsWith(repeatedScope)
      ? originalText.slice(0, -repeatedScope.length) : originalText;
    const originalUrl = document?.url && /^https?:\/\//i.test(document.url) ? document.url : null;
    let workbookAsset: DocumentAsset | null = null;
    let workbookNotice: string | null = null;
    if (document?.document_type === "screener_export") {
      try {
        workbookAsset = (await serverFetchApiResponse<DocumentAsset>(`/api/raw-documents/${documentId}/asset`)).data;
      } catch (error) {
        workbookNotice = error instanceof ApiError && error.status === 404
          ? "The original workbook was not retained by the older importer. Upload the identical original file for this company to restore it without changing reviewed values."
          : "Original workbook availability could not be checked. Reload to retry.";
      }
    }

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
        <p><Link href="/">Return to Today</Link>{document?.company_id && <> · <Link href={`/companies/${document.company_id}/fundamentals#dated-inputs`}>Review this company’s dated financial inputs</Link> · <Link href={`/companies/${document.company_id}/valuation`}>Saved models remain unchanged</Link></>}</p>
        <PageHeader
          eyebrow={`Document ${document?.id}`}
          title={document?.title || "Unknown"}
          status={`${sections.length} sections`}
          actions={originalUrl ? (
            <a className="secondary-button" href={originalUrl} target="_blank" rel="noopener noreferrer">
              Open original source
            </a>
          ) : undefined}
        />

        <DataStateNotices
          metas={metas}
          mockMessage="One or more sections are using mock data. Treat affected source trails as placeholders."
        />
        {workbookAsset ? <p><a className="secondary-button" href={`/api/backend/api/raw-documents/${documentId}/asset/content`}>Download original workbook</a></p> : null}
        {workbookNotice ? <p className="notice notice-warning">{workbookNotice}</p> : null}

        {selectedCandidate ? (
          <Panel title={`Evidence: ${selectedCandidate.reported_label}`}>
            <div style={{ display: "grid", gap: "0.5rem" }}>
              <p><strong>Claim type:</strong> {evidenceClaim}</p>
              {financialOverrideNotice(selectedCandidate) ? <p className="notice notice-warning">{financialOverrideNotice(selectedCandidate)}</p> : null}
              <p><strong>{evidenceClaim === "Calculation" ? "Calculated value" : evidenceClaim === "User Assumption" ? "Assumed value" : "Reported value"}:</strong> {selectedCandidate.value.toLocaleString()} {selectedCandidate.unit || "unit missing"}</p>
              {typeof sourceDate === "string" ? <p><strong>Period end:</strong> {sourceDate}</p> : null}
              <p><strong>Location:</strong> {financialEvidenceLocatorLabel(selectedCandidate)}</p>
              <p style={{ overflowWrap: "anywhere" }}><strong>Source text and basis:</strong> {sourceText}</p>
              <p><strong>Review status:</strong> {selectedCandidate.review_status.replaceAll("_", " ")}</p>
              {reviewNotes.length ? <div><strong>Review scope</strong><ul>{reviewNotes.map((note, index) => <li key={index}>{note}</li>)}</ul></div> : null}
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

        {document?.document_type !== "screener_export" ? <Panel title="Parse Document">
          <RetainedActionForm label="Trigger parse" action={triggerParse}>
            <p style={{ marginBottom: "1rem", color: "var(--text-secondary)" }}>
              Extracts standard sections (e.g., &quot;Item 1A&quot;) and computes text diffs against the previous comparable filing.
            </p>
            <button type="submit">Run Parser &amp; Diff Engine</button>
          </RetainedActionForm>
        </Panel> : <p>Workbook evidence uses the original file and its sheet and cell references. Text-section parsing is not available for workbooks.</p>}

        {sections.length === 0 ? (
          document?.document_type !== "screener_export" ? <EmptyState label="No sections parsed yet. Click 'Run Parser' above." /> : null
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
