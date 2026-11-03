# Peer CSV Idempotent Apply Checkpoint

**Date:** 2026-09-04

## Twenty tracked steps

1. Reproduce duplicate Draft creation from an exact CSV retry.
2. Define receipt identity as owner, target company, and exact UTF-8 content hash.
3. Add nullable `import_sha256` storage to peer-set parents.
4. Add the owner/company/hash unique database constraint.
5. Preserve null receipts for manual sets.
6. Preserve null receipts for rows created before the migration.
7. Check for an existing scoped receipt before parsing or writing again.
8. Return the existing set for an exact retry.
9. Mark first-time API results as `created`.
10. Mark exact-retry API results as `reused`.
11. Keep archived matches archived when reused.
12. Keep later edits and the current version intact when reused.
13. Catch a concurrent unique collision and return the winning row.
14. Re-raise unrelated integrity failures instead of hiding them.
15. Verify the same hash remains independent across owners.
16. Verify the same hash remains independent across target companies.
17. Verify legacy member-only CSV receives the same retry protection.
18. Tell the user whether the UI created or reused a set.
19. Make post-save refresh failure explicitly safe to retry.
20. Validate migration, rollback, regressions, production images, deployment, and limitations.

These are implementation and verification steps, not 20 Git commits. The shared
worktree contains substantial earlier changes and remains uncommitted.

## Evidence

- 677 backend tests passed with four upstream `openpyxl` deprecation warnings.
- 54 focused peer CSV, peer lifecycle, Alembic, and readiness tests passed.
- All 136 frontend tests and TypeScript passed.
- Backend and Next.js 16.2.11 production images built successfully.
- A disposable PostgreSQL database upgraded through the full chain to m4, kept
  two populated legacy peer sets through the n5 upgrade with null receipts,
  rejected a duplicate non-null receipt, and downgraded to m4 without row loss.
- The normal backend, frontend, PostgreSQL, and scheduler services are running at
  `n5n5n5n5n5n5`; readiness reports no missing tables, columns, or constraints.

## Remaining limitations

- The migration cannot safely backfill receipts for pre-n5 imports because the
  original uploaded bytes are not stored. The first exact retry of an old import
  can therefore create one additional tracked Draft.
- Identity is exact UTF-8 request content. Changed line endings, whitespace, BOM,
  or other byte-level content produces a different hash and is a new import.
- Reusing an archived or later-edited set returns its current state. It does not
  restore the original imported snapshot or reactivate the set.
- Idempotency prevents duplicate writes. It does not verify peer facts, refresh
  market evidence, normalize currencies/accounting, or improve comparability.

## Changed files

- `backend/alembic/versions/n5n5n5n5n5n5_add_peer_csv_import_receipts.py`
- `backend/app/models/peer_valuation.py`
- `backend/app/services/peer_valuation_import.py`
- `backend/app/services/peer_valuation_sets.py`
- `backend/app/services/runtime_readiness.py`
- `backend/app/api/schemas.py`
- `backend/tests/test_peer_csv_idempotency.py`
- `backend/tests/test_alembic.py`
- `backend/tests/test_runtime_readiness.py`
- `frontend/lib/api.ts`
- `frontend/components/valuation/peer-set-manager.tsx`
- `frontend/components/runtime-readiness-panel.tsx`
- `frontend/lib/frontend-integrity.test.ts`
