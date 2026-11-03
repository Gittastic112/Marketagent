# Core DCF zero/default correction

Date: 2026-09-14. Scope: the next handoff task after saved-input/reverse verification.

## Findings and change

Core DCF treated zero as missing through Python truthiness defaults. Tax zero
became 21%; zero target margin became current margin; zero rates, growth and
terminal ROIC were replaced by presets. The duplicate sensitivity calculator
and axis centers did the same for these values and funding inputs. Diagnostics
also replaced zero sales-to-capital/terminal rates, hiding the expected warnings.

- Added a local None-only default helper and explicit projection-horizon bounds.
- Applied None-only defaults to forecast/terminal cash flows, share handling,
  sensitivity calculations and centers, including beta, ERP, risk-free rate and
  debt cost. Kept existing absent-input defaults and financial equations.
- Corrected related diagnostics so invalid zero inputs remain visible. Numeric
  fallback results for undefined ratios are still subject to the existing gates;
  this change does not make invalid zero assumptions usable.
- Added regressions for independent expected cash flows, margin fade, discount
  factors, zero-growth terminal reinvestment, invalid input warnings, sensitivity
  agreement/centers, funding calculations, missing defaults, scenario/reverse
  consumers, and persisted forecasts/results with prior versions unchanged.

Only dcf.py, diagnostics_engine.py and the new regression test change runtime/test
code in this task. Earlier unrelated worktree changes remain intact. No contract,
migration, source file import, dependency or frontend changes were needed.

## Verification

The initial regressions reproduced the tax/margin/rate/diagnostic/axis failures.
The first focused suite passed after correction; the final full backend suite
passed with all new regressions included. Exact counts live in
[Current State](../../../00-current-state.md). Backend and scheduler production
images built successfully without replacing normal running containers.
Documentation, secret, workflow-reference and whitespace checks passed. No new
browser or frontend run was needed for the unchanged frontend. An automatic
approval timeout occurred before the full test command ran; the permitted retry
succeeded and produced the observed full-suite result.

## Scope boundaries

The [single limitation ledger](../../../agent_capabilities_and_limitations.md)
owns outstanding adjacent-engine, missing-default and sensitivity-method issues.
Historical stored calculations were not rewritten. New calculations use the fix
only where this source has been deployed. This is deterministic/API evidence,
not a fresh browser, genuine-input or provider certification. Earlier browser
proof belongs to the preceding saved-input/reverse checkpoint.
