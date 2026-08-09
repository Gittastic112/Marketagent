# Synthetic Ratings Workbook

Primary file: `raw/models/ratings.xls`

## Purpose

Estimate a synthetic bond rating and company default spread from interest coverage, then add the risk-free rate to estimate pretax cost of debt. The workbook has separate lookup bands for large non-financial firms, smaller/riskier firms, and financial firms.

## Main inputs

- firm type
- current EBIT
- current interest expense
- current long-term government bond rate
- whether operating lease commitments exist
- current lease expense and future lease commitments when applicable

## Main logic

```text
Interest coverage = adjusted EBIT / adjusted interest expense
Synthetic rating = lookup(interest coverage, firm-type table)
Company default spread = lookup(interest coverage, firm-type table)
Pretax cost of debt = government bond rate + company default spread
```

When leases are enabled, the workbook capitalizes lease commitments and adjusts EBIT/interest coverage iteratively.

## Workbook map

- `Start here Ratings sheet`: inputs, outputs, three rating/spread lookup tables.
- `Operating Leases`: lease commitments, present value, imputed interest, adjusted operating income, and coverage.

## Date and approval state

The workbook contains no reliable embedded as-of date for its default-spread
table. File modification time is not a source date.

On `2026-08-07`, the user approved treating the table as recent for the current
personal, local workflow. The source date remains unknown and date confidence
remains low. The recency decision must be labeled `User Assumption`; it is not a
reported source fact. See
`review_queue/resolved/2026-08-07-undated-synthetic-rating-spreads.md`.

## Application implementation

The application stores the workbook's 45 rating rows as an immutable typed
catalog in `backend/app/services/synthetic_rating_catalog.py`. Catalog version
`ratings-xls-45d1f61c67f0` is tied to canonical workbook SHA-256
`45d1f61c67f02fb595661e95ef294e72524a105c9db85ee198a918386d580d3c`.

The WACC service supports all three source tables:

- `large_non_financial`
- `small_or_risky`
- `financial_service`

Lookup uses each source row's lower bound as the effective threshold, matching
workbook behavior at exact breakpoints. API output preserves the combined
Moody's/S&P label, decimal default spread, selected bounds, firm type, catalog
version, source path/hash, unknown source date, low date confidence, and the
approved `User Assumption` recency basis. The old `is_large_mfg` boolean remains
a compatibility input for large versus small non-financial firms; conflicting
old and new inputs fail validation.

The workbook's iterative operating-lease conversion is not implemented in this
service. Callers must supply an interest-coverage ratio that already includes
any required lease capitalization. That normalization is the next ratings-model
extension, not part of the source-table lookup.
