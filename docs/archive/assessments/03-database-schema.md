# Database Schema

This file summarizes the current schema and the immediate next schema work based on the frontend/backend design brief.

## Purpose
The database is the app's memory. It must preserve source provenance, portfolio data, explainable scores, human review decisions, and strictly track the health of data ingestion.

## Implemented Tables

### User
```text
id
email
name
created_at
```

This table provides the foundation for multi-tenancy. Core entity tables reference `user_id` to strictly isolate data at the API layer.

### Company
```text
id
ticker
name
sector
industry
exchange
market
primary_exchange
local_symbol
isin
figi
regulatory_id
regulatory_id_type
cik
damodaran_industry
aliases_json
country
region
currency
asset_type
security_type
market_cap_category
is_etf
etf_provider
active
created_at
updated_at
```

Company identity is now market-aware. `ticker` remains for display and backward compatibility, but it is not globally unique. The API enforces duplicate detection on `(market, primary_exchange, local_symbol)` so the same ticker can exist in the US and India without collision. `damodaran_industry` stores the highest-weight industry for compatibility; the persisted mix below is canonical when present.

### CompanyIndustryMix / CompanyIndustryAllocation
```text
company_industry_mixes:
id
company_id
basis
as_of_date
source_document_id
notes
created_at
updated_at

company_industry_allocations:
id
mix_id
segment_name
industry_name
weight_percent
created_at
updated_at
```

One current mix is stored per company. The implemented basis is `revenue`.
Allocations must use unique non-empty segment labels, reference a name in the
loaded Damodaran taxonomy, remain individually above 0% and at most 100%, and
total 100% within a 0.01 percentage-point tolerance. `source_document_id` is an
optional company-owned evidence link; the mix remains a `User Assumption` even
when source-backed. Weighted priors are `Estimate` outputs. If any component
lacks a benchmark value, that blended field is unavailable; the service never
renormalizes around missing data. Migration `j6j6j6j6j6j6` adds both tables.

### Source
```text
id
name
source_type
base_url
reliability_score
active
created_at
updated_at
```

### MarketSourceCapability
```text
id
market
source_type
provider_name
capability
status
requires_api_key
freshness_expected_seconds
notes
updated_at
```

This table is the source capability matrix for US/India feature availability. Status values are `available`, `manual_only`, `not_configured`, or `not_supported`. The API uses this table to avoid implying that unsupported India/US data sources are live.

### CountryMarketContext
```text
id
market
country
currency
risk_free_rate
risk_free_rate_source
equity_risk_premium
country_risk_premium
inflation_rate
fx_rate_to_usd
as_of_date
is_manual
notes
created_at
updated_at
```

This table stores manual country/market macro and rate context for valuation. It currently uses one row per market and does not seed default USD or INR rates. `GET /api/valuation/risk-free-rate?currency=...` only returns a rate when a stored row has both `risk_free_rate` and `risk_free_rate_source`.

### RawDocument
```text
id
company_id
source_id
document_type
title
url
published_at
ingested_at
raw_text
raw_payload_json
content_hash
created_at
```

### DocumentAsset
```text
id
raw_document_id
original_filename
mime_type
size_bytes
sha256
page_count
content
created_at
```

`document_assets` is a one-to-one binary companion to `raw_documents`.
`raw_document_id` is unique and cascades on delete. Normal document and asset
metadata responses omit `content`; the original PDF is available only through
the authenticated stream endpoint. `sha256` is indexed for audit and duplicate
checks, while the raw-document `content_hash` remains company-scoped.
Migration `a7a7a7a7a7a7` adds this table.

### FinancialStatementPeriod / FinancialMetric
```text
financial_statement_periods:
id
company_id
period_type
year
quarter
report_date
currency
currency_source
currency_confidence
created_at
updated_at

financial_metrics:
id
period_id
metric_name
value
unit
created_at
updated_at
```

These are the approved/stored financial period and metric tables currently used by fundamentals views and valuation inputs.

### FinancialExtractionCandidate
```text
id
company_id
raw_document_id
metric_code
reported_label
value
unit
fiscal_year
period_type
source_text
source_line_number
source_page
source_section
source_table_name
source_row_label
source_column_label
source_cell_reference
source_locator_json
extraction_warnings
extraction_method
confidence_label
review_status
created_at
updated_at
```

This table stores first-pass extracted candidate metrics from filing text, PDF
tables, structured workbooks, or SEC XBRL. It is intentionally separate from
`financial_metrics` because candidates must be reviewed before they should feed
valuation or normalized statements. The nullable source fields hold common
coordinates, while `source_locator_json` carries a typed `text_line`,
`pdf_table_cell`, `spreadsheet_cell`, or `xbrl_fact` locator. PDF locators use
one-based page/table/row/column labels and `pdfplumber_top_left_points` table
and cell bounding boxes. `extraction_warnings` stores stable semicolon-separated
warning codes such as `reporting_unit_missing`,
`fiscal_year_inferred_from_document`, and
`multiple_numeric_values_on_source_line`. Formula locators may additionally
carry `claim_type: Calculation`, a component list, exclusions, and a reproducible
formula. Point-in-time source revisions preserve that calculation claim instead
of mislabeling it as a reported fact.

Reviewed candidates can be promoted into legacy metrics and canonical normalized snapshots. Review and override require a reporting unit. Promotion persists reporting-currency source/confidence, rejects conflicting reviewed currencies, and is covered for review/override/reject/promote paths. Promoted rows remain in `financial_extraction_candidates` as audit history, are individually readable, and are excluded from the active company review-list endpoint. Migration `e5e5e5e5e5e5` added text evidence fields; additive migration `f6f6f6f6f6f6` added structured table/cell/locator fields without rewriting existing rows.

### NormalizedFinancialSnapshot / NormalizedFinancialMetric
```text
normalized_financial_snapshots:
id
company_id
period_id
created_at
updated_at

normalized_financial_metrics:
id
snapshot_id
metric_code
value
unit
provenance_notes
warnings
created_at
updated_at
```

These tables are the canonical reviewed-financial store when a snapshot exists. Candidate promotion writes them transactionally. `GET /api/companies/{company_id}/financial-statements/normalized/coverage` audits period coverage and trust readiness without writing. `POST /api/companies/{company_id}/financial-statements/normalized/backfill` can dry-run or create missing/stale snapshots and returns coverage before and after the operation. Currency-conflicting periods are reported and skipped; legacy metrics remain a labeled compatibility source until historical coverage is complete.

`GET /data-health/evidence-integrity` derives financial trust state without a
new badge table. It checks every promoted candidate's exact locator, fiscal-year
resolution, and locator period end against `financial_statement_periods`, then
runs the real-source history gate for each company represented by promoted
facts. The response exposes checked candidate/period counts, eligible history
count, certified markets, and `passed`, `partial`, `blocked`, or
`not_available` certification state.

### Event
```text
id
company_id
raw_document_id
event_type
information_speed
title
description
event_time
credibility_score
novelty_score
impact_score
priority_score
score_explanation_json
created_at
```

### Alert
```text
id
event_id
company_id
alert_type
severity
title
summary
why_it_matters
what_changed
evidence
confidence_bucket
review_status
review_notes
reviewed_at
created_at
```

### ThesisNote
```text
id
company_id
title
thesis_text
assumptions_json
status
created_at
updated_at
```

### DailyBrief
```text
id
brief_date
title
summary
payload_json
created_at
```

### ProcessingRun
```text
id
request_id
run_type
source_type
source_id
company_id
started_at
finished_at
status
fetched_count
created_count
skipped_duplicate_count
error_count
error_details_json
metadata_json
created_at
```

`request_id` is nullable for historical/manual records and indexed for support
lookups. New HTTP-triggered runs inherit the validated request-context ID;
processing-run lifecycle logs include both identifiers. Added by migration
`c9c9c9c9c9c9`.

### Portfolio
```text
id
name
base_currency
description
created_at
updated_at
```

### PortfolioHolding
```text
id
portfolio_id
company_id
ticker
quantity
average_cost
currency
as_of_date
created_at
updated_at
```

### PortfolioTransaction
```text
id
portfolio_id
company_id
ticker
transaction_type
quantity
price
fees
currency
transaction_date
notes
created_at
updated_at
```

### PortfolioCashBalance
```text
id
portfolio_id
currency
amount
as_of_date
created_at
updated_at
```

### PortfolioSnapshot
```text
id
portfolio_id
snapshot_date
total_market_value
total_cost_basis
total_cash
payload_json
created_at
```

### ValuationModels & Damodaran Benchmarks
*(Damodaran Valuation Agent and DCF tables)*
```text
valuation_models (id, company_id, name, model_type)
valuation_setup_drafts (id, user_id, company_id, promoted_model_id, status, industry_name, assumptions_json, provenance_json, source_metadata_json, warnings_json, reviewed_fields_json, edited_fields_json)
dcf_assumption_sets (id, valuation_model_id, scenario, revenue_growth, margins, wacc, etc.)
dcf_projection_years (id, assumption_set_id, year, fcff, roic, etc.)
dcf_outputs (id, assumption_set_id, enterprise_value, equity_value, fcfe_intrinsic_value_per_share, ddm_intrinsic_value_per_share, etc.)
dcf_sensitivity_tables
dcf_decision_logs

damodaran_dataset_files (
  id,
  uploaded_filename,
  dataset_code,
  country,
  region,
  source_file_type,
  source_sha256,
  source_byte_size,
  source_as_of,
  date_confidence,
  canonical_source_path,
  import_kind,
  is_active,
  superseded_at,
  row_count,
  imported_at,
  notes
)
damodaran_industry_pricing_benchmarks (one sparse row per source version and industry; firm count; PE/trailing/forward/aggregate/PEG/growth controls; PBV/ROE/EV-IC/ROIC; PS/net margin/EV-sales/pre-tax operating margin; positive-denominator and all-firm EV/R&D-adjusted EBITDA, EV/EBITDA, EV/EBIT, and EV/after-tax EBIT)
damodaran_industry_margin_benchmarks (firm count, gross margin, net margin, pre-tax unadjusted operating margin in ebit_margin, EBITDA/sales)
damodaran_industry_roe_benchmarks (firm count, unadjusted ROE, R&D-adjusted ROE; legacy ROC/ROIC columns remain nullable and are not populated from roeIndia.xls)
damodaran_industry_working_capital_benchmarks (firm count, non-cash working capital/sales; legacy wc_to_sales remains nullable)
damodaran_industry_dividend_benchmarks (firm count, dividend yield, dividend payout ratio)
damodaran_industry_fcfe_benchmarks (firm count, net income, FCFE before debt cash flows, FCFE after debt cash flows; legacy fcfe mirrors after-debt and unsupported component fields remain nullable)
industry_volatility_benchmarks (nullable legacy-compatible dataset_file_id, source date, firm count, equity/firm-value volatility, capital weights, source volatility/correlation assumptions)
macro_series
macro_observations
sector_macro_sensitivity_benchmarks
```

`damodaran_dataset_files` is the source-version parent for dataset-backed typed
benchmarks. `is_active` selects the version used by assumption and industry
mapping readers; superseded child rows remain stored for auditability. A typed
version is reproducible only when hash, source date/confidence, canonical path,
and row count are present. Migration `k7k7k7k7k7k7` introduced this contract;
`l8l8l8l8l8l8` added exact firm-count and FCFE aggregate fields needed by the
Margin, Working Capital, Dividend, and FCFE conversions. Migration
`m9m9m9m9m9m9` linked volatility rows to preserved dataset versions. The link is
nullable only so unproven historical rows can remain stored; active readers
exclude them.

Migration `n0n0n0n0n0n0` adds the omitted PE growth/aggregate fields, PBV return
controls, PS margin controls, and EV normalization variants. It does not merge
the four source rows. Their independent `dataset_file_id` values preserve
source-specific history; active read assembly occurs in the service layer.

Migration `p1p1p1p1p1p1` adds `median_cash_to_firm_value` and
`total_dividends_usd_millions` to `country_market_stats`. Existing debt, firm
value, cash, source date, and multiple fields are now populated by the exact
country-stat importer. Each row belongs to a preserved `countrystats` dataset
version; active API and mapping reads join through the active parent.

### Macro Sensitivity Benchmarks
*(Batch 05 macro duration, cyclicality, inflation, and currency source data)*
```text
macro_series (id, name, description, units, frequency)
macro_observations (id, series_id, date_recorded, value)
sector_macro_sensitivity_benchmarks (
  id,
  source_file,
  market,
  country,
  classification_system,
  currency_context,
  currency_variable_description,
  sic_code,
  industry_name,
  firm_value_duration,
  firm_value_cyclicality,
  firm_value_inflation,
  firm_value_currency,
  operating_income_duration,
  operating_income_cyclicality,
  operating_income_inflation,
  operating_income_currency,
  created_at
)
```

Existing `macrodur.xls` sector rows are tagged as `market=IN`, `country=India`, and `classification_system=SIC`. The source coefficient signs are preserved. Consumers should use `raw_duration`, `duration_magnitude`, and `duration_interpretation` API fields instead of changing negative duration values in storage.

---

## Implemented but Still Being Hardened

### Score / Scoring Config
*(Supports explainable event and alert scoring.)*
```text
id
entity_type
entity_id
score_type
value
label
direction
confidence
explanation
inputs_json
created_at
updated_at
```

### Narrative
*(Tracks thematic stories linking companies and source material. Backend models/routes exist; UX and provenance should continue to be audited.)*
```text
id
name
description
status
confidence
first_seen_at
last_seen_at
created_at
updated_at
```

### NarrativeSource
```text
id
narrative_id
source_type
source_id
relevance_score
evidence_summary
created_at
```

### NarrativeCompanyLink
```text
id
narrative_id
company_id
ticker
relationship_type
strength
created_at
```

### ResearchSession
*(User-owned research workspace persistence.)*
```text
id
user_id -> users.id
title
created_at
updated_at
```

### ResearchMessage
```text
id
session_id
role
content
created_at
```

### AiOutput
*(Unified user-owned AI success/failure and provenance record. Added fields are
introduced by migration `b8b8b8b8b8b8`.)*
```text
id
user_id -> users.id
raw_document_id -> raw_documents.id, nullable
reference_type
reference_id
provider_name
model_name
is_mock
prompt_version
input_hash                 # SHA-256 for new output
source_ids_json
source_scope
privacy_disclosure_version
external_data_classes_json
transmission_scope         # none | external_provider | unknown legacy
execution_status           # success | failed
failure_code
output_text
limitations
confidence_label
human_review_status
reviewer_id -> users.id, nullable
reviewed_at
created_at
```

Existing pre-contract records are conservatively backfilled as
`provider_name=legacy_unknown`, `is_mock=true`, disclosure `legacy`, and
transmission scope `unknown` because prior rows cannot prove their provider.



---

## Security Notes
- Portfolio data is private financial data.
- Do not store broker passwords.
- Do not add broker sync until OAuth/token handling is designed.
- Treat imported CSV, markdown, RSS, social posts, and AI output as untrusted.
- See `docs/06-security-threat-model.md` before adding imports, external APIs, AI, broker integrations, or deployment.
## 2026-08-01 Additions

Current Alembic head: `h4h4h4h4h4h4`.

### `event_evidence_references`

Stores one or more exact references per event: owning raw document, optional
creator, locator type, page/section/span/quote/bounding box, metadata,
confidence, origin, and timestamp.

New `pdf_region` records use a normalized JSON contract containing the physical
page number, `pdfplumber_top_left_points` coordinate system, page width/height,
and `x0/top/x1/bottom`. The API verifies positive finite bounds and compares the
declared dimensions with the stored `DocumentAsset` page. Older page-only rows
remain schema-compatible but are not treated as exact regions.

### `ai_outputs` citation fields

`citations_json`, `citation_validation_status`, `evaluation_json`, and
`review_notes` extend the existing owned provenance and review record.

### `source_fact_revisions`

Stores reviewed financial fact revisions with company, source document,
financial candidate, fact key/value/unit, period, effective date, observed and
superseded timestamps, revision number, and `Fact` claim type. The initial
domain is reviewed financial promotion only.

### Full-text indexes

`ix_raw_documents_search_vector`, `ix_events_search_vector`,
`ix_thesis_notes_search_vector`, `ix_alerts_search_vector`,
`ix_decision_logs_search_vector`, and `ix_valuation_models_search_vector` are
PostgreSQL GIN expression indexes over English `tsvector` values. No vector
database is used.
