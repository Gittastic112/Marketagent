# Saved Output and Scenario Integrity

Date: 2026-09-09

Scope: finish verification of the interrupted saved-output batch, then perform
the next 15 bounded scenario tasks. These are implementation/verification steps,
not claims of 15 separate Git commits. No commits or schema migrations were made.

## Resumed saved-output batch

The preceding batch added shared display gates for stale, invalid, critical,
unrecognized-diagnostic, mismatched-identity and unconfigured-currency states.
It applies finite-value formatting to the headline, supplementary total-equity
values and FCFF/FCFE/DDM card. Zero and negative calculations are preserved.
Saved prices are User Assumptions, not live Market Facts. Stored quality scores
are bounded, labeled historical and never synthesized when missing. Model
labels distinguish financial-services and distressed calculations. Saved input
identity/timestamps are disclosed. Corrected forms can reach backend validation
even when their historical values were invalid. Fifteen frontend tests cover
these behaviors; the large workspace now delegates the output cards.

Verification had been interrupted by an automatic permission-review usage-limit
failure on September 8. It resumed on September 9 after a successful read-only
test-stack status check. No bypass or alternate authority was used.

## Next 15 tasks

1. Audit scenario API, engine, UI and existing output contracts.
2. Pass the owned model type into scenario calculations.
3. Preserve zero target margin in bull/bear shocks.
4. Preserve zero WACC in rate shocks.
5. Remove the undisclosed positive-margin floor from margin compression.
6. Reject stale saved inputs on the owner-scoped scenario route.
7. Validate historical input units before generating scenarios.
8. Add model-type, zero-preservation, non-mutation and ownership regressions.
9. Use the saved cash-flow currency instead of hardcoded INR.
10. Use backend-calculated price gaps, removing browser valuation arithmetic.
11. Keep missing/non-finite scenarios unavailable and sorted after finite values.
12. Apply per-scenario trust gates and expose diagnostics, source identity and time.
13. Load scenarios only on demand, with request isolation and failure/empty/retry states.
14. Run regression/build and isolated browser verification, then refresh the local app.
15. Update handoff, current state, architecture, feature register and the one limitations ledger.

## Code files

Saved-output phase: `frontend/lib/valuation-output-state.ts`, its test,
`frontend/components/valuation/saved-output-cards.tsx`, the workspace integration,
and the existing frontend-integrity test.

Scenario backend phase: `backend/app/services/scenario_engine.py`,
`backend/app/api/routers/valuations.py`, and `backend/tests/test_scenario_integrity.py`.

Scenario frontend phase: `frontend/lib/scenario-display.ts`, its test,
`frontend/components/valuation/scenario-range-panel.tsx`, and the workspace
integration. Existing unrelated worktree changes were preserved.

## Validation evidence

- Full backend suite: 845 passed, four upstream openpyxl deprecation warnings.
- Frontend suite: 191 passed. TypeScript passed.
- Backend, frontend and scheduler production images built successfully.
- Isolated Mock Data browser checks: no fabricated empty-state score, explicit
  saved-price labeling, six scenario cards in USD, per-scenario calculation basis,
  1280px desktop and 390px mobile layout, and no mobile page overflow.
- A simulated test-only scenario HTTP failure removed prior results. Retry
  restored the six cards after the interception was removed.
- A stale test assumption suppressed all three saved method values, marked the
  score not current, and caused the direct scenario API to return 422.
- Correcting an invalid saved margin through the form created assumption #2
  with margin 0.2 while assumption #1 retained margin 20. The initial check
  waited for a success message that disappeared during workspace remount; the
  subsequent API read confirmed the save. It also exposed conditional book-equity
  omission on standard-model resaves, now recorded as the next preservation fix.
- Documentation gate: 62 active Markdown files, 319 local links. Diff whitespace
  check passed. No changes were made to the normal database by test fixtures.
- Normal frontend/backend/PostgreSQL health, authentication readiness and schema
  readiness passed at migration `o6o6o6o6o6o6`; scheduler is running. The disposable
  browser containers and tmpfs fixtures were removed after verification.

The test stack uses a separate tmpfs PostgreSQL database and labeled Mock Data.
It does not establish genuine-source investment readiness. Outstanding boundaries
remain in `docs/agent_capabilities_and_limitations.md`; conditional saved-input
preservation is next, followed by Reverse DCF and Real Options.
