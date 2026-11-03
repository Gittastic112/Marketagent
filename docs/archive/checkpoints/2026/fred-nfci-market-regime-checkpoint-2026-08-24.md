# FRED NFCI Market Regime Checkpoint

**Date:** 2026-08-24

## Scope

This checkpoint records thirty dependency-ordered, commit-sized increments that
make one Market Regime module operational from persisted provider evidence. The
work does not claim automated options, liquidity, volume, or breadth coverage.
It does not fetch data during regime calculation and does not produce trading
instructions.

## Delivered Increments

1. Added focused FRED ingestion coverage.
2. Added a typed ingestion result.
3. Normalized and validated series identifiers.
4. Made metadata refresh deterministic.
5. Counted fetched, created, duplicate, missing, and rejected observations.
6. Kept failed attempts outside successful observation persistence.
7. Preserved provider name and official FRED series URL.
8. Required authentication for import.
9. Added stable missing-configuration errors.
10. Started a FRED Processing Run for configured attempts.
11. Completed successful runs with exact counts.
12. Stored sanitized failed-run evidence.
13. Returned the Processing Run ID.
14. Connected emitted runs to Provider Health.
15. Covered success, duplicate, invalid, missing-config, and provider-failure paths.
16. Added macro and regime provenance columns.
17. Added migration `f7f7f7f7f7f7`.
18. Exposed macro provenance in API and frontend contracts.
19. Defined the bounded NFCI normalization contract.
20. Added a read-only preview from persisted observations.
21. Blocked missing, unverified, non-finite, and future-only evidence.
22. Added provider-backed macro input application.
23. Linked the input to the exact macro observation.
24. Made repeated application idempotent.
25. Added preview/apply response envelopes and explicit data states.
26. Corrected current-score and declared-provider metadata semantics.
27. Added frontend types and a stateful server action.
28. Added an evidence-first FRED macro panel and macro-series provenance UI.
29. Extended backend, frontend-integrity, migration, readiness, and security tests.
30. Reconciled active documentation and the handoff.

## Calculation Contract

NFCI is stored as a provider observation. The application creates a separate
Calculation:

```text
macro regime score = clamp(-NFCI × 50, -100, 100)
```

Positive NFCI indicates tighter-than-average financial conditions, so it maps
to a negative regime contribution. NFCI `+2` maps to `-100`; NFCI `-2` maps to
`+100`. The transformation is an application methodology, not a FRED fact.

## Validation

- Full backend gate: 604 passed with four upstream `openpyxl` warnings.
- Focused backend gate: 30 passed.
- Frontend tests: 124 passed.
- TypeScript: passed.
- Alembic: one head, `f7f7f7f7f7f7`.
- Documentation checker: required after this checkpoint update.

## Runtime Boundary

The normal database was not migrated or seeded during source validation. The
running stack was last verified at prior migration `ee6ee6ee6ee6`. Rebuild the
backend and run `alembic upgrade head` before runtime verification. A genuine
FRED import additionally requires the user's configured FRED credential and an
explicit import action.

## Remaining Work

The real-input portfolio smoke and authenticated twenty-route matrix remain
open. Options, liquidity, volume, and breadth remain manual until a compliant,
source-preserving provider adapter is implemented.
