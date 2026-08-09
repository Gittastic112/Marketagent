# Versioned Country-Statistics Checkpoint

**Date:** 2026-08-08  
**Status:** Shipped and validated  
**Scope:** Exact `countrystats.xls` ingestion, active reads, and provenance

## Outcome

Country statistics no longer delete their prior dataset and typed rows on every
refresh. The importer now hashes the approved source, preserves changed versions,
reactivates known historical hashes, and exposes only the active version through
country-stat and industry-mapping reads.

The old parser also omitted source fields while Data Health called the workbook
supported. The exact contract now retains all 20 meaningful columns from the
22-column layout, including debt including leases, firm value, cash, median
cash/firm value, and signed total dividends.

## Five Delivered Steps

1. Locked SHA-256, source date, exact headers, 127 country rows, nulls, zeros,
   signed dividends, and representative India/US/China values.
2. Added `median_cash_to_firm_value` and `total_dividends_usd_millions` through
   additive migration `p1p1p1p1p1p1`.
3. Replaced destructive ingestion with exact, fail-closed, hash-versioned imports.
4. Restricted API and mapping readers to the active version and exposed fact provenance.
5. Applied the migration, imported twice, validated the live result, and reconciled docs.

## Live Evidence

| Measure | Result |
|---|---:|
| Active version | `#50` |
| Source SHA-256 | `900b6594f808461f9ce5194abf1a50e66f22854bc998473ad8282037d464829b` |
| Source as-of | `2026-01-05` |
| Country rows | 127 |
| Supported / partial / unsupported | 9 / 13 / 13 |
| Sources with typed rows | 14 of 35 |
| Total typed rows | 3,290 |
| Complete / partial / missing provenance | 12 / 0 / 0 |
| Active mirror hash mismatches | 0 |

Two consecutive scoped imports retained version `#50`, the same hash/date, and
127 rows.

The live India row resolves through version `#50` with 4,520 firms, debt
including leases of 698,017.671 US-dollar millions, median current PE of
25.59375, median cash/firm value of 0.01591915836101883, and signed source total
dividends of -46,229.36173 US-dollar millions.

## Operator Command

```bash
docker compose exec backend alembic upgrade head
docker compose exec backend python /workspace/scripts/ingest_damodaran.py --only country_stats
```

## Validation

- 27 focused country-stat, relative-valuation, mapping, coverage, migration,
  and API-contract tests pass.
- Full backend suite: 483 passed with four upstream `openpyxl` deprecation
  warnings.
- Frontend suite: 90 passed.
- TypeScript and the Next.js 16.2.11 production build pass.
- Python compile and live Alembic head `p1p1p1p1p1p1` pass.
- Four knowledge-base tests pass; corpus audit reports 61 canonical files,
  61 catalog rows, 38 ledger rows, and zero pending inbox files.
- `git diff --check` passes.

No rendered frontend component changed in this phase, so browser screenshots
were not rerun. The country-stat API path is covered through service and route
contract tests.

## Remaining Limitations

1. Country aggregates are market context, not company intrinsic-value inputs.
2. The source's signed dividend aggregate is preserved exactly; interpretation
   must respect the workbook's cash-flow sign convention.
3. Only 14 of 35 mirror sources have typed rows.
4. Historical `macro.xls` and `macrodur.xls` use a separate historical contract
   and show provenance as not applicable in Data Health.
5. One-active-version uniqueness remains enforced by the serial service path,
   not a partial database uniqueness constraint.

## Next Recommended Work

Stop spending the next phase on version conversion. The current application
replacement paths are closed. The next useful source work is either a carefully
selected unsupported workbook with an actual consuming workflow, or historical
macro provenance if point-in-time replay is prioritized.

Product completion remains **75% local-first** and **64% world-class**. The main
gaps remain provider breadth, integrated daily research, portfolio attribution,
frontend consistency, and broader real-issuer certification.
