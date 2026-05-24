import assert from "node:assert/strict";
import { test } from "node:test";

import {
  buildAlertPayload,
  buildCompanyPayload,
  buildEventPayload,
  buildRawDocumentPayload,
  buildRssIngestionPayload,
  buildSecFilingIngestionPayload,
  buildSourcePayload,
  buildThesisNotePayload,
  getRequiredFormId
} from "./form-payloads.ts";

test("company form payload trims text and treats blank optional fields as null", () => {
  const formData = new FormData();
  formData.set("ticker", " nvda ");
  formData.set("name", " NVIDIA ");
  formData.set("sector", " ");
  formData.set("exchange", "NASDAQ");
  formData.set("active", "on");

  assert.deepEqual(buildCompanyPayload(formData), {
    ticker: "NVDA",
    name: "NVIDIA",
    sector: null,
    industry: null,
    exchange: "NASDAQ",
    cik: null,
    active: true
  });
});

test("source form payload converts reliability score to a number", () => {
  const formData = new FormData();
  formData.set("name", "Manual Research");
  formData.set("source_type", "manual");
  formData.set("reliability_score", "80");

  assert.deepEqual(buildSourcePayload(formData), {
    name: "Manual Research",
    source_type: "manual",
    base_url: null,
    reliability_score: 80
  });
});

test("raw document form payload converts optional ids and text fields", () => {
  const formData = new FormData();
  formData.set("company_id", "");
  formData.set("source_id", "2");
  formData.set("document_type", "filing");
  formData.set("title", "10-K");
  formData.set("content_hash", "hash-1");

  assert.deepEqual(buildRawDocumentPayload(formData), {
    company_id: null,
    source_id: 2,
    document_type: "filing",
    title: "10-K",
    url: null,
    raw_text: null,
    content_hash: "hash-1"
  });
});

test("rss ingestion form payload keeps XML text and required source id", () => {
  const formData = new FormData();
  formData.set("source_id", "3");
  formData.set("company_id", "");
  formData.set("rss_xml", " <rss><channel /></rss> ");

  assert.deepEqual(buildRssIngestionPayload(formData), {
    source_id: 3,
    company_id: null,
    rss_xml: "<rss><channel /></rss>"
  });
});

test("sec filing ingestion form payload parses filing metadata JSON", () => {
  const formData = new FormData();
  formData.set("source_id", "4");
  formData.set("company_id", "2");
  formData.set(
    "filings_json",
    JSON.stringify([
      {
        accession_number: "0000789019-26-000123",
        form_type: "10-Q",
        filing_date: "2026-05-24"
      }
    ])
  );

  assert.deepEqual(buildSecFilingIngestionPayload(formData), {
    source_id: 4,
    company_id: 2,
    filings: [
      {
        accession_number: "0000789019-26-000123",
        form_type: "10-Q",
        filing_date: "2026-05-24"
      }
    ]
  });
});

test("event form payload converts score fields to numbers or null", () => {
  const formData = new FormData();
  formData.set("event_type", "guidance");
  formData.set("information_speed", "fast");
  formData.set("title", "Raised guidance");
  formData.set("credibility_score", "90");
  formData.set("novelty_score", "");
  formData.set("impact_score", "70");
  formData.set("priority_score", "85");

  assert.deepEqual(buildEventPayload(formData), {
    company_id: null,
    raw_document_id: null,
    event_type: "guidance",
    information_speed: "fast",
    title: "Raised guidance",
    description: null,
    credibility_score: 90,
    novelty_score: null,
    impact_score: 70,
    priority_score: 85
  });
});

test("alert and thesis note form payloads keep required ids numeric", () => {
  const alertForm = new FormData();
  alertForm.set("company_id", "1");
  alertForm.set("alert_type", "thesis_watch");
  alertForm.set("severity", "medium");
  alertForm.set("title", "Margin risk");
  alertForm.set("confidence_bucket", "medium");
  alertForm.set("review_status", "unreviewed");

  assert.equal(buildAlertPayload(alertForm).company_id, 1);

  const thesisForm = new FormData();
  thesisForm.set("company_id", "1");
  thesisForm.set("title", "AI demand");
  thesisForm.set("thesis_text", "Demand remains strong.");
  thesisForm.set("status", "active");

  assert.deepEqual(buildThesisNotePayload(thesisForm), {
    company_id: 1,
    title: "AI demand",
    thesis_text: "Demand remains strong.",
    status: "active"
  });
});

test("required form id trims and converts the id field to a number", () => {
  const formData = new FormData();
  formData.set("id", " 42 ");

  assert.equal(getRequiredFormId(formData), 42);
});
