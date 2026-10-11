# Peer-Set Lifecycle and Comparability Checkpoint

**Completed:** 2026-09-02

**Migration head:** `k2k2k2k2k2k2`

## Delivered 20-task slice

1. Added peer-set versions and immutable revision persistence.
2. Added owner-scoped revision models and relationships.
3. Recorded create as version 1.
4. Added optimistic version checks to every mutation.
5. Recorded updates and review invalidation.
6. Recorded explicit reviews.
7. Recorded archives.
8. Added restore-as-draft with a new revision.
9. Added owner-scoped revision history reads.
10. Exposed actions and changed-field summaries.
11. Added source-age and date-span diagnostics.
12. Added per-method dispersion diagnostics.
13. Added claim-type and sparse-coverage warnings.
14. Propagated warnings into relative-valuation results and reliability.
15. Fixed missing-country response metadata.
16. Added frontend version, history, and diagnostic contracts.
17. Added draft and reviewed-set editing.
18. Added archived-set restore and history UI.
19. Added backend and frontend regression coverage.
20. Validated the migration chain, legacy backfill, suites, production images,
    normal runtime, and current documentation.

## Trust behavior

- A stale write returns conflict and tells the caller to reload.
- Restore never silently reactivates a reviewed calculation input. It returns
  the set to Draft and clears review metadata.
- Revision rows are append-only snapshots with a unique peer-set/version key.
- Existing peer sets receive a version-1 `migration_snapshot` revision.
- Stale dates, date misalignment, Source Summary evidence, incomplete method
  coverage, and wide dispersion are visible warnings. They do not silently drop
  a peer or prove comparability.
- User-reviewed peer evidence is capped at medium reliability and falls to low
  when relevant warnings exist.

## Validation

- Full backend: 640 passed, four upstream `openpyxl` warnings.
- Focused lifecycle/migration/readiness: 17 passed.
- Frontend: 128 passed.
- TypeScript: passed.
- Next.js 16.2.11 production image: passed.
- Fresh PostgreSQL full-chain migration: `k2k2k2k2k2k2`.
- Legacy row at `j1` upgraded with a preserved version-1 migration snapshot.
- Normal backend, frontend, PostgreSQL, and scheduler are running; readiness is
  `ready` with no missing tables or columns.

## Still not solved

- The app does not independently verify user-entered peer facts.
- Peer members are JSON snapshots rather than normalized queryable rows.
- No licensed provider imports or refreshes company multiples.
- No automatic currency, accounting-standard, fiscal-period, size, growth, or
  margin normalization exists yet.
