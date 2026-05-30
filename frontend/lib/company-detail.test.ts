import assert from "node:assert/strict";
import { test } from "node:test";

import { buildCompanyDetail } from "./company-detail.ts";
import type { AlertRecord, Company, EventRecord, RawDocument, ThesisNote } from "./api.ts";

const company: Company = {
  id: 1,
  ticker: "AAPL",
  name: "Apple Inc.",
  sector: "Technology",
  industry: "Consumer Electronics",
  exchange: "NASDAQ",
  cik: "0000320193",
  aliases_json: ["Apple"],
  country: "United States",
  region: "North America",
  currency: "USD",
  asset_type: "equity",
  security_type: "common_stock",
  market_cap_category: "mega_cap",
  is_etf: false,
  etf_provider: null,
  active: true
};

test("buildCompanyDetail returns only records linked to the selected company", () => {
  const documents: RawDocument[] = [
    { id: 1, company_id: 1, source_id: 1, document_type: "10-K", title: "Apple 10-K", url: null, raw_text: null, content_hash: "a" },
    { id: 2, company_id: 2, source_id: 1, document_type: "10-K", title: "Other 10-K", url: null, raw_text: null, content_hash: "b" }
  ];
  const events: EventRecord[] = [
    {
      id: 1,
      company_id: 1,
      raw_document_id: 1,
      event_type: "sec_filing",
      information_speed: "slow",
      title: "Apple filing",
      description: null,
      credibility_score: 90,
      novelty_score: 70,
      impact_score: 65,
      priority_score: 75,
      score_explanation_json: null
    },
    {
      id: 2,
      company_id: null,
      raw_document_id: null,
      event_type: "manual",
      information_speed: "medium",
      title: "Unlinked",
      description: null,
      credibility_score: null,
      novelty_score: null,
      impact_score: null,
      priority_score: null,
      score_explanation_json: null
    }
  ];
  const alerts: AlertRecord[] = [
    {
      id: 1,
      event_id: 1,
      company_id: 1,
      alert_type: "thesis_watch",
      severity: "high",
      title: "Apple alert",
      summary: null,
      why_it_matters: null,
      confidence_bucket: "high",
      review_status: "unreviewed",
      review_notes: null,
      reviewed_at: null,
      portfolio_priority_score: 0,
      portfolio_impacts: []
    },
    {
      id: 2,
      event_id: null,
      company_id: 2,
      alert_type: "thesis_watch",
      severity: "low",
      title: "Other alert",
      summary: null,
      why_it_matters: null,
      confidence_bucket: "low",
      review_status: "unreviewed",
      review_notes: null,
      reviewed_at: null,
      portfolio_priority_score: 0,
      portfolio_impacts: []
    }
  ];
  const thesisNotes: ThesisNote[] = [
    { id: 1, company_id: 1, title: "Apple thesis", thesis_text: "Services matter.", status: "active", thesis_drift_score: 0, assumptions: [], changes: [] },
    { id: 2, company_id: 2, title: "Other thesis", thesis_text: "Other.", status: "active", thesis_drift_score: 0, assumptions: [], changes: [] }
  ];

  const detail = buildCompanyDetail(company, documents, events, alerts, thesisNotes);

  assert.deepEqual(detail.documents.map((document) => document.id), [1]);
  assert.deepEqual(detail.events.map((event) => event.id), [1]);
  assert.deepEqual(detail.alerts.map((alert) => alert.id), [1]);
  assert.deepEqual(detail.thesisNotes.map((note) => note.id), [1]);
  assert.deepEqual(detail.counts, {
    documents: 1,
    events: 1,
    alerts: 1,
    thesisNotes: 1
  });
});
