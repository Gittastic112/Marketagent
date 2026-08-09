# Versioned Pricing and Relative-Valuation Checkpoint

**Date:** 2026-08-08  
**Status:** Shipped and validated  
**Scope:** PE, PBV, PS, and enterprise-multiple source contracts plus active relative valuation

## Outcome

The four Damodaran India pricing workbooks now have independent preserved
dataset versions even though their sparse typed rows share one table. Identical
bytes verify and reuse existing rows, changed bytes preserve history, and a known
historical hash can be reactivated without duplication.

The prior relative-valuation reader used `.first()` for an industry. That could
return any one sparse source row and silently suppress the other three source
families. The service now assembles PE, PBV, PS, and EV/EBITDA only from their
active source versions. Every calculation includes the exact source version,
file, hash, source date, date confidence, and canonical path used by that method.

## Twenty Delivered Steps

1. Traced all four importers, the shared model, API routes, frontend, tests, and docs.
2. Verified all four runtime hashes, canonical paths, dates, headers, and row shapes.
3. Locked the exact PE header and representative source values.
4. Locked the exact PBV header and representative source values.
5. Locked the exact PS header and representative source values.
6. Locked the duplicate EV-multiple header groups and column order.
7. Proved the sparse-row first-match consumer defect.
8. Defined independent active-version semantics for each source code.
9. Defined active source-separated benchmark assembly and provenance.
10. Added exact PE growth/aggregate, PBV return, PS margin, and EV normalization fields.
11. Added additive migration `n0n0n0n0n0n0`.
12. Added exact-source ingestion and representative-value tests for all four files.
13. Added same-hash, changed-hash, and historical-reactivation tests.
14. Added fail-closed parser-contract and aggregate-exclusion tests.
15. Converted all four importers to `DamodaranDatasetVersionService`.
16. Replaced arbitrary reads with active source-code assembly.
17. Added per-method provenance and explicit unavailable-method diagnostics.
18. Added canonical `/api/valuation/relative/*` routes and frontend provenance states.
19. Applied the migration and proved two live scoped imports are idempotent.
20. Reconciled Data Health, architecture, schema, runbook, handoff, status, register, and KB docs.

## Exact Source Coverage

| Source | Retained controls |
|---|---|
| `peIndia.xls` | Firm count, losing-firm share, current/trailing/forward PE, two aggregate PE variants, expected five-year growth, PEG |
| `pbvIndia.xls` | Firm count, PBV, ROE, EV/invested capital, ROIC |
| `psIndia.xls` | Firm count, price/sales, net margin, EV/sales, pre-tax operating margin |
| `vebitdaIndia.xls` | Firm count and positive-denominator/all-firm EV/R&D-adjusted EBITDA, EV/EBITDA, EV/EBIT, and EV/after-tax EBIT |

All four sources are dated `2026-01-05`. Importers require exact headers before
version metadata creation, preserve source zero/null cells, exclude Total Market
aggregates, and roll back empty imports.

## Live Evidence

| Source | Version | Rows | SHA-256 |
|---|---:|---:|---|
| PE | `#46` | 94 | `e363c3fefb9bc3d225239d5823c18b09586bd91264151c3442d380bbcbbc21f4` |
| PBV | `#47` | 94 | `1944f8604552632a2e2470ba36f109e7e3d2ecc7e6d9da2aaf5793c7b004d615` |
| PS | `#48` | 94 | `dc40093f51f0f203dc2bf1c6e7e152899249829351c3cf76e750d253a9f152f4` |
| EV/EBITDA | `#49` | 94 | `75edc529c84fabb3356411c04e77f16b281d5574764c7adf497421788ccf334f` |

Two consecutive scoped imports retained the same four IDs, hashes, dates, and
row counts.

| Coverage measure | Result |
|---|---:|
| Supported / partial / unsupported | 9 / 13 / 13 |
| Sources with typed rows | 13 of 35 |
| Total typed rows | 3,163 |
| Complete / partial / missing provenance | 11 / 0 / 0 |
| Active mirror hash mismatches | 0 |

## API and UI Contract

Canonical routes:

```text
GET  /api/valuation/relative/countries
GET  /api/valuation/relative/countries/{country}/industries
GET  /api/valuation/relative/countries/{country}/industries/{industry}
POST /api/valuation/relative/run
```

Root-level `/relative-valuation/*` aliases remain hidden from OpenAPI for
compatibility. The frontend uses canonical routes, selects the first active
country instead of assuming `Global`, reports requested methods that cannot be
calculated, displays source versions, preserves zero values, and leaves currency
units unspecified when the input currency is unknown.

## Operator Command

```bash
docker compose exec backend alembic upgrade head
docker compose exec backend python /workspace/scripts/ingest_damodaran.py --only pe pbv ps vebitda
```

## Validation

- focused pricing/API/coverage/migration/response-contract tests: 22 passed
- complete backend suite: 476 passed, 4 upstream `openpyxl` deprecation warnings
- frontend: 90 passed
- TypeScript: passed
- Next.js 16.2.11 production build: passed
- Python compile: passed
- live migration head: `n0n0n0n0n0n0`
- live scoped import repeated with unchanged versions
- knowledge-base tests: 4 passed
- knowledge-base audit: 61 canonical files, 61 catalog rows, 38 processing rows,
  empty inbox
- `git diff --check`: passed

The first production-build attempt was blocked by the sandbox denying
Turbopack a local worker process/port. The identical build passed with the
required host permission. Browser navigation reached the configured sign-in
page with no console errors; the authenticated panel was not visually exercised
because the browser session did not contain the user's local credentials.

## Remaining Limitations

1. Country statistics are the last current typed importer on destructive replacement.
2. Relative valuation uses industry aggregates, not a reviewed comparable-company set.
3. Company accounting definitions, periods, currencies, and normalization still require review.
4. Industry multiples are benchmark facts; resulting values are calculations under user-selected inputs.
5. One-active-version uniqueness remains enforced by the serial service path, not a partial database constraint.
6. The admin comparison endpoint remains mock.

## Next Recommended Work

Convert `countrystats.xls` to an exact preserved source version and restrict
country-stat reads to the active version. Then add the missing country-context
provenance to relative valuation. Do not broaden pricing providers until that
last replacement path is closed.

Product completion remains **75% local-first** and **64% world-class**. This
phase materially improves valuation correctness and reproducibility but does not
close daily-workflow integration, provider breadth, portfolio attribution, or
broader issuer certification.
