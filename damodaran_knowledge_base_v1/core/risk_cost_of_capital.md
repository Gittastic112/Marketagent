# Risk and Cost of Capital

## Risk-free rate
Use a risk-free rate in the same currency as the forecast cash flows. A local government bond yield may need a sovereign default adjustment before it is treated as risk-free.

Currency is a measurement choice. If cash flows and discount rates are consistently estimated in different currencies, intrinsic value should reconcile after conversion.

## Equity risk premium
Separate:
- mature-market ERP
- country risk premium
- company operating exposure to countries

For a government bond with non-zero default risk, estimate a currency risk-free
rate by subtracting the sovereign default spread from the government yield. The
January 2026 country-risk source then estimates country risk premium by scaling
the default spread for relative equity-versus-bond volatility and adds that
premium to mature-market ERP. These are dated market inputs; store the exact
source version and do not reuse the January 2026 values as timeless constants.

Company country risk follows where the company operates, sells and produces, not incorporation alone.

Exposure weighting guidance:
- consumer/service: revenue exposure often works
- natural resources: production exposure often works
- manufacturing: mix of revenue and production may be better

For a multinational, use exposure-weighted ERP/CRP.

## Bottom-up beta
Prefer bottom-up business betas when possible.

`Levered Beta = Unlevered Beta × [1 + (1 - tax rate) × D/E]`

For a pure operating-business beta, correct unlevered beta for excess cash where appropriate because cash has near-zero beta.

For multi-business firms, estimate business values and value-weight unlevered betas. The FCFF cost-of-capital worksheet uses `Revenue × EV/Sales` as an estimated business-value weight.

## Cost of debt
If a market cost of debt is unavailable, synthetic rating logic can be used:
- interest coverage ratio -> synthetic rating -> company default spread
- add country default spread where applicable
- `Pretax Cost of Debt = Riskfree Rate + Company Default Spread + Country Default Spread`

The rating-to-spread table is dated market data even when the coverage-to-rating
method is reusable. Do not use a spread table with an unknown as-of date for a
current valuation.

Market value of straight debt can be estimated by discounting the current interest expense as a coupon and book debt as principal at current cost of debt over an estimated maturity.

## Uncertainty vs risk
Do not use WACC as a garbage bin for every uncertainty.
- systematic risk belongs in discount rates
- company-specific uncertainty belongs primarily in operating assumptions/scenarios/distributions
- discrete failure risk can be modeled explicitly
- optionality can be modeled separately where economically real

Use distributions/correlations when uncertainty is material.

## Empirical priors

Cross-sectional debt, payout, dividend, and macro-sensitivity regressions are
estimates, not optimal targets. Preserve the model date, variable units,
coefficients, fit statistics, and sample scope. Low or insignificant explanatory
power must be visible and should reduce or eliminate the prior's weight.
