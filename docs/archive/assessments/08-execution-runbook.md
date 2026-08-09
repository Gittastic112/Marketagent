# Execution Runbook & Implementation Checklist

This checklist supersedes older development plans and outlines the strict order of implementation required to align the application with the new frontend and backend design brief. It also serves as a runbook with validation steps.

## Operating Rules & Avoiding Giant Diffs
- **Keep tasks narrow:** Do not rewrite the entire frontend or backend in one go.
- **Incremental PRs/Commits:** Commit after *every* phase. 
- **Explain files touched:** After each phase, output a brief summary of the exact files changed and the manual tests performed.
- **Rollback:** Inspect `git diff` and revert only files changed by the current phase. Never discard unrelated dirty-worktree changes with a broad checkout/reset command.

---

## Phase 0: Audit & Documentation (Completed)
- [x] Audit the current codebase against the design brief.
- [x] Create an execution plan.
- [x] Consolidate and amend all existing markdown documents.

## Phase 1: Stabilize local dev
- [x] Ensure Docker startup works flawlessly.
- [x] Confirm Alembic migration chain is unbroken and local DB spins up.
- [x] Add `GET /api/health` endpoint and verify backend health.
- **Validation:** Run `docker compose up --build -d`. Visit `http://localhost:8000/api/health`.
- **Checkpoint Command:** `git add . && git commit -m "chore: stabilize local dev and add healthcheck"`

## Phase 2: API Response Envelope
- [x] Add the standard `{"data", "meta", "errors"}` response envelope schema to the backend.
- [x] Refactor all existing FastAPI routes to use this envelope.
- [x] Update frontend `fetchApi` client to parse this envelope.
- **Validation:** Write unit tests to confirm the `{"data", "meta", "errors"}` wrapper correctly wraps success and error responses. Verify frontend `fetchApi` parses it correctly without white-screening.
- **Checkpoint Command:** `git add . && git commit -m "feat: standard api response envelope"`

## Phase 3: Processing Runs and Ingestion Status
- [x] Create `processing_runs` table and models.
- [x] Update SEC and RSS services to track ingestion health to `processing_runs`.
- [x] Create `GET /api/ingestion/status` endpoint.
- **Validation:** Trigger an SEC or RSS fetch. Query the DB or check the `GET /api/ingestion/status` endpoint to ensure the run was logged successfully.
- **Checkpoint Command:** `git add . && git commit -m "feat: processing runs tracking"`

## Phase 4: SEC User-Agent and CIK Lookup
- [x] Add `SEC_USER_AGENT` environment variable validation.
- [x] Create `GET /api/sec/company/{ticker}/cik` endpoint.
- **Validation:** Remove the `SEC_USER_AGENT` from `.env` and verify the ingestion fails gracefully with a standard error. Put it back and verify success.
- **Checkpoint Command:** `git add . && git commit -m "feat: sec user agent and cik lookup"`

## Phase 5: Frontend App Shell
- [x] Build the new global `Sidebar` and `TopBar`.
- [x] Implement global page layout components.
- [x] Add basic Next.js routing for the new folder structure.

## Phase 6: Dashboard
- [x] Build the Daily Intelligence Brief UI.
- [x] Connect dashboard to backend events/alerts.
- [x] Add ingestion health summary.
- [x] Add portfolio concentration warnings.

## Phase 7: Portfolio Page
- [x] Build Holdings table and Portfolio summary cards.
- [x] Connect to existing portfolio backend routes.

## Phase 8: Company Intelligence Page
- [x] Build the individual `companies/[ticker]` view.
- [x] Add Ticker Header, Metric Cards, and SEC filings timeline.
- [x] Add Market Data header and Financial Trends.

## Phase 9: Narrative Page
- [x] Create backend models and endpoints for Narratives.
- [x] Build Narrative tracking UI and evidence timelines.

## Phase 10: Scoring Breakdown
- [x] Create backend models and endpoints for expanded Score types.
- [x] Build the `ScoreBreakdown` UI component to explain score formulas.
- [x] Integrate visual weighted bar chart into Events page.

## Phase 11: Valuation Agent (MVP & Expansion)
- [x] Create backend models and endpoints for Valuation Cases (`models/dcf.py`).
- [x] Build the frontend DCF UI (Assumptions, Scenarios, Sensitivity tables).
- [x] Implement Assumption Autofill from Damodaran Industry Benchmarks (Batch 02).
- [x] Integrate Relative Pricing Benchmarks (Batch 01).
- [x] Build FCFE, DDM, and Payout Policy Diagnostics (Batch 04).
- [x] Build Reverse DCF solving logic.
- [x] Start Batch 05 ingestion: import `macro.xls`, `macrodur.xls`, and SIC-level sector macro sensitivity benchmarks.
- [x] Expose Batch 05 read endpoints for filtered macro observations and SIC-level sector sensitivity benchmarks.
- [x] Translate user macro shocks into deterministic sector-level value and operating-income impact estimates.
- [x] Build top-down macro sensitivity regression for company history.
- [x] Build bottom-up segment-weighted macro sensitivity.
- [x] Add market/country context to Batch 05 sector macro benchmarks, scenarios, and bottom-up services.
- [x] Build Batch 05 UI panels and Real Options (Batch 06).

## Phase 12: Research Workspace
- [x] Create backend models for Research Sessions and Messages.
- [x] Build the source-backed AI workspace UI.

## Phase 13: Data Health Page
- [x] Build the Data Health page UI showing API connections and ingestion statuses.
- [x] Show recent processing runs with success/failure counts.
- [x] Show ingestion freshness per source type.

## Phase 14: Polish & Finalize
- [x] Add Error, Empty, Stale, and Loading states globally.
- [x] Perform final security checks (prevent secret leakage).
- [x] Clean up any remaining known issues.
- **Validation:** Run automated security checks (SSRF prevention, CSV escaping, no secrets logged). Ensure relevant known issues in `docs/00-current-state.md` and `docs/agent_capabilities_and_limitations.md` have been addressed.
- **Checkpoint Command:** `git add . && git commit -m "chore: final polish and security hardening"`

## Phase 15: India/US Platform Transition
- [x] Add market-aware company identity columns and relax global ticker uniqueness.
- [x] Add source capability matrix for US vs India features.
- [x] Route company lookup through market-aware providers.
- [x] Upgrade market data provider contract to carry market/exchange/currency context.
- [x] Split filing ingestion/readiness by US SEC vs India manual/not-configured sources.
- [x] Add country-aware valuation context endpoint.
- [x] Make backend macro context market-aware.
- [x] Make frontend company forms and macro UI market-aware.
- [x] Add manual country/market macro and risk-free-rate context endpoints.
- **Validation:** Run `pytest backend/tests/test_country_market_context.py backend/tests/test_macro_country_context.py backend/tests/test_api_macro_sensitivity.py backend/tests/test_filing_provider_routing.py backend/tests/test_valuation_country_context.py backend/tests/test_company_lookup_providers.py backend/tests/test_market_data_market_context.py backend/tests/test_source_capabilities.py backend/tests/test_company_market_identity.py backend/tests/test_api_crud.py -q` and verify Alembic reaches the latest head.

---

## Phase 16-20: Damodaran Valuation Master Build Plan
- [x] The core `docs/valuation-agent/master-build-plan.md` valuation engine work is substantially implemented and verified across the backend suite. This covers comprehensive DCF modeling, FCFE/DDM, payout diagnostics, reverse DCF workflows, real options, regression-based macro priors, and Damodaran data administrative controls.
- [ ] Newer automation around reviewed financials, normalized financial snapshots, source-grounded assumption autofill, and end-to-end valuation automation still needs hardening. Use `docs/roadmaps/valuation-auto-pipeline-master-plan.md` for that roadmap and verify against code before implementing.

## Phase 21: Financial Trust Bridge
- [x] Add line/page/section evidence and warning codes to extraction candidates.
- [x] Require reporting units before review or override.
- [x] Persist valid source/raw-document/content-hash/processing-run records for Screener `.xlsx` uploads.
- [x] Add normalized coverage and before/after backfill reporting.
- [x] Expose coverage gaps and currency confidence on company fundamentals.
- [x] Add valuation source-age diagnostics and explicit stale-source review.
- [x] Add non-secret local-auth readiness and block sign-in until checked.
- [x] Run an authenticated major-route smoke plus company setup, SEC picker/import,
  and complete portfolio create-to-cleanup lifecycle after local credentials are
  configured.
- **Validation:** Financial trust behavior remains covered by the current full-suite baseline below. AAPL FY2022-FY2025 now has four trust-ready normalized periods and exact reconciliation; Adani remains an honest `no_data` normalized state while its candidates await review.

### Normalized Coverage Procedure
1. Read `GET /api/companies/{company_id}/financial-statements/normalized/coverage`.
2. If `status` is `blocked`, resolve each currency conflict before writing.
3. Run `POST /api/companies/{company_id}/financial-statements/normalized/backfill` with `{"dry_run": true}`.
4. Review `coverage_before`, `eligible_periods`, and `skipped_conflicts`.
5. Apply with `{"dry_run": false}` only when the preview is acceptable.
6. Verify `coverage_after`, especially `trust_ready_period_count`; 100% normalized coverage does not imply 100% trust readiness when currency confidence is low.

## Phase 22: PDF Filing Evidence Foundation

- [x] Add authenticated PDF upload with extension, MIME, magic-byte, 40MB,
  1,000-page, basename, digest, and duplicate controls. Require target page
  ranges above 500 pages and cap targeted scans at 75 pages.
- [x] Store one original binary `DocumentAsset` per `RawDocument` without
  serializing bytes through metadata endpoints.
- [x] Extract text-based tables and statement rows into review-gated candidates,
  including INR crore/lakh units, attribution rows, and reported component sums.
- [x] Preserve page/table/row/column, statement-line references, formulas, and
  table/cell bounding boxes where available.
- [x] Store optional official source URLs and keep investor presentations out of
  annual-period classification.
- [x] Link review to the authenticated original PDF page.
- [x] Record success, duplicate, validation, and parser outcomes in
  `ProcessingRun`.
- [x] Add deterministic PDF fixture, visual render check, backend API tests,
  frontend evidence-link tests, and security documentation.
- [x] Run PDF upload/review/promote in an isolated authenticated browser,
  including missing-unit overrides, normalized coverage, and reconciliation.
- [x] Add bounded rendered-page row/region overlays for supported financial and
  event evidence, with authenticated source-PDF fallbacks.
- [ ] Add broader complex-layout profiles and statement-total reconciliation.
  The APSEZ profile is staged but its operating EBIT still requires review.
- **Validation:** Expected migration head is `a7a7a7a7a7a7`; the latest full
  backend suite is 307 tests with 4 third-party openpyxl deprecation warnings;
  the frontend suite is 60 tests. TypeScript typecheck, production build,
  two isolated authenticated Playwright workflows, dependency audit, and live
  backend health pass.
  See `docs/roadmaps/pdf-financial-extraction-checkpoint-2026-07-25.md`.

---

## Next Steps
All MVP baseline phases and the main valuation expansions are broadly in place, but some newer automation remains partial. Future development should refer to `docs/HANDOFF.md`, `docs/agent_capabilities_and_limitations.md`, and `docs/roadmaps/market-intelligence-build-roadmap.md` to define the next major milestone.

## Phase 23: Setup, Ingestion, and Portfolio Hardening

- [x] Restore company-setup industry choices with explicit country-taxonomy fallback.
- [x] Make SEC source selection optional and resolve/create the SEC source server-side.
- [x] Repair the SEC filing-text checkbox and selected-filing import state.
- [x] Propagate authenticated ownership through ingestion-created alerts.
- [x] Bound SEC-derived event/alert summaries and keep full evidence in raw documents.
- [x] Add raw-document summary endpoints and migrate collection/picker reads.
- [x] Scope portfolio parents and child routes to the current user.
- [x] Treat missing active-position prices as unavailable, not zero.
- [x] Separate opening holdings, security activity, and cash activity in the UI.
- [x] Complete an authenticated portfolio create-to-cleanup browser lifecycle.
- [x] Smoke all major authenticated pages and isolate first-compile timeouts.
- [x] Add repeatable isolated browser automation for valuation draft and PDF review/promotion.

**Validation:** Follow
`docs/roadmaps/setup-ingestion-portfolio-hardening-checkpoint-2026-07-25.md`.

---

## Phase 24: Browser and Representative-History Hardening

- [x] Add a disposable tmpfs PostgreSQL/backend/production-frontend E2E stack.
- [x] Prove a fresh database migrates to `a7a7a7a7a7a7` and repair duplicate
  normalized-table operations plus the missing event-thesis table migration.
- [x] Remove the temporary runtime DDL endpoint.
- [x] Add synthetic, explicitly `Mock Data` US and India three-period histories.
- [x] Verify normalization, trust readiness, reconciliation, CAGR, and valuation
  autofill for both histories.
- [x] Keep optional missing `basic_shares` outside the promotion review gate.
- [x] Upgrade Next/NextAuth patches and override vulnerable transitive PostCSS
  and sharp releases; `npm audit` reports zero known vulnerabilities.
- [x] Repeat the same coverage with a reviewed real-source US history (AAPL
  FY2022-FY2025).
- [ ] Complete the staged India history (Adani Ports FY2023-FY2025) before
  removing compatibility fallbacks or raising extraction confidence.

---

## Phase 25: Alert Evidence and Living Product Register

- [x] Replace ad-hoc event evidence ORM serialization with a typed summary contract.
- [x] Require authentication for event evidence.
- [x] Add a user-owned alert evidence endpoint.
- [x] Filter thesis and valuation impacts through current-user parents.
- [x] Close direct child-ID ownership gaps in thesis-assumption/impact and
  valuation model/assumption/output/change-log routes.
- [x] Exclude raw filing text, provider payloads, and document bytes.
- [x] Return claim type, confidence, source timestamp, evidence status, bounded
  claim context, and locator precision.
- [x] Add document, original-source, and stored-PDF links.
- [x] Add a bounded historical event-evidence preview/apply queue with unique
  exact-match rules, user-scoped alert evidence, dry-run defaults, event locks,
  duplicate rechecks, and processing-run provenance.
- [ ] Manually resolve unmatched, ambiguous, and conflicting historical events;
  do not broaden the scanner to fuzzy matching to inflate coverage.
- [x] Rebuild the evidence drawer with loading, error, partial, missing, and
  limitation states.
- [x] Add the missing `/alerts/{id}` review route and use alert ownership from
  alert UI entry points.
- [x] Add focused backend ownership/leakage tests and frontend contract tests.
- [x] Start
  `docs/roadmaps/world-class-product-ideation-register.md` as the active
  shipped/partial/proposed feature register.
- [x] Persist exact page/section/span locators on events and highlight the
  supporting source passage.
- [x] Add an isolated alert-evidence browser spec for complete and missing
  evidence states.
- [x] Execute that spec against a freshly rebuilt frontend image.

**Focused validation:**

```bash
docker compose exec backend pytest -q backend/tests/test_api_evidence_trails.py
cd frontend
npm test
npm run typecheck
```

---

## Testing Checklist (Pre-Commit)
Before any commit, ensure:
1. `docker compose logs backend` shows no Python stack traces.
2. Migrations are up to date (`alembic upgrade head`).
3. No environment variables or API keys have been hardcoded.
4. The frontend compiles without fatal Next.js errors.

---

## Phase 26: Product Integrity and Release Baseline

- [x] Persist validated request IDs on processing runs and emit correlated
  lifecycle logs.
- [x] Add executable response-contract classification with zero legacy JSON
  operations.
- [x] Compile Tailwind utilities through PostCSS and establish project-owned
  design tokens.
- [x] Add grouped responsive navigation, company workspace tabs, and root route
  boundaries.
- [x] Disable dense navigation prefetch to prevent unintended dynamic-route
  execution and database fan-out.
- [x] Add bounded configurable SQLAlchemy pool capacity for normal render bursts.
- [x] Replace research provider `alert()` failure handling with inline preserved
  state and correct CSV envelope error parsing.
- [x] Add isolated browser coverage for mobile navigation, AI disclosure/failure,
  and CSV row-error recovery.
- [x] Add clean release verification and GitHub Actions CI.
- [x] Complete database/document backup and a destructive restore drill in a
  disposable environment.
- [x] Add automated accessibility and responsive screenshot gates.
- [x] Add deterministic repository secret scanning, scanner unit tests, and
  project-skill/static integrity gates to local release verification and CI.
- [x] Enforce a representative dashboard budget of 20 SQL statements and
  1,000 ms backend generation time.
- [x] Add an authenticated on-demand evidence-integrity API and Data Health UI.
- [x] Persist company-wizard Damodaran mapping and verify create-to-workspace.
- [x] Add deterministic SEC readiness/failed-ingestion, valid CSV
  preview/apply/export, stale valuation write, review invalidation, and partial
  portfolio analytics browser workflows.

**Verified 2026-08-01:** 355 backend tests, 68 frontend tests, TypeScript,
production build, static repository gates, and all 13 isolated Playwright
workflows passed. The browser suite ran once as a complete disposable-stack
matrix. New workflows do not call mutable live providers; the failed RSS case
uses the production SSRF boundary deterministically. Evidence integrity is on
demand and bounded, not a scheduled repair process.

**Verified 2026-07-31:** backup/restore checksums, table counts, and exact
document bytes passed in isolation; 352 backend tests, 67 frontend tests,
TypeScript, and all 8 isolated Playwright workflows passed. The accessibility
workflow captured 12 route screenshots. Current Alembic head is
`g3g3g3g3g3g3`. At that historical checkpoint, real-source US/India
certification remained blocked at zero histories; Phase 30 supersedes this.

**Verified 2026-07-26:** Alembic `c9c9c9c9c9c9`; 336 backend tests; 65
frontend tests; TypeScript and production build pass; 3 product-integrity
Playwright workflows pass; clean isolated release baseline passes. Four
openpyxl Python 3.14 deprecation warnings remain third-party noise.

## Phase 27: Cross-Platform Frontend and Stored-Corpus Search

- [x] Isolate Linux frontend native modules and `.next` output from the Mac
  source bind mount; install dependencies inside the development container.
- [x] Repair decision-log creation so `company_id` reaches persistence and is
  validated before insert.
- [x] Expand typed search results to owned alerts, theses, decisions, and
  valuation models.
- [x] Enforce owner filters on every user-authored search domain.
- [x] Add result-type filtering, claim labels, source labels, timestamps,
  bounded excerpts, and deep workflow links.
- [x] Add PostgreSQL GIN indexes for the four added domains at migration head
  `h4h4h4h4h4h4`.
- [x] Bound search to 14 SQL statements and 750 ms locally; report timing in
  response metadata.
- [x] Normalize mixed legacy aware/naive model timestamps to UTC at the search
  boundary.
- [x] Add ownership, filtering, ranking, timestamp, and query-budget tests.
- [x] Add an authenticated production-stack browser workflow for cross-domain
  search and filtering.

**Verified 2026-08-01:** 358 backend tests, 70 frontend tests, TypeScript,
production build, one Alembic head at `h4h4h4h4h4h4`, and all 14 isolated
Playwright workflows pass. The accessibility gate audits the stable DOM after
React server-stream hydration instead of transient hidden transport nodes.

## Phase 28: Market Provider Routing And Provenance

- [x] Replace the direct yfinance route bypass with configured provider routing.
- [x] Define typed market request, quote, history, and provider-error contracts.
- [x] Make `yfinance_personal` explicit and visibly unofficial.
- [x] Make Alpha Vantage fail with stable missing-key, symbol, rate-limit,
  timeout, upstream, and invalid-response errors.
- [x] Reject unknown providers instead of silently selecting Alpha Vantage.
- [x] Keep FMP visibly not implemented.
- [x] Remove database writes from provider adapters.
- [x] Centralize quote/history persistence and company-identity validation.
- [x] Persist provider symbol, venue, currency, timestamps, price type, delay,
  adjustment state, and warnings on prices and current quotes.
- [x] Preserve manual-price behavior and label migrated rows `legacy_unknown`.
- [x] Record quote and quote/history ingestion processing-run outcomes.
- [x] Expose provenance through price, quote, and history schemas and render it
  on the market-price page.
- [x] Name `POST /api/market/ingest` as canonical and retain the quote-only
  compatibility route.
- [x] Replace the empty provider test with deterministic mocked tests.
- [x] Add route-level success, provenance, and stable-failure tests.
- [x] Add explicit provider-health behavior for personal yfinance use.
- [x] Upgrade the database to migration `i5i5i5i5i5i5`.
- [x] Pass 20 focused market/provider tests and all 367 backend tests.
- [x] Pass 73 frontend tests, TypeScript, the production build, and all six
  isolated product-integrity browser tests.
- [x] Verify the live backend health endpoint returns `200 OK`.
- [x] Reconcile environment examples, current-state docs, ingestion docs, and
  the provider roadmap without claiming Tiingo, Upstox, or certification exists.

**Known limitation:** Ruff is not installed in the backend image. Python
compilation, the repository secret scan, and the listed tests pass, but this
phase has no Ruff result. The full suite reports four third-party `openpyxl`
Python 3.14 deprecation warnings.

**Next gate:** Keep the AAPL/APSEZ certification pair green while broadening
source coverage and exposing industry-mix benchmark completeness.

## Phase 29: Representative Real-Source Certification

- [x] Repair SEC annual comparative selection and exact XBRL locator validation.
- [x] Promote exactly 24 user-approved AAPL FY2022-FY2025 core facts.
- [x] Preserve all seven AAPL FY2021 candidates as `needs_review`.
- [x] Verify four AAPL trust-ready periods and zero source/normalized mismatches.
- [x] Add bounded long-report PDF page targeting and official source URLs.
- [x] Stage APSEZ FY2023-FY2025 from two consolidated annual reports with NCI,
  associates, leases, and explicit debt component sums.
- [x] Store the Q1 FY27 presentation as supplementary evidence and link the
  revised consolidated NSE iXBRL.
- [x] Record valuation cutoff `2026-08-01` in Adani draft `2`.
- [x] Remove the invalid alphabetical industry fallback, validate mappings
  against the loaded taxonomy, report real benchmark coverage, and preserve
  valuation cutoff/source metadata across draft refreshes.
- [x] Reconstruct FY2023-FY2025 operating EBIT as reviewed calculations with
  explicit components and non-operating exclusions.
- [x] Promote, normalize, reconcile, and certify the India representative.
- [x] Correct APSEZ annual report dates to March 31 and source-fact effective dates.
- [x] Add persisted revenue-weighted segment-to-industry allocations with a
  strict 100% total and fail-closed missing benchmark behavior.

**Current result:** two eligible histories representing `IN` and `US`; overall
status is `passed`. APSEZ has three trust-ready periods, 51 exact reviewed
evidence rows, and 27/27 exact canonical reconciliation checks. The preserved
100% industry row remains a user assumption and should be replaced with actual
segment weights when available.

**Verified 2026-08-02:** 383 backend tests, 75 frontend tests, TypeScript, and
the Next.js webpack production build pass. Four
`openpyxl` deprecation warnings remain upstream and do not affect results.

## Phase 30: Portable Certification, Financial Integrity, and Weighted Mix UX

- [x] Add a stable-identity/hash certification manifest and resolver with
  fail-closed uniqueness checks.
- [x] Prove the APSEZ finalizer remains idempotent under strict same-page EBIT
  component validation.
- [x] Expose per-industry module and blended-field benchmark coverage.
- [x] Persist an optional company-owned source document for segment weights.
- [x] Preserve user overrides while refreshing open drafts after normalized
  financial history changes.
- [x] Extend Data Health with promoted-fact locator, fiscal-period, and
  source/stored period-end checks.
- [x] Derive current eligible-history counts and `IN`/`US` certification status
  in Data Health.
- [x] Add an authenticated weighted-mix/source-provenance Playwright workflow;
  compilation and test discovery pass, browser execution remains pending.
- [x] Reconcile current-state, architecture, schema, runbook, handoff,
  certification checkpoints, roadmap, and ideation register.

**Verified 2026-08-02:** 391 backend tests, 75 frontend tests, TypeScript,
webpack production build, secret scan and scanner tests, 11 project-skill
checks, `git diff --check`, and Alembic head `j6j6j6j6j6j6` pass. The portable
AAPL/APSEZ manifest passes live. Data Health reports 75 promoted facts, seven
annual periods, two eligible histories, certified markets `IN` and `US`, and no
financial integrity issue. The AAPL SEC Company Facts snapshot has no single
document-level publication timestamp, so one freshness warning remains even
though each certified XBRL locator carries its filed date.

The first guarded repair corrected document `3` from three scanned pages to 673
physical pages and document `4` to 609 physical pages. The immediate second run
reported `asset_page_count_corrections=0`, proving repair idempotency.

## Phase 31: Financial Statement Identities and Inspectable Certification

- [x] Define an absolute/relative tolerance contract for accounting identities.
- [x] Evaluate profit-after-tax and parent/NCI attribution by annual period.
- [x] Fail duplicate required facts and arithmetic mismatches closed.
- [x] Expose authenticated company identity results with formula inputs and delta.
- [x] Render period-level checks on company fundamentals.
- [x] Block financial-history certification on failed applicable identities.
- [x] Expose per-history gate details and limitations in Data Health.
- [x] Propagate identity failure into valuation draft review metadata and warnings.
- [x] Verify the portable AAPL/APSEZ certification report against live local data.
- [x] Reconcile current-state, architecture, handoff, roadmap, and register.

**Verified 2026-08-02:** APSEZ passes 6/6 applicable checks across three annual
periods. AAPL reports zero applicable and eight unavailable checks because its
approved fact set does not include pretax, tax, or attribution rows. The
portable two-market report still passes and now records that limitation.
Validation is 397 backend tests, 76 frontend tests, clean TypeScript, and a
successful Next.js 16.2.11 webpack production build. Data Health reports no
blocking error and one pre-existing AAPL source-timestamp warning.

## Phase 32: Exact Financial PDF Evidence Overlay

- [x] Pin `pypdfium2` and Pillow as direct backend runtime dependencies.
- [x] Add authenticated stored-page PNG rendering.
- [x] Bound scale to `0.5`-`2.0` and output to 16 million pixels.
- [x] Register PNG output in the explicit binary response-contract inventory.
- [x] Test PNG signature/dimensions, auth, invalid pages, scale, and headers.
- [x] Validate finite top-left point geometry and page bounds in the frontend.
- [x] Support single reported rows and multi-row component sums.
- [x] Add the `/documents/{id}/financial-evidence` source viewer.
- [x] Route trusted financial candidates to overlays and retain source fallback.
- [x] Verify an APSEZ promoted candidate and reconcile trust documentation.

**Verified 2026-08-02:** APSEZ candidate `40` renders document `3`, page `465`
as a 260,741-byte, 893x1170 PNG at scale `1.5`. Backend validation is 397
tests; frontend validation is 80 tests, clean TypeScript, and a successful
Next.js 16.2.11 webpack production build. Browser automation was not executed
in this batch.

## Phase 33: Quick Valuation Repair and Manual Exact Event Evidence

- [x] Replace the Quick Valuation UI's unregistered routes with typed backend
  baseline and calculation endpoints.
- [x] Remove hardcoded fallback assumptions after baseline failure.
- [x] Validate projection, growth, margin, reinvestment, WACC, terminal, bridge,
  diluted-share, and market-price inputs before calculation.
- [x] Keep Quick Valuation transient and prove that it creates no valuation,
  assumption-set, or output rows.
- [x] Add bounded exact search for an event's linked stored source text.
- [x] Return no more than 25 occurrences and 300 context characters per side;
  never return the full source body.
- [x] Add a dedicated resolver page and Data Health links for manual rows.
- [x] Revalidate source hash, event/document/company consistency, exact offsets,
  quote, occurrence index, and duplicate state under an event lock.
- [x] Record current-user and `manual_exact_resolution` provenance.
- [x] Cover changed-source, duplicate, bounds, missing-source, mismatch,
  provenance, UI contract, API envelope, and route-authentication behavior.

**Verified 2026-08-07:** 412 backend tests and 87 frontend tests pass. TypeScript
and the Next.js 16.2.11 webpack production build pass inside the Linux frontend
container. Browser automation and screenshot comparison were not run in this
batch. Exact search does not support fuzzy matching, whitespace normalization,
OCR-only documents, or arbitrary range expansion.

## Phase 34: Damodaran Coverage and Source-Backed Synthetic Ratings

- [x] Inventory all 35 mirrored Damodaran workbooks against canonical sources.
- [x] Separate typed rows from generic metadata-only parsing.
- [x] Expose coverage, freshness, limitations, and required action in Data Health.
- [x] Extract all 45 rating/default-spread rows from approved `ratings.xls`.
- [x] Bind the catalog version to the canonical source SHA-256.
- [x] Support large non-financial, small/risky, and financial-service tables.
- [x] Preserve exact breakpoint, rating-label, and spread behavior in tests.
- [x] Keep the legacy `is_large_mfg` input compatible.
- [x] Reject conflicting legacy and explicit firm-type inputs.
- [x] Return selected-band and source provenance from the WACC endpoint.
- [x] Preserve unknown source date, low date confidence, and user-assumed recency.
- [x] Keep operating-lease capitalization as an explicit limitation.

**Verified 2026-08-08:** 434 backend tests and 90 frontend tests pass. TypeScript
and the Next.js 16.2.11 production build pass. The four knowledge-base tests and
corpus audit pass with 61 canonical files, 61 catalog rows, 38 processing rows,
and an empty inbox. Both workbook copies match the catalog hash. `git diff
--check` passes.

## Phase 35: Damodaran Dataset Versions and Exact ROE

- [x] Add source SHA-256, byte size, as-of date, date confidence, canonical path,
  import kind, active/superseded lifecycle, and row count to dataset versions.
- [x] Add firm count and R&D-adjusted ROE to the ROE benchmark schema.
- [x] Preserve prior Capex and ROE typed rows when source bytes change.
- [x] Verify same-hash imports against stored row counts without duplication.
- [x] Reactivate a known historical hash without creating a third copy.
- [x] Parse all 94 non-aggregate `roeIndia.xls` industries exactly.
- [x] Preserve workbook `NA` values as null and leave ROC/ROIC unset.
- [x] Restrict assumption and industry mapping readers to active dataset IDs.
- [x] Expose active source/hash/version state in Data Health and admin history.
- [x] Keep generic admin parsing explicitly inactive and metadata-only.
- [x] Block deletion of active or typed version history from the admin route.
- [x] Add `--only` to the operator script to prevent unrelated source refreshes.
- [x] Apply Alembic head `k7k7k7k7k7k7` to the local database.
- [x] Load Capex and ROE live and prove a second ROE import is idempotent.
- [x] Reconcile architecture, schema, ingestion, runbook, handoff, coverage,
  product register, and knowledge processing documentation.

**Verified 2026-08-08:** active ROE version `#40` has SHA-256
`5608b78e268d7100c6d1ce171b8ee31913317158f22305cb6316d445cb4b675d`,
source date `2026-01-05`, and 94 rows. Active Capex version `#39` also has 94
rows. Live coverage is 5 supported, 17 partial, 13 unsupported, 9 typed sources,
and 2,787 typed rows. Nineteen focused tests, all 439 backend tests, all 90
frontend tests, TypeScript, and the Next.js 16.2.11 production build pass.

**Known limitation at Phase 35 completion:** only Capex and ROE used the
preserved-version service, and five active legacy dataset records lacked
complete provenance. Phase 36 below supersedes that current-state limitation.

## Phase 36: Versioned Margin, Working Capital, Dividend, and FCFE

- [x] Inspect exact runtime/canonical workbook hashes, headers, dates, and rows.
- [x] Replace permissive Margin matching with exact source columns, including
  `Pre-tax Unadjusted Operating Margin`.
- [x] Replace permissive Working Capital and Dividend matching with exact source
  fields and firm counts.
- [x] Correct FCFE semantics to the source's before-debt and after-debt
  aggregates without manufacturing component fields.
- [x] Add migration `l8l8l8l8l8l8` for firm counts and exact FCFE aggregates.
- [x] Move all four importers to `DamodaranDatasetVersionService`.
- [x] Fail closed before metadata creation on missing headers; roll back empty
  typed imports.
- [x] Restrict industry names and countries to active dataset IDs.
- [x] Add source-value, contract, rollback, idempotency, coverage, mapping, and
  migration tests.
- [x] Apply the migration and run each live importer twice.
- [x] Reconcile Data Health inventory version, coverage metrics, and limitations.
- [x] Reconcile current-state, handoff, architecture, schema, ingestion,
  limitations, product status/register, and knowledge-base processing docs.

**Verified 2026-08-08:** active versions are Margin `#41`, Working Capital
`#42`, Dividend `#43`, and FCFE `#44`; all are dated `2026-01-05` and contain 94
rows. Two consecutive scoped imports retained the same IDs, hashes, and row
counts. Active Capex remains `#39` and ROE remains `#40`. Live coverage remains
5 supported, 17 partial, 13 unsupported, 9 typed sources, and 2,787 typed rows.
Active provenance is complete for six sources, missing for one, and has zero
mirror-hash mismatches. Validation passes 32 focused tests, 452 backend tests,
90 frontend tests, TypeScript, the Next.js 16.2.11 production build, four
knowledge-base tests, and the knowledge-base audit.

**Known limitation at Phase 36 completion:** volatility was the active
provenance-missing source and lacked a dataset-version foreign key. Phase 37
below supersedes that current-state limitation. The FCFE component limitation
remains unchanged.

## Phase 37: Versioned Volatility and Honest Real-Options API

- [x] Verify runtime/canonical `optvarIndia.xls` hashes and exact source rows.
- [x] Pin six industry headers, two workbook assumptions, source date, nulls,
  zeros, and representative values.
- [x] Add migration `m9m9m9m9m9m9` with a nullable legacy-compatible version FK.
- [x] Preserve unproven legacy rows without exposing them as active evidence.
- [x] Convert volatility to `DamodaranDatasetVersionService`.
- [x] Fail closed before metadata creation on missing columns or assumptions.
- [x] Preserve changed hashes and reactivate known historical versions.
- [x] Count only active linked volatility rows in Data Health.
- [x] Expose source/version provenance from the volatility API.
- [x] Preserve legitimate zero and null cells instead of applying `or` fallbacks.
- [x] Return `VOLATILITY_BENCHMARK_NOT_FOUND` instead of generic numbers.
- [x] Register canonical `/api/valuation/options/*` routes and retain hidden aliases.
- [x] Print the active volatility version from the scoped operator script.
- [x] Apply the migration and prove two live imports are idempotent.
- [x] Reconcile current-state, handoff, architecture, schema, ingestion,
  limitations, status, product register, and knowledge-base docs.

**Verified 2026-08-08:** active volatility version `#45` has SHA-256
`763b4a907f9584395e5cba1bb428f064dd6a85ff90a08e0bfb80d919d97cb54b`,
source date `2026-01-05`, and 94 rows. Two consecutive imports retained the same
ID, hash, and row count. Live coverage remains 5 supported, 17 partial, 13
unsupported, 9 typed sources, and 2,787 typed rows. Active provenance is 7
complete, 0 partial, 0 missing, and 0 mismatches. Validation passes 28 focused
tests, 461 backend tests, 90 frontend tests, TypeScript, production build,
Python compile, Alembic head, four knowledge-base tests, the knowledge-base
audit, and `git diff --check`.

**Historical limitation at Phase 37, resolved by Phases 38-39:** pricing and
country-stat importers still used replacement paths at this checkpoint.
Pre-migration volatility rows remain stored with null version links and
are intentionally excluded from active reads. Industry volatility remains a
prior, not a company/project fact. Browser screenshots were not rerun because no
rendered component changed.

## Phase 38: Versioned Pricing and Source-Separated Relative Valuation

- [x] Verify PE, PBV, PS, and EV/EBITDA source hashes, dates, exact headers,
  duplicate header groups, nulls, zeros, aggregate rows, and representative values.
- [x] Add migration `n0n0n0n0n0n0` for source-backed growth, return, margin,
  and normalization controls without dropping or rewriting existing rows.
- [x] Convert all four pricing importers to `DamodaranDatasetVersionService`.
- [x] Require exact source columns before version creation and roll back empty imports.
- [x] Preserve changed hashes and reactivate known historical pricing versions.
- [x] Retain all 94 non-aggregate industries and source zeros/nulls.
- [x] Replace arbitrary shared-table `first()` reads with active source-code assembly.
- [x] Carry the correct workbook version into every relative-valuation calculation.
- [x] Report requested methods that lack an active benchmark or required company input.
- [x] Register canonical `/api/valuation/relative/*` routes and hidden legacy aliases.
- [x] Show benchmark versions and unavailable methods in the relative-valuation UI.
- [x] Remove hardcoded USD display from currency-agnostic relative outputs.
- [x] Move all four source contracts from partial to supported in Data Health.
- [x] Apply the migration and prove two live imports are idempotent.
- [x] Reconcile current-state, handoff, architecture, schema, ingestion,
  limitations, product register, roadmap, documentation indexes, and KB status.

**Verified 2026-08-08:** active versions are PE `#46`, PBV `#47`, PS `#48`,
and EV/EBITDA `#49`; each is dated `2026-01-05` and contains 94 rows. Two
consecutive imports retained identical IDs, hashes, and row counts. Live coverage
is 9 supported, 13 partial, 13 unsupported, 13 typed sources, and 3,163 typed
rows. Active provenance is 11 complete, 0 partial, 0 missing, and 0 mismatched.
Validation passes 22 focused tests, 476 backend tests, 90 frontend tests,
TypeScript, production build, Python compile, Alembic head, four knowledge-base
tests, the knowledge-base audit, and `git diff --check`.

**Historical limitation at Phase 38, resolved by Phase 39:** country statistics
were the last current typed importer using destructive replacement. Relative
valuation still uses industry aggregates, not a reviewed peer set, and requires
user review of comparability and company input definitions.

## Phase 39: Versioned Country Statistics

- [x] Verify the exact 22-column source layout, SHA-256, source date, row count,
  nulls, zeros, signed dividends, and representative India/US/China values.
- [x] Add migration `p1p1p1p1p1p1` for cash/firm value and total dividends.
- [x] Replace destructive country-stat ingestion with preserved hash versions.
- [x] Populate all existing debt, firm-value, cash, enterprise-value, multiple,
  dividend, firm-count, and source-date fields.
- [x] Restrict country-stat API and mapping availability reads to active versions.
- [x] Add source/version provenance to country-stat API facts.
- [x] Prove exact values, fail-closed structure, idempotency, changed-history
  preservation, reactivation, active-only reads, and mapping behavior in tests.
- [x] Apply the migration and repeat the live scoped import.
- [x] Reconcile Data Health, architecture, schema, ingestion, limitations,
  handoff, source-batch plans, product register, roadmap, and KB status.

**Verified 2026-08-08:** active country-stat version `#50` has SHA-256
`900b6594f808461f9ce5194abf1a50e66f22854bc998473ad8282037d464829b`,
source date `2026-01-05`, and 127 rows. Two consecutive imports retained the
same ID, hash, and count. Live coverage is 9 supported, 13 partial, 13
unsupported, 14 typed sources, and 3,290 typed rows. Active provenance is 12
complete, 0 partial, 0 missing, and 0 mismatched.

Validation passes 27 focused tests, 483 backend tests, 90 frontend tests,
TypeScript, the Next.js 16.2.11 production build, Python compile, Alembic head,
four knowledge-base tests, the corpus audit, and `git diff --check`.

**Remaining limitation:** the destructive replacement paths for current
application typed Damodaran sources are closed, but only 14 of 35 mirror sources
have typed rows. Historical `macro.xls` and `macrodur.xls` rows use a separate
historical contract and report provenance as not applicable in this inventory.
