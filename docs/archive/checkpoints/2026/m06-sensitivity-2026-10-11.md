# M06 saved sensitivity checkpoint

October 11, 2026. M06 is in progress; no saved normal models were recalculated.

FCFF sensitivity v2 reuses the canonical forecast, terminal value and equity bridge.
Funding axes add the change in weighted funding cost to both saved WACCs. Beta/ERP
shocks preserve the difference between saved cost of equity and its CAPM component.
Saved terminal ROIC is retained; an absent terminal ROIC resolves against the
unshocked saved terminal WACC. The terminal-WACC axis changes only that rate.
Defaulted input names, saved assumption ID, input hash, currency, version and
bounded cell diagnostics travel in existing JSON. No migration is needed.

Explicit revenue, shares, WACCs and sales-to-capital are required for new grids.
Stale, missing, nonfinite, nonpositive-denominator or nonconvergent cells are null
with a reason. The minimum terminal WACC-growth spread is 0.000001 in decimal
units. Valid zero and negative values remain numbers. Axes no longer clamp
different points to duplicate labels. Bank/distress do not receive FCFF grids.

The panel distinguishes historical unversioned grids, saved calculation dates,
unavailable cells and legitimate zero/negative values. Colors compare with the
saved assumed price; they do not establish investment value. Mobile tables scroll
inside their panels. Reverse DCF, scenarios and quick valuation skip the 150 grid
cells they do not consume; their core calculations remain unchanged.

This phase necessarily crosses engine callers, the renderer, tests and current
docs so calculation and display semantics remain consistent. Thirteen regressions
first exposed wrong funding shocks, invalid numeric cells and duplicate axes.
The older sensitivity-only expectations were updated to the documented v2 method;
core default/zero expectations remain intact.

Validation against this source:

- 57 focused valuation tests, then **1,427 backend tests passed**, three skipped
  PostgreSQL-only cases passed separately against real row/advisory locks.
- **263 frontend tests passed**; production build and TypeScript passed.
- **22 isolated production browser workflows passed** in 3.2 minutes, including
  a saved-model round trip, all six grid centers versus saved output, and a 390px
  sensitivity screenshot with no page overflow. Sources are explicitly Mock Data.
- Backend image manifest: `0a18c7bbcbf2f780a07bc4d7fe256cac1cc2e5008780886a342b15ece1dab786`.
  Frontend: `e9def37f6ca12e9b487dd944fee927741b90b6a2b0117fb3d20ade3c4edc732e`.
- Local logs: `/tmp/mi-architecture-20261010/m06-full.log` and `m06-browser.log`.
  Screenshots: `output/milestones/m06/browser/playwright/test-results/`.

M06-01/02 are evidenced. Broader accounting/method audits, genuine reviewed inputs,
concurrent saved-model proof and end-to-end research/memo traceability remain open.
Normal application images still run M01; source acceptance does not claim rollout.
