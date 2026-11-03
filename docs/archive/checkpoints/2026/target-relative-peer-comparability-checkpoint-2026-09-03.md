# Target-Relative Peer Comparability Checkpoint

**Date:** 2026-09-03

## Delivered in 20 commit-sized steps

1. Added an optional target-company profile to current peer sets.
2. Added immutable target-profile snapshots to peer-set revisions.
3. Added additive migration `m4m4m4m4m4m4` from `l3l3l3l3l3l3`.
4. Required source name, URL, as-of date, and claim type.
5. Normalized whitespace and three-letter currency codes.
6. Bounded market-cap, growth, margin, and source-date inputs.
7. Persisted target JSON and normalized rows together.
8. Made target edits and removals versioned mutations that reset review.
9. Preserved the exact target state in every new revision.
10. Returned target state and storage audit data in detail and history APIs.
11. Added current and revision JSON/relational consistency checks.
12. Blocked review and relative valuation on target storage mismatches.
13. Added target-versus-peer currency and country warnings.
14. Added accounting-standard and fiscal-period warnings.
15. Added a deterministic 10x market-cap mismatch warning.
16. Added 20-point growth and 15-point EBITDA-margin mismatch warnings.
17. Propagated target provenance and warnings into valuation reliability.
18. Added target create/edit/remove, audit, and history controls to the UI.
19. Added backend behavior and frontend integrity tests.
20. Validated migrations, full regressions, production build, runtime, and docs.

## Trust boundary

The application does not infer target-company facts from company metadata,
industry priors, or peer values. A missing target profile is shown as a warning.
Supplied target and peer facts remain user-reviewed evidence, not independently
verified market data. Warnings do not perform currency conversion, accounting
normalization, peer weighting, or calibrated comparability scoring.

The strict peer-member CSV remains member-only. Target profiles are entered or
updated through the peer-set form/API and are retained in immutable history.

## Validation

- Focused peer, Alembic, and readiness tests: 27 passed.
- Full backend suite with workbook data available: 650 passed, with four
  upstream `openpyxl` Python 3.14 deprecation warnings.
- Frontend tests: 128 passed.
- TypeScript: passed.
- Next.js 16.2.11 production Docker build: passed.
- Fresh PostgreSQL full-chain migration: reached `m4m4m4m4m4m4`.
- PostgreSQL `l3` fixture upgrade: preserved the existing peer set and revision,
  seeded empty target JSON, and created no fabricated target-profile rows.

## Files that define the boundary

- `backend/app/models/peer_valuation.py`
- `backend/app/services/peer_valuation_sets.py`
- `backend/app/services/relative_valuation.py`
- `backend/alembic/versions/m4m4m4m4m4m4_add_peer_target_comparability_profiles.py`
- `backend/tests/test_peer_valuation_sets.py`
- `frontend/components/valuation/peer-set-manager.tsx`
- `frontend/lib/api.ts`
- `frontend/lib/frontend-integrity.test.ts`

