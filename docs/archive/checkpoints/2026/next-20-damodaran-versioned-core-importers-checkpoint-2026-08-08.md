# Damodaran Versioned Core-Importer Checkpoint

**Date:** 2026-08-08  
**Status:** Shipped and validated  
**Scope:** Exact, preserved Margin, Working Capital, Dividend, and FCFE imports

> **Follow-on:** Volatility and the real-options API were subsequently converted
> and validated in
> `next-20-damodaran-versioned-volatility-and-real-options-api-checkpoint-2026-08-08.md`.
> Use that checkpoint for current provenance counts, migration head, limitations,
> and next work.

## Outcome

Six Damodaran typed sources now use one hash-idempotent dataset-version
lifecycle: Capex, ROE, Margin, Working Capital, Dividend, and FCFE. Identical
source bytes reuse and verify existing rows. Changed bytes create a new active
version without deleting history. Known historical hashes can be reactivated.

The four converted parsers fail closed on missing exact headers before creating
dataset metadata, exclude Total Market aggregates, preserve source nulls and
firm counts, and roll back an empty parse. Industry and country lookup paths no
longer leak names from superseded datasets.

The conversion also corrected two semantic errors:

- Margin `ebit_margin` now maps exactly to `Pre-tax Unadjusted Operating Margin`.
- `divfcfeIndia.xls` reports aggregate FCFE before and after debt cash flows. It
  does not report separate Capex minus depreciation, working-capital change, or
  net-debt-issued components. Those legacy fields remain null. Compatibility
  `fcfe` mirrors the source's after-debt value.

## Twenty Delivered Steps

1. Re-read the operating manual and current Damodaran status documents.
2. Inspected the four importer, schema, coverage, and reader boundaries.
3. Verified runtime and canonical workbook hashes match.
4. Inspected exact workbook headers, dates, row counts, nulls, and aggregates.
5. Defined the exact Margin header contract.
6. Defined the exact Working Capital header contract.
7. Defined the exact Dividend header contract.
8. Defined the exact FCFE header contract and removed false component claims.
9. Added firm-count and FCFE aggregate model fields.
10. Added Alembic migration `l8l8l8l8l8l8`.
11. Converted Margin to `DamodaranDatasetVersionService`.
12. Converted Working Capital to `DamodaranDatasetVersionService`.
13. Converted Dividend to `DamodaranDatasetVersionService`.
14. Converted FCFE to `DamodaranDatasetVersionService`.
15. Restricted industry and country readers to active dataset IDs.
16. Added exact-value, contract, rollback, idempotency, coverage, and migration tests.
17. Applied the migration and completed full backend/frontend/build validation.
18. Ran the four live imports twice and proved same-hash idempotency.
19. Reconciled live coverage, provenance, and Data Health inventory state.
20. Updated current-state, handoff, architecture, schema, ingestion, runbook,
    limitations, product-status, product-register, and knowledge-base docs.

## Live Evidence

| Source | Active version | SHA-256 | As-of | Rows |
|---|---:|---|---|---:|
| Capex | `#39` | `0d195d2bc0a284a3c579a4728faf78f15c6bd7c8c3fc748c2dea85e211af0c1b` | `2026-01-05` | 94 |
| ROE | `#40` | `5608b78e268d7100c6d1ce171b8ee31913317158f22305cb6316d445cb4b675d` | `2026-01-05` | 94 |
| Margin | `#41` | `48cb509eb2dc5a64649d20b84b0d15c7e05e1384fd93463afceba49734ef8934` | `2026-01-05` | 94 |
| Working Capital | `#42` | `323c251a42e1fa91442ce386e3e46300b01c4a287fba22a7628cabcd0cb6f30e` | `2026-01-05` | 94 |
| Dividend | `#43` | `456e82546d6665d4ff692968a2fb7f6f1b7f057b4a83617b1eb9957d3c7d1a03` | `2026-01-05` | 94 |
| FCFE | `#44` | `e85d5dc6b8c0b6f573be5bb8088ef0f45ea6ad413c45d86cc194759f51d5618d` | `2026-01-05` | 94 |

Both consecutive runs returned the same versions, hashes, dates, and row counts.

| Coverage measure | Result |
|---|---:|
| Sources with typed rows | 9 of 35 |
| Total typed rows | 2,787 |
| Supported / partial / unsupported | 5 / 17 / 13 |
| Complete active provenance | 6 sources |
| Partial active provenance | 0 sources |
| Missing active provenance | 1 source |
| Active mirror hash mismatches | 0 |

## Operator Command

From the repository root:

```bash
docker compose exec backend alembic upgrade head
docker compose exec backend python /workspace/scripts/ingest_damodaran.py --only margin working_capital dividend fcfe
```

The command reports each active version plus the aggregate coverage and
provenance summary. A second identical run must retain the same version IDs and
row counts.

## Validation

- focused backend: 32 passed
- complete backend: 452 passed, 4 upstream `openpyxl` deprecation warnings
- frontend: 90 passed
- TypeScript: passed
- Next.js 16.2.11 production build: passed
- Python compile: passed
- Alembic current/head: `l8l8l8l8l8l8`
- knowledge-base tests: 4 passed
- knowledge-base audit: 61 canonical files, 61 catalog rows, 38 processing rows,
  empty inbox

Browser screenshots were not rerun because this batch did not change frontend
code. The frontend suite, TypeScript, and production build still passed.

## Remaining Limitations

1. Volatility is the one active typed source with missing version provenance.
2. `industry_volatility_benchmarks` lacks a dataset-version foreign key, so its
   conversion requires a migration and reader update rather than only a service swap.
3. Pricing sources and country statistics still use legacy replacement behavior.
4. Not every approved source-specific parser is version-safe, so point-in-time
   replay is still partial.
5. Database uniqueness for one active version is enforced by the serial service
   path, not a partial unique index.
6. The generic admin comparison endpoint remains mock.
7. Industry benchmark rows are priors, not company facts.

## Next Recommended Work

1. Convert volatility with a dataset-version foreign key, exact headers,
   active-reader filtering, and changed-hash preservation tests.
2. Convert the shared pricing table carefully because PE, PBV, PS, and EV/EBITDA
   files populate different columns and must not overwrite one another's history.
3. Convert country statistics with exact source metadata and active reads.
4. Add `fundgrEBIndia.xls` only after the remaining correctness conversions; it
   is the next useful analytical source for sustainable EBIT-growth priors.

Product completion remains **75% local-first** and **64% world-class**. This
checkpoint improves benchmark reproducibility and truthfulness, not provider
automation, daily workflow integration, portfolio attribution, or broad issuer
certification.
