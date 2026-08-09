# Data and Provenance Rules

Every valuation input must have:
- metric
- value
- unit
- as-of date
- source
- source type
- whether reported/derived/assumed
- confidence

## Versioning
Do not overwrite historical data. Store new versions by as-of date.

## Benchmark use
Industry datasets are priors and reality checks. They should not mechanically replace company-specific economics.

## Dated datasets
ERP, country premiums, tax rates, betas, default spreads, multiples and expected growth become stale. A current valuation must check dates and prefer newer approved sources while retaining the old values for reproducibility.

## Conflicts
If two sources disagree:
1. retain both
2. identify which is used in the model
3. record the reason if known
4. flag unresolved discrepancies

## Template contamination
Spreadsheet text/formulas may contain stale template references. Treat unexplained cross-company names, stale dates and disconnected formulas as contamination until verified.
