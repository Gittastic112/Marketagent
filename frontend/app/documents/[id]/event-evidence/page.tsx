import Link from "next/link";
import { notFound } from "next/navigation";
import { ArrowLeft, ExternalLink } from "lucide-react";

import { ErrorState, PageHeader } from "@/components/page";
import type { DocumentAsset, EventEvidenceReference, RawDocument } from "@/lib/api";
import { eventEvidenceGeometry } from "@/lib/financial-evidence";
import { serverFetchApiResponse } from "@/lib/server-api";
import { DataStateNotices } from "@/components/ui/data-states";
import type { ApiMeta } from "@/lib/api";

type PageProps = {
  params: Promise<{ id: string }>;
  searchParams: Promise<{ evidence_reference?: string | string[] }>;
};

export default async function EventEvidencePage({ params, searchParams }: PageProps) {
  const { id } = await params;
  const query = await searchParams;
  const referenceValue = Array.isArray(query.evidence_reference)
    ? query.evidence_reference[0]
    : query.evidence_reference;
  const documentId = Number.parseInt(id, 10);
  const referenceId = referenceValue ? Number.parseInt(referenceValue, 10) : Number.NaN;
  if (!Number.isFinite(documentId) || !Number.isFinite(referenceId)) notFound();

  try {
    const metas: ApiMeta[] = [];
    const [documentRes, assetRes, referenceRes] = await Promise.all([
      serverFetchApiResponse<RawDocument>(`/raw-documents/${documentId}/summary`),
      serverFetchApiResponse<DocumentAsset>(`/api/raw-documents/${documentId}/asset`),
      serverFetchApiResponse<EventEvidenceReference>(`/evidence-references/${referenceId}`),
    ]);

    if (documentRes.meta) metas.push(documentRes.meta);
    if (assetRes.meta) metas.push(assetRes.meta);
    if (referenceRes.meta) metas.push(referenceRes.meta);

    const document = documentRes.data;
    const asset = assetRes.data;
    const reference = referenceRes.data;

    if (!document || !asset || !reference || reference.raw_document_id !== document.id) notFound();

    const geometry = eventEvidenceGeometry(reference);
    const sourcePdfHref = `/api/backend/api/raw-documents/${document.id}/asset/content${
      reference.source_page ? `#page=${reference.source_page}` : ""
    }`;
    const pageImageHref = geometry
      ? `/api/backend/api/raw-documents/${document.id}/asset/pages/${geometry.pageNumber}.png?scale=1.5`
      : null;

    return (
      <>
        <div style={{ marginBottom: "1rem" }}>
          <Link
            href={`/documents/${document.id}/sections?evidence_reference=${reference.id}`}
            className="inline-flex items-center gap-2"
          >
            <ArrowLeft aria-hidden="true" size={16} />
            Back to document evidence
          </Link>
        </div>
        <PageHeader
          eyebrow={`Event ${reference.event_id} / Document ${document.id}`}
          title="Event source evidence"
          status={geometry ? "Exact PDF region" : "Page-level fallback"}
        />
        <DataStateNotices
          metas={metas}
          mockMessage="This event evidence relies on mocked document data. Treat it as placeholder."
        />

        <div className="financial-evidence-layout">
          <aside className="financial-evidence-summary" aria-label="Event evidence details">
            <div>
              <span className="metric-label">Claim type</span>
              <strong>Source Summary</strong>
            </div>
            <div>
              <span className="metric-label">Locator</span>
              <strong>{geometry ? `Page ${geometry.pageNumber} region` : `Page ${reference.source_page ?? "unknown"}`}</strong>
            </div>
            <div>
              <span className="metric-label">Confidence</span>
              <span className="badge badge-outline">{reference.confidence_label}</span>
            </div>
            <div>
              <span className="metric-label">Origin</span>
              <span>{reference.origin.replaceAll("_", " ")}</span>
            </div>
            <div>
              <span className="metric-label">Source passage</span>
              <span>{reference.quote || "No bounded quote is stored for this region."}</span>
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

          <section className="financial-evidence-stage" aria-label="Rendered event evidence">
            {geometry && pageImageHref ? (
              <div
                className="financial-evidence-page"
                style={{ aspectRatio: `${geometry.pageWidth} / ${geometry.pageHeight}` }}
              >
                <img
                  src={pageImageHref}
                  alt={`Rendered page ${geometry.pageNumber} from ${document.title}`}
                />
                {geometry.boxes.map((box) => (
                  <span
                    aria-hidden="true"
                    className="financial-evidence-box"
                    key={`${box.x0}-${box.top}`}
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
                Exact PDF geometry is unavailable or unsupported. The stored source PDF and page reference remain available.
              </div>
            )}
          </section>
        </div>
      </>
    );
  } catch {
    return (
      <>
        <PageHeader eyebrow="Evidence Error" title="Event evidence unavailable" />
        <ErrorState message="The evidence reference, document asset, or rendered page could not be loaded." />
      </>
    );
  }
}
