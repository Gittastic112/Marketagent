# Agent Handoff Document

**Last updated:** 2026-08-08
**Purpose:** This document gives any agent (Codex, Antigravity, Claude Code, Cursor) everything needed to take over this project. Read this before touching code.

---

## 2026-08-08 Versioned Country-Statistics Checkpoint

`countrystats.xls` is now the twelfth current application source on the shared
preserved-version lifecycle. The exact parser requires the source's 22-column
layout, retains 127 countries and all 20 meaningful fields, preserves zero/null
and signed dividend values, and fails before metadata creation on structural
drift. It now populates debt including leases, firm value, cash, cash/firm value,
and total dividends that the old importer omitted.

Migration `p1p1p1p1p1p1` adds the two previously absent fields. Country-stat API
and industry-mapping macro availability now require a row linked to the active
`countrystats` version. API facts include source file, version, SHA-256, source
date, date confidence, canonical path, and claim type.

Live version `#50` has SHA-256
`900b6594f808461f9ce5194abf1a50e66f22854bc998473ad8282037d464829b`,
source date `2026-01-05`, and 127 rows. Two imports retained the same version.
Coverage is 9 supported, 13 partial, 13 unsupported, 14 typed sources, and 3,290
typed rows. Active provenance is 12 complete, 0 partial, 0 missing, and 0
mismatched. All current application source-specific typed Damodaran importers
now preserve versions; 21 mirror sources remain partial or unsupported and
should not be described as ingested.

Validation passes 27 focused tests, 483 backend tests, 90 frontend tests,
TypeScript, the Next.js 16.2.11 production build, Python compile, Alembic head,
four knowledge-base tests, the corpus audit, and `git diff --check`.

See
`docs/roadmaps/next-5-damodaran-versioned-country-statistics-checkpoint-2026-08-08.md`.

## 2026-08-08 Versioned Pricing and Relative-Valuation Checkpoint

Migration `n0n0n0n0n0n0` adds the PE growth/aggregate controls, PBV return
controls, PS margin controls, and EV normalization variants present in the four
approved pricing workbooks. PE, PBV, PS, and EV/EBITDA now use independent,
hash-idempotent dataset versions and preserve changed source histories.

The shared pricing table intentionally keeps one sparse row per source version.
`RelativeValuationBenchmarkService` now assembles the four active rows by source
code instead of returning SQL's arbitrary first row. Every relative calculation
links to its own active workbook version. Requested but unavailable methods are
reported explicitly. Canonical routes are `/api/valuation/relative/*`; hidden
legacy aliases remain. The frontend exposes unavailable methods and source
versions, initializes from the first active country, preserves zeros, and no
longer labels unknown-currency values as USD.

Live active versions are PE `#46`, PBV `#47`, PS `#48`, and EV/EBITDA `#49`.
All are dated `2026-01-05`, contain 94 rows, and were unchanged by a second
scoped import. Coverage is 9 supported, 13 partial, 13 unsupported, 13 typed
sources, and 3,163 typed rows. Active provenance is 11 complete, 0 partial,
0 missing, and 0 mismatched. Country statistics are the next and last current
typed replacement-path conversion.

Validation: 22 focused tests, 476 backend tests, 90 frontend tests, TypeScript,
Next.js 16.2.11 production build, Python compile, Alembic head, four KB tests,
KB audit, and `git diff --check` pass. The live Advertising check returned all
six requested methods from versions `#46`-`#49` with no unavailable method.
Browser navigation reached the configured sign-in page without console errors;
the authenticated panel was not visually exercised because that browser session
had no local credentials.

See
`docs/roadmaps/next-20-damodaran-versioned-pricing-and-relative-valuation-checkpoint-2026-08-08.md`.

## 2026-08-08 Versioned Volatility and Real-Options API Checkpoint

Migration `m9m9m9m9m9m9` adds a nullable dataset-version foreign key and index
to `industry_volatility_benchmarks`. Null is intentional for pre-migration rows
whose original source bytes cannot be proven. New reads and Data Health counts
join only rows belonging to the active version.

`optvarIndia.xls` now uses `DamodaranDatasetVersionService` and an exact source
contract. The importer requires all six industry headers, the workbook's
`Relative Standard Deviation of Bonds = 0.40`, and `Correlation between stocks
& bonds = 0.50`. It stores source date `2026-01-05`, preserves real zero/null
cells, excludes Total Market rows, rolls back empty parses, and fails before
metadata creation when the contract is incomplete.

Live volatility version `#45` has SHA-256
`763b4a907f9584395e5cba1bb428f064dd6a85ff90a08e0bfb80d919d97cb54b`
and 94 rows. Two consecutive imports retained the same ID, hash, and count:

```bash
docker compose exec backend python /workspace/scripts/ingest_damodaran.py --only volatility
```

Canonical `GET /api/valuation/options/volatility`, `POST
/api/valuation/options/eligibility`, and `POST
/api/valuation/options/calculate` routes now match the frontend contract. Hidden
legacy aliases remain. Volatility responses include claim type, active dataset
version, source file/hash/date/confidence/path, and exact nullable values. Missing
benchmarks return `VOLATILITY_BENCHMARK_NOT_FOUND`; generic numeric fallback was
removed.

Live coverage remains 5 supported, 17 partial, 13 unsupported, 9 typed sources,
and 2,787 typed rows. Active provenance is 7 complete, 0 partial, 0 missing, and
0 hash mismatches. Pricing and country-stat importers remain the next
replacement-path correctness boundary.

Validation: 28 focused tests, 461 backend tests, 90 frontend tests, TypeScript,
Next.js 16.2.11 production build, Python compile, Alembic head, four
knowledge-base tests, knowledge-base audit, and `git diff --check` pass. Browser
screenshots were not rerun because no rendered component changed. See
`docs/roadmaps/next-20-damodaran-versioned-volatility-and-real-options-api-checkpoint-2026-08-08.md`.

---

## 2026-08-08 Source-Backed Synthetic Ratings Checkpoint

`backend/app/services/synthetic_rating_catalog.py` reproduces all 45 rows from
approved `ratings.xls`, including exact breakpoints, combined Moody's/S&P
labels, and decimal spreads for large non-financial, small/risky, and
financial-service firms. Catalog version `ratings-xls-45d1f61c67f0` is tied to
the canonical source hash.

`POST /api/valuation/wacc/calculate` accepts explicit `firm_type`, preserves the
legacy `is_large_mfg` request path, rejects contradictory inputs, and returns
the selected rating band plus source provenance. The source date remains
unknown with low confidence. Treating it as recent remains a `User Assumption`
approved on 2026-08-07. The response says this directly.

Operating-lease capitalization from the workbook is not implemented; callers
must provide lease-adjusted interest coverage when applicable. Damodaran
coverage is now 4 supported, 18 partial, and 13 unsupported.

Validation: 27 focused tests, the full 434-test backend suite, 90 frontend
tests, TypeScript, production build, four knowledge-base tests, corpus audit,
source-hash comparison, and `git diff --check` pass. Browser automation was not
rerun because this milestone has no frontend consumer or visual change.
See
`docs/roadmaps/next-15-source-backed-synthetic-ratings-checkpoint-2026-08-08.md`.

---

## 2026-08-08 Damodaran Application Coverage Checkpoint

`GET /data-health/damodaran-coverage` and the Data Health page now expose a
versioned 35-workbook application inventory. Each source carries its canonical
knowledge-base path, source date and confidence, metric family, implementation
state, source-mirror presence, typed destination tables, live typed-row count,
freshness, supported and missing metrics, limitations, and required action.

The local snapshot has all 35 mirror files present, but only 8 have typed rows:
2,693 rows total. The strict implementation assessment is 4 supported, 18
partial, and 13 unsupported. Generic admin parsing is classified
`metadata_only`, not ingested coverage. `ratings.xls` remains source-date
unknown and low confidence while its user-approved recency is shown separately
as `user_assumed_recent`.

Validation: 422 backend tests and 90 frontend tests pass; TypeScript, the
Next.js 16.2.11 production build, four knowledge-base tests, and the corpus
audit pass. Browser automation was not rerun. See
`docs/roadmaps/next-15-damodaran-coverage-checkpoint-2026-08-08.md`.

---

## 2026-08-07 Damodaran Knowledge Base Checkpoint

The missing literal `damodaran_knowledge_base_v1/raw/inbox/` has been created,
and the legacy `Data for Model/` folder was processed as the prior intake. Of 38
sources, 12 workbooks were byte-identical to existing canonical files and 26
unique sources were routed without modifying their bytes. The canonical raw
corpus now contains 61 files; the source catalog has 61 rows and the processing
ledger has 38 intake decisions.

The knowledge layer now includes exact January 2025 debt/dividend regression
equations and fit limitations, the January 2026 country-risk method/data source,
and architecture maps for synthetic ratings and macro duration. Dated benchmark
values remain data rather than doctrine. `macro.xls` is historical through 2009,
and `macrodur.xls` uses 1987-1997 sector regressions.

Run `python3 damodaran_knowledge_base_v1/tools/audit_kb.py` before valuation
knowledge work. It passes with an empty inbox; its four unit tests pass. Read
`damodaran_knowledge_base_v1/INDEX.md` and
`damodaran_knowledge_base_v1/PROCESSING_PLAN.md` first. No review items remain
open. The six January 2025 regression models now use the source PDFs' 26 exact
coefficients, source-aligned variables and units, scoped idempotent seeding,
coefficient-drift rejection, and disabled weak payout priors. The user approved
`ratings.xls` as recent for local use on 2026-08-07, while retaining unknown
source date and low date confidence.

Validation: the knowledge audit and four audit tests, 419 backend tests, 89
frontend tests, TypeScript, and the Next.js 16.2.11 production build pass. The
local regression seed is synchronized and a second run changed nothing.

---

## 2026-08-07 Quick Valuation and Manual Event Evidence Checkpoint

Quick Valuation no longer calls the unregistered
`/valuation/assumptions/generate` and `/valuation/dcf/calculate` routes. It now
uses typed authenticated baseline and deterministic FCFF endpoints, rejects
unsafe inputs, displays assumption-generation failures instead of invented
fallbacks, labels output as a non-persisted `Calculation`, and creates no saved
valuation rows.

The historical Data Health queue now links unresolved rows to
`/events/{id}/evidence-resolution`. Exact search is limited to the event's
linked stored text, returns at most 25 bounded context snippets, and never
returns a full filing body. Save locks the event and rechecks the linked
document/company, content hash, offsets, quote, occurrence index, and duplicate
state before recording authenticated creator and manual-resolution provenance.

Validation: 412 backend tests and 87 frontend tests pass; TypeScript and the
Next.js 16.2.11 webpack production build pass. Browser automation was not run.
See
`docs/roadmaps/next-10-quick-valuation-and-manual-event-evidence-checkpoint-2026-08-07.md`.

---

## 2026-08-07 Historical Event Evidence Backfill Checkpoint

Data Health now previews historical events without evidence references through
`GET /data-health/event-evidence-backfill`. The scanner considers the event
description and only the authenticated user's alert evidence. A candidate is
eligible only when it is 24-2,000 characters and occurs exactly once, byte for
byte and case-sensitively, in stored source text. Fuzzy and whitespace-normalized
matching are deliberately disabled.

`POST /data-health/event-evidence-backfill` defaults to dry-run. Apply locks the
event, rechecks for an existing reference, creates a high-confidence exact text
span, and records source origin and processing-run provenance. Data Health shows
eligible, ambiguous, conflicting, missing, and unmatched records with corrective
actions. The live read-only preview checked one unreferenced event; it had no
exact match, so zero records were eligible and no live data was changed.

Validation: 403 backend tests and 85 frontend tests pass; TypeScript and the
Next.js 16.2.11 webpack production build pass. Browser automation was not run.
See `docs/roadmaps/next-10-historical-event-evidence-backfill-checkpoint-2026-08-07.md`.

---

## 2026-08-07 Exact Event PDF Evidence Checkpoint

New `pdf_region` event evidence must include finite, in-bounds
`pdfplumber_top_left_points` geometry whose page number and dimensions match the
stored PDF. Accepted geometry is normalized before storage. Legacy page-only or
malformed records remain readable, but evidence trails downgrade them to
page-level/partial evidence and Data Health reports invalid geometry.

Exact regions open
`/documents/{document_id}/event-evidence?evidence_reference={reference_id}`.
The page reuses the authenticated bounded PNG renderer and proportional overlay
used by financial evidence. Alert drawers and document review only say “exact”
when the strict geometry contract passes; otherwise they preserve a source-PDF
or document-context fallback.

Validation: 399 backend tests and 84 frontend tests pass; TypeScript and the
Next.js 16.2.11 webpack production build pass. Browser automation was not run.
See `docs/roadmaps/next-10-event-pdf-evidence-checkpoint-2026-08-07.md`.

---

## 2026-08-02 Exact Financial PDF Evidence Checkpoint

Financial candidates with trusted `pdfplumber_top_left_points` coordinates now
open `/documents/{document_id}/financial-evidence?candidate_id={candidate_id}`.
The page renders an authenticated PNG of the stored source page and overlays a
single reported row or each component row for summed/calculated candidates.
Malformed, unknown, mismatched, and out-of-bounds geometry is rejected by the
frontend helper and retains a direct authenticated source-PDF fallback.

The backend page route is
`GET /api/raw-documents/{id}/asset/pages/{page}.png`. It accepts stored assets
only, requires identity, limits scale to `0.5`-`2.0`, caps output at 16 million
pixels, and returns private `no-store`, inline, `nosniff` PNG bytes. The route is
registered in the explicit binary response-contract inventory. APSEZ candidate
`40` was live-rendered from document `3`, page `465` at 893x1170 pixels.

Validation: 397 backend tests and 80 frontend tests pass; TypeScript and the
Next.js 16.2.11 webpack production build pass. Browser automation was not run.
See `docs/roadmaps/next-10-exact-pdf-evidence-checkpoint-2026-08-02.md`.

---

## 2026-08-02 Statement Identity Checkpoint

`FinancialStatementIdentityService` now evaluates annual source facts using two
declared equations: profit after tax and profit attribution to parent plus NCI.
The authenticated API is
`GET /api/companies/{company_id}/financial-statements/identities`. Company
fundamentals renders each formula, expected value, actual value, delta,
tolerance, and missing or duplicate facts. Data Health exposes every promoted
history's normalization, reconciliation, identity, evidence, limitations, and
certification state.

Failed applicable identities now block certification and mark company-actual
valuation provenance for review with `valuation_trust_status=blocked`. Missing
facts do not manufacture a pass: they produce `not_available` and an explicit
certification limitation. Live APSEZ passes 6/6 checks. AAPL has zero applicable
and eight unavailable checks under its user-approved six-metric fact set. The
portable AAPL/APSEZ report remains passed for markets `US` and `IN`, with the
AAPL statement-identity limitation visible.

Validation: 397 backend tests and 76 frontend tests pass; TypeScript and the
Next.js 16.2.11 webpack production build pass. Data Health has zero blocking
errors and the pre-existing AAPL source-timestamp warning. See
`docs/roadmaps/next-10-statement-identity-checkpoint-2026-08-02.md`.

---

## 2026-08-02 Financial Integrity and Industry Mix Checkpoint

Certification is now portable across local databases through
`data/certification/aapl-apsez-reference-manifest.json`, which resolves AAPL and
APSEZ by stable market identity and official source hashes. It passes live with
two histories and markets `IN` and `US`. The APSEZ finalizer is idempotent under
strict same-page EBIT formula checks: rerunning it created and promoted zero
facts and retained 27/27 exact reconciliations.

Data Health now audits promoted financial locators, unique fiscal periods, and
source/stored period ends and derives current certification coverage. Live state
is 75 promoted facts, seven annual periods, two eligible histories, `IN` and
`US`, and no financial integrity issue. The weighted industry editor now shows
actual module/field coverage, attaches a company-owned source document, and
syncs returned coverage after save. Open valuation drafts automatically refresh
source values when normalized history changes without overwriting reviewed user
edits.

Validation: 391 backend tests, 75 frontend tests, TypeScript, webpack production
build, secret gates, project-skill validation, diff checks, and Alembic head
`j6j6j6j6j6j6` pass. The new weighted-mix Playwright workflow compiles and is
listed in the isolated suite; it was not browser-executed in this batch.

See `docs/roadmaps/next-10-financial-integrity-and-industry-mix-checkpoint-2026-08-02.md`.

---

## 2026-08-01 Real-Source Certification Checkpoint

The user explicitly approved AAPL FY2022-FY2025 core facts. Guarded processing
run `5` promoted exactly 24 SEC XBRL-backed facts, created four exact
September-ended periods, normalized all four, and reconciled with zero
mismatches. AAPL is eligible for certification. FY2021 was not authorized; its
seven candidates remain `needs_review`.

Adani Ports is now local company ID `6`, verified as `ADANIPORTS` / ISIN
`INE742F01042`. Documents `3` and `4` store the supplied FY2024-25 and FY2023-24
annual reports with NSE URLs. Processing runs `6` and `7` staged 48 consolidated
FY2023-FY2025 statement candidates. Those facts and three reviewed operating-EBIT
calculations are now promoted. Document `5` stores the supplied Q1 FY27 investor presentation as a
supplementary Source Summary and links the revised consolidated NSE iXBRL.
Valuation draft `2` records the 2026-08-02 cutoff. APSEZ has three March-ended,
trust-ready periods, 27/27 exact canonical reconciliations, and 51 reviewed exact
evidence rows. EBIT is a `Calculation`: revenue from operations less operating,
employee, depreciation/amortisation, and other expenses. The fail-closed report
now passes with AAPL and APSEZ, `certified_count=2`, and markets `IN` and `US`.

Long-report PDF ingestion now accepts 40 MB/1,000 pages, requires targeted page
ranges above 500 pages, scans at most 75 targeted pages, records official source
URLs, handles INR crore statement rows and component sums, and keeps
non-annual presentation candidates out of annual history.

Industry mapping no longer invents the first alphabetical fallback or reports
all benchmark modules as available. It now persists a revenue-weighted segment
mix with strict 100% validation, source metadata, and draft-signature invalidation.
Missing component benchmarks make only that blended field unavailable; weights
are never silently renormalized. The existing approved `Packaging & Container`
selection was preserved as a 100% user-assumption row until real segment weights
are entered.

Validation at this checkpoint: 391 backend tests and 75 frontend tests pass;
TypeScript and the Next.js webpack production build pass. The four backend warnings are upstream `openpyxl`
`datetime.utcnow()` deprecations.

See:

- `docs/roadmaps/aapl-real-source-certification-checkpoint-2026-08-01.md`
- `docs/roadmaps/adani-ports-real-source-checkpoint-2026-08-01.md`

---

## 2026-08-01 Next-10 Checkpoint

The follow-on search checkpoint is now implemented. Docker development isolates
Linux native frontend modules from the Mac bind mount, fixing the Lightning CSS
ARM64 startup failure. Search covers documents, events, and owner-scoped alerts,
theses, decisions, and valuation models with GIN indexes, claim/source labels,
timestamps, type filters, deep links, and a 14-query/750-ms local backend
budget. Decision creation now persists and validates `company_id`. Current
migration head is `h4h4h4h4h4h4`. See
`docs/roadmaps/next-10-search-execution-checkpoint-2026-08-01.md`.

Current proof is 358 backend tests, 70 frontend tests, TypeScript, production
build, repository secret/static/skill gates, and all 14 isolated Playwright
workflows. The browser suite includes the new owned cross-domain search workflow
and waits for React server streams before applying stable-DOM accessibility
assertions.

### Prior reliability batch

The next reliability batch added deterministic repository secret/static gates,
a measured 20-query/1,000-ms dashboard budget, an authenticated on-demand
evidence-integrity report with Data Health UI, and five new browser workflows.
The company wizard now persists the selected Damodaran industry and redirects
to the created company. SEC readiness/failed ingestion, valid CSV
preview/apply/export, valuation review invalidation/stale-write recovery, and
partial portfolio analytics now have repeatable isolated proof.

The full proof is 355 backend tests, 68 frontend tests, TypeScript, production
build, static repository gates, and all 13 isolated Playwright workflows.
Evidence integrity remains bounded and on demand: it does not fetch dead links,
repair records, run on a schedule, or replace real-source certification.
The prior reliability batch ended at migration `g3g3g3g3g3g3`. See
`docs/roadmaps/next-10-execution-checkpoint-2026-08-01.md`.

---

## 2026-07-31 Next-10 Checkpoint

The ten-item register sequence has been executed. Backup/restore, exact event
evidence, AI citation review, responsive accessibility gates, removal of known
blocking browser dialogs, and dashboard HTTP consolidation pass focused proof.
Point-in-time financial revisions, PostgreSQL document/event search, and the
contradiction/language-change queue are bounded foundations. The real-source
certification harness is fail-closed and reports no certification until one
reviewed US and one reviewed India history pass.

Current migration head: `g3g3g3g3g3g3`.

Latest full proof: 352 backend tests passed, 67 frontend tests passed,
TypeScript passed, and all 8 isolated Playwright workflows passed, including 12
responsive screenshots. The backup drill restored table counts and exact
document bytes. Promoted financial candidates remain auditable by ID but are
excluded from the active review queue after promotion.
See `docs/roadmaps/next-10-execution-checkpoint-2026-07-31.md` for the exact
status and remaining limits.

---

## 0. Current Handoff Status - 2026-07-26

### Full Product Audit Override

The latest measured product/code/UX/security audit is
`docs/roadmaps/product-codebase-ux-and-architecture-assessment-2026-07-25.md`.
It estimates the product at 58% quality-adjusted completion against the
local-first brief and 47% against a world-class daily-driver bar.

Its Phase A-C consolidation sequence now takes priority over the older
feature-first recommendation list below. The first 30-step R1 checkpoint is
complete: FastAPI is authenticated by default behind a two-route public health
allowlist, route classification is automated, research sessions are
owner-resolved, and CSV interchange is real, bounded, formula escaped,
portfolio scoped, previewable, and transactional. The exact record is in
`docs/world-class-product-execution-roadmap-2026-07-25.md`.

The next five R1 controls are also complete. Owned alert and daily-brief defects
were fixed and the user-owned negative matrix expanded; failed requests now use
safe stable codes plus request IDs; logs are request-aware JSON on stdout; weak
provenance hashes are SHA-256; and migration `b8b8b8b8b8b8` introduces one
owned AI provider/mock/source/privacy/transmission/review/failure contract.
Missing AI configuration and provider failure no longer become mock success.
AI UIs disclose transmitted data classes before calls, automatic ingestion no
longer invokes narrative AI, and event-to-thesis AI returns proposals rather
than writing impacts.

The next product-integrity batch is verified. Request IDs now correlate to
processing runs at migration head `c9c9c9c9c9c9`; the route-contract inventory
has zero legacy JSON responses; Tailwind/PostCSS and owned design tokens compile
in production; navigation is grouped and responsive; company routes share
workspace tabs and route boundaries; and research/CSV recovery states pass an
isolated browser suite. CI and `scripts/verify_release_baseline.sh` reproduce a
fresh migration, 336 backend tests, 65 frontend tests, and TypeScript. Dense
navigation prefetch is disabled and the database pool has a documented bounded
10 + 20 overflow default after browser testing exposed a 16-request render
burst against the previous 15-connection ceiling.

R1 edge work now centers on AI citation/evaluation and complete stored-output
review actions. The next major sequence is backup/restore, exact evidence
locators, representative real-source certification, accessibility/performance,
and integrated daily workflows. Do not start a new provider or top-level
product module before those gaps close.

### Safe Stop Point
The normalized-financial-to-valuation bridge has durable, user-owned setup drafts plus source-versus-normalized reconciliation. Filing candidates share typed evidence locators for text, PDF tables, Screener cells, and SEC XBRL. Authenticated PDF upload now stores one original `DocumentAsset`, extracts review-gated cells from line-based tables, preserves page/table/row/column and bounding-box coordinates, and links review to the exact source page. PDF, filing-text, XBRL, Screener, and backfill attempts persist standardized processing runs. Normalization no longer materializes absent reported revenue, EBIT, or net income as zero. Filing diff source text remains escaped and rendered without `dangerouslySetInnerHTML`. Local auth is configured in the current Docker environment without any committed default credential. The exact setup and rotation workflow remains in `docs/07-local-development.md`.

Company setup, SEC ingestion, and portfolio management were hardened in the
latest batch. The industry selector now loads the available 94-name taxonomy
with an explicit country fallback warning; SEC import resolves or creates its
source automatically; ingestion alerts are user-owned; raw-document collection
reads no longer transfer full filing bodies; and portfolio CRUD/valuation is
user-scoped and honest about missing prices. An authenticated SEC check,
major-route smoke, and complete temporary portfolio lifecycle passed. The
30-step record is in
`docs/roadmaps/setup-ingestion-portfolio-hardening-checkpoint-2026-07-25.md`.

The three follow-on hardening milestones are also complete. An isolated
Playwright stack now verifies valuation draft save/reset/refresh/archive/reopen
and promotion plus PDF upload/review/override/promotion/reconciliation. Synthetic
three-period US and India histories verify canonical normalization and autofill,
but are explicitly `Mock Data` test fixtures rather than production records.
The fresh-database run also exposed and fixed duplicate normalized-table
migration operations and the missing `event_thesis_impacts` migration; the
temporary runtime DDL endpoint was removed.

The latest trust pass replaced the ad-hoc event evidence response with typed,
authenticated event evidence and a user-owned alert evidence endpoint. The
contract exposes claim type, confidence, timestamp, explicit evidence status,
bounded claim context, safe source/document metadata, and current-user
thesis/valuation impacts without serializing filing bodies or provider payloads.
Alert cards, the alerts table, and the new `/alerts/{id}` page use the typed
drawer. New events can persist validated section/span and reproducible PDF-region
locators; page-only evidence is an explicit fallback. Historical records still
need safe backfill and retain explicit fallback states.
The same audit closed direct child-ID ownership gaps
in thesis assumption/impact and valuation child routes.

### Verified Complete (cumulative)
- **All Damodaran data batches ingested:**
  - `marginIndia.xls` → 94 records
  - `capexIndia.xls` → 94 records
  - `wcdataIndia.xls` → 94 records
  - `divfundIndia.xls` → 94 records
  - `divfcfeIndia.xls` → 94 records
  - `macro.xls` → 379 macro observations
  - `macrodur.xls` → 1358 macro observations + 392 sector sensitivities
  - `optvarIndia.xls` → 94 volatility records
- **Regression coefficients synchronized:** 26 exact coefficients across six January 2025 Global/US debt-ratio, dividend-yield, and disabled payout models
- **Frontend clean build:**
  ```bash
  npm test           # 67 tests passed
  npm run typecheck  # 0 errors
  npm run build      # compiled successfully
  ```
- **Backend full suite:** `352 passed`, with 4 third-party openpyxl Python 3.14
  deprecation warnings.
- **Isolated browser suite:** 8 passed for responsive accessibility, alert
  evidence, PDF promotion/reconciliation, company/mobile navigation, disclosed
  AI-provider failure, invalid CSV recovery, and valuation draft promotion.
- **Clean release baseline:** fresh PostgreSQL migration, backend/frontend
  tests, and TypeScript pass through `scripts/verify_release_baseline.sh`.
- **R1 auth/research/transfer checkpoint:** 13 focused tests pass; unsigned
  direct-port `/companies` and portfolio-export calls return `401`; public
  health returns `200`.
- **R1 ownership/error/logging/hash/AI checkpoint:** public errors include
  request IDs; static scans find no weak provenance hash, raw public exception,
  fixed error-log path, direct provider bypass, or silent mock fallback;
  Alembic current is `b8b8b8b8b8b8`.
- **Backend running:** 42 router groups registered, `/api/health` returns OK
- **Market transition complete:** US→India support across company CRUD, source capabilities, filings, and valuation context
- **Frontend Batch 05 Macro Workbench complete:** `/macro` has tabs for Series, Sector Lookup, Scenario, Top-Down, and Bottom-Up, with required source/claim labels and warnings.
- **Valuation market context complete:** valuation pages fetch country-aware context, show market/currency/benchmark context, and block saves when risk-free/discount-rate currency conflicts with cash-flow currency without an override note.
- **Backend first-party warnings cleaned up:** the full backend suite has no first-party runtime warning regressions. Four Python 3.14 deprecation warnings originate from openpyxl while the Screener test creates a workbook.
- **Phase 5 financial extraction foundation complete:** filing `raw_text` can produce reviewable financial extraction candidates linked to source documents.
- **Phase 6 financial candidate review foundation implemented:** backend routes and UI now support review, reject, override, and promote actions for extracted financial candidates.
- **SEC XBRL extraction foundation implemented:** `companyfacts` data can create `sec_xbrl_v1` financial extraction candidates for companies with CIKs.
- **Industry mapping/autofill foundation started:** companies now have `damodaran_industry`, industry mapping endpoints exist, the valuation page has a mapping/autofill section, and an assumption autofill route exists.
- **Normalized financial storage migration added:** `normalized_financial_snapshots` and `normalized_financial_metrics` tables now exist in the migration chain.
- **Structured evidence and reconciliation checkpoint complete:** migration `f6f6f6f6f6f6` adds table/cell/typed locator fields; the fundamentals page shows mismatches and gaps; normalized share-count, acquisition, lease-liability, minority-interest, preferred-stock, and employee-option metrics preserve source provenance.

- **Assumption Methodology Engine integrated:** Valuation page allows users to select country-specific default methods for Risk-Free Rate, ERP, etc. and saves their provenance correctly via the `/api/assumptions` routes.
- **Phase 16 Security Hardening initiated:**
  - `next-auth` installed on the frontend with basic JWT strategy.
  - Global CORS policies configured on FastAPI backend.
  - Global Rate Limiting (`slowapi`) applied to the backend.
  - Strict MIME-type whitelists and 2MB file size limits enforced on the Screener.in Excel upload endpoint.
  - FastAPI HMAC validation of short-lived Next.js identity assertions via `get_current_user` implemented.

### What Was Fixed Recently
- Fixed missing `"use client"` directives in various Next.js intelligence components (`EvidenceTrailDrawer.tsx`, `alerts-panel.tsx`, etc.) causing Turbopack build errors.
- Fixed `/api/admin/damodaran/files` reading a nonexistent `created_at` model
  attribute; it now exposes `imported_at` through the compatible response field,
  and the admin router requires authenticated identity.
- Corrected the missing `apiClient` export by switching to `fetchApiResponse` in intelligence components.
- Fixed `MarketPrice` import paths crashing the `yfinance_provider.py`.
- Seeded the India-specific valuation methods successfully via `seed_assumption_methods.py`.
- Damodaran Admin Dashboard (`/admin/damodaran`) implemented for safe file ingestion, validation, and rollback.
- `postApi` missing payload argument in `generateValuationMemo` → added `{}`
- `app/macro/page.tsx` type mismatches (`BottomUpMacroResult`, `TopDownMacroResult` types, segment/period field naming) → aligned with `lib/api.ts` types
- Regression priors router registered in `routes.py`
- `optvarIndia.xls` ingestion added to `scripts/ingest_damodaran.py`
- `fetchValuationContext` was calling `/valuation/context/company/{id}` but the backend route is `/api/valuation/context/company/{id}`. Added a focused frontend API test and fixed the path.
- `advanced-workspace.tsx` now enforces currency mismatch blocking in the submit handler, not only through a disabled button.
- Backend startup/page timeout issue was traced to `backend/app/api/routers/ai.py` importing a non-existent `app.schemas.api_response.APIResponse`. The project envelope is `ApiResponse` in `app.api.schemas`; the router now uses that.
- `generateValuationMemo` was posting to `/api/valuation/{id}/scenarios/{scenario}/ai/memo`, but the backend registers `/valuation/{id}/scenarios/{scenario}/ai/memo`. Added a focused frontend API regression test and fixed the client route.
- Added tested frontend metadata helpers for data-state badges and aggregate page metadata. `DataFreshnessIndicator` now honors explicit `meta.is_mock`, legacy `source: "mock"`, stale state, non-success status, confidence, and processing time. `DataStateNotices` now gives pages one consistent way to show stale, partial, and mock-data warnings.
- Wired stale/mock/partial notices into the main Dashboard, Portfolio, Portfolio Manage, Companies, Company Detail, Data, Data Health, Macro, Alerts, Events, Documents, Research, Narratives, Social, Sources, Settings, Market Prices, Thesis Notes, and Valuation pages.
- Fixed model registry drift: `DecisionLog`, `EvidenceLedgerItem`, and `VariantPerception` are now imported in `backend/app/models/__init__.py`, with `backend/tests/test_model_registry.py` guarding Alembic metadata registration.
- Fixed stale backend imports and response envelope usage in `backend/app/api/routers/relative_valuation.py`.
- Fixed frontend type/runtime issues around Damodaran admin rollback, relative valuation posting, `LoadingState` export, and company id typing in valuation components.
- Fixed `/companies/1/valuation` runtime 500 caused by schema drift. The model expected `dcf_assumption_sets.basic_shares`; the migration did not add it. `72fa829402a4_add_phase_16_lifecycle_fields.py` now adds `basic_shares` and no longer tries to re-add existing `cost_of_equity`.
- Added legacy `/health` while preserving enveloped `/api/health`.
- Fixed token encryption testability by exposing `get_settings` at module scope in `app.core.security`.
- Rounded WACC fade output to avoid binary float noise in exact-value assertions.
- Added `backend/tests/helpers.py` with response envelope helpers and reconciled API tests for market prices, daily brief, fundamentals/valuations, alert generation/review, event extraction, RSS ingestion, portfolio valuation, and portfolio analytics.
- Reconciled more backend API tests to the response envelope: portfolios, update/delete, portfolio cash, SEC API ingestion, and API error tests.
- Fixed duplicate `MarketPriceRead` schema names. Historical market data now uses `MarketHistoryPriceRead`; CRUD market prices retain full `MarketPriceRead` fields.
- Fixed RSS/SEC ingestion response helpers that were accidentally nesting `ApiResponse` objects inside endpoint `data`.
- Fixed valuation alert divergence checks importing the removed `app.models.market_data` module; they now use `app.models.market_price` and safely no-op for missing company ids.
- Fixed `test_social_narratives.py` dependency override leakage by moving the FastAPI override into the fixture.
- Verified fixes for the remaining named backend failures:
  - DCF tests now read structured diagnostic warnings and the current multi-table sensitivity return.
  - Distressed valuation per-share math now uses `assumption_set.diluted_shares` when the copied output has no share count.
  - Macro sensitivity parser tests now expect market/country/classification/currency metadata.
  - SEC service tests now use a non-placeholder test user-agent so strict SEC validation remains active.
  - Added shared backend test fixtures for legacy tests that expected `db`, `db_session`, and `client`.
  - `calculate_priority_score` is backward-compatible with older keyword-only test calls.
  - Thesis alert tests now use current unprefixed routes and unwrap `ApiResponse`.
  - RSS feed ingestion now honors its injected `http_get` test hook while preserving safe URL validation.
  - Alembic coverage test now checks the current consolidated migration corpus instead of deleted legacy migration files.
- SEC filing text download now honors its injected `http_get` hook instead of making real network requests during tests.
- Removed backend test warnings by migrating remaining Pydantic class configs to `ConfigDict`, replacing first-party `datetime.utcnow` callables, preventing event-scoring autoflush warnings, and scoping openpyxl's Python 3.14 deprecation warning during workbook parsing.
- Added `financial_extraction_candidates`, `POST /api/filings/{filing_id}/extract-financials`, and `GET /api/companies/{company_id}/financial-statements/extracted` for first-pass source-linked candidate extraction from filing text.
- Added UI wiring so `/companies/{id}/filings` can trigger extraction and `/companies/{id}/fundamentals` shows extracted candidates awaiting review.
- Added review/promote endpoints for financial extraction candidates:
  - `PATCH /api/financial-line-items/{candidate_id}/review`
  - `PATCH /api/financial-line-items/{candidate_id}/override`
  - `POST /api/companies/{company_id}/financial-statements/mark-reviewed`
- Added `FinancialCandidateReview` UI on company fundamentals for accept/reject/override/promote actions.
- Added SEC XBRL candidate extraction service and `POST /api/companies/{company_id}/extract-xbrl`.
- Added normalized financial tables via `75cc1d347c32_add_normalized_financials.py`.
- Added `companies.damodaran_industry` via `76dd1d347c33_add_damodaran_industry.py`.
- Added industry mapping endpoints and valuation page mapping/autofill UI hooks.
- Added an experimental assumption autofill engine and route. It returns per-field provenance and `source_metadata`; normalized warnings and formulas derived from unresolved inputs propagate review requirements.
- Added focused promotion edge-case tests for missing fiscal years, normalization warnings, and reported/derived provenance. Autofill now uses normalized invested capital, calculated sales-to-capital, multi-period revenue CAGR, and current company market data when available. Same-period legacy fallback is restricted and labeled for cash, debt, and diluted shares when a normalized snapshot exists.
- Rebuilt the valuation draft page as a review-first form with source, claim type, confidence, warning, and placeholder badges for every assumption. Critical values are validated, explicit review is required, and the server action rechecks current metadata before creating a model.
- Persisted valuation setup drafts with user ownership, edit/review tracking, safe source refresh, and atomic promotion. Repeated promotion now returns a conflict instead of creating duplicate models, and a failure-path test verifies transaction rollback.
- Added normalized bridge inputs for cash, debt, diluted shares, capex, depreciation, and working-capital change. Autofill now carries FCFE inputs and reporting-currency provenance from the canonical snapshot.
- Reviewed ISO units or filing metadata now set reporting currency; conflicting currencies return `422` before promotion. Company/period fallback remains labeled and warned.
- Added optimistic draft version checks, per-field reset-to-source, archive/reopen behavior, UI controls, and regression coverage.
- Replaced the hard-coded local `admin/admin` NextAuth credential with required local environment credentials. Added stable local session environment wiring, backend user provisioning from valid sessions, and server-only API helpers that forward session cookies for protected server actions.
- Migrated all server-rendered page reads to `frontend/lib/server-api.ts`, preserving response metadata and structured errors while forwarding the session cookie. A source-scan regression test prevents cookie-blind client helpers from being reintroduced into server pages.
- Added the Next.js 16 `proxy.ts` signed-out page boundary. Missing local auth configuration now produces an explicit disabled sign-in state instead of rendering protected navigation or partial dashboard data.
- Added `currency_source` and `currency_confidence` to financial periods in migration `d4d4d4d4d4d4`; reviewed units, filing metadata, SEC XBRL units, company fallback, and system fallback now remain distinguishable through normalization and autofill.
- Added financial-candidate `source_line_number`, `source_page`, `source_section`, and `extraction_warnings` in migration `e5e5e5e5e5e5`. Deterministic text extraction now lowers confidence when units are missing, years are inferred, or a source line has multiple numeric values.
- Candidate review/override now requires a non-empty reporting unit. The review UI exposes source location, warnings, confidence context, and unit editing.
- Rebuilt the Screener `.xlsx` path around valid `Source`, `RawDocument`, content-hash, and `ProcessingRun` records. Duplicate uploads return `409`, temporary files are deleted, and persisted records never reference temporary paths.
- Added `GET /api/companies/{company_id}/financial-statements/normalized/coverage`. Backfill responses now include before/after coverage, trust-ready counts, stale snapshots, missing snapshots, low-confidence currency counts, and conflict details.
- Added financial and market source-age diagnostics to valuation drafts. Stale or unknown-freshness inputs enter `review_fields`; user replacements remove obsolete stale metadata while preserving explicit review.
- Added `GET /api/auth/readiness`, which returns only configuration booleans and missing variable names. The sign-in form remains disabled until readiness is verified.
- Fixed missing `/api` prefixes on filing/XBRL extraction writes and moved Damodaran/Screener multipart uploads through the same-origin authenticated proxy helper.
- Added dry-run and executable normalized-snapshot backfill at `POST /api/companies/{company_id}/financial-statements/normalized/backfill`. It is idempotent, skips conflicting currencies, and reports eligibility/errors before writes.
- Added `GET /api/financial-line-items/{candidate_id}` and candidate-to-document evidence deep links.
- Added `GET /api/companies/{company_id}/financial-statements/normalized/reconciliation` with exact, mismatch, missing-normalized, normalized-only, delta, provenance, and warning states.
- Added reusable processing-run lifecycle helpers and wired filing extraction, SEC XBRL extraction, Screener upload, and normalized backfill preview/apply to standardized outcomes.
- Escaped all filing text used in section diff HTML and added regression tests for changed and first-time sections.
- Extended deterministic filing extraction to preserve multi-period capex and working-capital candidates when line text identifies fiscal years. Duplicate detection now includes metric, year, and period type.
- Added authenticated PDF filing upload, one-to-one binary `document_assets`
  storage, deterministic page/table/cell extraction, explicit unit warnings,
  source-page evidence links, and protected inline PDF streaming.
- Pinned `pdfplumber==0.11.10`; added a generated/visually verified financial
  statement fixture plus parser/API/security/processing-run regression tests.
- Added `scripts/check_local_auth.py`, which reports only configured/missing
  auth state and never prints credential values.
- Removed recursive FastAPI-to-NextAuth session validation, which could deadlock
  dashboard rendering after a valid login. Next.js now signs 60-second internal
  identity assertions, the browser proxy strips spoofable identity headers,
  FastAPI verifies signatures locally, and all frontend backend fetches have a
  15-second timeout.
- Fixed first-login user provisioning to commit before protected route work.
  This prevents parallel dashboard requests from blocking on competing,
  uncommitted inserts of the same user.
- Copied the root `pyproject.toml` into the backend image so bare `pytest -q`
  honors `testpaths = ["backend/tests"]` and no longer collides with the
  standalone `backend/test_models.py` diagnostic file.
- Corrected top-down and bottom-up macro payload contracts and removed synthetic form defaults. Macro sensitivity now requires actual user inputs when no source-backed values exist.
- Wired reviewed candidate promotion into normalized financial snapshots/metrics as well as legacy financial metrics. Autofill now prefers latest normalized metrics and falls back to legacy metrics for fields not yet normalized.
- Added an experimental event-to-thesis impact classifier service. It is wired from the events router, but treat it as needing focused verification before relying on it.
- Added a reusable project skill library under `docs/skills/` with workflows for architecture, documentation, backend API changes, frontend data states, data ingestion, financial statement extraction, valuation, market intelligence, security, operations, and skill maintenance.
- Upgraded `skills/security-review/SKILL.md` to point to the canonical project security workflow and added `scripts/validate_project_skills.py` for structural skill checks.

### Verification From Latest Agent Turn
```bash
docker compose exec backend pytest backend/tests -q
# 336 passed, 4 third-party openpyxl deprecation warnings

docker compose exec backend alembic current
# c9c9c9c9c9c9 (head)

npm test
# 65 passed

tsc --noEmit
# 0 errors

next build
# compiled successfully

npm run test:e2e:integrity
# 3 passed against a fresh isolated database

npx playwright test --list alert-evidence.spec.ts
# 1 alert-evidence workflow collected

npm audit --json
# 0 known vulnerabilities
```

Current manual checks:
- The live `/api/health` endpoint returns an enveloped `status: ok` response.
- The local database reports `c9c9c9c9c9c9 (head)` after the migration check.
- AAPL has four trust-ready normalized periods and 24 reviewed exact core facts. APSEZ has three March-ended trust-ready periods, 51 reviewed exact evidence rows, and 27/27 exact canonical reconciliations. The two-market certification passes.
- `GET /ingestion/status` returns the expanded run contract; the current local database has no persisted runs.
- `/api/auth/readiness` returns `configured: true` with no missing variable names in the current environment; no credential values are exposed.
- An unsigned browser request to `/` redirects to `/auth/signin?callbackUrl=%2F`.
- Automated local credential sign-in returns `200`; the authenticated dashboard returns `200` in under one second, and all seven overview endpoints complete with `200`.
- The unconfigured sign-in state remains covered by source/regression tests, but was not the active runtime state in this check.
- Authenticated valuation draft and PDF review/promotion workflows pass
  repeatably through Playwright without touching the normal local database.
- The alert-evidence Playwright spec now covers complete and missing evidence
  states, but it has not completed against the isolated stack. Docker Hub
  metadata resolution stalled during the clean image build; the older cached
  offline frontend image lacked the Playwright dev dependency and failed before
  the browser assertion. The disposable stack cleaned up successfully.
- Exact localhost login setup, readiness verification, sign-out, credential-rotation, and troubleshooting steps are documented in `docs/07-local-development.md`. There is deliberately no default application credential.

### Important Current Caveat
The worktree is very dirty from many earlier batches, including deleted old migrations and many untracked generated/source files. Do not revert unrelated changes. Work with the current state.

Autofill values remain draft inputs until reviewed, but review state and provenance are durable. New snapshots normalize broader equity-bridge fields; older periods can be backfilled through an explicit dry-run-capable action and reconciled before valuation use. Legacy financial metrics still fill labeled gaps when no canonical source is available.

Recommended next work:

1. Add balance-sheet/cash-flow identities only where reviewed facts support
   them; keep unavailable identities explicit rather than manufacturing passes.
2. Run the new alert-evidence browser spec after a clean frontend E2E image
   rebuild succeeds.
3. Replace APSEZ's preserved 100% single-industry row with reviewed segment
   revenue weights and, where possible, link the mix to an official source document.
4. Remove remaining legacy financial fallback only after representative backfill and reconciliation report full canonical coverage.
5. Add OCR, complex table reconstruction, and statement total/subtotal checks.

The active product status and ideation backlog are in
`docs/roadmaps/world-class-product-ideation-register.md`; trust-specific
acceptance criteria remain in
`docs/roadmaps/trust-and-evidence-checkpoint-2026-07-22.md`.

---

## 1. What This Project Is

A local-first Market Intelligence Engine and portfolio tracker for public equity research. It is **not** a trading bot, chatbot, or Bloomberg clone. It is a source-backed research system.

The core question it answers:

> What changed, why does it matter, how credible is it, does it affect my thesis, and how exposed am I through my portfolio?

The project has two major subsystems being actively built:
1. **Intelligence Pipeline:** SEC filings → events → scores → alerts → briefs
2. **Valuation Agent:** A Damodaran-style DCF system with assumption autofill, diagnostics, reverse DCF, and FCFE/DDM cross-checks

---

## 2. Tech Stack

| Layer | Technology | Notes |
|---|---|---|
| Backend | Python 3.14, FastAPI | Runs in Docker container |
| Database | PostgreSQL 16 | Docker volume `marketintel_postgres_data` |
| ORM | SQLAlchemy 2.0 (mapped_column style) | Declarative base in `app/db/base.py` |
| Migrations | Alembic | Current head `h4h4h4h4h4h4`; check `backend/alembic/versions/` for the full chain |
| Frontend | Next.js (App Router), Tailwind 4/PostCSS | TypeScript with owned design tokens and global primitives |
| Data files | Damodaran `.xls` spreadsheets | 35 files in `data/damodaran/raw/` |
| Containerization | Docker Compose | 4 services: postgres, backend, frontend, pgadmin |

---

## 3. Project Structure

```text
market-intelligence-md-files copy/
├── AGENTS.md                          # Agent operating manual (READ THIS FIRST)
├── README.md                          # Project overview
├── docker-compose.yml                 # 4 services: postgres, backend, frontend, pgadmin
├── alembic.ini                        # Points to backend/alembic
├── .env.example                       # Template for environment variables
├── .env                               # Actual env vars (DO NOT COMMIT)
│
├── backend/
│   ├── Dockerfile                     # Python 3.14-slim, WORKDIR /workspace
│   ├── requirements.txt               # FastAPI, SQLAlchemy, pandas, xlrd, openpyxl
│   ├── alembic/
│   │   ├── env.py                     # Imports all models via `from app import models`
│   │   └── versions/                  # Current Alembic migration chain through a7a7a7a7a7a7
│   └── app/
│       ├── main.py                    # FastAPI app + /api/health endpoint
│       ├── core/config.py             # Pydantic Settings, SEC_USER_AGENT validator
│       ├── db/
│       │   ├── base.py                # DeclarativeBase (THE canonical Base class)
│       │   └── session.py             # Engine + SessionLocal factory
│       ├── models/
│       │   ├── __init__.py            # Central model registry (imports ALL models)
│       │   ├── dcf.py                 # ValuationModel, DcfAssumptionSet, DcfOutput, etc.
│       │   ├── damodaran.py           # DamodaranDatasetFile
│       │   ├── damodaran_fundamentals.py  # All Damodaran benchmark models + RegressionModelCoefficient
│       │   ├── accounting.py          # DamodaranRdBenchmark, industry_rd_benchmarks
│       │   ├── real_options.py        # IndustryVolatilityBenchmark, RealOptionResult
│       │   ├── macro_sensitivity.py   # SectorMacroSensitivityBenchmark, MacroSensitivityResult
│       │   └── (24 other model files) # company, portfolio, event, alert, narrative, etc.
│       ├── api/
│       │   ├── routes.py              # Central router registry (37 router groups registered)
│       │   ├── schemas.py             # Pydantic schemas including ApiResponse envelope
│       │   ├── helpers.py             # Shared API helper functions
│       │   └── routers/               # 32 router files (incl. regression_priors, real_options)
│       ├── services/                  # 58 service files (business logic)
│       │   ├── dcf.py                 # FCFF DCF engine
│       │   ├── fcfe_ddm_engine.py     # FCFE and DDM cross-check engines
│       │   ├── reverse_dcf_engine.py  # Reverse DCF solver
│       │   ├── wacc_engine.py         # WACC calculation engine
│       │   ├── diagnostics_engine.py  # Assumption consistency checks
│       │   ├── real_options_service.py # Black-Scholes, eligibility, integration
│       │   ├── regression_prior_service.py  # Source-backed debt/yield/payout priors
│       │   ├── macro_sensitivity_service.py  # Top-down/bottom-up macro sensitivity
│       │   ├── damodaran_ingestion.py # Damodaran XLS file ingestion service
│       │   ├── damodaran_parser.py    # XLS parsing logic
│       │   ├── industry_assumption.py # Autofill assumptions from benchmarks
│       │   ├── industry_mapping.py    # Map company → Damodaran industry
│       │   ├── relative_valuation_service.py # Relative pricing (PE, PBV, etc.)
│       │   ├── accounting_normalization.py   # R&D capitalization, goodwill
│       │   └── (19 other service files)
│       └── providers/                 # Market data provider abstractions
│
├── frontend/
│   ├── Dockerfile                     # Next.js dev server
│   ├── package.json                   # Dependencies
│   ├── app/
│   │   ├── layout.tsx                 # Root layout with Sidebar
│   │   ├── page.tsx                   # Dashboard / Daily Brief
│   │   ├── valuation/page.tsx         # Valuation listing page
│   │   ├── valuation/quick/page.tsx   # Quick valuation workflow
│   │   └── (16 other page directories)
│   ├── components/
│   │   ├── dcf-form.tsx               # Full DCF assumption form (~28KB, needs refactor)
│   │   ├── advanced-workspace.tsx     # Advanced valuation workspace (~27KB, needs refactor)
│   │   ├── quick-valuation-workflow.tsx # Quick valuation UI
│   │   ├── sidebar.tsx                # Navigation sidebar
│   │   └── (16 other components)
│   └── lib/
│       ├── api.ts                     # Centralized API client (~32KB)
│       └── form-payloads.ts           # Form data transformation helpers
│
├── scripts/
│   ├── ingest_damodaran.py            # Ingests all 8 Damodaran XLS files into DB (incl. optvarIndia)
│   ├── seed_regressions.py            # Scoped sync for 6 models / 26 exact coefficients
│   ├── seed_regression_coefficients.py # Compatibility wrapper for canonical sync
│   ├── seed_sample_data.py            # Seeds sample companies
│   └── verify_milestone_a.py          # Verification script for Milestone A
│
├── data/
│   └── damodaran/raw/                 # 35 Damodaran XLS files (India-focused)
│
├── Data for Model/                    # Source Damodaran files + regression PDFs
│                                      # (superset of data/damodaran/raw/ + 3 PDFs)
├── damodaran_knowledge_base_v1/       # Canonical doctrine, source catalog, hashes,
│                                      # immutable originals, inbox, and audit tool
│
└── docs/
    ├── 00-current-state.md            # What works, what's mocked, what's missing
    ├── 01-product-brief.md            # Product requirements
    ├── 02-architecture.md             # System architecture
    ├── 03-database-schema.md          # Database table documentation
    ├── 04-data-sources-and-ingestion.md
    ├── 05-scoring-framework.md
    ├── 06-security-threat-model.md
    ├── 07-local-development.md
    ├── 08-execution-runbook.md        # Phase-by-phase implementation checklist
    ├── 09-beginner-glossary.md
    ├── agent_capabilities_and_limitations.md # Comprehensive product/agent capability audit
    ├── roadmaps/
    │   ├── market-intelligence-build-roadmap.md
    │   └── valuation-auto-pipeline-master-plan.md
    ├── skills/                       # Reusable project workflow skills for future agents
    ├── valuation-agent/
    │   ├── master-build-plan.md       # THE source of truth for valuation agent phases
    │   ├── autofill-workflow-plan.md  # Detailed autofill implementation spec
    │   ├── data-batch-build-plan-index.md
    │   ├── lecture-notes-absorption.md
    │   └── source-batches/            # Per-batch data specs
    └── archive/                       # Historical or needs-review docs
```

---

## 4. Critical Architecture Details

### 4.1 The Base Class Rule

**Every SQLAlchemy model MUST import Base from `app.db.base`:**

```python
from app.db.base import Base
```

**NEVER do `from app.models import Base`** inside a model file. This causes a circular import that crashes the entire backend container in a restart loop. This bug was fixed in `damodaran_fundamentals.py`, `damodaran.py`, and `accounting.py` on 2026-06-17 but the container may still need a rebuild.

### 4.2 How Models Are Registered

All models must be imported in `backend/app/models/__init__.py`. Alembic's `env.py` does `from app import models` which triggers `__init__.py`, which registers every model with `Base.metadata`. If you add a new model file, you must add its import to `__init__.py`.

### 4.3 API Response Envelope

Every backend endpoint uses this standard wrapper:

```json
{
  "data": {},
  "meta": {
    "status": "success",
    "source": "internal",
    "last_updated": "2026-06-17T10:00:00Z",
    "is_stale": false,
    "is_mock": false,
    "warnings": [],
    "confidence": "medium"
  },
  "errors": []
}
```

The Pydantic schema `ApiResponse[T]` lives in `backend/app/api/schemas.py`.

### 4.4 Docker Volume Mounts

From `docker-compose.yml`:

```yaml
volumes:
  - ./backend:/workspace/backend    # Backend code (hot-reload)
  - ./scripts:/workspace/scripts    # Utility scripts
  - ./data:/workspace/data          # Damodaran XLS files
```

The backend Dockerfile sets `PYTHONPATH=/workspace/backend` and `WORKDIR /workspace`.

### 4.5 Startup Command

```dockerfile
CMD ["sh", "-c", "alembic upgrade head && uvicorn app.main:app --app-dir backend --host 0.0.0.0 --port 8000 --reload"]
```

This means: if Alembic fails → the entire backend crashes → Docker restart loop.

---

## 5. What Has Been Built (Completed Phases)

### Intelligence Pipeline (Phases 0-14)
- ✅ Local Docker infrastructure (PostgreSQL, FastAPI, Next.js, pgAdmin)
- ✅ Full Alembic migration chain through `a7a7a7a7a7a7`
- ✅ API Response Envelope on all endpoints
- ✅ Processing Runs tracking for ingestion health
- ✅ SEC EDGAR ingestion (10-K, 10-Q, 8-K) with `SEC_USER_AGENT` validation
- ✅ RSS/News ingestion
- ✅ Event extraction and deterministic scoring
- ✅ Alert generation and review
- ✅ Daily Intelligence Brief
- ✅ Portfolio CRUD (holdings, transactions, cash, snapshots)
- ✅ Narrative tracking (clusters, claims, mentions)
- ✅ Thesis notes with assumptions and drift scores
- ✅ Score breakdown UI with weighted bar charts
- ✅ Research workspace (sessions, messages)
- ✅ Data Health page
- ✅ Frontend App Shell (Sidebar, TopBar, routing)
- ✅ US → India market identity transition (market, exchange, local_symbol, ISIN, FIGI)
- ✅ Source capability matrix (US vs India provider status)
- ✅ Country-aware valuation context (currency, benchmark country, risk-free rate)
- ✅ Financial extraction candidates from filing text
- ✅ Candidate review/override/reject/promote endpoints and fundamentals UI
- ✅ SEC XBRL `companyfacts` extraction foundation
- ✅ Company-to-Damodaran industry mapping field and endpoints

### Valuation Agent (from master-build-plan.md)
- ✅ **Phase 1 (FCFF Engine):** Core DCF calculation with FCFF, reinvestment, ROIC, terminal value, equity bridge
- ✅ **Batch 02 (Assumption Engine):** Industry assumption autofill from Damodaran benchmarks (margins, capex, WC, ROE, growth, financing flows)
- ✅ **Batch 03 (Accounting Normalization):** R&D capitalization, goodwill diagnostics
- ✅ **Batch 01 (Relative Pricing):** PE, PBV, PS, EV/EBITDA industry benchmarks
- ✅ **Batch 04 (FCFE/DDM/Payout):** FCFE engine, DDM engine, payout policy diagnostics, dividend/FCFE benchmarks
- ✅ **Batch 05 (Macro Sensitivity):** Duration, cyclicality, inflation, currency sensitivity. Top-down regression, bottom-up segment weighting, macro scenario translation. Data from `macro.xls` and `macrodur.xls`.
- ✅ **Batch 06 (Real Options):** Black-Scholes real option service, eligibility scoring (70+ weighted score), integration service with double-counting guardrail. Volatility benchmarks from `optvarIndia.xls`.
- ✅ **Regression Priors:** Six January 2025 Global/US debt-ratio, dividend-yield, and payout models with 26 exact source coefficients. Debt and yield APIs return low-confidence dated `Estimate` results with provenance and fit; weak payout models are disabled. API at `/api/priors/debt-ratio`, `/api/priors/dividend-yield`, and `/api/priors/dividend-payout`. The DCF debt-prior UI requires the source variables and contains no proxy or mock inputs.
- ✅ **WACC Engine:** Cost of equity, cost of debt, capital structure
- ✅ **Diagnostics Engine V1:** Assumption consistency, margin plausibility, ROIC vs WACC, terminal value discipline (6 checks)
- ✅ **Reverse DCF Engine:** Solve for implied growth rate from market price
- ✅ **Scenario Engine:** Bear/Base/Bull scenario comparison with range visualization
- ✅ **Sensitivity Engine:** WACC vs terminal growth tables
- ✅ **Narrative-to-Numbers:** AI-powered assumption extraction from thesis text
- ✅ **Valuation Memo Writer:** AI-generated analyst memos
- ✅ **Damodaran Data Ingestion:** Script to parse all 8 India XLS files into normalized DB tables

---

## 6. What Is Currently Broken or Risky

### 6.1 Backend Container Restart Loop (RESOLVED but be aware)

**Previous symptom:** `docker compose exec backend ...` returned "Container is restarting"

**Root cause was:** Circular imports in model files (`from app.models import Base` instead of `from app.db.base import Base`). This was fixed in `damodaran_fundamentals.py`, `damodaran.py`, and `accounting.py`.

**Current status:** Backend starts cleanly after rebuild. If it recurs, check `docker compose logs backend --tail 100` for Python tracebacks.

### 6.2 Models Not in `__init__.py` (RESOLVED)

The model registry drift has been fixed. `DecisionLog`, `EvidenceLedgerItem`, and `VariantPerception` are now correctly imported in `backend/app/models/__init__.py`.

### 6.3 `DcfAssumptionSet` has `beta` in migration but not in model (RESOLVED)

The `beta` column is now properly mapped in `DcfAssumptionSet` in `backend/app/models/dcf.py`.

---

## 7. What Is Mocked or Incomplete

| Feature | Status |
|---|---|
| Market Regime page | Explicitly mocked with `<MockDataState>` component |
| AI Summaries page | Falls back to mock if no `GEMINI_API_KEY` |
| Score Explanations | Backend calculates, but frontend doesn't have full breakdown for all score types |
| Data Honesty Layer | Main server-rendered pages now surface stale, partial, and mock states through shared `DataStateNotices`; nested/special-purpose pages still need opportunistic audit |
| Diagnostics Engine V2 | Core V2 checks exist and now have focused coverage in `backend/tests/test_diagnostics_engine_v2.py`; remaining work is UI/API exposure and any additional master-plan checks not represented in the current service |
| Regression Prior inputs | `insider_holdings`, `ebitda_to_value`, `intangibles_to_total_assets` are hardcoded proxies in the UI component. Real company data inputs not yet wired |
| Financial candidate promotion | Review/override/reject/promote tests exist. Promotion writes financial period/metric tables and normalized snapshots, prefers reviewed ISO currency units or filing metadata, and rejects conflicting currencies. Company currency is a warned fallback when sources omit currency |
| Normalized financial tables | Promotion writes normalized snapshots/metrics including direct cash, debt, diluted shares, capex, depreciation, and working-capital change. Older incomplete snapshots still need backfill before compatibility fallback can be removed |
| SEC XBRL extraction | Focused service test passes, and pseudo raw documents now use SEC source lookup/creation instead of assuming `source_id=1` |
| Assumption autofill | Autofill prefers normalized metrics, includes the main FCFF/FCFE bridge inputs and reporting-currency provenance, and uses only labeled compatibility fallback. Durable owned drafts persist provenance/edits/reviews, reject stale writes, reset fields to source, archive cleanly, and promote atomically |
| Industry mapping UI | Endpoints and valuation page section exist; needs focused tests and UX validation before treating as stable |
| Event-to-thesis impact classifier | Service and event-router hook exist, but it depends on Gemini and needs focused verification around model fields, missing API keys, and provenance |
| Broker Integrations | Not built (explicit non-goal) |
| Social/Twitter | Not built (explicit non-goal) |
| Auth/billing/production | Not built (explicit non-goal) |

---

## 8. Database Tables

### Core Tables (Migration 1: `365a2d347c17`)
`companies`, `sources`, `raw_documents`, `document_assets`, `events`, `event_corroborations`, `event_contradictions`, `alerts`, `alert_portfolio_impacts`, `thesis_notes`, `thesis_assumptions`, `thesis_changes`, `daily_briefs`, `portfolios`, `portfolio_holdings`, `portfolio_transactions`, `portfolio_cash_balances`, `portfolio_snapshots`, `market_prices`, `processing_runs`, `financial_statement_periods`, `financial_metrics`, `valuation_models`, `dcf_assumption_sets`, `dcf_projection_years`, `dcf_outputs`, `dcf_sensitivity_tables`, `dcf_decision_logs`, `filing_sections`, `filing_section_diffs`, `ai_outputs`, `social_posts`, `sentiment_scores`, `narrative_clusters`, `narrative_claims`, `narrative_mentions`, `scoring_configs`, `macro_series`, `macro_observations`, `oauth_tokens`, `research_sessions`, `research_messages`, `exposure_tags`, `company_exposure_tags`

### Damodaran Tables (Migrations 2-6)
- `damodaran_dataset_files` — tracks ingested XLS files
- `damodaran_industry_margin_benchmarks` — gross, EBITDA, EBIT, net margins
- `damodaran_industry_capex_benchmarks` — capex/revenue, capex/depreciation
- `damodaran_industry_wc_benchmarks` — working capital ratios
- `damodaran_industry_roe_benchmarks` — ROE, ROC
- `damodaran_industry_growth_benchmarks` — revenue and earnings growth
- `damodaran_industry_financing_flows_benchmarks` — net debt, equity issuance
- `regression_model_coefficients` — 26 source-backed coefficients across six January 2025 regression models
- `damodaran_industry_pricing_benchmarks` — PE, PBV, PS, EV/EBITDA
- `industry_rd_benchmarks` — R&D/revenue, R&D/EBITDA
- `industry_goodwill_benchmarks` — goodwill, impairment
- `industry_lease_benchmarks` — lease adjustments
- `damodaran_industry_dividend_benchmarks` — dividend yield, payout ratio
- `damodaran_industry_fcfe_benchmarks` — net income and FCFE before/after debt cash flows; legacy `fcfe` mirrors after-debt and unsupported components remain null
- `industry_volatility_benchmarks` — standard deviation of equity and firm values
- `real_option_results` — stored real option calculation results
- `sector_macro_sensitivity_benchmarks` — duration, cyclicality, inflation, currency coefficients
- `company_macro_sensitivity_results` — top-down/bottom-up macro sensitivity results
- `financial_extraction_candidates` — source-linked candidate metrics awaiting review
- `normalized_financial_snapshots` — normalized company financial snapshots populated by reviewed candidate promotion
- `normalized_financial_metrics` — normalized metrics with provenance and warnings populated by reviewed candidate promotion

---

## 9. Key Files to Read Before Making Changes

In priority order:

1. **`AGENTS.md`** — Non-negotiable operating rules. Read this first.
2. **`docs/valuation-agent/master-build-plan.md`** — Source of truth for valuation agent phases and architecture
3. **`docs/valuation-agent/autofill-workflow-plan.md`** — Detailed spec for the autofill workflow
4. **`docs/00-current-state.md`** — What works, what's mocked, what's missing
5. **`docs/08-execution-runbook.md`** — Phase checklist with validation steps
6. **`docs/02-architecture.md`** — System architecture overview
7. **`docs/03-database-schema.md`** — Database table documentation
8. **`docs/roadmaps/market-intelligence-build-roadmap.md`** — Forward-looking market-intelligence roadmap
8. **`backend/app/models/__init__.py`** — Model registry (what Alembic sees)
9. **`backend/app/api/routes.py`** — Router registry (what the API exposes)

---

## 10. What To Build Next

All Damodaran data batches (01–06), regression priors, company setup, filing acquisition, first-pass financial extraction candidates, candidate review/promote UI, SEC XBRL candidate extraction, and initial industry mapping/autofill wiring are in place. The next task should harden the research-to-valuation bridge rather than adding broad dashboard polish.

**Current execution override:** request/run correlation, response inventory,
the styling/token foundation, responsive shell/company tabs/route boundaries,
browser recovery coverage, and the clean release/CI baseline are complete.
Perform a database/document backup and restore drill next, then exact evidence
locators, AI citation/review controls, representative real-source US/India
certification, and accessibility/performance gates.

### Priority 1: Harden Phase 6 Financial Extraction Review
- Extend focused tests for review/override/reject/promote endpoints as edge cases are found.
- Keep the authenticated PDF browser workflow passing in the isolated E2E stack.
- Expand exact PDF evidence beyond current row/region overlays to validated
  cell geometry and additional reviewed statement layouts.
- Keep AAPL certification green and finish the staged Adani review/reconciliation
  before broadening parser confidence.

### Priority 2: Phase 7 Metric Normalization Engine
- Add a safe backfill command for snapshots created before direct bridge inputs were emitted.
- Add historical capex, depreciation, and working-capital trend outputs.
- Add lease liabilities and broader non-operating equity bridge inputs where reviewed source data exists.
- Preserve source-document currency confidence explicitly rather than inferring it only from units/payload metadata.

### Priority 3: Harden SEC XBRL Extraction
- Add endpoint tests for `POST /api/companies/{company_id}/extract-xbrl`.
- Record source/provenance warnings when SEC facts are partial.
- Add filing-specific statement mapping for structured facts that companyfacts cannot disambiguate.

### Priority 4: Phase 8/9 Industry Mapping and Assumption Autofill
- Add tests for industry mapping candidates and confirmation.
- Add historical capex and working-capital trends, lease liabilities, and broader non-operating equity bridge inputs.
- Add a safe backfill command for normalized snapshots created before direct bridge metrics were emitted.
- Remove compatibility fallback after old snapshots are backfilled and verified.

### Priority 5: Phase 10 Guided FCFF Valuation Workflow
- Extend the passing save/reset/refresh/archive/reopen/promotion browser workflow
  with review invalidation and stale-write conflict behavior.
- Harden scenario comparison and terminal-value diagnostics in the existing valuation workspace.

### Priority 6: Evidence Trail and Thesis Impact
- Event-to-assumption mapping (earnings → revenue growth, rate change → WACC)
- Valuation assumption change log
- Portfolio valuation staleness monitor
- Alerts: "assumption-breaking event", "valuation changed materially"

### Priority 7: Stronger Financial Extraction (XBRL)
- Add SEC XBRL companyfacts mapping for US companies.
- Add filing-specific XBRL statement parsing where source filings provide structured facts.
- Add PDF/table extraction for uploaded annual reports only after review UX exists.
- Keep India manual-first until a compliant NSE/BSE/vendor source is selected.

### Priority 8: Component Refactoring
- `dcf-form.tsx` (~31KB) and `advanced-workspace.tsx` (~34KB) need extraction into smaller components
- `lib/api.ts` (~43KB) should be split by domain

### Priority 9: Lifecycle / Special Cases
- Financial services model (PBV/ROE, not FCFF)
- Young loss-making company model
- Distressed company probability-weighted DCF
- Sum-of-the-parts model

---

## 11. Environment Variables

Required in `.env`:

```text
DATABASE_URL=postgresql+psycopg://marketintel:marketintel_password@localhost:5432/marketintel
SEC_USER_AGENT="YourName youremail@example.com"   # MUST contain @ symbol
APP_ENV=local
AI_DEMO_MODE=false
AI_PRIVACY_DISCLOSURE_VERSION=v1
# Optional; without it normal AI calls return AI_PROVIDER_NOT_CONFIGURED.
GEMINI_API_KEY=
```

Docker Compose overrides `DATABASE_URL` to use `postgres` hostname (Docker internal network).

The `SEC_USER_AGENT` validator in `config.py` will reject the default value. You must set a real contact string.

---

## 12. Running the Project

```bash
# Start everything
docker compose up --build -d

# Check health
curl http://localhost:8000/api/health

# Check backend logs
docker compose logs backend --tail 100

# Run migrations manually
docker compose exec backend alembic upgrade head

# Ingest Damodaran data
docker compose exec backend python3 /workspace/scripts/ingest_damodaran.py

# Synchronize source-backed regression coefficients
docker compose exec backend python /workspace/scripts/seed_regressions.py

# Run tests
docker compose exec backend pytest backend/tests/ -v

# Stop everything
docker compose down

# Nuclear reset (destroys all data)
docker compose down -v && docker compose up --build -d
```

---

## 13. Design Principles (from AGENTS.md)

1. **No fake intelligence.** Never present mock data as real. Label everything.
2. **No buy/sell recommendations.** Show evidence, not advice.
3. **Every claim needs a type:** Fact, Source Summary, Calculation, User Assumption, AI Interpretation, Estimate, or Mock Data.
4. **Growth must cost money.** High growth → reinvestment → return on capital.
5. **Backend does the math.** AI explains and audits, it does not freehand calculations.
6. **Every assumption needs a source:** User input, Company actual, Industry benchmark, Regression-implied prior, Market data, Agent suggested, Manual override.
7. **Dense, calm, professional UI.** No decorative gradients, no marketing-style dashboards.

---

## 14. User Preferences (from conversation history)

- The valuation agent should "act like a disciplined valuation analyst. It should not merely calculate. It should challenge."
- Use uploaded Damodaran XLS as seed datasets. Distinguish between "extracted company actuals" and "industry benchmark priors."
- India is the primary market focus (all Damodaran files are `*India.xls`).
- The user wants honest infrastructure — no false precision, no fake completeness.
- Component refactoring of `dcf-form.tsx` and `advanced-workspace.tsx` is desired but not urgent.
- Currency consistency checks should be warning barriers, not hard blocks.
- This handoff document is only updated when the user explicitly asks for it.

---

## 15. Common Pitfalls

| Pitfall | How to avoid |
|---|---|
| Circular import crash | Always import Base from `app.db.base`, never from `app.models` inside a model file |
| Container restart loop | Always check `docker compose logs backend` first. The CMD runs `alembic upgrade head` before the server starts — if migrations fail, everything fails |
| Missing model registration | Every new model must be imported in `backend/app/models/__init__.py` |
| Missing router registration | Every new router must be imported in `backend/app/api/routes.py` |
| Stale Docker image | After code changes, always `docker compose up --build -d` |
| SEC_USER_AGENT validation | Must contain `@` symbol or backend startup will fail |
| Giant diffs | Keep changes narrow. One feature = one commit scope. Don't reformat unrelated files |
| Hardcoded valuation data | Use Damodaran benchmark tables, never hardcode financial assumptions |
