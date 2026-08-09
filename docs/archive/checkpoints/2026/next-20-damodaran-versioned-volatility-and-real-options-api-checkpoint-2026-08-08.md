# Versioned Volatility and Real-Options API Checkpoint

**Date:** 2026-08-08  
**Status:** Shipped and validated  
**Scope:** Preserved `optvarIndia.xls` ingestion and an honest real-options API

## Outcome

Volatility is the seventh typed Damodaran source on the shared preserved-version
lifecycle. Identical bytes verify and reuse existing rows, changed bytes retain
history, and a known historical hash can be reactivated without duplication.
Pre-migration rows remain stored with a null version link because their original
source bytes cannot be proven; active reads and coverage counts exclude them.

The exact source contract includes all six industry columns and both workbook
assumptions:

- `Relative Standard Deviation of Bonds = 0.40`
- `Correlation between stocks & bonds = 0.50`

The importer stores source date `2026-01-05`, preserves real zeros and nulls,
excludes Total Market aggregates, rolls back empty imports, and fails before
metadata creation when required source structure is absent.

The real-options API now uses the canonical paths already expected by the
frontend. Responses select only the active linked dataset and expose claim type,
version ID, source file, SHA-256, source date, date confidence, and canonical
path. Missing benchmarks return `VOLATILITY_BENCHMARK_NOT_FOUND`; the former
generic `0.40/0.30/0.70/0.30` fallback was removed.

## Twenty Delivered Steps

1. Traced the source, model, importer, API, coverage, tests, and documentation.
2. Verified runtime and canonical workbook SHA-256 equality.
3. Inspected exact headers, source assumptions, nulls, and representative rows.
4. Audited the broken canonical real-options paths and fabricated fallback.
5. Defined a nullable legacy-compatible dataset-version link.
6. Added exact-source and same-hash ingestion tests.
7. Added changed-hash preservation and historical-reactivation tests.
8. Added API tests for active-only reads, provenance, zeros, nulls, and not-found.
9. Added migration-chain and Data Health contract tests.
10. Added migration `m9m9m9m9m9m9` and the indexed foreign key.
11. Replaced permissive volatility matching with exact required headers.
12. Parsed and stored both workbook-level source assumptions.
13. Moved volatility ingestion to `DamodaranDatasetVersionService`.
14. Changed the API query to require the active linked version.
15. Registered canonical `/api/valuation/options/*` paths and hidden aliases.
16. Updated Data Health to count active linked rows and inventory `2026-08-08.4`.
17. Updated the operator script to print active volatility provenance.
18. Applied the migration and ran the live import twice.
19. Ran focused, full backend, frontend, build, migration, and KB validation.
20. Reconciled handoff, architecture, schema, ingestion, runbook, limitations,
    status, product register, documentation indexes, and KB processing state.

## Live Evidence

| Measure | Result |
|---|---:|
| Active volatility version | `#45` |
| Source SHA-256 | `763b4a907f9584395e5cba1bb428f064dd6a85ff90a08e0bfb80d919d97cb54b` |
| Source as-of | `2026-01-05` |
| Active typed rows | 94 |
| Sources with typed rows | 9 of 35 |
| Total typed rows | 2,787 |
| Supported / partial / unsupported | 5 / 17 / 13 |
| Complete / partial / missing provenance | 7 / 0 / 0 |
| Active mirror hash mismatches | 0 |

Two consecutive live imports returned version `#45`, the same source hash/date,
and 94 rows.

## API Contract

Canonical routes:

```text
GET  /api/valuation/options/volatility
POST /api/valuation/options/eligibility
POST /api/valuation/options/calculate
```

The old `/volatility`, `/eligibility`, and `/calculate` aliases remain hidden
from OpenAPI for compatibility. Volatility values are nullable because the
source contains legitimate missing cells. Numeric zero is not treated as absent.

## Operator Command

```bash
docker compose exec backend alembic upgrade head
docker compose exec backend python /workspace/scripts/ingest_damodaran.py --only volatility
```

## Validation

- focused volatility/version/API/coverage/migration: 28 passed
- complete backend: 461 passed, 4 upstream `openpyxl` deprecation warnings
- frontend: 90 passed
- TypeScript: passed
- Next.js 16.2.11 production build: passed
- Python compile: passed
- Alembic current/head: `m9m9m9m9m9m9`
- knowledge-base tests: 4 passed
- knowledge-base audit: 61 canonical files, 61 catalog rows, 38 processing rows,
  empty inbox
- `git diff --check`: passed

The first build attempt was blocked by the sandbox denying Turbopack a local
process/port. The identical build passed with the required host permission.
Browser screenshots were not rerun because no rendered component changed.

## Remaining Limitations

1. PE, PBV, PS, and EV/EBITDA share one typed table and retain destructive
   replacement behavior. They need a version design that does not erase sibling
   source fields or merge incompatible source histories.
2. Country statistics also retain legacy replacement behavior.
3. Pre-migration volatility rows remain unversioned and are intentionally not
   relabeled with today's mirror hash.
4. Industry volatility is a prior, not a company or project fact.
5. The generic admin comparison endpoint remains mock.
6. One-active-version uniqueness is controlled by the serial service path, not
   a partial database uniqueness constraint.

## Next Recommended Work

Design and convert the four shared pricing importers as one coherent versioning
boundary. Each workbook needs its own preserved dataset version while active
pricing reads must assemble compatible fields without treating one source's row
as provenance for another source's columns. Convert country statistics after
that. Add `fundgrEBIndia.xls` only once these remaining replacement paths are
closed.

Product completion remains **75% local-first** and **64% world-class**. This
batch fixes benchmark reproducibility and API honesty; it does not broaden live
provider coverage, portfolio attribution, or issuer certification.
