# 2025 Regression Priors

Canonical sources:

- `raw/articles/debt regression.pdf`
- `raw/articles/global regression debt.pdf`

The second filename is misleading. Its content is **Dividend Regressions: January 2025**, not a debt regression. Preserve the original filename for provenance and use this reference for retrieval.

## Unit convention

The source equations return percentages. Effective tax rate is entered in percentage points, while expected EPS growth and institutional ownership are decimals in the worked global debt example. Convert the final percentage to a decimal only after evaluating the equation. Never infer a missing unit silently.

## Debt-ratio regressions

### United States

```text
Predicted debt ratio (%) =
  1.666
  - 0.176 * Effective tax rate (%)
  - 26.978 * Expected EPS growth (decimal)
  + 18.519 * Institutional ownership (decimal)
  + 0.065 * Company age (years)
```

Adjusted R-squared: `0.190`.

### Global

```text
Predicted debt ratio (%) =
  17.419
  - 0.057 * Effective tax rate (%)
  - 20.401 * Expected EPS growth (decimal)
  - 2.153 * Institutional ownership (decimal)
  + 0.033 * Company age (years)
```

Adjusted R-squared: `0.065`. The source floors negative predictions at zero. The worked example produces `14.12%`.

## Dividend regressions

### United States dividend yield

```text
Predicted dividend yield (%) =
  2.396
  - 0.017 * Effective tax rate (%)
  - 1.838 * Expected EPS growth (decimal)
  + 0.008 * Company age (years)
  - 1.124 * Beta
```

Adjusted R-squared: `0.346`.

### Global dividend yield

```text
Predicted dividend yield (%) =
  1.835
  + 0.035 * Effective tax rate (%)
  - 3.603 * Expected EPS growth (decimal)
  + 0.004 * Company age (years)
  - 0.279 * Beta
```

Adjusted R-squared: `0.146`. The source floors negative predictions at zero. The worked example produces `1.98%`.

### Payout regressions

The PDF also reports:

```text
US payout = 0.990 - 0.478 * Beta - 0.115 * ROE
Global payout = 0.733 - 0.182 * Beta + 0.253 * ROE
```

The US payout model has adjusted R-squared `0.025`. The global model has adjusted R-squared `0.000`, overall significance `0.244`, and individually insignificant beta/ROE coefficients. Do not use the global payout regression as an automated prior.

## Required use

1. Label every output `Estimate` and `dated empirical prior`.
2. Store the January 2025 model version and exact equation.
3. Show fit quality and a low-confidence warning.
4. Compare against current company economics and industry evidence.
5. Never treat predicted debt ratio or payout as an optimal target.
6. Reject unsupported coefficient sets, silent unit changes, and models whose variables differ from the source.

## Application alignment

Resolved on `2026-08-07`. The canonical application catalog is
`backend/app/services/regression_model_catalog.py`; scoped synchronization is in
`backend/app/services/regression_seed_service.py`. The API rejects coefficient
sets that differ from this source specification, exposes January 2025 provenance
and adjusted R-squared, labels outputs `Estimate`, and does not return automated
priors from either statistically unusable payout model. The audit trail is in
`review_queue/resolved/2026-08-07-unsupported-regression-seed.md`.
