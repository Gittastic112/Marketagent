# Next 10: Financial Integrity and Industry Mix Checkpoint

**Date:** 2026-08-02  
**Status:** Implemented and validated, with one browser execution limitation

## Completed Steps

1. Reran the guarded APSEZ finalizer with the 2026-08-02 cutoff. It created zero
   candidates, promoted zero facts, retained 27/27 exact reconciliations, and
   kept two-market certification passed.
2. Added a portable certification manifest that resolves companies by market,
   local symbol, optional exchange/regulatory identity and source documents by
   official payload or asset SHA-256. Every selector must resolve exactly once.
3. Exposed per-allocation benchmark-module availability and blended-field
   coverage on the industry-mix API.
4. Added optional company-owned source-document provenance, as-of date, and
   basis notes to the weighted-mix editor and synchronized returned coverage
   after save.
5. Added an authenticated Playwright workflow for a sourced 60/40 industry mix,
   persistence, API verification, and reload. TypeScript and Playwright test
   discovery pass; the browser case was not executed in this batch.
6. Hardened APSEZ EBIT calculations so every named component and value must be
   present on the declared PDF page before an existing or new candidate can pass.
   Targeted PDF ingestion now preserves the full physical page count separately
   from scanned pages, and the finalizer repairs the two affected APSEZ assets.
7. Extended Data Health to detect inexact promoted locators, missing/ambiguous
   fiscal periods, missing/invalid locator ends, invalid stored PDF pages, and
   source/stored period-end mismatches.
8. Added derived Data Health counts for promoted facts, annual periods, eligible
   histories, represented markets, and financial certification status. This
   derived badge requires promoted evidence; merely reviewed candidates do not
   qualify.
9. Added deterministic financial-history signatures to valuation drafts so
   source-derived values refresh after normalized history changes without
   overwriting reviewed user edits.
10. Reconciled current-state, architecture, schema, local development, runbook,
    handoff, certification checkpoints, roadmap, and product register.

## Live Proof

```text
portable certification: passed
certified histories: 2
certified markets: IN, US
promoted financial facts checked: 75
annual periods checked: 7
financial integrity issues: 0
APSEZ EBIT candidate creation on rerun: 0
APSEZ promotions on rerun: 0
APSEZ reconciliation: 27/27 exact
APSEZ physical page repair: 2 records, then 0 on immediate rerun
```

## Validation

```text
backend: 391 passed, 4 upstream openpyxl deprecation warnings
frontend: 75 passed
TypeScript: passed
Next.js 16.2.11 webpack production build: passed
secret scan and scanner tests: passed
project skills: 11 passed
git diff check: passed
Alembic head: j6j6j6j6j6j6
```

## Remaining Limits

- APSEZ still has a preserved 100% `Packaging & Container` user assumption. No
  segment percentages were invented. Replace it only from a reviewed source.
- That benchmark currently has partial field coverage; unavailable blended
  priors remain unavailable rather than being renormalized around gaps.
- The AAPL SEC Company Facts snapshot has no single document-level publication
  timestamp, so one freshness warning remains. Each certified XBRL locator still
  carries its filed date; no date was invented to suppress the warning.
- The representative corpus covers one US structured issuer and one India PDF
  issuer. It does not certify arbitrary filings, OCR, complex merged tables, or
  broad accounting-policy variation.
- The new weighted-mix browser workflow is registered but still needs an
  isolated-stack execution before it can be counted as passing.

## Next Recommended Work

Broaden audited extraction with statement identity, total/subtotal checks, and
rendered PDF evidence coordinates for one additional issuer per market. Keep the
AAPL/APSEZ portable manifest and Data Health financial audit green throughout.
