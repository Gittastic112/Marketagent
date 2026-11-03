# Peer Diagnostic Acknowledgement Receipts Checkpoint

**Date:** 2026-09-05

## Twenty tracked steps

1. Identify that peer review recorded an actor and time but not the warnings reviewed.
2. Define a canonical deterministic peer-diagnostic snapshot.
3. Add a SHA-256 acknowledgement hash to every diagnostic response.
4. Add a sorted unique warning-code inventory to every diagnostic response.
5. Bind the hash to the diagnostic date, thresholds, evidence, calculations, and warnings.
6. Require review requests to carry the displayed diagnostic hash.
7. Require review requests to carry the complete displayed warning-code set.
8. Reject malformed diagnostic hashes at request validation.
9. Reject hashes that no longer match current diagnostics.
10. Reject missing, partial, duplicate, or extra warning acknowledgements.
11. Store the accepted hash, warning codes, and diagnostic date on the peer set.
12. Copy the accepted receipt into the immutable review revision.
13. Expose receipt state on current-set and revision responses.
14. Report whether a stored receipt matches current diagnostics.
15. Clear the receipt when edits or restoration invalidate review state.
16. Block relative valuation when a reviewed set has no current receipt.
17. Permit explicit re-acknowledgement of a legacy or stale reviewed set.
18. Require a visible UI checkbox when current diagnostics contain warnings.
19. Display current, stale, and missing receipt states plus history, and filter the calculation selector.
20. Validate tests, types, production images, migration chain, live schema, and services.

These are implementation and verification steps, not 20 Git commits. The shared
worktree remains substantially uncommitted.

## Evidence

- Six receipt-specific tests cover deterministic hashes, stale hashes, exact
  warning acknowledgement, versioned invalidation, corrupt receipt detection,
  and legacy re-acknowledgement.
- The focused peer, CSV, Alembic, and readiness gate passed 67 tests.
- The full backend production-image suite passed 690 tests with four upstream
  `openpyxl` deprecation warnings.
- All 136 frontend tests and TypeScript passed.
- Backend, frontend, and scheduler production images built successfully.
- A fresh temporary PostgreSQL database upgraded through the complete migration
  chain to the single `o6o6o6o6o6o6` head and was then removed.
- The normal PostgreSQL database is at `o6o6o6o6o6o6`; readiness reports no
  missing tables, columns, or constraints.
- Backend and frontend health checks pass, and the scheduler reports a clean
  deterministic startup.

The consolidated product limitation record remains
[`../../../agent_capabilities_and_limitations.md`](../../../agent_capabilities_and_limitations.md).
