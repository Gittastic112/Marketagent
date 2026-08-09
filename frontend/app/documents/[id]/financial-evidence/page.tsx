import Link from "next/link";
import { notFound } from "next/navigation";
import { ArrowLeft, ExternalLink } from "lucide-react";

import { ErrorState, PageHeader } from "@/components/page";
import type { DocumentAsset, FinancialExtractionCandidate, RawDocument } from "@/lib/api";
import {
  financialEvidenceGeometry,
  financialEvidenceLocatorLabel,
} from "@/lib/financial-evidence";
import { serverFetchApiResponse } from "@/lib/server-api";
import { DataStateNotices } from "@/components/ui/data-states";
import type { ApiMeta } from "@/lib/api";

type PageProps = {
  params: Promise<{ id: string }>;
  searchParams: Promise<{ candidate_id?: string | string[] }>;
};

export default async function FinancialEvidencePage({ params, searchParams }: PageProps) {
  const { id } = await params;
  const query = await searchParams;
  const candidateValue = Array.isArray(query.candidate_id)
    ? query.candidate_id[0]
    : query.candidate_id;
  const documentId = Number.parseInt(id, 10);
  const candidateId = candidateValue ? Number.parseInt(candidateValue, 10) : Number.NaN;
  if (!Number.isFinite(documentId) || !Number.isFinite(candidateId)) notFound();

  try {
    const metas: ApiMeta[] = [];
    const [documentRes, assetRes, candidateRes] = await Promise.all([
      serverFetchApiResponse<RawDocument>(`/raw-documents/${documentId}/summary`),
      serverFetchApiResponse<DocumentAsset>(`/api/raw-documents/${documentId}/asset`),
      serverFetchApiResponse<FinancialExtractionCandidate>(`/api/financial-line-items/${candidateId}`),
    ]);

    if (documentRes.meta) metas.push(documentRes.meta);
    if (assetRes.meta) metas.push(assetRes.meta);
    if (candidateRes.meta) metas.push(candidateRes.meta);

    const document = documentRes.data;
    const asset = assetRes.data;
    const candidate = candidateRes.data;

    if (!document || !asset || !candidate || candidate.raw_document_id !== document.id) notFound();

    const geometry = financialEvidenceGeometry(candidate);
    const sourcePdfHref = `/api/backend/api/raw-documents/${document.id}/asset/content${
      candidate.source_page ? `#page=${candidate.source_page}` : ""
    }`;
    const pageImageHref = geometry
      ? `/api/backend/api/raw-documents/${document.id}/asset/pages/${geometry.pageNumber}.png?scale=1.5`
      : null;

    return (
      <>
        <div style={{ marginBottom: "1rem" }}>
          <Link href={`/companies/${candidate.company_id}/fundamentals`} className="inline-flex items-center gap-2">
            <ArrowLeft aria-hidden="true" size={16} />
            Back to fundamentals
          </Link>
        </div>
        <PageHeader
          eyebrow={`Document ${document.id} / Page ${candidate.source_page ?? "unknown"}`}
          title={candidate.reported_label}
          status={geometry ? `${geometry.boxes.length} exact region${geometry.boxes.length === 1 ? "" : "s"}` : "Document-level fallback"}
        />
        <DataStateNotices
          metas={metas}
          mockMessage="This financial evidence relies on mocked document data. Treat it as placeholder."
        />

        <div className="financial-evidence-layout">
          <aside className="financial-evidence-summary" aria-label="Financial evidence details">
            <div>
              <span className="metric-label">Reported value</span>
              <strong>{candidate.value.toLocaleString()} {candidate.unit || "unit missing"}</strong>
            </div>
            <div>
              <span className="metric-label">Metric</span>
              <strong>{candidate.metric_code.replaceAll("_", " ")}</strong>
            </div>
            <div>
              <span className="metric-label">Fiscal period</span>
              <strong>{candidate.period_type} {candidate.fiscal_year ?? "unknown"}</strong>
            </div>
            <div>
              <span className="metric-label">Review status</span>
              <span className={`badge ${
                candidate.review_status === "promoted" || candidate.review_status === "reviewed"
                  ? "badge-success"
                  : "badge-warn"
              }`}>
                {candidate.review_status.replaceAll("_", " ")}
              </span>
            </div>
            <div>
              <span className="metric-label">Source locator</span>
              <span>{financialEvidenceLocatorLabel(candidate)}</span>
            </div>
            <div>
              <span className="metric-label">Source text</span>
              <span>{candidate.source_text}</span>
            </div>
            <div>
              <span className="metric-label">Document</span>
              <span>{document.title}</span>
              <span className="financial-evidence-filename">{asset.original_filename}</span>
            </div>
            <Link href={sourcePdfHref} target="_blank" rel="noopener noreferrer" className="secondary-button">
              <ExternalLink aria-hidden="true" size={16} />
              Open source PDF
            </Link>
          </aside>

          <section className="financial-evidence-stage" aria-label="Rendered source evidence">
            {geometry && pageImageHref ? (
              <div
                className="financial-evidence-page"
                style={{ aspectRatio: `${geometry.pageWidth} / ${geometry.pageHeight}` }}
              >
                {/* The authenticated same-origin proxy requires the browser session cookie. */}
                <img
                  src={pageImageHref}
                  alt={`Rendered page ${geometry.pageNumber} from ${document.title}`}
                />
                {geometry.boxes.map((box, index) => (
                  <span
                    aria-hidden="true"
                    className="financial-evidence-box"
                    key={`${box.x0}-${box.top}-${index}`}
                    title={box.label}
                    style={{
                      left: `${(box.x0 / geometry.pageWidth) * 100}%`,
                      top: `${(box.top / geometry.pageHeight) * 100}%`,
                      width: `${((box.x1 - box.x0) / geometry.pageWidth) * 100}%`,
                      height: `${((box.bottom - box.top) / geometry.pageHeight) * 100}%`,
                    }}
                  />
                ))}
              </div>
            ) : (
              <div className="notice notice-warning">
                Exact PDF geometry is unavailable for this candidate. The source PDF and page reference remain available.
              </div>
            )}
          </section>
        </div>
      </>
    );
  } catch {
    return (
      <>
        <PageHeader eyebrow="Evidence Error" title="Financial evidence unavailable" />
        <ErrorState message="The candidate, document asset, or rendered evidence page could not be loaded." />
      </>
    );
  }
}
