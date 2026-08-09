# Unsupported Regression Seed

Status: `resolved`

Decision date: `2026-08-07`

## Original finding

The prior seed script deleted all regression coefficient rows and inserted
unsupported values and predictors described as typical January 2025 Damodaran
coefficients. They did not match the two canonical January 2025 source PDFs.

## Resolution

- Added a frozen catalog of the six exact source models and 26 coefficients.
- Preserved model month, geography, output units, adjusted R-squared, source
  path, confidence, and usability.
- Replaced the global delete with a scoped, idempotent synchronization that
  preserves unrelated models.
- Aligned debt, dividend-yield, and payout request variables and units with the
  PDFs; removed frontend proxy and mock inputs.
- Disabled both payout priors because the source fit is not suitable for an
  automated prior.
- Added coefficient-drift rejection, strict API validation, `Estimate` labels,
  provenance, fit, and visible warnings.

## Verification

- 7 focused regression tests pass.
- The complete backend suite passes: 419 tests.
- The first local database synchronization created 20 coefficients, updated 6,
  and removed 12 obsolete source-model rows.
- The second synchronization changed nothing and reported all 26 coefficients
  unchanged.

## Continuing limitation

These are dated empirical priors with low explanatory power, not optimal capital
structure or payout targets. They must be compared with company economics and
current industry evidence.
