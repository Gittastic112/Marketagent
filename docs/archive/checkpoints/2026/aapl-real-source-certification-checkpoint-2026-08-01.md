# AAPL Real-Source Certification Checkpoint

**Date:** 2026-08-01  
**Status:** AAPL FY2022-FY2025 promoted, reconciled, and certified with the APSEZ India reference

## Scope And Authorization

This checkpoint covers the US representative real-source financial history.
The user explicitly reviewed and approved the six AAPL core financial facts for
FY2022-FY2025 on 2026-08-01. That authorization did not include FY2021.

The promotion command enforced these boundaries before writing:

- exactly four fiscal years: FY2022, FY2023, FY2024, and FY2025
- exactly six core metrics per year: revenue, EBIT, net income, cash, debt, and
  diluted shares
- exact SEC XBRL locator-to-payload validation for all 24 facts
- no unrelated reviewed candidate in the promotion set
- FY2021 remained untouched

## Official Source

The primary source is the SEC Company Facts payload:

```text
https://data.sec.gov/api/xbrl/companyfacts/CIK0000320193.json
```

Stored payload SHA-256:

```text
2d1974cf68b105aa4ae1a9da58bc95488993216dde40f8470bcf17eef4c8a472
```

The local AAPL record is company ID `1`, CIK `0000320193`, market `US`.
Processing run `3` staged 39 candidates, idempotency run `4` skipped the same
39, and guarded promotion run `5` promoted exactly 24 approved facts.

## Promoted Facts

These values are now **Facts** backed by reviewed SEC XBRL evidence:

| FY | Report end | Revenue USD bn | EBIT USD bn | Net income USD bn | Cash USD bn | Debt USD bn | Diluted shares bn |
|---:|---|---:|---:|---:|---:|---:|---:|
| 2022 | 2022-09-24 | 394.328 | 119.437 | 99.803 | 23.646 | 110.087 | 16.326 |
| 2023 | 2023-09-30 | 383.285 | 114.301 | 96.995 | 29.965 | 105.103 | 15.813 |
| 2024 | 2024-09-28 | 391.035 | 123.216 | 93.736 | 29.943 | 96.662 | 15.408 |
| 2025 | 2025-09-27 | 416.161 | 133.050 | 112.010 | 35.934 | 90.678 | 15.005 |

Promotion retained the evidence candidates with `promoted` status; it did not
delete the audit trail.

## Reconciliation Result

```text
promoted_candidate_count: 24
annual_period_count: 4
normalized_period_count: 4
normalization_status: complete
normalization_coverage: 100%
trust_ready_period_count: 4
reconciliation_status: complete
exact_metric_count: 24
mismatch_count: 0
missing_normalized_count: 0
normalized_only_count: 0
```

The AAPL candidate result is eligible with no failures. After APSEZ FY2023-FY2025
promotion and reconciliation, the portable two-market manifest passes:

```text
status: passed
certified_count: 2
certified_markets: [IN, US]
required_markets: [IN, US]
```

## FY2021 Boundary

FY2021 was not promoted. Its seven candidates remain `needs_review`, and the
conservative extractor still lacks a defensible aggregate debt fact for that
year. Do not add FY2021 to the certified window without a separate explicit
review and exact debt-component reconciliation.

## Remaining Limitations

- The history uses the latest filed comparative observation for each period; it
  is not yet a bitemporal as-filed series.
- The source is official structured SEC evidence, not a rendered 10-K statement
  presentation.
- This is representative proof for one structured US issuer and one India PDF
  issuer, not broad parser or accounting-policy certification.

The India reference and remaining limitations are in
`docs/roadmaps/adani-ports-real-source-checkpoint-2026-08-01.md`. The checked-in
portable manifest is `data/certification/aapl-apsez-reference-manifest.json`.
