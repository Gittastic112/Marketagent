import assert from "node:assert/strict";
import { test } from "node:test";

import {
  buildAlertPayload,
  buildAlertReviewPayload,
  buildCompanyPayload,
  buildEventPayload,
  buildPortfolioHoldingPayload,
  buildPortfolioPayload,
  buildPortfolioTransactionPayload,
  buildRawDocumentMetadataPayload,
  buildRawDocumentPayload,
  buildRssIngestionPayload,
  buildSecFilingIngestionPayload,
  buildSourcePayload,
  buildThesisNotePayload,
  buildMarketPricePayload,
  buildDcfAssumptionSetPayload,
  getRequiredFormId
} from "./form-payloads.ts";

test("versioned DCF form distinguishes omitted fields from explicit clears and zero", () => {
  const form = new FormData();
  form.set("scenario", "Base");
  form.set("base_assumption_set_id", "7");
  form.set("base_assumption_set_updated_at", "2026-09-10T00:00:00Z");
  form.set("net_income", "0");
  form.set("currency_override_note", "");
  const payload = buildDcfAssumptionSetPayload(form);
  assert.equal(payload.base_assumption_set_id, 7);
  assert.equal(payload.base_assumption_set_updated_at, "2026-09-10T00:00:00Z");
  assert.equal(payload.net_income, 0);
  assert.equal(payload.currency_override_note, null);
  for (const field of ["book_value_of_equity", "target_roe", "probability_of_failure", "projection_years_count", "reinvestment_story"]) {
    assert.equal(field in payload, false, field);
  }
});

test("DCF numeric inputs reject nonfinite text and preserve zero for backend validation", () => {
  const form = new FormData(); form.set("scenario", "Base");
  form.set("projection_years", "0");
  assert.equal(buildDcfAssumptionSetPayload(form).projection_years_count, 0);
  for (const value of ["NaN", "Infinity", "invalid"]) {
    form.set("net_income", value);
    assert.throws(() => buildDcfAssumptionSetPayload(form), /finite number/);
  }
});

test("DCF payload preserves every rendered payout and equity-bridge input", () => {
  const formData = new FormData();
  formData.set("scenario", "Base");
  formData.set("projection_years", "7");
  formData.set("capex", "120");
  formData.set("depreciation", "80");
  formData.set("change_in_nwc", "25");
  formData.set("dividends", "30");
  formData.set("buybacks", "15");
  formData.set("stock_issuances", "5");
  formData.set("new_debt_issued", "40");
  formData.set("debt_repaid", "10");
  formData.set("company_age", "18");
  formData.set("cash_flow_currency", " inr ");
  formData.set("discount_rate_currency", " usd ");
  formData.set("currency_override_note", " USD contract cash flows ");

  const payload = buildDcfAssumptionSetPayload(formData);

  assert.equal(payload.projection_years_count, 7);
  assert.equal(payload.capex, 120);
  assert.equal(payload.depreciation, 80);
  assert.equal(payload.change_in_nwc, 25);
  assert.equal(payload.dividends, 30);
  assert.equal(payload.buybacks, 15);
  assert.equal(payload.stock_issuances, 5);
  assert.equal(payload.new_debt_issued, 40);
  assert.equal(payload.debt_repaid, 10);
  assert.equal(payload.company_age, 18);
  assert.equal(payload.cash_flow_currency, "INR");
  assert.equal(payload.discount_rate_currency, "USD");
  assert.equal(payload.currency_override_note, "USD contract cash flows");
});

test("company form payload trims text and treats blank optional fields as null", () => {
  const formData = new FormData();
  formData.set("ticker", " nvda ");
  formData.set("name", " NVIDIA ");
  formData.set("sector", " ");
  formData.set("exchange", "NASDAQ");
  formData.set("aliases", " Nvidia, GeForce ");
  formData.set("country", " United States ");
  formData.set("region", " North America ");
  formData.set("currency", " usd ");
  formData.set("asset_type", " equity ");
  formData.set("security_type", " common_stock ");
  formData.set("market_cap_category", " mega_cap ");
  formData.set("active", "on");

  assert.deepEqual(buildCompanyPayload(formData), {
    market: null,
    primary_exchange: null,
    local_symbol: null,
    ticker: "NVDA",
    name: "NVIDIA",
    sector: null,
    industry: null,
    damodaran_industry: null,
    exchange: "NASDAQ",
    cik: null,
    isin: null,
    regulatory_id: null,
    regulatory_id_type: null,
    aliases_json: ["Nvidia", "GeForce"],
    country: "United States",
    region: "North America",
    currency: "USD",
    asset_type: "equity",
    security_type: "common_stock",
    market_cap_category: "mega_cap",
    is_etf: false,
    etf_provider: null,
    active: true
  });
});

test("company form payload includes market identity fields", () => {
  const formData = new FormData();
  formData.set("market", " in ");
  formData.set("primary_exchange", " nse ");
  formData.set("local_symbol", " reliance ");
  formData.set("ticker", " reliance ");
  formData.set("name", " Reliance Industries ");
  formData.set("isin", " ine002a01018 ");
  formData.set("regulatory_id", " INE002A01018 ");
  formData.set("regulatory_id_type", " isin ");
  formData.set("currency", " inr ");
  formData.set("active", "on");

  assert.deepEqual(buildCompanyPayload(formData), {
    market: "IN",
    primary_exchange: "NSE",
    local_symbol: "RELIANCE",
    ticker: "RELIANCE",
    name: "Reliance Industries",
    sector: null,
    industry: null,
    damodaran_industry: null,
    exchange: null,
    cik: null,
    isin: "INE002A01018",
    regulatory_id: "INE002A01018",
    regulatory_id_type: "ISIN",
    aliases_json: null,
    country: null,
    region: null,
    currency: "INR",
    asset_type: null,
    security_type: null,
    market_cap_category: null,
    is_etf: false,
    etf_provider: null,
    active: true
  });
});

test("source form payload converts reliability score to a number", () => {
  const formData = new FormData();
  formData.set("name", "Manual Research");
  formData.set("source_type", "manual");
  formData.set("reliability_score", "80");
  formData.set("active", "on");

  assert.deepEqual(buildSourcePayload(formData), {
    name: "Manual Research",
    source_type: "manual",
    base_url: null,
    reliability_score: 80,
    active: true
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

test("raw document metadata update does not erase stored source text", () => {
  const formData = new FormData();
  formData.set("company_id", "1");
  formData.set("source_id", "2");
  formData.set("document_type", "filing");
  formData.set("title", "10-K");
  formData.set("url", "https://example.com/10-k");
  formData.set("published_at", "2026-07-30T12:00");
  formData.set("content_hash", "hash-1");

  assert.deepEqual(buildRawDocumentMetadataPayload(formData), {
    company_id: 1,
    source_id: 2,
    document_type: "filing",
    title: "10-K",
    url: "https://example.com/10-k",
    published_at: "2026-07-30T12:00",
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
    rss_xml: "<rss><channel /></rss>",
    feed_url: null
  });
});

test("sec filing ingestion form payload parses filing metadata JSON", () => {
  const formData = new FormData();
  formData.set("source_id", "4");
  formData.set("company_id", "2");
  formData.set("download_text", "on");
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
    ],
    form_types: ["10-K", "10-Q", "8-K"],
    filing_year: null,
    limit: 40,
    download_text: true
  });
});

test("sec filing ingestion form payload honors selected form and filing year", () => {
  const formData = new FormData();
  formData.set("source_id", "4");
  formData.set("company_id", "2");
  formData.set("form_type", "10-K");
  formData.set("filing_year", "2026");
  formData.set("limit", "10");

  assert.deepEqual(buildSecFilingIngestionPayload(formData), {
    source_id: 4,
    company_id: 2,
    filings: [],
    form_types: ["10-K"],
    filing_year: 2026,
    limit: 10,
    download_text: false
  });
});

test("sec filing ingestion allows the backend to resolve the SEC source", () => {
  const formData = new FormData();
  formData.set("company_id", "2");
  formData.set(
    "filings_json",
    JSON.stringify([
      {
        accession_number: "0000789019-26-000124",
        form_type: "10-Q",
        filing_date: "2026-05-25"
      }
    ])
  );

  assert.deepEqual(buildSecFilingIngestionPayload(formData), {
    source_id: null,
    company_id: 2,
    filings: [
      {
        accession_number: "0000789019-26-000124",
        form_type: "10-Q",
        filing_date: "2026-05-25"
      }
    ],
    form_types: ["10-K", "10-Q", "8-K"],
    filing_year: null,
    limit: 40,
    download_text: false
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
  alertForm.set("review_notes", "Needs a second source.");

  assert.equal(buildAlertPayload(alertForm).company_id, 1);
  assert.deepEqual(buildAlertReviewPayload(alertForm), {
    review_status: "unreviewed",
    review_notes: "Needs a second source."
  });

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

test("portfolio form payload trims text and keeps base currency uppercase", () => {
  const formData = new FormData();
  formData.set("name", " Core Portfolio ");
  formData.set("base_currency", " usd ");
  formData.set("description", " Long-term holdings ");

  assert.deepEqual(buildPortfolioPayload(formData), {
    name: "Core Portfolio",
    base_currency: "USD",
    description: "Long-term holdings"
  });
});

test("portfolio holding payload converts ids and numeric fields", () => {
  const formData = new FormData();
  formData.set("portfolio_id", "1");
  formData.set("company_id", "");
  formData.set("ticker", " aapl ");
  formData.set("quantity", "12.5");
  formData.set("average_cost", "145.25");
  formData.set("currency", " usd ");
  formData.set("as_of_date", "2026-05-26");

  assert.deepEqual(buildPortfolioHoldingPayload(formData), {
    portfolio_id: 1,
    company_id: null,
    ticker: "AAPL",
    quantity: 12.5,
    average_cost: 145.25,
    currency: "USD",
    as_of_date: "2026-05-26"
  });
});

test("portfolio transaction payload converts ids, numeric fields, and notes", () => {
  const formData = new FormData();
  formData.set("portfolio_id", "1");
  formData.set("company_id", "2");
  formData.set("ticker", " aapl ");
  formData.set("transaction_type", "buy");
  formData.set("quantity", "10");
  formData.set("price", "180.5");
  formData.set("fees", "1.25");
  formData.set("currency", " usd ");
  formData.set("transaction_date", "2026-05-26");
  formData.set("notes", " Initial entry ");

  assert.deepEqual(buildPortfolioTransactionPayload(formData), {
    portfolio_id: 1,
    company_id: 2,
    ticker: "AAPL",
    transaction_type: "buy",
    quantity: 10,
    price: 180.5,
    fees: 1.25,
    currency: "USD",
    transaction_date: "2026-05-26",
    notes: "Initial entry"
  });
});

test("required form id trims and converts the id field to a number", () => {
  const formData = new FormData();
  formData.set("id", " 42 ");

  assert.equal(getRequiredFormId(formData), 42);
});

test("market price payload converts numeric fields and uppercase strings", () => {
  const formData = new FormData();
  formData.set("company_id", "5");
  formData.set("ticker", " aapl ");
  formData.set("price", " 150.5 ");
  formData.set("currency", " usd ");
  formData.set("as_of_date", " 2026-05-28 ");

  assert.deepEqual(buildMarketPricePayload(formData), {
    company_id: 5,
    ticker: "AAPL",
    price: 150.5,
    currency: "USD",
    as_of_date: "2026-05-28"
  });
});
