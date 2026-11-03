# Reviewed Peer Relative Valuation Checkpoint

**Date:** 2026-08-26

**Status:** implemented and validated

## Delivered 20-task slice

1. Added additive migration `j1j1j1j1j1j1` for peer-set review metadata.
2. Extended peer-set persistence with aggregation, review, reviewer, and source-bearing members.
3. Added strict peer-member, multiple, create, update, and review contracts.
4. Added owner-scoped peer-set list and detail reads.
5. Added owner-scoped peer-set creation.
6. Added atomic updates that invalidate prior review.
7. Added non-destructive archive behavior.
8. Rejected duplicate peers and target-company self-comparison.
9. Rejected future dates, non-positive multiples, incomplete provenance, and Mock Data labels.
10. Added deterministic median aggregation.
11. Added per-method counts, member IDs, exclusions, formulas, and provenance.
12. Added reviewed-peer execution to the relative-valuation engine.
13. Added explicit unavailable states when fewer than three peers support a method.
14. Added authenticated peer-set API routes.
15. Added route-security and response-contract coverage.
16. Added frontend peer-set types and API methods.
17. Added peer-set creation, review, selection, provenance inspection, and archive UI.
18. Added focused backend and frontend integrity tests.
19. Validated the full migration chain, backend, frontend, production build, and normal runtime.
20. Reconciled current docs, the feature register, valuation instructions, handoff, and limitations.

## Calculation and trust boundary

- A peer set must be active, owned by the authenticated user, attached to the
  requested company, and reviewed before it can drive a valuation.
- Each included member retains an identifier, optional company link, multiples,
  source name, source URL, as-of date, claim type, and optional notes.
- Each multiple method needs at least three included positive values.
- The benchmark is the ordinary median. The API exposes the exact eligible
  count, required count, member identifiers, exclusions, formula, and source
  records used for each method.
- Editing a set resets review status and review timestamps.
- Review is an explicit user acknowledgement. The application validates the
  contract but does not independently verify the source or economic comparability.

## Security correction

The frontend Docker build context previously included `.env.local`. The build
was stopped, the protected file was not read, and `frontend/.dockerignore` now
excludes `.env` and every `.env.*` file except `.env.example`. A clean no-cache
production build passed without loading that file.

## Validation evidence

- Focused backend: 23 passed.
- Full backend with repository workbook data mounted read-only: 636 passed, four
  upstream `openpyxl` deprecation warnings.
- Frontend: 128 passed.
- TypeScript: passed.
- Next.js 16.2.11 clean no-cache Docker production build: passed.
- Fresh temporary PostgreSQL full-chain migration: one head at
  `j1j1j1j1j1j1`; readiness reported no missing tables or columns.
- Normal PostgreSQL upgraded additively from `i0i0i0i0i0i0` to
  `j1j1j1j1j1j1`.
- Normal backend, frontend, PostgreSQL, and scheduler services: healthy.

## Remaining limitations

- Peer facts are manually entered and user-reviewed. No licensed provider
  imports, verifies, or refreshes comparable-company multiples.
- The UI does not edit an existing draft or restore an archived set, although
  the backend supports update and retained inactive records.
- Peer-set revisions are not immutable and member rows are structured JSON, not
  normalized historical records.
- Aggregation does not perform winsorization, weighting, currency or accounting
  normalization, fiscal-period alignment, or automated comparability scoring.
- The genuine-input portfolio smoke remains blocked by absent real records in
  the normal database and must not be replaced by the Mock Data fixture.
