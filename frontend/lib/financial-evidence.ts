import type { EventEvidenceReference, FinancialExtractionCandidate } from "@/lib/api";

export type PdfEvidenceBox = {
  x0: number;
  top: number;
  x1: number;
  bottom: number;
  label: string;
};

export type PdfEvidenceGeometry = {
  pageNumber: number;
  pageWidth: number;
  pageHeight: number;
  boxes: PdfEvidenceBox[];
};

function record(value: unknown): Record<string, unknown> | null {
  return value !== null && typeof value === "object" && !Array.isArray(value)
    ? value as Record<string, unknown>
    : null;
}

function finiteNumber(value: unknown): number | null {
  return typeof value === "number" && Number.isFinite(value) ? value : null;
}

function parseBox(
  locator: Record<string, unknown>,
  pageNumber: number,
  pageWidth: number,
  pageHeight: number,
  label: string,
): PdfEvidenceBox | null {
  const locatorPage = finiteNumber(locator.page);
  const coordinateSystem = locator.coordinate_system;
  const box = record(locator.bounding_box);
  if (
    locatorPage !== pageNumber
    || coordinateSystem !== "pdfplumber_top_left_points"
    || !box
  ) {
    return null;
  }
  const x0 = finiteNumber(box.x0);
  const top = finiteNumber(box.top);
  const x1 = finiteNumber(box.x1);
  const bottom = finiteNumber(box.bottom);
  if (
    x0 === null || top === null || x1 === null || bottom === null
    || x0 < 0 || top < 0 || x1 > pageWidth || bottom > pageHeight
    || x1 <= x0 || bottom <= top
  ) {
    return null;
  }
  return { x0, top, x1, bottom, label };
}

function singlePdfEvidenceGeometry(
  locator: Record<string, unknown> | null,
  pageNumber: number | null,
  label: string,
): PdfEvidenceGeometry | null {
  if (!locator || !pageNumber || pageNumber < 1) return null;
  const pageWidth = finiteNumber(locator.page_width);
  const pageHeight = finiteNumber(locator.page_height);
  if (pageWidth === null || pageHeight === null || pageWidth <= 0 || pageHeight <= 0) {
    return null;
  }
  const box = parseBox(locator, pageNumber, pageWidth, pageHeight, label);
  return box ? { pageNumber, pageWidth, pageHeight, boxes: [box] } : null;
}

export function financialEvidenceGeometry(
  candidate: FinancialExtractionCandidate,
): PdfEvidenceGeometry | null {
  const locator = record(candidate.source_locator_json);
  const pageNumber = candidate.source_page;
  if (!locator || !pageNumber || pageNumber < 1) return null;

  const componentRecords = Array.isArray(locator.components)
    ? locator.components.map(record).filter((item): item is Record<string, unknown> => item !== null)
    : [];
  const dimensionSource = finiteNumber(locator.page_width) && finiteNumber(locator.page_height)
    ? locator
    : componentRecords.find((item) => finiteNumber(item.page_width) && finiteNumber(item.page_height));
  if (!dimensionSource) return null;
  const pageWidth = finiteNumber(dimensionSource.page_width);
  const pageHeight = finiteNumber(dimensionSource.page_height);
  if (pageWidth === null || pageHeight === null || pageWidth <= 0 || pageHeight <= 0) return null;

  const rootBox = parseBox(locator, pageNumber, pageWidth, pageHeight, "Reported row");
  const componentBoxes = componentRecords
    .map((component, index) => parseBox(
      component,
      pageNumber,
      pageWidth,
      pageHeight,
      `Component ${index + 1}`,
    ))
    .filter((box): box is PdfEvidenceBox => box !== null);
  const boxes = componentBoxes.length > 0 ? componentBoxes : rootBox ? [rootBox] : [];
  return boxes.length > 0 ? { pageNumber, pageWidth, pageHeight, boxes } : null;
}

export function financialEvidenceLocatorLabel(candidate: FinancialExtractionCandidate): string {
  const location = [
    candidate.source_table_name,
    candidate.source_cell_reference ? `cell ${candidate.source_cell_reference}` : null,
    candidate.source_page ? `page ${candidate.source_page}` : null,
    candidate.source_line_number ? `line ${candidate.source_line_number}` : null,
  ].filter(Boolean);

  if (location.length > 0) {
    return location.join(" / ");
  }

  const locatorType = candidate.source_locator_json?.type;
  if (locatorType === "xbrl_fact") {
    const concept = candidate.source_locator_json?.concept;
    return typeof concept === "string" ? `XBRL us-gaap:${concept}` : "XBRL fact";
  }

  return candidate.source_section || "Source location unavailable";
}

export function financialEvidenceHref(candidate: FinancialExtractionCandidate): string {
  if (financialEvidenceGeometry(candidate)) {
    return `/documents/${candidate.raw_document_id}/financial-evidence?candidate_id=${candidate.id}`;
  }
  const locatorType = candidate.source_locator_json?.type;
  if (typeof locatorType === "string" && locatorType.startsWith("pdf_")) {
    const page = candidate.source_page && candidate.source_page > 0 ? `#page=${candidate.source_page}` : "";
    return `/api/backend/api/raw-documents/${candidate.raw_document_id}/asset/content${page}`;
  }
  return `/documents/${candidate.raw_document_id}/sections?candidate_id=${candidate.id}`;
}

export function eventEvidenceGeometry(
  reference: EventEvidenceReference,
): PdfEvidenceGeometry | null {
  if (reference.locator_type !== "pdf_region" || reference.pdf_region_status !== "valid") {
    return null;
  }
  return singlePdfEvidenceGeometry(
    record(reference.bounding_box_json),
    reference.source_page,
    "Event evidence region",
  );
}

export function eventEvidenceHref(reference: EventEvidenceReference): string {
  if (eventEvidenceGeometry(reference)) {
    return `/documents/${reference.raw_document_id}/event-evidence?evidence_reference=${reference.id}`;
  }
  if (reference.locator_type === "pdf_region") {
    const page = reference.source_page && reference.source_page > 0 ? `#page=${reference.source_page}` : "";
    return `/api/backend/api/raw-documents/${reference.raw_document_id}/asset/content${page}`;
  }
  return `/documents/${reference.raw_document_id}/sections?evidence_reference=${reference.id}`;
}
