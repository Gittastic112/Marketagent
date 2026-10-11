# Saved Relative-Valuation Input Basis: 20-Step Batch

Started: 2026-09-07. Resumed: 2026-09-08.

## Increments

1. Extracted shared benchmark request validation without changing the direct API.
2. Added a read-only backend adapter for one saved DCF assumption set.
3. Preserved explicit zero cash and debt instead of turning them into missing values.
4. Mapped saved book equity and retained zero/loss values without substitution.
5. Derived EBIT only from finite, available revenue and decimal operating margin.
6. Removed the unsupported operating-profit-to-EBITDA substitution.
7. Added field-level claim types, source fields, model/assumption IDs, and timestamps.
8. Added explicit currency, unit-scale, and omitted bridge-adjustment disclosure.
9. Added method-specific positive-base and per-share company-input coverage.
10. Added canonical input-basis hashing and changed-preview rejection.
11. Added the authenticated owned saved-input read endpoint.
12. Added a saved-input calculation endpoint that rejects client financial overrides.
13. Rechecked ownership, stale state, invalid inputs, and basis consent on calculation.
14. Replaced the browser financial adapter with request-isolated saved-input loading.
15. Added input inspection, explicit confirmation, refresh, and unavailable/error states.
16. Returned and displayed the actual input basis consumed by each calculation.
17. Made relative calculation actions non-submitting inside the existing DCF form.
18. Added bounded horizontal table scrolling and non-sticky intermediate-width navigation.
19. Ran backend/frontend/build regressions and isolated browser checks.
20. Updated current docs and the single limitations ledger.

Work was split into backend, frontend, and documentation phases, each below ten
files. No migration, real source workbook, or normal database input was changed.
Existing worktree changes remain uncommitted and preserved.

## Automated validation

- Full source-mounted backend: 810 passed, four upstream openpyxl deprecation warnings.
- Frontend: 163 passed; TypeScript passes.
- Backend, scheduler, and frontend Docker production images built successfully.
- No source migration change; head remains `o6o6o6o6o6o6`.
- Documentation links: 62 active Markdown files, 315 local links; diff whitespace
  check passes.

## Browser and deployment evidence

Used the Playwright CLI skill with Compose project `saved-input-browser-20260908`,
a tmpfs PostgreSQL database, test-only credentials, and explicitly labeled Mock
Data company/model and pricing fixtures. No normal database inputs were used.

- Input read returned cash/debt `0`, book equity `500`, EBIT `200`, and unavailable
  EBITDA despite supplied depreciation. The UI exposed all input source fields.
- Run remained disabled until the current input basis was confirmed.
- Five supported methods calculated; EV/EBITDA remained explicitly unavailable.
  P/B used saved book equity and produced `100` per share; EV/Sales preserved the
  zero bridge and produced `400` per share in the labeled test fixture.
- Results returned the exact reviewed SHA-256 input basis.
- DCF assumption count before/after clicking relative Run was unchanged.
- A guarded mutation of only the test model's saved income caused the open
  preview's next calculation to return HTTP 409 with refresh/review guidance.
  Refresh cleared consent, and renewed confirmation calculated from income `110`.
- Final frontend was rebuilt after correcting input-table wrapping observed in
  the first screenshot. Final 1280px desktop and 390px mobile screenshots were
  inspected; no page overflow or navigation/output overlap. Tables scroll inside
  bounded, keyboard-focusable regions.
- Final screenshots:
  `output/playwright/.playwright-cli/page-2026-09-08T17-50-59-536Z.png` and
  `output/playwright/.playwright-cli/page-2026-09-08T17-51-03-215Z.png`.
- Normal backend/frontend/scheduler images were deployed with existing database
  volumes preserved. Backend/frontend/PostgreSQL health checks pass; scheduler
  is running. Readiness reports `ready`, no missing schema objects, and head
  `o6o6o6o6o6o6`. Frontend local authentication is configured.
- The isolated browser and test stack were removed after verification; their
  disposable tmpfs fixtures were discarded and can be recreated.

## Files changed in this batch

- Backend: `services/relative_valuation.py`, new `services/saved_relative_inputs.py`,
  `api/routers/relative_valuation.py`, new `tests/test_saved_relative_inputs.py`.
- Frontend: `lib/api.ts`, new `lib/saved-relative-inputs.test.ts`,
  `components/advanced-workspace.tsx`, `components/valuation/relative-valuation-panel.tsx`,
  new `components/valuation/saved-relative-valuation.tsx`,
  new `components/valuation/relative-input-basis.tsx`, and `app/globals.css`.
- Current state, handoff, architecture, feature register, valuation application map,
  checkpoint index, and the single limitations ledger.

## Next task

Reconcile the separate legacy DCF implied-pricing service and historical output
display, then add an explicit sourced EBITDA/complete D&A input workflow and
review the full relative equity bridge before expanding output claims. Remaining
limits are maintained only in
[`agent_capabilities_and_limitations.md`](../../../agent_capabilities_and_limitations.md).
