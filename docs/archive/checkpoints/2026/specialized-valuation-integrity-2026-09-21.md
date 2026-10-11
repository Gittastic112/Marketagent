# Specialized Valuation Integrity: September 21, 2026

The user requested the next 30 tasks. The handoff selected financial-services
and distressed-model integrity. These are 30 bounded work items in one focused
batch, not 30 git commits or a claim that every valuation workflow is complete.

## Completed work items

### Excess-return inputs and results

1. Require explicit positive finite book equity instead of a zero fallback.
2. Require finite net income instead of silently substituting zero.
3. Require explicit target ROE, preserving zero and valid negative assumptions.
4. Require explicit cost of equity; never substitute ten percent or WACC.
5. Require explicit bounded terminal growth, preserving zero/negative growth.
6. Require positive finite diluted shares instead of one-share substitution.
7. Validate the direct engine's integer 1-30 year horizon.
8. Preserve zero ROE/income/growth through the complete projection calculation.
9. Block nonconvergent equity perpetuities instead of returning zero terminal value.
10. Diagnose overflow/nonfinite results and discard unusable projections.
11. Treat missing/invalid comparison prices as unavailable, not zero gaps.
12. Keep enterprise value/bridge fields unavailable for the equity-only model.
13. Persist model-specific input/method diagnostics and diagnostic quality scores.

### Financial-services scenarios

14. Shock target ROE instead of unused FCFF operating margins in higher/lower cases.
15. Shock explicit cost of equity instead of unused WACC in the rate case.
16. Add accurately described current-earnings/ROE-compression shocks while
    preserving missing inputs and leaving saved assumptions unchanged.

### Distress calculations

17. Validate explicit failure probability, including valid zero/one endpoints.
18. Validate explicit nonnegative common-equity recovery, preserving zero.
19. Remove fallback share counts from the distress adjustment.
20. Reject missing/nonfinite base equity instead of interpreting it as zero.
21. Reconcile cross-holdings, leases and all existing bridge components.
22. Recalculate the price gap from adjusted equity, including zero recovery.
23. Withhold nonfinite/overflowing adjusted results and invalid price comparisons.
24. Preserve the original base output while applying the detached adjustment.
25. Remove unadjusted supplementary FCFE/DDM values and misleading terminal-value
    concentration from the probability-weighted result; disclose the basis.
26. Withhold FCFF-only sensitivity tables from new distressed calculations rather
    than misrepresent them as recovery-adjusted sensitivity results.

### Contracts, consumers and verification

27. Add probability/ROE bounds, finite specialized fields and nonnegative recovery
    validation to write contracts without changing historical read contracts.
28. Verify atomic invalid writes, saved diagnostics, prior-version preservation
    and historical output reads/storage remaining unchanged.
29. Run focused and full backend tests, frontend tests/TypeScript, production
    backend/scheduler builds and repository static gates.
30. Update current state, source map, feature status, next handoff and the single
    limitation ledger with the verified scope and remaining boundaries.

## Verification

- Focused specialized/lifecycle/scenario/reverse/implied-pricing suite: 121 passed.
- Full source-mounted, network-disabled backend suite: 1,053 passed, four existing
  upstream openpyxl deprecation warnings.
- Specialized regression file: 61 cases; rerun after strengthening historical
  output-read and unchanged-storage assertions.
- Frontend: 209 tests and TypeScript passed; no frontend source changes.
- Backend and scheduler production image builds passed. Images were not deployed.
- Documentation/secret unit checks, active link gate, secret scan, project
  workflow validation and patch whitespace checks passed.

Tests use disposable Mock Data. Docker Desktop was initially stopped and was
started for the isolated runner. No normal data was seeded, no migration was
added, no database volume was removed and no normal application container was
replaced. The substantially dirty preexisting worktree remains preserved.

No new browser or genuine-input certification is claimed. Remaining UI presets,
projection-label/calendar issues, simplified model assumptions and adjusted
sensitivity limits are tracked only in the
[single ledger](../../../agent_capabilities_and_limitations.md).
