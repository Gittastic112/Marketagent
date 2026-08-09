# Damodaran Dataset Version and ROE Checkpoint

**Date:** 2026-08-08  
**Status:** Shipped and validated  
**Scope:** Reproducible dataset provenance plus exact `roeIndia.xls` ingestion

> **Follow-on:** This checkpoint records the original Capex/ROE milestone.
> Margin, Working Capital, Dividend, and FCFE were subsequently converted and
> validated in
> `next-20-damodaran-versioned-core-importers-checkpoint-2026-08-08.md`. Use that
> file for current provenance counts, migration head, limitations, and next work.

## Outcome

The application can now prove which Capex and ROE source bytes produced the
active benchmark rows. Re-importing identical bytes verifies and reuses the
stored version. Importing changed bytes preserves prior typed rows and activates
a new version. Reintroducing a known historical hash reactivates the preserved
version instead of creating a duplicate.

The approved ROE workbook is now a real application source. It contributes 94
industry rows with firm count, unadjusted ROE, and R&D-adjusted ROE. Source `NA`
values remain null, Total Market aggregates are excluded, and the importer does
not manufacture ROC or ROIC.

## Fifteen Delivered Steps

1. Verified migration, model, consumer, importer, and coverage boundaries.
2. Matched runtime and canonical ROE files by SHA-256.
3. Confirmed the embedded `2026-01-05` source date and exact workbook columns.
4. Defined same-hash, changed-hash, historical-reactivation, and active-read rules.
5. Added dataset provenance and lifecycle model fields.
6. Added ROE firm-count and R&D-adjusted fields.
7. Created Alembic migration `k7k7k7k7k7k7`.
8. Added the reusable `DamodaranDatasetVersionService`.
9. Converted Capex to the preserved-version service.
10. Implemented exact typed ROE ingestion with fail-closed column validation.
11. Restricted assumption and industry-mapping reads to active dataset IDs.
12. Added focused lifecycle, source-value, null, API, coverage, and migration tests.
13. Exposed active provenance and mirror-hash status in Data Health and admin history.
14. Added scoped `--only` operator ingestion and applied the live migration/import.
15. Reconciled current-state, architecture, schema, ingestion, runbook, handoff,
    knowledge-processing, coverage, and product-register documentation.

## Live Evidence

| Measure | Result |
|---|---:|
| Active ROE version | `#40` |
| ROE source SHA-256 | `5608b78e268d7100c6d1ce171b8ee31913317158f22305cb6316d445cb4b675d` |
| ROE source as-of | `2026-01-05` |
| ROE typed rows | 94 |
| Active Capex version | `#39` |
| Capex typed rows | 94 |
| Sources with typed rows | 9 of 35 |
| Total typed rows | 2,787 |
| Supported / partial / unsupported | 5 / 17 / 13 |
| Complete active provenance | 2 sources |
| Missing active legacy provenance | 5 sources |
| Active mirror hash mismatches | 0 |

The ROE importer was run repeatedly after migration. Every run returned 94 rows
and retained active version `#40`, proving live same-hash idempotence.

## Operator Command

From the repository root:

```bash
docker compose exec backend alembic upgrade head
docker compose exec backend python /workspace/scripts/ingest_damodaran.py --only roe
```

Use `--only capex roe` to refresh both version-safe contracts. Do not run the
unscoped command merely to update one source: other source-specific importers
still use legacy replacement behavior.

## Architecture and Trust Rules

- `damodaran_dataset_files` owns source-level provenance and version state.
- Typed benchmark rows retain their `dataset_file_id` and are never relabeled to
  a newer source.
- Consumers select active dataset IDs; superseded rows remain auditable.
- A generic admin parse creates an inactive `metadata_only` record only.
- Active or typed versions cannot be deleted through the admin rollback route.
- Data Health compares an active stored hash with the current runtime mirror.
- Unknown legacy provenance remains missing. It is not backfilled from today's
  mirror because those may not be the bytes originally imported.

## Validation

- focused backend: 19 passed
- complete backend: 439 passed, 4 upstream `openpyxl` deprecation warnings
- frontend: 90 passed
- TypeScript: passed
- Next.js 16.2.11 production build: passed
- Alembic current/head: `k7k7k7k7k7k7`
- knowledge-base tests: 4 passed
- knowledge-base audit: 61 raw files, 61 catalog rows, 38 processing rows,
  empty inbox
- `git diff --check`: passed

The first host build attempt was blocked by the sandbox denying Turbopack's
internal local port. The identical build passed outside that restriction.

## Remaining Limitations

1. Only Capex and ROE use the preserved-version lifecycle.
2. Five active legacy dataset records have no provable source hash/date contract.
3. The database does not enforce one active version with a partial unique index;
   the local operator path is serial and the service deactivates prior versions.
4. ROE is an accounting return and must not be substituted for terminal ROIC.
5. The generic comparison endpoint remains mock and is not evidence of a real
   source-version diff workflow.
6. Browser screenshot automation was not rerun; frontend tests, TypeScript, and
   the production build cover this batch.

## Next Recommended Work

Convert the remaining live typed dataset importers to the same version service,
one source at a time, starting with margin, working capital, dividend, and FCFE.
Each conversion needs an exact source contract, changed-hash history test,
active-reader audit, live scoped import, and provenance-complete Data Health row.
After that correctness work, implement `fundgrEBIndia.xls` as the next analytical
breadth addition because it supports sustainable EBIT growth without inventing
company forecasts.

Product completion remains **75% local-first** and **64% world-class**. This
milestone improves reproducibility and analytical breadth, but does not close
provider automation, broad financial certification, integrated daily workflow,
portfolio attribution, or frontend consistency gaps.
