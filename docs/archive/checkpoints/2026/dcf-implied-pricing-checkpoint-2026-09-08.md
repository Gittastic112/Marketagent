# DCF Implied-Pricing Checkpoint

Date: 2026-09-08

Scope: continue the in-progress legacy pricing repair through 20 bounded steps.
These are implementation and verification steps, not 20 Git commits. No commits
were created. Existing unrelated worktree changes were preserved.

## Completed steps

1. Replace WACC-based proxy income with explicit saved net income for P/E.
2. Calculate P/B only from positive saved book equity.
3. Clear unsupported EV/EBITDA, including when depreciation alone is available.
4. Require valid revenue and margin operands for the EBIT denominator.
5. Preserve finite zero/negative DCF numerators and reject missing/non-finite
   denominators, booleans, losses, and overflow as usable ratios.
6. Suppress ratios for stale assumptions and critical/blocking diagnostics.
7. Calculate ratios after distressed adjustments, using final DCF numerators.
8. Add detached historical output reconciliation without database rewrites.
9. Replace structured legacy pricing warnings with explicit review heuristics,
   preserving unrelated warnings and removing proxy-based adjustment advice.
10. Supply saved input context in list, model-detail, result and save responses.
11. Supply each transient scenario's own calculation context.
12. Add typed frontend pricing-basis metadata without changing persistence.
13. Extract the implied-pricing sidebar from the large workspace component.
14. Display formulas, numerators, denominators, and source fields per method.
15. Display assumption identity, output/input timestamps, and saved-input scope.
16. Preserve zero in frontend formatting; avoid any legacy scalar fallback.
17. Show unavailable reasons and guard stale/invalid/untrusted UI states.
18. Validate formulas, historical non-mutation, ownership, new saves, scenarios,
    distressed values, and frontend rendering contracts with regression tests.
19. Build production images, refresh the local app, and verify browser states
    and responsive layouts using an isolated labeled Mock Data fixture.
20. Reconcile current docs, the handoff, feature register, and single limitations
    ledger; identify the next concrete output-card integrity task.

## Files changed in this batch

Backend phase, seven files:

- `backend/app/services/relative_valuation_service.py`
- `backend/app/services/dcf.py`
- `backend/app/services/scenario_engine.py`
- `backend/app/api/schemas.py`
- `backend/app/api/routers/valuations.py`
- `backend/tests/test_implied_pricing_integrity.py`
- `backend/tests/test_valuation_diagnostics.py`

Frontend phase, five files:

- `frontend/lib/api.ts`
- `frontend/lib/implied-pricing.ts`
- `frontend/lib/implied-pricing.test.ts`
- `frontend/components/valuation/implied-pricing-panel.tsx`
- `frontend/components/advanced-workspace.tsx`

Documentation phase updates current-state, architecture, handoff, valuation map,
feature register, limitations ledger, and checkpoint index alongside this record.

## Validation

- Final source-mounted full backend suite: **837 passed**, four upstream
  `openpyxl` deprecation warnings. Includes 27 new pricing regressions.
- Frontend suite: **170 passed**, including seven pricing checks.
- TypeScript: passed, including after the visual correction.
- Backend, scheduler, and frontend production images built successfully.
- The first browser screenshots exposed low-contrast explanatory text. The panel
  was corrected to use the established secondary-text token and explicit panel
  background, then rebuilt and rechecked.
- Isolated browser fixture: authenticated save; P/E 22.3x, P/B 4.5x; unsupported
  EBITDA with reason; expandable formula; 1280px desktop and 390px mobile
  without page-level horizontal overflow.
- A test-only historical output was set to stored P/E 999 and EV/EBITDA 888 with
  zero equity value. The UI showed 0.0x rather than either proxy. PostgreSQL
  reread still returned the stored 999/888, proving the GET did not rewrite them.
- Marking the disposable input stale made all five displayed ratios unavailable.
- Normal backend/frontend/PostgreSQL health and readiness passed. Scheduler is
  running; migration head remains `o6o6o6o6o6o6`. No migration was added.
- Final documentation check passed: 62 active Markdown files, 317 local links.
  `git diff --check` passed.
- The named disposable browser stack was removed and its tmpfs Mock Data
  discarded. The normal database was not populated with test fixtures.

## Boundaries and next task

Limitations remain centralized in `docs/agent_capabilities_and_limitations.md`.
Next: audit the adjacent Multi-Method card's trust gates and the current-price
claim label. This repair does not certify every output in the valuation workspace.
