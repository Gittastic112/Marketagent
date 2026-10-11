# Valuation source pipeline and US benchmarks

Date: September 22, 2026. Local personal-research scope, not a whole-product
completion or source-quality certification. The substantial pre-existing dirty
worktree was preserved. No migration or saved-model recalculation was required.

## Approved policy

- Latest completed financial year, not TTM.
- Populate drafts automatically; require review before saving a model.
- Weekdays at 07:00 America/New_York, with the computer, Docker and worker running.
- US-specific Damodaran priors, not India or global industry substitutes.

## Architectural changes and principal owners

| Responsibility | Implementation |
|---|---|
| Annual fact extraction | `backend/app/services/sec_xbrl_extractor.py`: v3 units, latest filing/amendment selection, explicit debt components, append-only revisions and separate share-class snapshots |
| Source-to-input adapter | `backend/app/services/valuation_source_inputs.py`: exact SEC/FRED/price links, annual/scale compatibility, source signatures and honest missing/stale states |
| Autofill and draft lifecycle | `assumption_autofill_engine.py` and `valuation_setup_draft.py`: edited values/provenance preserved, source changes invalidate affected review, row locks/version checks prevent stale writes |
| Background workflow | `valuation_source_refresh.py`, `schemas/valuation_refresh.py`, owned `api/routers/valuation_refresh.py`, and `workers/valuation_source_scheduler.py`: durable queue, provider-specific audits, partial outcomes and a PostgreSQL worker lock |
| UI | `frontend/lib/api/valuation-refresh.ts` and `components/valuation/source-refresh-panel.tsx`: immediate queueing, polling/resume after reload, scoped results, original dates, explicit partial failures and edit locking |
| US benchmark intake | `damodaran_us_ingestion.py`, the existing typed importers/coverage registry and `scripts/ingest_damodaran.py --market US`: explicit dated/geographic contracts, audit and idempotence |
| Methodology integrity | `assumption_methodology.py` and `industry_assumption.py`: US aliases, truthful global-input labels, no fabricated adjusted-margin proxies |
| Runtime | `.env.example` documents opt-in settings; the ignored local environment enables the approved schedule. Compose adds a separate unexposed source worker; existing brief scheduling remains separate |

This is cross-cutting work because source extraction, deterministic adapters,
draft persistence, queue ownership, browser state, source intake and deployment
must share the same review/provenance contract. Calculations remain backend-owned.
No new package dependency was added for these changes.

## Source and financial integrity

SEC v3 adds cash-flow, payout, tax, equity, lease and debt-component tags.
Long-term debt or commercial paper alone is not complete borrowing coverage.
Compatible complete components may produce a review-required calculation; other
debt remains unresolved. Legacy long-term-only candidates are not silently used
as total debt. Reviewed normalized financial facts were not rewritten.

Annual issuer weighted-average shares retain an explicit class/dilution warning.
GOOGL can use its explicit regulatory CIK without reusing GOOG prices or claiming
issuer shares are Class A shares. This is not a dedicated issuer/security model.

FRED DGS10 percentages are converted to a dated USD proxy, never applied to INR
cash flows. NFCI is stored through the existing macro pipeline. Same-date FRED
revisions require review rather than overwrite. Stored quotes keep their original
date; mock-marked prices are excluded. Provider failure does not become live success.
Reviewed million-scale annual data is not mixed with full-currency SEC candidates.

Companyfacts downloads now check the existing safe-URL helper, prohibit redirects,
bound declared/decoded bodies to 32 MiB, use a 20-second I/O timeout and check a
60-second elapsed deadline between chunks. This is not hard wall-clock cancellation
of DNS or an in-flight read. Invalid/wrong-issuer payloads fail before candidate writes.
The final live AAPL check, run 68, succeeded with 123 existing candidates and no additions.

## US benchmark evidence

Six January 5, 2026 US datasets were inspected: beta, WACC, margins, capex,
ROE and working capital. Three existing originals were reused byte-for-byte;
three official originals were routed through the knowledge-base inbox. Embedded
date/population, source formulas, names/comments and column meanings were checked.
The original workbooks were not modified or presented as newly dated company facts.
The spreadsheet workflow informed the source-scope and formula review, not model approval.

Runs 56-61 created 1,131 source-linked records and six active versions. Runs 62-67
created zero duplicate records/versions. Final application coverage is 24 active
typed sources, 3,756 rows and 24 complete provenance records; the 41-mirror
registry classifies 14 supported, 18 partial and 9 unsupported sources.
US rows do not deactivate India versions or create artificial INR rate methods.
All six US drafts now offer the dated US ERP prior; all 11 company industry
mappings remain unconfirmed. No review box or saved model was approved.

The India WACC workbook explicitly labels its D10/D11 inputs Global weighted
average. Read-time labels now reflect that source scope. US ERP and a current
Treasury proxy still require review of date and sovereign-risk conventions.
Unadjusted EBIT/EBITDA are no longer exposed as lease/R&D-adjusted margins.
See the [source intake record](../../../../damodaran_knowledge_base_v1/reference/us_benchmark_intake_2026.md).

## Normal runtime and preservation

Backup `backups/20260922T135330Z-market-intelligence` was checksummed and
independently restored to the separate disposable `source_refresh_preservation`
database. Canonical PostgreSQL row-JSON fingerprints compared all 107 tables.
Final normal data has 93 identical table fingerprints. Every prior row in all
11 benchmark/method tables is identical; six of those tables have new US rows.

| Expected changed table | Before | After |
|---|---:|---:|
| assumption_method_values | 1,276 | 2,031 |
| damodaran_dataset_files | 18 | 24 |
| damodaran_industry_capex_benchmarks | 94 | 188 |
| damodaran_industry_margin_benchmarks | 94 | 188 |
| damodaran_industry_roe_benchmarks | 94 | 188 |
| damodaran_industry_working_capital_benchmarks | 94 | 188 |
| company_market_data | 11 | 11 |
| financial_extraction_candidates | 187 | 694 |
| macro_series | 0 | 2 |
| macro_observations | 0 | 196 |
| market_prices | 1,549 | 1,560 |
| raw_documents | 5 | 6 |
| valuation_setup_drafts | 1 | 11 |
| processing_runs | 28 | 68 |

Saved models (2), assumption versions (4), holdings (2), transactions (3), other
portfolio activity and historical outputs remain byte-identical. All 694 SEC
candidates remain unreviewed; no normalized financial snapshots were approved.

The first scheduled batch had partial outcomes, including unsupported India SEC
coverage and a GOOG/GOOGL source-hash collision. The security-specific snapshot
repair was tested; GOOGL retry run 51 succeeded and created 103 candidates in
child run 54. The original failed attempt remains visible in Processing Runs.
FRED imported 196 observations; four missing DGS10 observations were skipped.

The final backend, standalone frontend and source worker were recreated locally.
Health/readiness returned 200 with migration head p7p7p7p7p7p7. Normal PostgreSQL
was not recreated. All published application/admin/database ports remain bound
to 127.0.0.1; neither scheduler publishes a port. The approved next run is
September 23 at 11:00 UTC, or 07:00 New York time. There is no missed-day backfill.

## Verification

- Full source-mounted, network-disabled backend suite: 1,155 passed, five upstream
  Starlette/anyio/openpyxl deprecation warnings.
- Frontend: 221 tests and TypeScript passed. Final production build passed.
- Backend/worker production images passed. Docker Hub Node metadata timed out;
  frontend builds used verified cached Node 24/dependency images with matching
  package/lock hashes, rebuilding the final source and standalone output. No
  dependency updates or secret-copy exceptions were used.
- Static gates: 16 documentation/security/Compose/backup workflow tests, secret
  scan and 11 project-workflow checks passed. Final active-doc/link check passed
  after checkpoint creation: 74 active Markdown files and 591 local links.
- Knowledge base: audit status OK, 64 canonical originals/catalog rows, 44 ledger
  rows, zero pending inbox files and four audit-tool tests passed. Existing raw
  hashes remain intact.
- Authenticated, isolated browser fixture: edited revenue 1,234 persisted before
  enqueue and survived refresh. Reload resumed the same queued run without a
  duplicate job. Editing was disabled while pending and restored after completion.
  Missing FRED/SEC/provider coverage remained visibly partial; draft creation
  succeeded without model creation or automatic review. Fixture model count stayed 2.
- Final layout checks: 1440px desktop and 390px mobile, no horizontal page overflow,
  unlabelled visible fields or unnamed visible buttons. Final desktop/mobile
  captures were visually inspected. This is focused Mock Data UI proof, not
  company-source certification or a complete accessibility audit.

Local artifacts live under `output/playwright/source-refresh-2026-09-22/`, including
final desktop/mobile captures and the read-only preservation audit. The separate
browser session was closed. Deleting its disposable Docker environment/restored
backup copy was blocked by the safety reviewer, so approval was requested. No
test database deletion occurred. Its test web services were stopped as a
non-destructive alternative; temporary PostgreSQL remains running. The normal
backup, user database and verification artifacts are retained. Cleanup status
lives in the single ledger.

## Remaining work

Use the [single limitation ledger](../../../agent_capabilities_and_limitations.md).
No completion claim is made for every forecast input, company disclosure, India
statement workflow, issuer/share reconciliation or public-deployment requirement.
Review mappings, source units, borrowing scope and model assumptions before saving.
