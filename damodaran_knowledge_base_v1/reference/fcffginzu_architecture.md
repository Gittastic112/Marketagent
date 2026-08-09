# FCFFGINZU Architecture Reference

Primary file: `raw/models/fcffginzu(1).xlsx`

## What the workbook is for
Standard non-financial FCFF valuation when operating income is positive or can be normalized positive. It supports 0-15 years of high growth, 2-stage or 3-stage transition, and a stable-growth terminal phase.

## Sheet map

### `Read me first`
Model scope, input guidance and stage-selection instructions.

### `Master Inputs Start here`
Main factual and assumption entry point.
Key groups:
- B4-B9: company/date/options/country
- B12-B26: current financials and non-operating items
- B29-B36: market/private-company capital structure
- B39-B46: risk-free/ERP/rating/cost of debt
- B49-B54: employee options
- B58-B75: high-growth assumptions
- B78-B87: stable-growth assumptions

Important logic:
- Current EBIT must be positive/normalized or use high-growth model.
- Fundamental growth uses ROC × reinvestment rate.
- Stable growth uses sustainable growth/ROC consistency.

### `Valuation Model`
The core DCF engine.

Base-year normalization:
- D2 normalized EBIT
- D3 adjusted EBIT after R&D/lease adjustments
- D5 adjusted capital spending
- D6 adjusted depreciation/amortization
- D11-D12 adjusted debt/equity

High-growth inputs/output:
- D15 expected growth
- D23 ROC
- D24 reinvestment rate
- D31 WACC
- D34 growth rate used
- D35 working-capital/revenue

Forecast rows:
- row 38 growth
- row 40 reinvestment rate
- row 41 EBIT
- row 42 tax rate
- row 43 NOPAT
- row 44 net capex/reinvestment component
- row 45 change in working capital
- row 46 FCFF
- row 47 WACC
- row 48 cumulative discount factor
- row 49 PV of FCFF

Stable phase:
- D51 growth
- D52 reinvestment rate
- D53 FCFF
- D58 WACC
- D59 terminal value

Equity bridge:
- F61 PV high-growth FCFF
- F62 PV terminal value
- F63 operating assets
- F64 cash/non-operating assets
- F66 debt
- F67 minority interests
- F68 equity value
- F69 option value
- F70 common equity
- F71 value/share
- F73 over/undervaluation

### `Input Summary`
Compact high-growth vs stable-growth summary of ROC, reinvestment, growth and WACC.

### `Earnings Normalizer`
Three normalization routes:
1. historical average EBIT
2. historical average pretax ROC × invested capital
3. sector operating margin × revenue

### `R&D converter`
Capitalizes R&D using a 2-10 year economic life. Computes research asset, amortization, EBIT adjustment and tax effect.

### `Operating lease converter`
PV of lease commitments at pretax cost of debt, lease debt adjustment, implied depreciation and EBIT adjustment.

### `Stories to Numbers`
Summarizes high/stable growth, ROC, WACC, reinvestment and separates value of assets in place from value created/destroyed by growth.

### `Option Value`
Dilution-aware Black-Scholes-style value for management options/warrants.

### `Cost of capital worksheet`
Handles:
- bottom-up unlevered beta
- country/region revenue-weighted ERP
- multi-business beta using estimated business-value weights
- market value of straight debt
- convertibles, leases and preferred stock
- WACC

### `Ratings estimator`
Interest coverage -> synthetic rating -> company default spread; adds country default spread and risk-free rate to estimate cost of debt.

### Industry / country sheets
US and Global industry averages, country ERP and trailing-12-month data support benchmarking and cost-of-capital inputs.

## Transition logic
If gradual adjustment is selected, growth, reinvestment and WACC remain at high-growth levels in the first half and converge linearly toward stable levels through the second half.

## Stable-growth diagnostics embedded in workbook
- flag stable growth above risk-free rate
- move stable beta toward 1 (roughly 0.8-1.2)
- question unusually high stable ROC vs WACC
- reject perpetual ROC below WACC without justification
- mature-firm debt ratio may differ from high-growth leverage
- move tax rate toward marginal rate
