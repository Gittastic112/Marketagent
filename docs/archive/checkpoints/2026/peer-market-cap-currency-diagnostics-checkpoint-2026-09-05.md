# Peer Market-Cap Currency Diagnostics Checkpoint

**Date:** 2026-09-05

## Twenty tracked steps

1. Reproduce the false raw ratio across USD and EUR peer market caps.
2. Define size comparability as matching stated currency rather than raw amount.
3. Separate included peer market caps into currency groups.
4. Preserve member identifiers for every group.
5. Calculate minimum, maximum, and max-to-min ratio inside each group.
6. Stop emitting one combined ratio when multiple currencies are present.
7. Preserve the existing ratio contract for one complete currency group.
8. Emit wide-size warnings separately for each eligible currency group.
9. Attach the applicable currency to each wide-size warning.
10. Exclude market caps that have no stated currency.
11. Identify every member excluded because currency is missing.
12. Exclude non-positive, non-finite, or unparsable legacy market-cap values.
13. Identify every member excluded because its value is invalid.
14. Compare target market cap only with peers using the target currency.
15. Count peers skipped for currency mismatch.
16. Count peers skipped for missing currency or invalid values.
17. Keep same-currency target-size mismatch warnings intact.
18. Expose peer and target comparison coverage in the frontend contract.
19. Display grouped and skipped coverage in the peer-set manager.
20. Run focused, full, frontend, build, deployment, documentation, and runtime gates.

These are implementation and verification steps, not 20 Git commits. The shared
worktree remains substantially uncommitted.

## Evidence

- The new tests reproduced nine failures before implementation.
- 33 focused currency-diagnostic and peer-lifecycle tests passed afterward.
- The final peer, CSV, Alembic, and readiness gate passed 61 tests.
- The full backend suite passed 684 tests with four upstream `openpyxl` warnings.
- All 136 frontend tests and TypeScript passed.
- Backend, frontend, and scheduler production images built successfully.
- Backend and frontend healthchecks pass, PostgreSQL is healthy, the scheduler
  reports a deterministic startup, and readiness remains green at
  `n5n5n5n5n5n5` with no missing tables, columns, or constraints.

The consolidated product limitation record remains
[`../../../agent_capabilities_and_limitations.md`](../../../agent_capabilities_and_limitations.md).
