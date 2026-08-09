# Macro Sensitivity and Duration Workbook

Primary file: `raw/models/macrodur.xls`

Related data: `raw/datasets/macro.xls`

## Purpose

Estimate how operating income and firm value respond to changes in long-term rates, real GDP, inflation, and currency. The workbook supports a company-specific top-down regression and a bottom-up SIC/business-weighted estimate.

## Workbook map

- `Read me first`: scope, inputs, and explicit small-sample warning.
- `Inputs for top down`: operating income, market capitalization, and debt history.
- `Duration Calculator`: regressions of changes in operating income and firm value against macro changes.
- `Bottom up Estimator`: value- or revenue-weighted business/SIC sensitivity estimates.
- `Annual Data` and `Quarterly Data`: embedded historical macro series.
- `Sector Averages by SIC`: duration, cyclicality, inflation, and currency sensitivity estimates.

## Output interpretation

- Duration: sensitivity to long-term rate changes.
- Cyclicality: sensitivity to real-GDP changes.
- Inflation sensitivity: response to inflation changes.
- Currency sensitivity: response to dollar changes.

The workbook recommends firm-value regressions for duration/cyclicality and operating-income regressions for inflation/currency.

## Limitations

- The source explicitly warns that few observations and one outlier can produce unstable results.
- Sector regressions use quarterly data from `1987-1997`.
- The separate `macro.xls` series ends in `2009`.
- These files are historical methodology references, not current macro inputs.

Use outputs as `Estimate` priors with fit/sample disclosure, never as current facts or automatic DCF assumptions.
