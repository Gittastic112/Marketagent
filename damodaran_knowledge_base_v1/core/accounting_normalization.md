# Accounting Normalization

## Operating income normalization
If current EBIT is unusually high/low, normalize using one of:
1. historical average EBIT
2. historical average pretax ROC × current invested capital
3. sector pretax operating margin × current revenue

Use normalization when current operating income is not representative. If EBIT remains meaningfully negative for a young growth company, use the high-growth framework rather than forcing positive normalized EBIT.

## R&D capitalization
Treat R&D as investment when it creates multi-period benefits.

For an amortization life `N`:
- Current R&D is a new capital investment.
- Past R&D is amortized straight-line over `N` years.
- Research asset = sum of unamortized portions of current/prior R&D.
- Current amortization = sum of current-year amortization on prior R&D.
- `Adjusted EBIT = Reported EBIT + Current R&D - R&D Amortization`
- Add the research asset to invested capital/book equity as appropriate.
- Preserve the tax effect of expensing R&D.

The FCFF workbook includes an industry amortization lookup and allows 2-10 years depending on economic life.

## Operating leases
Convert lease commitments to debt:
1. discount future lease commitments at pretax cost of debt
2. PV = lease debt
3. estimate depreciation on lease asset
4. `Adjusted EBIT = Reported EBIT + Lease Expense - Lease Depreciation`
5. add lease debt to total debt

## Working capital
`Non-cash WC = (Current Assets - Cash) - (Current Liabilities - Short-term Interest-bearing Debt)`

Forecast working capital as a percentage of revenue or with a separate operating-driver model.

## Debt and non-operating items
- Include short- and long-term interest-bearing debt.
- Separate debt and equity components of convertibles.
- Add cash and genuine non-operating assets after valuing operating assets.
- Do not use non-operating assets as a catch-all or double count assets already generating forecast cash flow.
- Subtract minority interests when consolidated businesses are not fully owned.

## Options/warrants
Employee options/warrants are an equity claim. Value them explicitly when material rather than relying only on treasury-stock dilution.
