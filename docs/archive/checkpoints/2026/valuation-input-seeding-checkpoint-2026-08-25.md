# Valuation Input Seeding Checkpoint

**Date:** 2026-08-25

## Delivered

- Added migration `i0i0i0i0i0i0` to link assumption methods to versioned
  Damodaran dataset files and store the missing growth and financing-flow fields.
- Added source-specific importers for `betaIndia.xls`, `waccIndia.xls`,
  `taxrateIndia.xls`, `countrytaxrates.xls`, `histgrIndia.xls`, and
  `finflowsIndia.xls`.
- Removed hardcoded India ERP and risk-free-rate method fallbacks. An unseeded
  methodology table now returns only custom user input.
- Made autofill industry- and currency-aware for risk-free rate, ERP, beta, cost
  of debt, capital weights, WACC, and tax. Every benchmark method retains exact
  dataset, SHA-256, date, path, sheet, row, and column provenance and requires
  review.
- Added every supported DCF input to the review draft, including projection
  length, currencies, cross-holdings, leases, payout/FCFE fields, narratives,
  and special-case inputs.
- Added a field-level input-readiness contract and visible readiness summary.
- Kept industry aggregate financing flows as context only. They are never copied
  into company cash-flow assumptions.

## Live Data Applied

The normal PostgreSQL database was upgraded to `i0i0i0i0i0i0` and seeded with
18 active typed sources and 2,625 rows. The active assumption-method population
is 1,276 rows:

- beta methods: 280
- WACC/rate/capital-structure methods: 654
- industry tax methods: 94
- country tax methods: 248

All 18 active source records report complete provenance and no hash mismatch.
For the Transportation benchmark, live verification returned INR risk-free rate
6.4854%, ERP 7.08%, beta 1.1293, local pre-tax cost of debt 9.5394%, debt weight
17.5525%, equity weight 82.4475%, local WACC 13.4002%, 2Y revenue growth 11.9167%,
and 5Y revenue growth 5.2386%.

## Validation

- Backend full suite: 627 passed; four upstream `openpyxl` deprecation warnings.
- Focused importer/methodology/autofill/coverage suite: 38 passed.
- Frontend tests: all 127 passed; focused valuation subset: 20 passed.
- TypeScript: passed with incremental output disabled.
- Next.js 16.2.11 production build: passed and deployed to the running frontend
  container; auth readiness and container health passed after restart.
- Alembic: one head and normal runtime at `i0i0i0i0i0i0`.
- Runtime readiness: database and schema both ready at `i0i0i0i0i0i0`, with no
  missing tables or columns.

## Limitations

- The supplied accessible files are benchmark workbooks, not company financial
  source files. The normal database has no reviewed company financial histories
  or confirmed valuation industry mappings. Starting financials, bridge values,
  shares, market price, payout facts, and special-case inputs therefore remain
  missing or review-required.
- Revenue-weighted multi-industry beta and WACC blending is not implemented.
- Missing source cells remain missing. No synthetic replacement is generated.
- All benchmark inputs are estimates, not company facts, and require explicit
  user review before valuation promotion.
