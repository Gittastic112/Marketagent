# Source-Backed Synthetic Ratings Checkpoint

**Date:** 2026-08-08  
**Status:** Shipped and validated  
**Scope:** Approved `ratings.xls` table lookup and WACC API contract

## Problem Fixed

The WACC engine previously hardcoded approximate rating labels and default
spreads, supported only two firm classes, and returned no source provenance.
That contradicted the approved workbook and could materially distort cost of
debt.

## Fifteen Steps

1. Verified the immutable canonical workbook and runtime mirror.
2. Extracted and visually checked all three source tables.
3. Traced all service, API, test, frontend, and coverage consumers.
4. Defined explicit large non-financial, small/risky, and financial firm types.
5. Added a typed catalog containing all 45 exact source rows.
6. Bound catalog version `ratings-xls-45d1f61c67f0` to the source SHA-256.
7. Added exact lower-bound lookup semantics matching workbook behavior.
8. Preserved combined Moody's/S&P labels and decimal spreads.
9. Added finite-ratio validation.
10. Preserved the legacy `is_large_mfg` compatibility wrapper and API input.
11. Added explicit financial-firm API selection and conflict rejection.
12. Added selected-band, calculation, source, date-confidence, and recency provenance.
13. Added exact catalog, boundary, example, compatibility, and API tests.
14. Reclassified `ratings.xls` as supported in the application coverage register.
15. Reconciled the knowledge base, architecture, current state, runbook,
    roadmap, capability register, and handoff.

## Contract

`POST /api/valuation/wacc/calculate` accepts:

```text
firm_type = large_non_financial | small_or_risky | financial_service
```

When `firm_type` is omitted, legacy `is_large_mfg=true|false` still selects the
large or small non-financial table. Contradictory old and new inputs return
validation error `422`.

The response includes the selected band, rating, spread, catalog version,
source file/path/hash, `source_as_of=unknown`, `date_confidence=low`, and the
2026-08-07 `User Assumption` recency decision.

## Validation

- focused ratings/WACC/coverage slice: 27 passed
- full backend: 434 passed, four existing third-party `openpyxl` warnings
- frontend: 90 passed
- TypeScript: passed
- Next.js 16.2.11 production build: passed
- knowledge-base tests: 4 passed
- knowledge-base audit: 61 canonical files, 61 catalog rows, 38 processing rows,
  empty inbox
- canonical and runtime workbook hashes: matched catalog SHA-256
- `git diff --check`: passed

Browser automation was not rerun because no frontend consumer or visual surface
changed in this milestone.

## Limitation

The workbook's iterative operating-lease capitalization is not implemented.
Interest coverage supplied to the rating lookup must already include that
normalization when applicable. The service also remains an estimate fallback;
an observable market cost of debt should take precedence when reliable.

## Product Effect

Damodaran application coverage changes from 3 supported / 19 partial / 13
unsupported to 4 supported / 18 partial / 13 unsupported. The product remains
approximately 75% complete for the declared local-first scope and 64% against a
world-class daily-driver standard. This milestone improves financial
correctness and provenance, but does not close broader source coverage or daily
workflow gaps.

## Next Priority

Add source hash and source-as-of fields to stored benchmark dataset versions,
then convert the highest-value partial workbook source with an idempotent typed
importer. Implement operating-lease capitalization only as a separate reviewed
accounting-normalization workflow.
