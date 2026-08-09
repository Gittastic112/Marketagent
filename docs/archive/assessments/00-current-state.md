# Current State & Known Issues

This is the source of truth for the current state of the application following the recent UI and backend pivot toward a unified intelligence cockpit, along with the prioritized backlog of known issues. For the latest agent-to-agent status, also read `docs/HANDOFF.md`. For the long-form capability audit, read `docs/agent_capabilities_and_limitations.md`.

**Latest checkpoint:** the versioned country-statistics checkpoint below
supersedes earlier 2026-08-08 Damodaran counts and migration-head notes. Current
live state is 9 supported, 13 partial, 13 unsupported, 14 typed sources, 3,290
typed rows, 12 complete active provenance records, and migration head
`p1p1p1p1p1p1`.

**2026-08-08 versioned country-statistics checkpoint:** `countrystats.xls` now
uses the preserved dataset lifecycle and an exact 22-column source contract.
The importer retains 127 country rows and all 20 meaningful fields, including
debt including leases, firm value, cash, cash/firm value, and signed source
dividends that the prior importer omitted. Active version `#50` has SHA-256
`900b6594f808461f9ce5194abf1a50e66f22854bc998473ad8282037d464829b`,
source date `2026-01-05`, and 127 rows; two imports reused the same version.
Country-stat API and industry-mapping reads require the active version and
expose exact provenance. Migration `p1p1p1p1p1p1` is additive. This closes the
destructive replacement behavior in all current application source-specific
typed Damodaran importers; it does not mean all 35 mirrored workbooks are
implemented. Validation passes 27 focused tests, 483 backend tests, 90 frontend
tests, TypeScript, the Next.js 16.2.11 production build, Python compile,
Alembic head, four knowledge-base tests, the corpus audit, and
`git diff --check`. See
`docs/roadmaps/next-5-damodaran-versioned-country-statistics-checkpoint-2026-08-08.md`.

**2026-08-08 versioned volatility and real-options API checkpoint:** Capex, ROE,
Margin, Working Capital, Dividend, FCFE, and Volatility now use the preserved,
hash-idempotent dataset lifecycle. Volatility rows have a nullable
legacy-compatible `dataset_file_id`; unproven legacy rows remain stored but are
excluded from active reads and Data Health counts. The exact `optvarIndia.xls`
parser requires all six industry columns plus the workbook's `0.40` relative
bond-volatility and `0.50` stock/bond-correlation assumptions. It preserves
legitimate zero and null values and excludes Total Market aggregates. Active
version `#45` has SHA-256
`763b4a907f9584395e5cba1bb428f064dd6a85ff90a08e0bfb80d919d97cb54b`,
source date `2026-01-05`, and 94 rows; two imports reused the same version.
The canonical `/api/valuation/options/*` routes now exist, hidden legacy aliases
remain compatible, and a missing volatility benchmark returns
`VOLATILITY_BENCHMARK_NOT_FOUND` instead of fabricated numbers. Live coverage
remains 5 supported, 17 partial, 13 unsupported, 9 typed sources, and 2,787
typed rows. Seven active typed sources have complete provenance, none are
partial or missing, and no mirror hash mismatch exists. Migration head is
`m9m9m9m9m9m9`. Validation is 461 backend tests, 90 frontend tests, TypeScript,
and the Next.js 16.2.11 production build. Completion remains 75% local-first and
64% world-class. See
`docs/roadmaps/next-20-damodaran-versioned-volatility-and-real-options-api-checkpoint-2026-08-08.md`.

**2026-08-08 versioned pricing and relative-valuation checkpoint:** PE, PBV,
PS, and EV/EBITDA now use independent preserved dataset versions instead of
destructive replacement. Exact parsers retain every workbook control: aggregate
PE variants and expected growth; ROE/ROIC; net and operating margins; and both
positive-denominator/all-firm R&D-adjusted, EBITDA, EBIT, and after-tax EBIT
multiples. Migration `n0n0n0n0n0n0` is additive. Relative valuation no longer
selects an arbitrary sparse row from the shared table; it assembles only active
rows by source and attaches the correct source version to every calculation.
Canonical routes are `/api/valuation/relative/*`; hidden legacy aliases remain.
The UI selects the first available active country, reports unavailable methods,
shows benchmark versions, preserves zero values, and does not assume USD. Live
versions are PE `#46`, PBV `#47`, PS `#48`, and EV/EBITDA `#49`, each dated
`2026-01-05` with 94 rows. Live coverage is 9 supported, 13 partial, 13
unsupported, 13 typed sources, and 3,163 typed rows. Eleven active typed sources
have complete provenance with no mismatch. At this historical checkpoint, the
remaining destructive typed path was country statistics; the latest checkpoint
above resolves it. Completion remains 75% local-first and 64% world-class.
See `docs/roadmaps/next-20-damodaran-versioned-pricing-and-relative-valuation-checkpoint-2026-08-08.md`.

**2026-08-08 source-backed synthetic-ratings checkpoint:** The WACC service no
longer uses approximate hardcoded rating labels or spreads. A hash-versioned
catalog reproduces all 45 rows from approved `ratings.xls` for large
non-financial, small/risky, and financial-service firms. Exact source
breakpoints, combined Moody's/S&P labels, and default spreads are tested. The
authenticated WACC response exposes the selected band, calculation claim type,
source path/hash, catalog version, unknown source date, low date confidence,
and `User Assumption` recency basis. Legacy `is_large_mfg` callers remain
compatible; conflicting legacy/new firm types fail closed. Operating-lease
capitalization is still not implemented. Coverage is now 4 supported, 18
partial, and 13 unsupported. Full backend validation is 434 tests. See
`docs/roadmaps/next-15-source-backed-synthetic-ratings-checkpoint-2026-08-08.md`.

**2026-08-08 Damodaran application-coverage checkpoint:** The 35-workbook
runtime mirror now has a versioned source/metric registry and authenticated
`GET /data-health/damodaran-coverage` report. It joins canonical aliases,
source dates/confidence, implementation support, physical file presence,
generic import metadata, typed destination tables, live row counts, supported
and missing metrics, freshness, limitations, and corrective actions. The current
local state is honest but incomplete: all 35 files are present, 8 have typed
rows, 2,693 typed records exist, 4 sources are fully supported, 18 are partial,
and 13 are unsupported. Generic workbook parsing does not count as usable
coverage. Validation is 422 backend tests, 90 frontend tests, TypeScript,
production build, four knowledge-base tests, and a clean corpus audit. See
`docs/roadmaps/next-15-damodaran-coverage-checkpoint-2026-08-08.md`.

**2026-08-07 Damodaran knowledge-base checkpoint:** The legacy `Data for
Model/` intake has been reconciled into `damodaran_knowledge_base_v1/`: 38 files
were inspected, 12 exact duplicates were retained as ledger decisions without
extra copies, and 26 unique sources were routed into a 61-file immutable raw
corpus. The source catalog now records canonical paths, as-of dates, date
confidence, usage, and status; a processing ledger preserves every intake
decision. Exact January 2025 debt/dividend regression equations, country-risk
method updates, and workbook architecture references are extracted. A
deterministic audit and four unit tests pass with an empty inbox and no open
review items. The six January 2025 regression models and 26 exact coefficients
now replace the unsupported seed; scoped seeding is idempotent, API/UI inputs
match the source, coefficient drift fails closed, and unusable payout models are
disabled. The user approved the undated `ratings.xls` spread table as a recent
local `User Assumption`; its source date remains unknown and date confidence
remains low. See
`damodaran_knowledge_base_v1/PROCESSING_PLAN.md` and
`damodaran_knowledge_base_v1/review_queue/README.md`.

**2026-08-01 checkpoint:** repository secret/static gates, a measured dashboard
query/latency budget, on-demand evidence-integrity reporting, and five new
authenticated failure/lifecycle browser workflows are implemented. The company
wizard now persists its selected Damodaran industry. Real-source certification
now passes with one reviewed US history and one reviewed India history. See
`docs/roadmaps/next-10-execution-checkpoint-2026-08-01.md`.

**2026-08-01 follow-on:** Docker development now isolates Linux native frontend
modules from the Mac bind mount. Stored-corpus search now includes owner-scoped
alerts, theses, decisions, and valuation models in addition to documents/events,
with type filters, claim labels, timestamps, deep links, GIN indexes, and a
14-query/750-ms local backend budget. See
`docs/roadmaps/next-10-search-execution-checkpoint-2026-08-01.md`.

**2026-08-01 AAPL real-source checkpoint:** Official SEC Company Facts are
stored as a hash-addressed source snapshot. Following explicit user approval,
exactly 24 core FY2022-FY2025 facts were promoted, normalized, and reconciled;
all four periods are trust-ready with zero mismatches. FY2021 was not authorized
and its seven candidates remain `needs_review`. AAPL is now eligible for the US
certification half. See
`docs/roadmaps/aapl-real-source-certification-checkpoint-2026-08-01.md`.

**2026-08-02 Adani Ports real-source completion:** Local company ID `6` is
verified as `ADANIPORTS` / `INE742F01042`. The supplied FY2024-25 and FY2023-24
annual reports are stored with NSE source URLs. All 48 reviewed consolidated
FY2023-FY2025 facts plus three reviewed operating-EBIT calculations are promoted.
The Q1 FY27 presentation is stored as a
supplementary Source Summary and linked to the revised consolidated NSE iXBRL;
it creates no annual certification candidates. Valuation draft `2` records the
2026-08-02 cutoff. FY2023-FY2025 are March-ended, trust-ready, and reconcile
27/27 canonical source metrics exactly. The real-source harness passes with
`certified_count=2` and markets `IN` and `US`. Operating EBIT is explicitly a
`Calculation`, not a reported fact: revenue from operations less operating,
employee, depreciation/amortisation, and other expenses. The existing approved
`Packaging & Container` mapping was preserved as an editable 100% user-assumption
mix; no segment weights were invented.
See `docs/roadmaps/adani-ports-real-source-checkpoint-2026-08-01.md`.

**2026-08-02 statement-identity checkpoint:** Annual source facts now pass
through two explicit accounting checks: profit after tax and profit attribution
to parent plus non-controlling interests. APSEZ passes 6/6 applicable checks
across FY2023-FY2025. AAPL has no applicable checks because its approved fact
set contains only the six certification core metrics; it remains eligible with
an explicit `not_available` limitation rather than false statement-level
assurance. Failed applicable identities block certification, mark actual-based
valuation inputs for review, and appear in company fundamentals and Data Health.
See `docs/roadmaps/next-10-statement-identity-checkpoint-2026-08-02.md`.

**2026-08-02 exact PDF evidence checkpoint:** Financial candidates with trusted
`pdfplumber_top_left_points` geometry now open an authenticated rendered-page
viewer with proportional row or component overlays. Page rendering is limited
to stored assets, scale `0.5`-`2.0`, and 16 million output pixels, with private
`no-store` PNG responses. Unknown, malformed, or out-of-bounds geometry keeps a
visible direct-PDF fallback. Live APSEZ candidate `40` renders document `3`,
page `465` at 893x1170 pixels. See
`docs/roadmaps/next-10-exact-pdf-evidence-checkpoint-2026-08-02.md`.

## 1. What Currently Works
- **Local Infrastructure:** Docker setup for PostgreSQL, FastAPI backend, Next.js frontend, and pgAdmin spins up successfully. `docker-compose.e2e.yml` provides a separate disposable PostgreSQL/backend/frontend stack for authenticated browser tests without touching the normal local database.
- **Database Models:** SQLAlchemy models and Alembic migrations exist for all MVP tables and recent intelligence tracking tables. A fresh database migrates to `j6j6j6j6j6j6`; exact event evidence, AI citation/evaluation, point-in-time source facts, market-price provenance, and revenue-weighted company industry mixes are in the active chain.
- **Core Entity Creation:** The backend correctly handles CRUD operations for Companies, Sources, Raw Documents, Events, Alerts, Thesis Notes, Portfolios, Transactions, Narratives, Evidence, and Macro data.
- **India/US Market Identity:** Companies now carry explicit `market`, `primary_exchange`, `local_symbol`, `isin`, `figi`, and regulatory ID fields. `ticker` remains for display/backward compatibility, but duplicate detection is now based on `(market, primary_exchange, local_symbol)`, allowing the same ticker to exist in US and India contexts.
- **Company Setup Workflow Foundation:** `POST /api/company-setup/start`, `GET /api/company-setup/{company_id}`, `PATCH /api/company-setup/{company_id}/step`, `POST /api/company-setup/{company_id}/resolve-identity`, and `POST /api/company-setup/{company_id}/confirm-identity` track identity, source setup, filing, financial extraction, industry mapping, valuation readiness, and local-only security state. `/companies/{id}/setup` exposes the checklist and US/India source readiness. Industry selection loads asynchronously, falls back to the available country taxonomy with a visible warning when the exact country dataset is absent, persists through company creation, and is protected by an authenticated browser workflow. Valuation setup also supports a persisted revenue-weighted segment mix through `GET/PUT /companies/{company_id}/industry-allocations`; weights must total 100%, each row retains its business-segment label, and missing benchmark coverage blocks only the affected blended prior instead of silently renormalizing the remaining industries. Mapping suggestions require a related profile token, confirmation must match the loaded taxonomy, availability flags come from stored benchmark modules, and manual selection remains available when no reliable suggestion exists. It is a workflow tracker, not full filing extraction automation.
- **India/US Source Capability Matrix:** `GET /api/source-capabilities?market=US|IN` exposes source availability by market. It distinguishes `available`, `manual_only`, `not_configured`, and `not_supported` states so the UI can avoid presenting missing India/US providers as live.
- **Provider and Evidence Health:** `GET /api/providers/health` computes provider readiness for SEC EDGAR, RSS feeds, FRED, market data, AI, OpenFIGI, Damodaran benchmarks, and India manual filings. `GET /api/data-health/evidence-integrity` performs a bounded on-demand audit of timestamps, document/asset links, SHA-256 and byte-size metadata, company consistency, exact text spans/quotes, PDF pages/regions, and low-confidence locators. `/data-health` exposes both reports with corrective links. Dead external URL checks, scheduled execution, and full ownership auditing are not included.
- **Data Page Capability Matrix:** `/data` shows a US/India source capability matrix for company lookup, filings/announcements, fundamentals, market prices, macro/rates, valuation benchmarks, and portfolio/manual entry support.
- **Market-Aware Company Lookup:** `GET /companies/lookup` accepts `market`, `exchange`, and `ticker`. US lookup routes through SEC EDGAR and returns CIK/regulatory identity. India lookup returns existing local companies and otherwise reports that the India provider is not implemented.
- **Market-Aware Market Data Contract:** Market data providers receive `market`, `exchange`, `ticker`, and `currency` and return typed quote/history results with provider symbol, source/observed time, price type, delay, adjustment state, and warnings. `POST /api/market/ingest` is canonical; quote-only `POST /market-prices/fetch-latest` uses the same configured provider and persistence boundary. Stored price/current-quote rows preserve provenance, manual prices remain labeled, and legacy rows are backfilled as `legacy_unknown`; `/market-prices` visibly shows source, provider symbol, timing, adjustment, and warnings. Alpha Vantage fails visibly when unconfigured, `yfinance_personal` is explicit/unofficial with warnings, FMP remains not implemented, and no provider silently falls back to another.
- **Market-Aware Filing Acquisition Workflow:** `GET /api/companies/{company_id}/filings/discover` returns US SEC EDGAR filing candidates or an explicit India manual-only state. `POST /api/companies/{company_id}/filings/manual-link` stores reviewed manual filing links/text. Authenticated `POST /api/companies/{company_id}/filings/pdf` validates and stores an original PDF plus deterministic review candidates. It accepts an official source URL and bounded target page ranges for long reports. `GET /api/companies/{company_id}/filings` and `GET /api/filings/{filing_id}` expose stored filing documents. `/companies/{id}/filings` provides discovery, manual capture, PDF upload, stored-source review, and extraction actions.
- **SEC Filing Picker:** The company detail and Data page SEC controls no longer require a manually selected source. The backend resolves an active SEC source or creates the local `SEC EDGAR` source record, while the UI filters to active CIK-backed US companies and uses a normal labeled checkbox for optional filing-text download.
- **Financial Extraction Candidate Foundation:** Filing text, PDF tables/statement rows, Screener workbooks, and SEC `companyfacts` produce review-gated `financial_extraction_candidates`. Text candidates preserve line/page/section locators; PDF candidates preserve statement page, row/cell references, bounding boxes where available, and explicit component-sum formulas; Screener candidates preserve sheet/row/column/cell coordinates; XBRL candidates preserve concept/unit/period/accession metadata. Trusted PDF row and component geometry opens a rendered source page with proportional highlights; unsupported geometry falls back to the authenticated source PDF. The targeted PDF parser recognizes INR crore/lakh units, consolidated revenue/profit attribution, cash, borrowings, customer bills discounted, leases, NCI, associates, and diluted shares. It does not infer APSEZ operating EBIT. OCR, arbitrary complex-table reconstruction, and broad statement-total validation remain unimplemented.
- **Reviewed Financial Candidate Promotion:** `PATCH /api/financial-line-items/{candidate_id}/review`, `PATCH /api/financial-line-items/{candidate_id}/override`, and `POST /api/companies/{company_id}/financial-statements/mark-reviewed` exist. A non-empty reporting unit is required before review or override. Focused tests cover review, override, reject, missing fiscal years, evidence location, normalized warnings, and reported/derived provenance. Reporting currency persists source and confidence from reviewed units, filing metadata, SEC XBRL units, or visibly warned fallbacks. Conflicting sources block promotion. Promoted candidates remain stored and individually retrievable for audit history but are excluded from the active review queue. A Playwright workflow uploads the deterministic PDF fixture, reviews all 12 candidates, supplies missing share units, promotes them, and verifies 2/2 normalized trust-ready periods plus zero reconciliation mismatches.
- **Durable Valuation Draft Workflow:** `valuation_setup_drafts` persists owned assumptions, per-field provenance, source metadata, warnings, edits, and review acknowledgements before a valuation model exists. Financial actuals older than 550 days and market prices older than 7 days are marked stale and require explicit review; missing market timestamps are marked unknown-freshness. User replacements remove obsolete stale metadata but still require review. Refresh preserves user-edited values, updates unreviewed priors, and invalidates source reviews when values or provenance change. Promotion is atomic and refuses incomplete review. Optional missing `basic_shares` no longer blocks promotion; `diluted_shares` remains required. A Playwright workflow verifies save, reset-to-source, refresh, archive/reopen, review, and model promotion.
- **Country-Aware Valuation Context:** `GET /api/valuation/context/company/{company_id}` returns company market, country, default valuation currency, recommended benchmark country, and warnings about currency/risk-free-rate consistency.
- **Manual Country/Market Rate Context:** `GET /api/market-context?market=US|IN`, `POST /api/market-context/manual`, and `GET /api/valuation/risk-free-rate?currency=USD|INR` support manual country/market macro and risk-free-rate context. No default rates are fabricated. Missing rows return an explicit not-configured envelope.
- **Market-Aware Frontend Company Flow:** Company create/edit UI now captures market, primary exchange, local symbol, ISIN, and regulatory identity. Lookup passes market/exchange context and Indian companies do not show SEC filing automation as available.
- **API Response Envelope:** The robust `{"data", "meta", "errors"}` wrapper (`ApiResponse`) is actively implemented across all JSON FastAPI routes. The executable response inventory reports zero legacy JSON operations and explicitly classifies binary downloads and no-content responses. Backend metadata includes the explicit `is_mock` boolean expected by the frontend data-state contract.
- **Data Pipelines:**
  - RSS ingestion fetches feeds and stores XML items.
  - SEC ingestion fetches filing metadata and text (10-K, 10-Q, 8-K) via SEC EDGAR. Strict `SEC_USER_AGENT` validation is in place.
  - Event extraction parses raw documents into rule-based events.
  - Deterministic event scoring assigns `credibility_score`, `novelty_score`, and `impact_score`.
  - Alert generation runs when priority thresholds are met.
- **Processing Runs Tracking:** SEC/RSS ingestion, PDF/Screener uploads, filing financial extraction, SEC XBRL extraction, and normalized-financial backfill preview/apply attempts use reusable lifecycle helpers and persist counts, status, timestamps, safe errors, metadata, source/company links, and the active request ID. `GET /ingestion/status` exposes the latest detailed runs and correlation field; lifecycle logs include request and run IDs.
- **Frontend Integrity Foundation:** Tailwind 4 utilities compile through PostCSS against project-owned design tokens. Primary navigation is grouped into Today/Portfolio/Research/Data/System with a mobile drawer; company routes share stable workspace tabs; root loading/error/not-found boundaries exist; and the non-functional global search field was removed. Dense navigation disables automatic prefetch to avoid executing every dynamic route tree. Docker isolates `/app/node_modules` and `/app/.next` from the Mac source bind mount and installs dependencies inside Linux before development startup, preventing native Lightning CSS/SWC mismatches. Production build and mobile browser proof pass.
- **Release Baseline:** `.github/workflows/ci.yml` and `scripts/verify_release_baseline.sh` build isolated production images, migrate fresh PostgreSQL, and run backend, frontend, TypeScript, repository-secret, scanner-unit, and project-skill gates. The current verified baseline is 358 backend tests, 70 frontend tests, TypeScript, production build, and 14 isolated Playwright workflows; the accessibility workflow captures 12 desktop/mobile route screenshots.
- **Bounded Raw-Document Lists:** `GET /raw-documents/summaries` and `GET /raw-documents/{id}/summary` return metadata plus `has_raw_text` without serializing full filing bodies. Document, event, research, company, section, and AI list/setup pages use these summaries; a metadata edit cannot erase stored source text.
- **Alert/Event Evidence Contract:** Evidence trails prefer validated `event_evidence_references` with exact text spans, sections, or PDF regions and explicit page/document fallbacks. New PDF regions require finite, in-bounds `pdfplumber_top_left_points` geometry whose page and dimensions match the stored PDF; exact regions render through the authenticated bounded page renderer with a proportional overlay. Text spans must match stored source characters exactly. Data Health previews a bounded historical backfill queue and can create spans only for unique 24-2,000 character case-sensitive matches from event descriptions or the current user's alert evidence; every POST is dry-run by default and recorded as a processing run. Unmatched, ambiguous, conflicting, and missing-candidate rows with stored source text now link to `/events/{id}/evidence-resolution`, where authenticated exact search returns at most 25 matches with at most 300 context characters per side and never returns the full source body. Save rechecks the event/document/company, source content hash, exact offsets, occurrence index, and duplicates under an event-row lock before recording current-user and `manual_exact_resolution` provenance. Legacy page-only or malformed regions remain readable but are downgraded to partial/page-level evidence. The on-demand integrity report detects corrupt stored locators, PDF geometry, and asset metadata but does not repair them automatically.
- **Unified Stored-Corpus Search:** `GET /search/evidence` searches documents, events, owner-scoped alerts, thesis notes, decision logs, and valuation models. Results carry record type, claim type, source label, timestamp, bounded excerpt, deterministic source-priority rank, and an exact workflow link. `type` and `company_id` filters are supported. Documents/events retain exact locators where available; mutable user-authored records are not misrepresented as immutable source evidence. PostgreSQL GIN indexes cover all six domains. Section-level records, research messages, AI outputs, saved queries, and measured large-corpus relevance remain outside this foundation.
- **Portfolio Lifecycle:** Portfolio, holding, transaction, cash, snapshot, valuation, and analytics routes enforce current-user ownership. Missing active-position prices make aggregate market value, P&L, and weights unavailable instead of treating the position as worth zero. The management UI separates opening holdings, security activity, and cash activity.
- **Bounded CSV Interchange:** CSV import/export remains interchange. Separate backup scripts now create and validate a custom PostgreSQL archive, table counts, checksums, and a manifest; the destructive isolated restore drill verifies counts and exact `document_assets` bytes.
- **Advanced Intelligence Modules:**
  - **Damodaran-Style Valuation Agent:** Deeply integrated into the backend and UI. It supports deterministic FCFF DCF, Relative Pricing Benchmarks (Batch 01), Payout Diagnostics / FCFE / DDM integration (Batch 04), Reverse DCF logic, Real Options valuation (Batch 06), macro sensitivity, WACC, and regression-based priors. Assumption autofill has per-field provenance, placeholder flags, broader normalized actual extraction, durable review state, and atomic reviewed promotion. Generated values remain draft inputs until explicitly reviewed. Quick Valuation now uses typed `POST /api/valuation/quick/assumptions` and `POST /api/valuation/quick/calculate` routes; it fails visibly when a baseline cannot be generated, validates critical FCFF inputs, labels output as `Calculation`, and never persists a model, assumption set, or output row.
  - **Macro Sensitivity Ingestion and UI:** Batch 05 is fully implemented across backend and frontend. `macro.xls` and `macrodur.xls` import annual/quarterly macro observations into `macro_series` / `macro_observations`; `macrodur.xls` imports India/SIC sector macro sensitivity benchmarks into `sector_macro_sensitivity_benchmarks` with market, country, classification, and currency context. The Macro Workbench exposes sector sensitivity, macro shock scenarios, bottom-up segment weighting, and top-down company-history regression. Negative raw duration coefficients are preserved and explained instead of rewritten.
- **Damodaran Admin Control Panel:** `/admin/damodaran` records generic workbook parses as inactive `metadata_only` versions and shows source/version provenance. Generic uploads do not create typed benchmarks. Active or typed versions are preserved for auditability; only inactive metadata-only records can be deleted from this screen.
  - **Assumption Methodology Engine:** Fully integrated for dynamic, country-specific valuation priors (e.g. India ERP defaults). Stores provenance for user selections to track whether they overrode defaults or used AI-supplied estimates.
  - Narrative Tracking is actively modeled and functional via the backend API.
  - Thesis Notes track assumptions and drift scores over time.

## 1.5 Security Hardening (Phase 16)
- **Authentication by Default:** The aggregate FastAPI router now requires `get_current_user`. Only `GET /api/health` and `GET /health` are explicitly public application routes. An automated route-security inventory rejects authenticated operations that lose the dependency, and direct-port tests cover unauthenticated read and mutation rejection. The live backend returns `401` for unsigned `/companies` and transfer requests.
- **Owned-Domain Matrix:** User-owned portfolio trees, valuations and drafts, thesis children, alerts/evidence, decisions, research sessions, daily briefs, CSV transfer, and AI outputs resolve or filter through the authenticated owner. Alert creation and daily-brief aggregation/persistence now assign and filter `user_id` explicitly. Cross-user records return `404` or are absent from owned lists. This remains local access control, not public-deployment security.
- **Public Error and Request Contract:** Failed requests return the `ApiResponse` envelope with a stable code, safe message, request ID, retryability, field, provider, and processing-run reference where relevant. `X-Request-ID` is generated or validated at the HTTP boundary. A transitional top-level `detail` field remains for older frontend callers. Raw exception strings and the fixed `/workspace/backend/error.log` path have been removed.
- **Structured Logging:** Backend logs are JSON on stdout and include timestamp, level, logger, message, request ID, and explicitly supplied safe fields. Provider response bodies, prompts, private request bodies, credentials, and raw exception text are not logged.
- **AI Honesty and Privacy Contract:** Migration `b8b8b8b8b8b8` makes AI outputs user-owned and records provider, model, prompt version, SHA-256 input hash, explicit mock state, source IDs/scope, disclosure version, transmitted data classes, transmission scope, limitations, confidence, review metadata, execution status, and safe failure code. Mock output is limited to tests or explicit `AI_DEMO_MODE=true`; provider failure remains failure. Active AI UIs require the versioned disclosure acknowledgement before sending data. Narrative extraction no longer runs automatically during ingestion, and event-to-thesis AI returns proposals instead of writing impacts automatically.
- **Research Child Ownership:** Thesis assumptions/impacts and valuation assumption sets, outputs, scenarios, change logs, diagnostics, reverse DCF, and model deletion resolve through their user-owned thesis note or valuation model. Manual valuation-model creation sets `user_id` explicitly. Cross-user numeric IDs return `404`.
- **Local Authentication**: NextAuth.js uses a JWT session and configured local credentials. Next.js validates browser sessions, then signs a short-lived internal identity assertion for server-rendered and proxied FastAPI requests. FastAPI verifies the HMAC locally, commits first-use user provisioning before protected route work, and never calls the frontend session endpoint. Internal requests have a 15-second timeout so provider or backend failures cannot leave a page rendering indefinitely. Next.js redirects unsigned app-page requests to sign-in. `GET /api/auth/readiness` returns only configured/missing flags and variable names, never credential values, and keeps sign-in disabled until local setup is verified. This is local single-user access control, not a public deployment identity system.
- **API Defense**: `slowapi` installed for global rate limiting to protect expensive backend solvers (e.g., DCF).
- **Endpoint Lockdown**: The Screener.in endpoint accepts `.xlsx` only, enforces a 2MB limit, hashes uploads, rejects duplicates, removes temporary files, creates traceable raw-document/source records, and records a processing-run outcome. It does not persist temporary paths or workbook bytes.
- **PDF Upload and Render Boundary**: Authenticated PDF upload accepts `.pdf` with PDF/octet-stream MIME only, enforces `%PDF-` magic bytes, a 40MB limit, a 1,000-page hard limit, sanitized basenames, company-scoped hashes, duplicate rejection, controlled parser errors, and processing-run outcomes. Full-document scans remain capped at 500 pages; longer reports require at most 75 explicitly targeted pages. Original bytes live in one-to-one `document_assets` rows and stream only through authenticated, `no-store`, `nosniff` endpoints; normal raw-document and asset metadata responses omit bytes. Evidence page rendering accepts only stored pages, scale `0.5`-`2.0`, and at most 16 million pixels.
- **CORS Policies**: Strict origin limits activated in `main.py`.

## 2. What is Mocked (or Hardcoded)
- **Market Regime:** The Market Regime page (`frontend/app/portfolio/regime/page.tsx`) explicitly uses a `<MockDataState>` component warning that "Market Regime data is simulated for this UI prototype."
- **AI Demo/Test Output:** Deterministic mock output is available only under tests or explicit `AI_DEMO_MODE=true`. It is persisted and displayed as `Mock Data`; missing provider configuration returns `AI_PROVIDER_NOT_CONFIGURED` instead of mock success.
- **Score Explanations:** While the backend calculates scores, the frontend does not yet have the full `ScoreBreakdown` UI to explain them cleanly across all endpoints.
- **Assumption Autofill Defaults:** `AssumptionAutofillEngine` still fills some missing fields with generic defaults, but placeholder-derived values are now labeled with `[PLACEHOLDER]`, `requires_review`, and `source_metadata.placeholder_fields`.
- **Financial Currency Fallback:** Reviewed ISO currency units, filing payload currency, and SEC XBRL units drive the financial period currency where available. Company or system currency remains a low-confidence, visibly warned fallback when source data does not identify currency.

## 3. What is Missing
- **Broker Integrations:** There is no evidence of real broker credential syncing (which aligns with the "Explicit Non-Goals").
- **Social/Twitter Scraping:** Not present (also an explicit non-goal).
- **Advanced Microstructure/Real-time trading feeds:** Missing, as expected.
- **Provider-Backed India Rates:** India/US market context supports manual entries only. RBI/FRED-style provider ingestion has not been reviewed or implemented.
- **Representative Real-Source Normalized Financial Coverage:** Canonical normalized storage, coverage, backfill, reconciliation, and annual statement-identity evaluation exist. AAPL FY2022-FY2025 has 24 promoted exact core facts and four trust-ready periods; FY2021 remains outside the approved window. Its narrower approved fact set cannot evaluate the two current identities, so certification records `not_available` as a limitation. APSEZ FY2023-FY2025 has 48 promoted audited statement facts, three promoted operating-EBIT calculations, three trust-ready March-ended periods, 27/27 exact canonical reconciliation checks, and 6/6 passing statement identities. The portable fail-closed manifest passes with two histories and markets `IN` and `US`. This is representative proof, not broad parser certification. Synthetic fixtures remain explicitly `Mock Data` and never load into production tables. `GET /api/companies/{company_id}/financial-statements/normalized/reconciliation` reports source-to-normalized differences; `GET /api/companies/{company_id}/financial-statements/identities` reports formula, inputs, expected value, delta, tolerance, missing facts, duplicate facts, and blocking state.

## 4. Existing Backend Endpoints
Currently, the backend has active routers for a vast array of features, fully utilizing the `ApiResponse` envelope:
- `/alerts`
- `/companies`
- `/api/company-setup`
- `/daily_brief`
- `/data_transfer`
- `/decisions`
- `/events`
- `/evidence`
- `/exposure_tags`
- `/fundamentals`
- `/ingestion` (SEC/RSS)
- `/macro`
- `/api/valuation/macro/data`
- `/api/valuation/macro/bottom-up`
- `/api/valuation/macro/scenario`
- `/api/valuation/macro/sector`
- `/api/valuation/macro/top-down`
- `/api/valuation/context/company/{company_id}`
- `/api/companies/{company_id}/extract-xbrl`
- `/api/companies/{company_id}/financial-statements/extracted`
- `/api/financial-line-items/{candidate_id}`
- `/api/financial-line-items/{candidate_id}/review`
- `/api/financial-line-items/{candidate_id}/override`
- `/api/companies/{company_id}/financial-statements/mark-reviewed`
- `/api/companies/{company_id}/financial-statements/normalized/coverage`
- `/api/companies/{company_id}/financial-statements/normalized/backfill`
- `/api/companies/{company_id}/financial-statements/normalized/reconciliation`
- `/api/companies/{company_id}/financial-statements/identities`
- `/ingestion/status`
- `/companies/{company_id}/industry-mapping-candidates`
- `/companies/{company_id}/industry-mapping`
- `/companies/{company_id}/valuation-models/autofill`
- `/api/market-context`
- `/api/market-context/manual`
- `/api/valuation/risk-free-rate`
- `/manual_processing`
- `/market`
- `/market_prices`
- `/narratives`
- `/oauth`
- `/portfolios`
- `/processing_runs`
- `/raw_documents`
- `/research`
- `/scoring_config`
- `/social`
- `/sources`
- `/api/source-capabilities`
- `/api/providers/health`
- `/thesis_notes`
- `/valuations`
- `/variant_perception`

## 5. Existing Frontend Pages
The vast majority of the frontend app directory appears designed to call real APIs mapping to the backend. Directories include:
- `/companies`
- `/companies/{id}/setup`
- `/companies/{id}/filings`
- `/companies/{id}/fundamentals`
- `/sources`
- `/documents`
- `/events`
- `/alerts`
- `/thesis-notes`
- `/daily-brief`
- `/portfolio`
- `/narratives`
- `/research`
- `/valuation`
- `/admin/damodaran`
- `/macro`
- `/data-health`
- `/settings`

## 6. Current Blockers to Progress
- **Remaining R1 Edges:** Auth, owned domains, transfer, public errors, request/run correlation, structured logging, deterministic hashes, response classification, AI honesty/privacy, citation evaluation, and stored-output review are implemented foundations. Remaining AI trust work is automatic provider citation generation, a larger evaluation corpus, and broader workflow review coverage.
- **Frontend Follow-Through:** Known production `alert()`/`confirm()` calls are removed, and six core routes pass the responsive accessibility baseline. Many legacy pages still rely on inline layout, and the browser matrix does not cover every dynamic or failure path.
- **AI Citation and Review Depth:** Exact declared-source text citation checks, deterministic evaluation fixtures, recommendation-language checks, and owner-scoped approve/reject/revision controls exist. Do not market AI text as verified source-backed research unless its stored citations and evaluation pass; providers do not yet generate complete citations automatically.
- **Exact Evidence Locators:** New event evidence preserves validated text spans, sections, and reproducible PDF regions; pages remain an explicit non-exact fallback. A deterministic preview/apply workflow backfills uniquely matching historical text spans. A separate authenticated resolver now supports bounded exact search and reviewed occurrence selection for unmatched, ambiguous, and conflicting records without exposing full source bodies. Paraphrases, OCR-only sources, and normalized/fuzzy matches still require a different reviewed workflow. Some sources can only support page- or document-level evidence.
- **Financial Review to Valuation Bridge:** Candidate extraction, typed text/PDF/Screener/XBRL locators, PDF-page evidence links, normalized promotion/backfill/reconciliation, two annual accounting identities, broader equity-bridge metrics, durable source-labeled drafts, review persistence, source-age checks, atomic model promotion, and reporting-currency checks exist. AAPL proves the structured path; APSEZ proves a targeted long-report path with auditable EBIT calculations and 6/6 passing identity checks. A failed applicable identity marks company-actual provenance for review and sets valuation trust to `blocked`; partial or unavailable checks remain explicit limitations. Open valuation drafts refresh source-derived values when the normalized financial-history signature changes while preserving reviewed user overrides. OCR, arbitrary complex-table reconstruction, broad total/subtotal validation, and broader accounting mapping remain trust gaps.
- **Provider-Backed India/US Data:** India/US support and honest market-price routing/provenance are structurally present, and provider health is visible on `/data-health`. Representative real-source certification covers one issuer in each market, while India acquisition remains manual and broader country-specific rates, filings, fundamentals, and market data remain manual or not configured. Tiingo and Upstox are not implemented. The UI must keep showing this honestly.
- **Recovery and Operations:** Versioned database/document backup and a destructive isolated restore drill pass checksum, table-count, and exact document-byte verification. Off-device scheduling and encryption remain storage concerns. Browser coverage now includes accessibility, alert evidence, PDF promotion, AI failure disclosure, invalid and valid CSV transfer, mobile navigation, company setup, SEC readiness and deterministic ingestion failure, valuation review invalidation and stale-write recovery, partial portfolio analytics, and valuation draft promotion. Live-provider-dependent behavior, every portfolio mutation, and the full dynamic matrix remain incomplete.

## 7. Explicit Non-Goals (Do Not Build)
- Trading recommendations.
- Twitter, Reddit, or social scraping.
- Production authentication, billing, cloud deployment, or team accounts.
- Vector databases, LangChain, Kafka, Kubernetes, or other heavy infrastructure.
- Broker integrations or broker credential storage.

---

## 8. Prioritized Backlog of Known Issues

### Priority 1: Broaden Real-Source Certification Coverage
- **Issue:** The fail-closed harness now passes for one AAPL and one APSEZ history, but two companies do not establish broad parser or accounting-policy coverage.
- **Fix:** Keep the AAPL/APSEZ pair green and add a second reviewed company per market only after a source-specific extraction path can preserve exact evidence, fiscal dates, units, and reconciliation.

### Priority 2: Backfill Evidence and Expand AI Evaluation
- **Issue:** New exact locators and stored AI review gates work, but historical events lack locator backfill and the deterministic AI corpus is small.
- **Fix:** Backfill locators where source bytes permit it, add provider-generated citation proposals, and expand the evaluation corpus without auto-approving output.

### Priority 3: Broaden Audited Financial Extraction
- **Issue:** Targeted statement-row extraction now supports APSEZ's long consolidated reports, INR crore units, attribution rows, and financing-component sums. OCR, arbitrary merged layouts, statement-total validation, and generic operating/non-operating classification remain unsupported.
- **Fix:** Expand the shipped profit and attribution identities into assets, liabilities/equity, cash-flow movement, and statement total/subtotal checks; add additional reviewed layout profiles. Exact PDF row/component highlighting is now available where stored geometry passes strict bounds. Keep unsupported and low-confidence fields out of promoted valuation inputs.

### Priority 4: Broaden Exact Source Evidence
- **Issue:** Exact financial PDF row/component overlays and event text spans are shipped for supported records, but historical events, event PDF regions, and unsupported source layouts still fall back to page or document level.
- **Fix:** Add safe historical locator backfill and event-region overlays where stored geometry is trustworthy; keep the explicit fallback where it is not.

### Priority 5: Provider-Backed India/US Data Coverage
- **Issue:** Market routing and price provenance are repaired and AAPL/APSEZ pass representative certification, but India financial acquisition remains manual and provider breadth is thin. Tiingo and Upstox adapters do not exist.
- **Fix:** Keep the reference pair green, broaden one reviewed profile at a time, and keep `/data-health` explicit about manual-only, missing-key, unofficial, failing, and not-configured states.

### Priority 6: Broaden Authenticated Browser Workflow Coverage
- **Issue:** Thirteen repeatable isolated workflows cover the major flows listed above. Coverage is still not exhaustive for provider success/rate-limit behavior, every portfolio mutation, long-running ingestion, and all dynamic failure/empty states.
- **Fix:** Extend the disposable Playwright suite one workflow at a time without embedding credentials, touching the normal database, or depending on mutable live-provider responses.

### Priority 7: Alembic Missing Revision Risk
- **Issue:** Users have previously encountered: `Can't locate revision identified by 'a2afaa43a162'`. This breaks local database setup.
- **Fix:** Do not tell users to run destructive commands. Explain how to inspect migration history and either stamp head or restore the missing file safely.

### Priority 8: Docker Socket Permission
- **Issue:** Users may see `permission denied while trying to connect to the docker API at unix:///var/run/docker.sock`.
- **Fix:** Explain that Docker Desktop must be running. On macOS, restarting Docker Desktop usually helps. Do not recommend `sudo chmod 666 /var/run/docker.sock`.

### Priority 9: Frontend/Backend Connectivity
- **Issue:** The frontend may show "backend not reachable" even when containers are running.
- **Fix Checklist:**
  - Are both containers running?
  - Is `NEXT_PUBLIC_API_BASE_URL` properly passed into the frontend container?
  - Is CORS configured on the backend?

---

## Later, Not Now
- Deeper AI summaries or extraction improvements
- Advanced narrative clustering
- Extra data sources beyond SEC/RSS
- Auth, billing, production deployment, or team accounts
- Trading recommendations
- Social scraping
- Live market data, macro APIs, options flow, broker sync, or real-time alerts
