import assert from "node:assert/strict";
import { test } from "node:test";

import type { FinancialExtractionCandidate } from "@/lib/api";
import {
  eventEvidenceGeometry,
  eventEvidenceHref,
  financialEvidenceGeometry,
  financialEvidenceHref,
  financialEvidenceLocatorLabel,
} from "./financial-evidence.ts";
import type { EventEvidenceReference } from "@/lib/api";

const candidate = {
  source_table_name: null,
  source_cell_reference: null,
  source_page: null,
  source_line_number: null,
  source_section: null,
  source_locator_json: null,
} as FinancialExtractionCandidate;

test("financialEvidenceLocatorLabel formats spreadsheet coordinates", () => {
  assert.equal(
    financialEvidenceLocatorLabel({
      ...candidate,
      source_table_name: "Data Sheet",
      source_cell_reference: "B3",
      source_line_number: 3,
    }),
    "Data Sheet / cell B3 / line 3",
  );
});

test("financialEvidenceLocatorLabel falls back to an XBRL concept", () => {
  assert.equal(
    financialEvidenceLocatorLabel({
      ...candidate,
      source_locator_json: { type: "xbrl_fact", concept: "Revenues" },
    }),
    "XBRL us-gaap:Revenues",
  );
});

test("financialEvidenceHref links a PDF candidate to its authenticated source page", () => {
  assert.equal(
    financialEvidenceHref({
      ...candidate,
      id: 41,
      raw_document_id: 9,
      source_page: 12,
      source_locator_json: { type: "pdf_table_cell" },
    }),
    "/api/backend/api/raw-documents/9/asset/content#page=12",
  );
});

test("financialEvidenceGeometry validates exact top-left PDF coordinates", () => {
  const located = {
    ...candidate,
    id: 41,
    raw_document_id: 9,
    source_page: 12,
    source_locator_json: {
      type: "pdf_text_row",
      page: 12,
      coordinate_system: "pdfplumber_top_left_points",
      page_width: 600,
      page_height: 800,
      bounding_box: { x0: 50, top: 100, x1: 550, bottom: 120 },
    },
  } as FinancialExtractionCandidate;

  assert.deepEqual(financialEvidenceGeometry(located), {
    pageNumber: 12,
    pageWidth: 600,
    pageHeight: 800,
    boxes: [{ x0: 50, top: 100, x1: 550, bottom: 120, label: "Reported row" }],
  });
  assert.equal(
    financialEvidenceHref(located),
    "/documents/9/financial-evidence?candidate_id=41",
  );
});

test("financialEvidenceGeometry preserves bounded component-sum rows", () => {
  const component = (top: number) => ({
    type: "pdf_text_row",
    page: 12,
    coordinate_system: "pdfplumber_top_left_points",
    page_width: 600,
    page_height: 800,
    bounding_box: { x0: 50, top, x1: 550, bottom: top + 12 },
  });
  const geometry = financialEvidenceGeometry({
    ...candidate,
    id: 42,
    raw_document_id: 9,
    source_page: 12,
    source_locator_json: {
      type: "pdf_reported_component_sum",
      components: [component(200), component(240)],
    },
  } as FinancialExtractionCandidate);

  assert.deepEqual(geometry?.boxes.map((box) => box.label), ["Component 1", "Component 2"]);
});

test("financialEvidenceGeometry rejects untrusted or out-of-bounds geometry", () => {
  assert.equal(financialEvidenceGeometry({
    ...candidate,
    source_page: 1,
    source_locator_json: {
      type: "pdf_text_row",
      page: 1,
      coordinate_system: "bottom_left_points",
      page_width: 600,
      page_height: 800,
      bounding_box: { x0: 50, top: 100, x1: 700, bottom: 120 },
    },
  } as FinancialExtractionCandidate), null);
});

test("financialEvidenceHref keeps non-PDF evidence in the document review view", () => {
  assert.equal(
    financialEvidenceHref({
      ...candidate,
      id: 41,
      raw_document_id: 9,
    }),
    "/documents/9/sections?candidate_id=41",
  );
});

const eventReference: EventEvidenceReference = {
  id: 17,
  event_id: 8,
  raw_document_id: 9,
  created_by_user_id: "test-user",
  locator_type: "pdf_region",
  source_page: 12,
  source_section: null,
  start_char: null,
  end_char: null,
  quote: "Reported event passage",
  bounding_box_json: {
    page: 12,
    coordinate_system: "pdfplumber_top_left_points",
    page_width: 600,
    page_height: 800,
    bounding_box: { x0: 40, top: 90, x1: 560, bottom: 130 },
  },
  source_metadata_json: null,
  confidence_label: "high",
  origin: "manual_review",
  pdf_region_status: "valid",
  created_at: "2026-08-07T00:00:00Z",
};

test("event PDF evidence uses the exact viewer only for trusted geometry", () => {
  assert.deepEqual(eventEvidenceGeometry(eventReference), {
    pageNumber: 12,
    pageWidth: 600,
    pageHeight: 800,
    boxes: [{ x0: 40, top: 90, x1: 560, bottom: 130, label: "Event evidence region" }],
  });
  assert.equal(
    eventEvidenceHref(eventReference),
    "/documents/9/event-evidence?evidence_reference=17",
  );
});

test("event PDF evidence falls back to the source page for invalid geometry", () => {
  const invalid = {
    ...eventReference,
    bounding_box_json: {
      ...eventReference.bounding_box_json,
      coordinate_system: "bottom_left_points",
    },
  } as EventEvidenceReference;

  assert.equal(eventEvidenceGeometry(invalid), null);
  assert.equal(
    eventEvidenceHref(invalid),
    "/api/backend/api/raw-documents/9/asset/content#page=12",
  );
});

test("event PDF evidence requires backend asset validation", () => {
  const invalid = { ...eventReference, pdf_region_status: "invalid" } as EventEvidenceReference;

  assert.equal(eventEvidenceGeometry(invalid), null);
  assert.equal(
    eventEvidenceHref(invalid),
    "/api/backend/api/raw-documents/9/asset/content#page=12",
  );
});
