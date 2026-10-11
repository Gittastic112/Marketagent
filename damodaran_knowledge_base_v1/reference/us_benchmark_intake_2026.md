# US benchmark intake, September 22, 2026

User approved US-specific, not global, industry priors. Six application mirrors
carry the embedded January 5, 2026 date (`Industry Averages!B1`) and the explicit
`US companies` scope (`F3`). Three reuse byte-identical existing originals; three
are new official downloads. Raw files were not edited. Hashes and routing are in
the source catalog, processing ledger and raw-file hash ledger.

| Runtime mirror | Canonical original | Consuming workflow |
|---|---|---|
| betasUS-2026-01-05.xls | raw/datasets/betas.xls | Regression, unlevered and cash-corrected beta alternatives |
| waccUS-2026-01-05.xls | raw/datasets/waccUS-2026-01-05.xls | ERP, USD rate, borrowing-cost and capital-weight priors |
| marginUS-2026-01-05.xls | raw/datasets/marginUS-2026-01-05.xls | Gross, net, EBITDA and unadjusted operating-margin priors |
| capexUS-2026-01-05.xls | raw/datasets/capexUS-2026-01-05.xls | Net capex/sales and sales/invested-capital priors |
| roeUS-2026-01-05.xls | raw/datasets/roe(1).xls | Unadjusted and R&D-adjusted ROE priors |
| wcdataUS-2026-01-05.xls | raw/datasets/wcdata.xls | Noncash working-capital/sales prior |

## Inspection and reconciliation

All sheets, named ranges, available formulas and comments were inspected.
Beta has 288 formulas, a print-title name, and no cell comments. Its F11
unlevers C11 using D/E and the selected effective/marginal tax convention; H11
removes cash. The WACC sheet has 576 formulas and no names or cell comments.
D20 uses D9 + C20 × D10; G20 adds the volatility-band spread and D11; I20
applies the selected marginal/effective tax convention. Other four industry
tables contain stored values and no formulas, names or cell comments. Their
Variables & FAQ sheets define the populations and metrics.

The importer reads the supplied cached benchmark values. This intake is not an
Excel recalculation certification. Source formulas were inspected, not changed.
Imported industry averages are `Estimate`, not reported company facts.
Dates remain January 5, not the September download/import date.

## Scope and ambiguity boundaries

- India rows and versions remain distinct and active. US selection never copies
  India beta, WACC or inflation-conversion inputs.
- The US WACC conversion block has equal USD/local inflation assumptions. No
  artificial INR rate or INR borrowing-cost record is imported from it.
- US WACC D10 is the workbook's 0.0446 equity premium; D9 is its 0.0395 rate and
  D11 its 0.0023 spread. These are dated model inputs. A current FRED Treasury
  proxy uses a different date and may use a different sovereign-risk convention;
  review that convention and geographic business exposure before accepting CAPM.
- The India workbook labels D10/D11 `Global weighted average`. The application
  now preserves that scope rather than calling the inputs verified country risk.
- Confirm company/segment mappings and leverage. No company industry mapping,
  canonical doctrine, financial review decision or saved valuation was approved
  by this intake. Existing rules already require geography and business-mix review.

Official source pages: [US betas](https://pages.stern.nyu.edu/~adamodar/New_Home_Page/datafile/Betas.html),
[US cost of capital](https://pages.stern.nyu.edu/~adamodar/New_Home_Page/datafile/wacc.html),
[US margins](https://pages.stern.nyu.edu/~adamodar/New_Home_Page/datafile/margin.html),
[US reinvestment](https://pages.stern.nyu.edu/~adamodar/New_Home_Page/datafile/capex.html).
