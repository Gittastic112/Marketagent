# Damodaran Application Coverage Checkpoint

**Date:** 2026-08-08  
**Status:** Shipped and validated  
**Scope:** The 35-workbook application runtime mirror

## Outcome

The application can now answer which Damodaran sources are merely present,
which have source-specific typed ingestion, which metrics are stored or omitted,
where rows live, and whether the source is current, historical, unknown-date, or
accepted as recent by user assumption.

This is an honesty and planning milestone. It does not make all 35 workbooks
usable.

## Shipped Contract

`GET /data-health/damodaran-coverage` returns:

- inventory version and generation time
- canonical path, filename alias, geography, source date, and date confidence
- physical runtime-mirror presence
- supported, partial, or unsupported implementation state
- ingested, metadata-only, not-ingested, or source-missing state
- destination tables and live typed-row counts
- current, stale, historical, unknown, or user-assumed-recency state
- stored metrics, missing metrics, limitations, and required action
- aggregate warnings and counts

All routes remain authenticated. The response uses the standard API envelope,
is explicitly non-mock, and labels each inventory row as a `Source Summary`.

## Local Snapshot

| Measure | Result |
|---|---:|
| Runtime-mirror sources | 35 |
| Mirror files present | 35 |
| Sources with typed rows | 8 |
| Typed rows | 2,693 |
| Fully supported sources | 4 |
| Partial sources | 18 |
| Unsupported sources | 13 |
| Historical-only sources | 2 |
| User-assumed recent sources | 1 |

The eight sources that currently have typed rows are:

- `capexIndia.xls`
- `divfcfeIndia.xls`
- `divfundIndia.xls`
- `macro.xls`
- `macrodur.xls`
- `marginIndia.xls`
- `optvarIndia.xls`
- `wcdataIndia.xls`

## Status Rules

- `supported`: source-specific ingestion persists the decision-relevant source
  fields used by an application workflow.
- `partial`: only part of the source is persisted, or a destination/service
  exists without a complete source-backed path.
- `unsupported`: no source-specific typed application contract exists.
- `ingested`: at least one source-specific typed row exists.
- `metadata_only`: a generic parse/file record exists, but no typed benchmark
  row exists.
- `not_ingested`: the source is present but has no typed rows.
- `source_missing`: the expected application mirror file is absent.

Import timestamps are not freshness dates. Freshness uses the canonical source
date. `ratings.xls` remains source-date unknown and low confidence; the user's
recency decision appears separately as `user_assumed_recent`.

## Architecture

- Registry and live count service:
  `backend/app/services/damodaran_coverage.py`
- Typed API schema and route:
  `backend/app/api/schemas.py` and
  `backend/app/api/routers/evidence_integrity.py`
- Frontend contract and report:
  `frontend/lib/api.ts` and `frontend/app/data-health/page.tsx`
- Focused backend verification:
  `backend/tests/test_damodaran_coverage.py`
- Frontend contract verification:
  `frontend/lib/frontend-integrity.test.ts`

No database migration was needed. The report reads existing dataset metadata and
typed destination tables.

## Validation

- backend: 422 passed
- frontend: 90 passed
- TypeScript: passed
- Next.js 16.2.11 production build: passed
- knowledge-base tests: 4 passed
- knowledge-base audit: 61 canonical files, 61 catalog rows, 38 processing rows,
  empty inbox
- `git diff --check`: passed

Four third-party `openpyxl` datetime deprecation warnings remain. Browser
automation was not rerun.

## Remaining Work

1. [Completed 2026-08-08] Replace the approximate hardcoded synthetic-rating
   bands with a versioned table extracted from approved `ratings.xls`.
2. [Completed initial slice 2026-08-08] Add source hash and source-as-of fields
   plus preserved versions for Capex and ROE; remaining importers still require
   conversion.
3. Convert the highest-value partial sources before adding low-value tables.
4. Keep generic admin parsing visibly metadata-only.
5. Add source-specific idempotence and parser tests with each new importer.

Completion percentages remain 75% local-first and 64% world-class. This work
improves truthfulness and execution efficiency more than end-user analytical
breadth.
