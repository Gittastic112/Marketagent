# Normalized Peer Evidence and CSV Checkpoint

**Date:** 2026-09-02

**Migration head:** `l3l3l3l3l3l3`

## Delivered 20-Step Slice

1. Added normalized current peer-member storage.
2. Added normalized immutable revision-member storage.
3. Backfilled both tables from existing JSON snapshots.
4. Preserved member order and parent-scoped identifier uniqueness.
5. Mirrored create writes into normalized rows.
6. Replaced update rows atomically before inserting same identifiers.
7. Persisted normalized members with every revision.
8. Read current and historical members from normalized rows when present.
9. Exposed JSON/relational storage consistency in API responses.
10. Added optional country, currency, fiscal-period, and accounting context.
11. Added optional market-cap, revenue-growth, and EBITDA-margin facts.
12. Normalized and bounded the new inputs.
13. Added currency, accounting, and fiscal-period mismatch warnings.
14. Added deterministic size, growth, and margin dispersion warnings.
15. Added a strict header-only peer CSV template.
16. Added non-writing preview with row errors and SHA-256.
17. Added exact-hash atomic apply that always creates Draft evidence.
18. Added source-preserving, spreadsheet-formula-safe CSV export.
19. Added import, preview, apply, export, consistency, and context UI controls.
20. Completed focused/full regressions, migration tests, production build,
    normal-stack deployment, readiness, and documentation reconciliation.

## Validation Evidence

- Focused peer/Alembic/readiness tests: 22 passed.
- Full backend suite with repository data mounted read-only: 645 passed, with
  four upstream `openpyxl` deprecation warnings.
- Frontend tests: 128 passed.
- TypeScript: passed.
- Next.js 16.2.11 Docker production build: passed.
- Fresh PostgreSQL migration chain: passed to `l3l3l3l3l3l3`.
- k2 fixture upgrade: backfilled two unique current rows and one revision row;
  preserved values, normalized currency, tolerated an invalid legacy date, and
  skipped a duplicate identifier.
- PostgreSQL ORM smoke: create and same-identifier update passed at version 2
  with three normalized members and the expected median.
- Normal runtime: backend, frontend, PostgreSQL, and scheduler are running;
  backend readiness reports the expected head with no missing schema.

## Trust Boundary

The workflow validates shape, provenance fields, storage consistency, and
deterministic thresholds. It does not verify source URLs, acquire licensed peer
facts, normalize accounting statements or currencies, compare against sourced
target-company facts, or manufacture a calibrated comparability score. Imported
facts remain user-supplied and must be reviewed before valuation use.
