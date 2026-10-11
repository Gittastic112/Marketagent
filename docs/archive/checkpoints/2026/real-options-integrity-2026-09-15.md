# Real Options integrity

Implemented and verified September 15, 2026. Documentation closed September 16.
Historical evidence only; current next work lives in the handoff.

## Scope and changes

- Replaced the panel's arbitrary custom-base request with an owned, timestamp-
  checked saved-FCFF endpoint. Routes authorize; the new saved_real_options service
  validates and integrates; pure contracts live in schemas/real_options.py.
- Validates currency, shares, saved equity/per-share consistency, saved diagnostics,
  numeric ranges, all seven eligibility confirmations and incremental-equity scope.
- Adds option value to total common equity, then divides by saved shares. Explicit
  zero exclusivity and already-counted value add nothing. No database writes.
- Response carries saved identity/times, currency, shares, separate totals and
  per-share values, warnings, calculation time and a request/basis fingerprint.
- RealOptionsPanel uses the domain API, blank explicit numerical inputs, shared
  trust checks and request invalidation. No scored suitability or override gate.
- Independent analysis forms sit outside the DCF save form. Shared responsive
  placement supports Real Options and Reverse DCF; the DCF form stays mounted but
  hidden while these panels are active, preserving unsaved edits.
- Main source changes: backend schemas/real_options.py, services/saved_real_options.py,
  services/real_options_service.py, api/routers/real_options.py; frontend
  lib/api/real-options.ts, lib/real-options-state.ts, real-options-panel.tsx,
  advanced-workspace.tsx and globals.css. Contract/boundary regressions accompany them.
- No dependencies, migrations, normal-data rewrites or normal deployment.

## Verification

- Backend: 949 passed, including 33 new regressions; four upstream openpyxl
  datetime deprecation warnings. Maintained network-disabled source-mounted suite.
- Frontend: 209 passed and TypeScript passed. New fixture assertion/type errors
  were corrected and the complete checks rerun successfully.
- Backend, scheduler and frontend production image builds passed. Final layout
  changes received a fresh frontend build and isolated runtime refresh.
- Browser backend source digest matched workspace:
  `9a533eabbd6226befaae60f7195fc34c4e373261ceb417d992ab1763f56b8458`.
- Disposable PostgreSQL migrated to o6o6o6o6o6o6; readiness passed.

## Isolated browser evidence

Fixture: Mock Data Options Integrity, saved INR FCFF, 10 shares. Normal database
and credentials were not used. Only frontend port 13110 was exposed on loopback.

- S=100, K=100, life=1, rate=.05, volatility=.2, yield=0, exclusivity=1 returned
  total option 10.450583572185565 INR and 1.0450583572185566 INR per share.
  Base equity 2225.779581805597 became 2236.2301653777827; combined per share
  223.62301653777826. No dollar symbol or total/per-share mixing.
- Zero exclusivity returned zero adjusted option; already-counted option left
  base equity unchanged and displayed the double-counting warning.
- Eligibility removal cleared results and disabled calculation. An input change
  invalidated a held response. Transport failure cleared results, displayed an
  error and recovered on successful retry.
- No nested forms; all calculations left the assumption-version count at one.
- Final built UI passed 1280px desktop and 390px mobile page-width checks.
  Screenshots were inspected and retained under output/playwright as
  real-options-desktop-20260915.png and real-options-mobile-20260915.png.
- Switching to standalone analyses hid the DCF save action. An unsaved horizon
  of seven survived tab switches while the saved horizon remained five.
- Browser session closed; disposable project real-options-integrity-20260915
  removed, including its temporary Mock Data database. No normal containers or
  user records were replaced. This is Mock Data proof, not genuine-input proof.

Remaining method, compatibility and persistence boundaries are recorded only in
the [single limitation ledger](../../../agent_capabilities_and_limitations.md).
