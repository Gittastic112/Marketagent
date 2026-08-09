# Canonical Valuation Framework

## Core chain
**Story -> Revenue -> Operating Margin -> Reinvestment -> FCFF -> Risk -> Enterprise Value -> Equity Value -> Value per Share**

The default operating-business framework is FCFF, anchored to `fcffginzu(1).xlsx`.

## 1. Classify the company
- Corporate life cycle: start-up, young growth, high growth, mature growth, mature, decline/distress.
- Financial vs non-financial.
- Single business vs materially different segments.
- Public vs private.
- Positive/normalizable EBIT vs structurally negative EBIT.

## 2. Build and normalize the base year
Capture current and prior-year revenue, EBIT, interest, capex, depreciation, non-cash working capital, debt, book equity, cash, non-operating assets, minority interest, shares and market price.

Possible adjustments:
- normalize unusual EBIT
- capitalize R&D
- capitalize operating leases
- split convertible debt
- incorporate NOLs
- separate cash/cross-holdings/non-operating assets
- value employee options/warrants

## 3. Translate story to numbers
For each business/segment, determine:
- size of the market
- sustainable share / target revenue
- target operating margin from unit economics, competition and scale
- reinvestment intensity / sales-to-capital or reinvestment rate
- speed of convergence

Do not extrapolate history mechanically when the business is changing. Use historical numbers as evidence for the endpoint story.

## 4. Forecast high growth and transition
High-growth inputs may remain fixed or gradually transition to stable-growth inputs. In the FCFF workbook, transition can occur during the second half of high growth.

Fundamental growth when margins are stable:
`Expected growth in operating income = ROC × Reinvestment Rate`

If margins/efficiency are changing, decompose growth rather than blindly applying the sustainable-growth equation.

## 5. FCFF
`FCFF = EBIT(1-tax rate) - (Capital Expenditures - Depreciation) - Change in Non-cash Working Capital`

Equivalent economic implementation can use total reinvestment directly.

## 6. Discount rate
`Cost of Equity = Riskfree Rate + Beta × Equity Risk Premium`

`After-tax Cost of Debt = Pretax Cost of Debt × (1 - marginal tax rate)`

`WACC = E/(D+E) × Cost of Equity + D/(D+E) × After-tax Cost of Debt`

Include preferred stock when material.

## 7. Stable growth
- Perpetual growth should be sustainable for the economy/currency. Risk-free rate is a useful upper anchor.
- Beta should move toward mature-firm levels, generally around 1 and normally within 0.8-1.2 absent a strong reason.
- Tax rate should normally move toward marginal tax rate.
- Mature firms often carry more debt than young firms; use target/industry economics rather than blindly freezing current leverage.
- Default long-run ROC is convergence toward WACC as excess returns fade, with explicit exceptions for durable competitive advantages.

If stable reinvestment is based on fundamentals:
`Stable Reinvestment Rate = Stable Growth / Stable ROC`

`Terminal FCFF_(n+1) = NOPAT_(n+1) × (1 - g/ROC)`

`Terminal Value_n = FCFF_(n+1) / (WACC_stable - g)`

## 8. Equity bridge
`Operating Asset Value + Cash + Non-operating Assets - Debt - Minority Interests - Option Value = Common Equity Value`

Divide by diluted/common share count consistently.

## 9. Output
Always show:
- intrinsic enterprise and equity value
- per-share value
- market price and price/value gap
- value of assets in place vs value created/destroyed by growth
- key assumptions
- sensitivities / uncertainty
- current pricing/comps separately
