# Target-Profile CSV Portability Checkpoint

**Date:** 2026-09-03

## Delivered in 20 commit-sized steps

1. Versioned the published peer CSV contract as format v2.
2. Added twelve explicit target-company columns.
3. Kept set metadata and peer columns stable.
4. Published the target-column list in the template response.
5. Declared legacy member-only compatibility in template metadata.
6. Detected v1 and v2 headers without accepting arbitrary schemas.
7. Required one identical target profile across every v2 peer row.
8. Rejected partial or inconsistent repeated target data.
9. Reused the direct target-profile validation contract.
10. Preserved source name, URL, date, and claim type.
11. Preserved country, currency, fiscal period, and accounting standard.
12. Preserved market cap, revenue growth, EBITDA margin, and notes.
13. Returned parsed target evidence in non-writing previews.
14. Kept exact SHA-256 preview-to-apply enforcement.
15. Applied valid target evidence into Draft peer sets.
16. Preserved normalized current and immutable revision target rows.
17. Repeated target evidence safely in exported peer rows.
18. Escaped formula-leading target text on export and restored it on import.
19. Added target presence, format version, and legacy state to the UI/API types.
20. Added round-trip, inconsistency, Mock Data, legacy, regression, build, and
    documentation proof.

## Trust boundary

CSV v2 transports user-supplied evidence. It does not verify market facts or
make a peer economically comparable. Apply always creates a Draft and still
requires explicit review before valuation use. Legacy v1 files remain usable,
but their missing target context is shown as a limitation.

## Validation

- Focused peer, Alembic, and readiness tests: 30 passed.
- Full backend suite: 653 passed with four upstream `openpyxl` Python 3.14
  deprecation warnings.
- Frontend tests: 128 passed.
- TypeScript: passed.
- Next.js 16.2.11 production Docker build: passed.
- Migration head remains `m4m4m4m4m4m4`; this increment requires no schema
  change.

## Primary implementation files

- `backend/app/services/peer_valuation_import.py`
- `backend/tests/test_peer_valuation_sets.py`
- `frontend/lib/api.ts`
- `frontend/components/valuation/peer-set-manager.tsx`
- `frontend/lib/frontend-integrity.test.ts`

