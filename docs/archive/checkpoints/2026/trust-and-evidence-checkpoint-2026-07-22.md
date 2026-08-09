# Trust and Evidence Checkpoint - 2026-07-22

This file separates the features shipped in the 2026-07-22 trust pass from proposed follow-up work. A proposal below is not proof that the feature exists.

For the active cross-product status and ideation backlog, read
[world-class-product-ideation-register.md](world-class-product-ideation-register.md).

## Shipped In The 2026-07-25 Follow-Up

| Area | Implemented behavior | Verification |
|---|---|---|
| Diff rendering security | Filing text is HTML-escaped before storage; the frontend parses only generated add/remove semantics into React text, protecting legacy rows without `dangerouslySetInnerHTML` | Backend and frontend diff security tests |
| Structured candidate evidence | Text, Screener, and XBRL candidates store typed source locators; candidate review deep-links into the owning document | Migration `f6f6f6f6f6f6`, extraction/API/frontend tests |
| Processing-run lifecycle | Filing extraction, SEC XBRL, Screener upload, and normalized backfill preview/apply persist standardized run outcomes | Focused processing-run tests and expanded `/ingestion/status` |
| Financial reconciliation | Source-versus-normalized exact, mismatch, missing, normalized-only, delta, provenance, and warning states are exposed in API/UI | Backfill/reconciliation regression test |
| Broader valuation bridge | Basic shares, acquisitions, lease liabilities, minority interests, preferred stock, and employee option value normalize with provenance; supported fields feed autofill | Normalization and autofill tests |
| Honest missing direct metrics | Absent reported revenue, EBIT, and net income are no longer materialized as zero-valued reported metrics | Reconciliation regression test |

## Shipped In This Checkpoint

| Area | Implemented behavior | Verification |
|---|---|---|
| Extraction routing | Filing and XBRL writes use their registered `/api` routes; multipart browser writes use the same-origin proxy | Frontend API/source regression tests |
| Candidate evidence | Candidates store source line, explicit page/section markers, warning codes, confidence, and unit state | Backend extraction tests and migration `e5e5e5e5e5e5` |
| Candidate review | Review/override requires a reporting unit; the UI exposes evidence and warnings | Backend API tests and frontend typecheck |
| Screener upload | `.xlsx` only, 2MB limit, content hash, duplicate rejection, valid source/raw document, temporary cleanup, processing run | Backend upload test |
| Normalized coverage | Coverage endpoint plus before/after backfill detail, trust-ready counts, stale/missing snapshots, and currency conflicts | Backend coverage/backfill tests |
| Valuation freshness | Financial actuals older than 550 days and market prices older than 7 days require explicit review; unknown timestamps are flagged | Valuation draft lifecycle tests |
| Local auth readiness | Non-secret readiness endpoint; sign-in disabled until configuration is verified | Frontend source regression test |

## Proposed Follow-Up Features

### P1. Authenticated Browser Lifecycle Suite

**Status:** In progress. Isolated valuation-draft and PDF review/promotion/reconciliation
workflows are shipped. Company setup, alert evidence, provider failure, and stale-write
browser coverage remain.

**Why:** Backend tests cover state transitions, but a configured browser session has not exercised save, refresh, reset, archive, reopen, conflict, and promotion together.

**Acceptance criteria:**

- Runs against local seeded India and US companies without live provider calls.
- Verifies signed-out redirect and configured/unconfigured readiness states.
- Exercises draft save, source refresh, stale-write conflict, reset, archive/reopen, and one atomic promotion.
- Captures screenshots only for failures and never stores credentials in test files.

### P2. Audited PDF and Table Evidence

**Status:** In progress. Structured Screener table/cell locators, XBRL fact locators, text locators, and candidate-to-document links shipped on 2026-07-25. Audited PDF coordinates and table reconstruction remain proposed.

**Why:** Explicit text page markers are useful but are not PDF coordinates or table-cell evidence.

**Acceptance criteria:**

- Stores document id, page, table identifier, row label, column header, and cell coordinates for each extracted value.
- Reconciles comparative periods and statement totals before assigning high confidence.
- Keeps parser output as candidates until user review.
- Provides a source deep link or rendered-page anchor from the review UI.
- Adds fixture-based tests for multi-column statements, negative values, unit scaling, and duplicate periods.

### P3. Canonical Financial Reconciliation and Legacy Retirement

**Status:** In progress. The reconciliation endpoint/UI and broader bridge metrics shipped on 2026-07-25. Representative India/US coverage and legacy retirement remain proposed.

**Why:** Legacy fallback is still required for uncovered or blocked periods.

**Acceptance criteria:**

- Coverage reports 100% normalized and 100% trust-ready for selected representative companies.
- Lease liabilities, acquisitions, minority interest, preferred stock, and share-count bridges are normalized with units/provenance.
- A reconciliation report compares source, legacy, and normalized values before fallback removal.
- Legacy reads are removed only after tests prove no silent valuation input loss.

### P4. Alert-to-Evidence Deep Links

**Status:** In progress. Typed authenticated event evidence and user-owned alert evidence
endpoints now return claim type, confidence, source timestamp, explicit evidence status,
safe bounded context, document/source metadata, and user-filtered thesis/valuation impacts.
Alert cards, the alerts table, and the new alert detail route open the same typed drawer.
Raw filing text and provider payloads are not serialized. Links are document-level because
events do not yet persist an exact page/section/span locator.

**Why:** Alerts and events exist, but the user cannot consistently jump to the exact supporting source text.

**Acceptance criteria:**

- Every alert exposes event, document, source timestamp, claim type, confidence, and supporting excerpt location.
- Missing evidence produces an explicit incomplete state, not an empty successful panel.
- Links preserve company context and never render imported HTML as trusted markup.

The first two metadata requirements and the incomplete state are shipped. Exact supporting
passage location and highlighting remain the acceptance blocker.

### P5. Native, Reporting, and Valuation Currency Model

**Status:** Proposed.

**Why:** Currency provenance exists, but cross-market comparison and FX conversion remain basic.

**Acceptance criteria:**

- Separates native security currency, financial reporting currency, portfolio base currency, and valuation currency.
- Every conversion stores rate, source, as-of timestamp, and formula.
- Stale or missing FX blocks converted totals or labels them unavailable.
- DCF cash flow and discount-rate currency consistency remains enforced.

### P6. Official India Filing and Fundamentals Provider

**Status:** Proposed, provider decision required.

**Why:** India filing/fundamental coverage is currently manual-only.

**Acceptance criteria:**

- Uses an official, licensed, or explicitly approved structured source.
- Adds capability and provider-health states before enabling UI automation.
- Creates raw documents, content hashes, processing runs, and source timestamps.
- Handles rate limits, duplicates, source failures, and partial coverage without fake fallback data.

### P7. Background Extraction and Backfill Runs

**Status:** Proposed.

**Why:** Screener uploads now have processing runs, but filing extraction and normalization backfill are synchronous and can become slow as coverage expands.

**Acceptance criteria:**

- Every external or long-running extraction/backfill action creates a processing run with counts and safe errors.
- Retries are idempotent and do not duplicate candidates or snapshots.
- UI shows queued/running/completed/failed/partial states with last update time.
- Cancellation or retry semantics are documented before a worker system is introduced.

## Explicitly Deferred

- Public deployment security, team accounts, or broker synchronization.
- Unlabeled AI extraction or valuation math.
- Live trading, execution, or buy/sell recommendations.
- Market-regime automation until source coverage and deterministic formulas are available.

## Recommended Order

1. Finish P4 exact alert/event source locators and add its browser workflow.
2. Finish P2 audited PDF overlays and complex table reconstruction.
3. Complete P3 representative reconciliation and legacy retirement.
4. Broaden P1 browser coverage to setup, conflict, and provider failure states.
5. P5 currency/FX model.
6. P6 India provider after source approval.
7. Finish P7 background workers only when synchronous duration becomes material.
