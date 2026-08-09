# Agent Capabilities and Limitations

Last audited: 2026-08-08 (Damodaran versioned volatility/API sections reconciled;
the full long-form audit outside those sections remains the 2026-07-31 baseline)

This document describes what the current Market Intelligence Engine can and cannot do based on the repository state, planning docs, backend services, frontend routes, database models, scripts, and tests. It is intentionally blunt. Do not treat planned features as working product.

## 1. Executive Summary

The app is a local-first investment intelligence and portfolio research system. Its job is to help a user track companies, ingest source documents, extract events, score those events, review alerts, manage a portfolio, and run source-aware valuation workflows.

What it currently does well:

- It has a broad FastAPI backend with many real database-backed routes.
- It has a serious deterministic valuation layer, especially FCFF DCF, diagnostics, sensitivity analysis, reverse DCF, WACC, macro sensitivity, relative valuation, and Damodaran benchmark ingestion.
- It supports core research objects: companies, sources, raw documents, events, alerts, thesis notes, daily briefs, portfolios, market prices, valuation models, evidence, decisions, narratives, and research sessions.
- It has meaningful automated coverage. The current baseline is `461` backend
  tests, `90` frontend tests, clean TypeScript, and a successful production
  build. Browser automation was not rerun in the latest Damodaran batch; do not
  infer current visual proof from the unit/build baseline.
- It now has structural support for both US and India markets: market-aware company identity, country market context, source capability metadata, currency fields, and manual India filing support.

What is partially built:

- SEC and RSS ingestion are functional when configured and triggered, but this is not a fully automated research machine.
- India support is mostly structural and manual. Automated NSE/BSE filing lookup is not implemented.
- Market data providers exist for Alpha Vantage/FMP style integration, but provider-backed coverage is not yet a complete, trusted US/India data layer.
- AI memo and narrative-to-numbers features exist, but they are assistive and require review. They must not be treated as verified finance logic.
- The frontend server-rendered routes use the signed-identity server API helper and preserve response metadata. Isolated authenticated browser coverage now protects responsive accessibility, alert evidence, PDF review/promotion, AI failure disclosure, invalid CSV recovery, mobile navigation, and valuation draft promotion; other state-changing and live-provider failure paths still need broader coverage.
- Financial candidates preserve typed text, PDF table/statement-row,
  spreadsheet-cell, or XBRL-fact locators and link to their owning
  document/source page. PDF locators can include explicit reported-component
  sum formulas. They are deterministic parser evidence, not an audited claim of
  statement completeness.
- Alert/event evidence supports validated text-span, page, section, and PDF
  region references. Legacy records without a precise reference remain visibly
  partial or document-level.
- Stored AI output supports exact declared-source citation validation,
  deterministic evaluation, owner-scoped review, and approval blocking. AI
  providers do not yet generate complete citations automatically, and the
  evaluation corpus is small.
- Reviewed financial promotions now create point-in-time source-fact revisions.
  Other fact domains do not yet preserve revision history.
- PostgreSQL evidence search currently covers raw documents and events. It is
  not yet unified across thesis, alert, decision, and valuation content.
- Normalized financial coverage and source reconciliation are implemented.
  AAPL FY2022-FY2025 is reviewed, trust-ready, and exactly reconciled. Adani
  FY2023-FY2025 is staged but not promoted. Synthetic `Mock Data` histories
  remain separate.
- A fail-closed real-source certification harness exists. The current eligible
  count is one, represented market `US`; the overall two-market gate is blocked
  until India passes.

What is not built yet:

- Public deployment readiness.
- Production-grade authentication and authorization. A local single-user credential/session boundary exists, but it is not suitable for public deployment.
- Broker sync.
- Real-time trading data.
- Fully automated financial statement ingestion for every company.
- Production-grade India data ingestion.
- A fully trusted market-regime engine.
- A fully audited source-backed AI research workflow.

What users should not assume:

- Do not assume every UI panel is backed by live data.
- Do not assume industry mapping is correct without review.
- Do not assume AI text is fact.
- Do not assume valuation output is useful unless assumptions and source data have been checked.
- Do not assume this app is safe to expose publicly.
- Do not treat anything as a buy/sell recommendation.

## 2. Product Purpose

The core problem is investment research drift: users collect filings, news, thesis notes, prices, assumptions, alerts, and valuation work in separate places, then lose the link between evidence and judgment.

The target user is an equity-focused investor, analyst, founder-investor, or portfolio manager who wants a local research cockpit rather than a generic chatbot.

The intended workflow:

1. Track companies and portfolios.
2. Configure sources.
3. Ingest source documents.
4. Extract events and evidence.
5. Score what matters.
6. Review alerts and daily briefs.
7. Maintain thesis notes and assumptions.
8. Run valuation models.
9. Compare market price, thesis, risk, and portfolio exposure.
10. Decide what to inspect next.

Long-term vision:

- A source-backed investment cockpit with data provenance, deterministic calculations, AI explanation, cross-market data support, evidence trails, and decision workflows.

Current implementation:

- A strong local backend foundation with many implemented modules.
- A usable but uneven frontend.
- A valuation engine that is more mature than the rest of the intelligence workflow.
- A data ingestion layer that works for selected sources, not a universal data platform.

## 3. End-to-End User Workflow

### Step 1: User creates or selects a company

What the user does:

- Adds a company with ticker, market, exchange, currency, and optional regulatory identifiers.

What the system does:

- Normalizes US/India market identity.
- Prevents duplicate company identity by market, exchange, and local symbol.
- Can look up SEC CIKs for US companies.

Automated:

- Basic normalization.
- SEC CIK lookup for US tickers.

Requires user input:

- Correct market, exchange, local symbol, and currency.
- India identifiers are manual today.

Output:

- A persisted `Company` record.

What can go wrong:

- India lookup is a stub.
- Tickers can be ambiguous across exchanges.
- Missing currency or exchange metadata reduces downstream trust.

### Step 2: User configures data sources

What the user does:

- Adds RSS sources, SEC source records, manual filing links, or provider credentials in `.env`.

What the system does:

- Stores source records and source capability metadata.
- Reads provider keys from environment where supported.

Automated:

- Source CRUD.
- Source capability matrix endpoints.

Requires user input:

- RSS URLs.
- `SEC_USER_AGENT`.
- Optional API keys such as `FRED_API_KEY`, `ALPHA_VANTAGE_API_KEY`, `FINNHUB_API_KEY`, `NEWS_API_KEY`, `GEMINI_API_KEY`.

Output:

- Configured source records and provider readiness.

What can go wrong:

- API key missing.
- RSS URL invalid.
- SEC user agent missing or invalid.
- Provider coverage may not match the company market.

### Step 3: User ingests documents or data

What the user does:

- Runs RSS ingestion, SEC filing ingestion, FRED ingestion, market-data ingestion, CSV import, or manual filing upload/link.

What the system does:

- Stores raw documents or observations.
- Records processing runs.
- Deduplicates some document ingestion by content/source.
- Runs post-ingestion event, narrative, and alert pipelines where wired.

Automated:

- RSS XML/feed ingestion.
- Active RSS batch ingestion.
- Recent SEC filing metadata/text ingestion for configured US companies.
- FRED series ingestion if key is configured.
- Market-data ingestion through configured provider.
- Processing run logging.

Requires user input:

- Triggering ingestion.
- Source/company mapping.
- Manual filing entry for India.
- Provider keys.

Output:

- Raw documents, events, alerts, processing runs, macro observations, prices, or imported records.

What can go wrong:

- External API failure.
- Duplicate data.
- Bad CSV rows.
- RSS content quality problems.
- India automated filings are not available.
- Post-ingestion intelligence is only as good as the source text and extraction rules.

### Step 4: System extracts events and alerts

What the system does:

- Converts raw documents into event records.
- Scores events by credibility, novelty, impact, and priority.
- Creates alerts when priority crosses threshold.
- Tracks bounded claim context and safe raw-document/source links where available.

Automated:

- Event extraction from raw documents.
- Alert generation after ingestion or manual processing.

Requires user input:

- Review alerts.
- Tune scoring config.
- Confirm whether events matter to the thesis.

Output:

- Events, alerts, evidence fields, and daily-brief inputs.

What can go wrong:

- Extraction is rule-based and may miss nuance.
- Score weights may be wrong for a user’s strategy.
- Alerts are not investment advice.

### Step 5: User manages thesis and evidence

What the user does:

- Writes thesis notes, assumptions, changes, evidence records, decisions, and variant perception entries.

What the system does:

- Stores those records and links them to companies where supported.
- Can track thesis changes and decision context.

Automated:

- Persistence and retrieval.

Requires user input:

- Actual thesis logic, assumptions, confidence, and review.

Output:

- Thesis notes, assumption records, evidence ledger entries, decisions.

What can go wrong:

- Alert review has a document-level evidence drawer and alert detail route.
  Exact page/section/span highlighting is not available yet.
- Poorly structured user notes reduce downstream value.

### Step 6: User runs valuation

What the user does:

- Creates a valuation model.
- Enters assumptions or uses benchmark priors where available.
- Runs DCF, scenario, sensitivity, reverse DCF, relative valuation, WACC, macro sensitivity, or real-options analysis.

What the system does:

- Calculates deterministic outputs.
- Stores assumptions, projections, outputs, sensitivity tables, diagnostics, and change logs.
- Can use Damodaran benchmark data if imported.

Automated:

- FCFF DCF math.
- Terminal value and equity bridge.
- Sensitivity table generation.
- Reverse DCF solving.
- Diagnostics and warnings.
- Industry-prior lookup after user-selected industry/country.

Requires user input:

- Correct assumptions.
- Correct company/industry mapping.
- Market price and share-count validation.
- Review of warnings.

Output:

- Forecast, valuation output, sensitivity tables, diagnostics, implied assumptions, memos.

What can go wrong:

- Wrong assumptions produce wrong valuations.
- Industry mapping is fragile.
- Benchmark priors are not company facts.
- AI memo text may overstate confidence if not constrained.

### Step 7: User reviews portfolio impact

What the user does:

- Enters portfolios, holdings, transactions, cash balances, and market prices.

What the system does:

- Calculates portfolio analytics, exposure, top positions, concentration warnings, and valuation context where data exists.

Automated:

- Portfolio value and position calculations from entered data.
- CSV interchange returns real files, formula escapes text, scopes portfolio
  rows to the current user, supports preview/apply, and rolls transaction
  batches back atomically. CSV remains interchange; separate database/document
  backup scripts pass a destructive isolated restore drill.

Requires user input:

- Holdings, transactions, cash, market prices, currencies.

Output:

- Portfolio dashboard, analytics, exposure metrics.

What can go wrong:

- Prices may be stale or manual.
- Currency normalization is still basic.
- Broker sync is not built.

### Step 8: User reads dashboard, daily brief, research pages, and AI outputs

What the user does:

- Reviews overview, alerts, events, daily brief, documents, research sessions, narratives, social sentiment, valuation memos, and data health.

What the system does:

- Displays backend records and data-state indicators.
- Uses AI provider where configured for selected summaries/memos.

Automated:

- Fetching and rendering.
- Some daily brief generation.
- AI memo generation when requested.

Requires user input:

- Interpretation and approval.
- Any serious investment decision.

Output:

- Dashboard panels, tables, brief text, memos, summaries, alerts.

What can go wrong:

- Some UI surfaces are prototypes.
- Some docs are stale.
- AI output is mock only in tests or explicit demo mode. Missing provider
  configuration is a visible failure.

## 4. Current Capabilities

### Company Intake

Status: Working core; transfer controls are broken

What it does:

- Creates, lists, updates, and deletes companies.
- Normalizes market identity for US and India.
- Supports ticker, market, exchange, local symbol, currency, country, CIK, ISIN, FIGI, regulatory ID, and exposure tags.
- Blocks duplicate market/exchange/local-symbol identities.

Inputs required:

- Ticker or local symbol.
- Market, exchange, currency, and country for best results.

Outputs produced:

- Company records.
- SEC CIK lookup result where available.

Important files:

- `backend/app/api/routers/companies.py`
- `backend/app/models/company.py`
- `backend/app/services/company_lookup.py`
- `backend/app/providers/company_lookup/`
- `frontend/app/companies/page.tsx`
- `frontend/components/add-company-form.tsx`

Limitations:

- India company lookup provider is a stub.
- Identity handling is better than before, but downstream pages may still rely on legacy ticker assumptions.

Confidence level: High

### Company Setup Workflow

Status: Working foundation

What it does:

- Creates a company-specific setup checklist.
- Tracks identity, source setup, filing, financial extraction, industry mapping, valuation readiness, and local-only security status.
- Shows US source readiness for SEC EDGAR and SEC company facts.
- Shows India source readiness as manual-only for filings and financial statements.
- Lets the user confirm company identity and update workflow steps from `/companies/[id]/setup`.
- Links setup into `/companies/[id]/filings` when filings still need review.

Inputs required:

- Existing company record.
- User confirmation of identity.
- User updates as filings, financial metrics, industry mapping, and valuation readiness progress.

Outputs produced:

- `CompanySetupWorkflow` state and source-readiness rows.

Important files:

- `backend/app/models/company_setup.py`
- `backend/app/services/company_setup.py`
- `backend/app/api/routers/company_setup.py`
- `backend/tests/test_company_setup_workflow.py`
- `frontend/app/companies/[id]/setup/page.tsx`
- `frontend/app/companies/[id]/filings/page.tsx`

Limitations:

- This is a workflow tracker and readiness surface.
- It does not extract statements, normalize metrics, or auto-fill valuation assumptions.
- India remains manual-only.

Confidence level: High

### Source Configuration

Status: Working

What it does:

- Stores sources.
- Tracks source capability metadata for market/source combinations.
- Supports RSS and SEC-oriented workflows.

Inputs required:

- Source name, type, base URL, and active status.

Outputs produced:

- Source records and source capability matrix.

Important files:

- `backend/app/api/routers/sources.py`
- `backend/app/api/routers/source_capabilities.py`
- `backend/app/models/source.py`
- `backend/app/models/source_capability.py`
- `frontend/app/sources/page.tsx`
- `frontend/components/source-capability-matrix.tsx`

Limitations:

- Capability metadata is not the same as live provider reliability.
- Some future sources are represented by metadata before full provider automation exists.

Confidence level: High

### Provider Health

Status: Working foundation

What it does:

- Reports provider readiness for SEC EDGAR, RSS feeds, FRED, market data, AI, OpenFIGI, Damodaran benchmarks, and India manual filings.
- Uses environment configuration to identify missing keys.
- Uses `processing_runs` history to show last success, last failure, failure reason, and freshness where available.
- Displays provider health on the Data Health page.

Inputs required:

- Environment variables for provider keys.
- Processing run history for live success/failure evidence.
- Damodaran imports and active RSS sources where applicable.

Outputs produced:

- Provider health records with status, configured flag, last success/failure, freshness label, notes, and action required.

Important files:

- `backend/app/services/provider_health.py`
- `backend/app/api/routers/providers.py`
- `backend/tests/test_provider_health.py`
- `frontend/app/data-health/page.tsx`
- `frontend/lib/api.ts`

Limitations:

- This is a computed health foundation, not a full active provider ping system.
- It does not yet perform live external health checks or store dedicated provider-health rows.

Confidence level: High

### Financial Statement Ingestion

Status: Working assistive foundation; citation/evaluation incomplete

What it does:

- Stores financial periods and financial metrics.
- Provides fundamentals trend endpoints.
- Can ingest company fundamentals through backend services.
- Has SEC parsing models and services.
- Extracts first-pass reviewable financial metric candidates from stored filing `raw_text`.
- Tracks source filing, source text, line number, explicit page/section markers, extraction warning codes, extraction method, confidence label, unit, and review status for extracted candidates.
- Accepts authenticated PDF filings up to 40MB/1,000 pages, stores the original
  in a one-to-one binary asset, and records an optional official source URL.
  Full scans stop at 500 pages; at most 75 explicit target pages support long
  reports. It extracts text-based tables and statement rows with fiscal-year
  headers and preserves page/row/cell evidence plus bounding boxes where available.
- Streams original PDF evidence only through an authenticated, no-store route;
  normal metadata responses omit binary content.
- Requires a reporting unit before review/override and blocks conflicting reviewed currencies before promotion.
- Accepts traced Screener `.xlsx` uploads with size/type checks, content hashing, duplicate rejection, temporary-file cleanup, and processing-run status.
- Reports normalized period coverage, trust readiness, stale/missing snapshots, low-confidence currency, and conflicts before and after backfill.
- Updates setup state to financial review after extraction.

Inputs required:

- Company.
- Financial periods and metrics, or provider-backed ingestion request.
- Filing document with reviewed `raw_text` for candidate extraction.

Outputs produced:

- Financial periods, metrics, trend data.
- Financial extraction candidates awaiting review.

Important files:

- `backend/app/api/routers/fundamentals.py`
- `backend/app/services/fundamentals.py`
- `backend/app/services/financial_extraction.py`
- `backend/app/models/financial.py`
- `backend/app/models/sec_parsing.py`
- `backend/app/services/sec_parsing.py`
- `backend/tests/test_financial_extraction_workflow.py`
- `frontend/app/companies/[id]/fundamentals/page.tsx`
- `frontend/app/companies/[id]/filings/page.tsx`
- `frontend/components/financial-trends.tsx`

Limitations:

- This is not yet a fully automated, audited financial statement ingestion workflow.
- Text extraction is regex-based and PDF extraction is a deterministic targeted
  statement-row/table pass. The APSEZ profile supports INR crore/lakh units,
  attribution rows, NCI, associates, leases, and reported debt sums; it refuses
  to invent operating EBIT.
- PDF OCR, password-protected/scanned files, arbitrary merged layouts, tables
  without explicit fiscal-year headers, subtotal validation, and full statement
  coverage are unsupported.
- Reviewed/overridden candidates can be promoted into legacy financial metrics and normalized financial snapshots. Reporting-currency source/confidence is persisted, and eligible older periods can be dry-run/backfilled with measurable coverage and source reconciliation. Promoted candidates remain stored for audit lookup but leave the active review queue. Text, PDF, Screener, and XBRL candidates preserve source-specific locators, but comparative-total checks and full statement coverage remain incomplete.
- Users must review extracted financial data before using it for valuation.

Confidence level: Medium

### Filing Acquisition Workflow

Status: Working foundation

What it does:

- Discovers US filing candidates through SEC EDGAR when a company has a CIK.
- Returns an explicit manual-only filing state for India companies.
- Stores reviewed manual filing links or text as traceable raw documents.
- Lists stored company filing documents.
- Advances company setup filing status to `needs_review` after a manual filing source is added.

Inputs required:

- Existing company record.
- US CIK for automated SEC discovery.
- Manual filing title, document type, optional URL, optional publication date, and optional reviewed text for manual filing capture.

Outputs produced:

- Filing discovery response with provider, mode, candidates, and next action.
- Raw document records for manual filings.
- Updated setup workflow state when a manual filing is added.

Important files:

- `backend/app/services/filing_acquisition.py`
- `backend/app/api/routers/filing_acquisition.py`
- `backend/tests/test_filing_acquisition_workflow.py`
- `frontend/app/companies/[id]/filings/page.tsx`
- `frontend/app/actions.ts`

Limitations:

- The dedicated filing-discovery page and company-detail SEC picker remain
  separate paths. The company-detail picker now imports a selected SEC filing
  into raw documents; consolidating the duplicate discovery surfaces remains a
  UX improvement.
- Financial extraction is a separate first-pass candidate workflow and still requires reviewed filing text.
- India remains manual-only until a real filings provider is selected and implemented.

Confidence level: High

### SEC Filing Ingestion

Status: Working for configured US companies

What it does:

- Looks up SEC CIKs.
- Previews recent filings.
- Provides metadata candidates to the filing acquisition workflow.
- Ingests SEC filing metadata and optionally filing text.
- Stores raw documents.
- Runs downstream event/alert pipeline.

Inputs required:

- US company with CIK.
- Valid `SEC_USER_AGENT`.

An SEC source id is optional. The ingestion service validates a supplied source,
otherwise resolves an active SEC source or creates the local `SEC EDGAR` source
record.

Outputs produced:

- Raw documents, processing runs, events, alerts.

Important files:

- `backend/app/services/sec_ingestion.py`
- `backend/app/providers/filings/sec_edgar.py`
- `backend/app/services/filing_acquisition.py`
- `backend/app/api/routers/filing_acquisition.py`
- `backend/app/api/routers/companies.py`
- `backend/app/api/routers/ingestion.py`
- `backend/tests/test_filing_acquisition_workflow.py`
- `backend/tests/test_api_sec_ingestion.py`
- `backend/tests/test_sec_ingestion.py`

Limitations:

- SEC coverage is US-focused.
- External availability and SEC rate limits still matter.
- Filing text extraction is not the same as full financial statement normalization.

Confidence level: High

### India Filing Support

Status: Partially Working

What it does:

- Routes India companies to a manual filing provider.
- Allows manual filing upload/link using allowed Indian document types.
- Shows manual-only discovery state on `/companies/[id]/filings`.
- Stores India market identity and currency fields.

Inputs required:

- Manual filing metadata, URL, or raw text.

Outputs produced:

- Raw document records that can feed downstream pipelines.

Important files:

- `backend/app/providers/filings/india_manual.py`
- `backend/app/providers/filings/base.py`
- `backend/app/services/filing_acquisition.py`
- `backend/app/services/filing_manual.py`
- `backend/app/api/routers/filing_acquisition.py`
- `backend/app/api/routers/companies.py`
- `frontend/app/companies/[id]/filings/page.tsx`

Limitations:

- Automated India filing provider is not configured.
- NSE/BSE company lookup is a stub.
- Users must manually provide Indian filings today.

Confidence level: High

### RSS and News Ingestion

Status: Working

What it does:

- Ingests RSS XML or live RSS feed URLs.
- Supports active-source batch ingestion.
- Deduplicates raw documents.
- Runs post-ingestion event, narrative, and alert pipeline.

Inputs required:

- RSS source.
- Company mapping for targeted ingestion, or active source configuration for batch ingestion.

Outputs produced:

- Raw documents, processing runs, events, alerts, narrative extraction results.

Important files:

- `backend/app/services/rss_ingestion.py`
- `backend/app/api/routers/ingestion.py`
- `backend/tests/test_api_rss_ingestion.py`
- `backend/tests/test_rss_ingestion.py`

Limitations:

- RSS quality varies.
- Company matching is not a complete entity-resolution engine.
- Imported content is untrusted.

Confidence level: High

### Raw Documents and Document Sections

Status: Working

What it does:

- Stores raw source documents.
- Parses selected document sections.
- Computes section diffs.
- Supports document-level AI outputs and summaries.

Inputs required:

- Raw document content, source metadata, and company/source linkage.

Outputs produced:

- Raw document records, sections, diffs, AI outputs.

Important files:

- `backend/app/api/routers/raw_documents.py`
- `backend/app/models/raw_document.py`
- `backend/app/models/document_section.py`
- `frontend/app/documents/page.tsx`
- `frontend/app/documents/[id]/sections/page.tsx`
- `frontend/app/documents/[id]/ai/page.tsx`

Limitations:

- AI summaries require review.
- Section parsing quality depends on source format.

Confidence level: Medium

### Event Extraction

Status: Working

What it does:

- Extracts events from raw documents.
- Creates event records with classification, scores, and evidence fields.
- Supports corroboration and contradiction links.

Inputs required:

- Raw documents.

Outputs produced:

- Event records.

Important files:

- `backend/app/services/event_extraction.py`
- `backend/app/api/routers/events.py`
- `backend/app/api/routers/manual_processing.py`
- `backend/tests/test_event_extraction.py`
- `frontend/app/events/page.tsx`
- `frontend/components/events-timeline.tsx`

Limitations:

- Extraction is not a general human-level document understanding system.
- False negatives and shallow classifications are possible.

Confidence level: High

### Scoring Framework

Status: Working for event-level scoring, partially expanded elsewhere

What it does:

- Scores events by credibility, novelty, impact, and priority.
- Provides scoring config.
- Supports score explanation components in the frontend.

Inputs required:

- Event data and scoring weights.

Outputs produced:

- Scores, priority levels, alert decisions, explanations.

Important files:

- `backend/app/services/scoring.py`
- `backend/app/api/routers/scoring_config.py`
- `backend/tests/test_scoring.py`
- `frontend/components/score-breakdown.tsx`
- `frontend/components/score-explanation.tsx`

Limitations:

- Entity-level and portfolio-level scoring are not as mature as event-level scoring.
- Score weights still need product calibration.

Confidence level: Medium

### Alerts

Status: Working

What it does:

- Creates alerts from high-priority events.
- Supports alert CRUD and review status updates.
- Displays alert panels in the frontend.

Inputs required:

- Events and scoring configuration.

Outputs produced:

- Alerts with status, priority, evidence, and review fields.

Important files:

- `backend/app/services/alert_generation.py`
- `backend/app/api/routers/alerts.py`
- `backend/tests/test_alert_generation.py`
- `backend/tests/test_api_alert_generation.py`
- `backend/tests/test_api_alert_review.py`
- `frontend/app/alerts/page.tsx`
- `frontend/components/alerts-panel.tsx`

Limitations:

- Alert quality depends on event extraction and score configuration.
- Alerts are not investment recommendations.

Confidence level: High

### Daily Brief

Status: Working

What it does:

- Generates and stores daily brief data from events and alerts.
- Provides current and historical brief endpoints.
- Displays brief panel on dashboard.

Inputs required:

- Existing events and alerts.

Outputs produced:

- Daily brief record.

Important files:

- `backend/app/api/routers/daily_brief.py`
- `backend/app/services/daily_brief.py`
- `backend/tests/test_api_daily_brief.py`
- `backend/tests/test_daily_brief.py`
- `backend/tests/test_persisted_daily_brief.py`
- `frontend/app/daily-brief/page.tsx`
- `frontend/components/daily-brief-panel.tsx`

Limitations:

- Brief quality depends on underlying event/alert quality.

Confidence level: High

### Thesis Notes and Assumptions

Status: Working

What it does:

- Stores thesis notes, assumptions, and thesis changes.
- Supports drift-related fields.

Inputs required:

- User-written thesis notes and assumption details.

Outputs produced:

- Thesis note, assumption, and change records.

Important files:

- `backend/app/api/routers/thesis_notes.py`
- `backend/app/models/thesis.py`
- `backend/tests/test_thesis_alerts.py`
- `frontend/app/thesis-notes/page.tsx`
- `frontend/app/thesis-notes/[id]/page.tsx`
- `frontend/app/companies/[id]/thesis/page.tsx`

Limitations:

- Thesis quality is manual.
- Evidence linkage exists but still needs stronger UX.

Confidence level: High

### Portfolio Tracking

Status: Working

What it does:

- Stores portfolios, holdings, transactions, cash balances, and snapshots.
- Computes analytics and top positions.
- Exposes CSV import/export controls, but the current export implementation
  returns HTTP 500 and transfer routes are not yet safe as a user-scoped backup.
- Enforces current-user ownership on portfolio parents and child resources.
- Keeps aggregate value, P&L, and weights unavailable when an active holding has
  no market price, rather than treating missing data as zero.
- Separates opening holdings, security activity, and cash activity in the
  management UI.

Inputs required:

- Holdings, transactions, cash balances, market prices.

Outputs produced:

- Portfolio analytics, positions, exposure, snapshots.

Important files:

- `backend/app/api/routers/portfolios.py`
- `backend/app/services/portfolio_analytics.py`
- `backend/app/services/portfolio_valuation.py`
- `backend/app/models/portfolio.py`
- `backend/tests/test_api_portfolios.py`
- `backend/tests/test_portfolio_analytics.py`
- `backend/tests/test_portfolio_cash.py`
- `backend/tests/test_portfolio_valuation.py`
- `frontend/app/portfolio/page.tsx`
- `frontend/app/portfolio/manage/page.tsx`
- `frontend/components/portfolio-analytics.tsx`

Limitations:

- No broker sync.
- Prices may be manual or stale.
- Currency conversion needs more complete provider support.

Confidence level: High

### Manual Market Prices and Market Data

Status: Partially Working

What it does:

- Stores market prices.
- Serves current quotes and price history from stored data.
- Can ingest provider data through Alpha Vantage/FMP-style provider abstraction.
- Tracks market-data ingestion runs.

Inputs required:

- Manual price records or provider API key.
- Company market identity.

Outputs produced:

- Market prices, quote records, history records.

Important files:

- `backend/app/api/routers/market.py`
- `backend/app/api/routers/market_prices.py`
- `backend/app/services/market_data/`
- `backend/app/models/market_price.py`
- `frontend/app/market-prices/page.tsx`

Limitations:

- Provider-backed coverage is not yet validated as a complete US/India layer.
- External API behavior is not guaranteed.
- No real-time feed.

Confidence level: Medium

### Market Regime

Status: Planned / UI prototype

What it does:

- The frontend has a market regime page showing entry timing, liquidity, volatility, breadth, and positioning concepts.

Inputs required:

- None today for the prototype page.

Outputs produced:

- Simulated UI values.

Important files:

- `frontend/app/portfolio/regime/page.tsx`
- `docs/roadmaps/market-intelligence-build-roadmap.md`

Limitations:

- The page explicitly shows mock data.
- Backend market-regime scoring is not a trusted live engine yet.

Confidence level: High

### Valuation Engine

Status: Working

What it does:

- Creates valuation models and assumption sets.
- Runs FCFF DCF.
- Produces forecasts, terminal value, equity bridge, sensitivity tables, scenarios, diagnostics, and reverse DCF.
- Supports FCFE/DDM, lifecycle calculations, WACC, macro sensitivity, relative valuation, accounting normalization, real options, and regression priors through additional services/routes.

Inputs required:

- Company.
- Assumptions including revenue, margins, tax, sales-to-capital, WACC, terminal growth, cash, debt, shares, and market price.

Outputs produced:

- Valuation outputs, projection years, sensitivity tables, diagnostics, reverse DCF results, scenario outputs.

Important files:

- `backend/app/services/dcf.py`
- `backend/app/services/diagnostics_engine.py`
- `backend/app/services/reverse_dcf_engine.py`
- `backend/app/services/wacc_engine.py`
- `backend/app/services/relative_valuation.py`
- `backend/app/services/macro_sensitivity_service.py`
- `backend/app/services/real_options_service.py`
- `backend/app/api/routers/valuations.py`
- `backend/app/api/routers/wacc.py`
- `backend/app/api/routers/relative_valuation.py`
- `backend/app/api/routers/real_options.py`
- `frontend/app/valuation/page.tsx`
- `frontend/app/valuation/quick/page.tsx`
- `frontend/app/companies/[id]/valuation/page.tsx`
- `frontend/components/valuation/`

Limitations:

- Output quality depends heavily on user assumptions.
- Industry priors are not company facts.
- Some diagnostic comparisons use imperfect proxies.
- AI memo output must remain explanatory, not advisory.

Confidence level: High

### Industry Benchmark Lookup

Status: Partially Working

What it does:

- Imports Damodaran workbooks.
- Stores benchmark datasets.
- Suggests industries.
- Provides assumption priors by country and industry.
- Reports all 35 runtime-mirror sources through Data Health with canonical
  provenance, source presence, implementation state, typed-row counts,
  freshness, supported/missing metrics, active dataset-version provenance,
  runtime-mirror hash agreement, limitations, and corrective actions.
- Preserves hash-idempotent Capex, ROE, Margin, Working Capital, Dividend, FCFE,
  and Volatility source versions and reads only active linked versions.
- Imports 94 exact `roeIndia.xls` industry rows with firm count, unadjusted ROE,
  and R&D-adjusted ROE.
- Requires exact source headers for Margin, Working Capital, Dividend, and FCFE.
  Margin uses pre-tax unadjusted operating margin. FCFE preserves aggregate
  before-debt and after-debt values and leaves unsupported component fields null.
- Imports 94 exact `optvarIndia.xls` rows plus both source assumptions. The
  canonical real-options API exposes active source provenance, preserves
  zero/null cells, and returns not-found instead of a generic fallback.

Inputs required:

- Uploaded Damodaran files or seeded datasets.
- User-selected country and industry.

Outputs produced:

- Benchmark rows, industry candidates, assumption priors.

Important files:

- `backend/app/api/routers/admin_damodaran.py`
- `backend/app/services/damodaran_parser.py`
- `backend/app/services/damodaran_ingestion.py`
- `backend/app/services/damodaran_coverage.py`
- `backend/app/services/industry_mapping.py`
- `backend/app/services/industry_assumption.py`
- `scripts/ingest_damodaran.py`
- `frontend/app/admin/damodaran/page.tsx`
- `frontend/app/data-health/page.tsx`

Limitations:

- Industry suggestion is simple and can fall back poorly.
- User confirmation is required.
- Admin benchmark comparison endpoint still returns mock comparison data.
- 14 of 35 mirrored sources currently have typed rows. The strict support
  assessment is 9 supported, 13 partial, and 13 unsupported. `ratings.xls` is
  service-backed rather than database-ingested: all 45 source rows are in a
  hash-versioned catalog with exact boundary tests and API provenance.
- Generic workbook parsing stores metadata and sheet summaries, not usable
  typed benchmark rows.
- Capex, ROE, Margin, Working Capital, Dividend, FCFE, Volatility, PE, PBV, PS,
  EV/EBITDA, and Country Statistics preserve source hash, source
  date/confidence, active/superseded state, and typed row count. Historical
  macro datasets use a separate historical contract.
- ROE is an accounting-return prior, not ROC or terminal ROIC. The source does
  not populate those fields.

Confidence level: Medium

### Relative Valuation

Status: Working

What it does:

- Provides countries, industries, industry stats, and relative valuation run endpoint.
- Assembles PE, PBV, PS, and EV multiples only from their active independent
  source versions and exposes method-specific provenance.

Inputs required:

- Company/industry/country data and selected peer/benchmark assumptions.

Outputs produced:

- Relative valuation outputs.

Important files:

- `backend/app/api/routers/relative_valuation.py`
- `backend/app/services/relative_valuation.py`
- `backend/tests/test_valuation_cases.py`
- `frontend/components/valuation/relative-valuation-panel.tsx`

Limitations:

- Needs trustworthy benchmark data.
- Peer/industry selection still needs user review.
- It is an industry-multiple cross-check, not a reviewed comparable-company set.

Confidence level: Medium

### Macro and Country Context

Status: Partially Working

What it does:

- Stores macro series and observations.
- Supports FRED ingestion if configured.
- Supports country market context and risk-free rate lookup.
- Supports macro-to-valuation scenario translation.

Inputs required:

- Macro series definitions, observations, country context, API key where needed.

Outputs produced:

- Macro observations, valuation context, scenario adjustments.

Important files:

- `backend/app/api/routers/macro.py`
- `backend/app/api/routers/macro_valuation.py`
- `backend/app/api/routers/country_market.py`
- `backend/app/services/macro_ingestion.py`
- `backend/app/services/macro_context.py`
- `backend/app/services/macro_scenario_translation.py`
- `frontend/app/macro/page.tsx`
- `frontend/components/macro/`

Limitations:

- Macro data coverage depends on configured sources.
- India macro/provider coverage is not complete.

Confidence level: Medium

### AI Memo Generation

Status: Partially Working

What it does:

- Generates valuation memos from company, valuation, assumptions, and DCF output.
- Stores owned AI outputs with provider/model identity, SHA-256 input hash,
  source scope, explicit mock/transmission state, privacy version, limitations,
  confidence, review metadata, and safe failure state.
- Uses mock only in tests or explicit `AI_DEMO_MODE`. Missing configuration and
  provider failures do not fall back.

Inputs required:

- Completed valuation output.
- AI provider key if real generation is desired.

Outputs produced:

- Markdown memo and stored `AiOutput` record.

Important files:

- `backend/app/api/routers/ai.py`
- `backend/app/services/memo_writer.py`
- `backend/app/providers/ai_provider.py`
- `backend/app/providers/mock_provider.py`
- `backend/app/models/ai.py`
- `frontend/components/valuation/valuation-memo-panel.tsx`

Limitations:

- AI must not be used to invent data or perform unsupported finance math.
- Production prompts prohibit buy/sell recommendations.
- Users must review and approve AI output.

Confidence level: Medium

### Narrative-to-Numbers

Status: Partially Working

What it does:

- Maps user narrative text to suggested DCF assumption changes.
- Uses current assumptions and company context.

Inputs required:

- Narrative text.
- Existing valuation model and scenario.

Outputs produced:

- Suggested margin, growth, sales-to-capital, and terminal-growth assumptions with reasons.

Important files:

- `backend/app/api/routers/ai.py`
- `backend/app/services/narrative_to_numbers.py`
- `frontend/components/valuation/narrative-to-numbers-panel.tsx`

Limitations:

- Suggestions must not be auto-applied without review.
- AI-generated assumptions can be wrong.

Confidence level: Medium

### Research Sessions

Status: Owned AI/privacy foundation; source-grounding still partial

What it does:

- Stores research sessions and messages.
- Persists the authenticated user on creation.
- Resolves list, read, message, and delete operations through the current-user
  parent.
- Rejects caller-created assistant messages.

Inputs required:

- User-created session and messages.

Outputs produced:

- Persisted research conversation/message records.

Important files:

- `backend/app/api/routers/research.py`
- `backend/app/models/research.py`
- `frontend/app/research/page.tsx`
- `frontend/app/research/sessions/page.tsx`
- `frontend/app/research/sessions/[id]/page.tsx`

Limitations:

- This is not yet a fully source-grounded autonomous research agent.
- The synchronous AI call uses the unified provider/mock/privacy/source/review
  contract. Exact declared-source citation checks and a deterministic evaluation
  corpus exist, but providers do not yet generate complete citations and
  retrieval grounding remains incomplete.
- Broad `any` and optimistic behavior still need reduction. Known production
  blocking browser dialogs are removed, and covered failures preserve inline
  state.

Confidence level: High for ownership; Low for source-grounded AI behavior

### Narratives and Social Sentiment

Status: Working data model and CRUD, partially automated extraction

What it does:

- Stores narrative clusters, claims, mentions, social posts, and sentiment scores.
- Provides narrative extraction endpoint.

Inputs required:

- Source documents, social posts, or user-entered data.

Outputs produced:

- Narrative and sentiment records.

Important files:

- `backend/app/api/routers/narratives.py`
- `backend/app/api/routers/social.py`
- `backend/app/services/narrative_extraction.py`
- `backend/app/models/narrative.py`
- `backend/app/models/social.py`
- `frontend/app/narratives/page.tsx`
- `frontend/app/social/page.tsx`

Limitations:

- Social ingestion is not a live official-platform integration.
- Avoid scraping.
- AI/narrative interpretation requires provenance and review.

Confidence level: Medium

### Evidence, Decisions, and Variant Perception

Status: Working foundation

What it does:

- Stores evidence entries, decisions, and variant perception records.
- Provides company-level frontend pages for evidence and decisions.

Inputs required:

- User-entered or linked evidence and decision details.

Outputs produced:

- Evidence, decision, and variant perception records.

Important files:

- `backend/app/api/routers/evidence.py`
- `backend/app/api/routers/decisions.py`
- `backend/app/api/routers/variant_perception.py`
- `backend/app/models/evidence.py`
- `backend/app/models/decision.py`
- `backend/app/models/variant_perception.py`
- `frontend/app/companies/[id]/evidence/page.tsx`
- `frontend/app/companies/[id]/decisions/page.tsx`

Limitations:

- Alert/event traceability stops at the document unless a downstream financial
  candidate owns a more precise locator.
- Exact passage highlighting, contradiction review, and the broader evidence
  ledger workflow still need sharpening.

Confidence level: Medium

### Data Import and Export

Status: Partially Working

What it does:

- Exports selected portfolio, market price, raw document, and event data to CSV.
- Imports market prices, portfolio transactions, and holdings with row-level
  validation, file/row limits, preview/apply, duplicate checks, and owned
  portfolio resolution.
- Escapes CSV formula injection on export.
- Applies portfolio transaction batches atomically.

Inputs required:

- CSV files in expected schemas.

Outputs produced:

- Imported records or CSV data.

Important files:

- `backend/app/api/routers/data_transfer.py`
- `backend/app/services/data_transfer.py`
- `backend/app/core/security.py`
- `frontend/components/csv-importer.tsx`
- `frontend/components/csv-upload-form.tsx`

Limitations:

- Import validation is practical but not comprehensive financial audit logic.
- Invalid CSV preview and blocked-apply recovery pass in the browser; download
  and valid apply coverage remain.
- CSV is not the backup mechanism. Separate PostgreSQL/document backup and
  restore scripts pass an isolated destructive drill with checksums and exact
  document-byte verification.

Confidence level: High for tested manual interchange; Low as a backup

### Authentication and Security

Status: Not production-ready

What it does:

- Provides a configured local credential login backed by a NextAuth JWT session.
- Redirects unsigned frontend page requests to sign-in.
- Exposes non-secret local configuration readiness and disables sign-in until the required variables are present.
- Enforces validated-session ownership on selected protected backend routes.
- Includes CSV formula escaping.
- Includes security docs and tests for some basic controls.
- Has OAuth token storage routes/models, but this does not mean broker sync is production-safe.

Inputs required:

- Local environment configuration.

Outputs produced:

- Local app access and selected security controls.

Important files:

- `docs/06-security-threat-model.md`
- `backend/app/core/security.py`
- `backend/app/api/routers/oauth.py`
- `backend/app/models/oauth.py`
- `backend/tests/test_security.py`
- `frontend/app/api/auth/readiness/route.ts`
- `frontend/proxy.ts`
- `.env.example`

Limitations:

- FastAPI protects the aggregate router by default; only the two health routes
  are public application operations, and an automated inventory verifies the
  dependency.
- This is single-user local access control, not a reviewed public-deployment identity system.
- It does not provide team roles, production session governance, HTTPS termination, CSRF deployment review, or an audit-log policy.
- No production identity provider, role model, or team authentication.
- No authorization model beyond the current session ownership checks.
- No public deployment model.
- No rate limiting or hardened CORS model for production.
- No approved broker credential design.

Confidence level: High

### UI and Dashboard

Status: Partially Working

What it does:

- Provides dashboard, companies, sources, data ingestion, documents, events, alerts, daily brief, portfolio, valuation, macro, research, social, narratives, settings, admin Damodaran, and data-health routes.
- Supports API envelope parsing and fallback legacy response parsing.
- Provides loading, empty, error, stale, partial, not configured, freshness, and mock-data UI components.

Inputs required:

- Backend API availability and persisted data.

Outputs produced:

- Tables, panels, workflows, forms, and dashboards.

Important files:

- `frontend/app/`
- `frontend/components/`
- `frontend/lib/api.ts`
- `frontend/components/ui/data-states.tsx`
- `frontend/lib/data-state-meta.ts`

Limitations:

- Not every page has been audited for trust labels and endpoint parity.
- Market regime page is explicitly mock.
- Some pages may show sparse records rather than full workflows.

Confidence level: Medium

### API and Backend

Status: Working

What it does:

- Provides a large FastAPI route set around companies, sources, ingestion, documents, events, alerts, thesis, portfolio, valuation, macro, research, evidence, decisions, narratives, social, import/export, admin benchmarks, and AI.
- Uses `ApiResponse` envelope for many routes.
- Has database-backed CRUD and service layers.

Inputs required:

- Valid request payloads and a running Postgres database.

Outputs produced:

- JSON API responses, database records, calculated outputs.

Important files:

- `backend/app/main.py`
- `backend/app/api/routes.py`
- `backend/app/api/routers/`
- `backend/app/api/schemas.py`
- `backend/app/services/`
- `backend/app/models/`

Limitations:

- Some older routes include `/api/...` in router paths while others rely on app-level prefixing/proxy behavior. This should be normalized carefully, not by broad rewrite.
- Error handling is decent but not uniform across every route.

Confidence level: High

### Database

Status: Working

What it does:

- Stores companies, sources, raw documents, events, alerts, thesis notes, processing runs, portfolios, market prices, valuation objects, Damodaran datasets, macro data, AI outputs, narratives, social records, research records, evidence, decisions, and more.

Inputs required:

- Alembic migrations and Postgres.

Outputs produced:

- Persistent local application state.

Important files:

- `backend/app/models/`
- `backend/alembic/versions/`
- `docs/03-database-schema.md`
- `backend/tests/test_alembic.py`
- `backend/tests/test_models.py`

Limitations:

- Some schema areas are ahead of product maturity.
- Long-term audit trail/versioning is uneven outside valuation/AI/processing-run objects.

Confidence level: High

### Testing

Status: Strong backend coverage, moderate frontend utility coverage

What it does:

- Backend tests cover API CRUD, ingestion, scoring, valuation math, diagnostics, macro sensitivity, portfolios, security, providers, models, and migrations.
- Frontend tests cover API parsing and selected utility logic.

Inputs required:

- Docker/backend test environment.
- Frontend node dependencies.

Outputs produced:

- Test validation.

Important files:

- `backend/tests/`
- `frontend/lib/*.test.ts`
- `frontend/package.json`

Limitations:

- Frontend page/component coverage is much thinner than backend coverage.
- Eight isolated workflows cover responsive accessibility, alert evidence, PDF
  review/promotion/reconciliation, mobile navigation, disclosed AI failure,
  invalid CSV recovery, and valuation draft promotion. Live-provider failures,
  stale-write conflicts, company setup, portfolio lifecycle in the current
  suite, and many dynamic empty/error states still lack repeatable coverage.

Confidence level: High

## 5. What Is Actually Automated

| Workflow area | Fully automated | Semi-automated | Manual | Notes |
| --- | --- | --- | --- | --- |
| Company creation | No | Yes | Yes | Normalization is automated, but user provides identity. |
| US CIK lookup | Yes | Yes | No | Works for SEC-supported tickers. |
| India company lookup | No | No | Yes | NSE/BSE provider is a stub. |
| RSS ingestion | Yes | Yes | Yes | Triggered by user/API, then pipeline runs automatically. |
| Filing discovery/acquisition | No | Yes | Yes | US SEC candidates can be discovered; India and unsupported sources require manual filing links/text. |
| SEC filing ingestion | Yes | Yes | Yes | Automated for configured US companies, still user-triggered/config-dependent. |
| India filing ingestion | No | Yes | Yes | Manual upload/link only; no automated NSE/BSE filings provider. |
| FRED macro ingestion | Yes | Yes | Yes | Requires API key and selected series. |
| Market-price ingestion | No | Yes | Yes | Provider abstraction exists, but user/API key/config still required. |
| Financial statement parsing | No | Yes | Yes | First-pass candidates come from reviewed text, line-based PDF tables, Screener workbooks, or SEC companyfacts. All require review; OCR, complex-table reconstruction, total checks, and full statement coverage are incomplete. |
| Event extraction | Yes | Yes | No | Runs after ingestion/manual processing; quality varies. |
| Alert generation | Yes | Yes | No | Depends on event scoring threshold. |
| Daily brief | Yes | Yes | No | Generated from current data, not external judgment. |
| Portfolio analytics | Yes | Yes | Yes | Calculated from manually entered/imported portfolio and price data. |
| DCF calculations | Yes | Yes | Yes | Math is deterministic after assumptions are provided. |
| Industry mapping | No | Yes | Yes | Industry lists load with an explicit country-taxonomy fallback; suggestions still require confirmation. |
| Damodaran benchmark ingestion | No | Yes | Yes | Upload/script/admin-driven. |
| AI valuation memo | No | Yes | Yes | Generated on request, must be reviewed. |
| Narrative-to-numbers | No | Yes | Yes | Suggestions only, not trusted automatic assumptions. |
| Market regime score | No | No | No | Current UI page is mock. |
| Broker sync | No | No | No | Not built. |
| Public deployment security | No | No | No | Not built. |

## 6. What Requires User Input

### Company selection

- Ticker, market, exchange, local symbol, currency, and company metadata.
- Needed because provider lookup is incomplete, especially for India.

### Financial data

- Manual financial metrics or verified provider-derived metrics.
- Needed because full financial-statement extraction is not yet a trusted automated pipeline.

### Assumptions

- Revenue growth, margins, taxes, reinvestment, WACC, terminal growth, cash/debt, share count, market price.
- Needed because valuation quality depends more on assumptions than formulas.

### Industry mapping

- Country and Damodaran industry selection.
- Needed because current industry suggestion is simple and can be wrong.

### Valuation model choice

- Model type, scenario, and whether FCFF/FCFE/DDM/relative/macro/real-options analysis is appropriate.
- Needed because the app cannot know the right valuation method without context.

### Data sources/API keys

- `SEC_USER_AGENT`, optional market/news/macro/AI provider keys, RSS URLs, and uploaded benchmark files.
- Needed because external providers cannot run without configuration.

### Thesis/narrative

- Thesis notes, assumptions, evidence, and narrative text.
- Needed because the app structures judgment but does not replace investment judgment.

### Scenario assumptions

- Bear/base/bull or other scenario inputs.
- Needed because scenario generation is only useful with explicit user beliefs.

### Review/approval

- AI memos, narrative-to-numbers suggestions, alerts, industry mappings, and valuation warnings.
- Needed because these outputs can be incomplete or wrong.

## 7. Data Sources and Data Flow

Current data sources:

- Manual user input.
- CSV imports.
- SEC EDGAR for US filings.
- RSS feeds.
- FRED macro series if configured.
- Market-data providers through Alpha Vantage/FMP-style abstraction if configured.
- Damodaran workbook uploads/import scripts.
- Optional Gemini AI provider; mock is test/demo-only and never a failure fallback.

Uploaded/static data files:

- Damodaran `.xls`/`.xlsx` workbooks.
- Portfolio and market-price CSV files.
- Manual filing text/links.

External APIs:

- SEC EDGAR.
- RSS feed URLs.
- FRED.
- Alpha Vantage/FMP style market data.
- Gemini/OpenAI/Anthropic config placeholders, with production code currently
  using the unified Gemini contract and explicit test/demo mock mode.

Manual inputs:

- Companies, sources, thesis notes, assumptions, portfolio records, market prices, benchmark selections, data review decisions.

Database tables:

- Company, Source, MarketSourceCapability, CountryMarketContext, RawDocument, Event, Alert, ThesisNote, DailyBrief, ProcessingRun, Portfolio, Holding, Transaction, CashBalance, Snapshot, MarketPrice, CompanyMarketData, ValuationModel, DcfAssumptionSet, DcfOutput, DcfProjectionYear, DcfSensitivityTable, Damodaran datasets, MacroSeries, AiOutput, Research, Evidence, Decision, VariantPerception, Narrative, Social/Sentiment, OAuth.

Backend services:

- Ingestion, event extraction, scoring, alert generation, daily brief, portfolio analytics, DCF, diagnostics, WACC, reverse DCF, macro sensitivity, relative valuation, real options, Damodaran parsing, industry priors, AI memo writing.

Frontend display:

- Dashboard and module pages render API data using `frontend/lib/api.ts`, page components, data-state components, and module-specific panels.

Actual data flow:

```text
User input / CSV / SEC / RSS / FRED / market-data provider / Damodaran files
-> ingestion or CRUD route
-> normalized database tables
-> backend services
-> deterministic engines and scoring
-> optional AI explanation layer
-> frontend pages and panels
```

Aspirational data flow:

```text
Official US/India providers
-> source capability registry
-> automated ingestion schedules
-> normalized multi-country financial and market database
-> evidence-backed intelligence and valuation cockpit
-> reviewed AI memos and decision workflows
```

The aspirational flow is not fully implemented.

## 8. AI Layer Responsibilities

AI should do:

- Explain deterministic outputs.
- Summarize source-backed information.
- Draft valuation memos.
- Challenge assumptions.
- Map user narrative into suggested assumptions.
- Identify missing information.
- Preserve limitations, prompt version, model name, and review status.
- Persist source scope, privacy disclosure, transmitted data classes, explicit
  mock state, and safe failure status.

AI should not do:

- Freehand financial calculations without deterministic backend support.
- Invent data.
- Hide assumptions.
- Treat industry averages as company facts.
- Make buy/sell recommendations.
- Convert weak evidence into confident conclusions.
- Replace user review.

Current risk:

- The unified provenance/privacy boundary exists and mock output is visible.
- Citation verification, evaluation thresholds, and complete approve/reject UI
  are still missing, so AI output is not certified source-backed research.

## 9. Deterministic Logic / Calculation Layer

Currently deterministic:

- FCFF DCF forecast.
- Revenue growth path.
- Operating margin fade.
- NOPAT.
- Reinvestment using change in revenue divided by sales-to-capital ratio.
- Invested capital.
- ROIC.
- WACC fade.
- Present value of FCFF.
- Terminal value using terminal FCFF divided by WACC minus growth.
- Equity bridge from enterprise value to intrinsic value per share.
- Sensitivity tables.
- Reverse DCF.
- Scenario outputs.
- WACC calculations.
- Macro sensitivity translation.
- Portfolio analytics.
- Event scoring.
- Alert thresholding.
- CSV import row validation for selected imports.

Important formulas implemented:

```text
EBIT = Revenue * Operating Margin
NOPAT = EBIT * (1 - Tax Rate)
Reinvestment = Change in Revenue / Sales-to-Capital Ratio
FCFF = NOPAT - Reinvestment
ROIC = NOPAT / Invested Capital
Terminal Value = Terminal FCFF / (WACC - Terminal Growth)
Equity Value = Enterprise Value + Cash - Debt - Minority Interests - Preferred Stock - Options Value
Intrinsic Value Per Share = Equity Value / Diluted Shares
```

Validation and warnings include:

- Terminal growth above risk-free rate.
- Terminal value share too high.
- WACC below risk-free rate.
- Positive growth with no reinvestment.
- ROIC below WACC during high growth.
- Missing share count.
- Basic shares versus diluted shares.
- Negative FCFF patterns.
- External funding dependence.
- Financial-services mismatch.

Known calculation gaps:

- Some diagnostic comparisons still use imperfect proxies.
- Currency conversion and market-specific rates need more provider-backed rigor.
- Industry priors need stronger source labeling and confirmation UX.
- Market regime calculations are not implemented as trusted deterministic backend logic.

Calculations still involving LLM:

- Narrative-to-numbers suggestions.
- Valuation memo explanation.
- Document AI summaries.

These should be treated as explanations or suggestions, not source-of-truth calculations.

## 10. Frontend Capabilities

Pages/routes observed:

- `/`
- `/companies`
- `/companies/[id]`
- `/companies/[id]/setup`
- `/companies/[id]/filings`
- `/companies/[id]/fundamentals`
- `/companies/[id]/valuation`
- `/companies/[id]/valuation/[model_id]`
- `/companies/[id]/thesis`
- `/companies/[id]/evidence`
- `/companies/[id]/decisions`
- `/sources`
- `/data`
- `/data-health`
- `/documents`
- `/documents/[id]/sections`
- `/documents/[id]/ai`
- `/events`
- `/alerts`
- `/daily-brief`
- `/portfolio`
- `/portfolio/[id]`
- `/portfolio/manage`
- `/portfolio/regime`
- `/valuation`
- `/valuation/quick`
- `/macro`
- `/market-prices`
- `/research`
- `/research/sessions`
- `/research/sessions/[id]`
- `/narratives`
- `/social`
- `/settings`
- `/admin/damodaran`
- `/api/backend/[...path]`

Main components:

- `AdvancedWorkspace`
- `QuickValuationWorkflow`
- `DcfForm`
- `PortfolioAnalytics`
- `DailyBriefPanel`
- `EventsTimeline`
- `AlertsPanel`
- `FinancialTrends`
- `ScoreBreakdown`
- `ScoreExplanation`
- `SourceCapabilityMatrix`
- valuation panels for diagnostics, sensitivity, relative valuation, macro sensitivity, real options, memo, narrative-to-numbers, market context, scenario range, change log.

Data states:

- `LoadingState`
- `ErrorState`
- `EmptyState`
- `StaleDataBanner`
- `MockDataBadge`
- `MockDataState`
- `NotConfiguredState`
- `PartialDataNotice`
- `DataFreshnessIndicator`

Confusing or missing UI elements:

- Market regime is mock despite looking like a real analytical dashboard.
- New alert/event evidence can use validated text spans, sections, and PDF regions with safe exact highlighting. PDF regions are exact only when finite top-left coordinates and declared page dimensions match the stored asset. A bounded Data Health workflow can backfill historical spans only when a 24-2,000 character event/current-user-alert claim occurs exactly once in stored source text; every POST records a processing run. Unmatched, ambiguous, and conflicting rows with stored text can now use authenticated bounded exact search and reviewed occurrence selection. Page-only, fuzzy/normalized, OCR-only, and unsupported records retain explicit review or partial/page/document fallbacks.
- Some empty states are actionable; not every route has been verified.
- Some backend modules may have routes before the frontend gives them a complete workflow.

Does the UI match backend capabilities?

- Partly. Core dashboard, company, source, ingestion, alert, portfolio, and valuation flows align with real backend data.
- Market regime does not.
- Some advanced research/social/narrative areas are more data-model foundation than complete product workflow.

## 11. Backend/API Capabilities

Existing API areas:

- Companies and company lookup.
- Sources and source capability matrix.
- Raw documents, document sections, diffs, AI outputs.
- Events, corroborations, contradictions.
- Alerts and review.
- Thesis notes, assumptions, and changes.
- Daily briefs.
- Processing runs and ingestion status.
- RSS, SEC, FRED, and market-data ingestion.
- Portfolio, holdings, transactions, cash balances, snapshots, analytics.
- Market prices and quotes.
- Valuation models, DCF assumptions, forecasts, results, sensitivity, scenarios, reverse DCF, diagnostics.
- WACC, accounting normalization, real options, regression priors, relative valuation.
- Damodaran admin import/files/rollback/compare.
- Macro series, observations, macro valuation.
- AI narrative-to-numbers and memo.
- Research sessions/messages.
- Evidence, decisions, variant perception.
- Narratives, social posts, sentiment.
- CSV import/export.
- OAuth token storage/status.

Validation:

- Pydantic schemas are used broadly.
- Many routes check references and return 404/400/409 where appropriate.
- CSV import has row-level validation.
- Company identity has duplicate checks.

Error handling:

- Good enough in many CRUD and ingestion paths.
- Not uniform across all routes.
- Some routes return raw exception strings through HTTP errors, which should be reviewed for production.

Auth requirements:

- None. This is local-first only.

Missing endpoints:

- Production auth/session endpoints.
- Complete broker integration.
- Complete India provider ingestion.
- Trusted market regime scoring endpoint.
- Scheduling/automation controls.

Routes that may exist before full frontend use:

- Evidence, decisions, variant perception, social, narrative, real options, regression priors, some macro valuation, and some admin benchmark functions.

Frontend features with no complete backend support:

- Market regime page.
- Any surface implying live institutional positioning, gamma, breadth, or liquidity data.

## 12. Database and Persistence

Main tables/models:

- `Company`: company identity and market metadata.
- `Source`: data source metadata.
- `MarketSourceCapability`: provider/source coverage.
- `CountryMarketContext`: country-level market assumptions.
- `RawDocument`: ingested or manual source documents.
- `DocumentSection`: parsed document sections.
- `Event`: extracted events and scores.
- `Alert`: reviewable alerts.
- `ThesisNote`, `ThesisAssumption`, `ThesisChange`: thesis workflow.
- `DailyBrief`: brief snapshots.
- `ProcessingRun`: ingestion/provider run history.
- `Portfolio`, `PortfolioHolding`, `PortfolioTransaction`, `PortfolioCashBalance`, `PortfolioSnapshot`: portfolio state.
- `MarketPrice`, `CompanyMarketData`: price and quote records.
- `ValuationModel`, `DcfAssumptionSet`, `DcfOutput`, `DcfProjectionYear`, `DcfSensitivityTable`, `ValuationAssumptionChangeLog`: valuation persistence.
- `DamodaranDatasetFile` and related benchmark models: benchmark imports.
- `MacroSeries`, `MacroObservation`, `SectorMacroSensitivity`: macro data.
- `AiOutput`: AI output provenance.
- `ResearchSession`, `ResearchMessage`: research conversations.
- `Evidence`, `Decision`, `VariantPerception`: decision workflow.
- `NarrativeCluster`, `NarrativeClaim`, `NarrativeMention`, `SocialPost`, `SentimentScore`: narrative/social layer.
- `OAuthToken`: OAuth-like token storage.

What data is stored:

- Local research state, assumptions, source documents, derived events, outputs, and review records.

What data is not stored or not complete:

- Production user accounts.
- Complete provider audit logs.
- Broker account data.
- Full real-time market feed.
- Fully normalized multi-country financial statements.

Migration status:

- Alembic exists and is covered by tests.
- Backend tests currently pass.

Seed data status:

- Scripts exist for sample data and regression coefficients.
- Damodaran ingestion scripts exist.

Data versioning:

- Stronger in valuation, AI output, processing runs, and Damodaran dataset records.
- Weaker in general CRUD records.

Audit trail support:

- Partial. Processing runs and AI outputs are good starts. Full user/action audit trail is not implemented.

Schema weaknesses:

- Some schema breadth is ahead of product workflow maturity.
- OAuth/token storage requires deeper security design before any sensitive integration.

## 13. Tests and Reliability

Existing tests:

- Backend tests under `backend/tests/`.
- Frontend utility tests under `frontend/lib/*.test.ts`.

Backend coverage includes:

- Alembic.
- API CRUD.
- API errors.
- RSS and SEC ingestion.
- Event extraction.
- Alert generation/review.
- Daily briefs.
- Scoring.
- Security helpers.
- Portfolio analytics and valuation.
- Company market identity.
- Source capabilities.
- Country market context.
- Market data context.
- Damodaran parser/ingestion.
- DCF, valuation math, diagnostics, red flags, integration.
- WACC.
- Macro sensitivity and scenario translation.
- Real options.
- AI service.
- Social/narratives.

What tests do not cover well:

- Full frontend page behavior.
- Browser-level UI flows.
- Production deployment security.
- Real external provider reliability.
- End-to-end India data workflows.
- Market regime, because it is not real yet.
- AI output quality.

Known warnings:

- The latest full backend verification completed without a warning summary. New dependency upgrades can reintroduce warnings and should be checked in CI output.

Commands to run:

```bash
docker compose exec backend pytest backend/tests -q
```

Frontend checks depend on local Node setup:

```bash
cd frontend
npm test
npm run typecheck
npm run build
```

Minimum tests needed before serious usage:

- Browser-level smoke tests for core workflows.
- Frontend route tests for data states.
- Provider integration tests with mocked external APIs.
- End-to-end valuation workflow tests from company creation through memo.
- CSV import/export file download tests.
- India-market manual filing workflow tests.

## 14. Known Flaws and Limitations

| Severity | Issue | Why it matters | Affected area | Suggested fix |
| --- | --- | --- | --- | --- |
| Resolved checkpoint | FastAPI auth and owned-domain resolution were incomplete | Closed by aggregate authentication, a two-route public allowlist, automated inventory, direct-port tests, and expanded negative ownership coverage | Backend/security | Keep inventory and ownership suites in CI; this remains local-only security. |
| Resolved checkpoint | Research-session and AI-output ownership were defective | Closed for owned research CRUD/messages and owned AI output/routes with cross-user tests; exact citation/evaluation/review foundations now exist | Research/security | Add provider-generated citations, broaden the corpus, and complete remaining review/failure browser states. |
| Resolved checkpoint | CSV export and transfer ownership were broken | Closed for tested manual interchange with true files, owned portfolios, bounded validation, preview/apply, rollback, and invalid-preview browser proof | Data transfer/portfolio | Add valid apply/download browser coverage; continue treating the separate restore-tested scripts as backup. |
| Critical | Local auth is not public-deployment security | Public exposure would still risk private research and portfolio data | Security/deployment | Keep localhost-only until production identity, authorization review, HTTPS, CSRF review, secret management, backups, and audit logging exist. |
| Critical | Broker sync is not safe or built | Broker credentials/tokens are sensitive and could create financial/security risk | Portfolio/security | Do not build broker sync until official OAuth, encrypted storage, revocation, audit logs, and threat model are approved. |
| High | Market regime UI is mock | It looks analytical but is simulated | Frontend/market intelligence | Keep mock badge visible and build backend deterministic regime score before presenting values as real. |
| High | India platform support is incomplete | US/India transition could be overstated | Providers/data | Add real India company lookup, filings provider, market data, fundamentals, and source capability health. |
| High | Industry mapping is fragile | Wrong industry creates wrong benchmark priors and valuation assumptions | Valuation | Require user confirmation, show confidence/source, and improve matching with identifiers and benchmark coverage. |
| Resolved checkpoint | AI prompts requested recommendation-like conclusions | Could produce prohibited advice language | AI/valuation | Production memo/narrative prompts now prohibit buy/sell recommendations; keep prompt tests and review. |
| Resolved checkpoint | Frontend styling pipeline was missing for utility-class usage | Tailwind/PostCSS, project-owned tokens, production build, semantic/overflow checks, and representative responsive screenshots now pass | Frontend | Continue reducing legacy inline layout and extend screenshot coverage to dynamic workflows. |
| High | Frontend parity has not been fully audited page-by-page | UI may imply more than backend supports | Frontend | Run route audit and add trust labels, empty states, and endpoint checks per page. |
| High | Provider-backed market data is not complete | Portfolio and valuation may use stale/manual prices | Market data/portfolio | Add provider health, freshness badges, per-market support, and manual override labeling. |
| Medium | Some docs are stale | Future agents may make wrong assumptions | Documentation | Keep current-state, architecture, and product docs reconciled after each feature batch. |
| Medium | AI summaries/memos require deeper citation coverage | Users may overtrust generated language | AI/research | Existing review status, provider/mock labels, source validation, and approve/reject/revision controls are foundations; add automatic provider citations and a larger evaluation set. |
| Medium | Event extraction is rule-based | It can miss nuance or overclassify weak text | Ingestion/intelligence | Add extraction confidence, manual correction, and source-backed evidence review. |
| Medium | Full financial statement ingestion is not complete | Valuation inputs may be manual or partial even though typed candidate evidence, normalized coverage, and source reconciliation exist | Financials/valuation | Build verified PDF/table extraction with bounding boxes, comparative-period total checks, and broader statement normalization before automatic valuation defaults. |
| Medium | Currency handling is still basic | US/India portfolio/valuation comparisons can be misleading | Portfolio/valuation | Add FX rates, source labels, conversion rules, and native/reporting currency separation. |
| Resolved checkpoint | Current Damodaran typed importers could replace history | Closed for all current application source-specific typed paths through exact hash-versioned imports and active-only reads | Valuation/data health | Keep preserved-version tests on every new source parser; historical macro datasets remain a separate contract. |
| Low | Some advanced schema exists before polished workflows | Complexity may confuse future agents | Architecture/UI | Prioritize user-facing workflows over adding more models. |
| Low | Admin Damodaran compare is mock | Admin users may misread benchmark comparison | Admin/valuation | Replace mock compare with real dataset diff or label it clearly as not implemented. |

## What Not To Trust Yet

Do not trust these outputs without review:

- Market regime values.
- Any UI panel marked `Mock Data`.
- AI-generated valuation memos as investment conclusions.
- Narrative-to-numbers assumption suggestions.
- Industry mapping without user confirmation.
- Industry averages as company-specific facts.
- Autofilled assumptions from `/valuation-models/autofill`; drafts persist per-field provenance, review state, and source-age diagnostics, but stale sources, unknown freshness, and generic placeholders still require explicit user review.
- Valuation numbers based on unreviewed assumptions.
- Financial metrics from incomplete ingestion.
- Real-time or near-real-time prices.
- Portfolio analytics when market prices are stale, manual, or missing.
- India automated filings or data provider coverage.
- Social sentiment as live market intelligence.
- Any output that resembles a buy/sell recommendation.

## 16. Potential Upgrades

### Priority 1: Must Fix / Core Product

- Backfill exact evidence locators for historical events where stored bytes permit it.
  - Why it matters: New validated text/page/section/PDF-region locators work, but historical records still fall back explicitly.
  - Dependencies: Stored source bytes plus the shipped typed reference model.
  - Estimated difficulty: Medium.
  - Suggested phase: Real-source certification work.

- Replace market-regime mock with real backend status or hide it behind explicit prototype labeling.
  - Why it matters: Mock macro/liquidity signals are dangerous.
  - Dependencies: Macro/market data provider readiness.
  - Estimated difficulty: Medium.
  - Suggested phase: Before any market-regime usage.

- Harden AI memo language and review flow.
  - Why it matters: Prevents recommendation-like output and overtrust.
  - Dependencies: Existing `AiOutput` provenance.
  - Estimated difficulty: Low.
  - Suggested phase: Immediate.

- Audit every frontend route for backend parity and data-state honesty.
  - Why it matters: UI must not overstate capabilities.
  - Dependencies: Route inventory.
  - Estimated difficulty: Medium.
  - Suggested phase: Immediate.

- Expand provider health from computed readiness into active health checks for market data, SEC, RSS, FRED, and AI.
  - Why it matters: Users need to know what data is current or missing.
  - Dependencies: Processing runs and source capabilities.
  - Estimated difficulty: Medium.
  - Suggested phase: Core data-health batch.

### Priority 2: Serious Usability Improvements

- Build guided company setup for US and India.
  - Why it matters: Correct identity drives every downstream workflow.
  - Dependencies: Company lookup providers and source capability metadata.
  - Estimated difficulty: Medium.
  - Suggested phase: Company intake batch.

- Improve industry mapping.
  - Why it matters: Bad benchmark priors distort valuations.
  - Dependencies: Damodaran dataset coverage and user confirmation UI.
  - Estimated difficulty: Medium.
  - Suggested phase: Valuation workflow batch.

- Add valuation assumption source labels everywhere.
  - Why it matters: Users must know what is manual, benchmark-derived, calculated, AI-suggested, or provider-derived.
  - Dependencies: Existing valuation schemas may need small extensions.
  - Estimated difficulty: Medium.
  - Suggested phase: Valuation trust batch.

- Extend browser smoke tests beyond the protected core workflows.
  - Why it matters: Valuation and PDF state transitions are protected, but provider and failure-state reliability is less proven.
  - Dependencies: Isolated Docker E2E stack.
  - Estimated difficulty: Medium.
  - Suggested phase: Reliability batch.

- Add browser coverage for CSV download, preview, apply, malformed input, and
  rollback, then complete a clean-environment restore drill.
  - Why it matters: Manual data transfer is important until providers are complete.
  - Dependencies: Data transfer endpoints.
  - Estimated difficulty: Low.
  - Suggested phase: Data operations batch.

### Priority 3: Advanced Intelligence

- Build source-backed research memo workflow.
  - Why it matters: AI becomes useful only when tied to evidence.
  - Dependencies: Evidence trail, document sections, AI output provenance.
  - Estimated difficulty: High.
  - Suggested phase: After evidence UX.

- Add contradiction and falsification engine.
  - Why it matters: The app should challenge theses, not just summarize.
  - Dependencies: Thesis assumptions, events, evidence links.
  - Estimated difficulty: High.
  - Suggested phase: After thesis/evidence workflow stabilizes.

- Add real US/India provider layer for fundamentals and market data.
  - Why it matters: Manual data limits scale.
  - Dependencies: Provider selection, keys, rate limits, source capability health.
  - Estimated difficulty: High.
  - Suggested phase: Provider batch.

- Build real market-regime scoring.
  - Why it matters: Risk-on/risk-off context is useful only if source-backed.
  - Dependencies: Market data, macro data, breadth, volatility, options/flows where available.
  - Estimated difficulty: High.
  - Suggested phase: After provider health and macro data.

### Priority 4: Nice-to-Have / Later

- Broker sync.
  - Why it matters: Reduces manual portfolio entry.
  - Dependencies: Approved security model and official OAuth providers.
  - Estimated difficulty: High.
  - Suggested phase: Much later.

- Public deployment.
  - Why it matters: Enables multi-device or team use.
  - Dependencies: Auth, authorization, HTTPS, secrets, rate limits, audit, backups.
  - Estimated difficulty: High.
  - Suggested phase: Much later.

- Advanced social/news integrations.
  - Why it matters: Better narrative monitoring.
  - Dependencies: Official APIs and provenance model.
  - Estimated difficulty: Medium to High.
  - Suggested phase: After core source-backed workflow.

## 17. Recommended Build Order

| Phase | Build item | Why now | Dependencies | Acceptance criteria |
| --- | --- | --- | --- | --- |
| 1 | Frontend/backend capability audit route-by-route | Prevents fake or misleading UI | Current route inventory | Every page marked real/partial/mock/not configured with visible state. |
| 2 | Exact evidence locator backfill | New exact locators are shipped; historical coverage remains | Typed trail plus stored source bytes | Backfilled records jump to validated source spans/regions and unsupported records retain explicit fallback. |
| 3 | AI citation depth | AI can mislead users | Shipped citation/evaluation/review foundation | Providers emit validated citations and the expanded evaluation corpus passes before source-backed trust claims. |
| 4 | Provider health dashboard | User needs to know what is configured | Processing runs/source capabilities | Implemented foundation: Data Health page shows configured/missing/failing/manual-only provider status. |
| 5 | Company setup workflow | Correct identity/source readiness is the first step in valuation automation | Company model/source readiness | Implemented foundation: `/companies/[id]/setup` tracks identity and setup states. |
| 6 | Industry mapping confirmation workflow | Valuation priors depend on it | Damodaran datasets | User sees candidates, source, confidence, and confirms industry before priors apply. |
| 7 | Assumption provenance in valuation UI | Valuation trust depends on assumptions | Valuation schemas/UI | Every assumption is labeled manual/benchmark/provider/calculated/AI-suggested. |
| 8 | US/India provider expansion | Platform transition requires real coverage | Source capability matrix | India and US company/filing/price/fundamental support clearly implemented or marked unavailable. |
| 9 | Financial statement normalization | Reduces manual valuation input | SEC/fundamentals services | User can review normalized statements with validation errors and source links. |
| 10 | Real market-regime backend | Current page is mock | Market/macro providers | Score endpoint returns score, confidence, drivers, blockers, warnings, sources, formula, timestamp. |
| 11 | Browser workflow expansion | Protects workflows | Eight isolated workflows already pass | Add company setup, live-provider errors, stale-write conflicts, current portfolio lifecycle, and remaining dynamic states. |

## 18. Open Questions

### Product

- Is the first paid/user-facing workflow valuation-first, portfolio-first, or source-ingestion-first?
- Should the app optimize for solo investors, small funds, or founder/operator research?
- Which outputs must be printable/exportable?

### Data

- Which US market-data provider should be primary?
- Which India providers are acceptable: NSE/BSE official data, filings, paid APIs, manual only?
- How fresh does each data category need to be?
- Is manual data entry acceptable for early users?

### Valuation/finance logic

- Which valuation methods are required for financials, banks, insurers, and high-growth negative-FCF companies?
- What default country risk premiums and risk-free rates should be used?
- Should benchmark priors be auto-filled or only suggested?
- What level of source proof is required before a valuation is marked reviewed?

### UI/UX

- Should the dashboard prioritize alerts, portfolio exposure, or valuation tasks?
- What is the minimum evidence trail a user needs on every alert?
- Which pages should be hidden until backed by real data?

### Backend

- Should route prefixes be normalized?
- Should export endpoints return raw file responses instead of `ApiResponse` wrappers?
- Should provider health be calculated live or persisted from processing runs?

### Security

- Will this remain localhost-only?
- If not, who are the user roles?
- What private data can AI providers receive?
- Is broker integration actually needed soon?

### Deployment

- Is Docker Compose enough for the next phase?
- Is there a need for cloud deployment, backups, and multi-user access?
- What secrets manager and auth provider should be used if deployed?

## 19. File Map

| File/folder | Purpose | Notes |
| --- | --- | --- |
| `README.md` | Project overview | Honest high-level summary of current and planned scope. |
| `AGENTS.md` | Agent operating manual | Must be followed by future coding agents. |
| `docs/00-current-state.md` | Current implementation status | Good starting point, should stay updated. |
| `docs/01-product-brief.md` | Product intent | Some older planned/implemented wording may be stale. |
| `docs/02-architecture.md` | Architecture overview | Describes source-backed data flow and API envelope. |
| `docs/03-database-schema.md` | Schema documentation | Useful map of major models. |
| `docs/04-data-sources-and-ingestion.md` | Ingestion documentation | Describes SEC/RSS/manual/provider data flow. |
| `docs/05-scoring-framework.md` | Scoring framework | Event-level scoring is most mature. |
| `docs/06-security-threat-model.md` | Security assumptions | Clear that app is local-only, not public-ready. |
| `docs/07-local-development.md` | Local setup | Docker, env, troubleshooting. |
| `docs/08-execution-runbook.md` | Build phase history | Some completed-phase claims should be interpreted against code. |
| `docs/valuation-agent/master-build-plan.md` | Valuation build plan | Largely reflects the mature valuation system. |
| `docs/valuation-agent/autofill-workflow-plan.md` | Valuation autofill workflow plan | Partially implemented; verify source grounding before building on it. |
| `docs/roadmaps/market-intelligence-build-roadmap.md` | Market intelligence roadmap | Contains useful future direction; verify against code before implementation. |
| `docs/roadmaps/valuation-auto-pipeline-master-plan.md` | Valuation automation roadmap | Active planning reference for reviewed financials and automation. |
| `docs/archive/needs-review/` | Stale or redundant docs | Preserved context, not current implementation guidance. |
| `backend/app/main.py` | FastAPI app entry | Mounts app and health behavior. |
| `backend/app/api/routes.py` | Router registration | Shows broad backend API surface. |
| `backend/app/api/routers/` | API route modules | Main implementation surface for product capabilities. |
| `backend/app/api/schemas.py` | Pydantic API schemas | Includes `ApiResponse` envelope and domain schemas. |
| `backend/app/models/` | SQLAlchemy models | Database truth for persisted data. |
| `backend/app/services/` | Business logic | Valuation, ingestion, scoring, alerts, macro, portfolio, AI. |
| `backend/app/providers/` | Provider abstractions | SEC/RSS/AI/company lookup/filing providers. |
| `backend/alembic/versions/` | Database migrations | Required for schema state. |
| `backend/tests/` | Backend tests | Strongest reliability evidence. |
| `frontend/app/` | Next.js routes | Main UI surfaces. |
| `frontend/components/` | Reusable UI/workflow components | Valuation and dashboard components live here. |
| `frontend/lib/api.ts` | Frontend API client | Handles API envelope and legacy response shapes. |
| `frontend/components/ui/data-states.tsx` | Data-state UI | Loading/error/empty/stale/mock/not-configured components. |
| `scripts/ingest_damodaran.py` | Damodaran import helper | Benchmark ingestion support. |
| `scripts/seed_regressions.py` | Regression seed helper | Supports valuation priors/regression features. |
| `.env.example` | Local environment template | Contains placeholders and local defaults. |
| `docker-compose.yml` | Local service orchestration | Standard way to run app. |

## 20. Final Handoff Summary

```text
Current status:
Local-first market intelligence and valuation app with a broad, tested backend and uneven but usable frontend. Valuation is the strongest implemented capability. Source-backed intelligence is functional but not fully mature.

Most important working capability:
Deterministic valuation engine plus company/source/document/event/alert/portfolio persistence.

Most important gap:
India representative certification. AAPL is trust-ready and reconciled. Adani
has exact source custody and 48 staged candidates, but operating EBIT, industry
mapping, promotion, and normalized reconciliation remain unresolved.

Next best task:
Review APSEZ operating EBIT and industry mapping, promote the approved set, run
India reconciliation/certification, then add the PDF evidence overlay.

Do not build yet:
Broker sync, public deployment, live trading features, or advanced market-regime claims.

Main risk:
The app can look more complete than it is. Mock, stale, manual, or AI-suggested outputs must never be presented as verified investment intelligence.

Recommended next prompt:
Review the staged APSEZ FY2023-FY2025 candidates, reconstruct operating EBIT
with explicit non-operating classifications, promote only the approved set, and
run the India certification gate without weakening it.
```
