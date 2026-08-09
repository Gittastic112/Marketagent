# Damodaran-Style Valuation Agent: Lecture Notes Absorption and Build Requirements

**Source batch:** Spring 2025 / January 2025 Damodaran valuation lecture packets uploaded by user  
**Output purpose:** Translate the uploaded lecture notes into the design principles, formulas, workflows, guardrails, and build implications needed for a serious valuation agent inside the Market Intelligence Agent project.  
**Status:** This is not yet the final engineering spec. It is the distilled learning layer that should guide the next full build-spec MD.

---

## 0. Executive Summary

The uploaded lecture notes make one thing clear: a Damodaran-style valuation agent should not be a simple DCF calculator. It should be a structured valuation system that forces the user to connect story, cash flows, growth, reinvestment, risk, terminal assumptions, and market pricing.

The core lesson is:

> Value is driven by expected cash flows, growth, risk, reinvestment, and competitive advantage. Price is driven by market mood, comparables, liquidity, and demand-supply forces. A serious valuation tool must keep these separate, then reconcile them.

The tool should therefore have 3 major engines:

1. **Intrinsic valuation engine**
   - FCFF DCF
   - FCFE DCF
   - Dividend discount model
   - Stable growth, two-stage, and multi-stage models
   - Story-to-numbers workflow
   - Terminal value discipline
   - Loose-end adjustments

2. **Relative valuation / pricing engine**
   - PE, PEG, PBV, EV/EBITDA, EV/Sales, EV/Invested Capital, sector metrics
   - Comparable company selection
   - Multiple definition consistency
   - Statistical control for growth, risk, margins, returns, payout, and reinvestment
   - Pricing versus value distinction

3. **Contingent claim / real options engine**
   - Option to delay
   - Option to expand
   - Option to abandon
   - Natural resource reserves
   - Patents and R&D-heavy companies
   - Distressed equity as a call option on firm assets
   - Explicit double-counting checks

The AI layer should not do the math loosely. The deterministic backend should compute valuation. The AI layer should:

- Help translate narrative into assumptions.
- Explain assumptions.
- Flag inconsistent assumptions.
- Identify which model should be used.
- Challenge bad inputs.
- Generate valuation memos.
- Track how new information affects the valuation story.

The main build principle:

> Build deterministic valuation math first. Add AI as a guide, critic, interpreter, and memo writer. Do not let the LLM freehand the valuation numbers.

---

## 1. Source Map: What Each Uploaded Document Adds

### 1.1 `ValIntroSpr25.pdf`

This is the philosophical foundation.

Key learnings:

- Valuation is biased. The right goal is not fake objectivity. The tool should expose assumptions and bias direction.
- No valuation is precise. The tool should output ranges, sensitivities, and uncertainty diagnostics, not a single false-precision number.
- Simpler models are usually better than complex models that the user cannot understand.
- There are only 3 broad valuation approaches:
  - Intrinsic valuation
  - Relative valuation / pricing
  - Contingent claim / real option valuation
- Different approaches can produce different estimates at the same point in time.
- Knowing when to use each approach is part of valuation skill.

Build implication:

The app should begin every valuation by asking or inferring:

```text
Are we valuing, pricing, or valuing optionality?
```

The tool should not hide this distinction.

---

### 1.2 `valpacket1spr25.pdf`

This is the core intrinsic valuation packet.

Major topics absorbed:

- Intrinsic value as risk-adjusted present value of expected cash flows.
- Equity valuation versus firm valuation.
- Discounting consistency: FCFE with cost of equity, FCFF with WACC.
- Risk-free rate selection by currency and maturity.
- Country default spreads and country risk premiums.
- Implied versus historical equity risk premiums.
- Bottom-up beta.
- Synthetic credit ratings and cost of debt.
- WACC with market value weights.
- Operating leases, R&D, and accounting adjustments.
- Reinvestment, working capital, taxes, and FCFF construction.
- Growth from fundamentals: reinvestment rate multiplied by return on capital.
- Stable growth and terminal value rules.
- Loose-end adjustments: cash, cross holdings, debt, pensions, employee options, SBC, minority interests.
- Narrative-to-numbers methodology.
- Lifecycle-based valuation: young growth, mature, declining, distressed, emerging market, financial services, commodity/cyclical, user/platform businesses.
- Value versus price.

Build implication:

This packet should be the primary foundation for the first serious version of the valuation engine.

---

### 1.3 `valpacket2spr25.pdf`

This is the relative valuation / pricing packet.

Major topics absorbed:

- Relative valuation is pricing, not intrinsic value.
- Most market valuation work is built around multiples.
- Multiples must be defined, described, analyzed, and applied.
- The numerator and denominator must refer to the same claimholder group.
  - Equity value goes with equity earnings or equity book value.
  - Enterprise value goes with firm-level earnings, revenue, invested capital, or EBITDA.
- Multiples are driven by the same fundamentals as DCFs: growth, risk, cash flows, payout, margins, reinvestment, and returns on capital/equity.
- Comparable firms should be comparable on fundamentals, not just sector label.
- Statistical approaches can control for multiple differences across firms.
- PE, PEG, PBV, EV/EBITDA, EV/Sales, and asset-based valuation each have specific drivers and failure modes.
- Sum-of-the-parts valuation can use intrinsic or relative approaches by division.
- Private company valuation needs adjustments for total risk, owner dependence, illiquidity, and transaction type.

Build implication:

Relative valuation should be a full module, not a simple comp table. It should explain why a company deserves a premium or discount.

---

### 1.4 `valpacket3spr25.pdf`

This covers real options, acquisition valuation, value enhancement, and EVA-style thinking.

Major topics absorbed:

- Traditional DCF can understate value when real options exist.
- Real options only matter economically when there is exclusivity or meaningful competitive restriction.
- Option value should not be added blindly. It is often noisy and easy to double count.
- Real option types:
  - Delay
  - Flexibility
  - Expansion
  - Abandonment
  - Financing flexibility
  - Patents
  - Natural resource reserves
  - Distressed equity
- Acquisition valuation must separate control, synergy, debt subsidies, risk transference, biased comparables, and deal momentum.
- Synergy must be valued before deciding what to pay, not used afterward to justify a premium.
- Value enhancement comes from four levers:
  - Increase cash flows from existing assets.
  - Increase growth from new investments where returns exceed cost of capital.
  - Reduce cost of capital where appropriate.
  - Extend or strengthen competitive advantage period.
- EVA is another way to express the same DCF logic: value comes from excess returns on invested capital.

Build implication:

Real options and M&A should be advanced modules, not phase 1. They require serious guardrails because they are easy to misuse.

---

## 2. Core Philosophical Rules the Valuation Agent Must Encode

### 2.1 Valuation is not objective

The notes explicitly reject the idea that valuation is a search for one precise true number. Every valuation is biased. The practical question is:

```text
How much bias, and in which direction?
```

Product requirement:

- Every valuation should store an **assumption audit trail**.
- The system should label assumptions as:
  - User-provided
  - Market-derived
  - Company-reported
  - Industry-derived
  - Agent-suggested
  - Default fallback
- The valuation report should show:
  - Which assumptions drive most of the value
  - Whether assumptions are aggressive, neutral, or conservative
  - Whether assumptions are internally consistent

Possible UI element:

```text
Bias & Confidence Panel
- Revenue growth: aggressive versus history and peers
- Target margin: neutral versus peer range
- Reinvestment: optimistic given growth path
- Terminal growth: acceptable / warning
- Cost of capital: market-consistent / stale / unsupported
```

---

### 2.2 Precision is false comfort

A good valuation does not mean a precise valuation. The payoff to valuation is often greatest when valuation is least precise because uncertainty creates opportunity.

Product requirement:

The system should always output:

- Point estimate
- Valuation range
- Sensitivity table
- Scenario table
- Key value drivers
- Margin of safety view
- Uncertainty explanation

Avoid outputs like:

```text
Fair value = $124.37
```

Prefer:

```text
Base case value per share: $124
Reasonable range: $95 to $155
Current price: $102
Implied upside to base: 22%
Main swing factors: target operating margin, sales-to-capital ratio, terminal ROC
```

---

### 2.3 Simplicity beats fake sophistication

The notes repeatedly warn that more inputs do not necessarily make valuation better. A model with too many inputs can become a device for hiding bias.

Product requirement:

The tool needs 2 layers:

1. **Quick valuation mode**
   - Minimal assumptions
   - Transparent defaults
   - Fast output

2. **Advanced valuation mode**
   - Full controls
   - Explicit formulas
   - Segment logic
   - Country risk
   - Accounting adjustments
   - Scenario and sensitivity analysis

But advanced mode should not mean random complexity. Every advanced input must map to value through a clear formula.

---

### 2.4 Value and price are different

Intrinsic valuation estimates value from cash flows and risk. Relative valuation estimates price by looking at what others pay for similar assets.

Product requirement:

The system should separate:

```text
Intrinsic value output
Market pricing output
Market-implied expectations output
```

Recommended UI layout:

```text
Valuation Dashboard
1. Intrinsic Value
2. Relative Pricing
3. Market-Implied Assumptions
4. Difference Between Value and Price
5. What Has To Be True
```

---

## 3. The 3 Master Approaches the Agent Must Support

## 3.1 Intrinsic Valuation

### Definition

Intrinsic valuation links value to:

```text
Expected cash flows
Growth in those cash flows
Risk in those cash flows
Life of the asset or business
```

The general formula:

```text
Value = Sum over t of E(CF_t) / (1 + r)^t
```

For businesses with infinite lives:

```text
Value = PV of explicit forecast cash flows + PV of terminal value
```

### Build requirements

The intrinsic valuation engine should support:

- FCFF valuation
- FCFE valuation
- Dividend discount model
- Stable growth model
- Two-stage model
- Three-stage model
- Declining company model
- Distressed company expected value model
- Financial services equity model
- Commodity/cyclical normalized model
- User/platform company model
- Private company model later

### Core cash flow types

| Model | Cash flow | Discount rate | Value output |
|---|---|---|---|
| Dividend discount model | Dividends | Cost of equity | Equity value |
| FCFE model | Free cash flow to equity | Cost of equity | Equity value |
| FCFF model | Free cash flow to firm | WACC | Firm value |

### Non-negotiable consistency rule

The agent must never mix cash flow and discount rate types.

```text
If cash flow is after debt payments, discount at cost of equity.
If cash flow is before debt payments, discount at cost of capital.
```

Backend validation:

```pseudo
if valuation_model == "FCFE" and discount_rate_type != "cost_of_equity":
    raise ValuationConsistencyError

if valuation_model == "FCFF" and discount_rate_type != "wacc":
    raise ValuationConsistencyError
```

---

## 3.2 Relative Valuation / Pricing

### Definition

Relative valuation prices an asset by comparing it to how similar assets are priced by the market.

It requires:

1. Comparable assets
2. A standardized price multiple
3. Controls for differences in fundamentals

### Build requirements

The relative valuation engine should support:

- PE
- Forward PE
- PEG
- Price-to-book
- EV/EBITDA
- EV/EBIT
- EV/Sales
- EV/Invested Capital
- Sector-specific operating metrics
- Sum-of-parts relative valuation
- Regression-based controlled multiple valuation

### Damodaran four-step multiple framework

Every multiple should go through:

```text
Define the multiple
Describe the multiple
Analyze the multiple
Apply the multiple
```

Product requirement:

When the user sees a multiple, they should also see:

- Numerator definition
- Denominator definition
- Whether numerator and denominator are claimholder-consistent
- Peer median
- Peer quartiles
- Outliers
- Fundamental drivers
- Premium/discount explanation

---

## 3.3 Contingent Claim / Real Option Valuation

### Definition

A real option exists when a business has the right, but not the obligation, to take an action in the future.

Examples:

- Delay a project
- Expand into a new market
- Abandon a project
- Develop a patent
- Extract natural resources
- Treat distressed equity as a call option on firm assets

### Build requirements

Real options should be advanced only. The agent should first test whether a real option exists and whether it has economic value.

Real option tests:

```text
1. Is there an underlying asset?
2. Is there a clear contingency?
3. Is there exclusivity or a barrier to competition?
4. Can the value of the underlying asset be estimated?
5. Can volatility be estimated?
6. Is the exercise price known?
7. Is there a finite life?
8. Is there a risk of double counting with the DCF?
```

Output should include:

```text
Real option value
DCF value excluding option
Total value with option
Double-counting warning
Confidence level
```

---

## 4. Core Architecture for the Valuation Agent

The valuation agent should be divided into deterministic services plus AI services.

```text
valuation-agent/
  data/
    financials_normalizer
    market_data_adapter
    macro_data_adapter
    peer_data_adapter
    filings_adapter
  engines/
    intrinsic_engine
    relative_pricing_engine
    real_options_engine
    reverse_dcf_engine
    scenario_engine
    sensitivity_engine
    diagnostics_engine
  adjustments/
    leases
    r_and_d
    sbc
    options
    pensions
    cross_holdings
    minority_interests
    cash_and_non_operating_assets
    synthetic_ratings
  ai/
    model_selector_agent
    narrative_to_numbers_agent
    assumption_auditor_agent
    valuation_memo_agent
    market_intelligence_impact_agent
  api/
    valuation_routes
    assumptions_routes
    peer_routes
    report_routes
  ui/
    quick_valuation
    advanced_assumptions
    valuation_output
    diagnostics_panel
    scenario_panel
    relative_pricing_panel
    narrative_panel
```

### Deterministic math layer

This layer calculates:

- Cash flows
- Discount rates
- Betas
- WACC
- Growth
- Terminal value
- Relative multiples
- Option values
- Scenarios
- Sensitivities

### AI layer

This layer should:

- Select the right model.
- Translate story into assumptions.
- Explain what changed after new filings/news.
- Challenge implausible assumptions.
- Generate a valuation memo.
- Ask for missing inputs.

It should not be the source of truth for valuation math.

---

## 5. User Modes

## 5.1 Quick Valuation Mode

Purpose:

Get a fast first-pass valuation without overwhelming the user.

Inputs:

```text
Ticker or company name
Currency
Country
Industry
Revenue growth assumption or auto-generated default
Target operating margin or auto-generated default
Reinvestment intensity or sales-to-capital ratio
Risk level or auto-generated cost of capital
Terminal growth
```

The agent should auto-fill:

- Current revenue
- Current operating income
- Tax rate
- Net capex
- Working capital change
- Cash
- Debt
- Shares outstanding
- Current price
- Peer group
- Industry beta
- Mature ERP
- Country risk premium

Output:

```text
Base case value per share
Current price
Upside/downside
Implied market expectations
Main assumptions
Sensitivity table
Diagnostics warnings
Quick memo
```

Quick mode must show assumptions, not hide them.

---

## 5.2 Advanced Valuation Mode

Purpose:

Allow a full Damodaran-style valuation.

Advanced modules:

1. Company and business model setup
2. Historical financial normalization
3. Accounting adjustments
4. Revenue forecast
5. Margin forecast
6. Reinvestment forecast
7. Tax forecast
8. Cost of capital
9. Terminal value
10. Loose-end adjustments
11. Scenarios
12. Sensitivities
13. Relative pricing
14. Reverse DCF
15. Narrative-to-numbers
16. Final memo

Advanced mode should be expandable section by section.

---

## 5.3 Teaching Mode

Purpose:

Explain valuation concepts while the user works.

Examples:

```text
Why is sales-to-capital ratio used?
Why cannot terminal growth exceed the economy forever?
Why is revenue growth not enough if reinvestment is ignored?
Why does a low PE not automatically mean cheap?
```

Teaching mode should use concise explanations and show formulas.

---

## 5.4 Audit Mode

Purpose:

Review an existing valuation and find errors.

Audit checklist:

- Cash flow and discount rate mismatch
- Revenue growth inconsistent with market size
- Margins above plausible industry ceiling
- Terminal growth too high
- Stable growth reinvestment missing
- ROC below cost of capital while growth assumed to create value
- Risk-free rate inconsistent with currency
- WACC based on book weights rather than market weights
- Debt not subtracted from firm value
- Cash double counted
- SBC added back incorrectly
- Options diluted incorrectly
- Country risk applied mechanically without exposure adjustment
- Exit multiple terminal value used without fundamental support

---

## 6. Intrinsic Valuation Engine: Detailed Requirements

## 6.1 Company Intake

The agent should start by classifying the company.

Inputs:

```text
Company name
Ticker
Exchange
Country of incorporation
Operating countries
Currency of analysis
Reporting currency
Industry/industries
Business description
Public/private
Financial/non-financial
Current lifecycle stage
Current profitability
Leverage level
Revenue history
Operating income history
Market price
Shares outstanding
```

Company classifications:

| Type | Primary model |
|---|---|
| Stable dividend-paying firm | Dividend discount model or FCFE |
| Stable non-financial firm | FCFF |
| High-growth public company | Multi-stage FCFF |
| Young money-losing company | Revenue-to-margin lifecycle DCF |
| Financial service firm | Equity valuation, excess equity, dividend/FCFE framework |
| Commodity/cyclical firm | Normalized earnings and cycle scenario DCF |
| Distressed firm | Probability-weighted DCF plus distress / liquidation value |
| Holding company | Sum-of-the-parts |
| Patent/R&D-heavy firm | DCF plus option value for patents, with double-counting controls |
| Natural resource firm | Developed reserves DCF plus undeveloped reserves option model |
| Private company | Intrinsic valuation with buyer-specific risk and illiquidity treatment |

---

## 6.2 Current Financials Normalization

The notes repeatedly emphasize that accounting numbers are flawed but important. The system must normalize them before forecasting.

Required normalized fields:

```text
Revenue
EBIT
Adjusted EBIT
EBIT after tax
Net income
Depreciation and amortization
Capital expenditures
Net capital expenditures
Change in non-cash working capital
R&D expense
Operating lease expense / lease liabilities
Stock-based compensation
Interest expense
Cash and marketable securities
Debt
Minority interests
Cross holdings
Pension underfunding
Options and restricted stock
Shares outstanding
```

### Trailing 12-month update

The notes recommend updating stale annual data using quarterly data.

Formula:

```text
Trailing 12-month revenue = Last annual revenue - same-period prior-year interim revenue + current-year interim revenue
```

Same logic should apply to:

- Revenue
- EBIT
- Net income
- Capex
- Depreciation
- Working capital where practical

Product requirement:

The tool should show whether it is using:

```text
Annual data
Trailing 12-month data
Manual user numbers
```

---

## 6.3 Operating Earnings Cleanup

The agent must separate operating, financing, and capital expenses.

### Financing expenses

A financing expense has these characteristics:

```text
Contractual commitment
Tax deductible
Must be paid regardless of operating performance
Failure to pay can cause loss of control
```

Interest and lease financing belong here.

### Capital expenses

A capital expense creates benefits over multiple periods. Accounting may incorrectly expense it.

Examples:

```text
R&D
Brand-building expenses in some cases
Customer acquisition in some business models
Long-term platform/infrastructure investment
```

Product requirement:

Advanced mode should allow users to capitalize R&D and selected operating expenses.

---

## 6.4 Operating Lease Adjustment

Even though accounting standards now capitalize many leases, the agent should still support lease cleanup because data may be inconsistent across periods, countries, or data vendors.

Core logic:

```text
Lease debt = PV of future lease commitments at pre-tax cost of debt
Lease asset = lease debt
Adjusted operating income = operating income + lease expense - depreciation on lease asset
Approximation: adjusted operating income = operating income + pre-tax cost of debt * PV of leases
```

Data fields:

```text
lease_expense_current_year
lease_commitments_by_year
pre_tax_cost_of_debt
lease_asset_life
lease_debt_value
adjusted_operating_income
```

Validation:

- Do not double capitalize leases if lease liabilities are already included and adjusted consistently.
- Show whether lease treatment is accounting-reported or valuation-adjusted.

---

## 6.5 R&D Capitalization

R&D should often be treated as a capital expense because it creates benefits across multiple years.

Required functionality:

- User chooses amortizable life by industry.
- The system builds an R&D asset from historical R&D expenses.
- Adjusted operating income adds back current R&D expense and subtracts amortization of the R&D asset.
- Invested capital increases by the R&D asset.

Formula structure:

```text
R&D asset = sum of unamortized historical R&D expenses
Adjusted EBIT = EBIT + current R&D expense - amortization of R&D asset
Adjusted invested capital = invested capital + R&D asset
```

AI role:

Suggest amortization life by sector, but allow user override.

---

## 6.6 Free Cash Flow to Firm

Core formula:

```text
FCFF = EBIT * (1 - tax rate) - (capital expenditures - depreciation) - change in non-cash working capital
```

Alternative formula:

```text
FCFF = After-tax operating income - reinvestment
```

Where:

```text
Reinvestment = net capital expenditures + change in non-cash working capital
```

The system should explicitly display:

```text
After-tax operating income
Net capex
Change in non-cash working capital
Reinvestment
FCFF
```

---

## 6.7 Free Cash Flow to Equity

Formula:

```text
FCFE = Net income - (capital expenditures - depreciation) - change in non-cash working capital + net debt issued
```

Equivalent framing:

```text
FCFE = cash flow after taxes, reinvestment needs, and debt cash flows
```

Use FCFE when:

- Leverage is stable or can be modeled directly.
- Valuing equity directly.
- Financial service firms require equity-focused valuation.

---

## 6.8 Tax Treatment

The engine should support:

```text
Effective tax rate
Marginal tax rate
Transition from effective to marginal tax rate
NOL / loss carryforward use
Tax holidays
Country-specific tax rates
```

Recommended default:

- Use current effective tax rate in early years if meaningful.
- Move toward marginal tax rate in stable growth.
- For money-losing firms, explicitly model NOL usage before cash taxes normalize.

Validation:

```text
If terminal tax rate is materially below marginal tax rate, require justification.
```

---

## 6.9 Reinvestment Engine

This is central. A Damodaran-style agent must not let users assume high growth without reinvestment.

Key formulas:

```text
Reinvestment rate = Reinvestment / EBIT(1 - tax rate)
Return on capital = EBIT(1 - tax rate) / invested capital
Expected growth in operating income = reinvestment rate * return on capital
```

Alternative using sales-to-capital ratio:

```text
Reinvestment = Change in revenue / sales-to-capital ratio
```

Where:

```text
Sales-to-capital ratio = revenue / invested capital
```

Required inputs:

```text
Historical sales-to-capital ratio
Industry sales-to-capital ratio
User-selected sales-to-capital ratio
Reinvestment rate
Return on capital
Incremental return on capital
```

Diagnostics:

```text
High growth with low reinvestment: warning
Growth while ROC < WACC: value destruction warning
Terminal growth with zero reinvestment: warning
Sales exceeding plausible TAM: warning
```

---

## 6.10 Growth Engine

The notes break growth into multiple sources.

### Historical growth

Historical growth can be useful but dangerous.

Problems:

- Small base effects
- Negative earnings base
- Acquisitions
- Accounting changes
- Cyclicality
- One-time events
- Management changes

The system should not mechanically extrapolate historical growth.

### Analyst estimates

Analyst estimates can be useful for near-term expectations but should not dominate the model.

Use cases:

- First 1 to 3 forecast years
- Consensus anchor
- Market-implied comparison

### Fundamental growth

Core formula:

```text
Expected growth = reinvestment rate * return on capital
```

For equity earnings:

```text
Expected growth in equity earnings = retention ratio * return on equity
```

For FCFE with real reinvestment:

```text
Equity reinvestment rate = (net capex + change in working capital - net debt issued) / net income
Expected growth in net income = equity reinvestment rate * return on equity
```

### Growth from changing returns

When return on capital changes, growth has 2 components:

```text
Growth from new investment
Growth from improvement or deterioration in ROC on existing capital
```

Product requirement:

Advanced mode should allow:

```text
Current ROC
Target ROC
Years to target ROC
Reinvestment rate
```

### Top-down growth

For young companies, growth should be checked against market size.

Inputs:

```text
TAM
Expected market growth
Target market share
Revenue per user / unit
User count / units sold
Take rate
Pricing
```

Diagnostic:

```text
If implied market share > plausible ceiling, flag it.
```

---

## 6.11 Cost of Equity Engine

Core CAPM formula:

```text
Cost of equity = risk-free rate + beta * equity risk premium
```

Expanded country risk version:

```text
Cost of equity = risk-free rate + beta * mature market ERP + lambda * country risk premium
```

The tool should support 3 country risk approaches:

```text
Approach 1: Add CRP equally to all companies in the country
Approach 2: Multiply beta by mature ERP plus CRP
Approach 3: Treat CRP as separate and apply company-specific lambda
```

Recommended default:

Use operation-based country exposure, not just incorporation country.

Inputs:

```text
risk_free_rate
currency
mature_market_erp
country_risk_premium
country_revenue_weights
country_production_weights
lambda_country_risk
beta
```

---

## 6.12 Risk-Free Rate Engine

The risk-free rate must be:

- In the same currency as cash flows.
- Consistent with nominal versus real cash flows.
- Free of default risk.
- Matched reasonably to long-term valuation horizon.

For currencies where government bonds include default risk:

```text
Currency risk-free rate = local government bond yield - default spread
```

Default spread sources:

```text
Sovereign dollar/euro bond spread
Sovereign CDS spread
Sovereign rating-based spread
```

Currency conversion method:

```text
1 + riskfree_rate_foreign = (1 + riskfree_rate_base) * (1 + inflation_foreign) / (1 + inflation_base)
```

Validation:

```text
If cash flows are in INR but discount rate is USD-based, block or require conversion.
If using real cash flows, require real risk-free rate.
If user normalizes risk-free rate upward, require matching inflation/growth assumptions.
```

---

## 6.13 Equity Risk Premium Engine

The notes prefer implied premiums over blindly using long-term historical averages.

Supported methods:

```text
Historical ERP
Current implied ERP
Average implied ERP over time
Country default spread plus mature market premium
Country default spread adjusted by relative equity/bond volatility
```

Warning:

Historical premiums are noisy and highly sensitive to:

```text
Start date
End date
T-bill versus T-bond
Arithmetic versus geometric average
Survivorship bias
```

Product requirement:

The ERP screen should show:

```text
Selected ERP
Source
Date
Method
Mature market premium
Country risk premium
Total ERP
```

---

## 6.14 Beta Engine

The notes strongly prefer bottom-up beta over regression beta.

### Regression beta problems

Regression beta:

- Has high standard error.
- Reflects past business mix, not current business mix.
- Reflects past leverage, not current leverage.

### Bottom-up beta workflow

```text
1. Identify business segments.
2. Find comparable public firms for each business.
3. Estimate average regression beta for peers.
4. Unlever peer betas using peer debt/equity.
5. Weight segment unlevered betas by segment value.
6. Relever using target company's debt/equity.
```

Formula:

```text
Unlevered beta = levered beta / (1 + (1 - tax rate) * debt/equity)
Levered beta = unlevered beta * (1 + (1 - tax rate) * debt/equity)
```

Debt beta advanced formula:

```text
Levered beta = unlevered beta * (1 + (1 - tax rate) * D/E) - debt_beta * (1 - tax rate) * D/E
```

Product requirement:

Quick mode can use industry beta. Advanced mode should allow:

```text
Segment beta table
Peer beta table
Target capital structure
Year-by-year beta fade
```

---

## 6.15 Cost of Debt Engine

Cost of debt is the current long-term borrowing rate, not historical coupon or accounting interest expense.

Supported methods:

```text
Yield to maturity on traded straight bond
Rating-based default spread
Synthetic rating from interest coverage ratio
```

Formula:

```text
Pre-tax cost of debt = risk-free rate + company default spread + applicable country default spread
After-tax cost of debt = pre-tax cost of debt * (1 - marginal tax rate)
```

Synthetic rating input:

```text
Interest coverage ratio = EBIT / interest expense
```

Product requirement:

The system should maintain a default spread table by rating and date.

Validation:

- Do not use subsidized borrowing rate as hurdle rate unless valuing actual financing benefit separately.
- If EBIT is negative, synthetic rating needs special handling.
- For cyclical firms, use normalized EBIT for interest coverage.

---

## 6.16 WACC Engine

Formula:

```text
WACC = cost of equity * E/(D + E) + after-tax cost of debt * D/(D + E)
```

Use market value weights, not book value weights.

Required values:

```text
Market value of equity
Market value of debt
Cost of equity
Pre-tax cost of debt
Marginal tax rate
After-tax cost of debt
Debt ratio
Equity ratio
```

### Market value of debt

If debt is not traded, estimate:

```text
Market value of debt = PV of interest payments + PV of principal repayment at current pre-tax cost of debt
```

### Hybrids

Convertible debt should be split:

```text
Straight debt value = PV of coupon and principal at straight debt rate
Conversion option value = market value of convertible - straight debt value
```

Preferred stock:

```text
Cost of preferred = preferred dividend / preferred market value
```

---

## 6.17 Terminal Value Engine

Terminal value is the most dangerous part of most DCFs. The notes are explicit that stable growth assumptions carry hidden economic assumptions.

### Stable growth formula

For FCFF:

```text
Terminal value_n = FCFF_(n+1) / (WACC_terminal - g_terminal)
```

For FCFE:

```text
Terminal equity value_n = FCFE_(n+1) / (cost_of_equity_terminal - g_terminal)
```

### Stable growth constraints

The agent must enforce:

```text
Terminal growth cannot exceed long-term nominal growth of the economy without warning.
Terminal risk should move toward mature company risk.
Terminal beta should move toward 1 unless justified.
Terminal debt ratio should move toward sustainable industry/mature company ratio.
Terminal reinvestment must support terminal growth.
Stable growth ROC should be explicit.
```

Key formula:

```text
Stable reinvestment rate = terminal growth rate / terminal return on capital
```

Critical diagnostic:

```text
If terminal growth > 0 and terminal reinvestment = 0, flag error.
```

### Exit multiple terminal value

Allowed only as a cross-check or pricing method, not as a disguised DCF closure unless explicitly labeled.

If the user uses exit multiple:

```text
Show implied terminal growth.
Show implied terminal ROC.
Show implied terminal reinvestment.
Compare to intrinsic terminal value.
```

---

## 7. Loose-End Adjustments After Operating Asset Value

After valuing operating assets, the agent must bridge to equity value.

Formula:

```text
Value of operating assets
+ cash and marketable securities
+ non-operating assets
+ value of cross holdings
- debt
- minority interests, if applicable
- underfunded pension/healthcare obligations
- value of employee options
= value of equity
```

Then:

```text
Value per share = value of equity / shares outstanding
```

But employee options should not be handled by crude fully diluted shares alone.

---

## 7.1 Cash and Marketable Securities

Preferred treatment:

- Keep cash out of operating cash flows.
- Add cash separately after valuing operating assets.

Warnings:

- Do not include interest income from cash in operating income and then add cash again.
- Excess cash may deserve discount only if corporate governance risk is material.

---

## 7.2 Cross Holdings

Categories:

```text
Minority passive holdings
Minority active holdings
Majority active holdings / consolidated subsidiaries
```

Required treatment:

- Value parent operating business without cross holdings when possible.
- Add market value or estimated value of minority stakes.
- For consolidated holdings, avoid double counting operating income and assets.
- Adjust minority interest from book to market value where needed.

---

## 7.3 Debt and Debt-Like Claims

Debt includes claims with:

```text
Fixed contractual payments
Tax-deductible payments
Loss of control on default
```

Include:

- Bank debt
- Bonds
- Lease debt
- Debt portion of convertibles
- Underfunded pensions/health obligations, where appropriate
- Other fixed claims

---

## 7.4 Employee Options and Stock-Based Compensation

Key lesson:

Options affect value not merely by increasing share count. They transfer value from existing equity holders to option holders.

Preferred treatment:

```text
1. Value firm or equity.
2. Subtract debt to get equity value.
3. Value outstanding employee options using option pricing, adjusted for dilution and early exercise.
4. Subtract option value from equity value.
5. Divide by actual shares outstanding.
```

For future option grants or SBC:

- Treat as part of compensation expense.
- Do not casually add back SBC as if it were free.
- If adding back SBC to EBITDA, show dilution/equity cost elsewhere.

System warning:

```text
Adding back SBC without subtracting value transferred to employees will overstate equity value.
```

---

## 8. Narrative-to-Numbers Engine

This is one of the most important parts of a Damodaran-style valuation agent.

The notes emphasize that every valuation starts with a story. The story must become numbers.

### Narrative dimensions

The agent should ask:

```text
What business is the company in?
How large can the market become?
What market share can the company capture?
What margins can it earn?
How much must it reinvest to grow?
How risky are the cash flows?
How long can it sustain excess returns?
What can break the story?
```

### Story-to-number mapping

| Narrative claim | Valuation input |
|---|---|
| Huge market opportunity | TAM and revenue growth |
| Market share gains | Revenue scale path |
| Pricing power | Target operating margin |
| Operating leverage | Margin improvement speed |
| Capital-light model | Sales-to-capital ratio |
| Network effects / moat | Length of high-growth period and terminal ROC |
| Regulatory risk | Scenario probabilities or country/business risk |
| Cyclicality | Normalized margins and scenario distribution |
| Execution risk | Failure probability or slower convergence |

### Story quality checks

The notes warn against:

```text
Runaway stories
Big market delusion
Untrustworthy storytellers
Stories at war with numbers
Impossible stories
Improbable stories
```

Agent diagnostics:

```text
Does the story imply revenues greater than plausible market size?
Does the margin exceed the most profitable peers without a reason?
Does the story require growth without reinvestment?
Does the story assume permanent excess returns without a moat?
Does the story rely on optionality already embedded in growth assumptions?
```

### Narrative change tracking

Market intelligence integration should classify events as:

```text
Narrative break/end
Narrative shift
Narrative expansion
Narrative contraction
Temporary noise
```

Then map event to assumptions:

```text
Revenue path
Margin path
Reinvestment need
Cost of capital
Failure probability
Scenario probability
Terminal assumptions
```

---

## 9. Lifecycle-Based Valuation

The uploaded notes emphasize that company lifecycle determines model choice and assumption structure.

## 9.1 Young Growth Companies

Problems:

- Limited operating history
- Small or no revenues
- Large losses
- High failure probability
- High future dilution
- Business model still changing

Recommended model:

```text
Revenue-first lifecycle DCF
```

Key assumptions:

```text
TAM
Revenue growth path
Target market share
Target operating margin
Sales-to-capital ratio
Years to profitability
Cost of capital fade
Probability of failure
Future dilution / capital needs
```

Diagnostics:

```text
Revenue scale versus TAM
Target margin versus mature peers
Reinvestment needed to reach scale
Failure risk separately modeled, not hidden in discount rate
Value changes over time as information arrives
```

---

## 9.2 Mature Companies

Mature firms are easier to value because they have history, stable margins, established reinvestment patterns, and clear peer groups.

Recommended model:

```text
Stable growth DCF or two-stage DCF
```

Key assumptions:

```text
Normalized revenue growth
Stable margin
Stable reinvestment
Industry beta
Mature debt ratio
Terminal growth close to economy growth
```

---

## 9.3 Declining Companies

Declining firms may have:

- Falling revenues
- Lower margins
- Negative growth
- Asset sales
- Shrinking reinvestment
- Potential liquidation value

Recommended model:

```text
Declining cash flow DCF with possible liquidation floor
```

Diagnostics:

```text
Are managers reinvesting despite poor returns?
Is liquidation value higher than going-concern value?
Is terminal value appropriate or should the business fade out?
```

---

## 9.4 Distressed Companies

A standard going-concern DCF is not enough if default risk is material.

Recommended approach:

```text
Expected equity value = probability of survival * going concern equity value + probability of distress * distress sale equity value
```

Where distress sale equity value may be zero if debt exceeds liquidation value.

Advanced option view:

Distressed equity can be modeled as a call option on firm value, with debt face value as exercise price.

Use only in advanced mode.

---

## 9.5 Emerging Market Companies

Important rules:

- Country of incorporation is not enough.
- Exposure depends on where the company earns revenues and where it produces.
- Currency choice should not change value if assumptions are internally consistent.

Required modules:

```text
Country risk premium by country
Revenue-weighted country exposure
Production-weighted country exposure
Currency conversion of discount rates
Governance risk commentary
Cross-holding adjustment
```

---

## 9.6 Financial Service Firms

Financial firms require special treatment.

Why they are different:

- Debt is raw material, not just financing.
- Capex and working capital are hard to define.
- Regulatory capital matters.
- Book equity is more meaningful than for non-financial firms.

Recommended models:

```text
Dividend discount model
Excess equity return model
Price-to-book plus ROE/cost of equity framework
```

Do not use standard FCFF model for banks.

System guardrail:

```text
If company_type == financial_service:
    block standard FCFF by default
    recommend equity valuation / bank model
```

---

## 9.7 Commodity and Cyclical Companies

Problems:

- Current earnings may be peak or trough.
- Commodity price assumptions drive value.
- Margins and revenue should be normalized.

Recommended approach:

```text
Normalized commodity price or macro scenario distribution
Cycle-adjusted revenue and margins
Scenario-weighted value
```

Agent should allow:

```text
Base commodity price
Bull commodity price
Bear commodity price
Probability weights
Normalized margin
```

---

## 9.8 User, Subscriber, and Platform Companies

The relative valuation notes mention that pricing can be built on non-financial operating metrics.

For platform/user companies, model drivers may include:

```text
Users
Subscribers
Monthly active users
Average revenue per user
Churn
Retention
Take rate
Gross merchandise value
Unit economics
Customer acquisition cost
Lifetime value
```

But the intrinsic valuation should still eventually convert these into:

```text
Revenue
Margins
Reinvestment
Cash flows
Risk
```

---

## 10. Relative Valuation Engine: Detailed Requirements

## 10.1 Multiples Must Be Defined Correctly

The tool should never show a multiple without definition.

Core rule:

```text
Numerator and denominator must belong to the same claimholders.
```

Examples:

| Correct | Incorrect / dangerous |
|---|---|
| Market cap / net income | Enterprise value / net income |
| Market cap / book equity | Enterprise value / book equity |
| EV / EBITDA | Market cap / EBITDA |
| EV / sales | Price / sales for high-debt firms |
| EV / invested capital | Market cap / invested capital |

Validation:

```pseudo
if numerator == "enterprise_value" and denominator in ["net_income", "eps", "book_equity"]:
    warning("Claimholder mismatch")
```

---

## 10.2 Describe the Multiple

Before judging a multiple, show distribution.

Metrics:

```text
Sample size
Number with valid multiple
Mean
Median
First quartile
Third quartile
Deciles
Maximum
Minimum
Skewness
Outliers
Number excluded due to negative denominator
```

Important lesson:

Multiples are often skewed. Median is usually more useful than average.

---

## 10.3 Analyze the Multiple

Every multiple is driven by fundamentals.

### PE drivers

```text
Expected growth
Payout ratio or FCFE/earnings
Cost of equity
Risk
Quality of growth through ROE
```

Simple stable growth PE:

```text
PE = payout ratio * (1 + g) / (cost of equity - g)
```

If using FCFE instead of dividends:

```text
PE = (FCFE / earnings) * (1 + g) / (cost of equity - g)
```

### PEG drivers

PEG does not neutralize growth. It is still affected by:

```text
Risk
Payout
Quality of growth
Level of growth
Interest rates
```

System warning:

```text
A low PEG may indicate high risk or poor-quality growth, not undervaluation.
```

### Price-to-book drivers

Stable PBV relationship:

```text
PBV = (ROE - g) / (cost of equity - g)
```

Implication:

```text
If ROE > cost of equity, PBV should exceed 1.
If ROE < cost of equity, PBV should be below 1.
```

### EV/Invested Capital drivers

```text
EV / invested capital = (ROC - g) / (WACC - g)
```

### EV/EBITDA drivers

Driven by:

```text
Cost of capital
Expected growth
Tax rate
Reinvestment needs
Depreciation
Return on capital
```

Important warning:

Low EV/EBITDA does not automatically mean cheap. It may reflect old assets, high reinvestment needs, declining business quality, or risk.

### EV/Sales drivers

Driven by:

```text
After-tax operating margin
Growth
Reinvestment rate
WACC
Terminal assumptions
```

Revenue multiples are useful for young/loss-making firms but can be misleading without margin and reinvestment assumptions.

---

## 10.4 Apply the Multiple

Comparable company selection should be fundamentals-based.

Comparable dimensions:

```text
Business model
Revenue growth
Margins
Return on capital
Risk/beta
Country risk
Capital intensity
Lifecycle stage
Accounting consistency
Size
Liquidity
```

The system should support 4 methods:

1. Direct comparison
2. Story adjustment
3. Modified multiple such as PEG
4. Regression-controlled multiple

---

## 10.5 Regression-Based Relative Valuation

The notes show regressions such as PE explained by growth and emerging market dummy, or PBV explained by ROE and risk.

Product requirement:

Advanced relative valuation should allow:

```text
Dependent variable: selected multiple
Independent variables: growth, margin, beta/risk, ROE, ROC, payout, country risk, size
Regression output: coefficients, R-squared, predicted multiple, residual
```

Output:

```text
Actual multiple
Predicted multiple
Percent over/under priced versus prediction
Confidence warning based on R-squared and sample size
```

---

## 10.6 Relative Valuation Output Format

For each multiple:

```text
Company actual multiple
Peer median
Peer quartile range
Fundamental-adjusted fair multiple
Implied price/value
Premium/discount explanation
Key caveats
```

Example output structure:

```text
EV/EBITDA
- Actual: 9.2x
- Peer median: 8.5x
- Regression-adjusted fair multiple: 10.1x
- Interpretation: company trades above median but below fundamental-adjusted level due to higher margins and lower leverage.
```

---

## 11. Reverse DCF Engine

This should be a high-priority feature because it converts current price into expectations.

Purpose:

```text
Given the current market price, what assumptions must be true?
```

Reverse DCF should solve for one or more of:

```text
Revenue CAGR
Target operating margin
Sales-to-capital ratio
Terminal growth
Terminal ROC
WACC
Market share
```

Recommended reverse DCF flows:

1. Hold margin, WACC, reinvestment constant. Solve for revenue growth.
2. Hold growth, WACC, reinvestment constant. Solve for target margin.
3. Hold revenue and margin path. Solve for terminal ROC or competitive advantage period.
4. Convert implied revenue into implied market share.

Output:

```text
Current price implies:
- Revenue grows at X% for Y years
- Target margin reaches Z%
- Company captures A% of TAM
- Terminal ROC remains B% above WACC
```

Diagnostic:

```text
Plausible / demanding / heroic / impossible
```

---

## 12. Scenario and Sensitivity Engine

### Scenarios

At minimum:

```text
Bear
Base
Bull
Market-implied
User custom
```

For each scenario:

```text
Narrative
Revenue growth
Target margin
Reinvestment efficiency
Cost of capital
Terminal growth
Terminal ROC
Failure probability
Value per share
Probability weight
```

Expected value:

```text
Expected value = sum(probability_i * value_i)
```

### Sensitivities

Core sensitivity tables:

```text
Value versus revenue growth and target margin
Value versus WACC and terminal growth
Value versus sales-to-capital ratio and target margin
Value versus terminal ROC and terminal growth
```

Output should show which assumptions matter most.

---

## 13. Real Options Engine: Advanced Requirements

## 13.1 Option to Delay

Applicable when:

```text
Company has exclusive rights to a project or asset for a fixed period
Project may be negative NPV today but valuable if conditions improve
```

Inputs:

```text
Value of underlying project cash flows today
Cost of investment / exercise price
Life of right
Volatility of project value
Risk-free rate
Cost of delay / dividend yield
Exclusivity score
```

Output:

```text
Option value
Optimal exercise insight
DCF value today
Total value with option
```

---

## 13.2 Patent Option

Patent payoff:

```text
Payoff = max(PV of product cash flows - development cost, 0)
```

Inputs:

```text
PV of expected product cash flows
PV of development cost
Patent life
Risk-free rate
Variance of underlying asset value
Cost of delay
```

Important guardrail:

If DCF already uses high growth from patents, do not also add patent option value unless growth excludes them.

---

## 13.3 Natural Resource Option

Natural resource payoff:

```text
Payoff = max(value of developed reserves - development cost, 0)
```

Inputs:

```text
Estimated reserves
Resource price
Production cost
Taxes and royalties
Development cost
Development lag
Relinquishment life
Volatility of commodity price
Risk-free rate
Net production revenue yield
```

---

## 13.4 Expansion Option

Expansion option payoff:

```text
Payoff = max(PV of expansion project cash flows - expansion investment, 0)
```

Use only if:

```text
The first investment gives the firm meaningful access to the second investment
There is some competitive advantage or barrier
```

Warning:

First-mover advantage alone is often weak. Do not attach large option value unless exclusivity is meaningful.

---

## 13.5 Abandonment Option

Abandonment option is a put option.

Inputs:

```text
PV of project cash flows
Salvage/abandonment value
Life of abandonment right
Variance in project value
Risk-free rate
Dividend yield / cash flow yield
```

Useful when:

```text
Project has flexible cost structure
Company can exit with meaningful salvage value
Long-term obligations are limited
```

---

## 13.6 Distressed Equity as Option

Equity in a highly levered distressed firm can be treated as a call option.

Inputs:

```text
Value of firm assets
Face value of debt
Maturity of debt
Volatility of firm value
Risk-free rate
```

Formula framing:

```text
Equity value = call option on firm value with strike equal to debt face value
```

Use cases:

```text
Deeply distressed firms
Bankrupt or near-bankrupt companies
Highly levered companies with negative earnings
```

Guardrail:

This model is advanced. It requires careful explanation because it can produce positive equity value even when accounting equity is negative.

---

## 14. M&A and Synergy Module: Later-Phase Requirements

The notes warn that acquisition valuations are often contaminated by rationalizations.

Common errors:

```text
Risk transference
Debt subsidies
Arbitrary control premiums
Synergy used as post-hoc justification
Biased comparable deal multiples
Winner's curse
Strategic buzzwords replacing numbers
```

### Control value

Control value should equal:

```text
Value under optimal management - value under current management
```

Expected value of control:

```text
Expected control value = probability of management change * control value
```

### Synergy value

Process:

```text
1. Value acquirer independently.
2. Value target independently.
3. Value combined company with synergy assumptions.
4. Synergy value = combined value with synergy - standalone acquirer value - standalone target value.
```

Synergy types:

```text
Cost savings
Revenue enhancement
Tax benefits
Debt capacity benefits
Lower reinvestment needs
```

Rule:

```text
Value synergy before deciding what premium to pay.
```

---

## 15. Value Enhancement and EVA Module

The notes describe value enhancement through DCF levers.

### Four ways to increase value

```text
1. Increase cash flows from existing assets.
2. Increase expected growth, but only through investments earning more than cost of capital.
3. Reduce cost of capital where appropriate.
4. Extend the period of excess returns / competitive advantage.
```

### EVA formula

```text
EVA = (Return on capital - cost of capital) * capital invested
```

Value connection:

```text
Firm value = capital invested + present value of expected future EVA
```

Critical lesson:

Growth alone does not create value. Growth creates value only when returns exceed the cost of capital.

Product requirement:

Add a value-driver bridge:

```text
Base value
+ value from margin improvement
+ value from better reinvestment / higher ROC
+ value from lower WACC
+ value from longer competitive advantage period
= enhanced value
```

---

## 16. Diagnostics Engine: Required Warnings

This should be a major differentiator.

### 16.1 Cash flow and discount rate warnings

```text
FCFF discounted at cost of equity
FCFE discounted at WACC
Currency mismatch
Real cash flows discounted at nominal rate
Nominal cash flows discounted at real rate
```

### 16.2 Growth warnings

```text
Revenue growth exceeds market growth without market share explanation
Implied market share exceeds plausible cap
Growth assumed without reinvestment
Long high-growth period without competitive advantage
EPS growth driven by buybacks but treated as operating growth
Historical growth extrapolated from small base
```

### 16.3 Reinvestment warnings

```text
Terminal growth with zero reinvestment
Sales-to-capital ratio far above peer range
ROC below WACC while growth is treated as value-creating
Negative reinvestment used indefinitely
Working capital ignored for growth company
```

### 16.4 Margin warnings

```text
Target margin above best-in-class peers without explanation
Margin expansion without operating leverage or pricing power story
Cyclical peak margin used as normalized margin
One-time cost cuts treated as permanent
```

### 16.5 Risk warnings

```text
Risk-free rate does not match currency
Country risk applied based only on incorporation country
Beta from regression used despite changed business mix
Book debt/equity weights used in WACC for public company
Cost of debt based on historical coupon instead of current default risk
```

### 16.6 Terminal value warnings

```text
Terminal growth exceeds risk-free rate or long-term nominal GDP
Terminal value represents excessive percent of total value
Terminal ROC unrealistic
Exit multiple inconsistent with fundamentals
Stable company assumptions inconsistent with high-risk beta
```

### 16.7 Loose-end warnings

```text
Cash double counted
Debt not subtracted from firm value
Minority interest ignored
Cross holdings double counted
Employee options handled only through diluted shares
SBC added back without economic cost
Underfunded pensions ignored
```

### 16.8 Relative valuation warnings

```text
Claimholder mismatch in multiple
Negative denominator exclusions bias sample
Peer group not comparable on fundamentals
Low multiple treated as cheap without controlling for growth/risk
PEG treated as growth-neutral
EV/EBITDA treated as cash flow without capex/reinvestment consideration
```

### 16.9 Real options warnings

```text
No exclusivity, option value likely low or zero
Underlying asset not estimable
Exercise cost not clear
DCF already includes option value through high growth
Volatility input unsupported
```

---

## 17. Database Schema Implications

The valuation agent should store assumptions and outputs, not just final values.

## 17.1 Core tables

### `valuation_projects`

```text
id
user_id
company_id
ticker
company_name
valuation_date
currency
valuation_purpose
company_type
lifecycle_stage
primary_model
status
created_at
updated_at
```

### `company_financials_normalized`

```text
id
company_id
period_type
period_end
revenue
ebit
adjusted_ebit
ebit_after_tax
net_income
depreciation_amortization
capex
net_capex
change_non_cash_working_capital
r_and_d_expense
sbc_expense
lease_expense
interest_expense
cash
debt
book_equity
invested_capital
shares_outstanding
source
created_at
```

### `valuation_assumptions`

```text
id
valuation_project_id
scenario_name
assumption_key
assumption_value
unit
source_type
source_detail
confidence_level
is_user_override
created_at
```

### `forecast_years`

```text
id
valuation_project_id
scenario_name
year_index
calendar_year
revenue
revenue_growth
ebit_margin
ebit
adjusted_tax_rate
ebit_after_tax
reinvestment
reinvestment_rate
sales_to_capital_ratio
roc
fcff
cost_of_capital
pv_fcff
```

### `cost_of_capital_builds`

```text
id
valuation_project_id
scenario_name
currency
risk_free_rate
mature_erp
country_risk_premium
lambda_country_risk
beta_unlevered
beta_levered
cost_of_equity
pre_tax_cost_of_debt
after_tax_cost_of_debt
market_value_equity
market_value_debt
debt_weight
equity_weight
wacc
source_notes
```

### `terminal_value_builds`

```text
id
valuation_project_id
scenario_name
terminal_growth_rate
terminal_roc
terminal_reinvestment_rate
terminal_wacc
terminal_fcff
terminal_value
pv_terminal_value
terminal_value_percent_of_total
warnings_json
```

### `valuation_outputs`

```text
id
valuation_project_id
scenario_name
value_operating_assets
cash_and_non_operating_assets
cross_holdings_value
debt_value
minority_interest_value
pension_adjustment
employee_options_value
equity_value
shares_outstanding
value_per_share
current_price
upside_downside
created_at
```

### `relative_valuation_outputs`

```text
id
valuation_project_id
multiple_type
company_multiple
peer_median
peer_q1
peer_q3
peer_mean
peer_sample_size
controlled_predicted_multiple
implied_value_per_share
premium_discount_explanation
warnings_json
```

### `valuation_diagnostics`

```text
id
valuation_project_id
scenario_name
diagnostic_type
severity
message
affected_assumption
suggested_fix
created_at
```

---

## 18. API Design Implications

Recommended backend endpoints:

```text
POST /api/valuations/projects
GET /api/valuations/projects/:id
POST /api/valuations/projects/:id/financials/normalize
POST /api/valuations/projects/:id/assumptions
POST /api/valuations/projects/:id/run-fcff
POST /api/valuations/projects/:id/run-fcfe
POST /api/valuations/projects/:id/run-relative
POST /api/valuations/projects/:id/run-reverse-dcf
POST /api/valuations/projects/:id/run-scenarios
POST /api/valuations/projects/:id/run-sensitivity
POST /api/valuations/projects/:id/run-diagnostics
POST /api/valuations/projects/:id/generate-memo
GET /api/valuations/projects/:id/report
```

Important backend rule:

```text
Every valuation run should be reproducible from stored financials, assumptions, and formula version.
```

Add:

```text
formula_version
source_version
macro_data_timestamp
market_data_timestamp
```

---

## 19. Frontend Screen Requirements

## 19.1 Quick Valuation Screen

Sections:

```text
Company input
Auto-filled financial summary
5 key assumptions
Run valuation button
Output summary
Diagnostics
```

Key assumption cards:

```text
Revenue growth
Target operating margin
Sales-to-capital / reinvestment
Cost of capital
Terminal growth
```

---

## 19.2 Advanced Assumptions Screen

Tabs:

```text
1. Story
2. Historical financials
3. Accounting adjustments
4. Revenue
5. Margins
6. Reinvestment
7. Risk and WACC
8. Terminal value
9. Loose ends
10. Scenarios
11. Relative pricing
12. Reverse DCF
13. Diagnostics
14. Memo
```

---

## 19.3 Forecast Table

Columns:

```text
Year
Revenue
Revenue growth
Operating margin
EBIT
Tax rate
EBIT after tax
Reinvestment
FCFF
WACC
PV of FCFF
```

Advanced columns:

```text
Sales-to-capital ratio
Invested capital
ROC
Incremental ROC
Working capital
Net capex
```

---

## 19.4 Diagnostics Panel

Severity levels:

```text
Info
Caution
Warning
Critical
```

Each diagnostic should include:

```text
Problem
Why it matters
Affected value driver
Suggested fix
```

---

## 19.5 Narrative Panel

User writes:

```text
My story for the company is...
```

Agent extracts:

```text
Market size claim
Growth claim
Margin claim
Moat claim
Risk claim
Reinvestment claim
```

Then converts into assumptions.

---

## 20. AI Agent Behavior Rules

### 20.1 Model selector agent

Should decide:

```text
Is the company financial or non-financial?
Is it stable, growth, declining, distressed, cyclical, commodity, or private?
Should we use FCFF, FCFE, DDM, relative valuation, SOTP, real options, or a hybrid?
```

Output:

```text
Recommended primary model
Secondary cross-checks
Models to avoid
Reasoning
```

---

### 20.2 Assumption auditor agent

Should identify:

```text
Unsupported assumptions
Internally inconsistent assumptions
Aggressive assumptions
Hidden double counting
Assumptions inconsistent with narrative
Assumptions inconsistent with industry data
```

---

### 20.3 Narrative-to-numbers agent

Should convert story to model inputs.

Input:

```text
User narrative
Company data
Peer data
Industry data
Historical financials
```

Output:

```text
Revenue growth path
Target margin
Reinvestment assumption
Risk assumption
Competitive advantage period
Terminal assumptions
Scenario risks
```

---

### 20.4 Market intelligence impact agent

When new news, filing, transcript, or macro event arrives, the agent should classify impact.

Output:

```text
Event summary
Affected valuation assumptions
Suggested assumption changes
Confidence
Narrative classification
```

Example:

```text
New regulation increases compliance cost.
Affected assumptions:
- Operating margin down 150 bps in years 1-3
- Reinvestment up due to compliance capex
- Scenario probability shifts toward bear case
```

---

### 20.5 Valuation memo agent

Memo structure:

```text
1. Company and story
2. Valuation method
3. Key assumptions
4. Intrinsic value output
5. Relative pricing cross-check
6. Reverse DCF
7. Sensitivity and scenarios
8. Diagnostics
9. Investment conclusion
10. What would change my mind
```

The memo must separate:

```text
Facts
Assumptions
Judgment
Market price
Intrinsic value
```

---

## 21. Build Phasing Recommendation

## Phase 1: Deterministic FCFF Engine

Build first:

```text
Manual company input
Manual financials
Revenue forecast
Margin forecast
Tax rate
Reinvestment using sales-to-capital
FCFF
WACC manual input
Terminal value
Equity bridge
Value per share
Sensitivity table
Basic diagnostics
```

Do not build AI-heavy features yet.

---

## Phase 2: Cost of Capital and Accounting Adjustments

Add:

```text
Risk-free rate module
ERP module
Country risk premium module
Bottom-up beta module
Synthetic rating module
Cost of debt module
Market value debt calculation
Operating lease adjustment
R&D capitalization
SBC warning/treatment
```

---

## Phase 3: Scenario, Reverse DCF, and Relative Pricing

Add:

```text
Bull/base/bear scenarios
Sensitivity tables
Reverse DCF solver
PE, PBV, EV/EBITDA, EV/Sales
Peer group tables
Multiple diagnostics
```

---

## Phase 4: Narrative-to-Numbers and Memo Generation

Add:

```text
Narrative input
Assumption extraction
Story checks
Valuation memo
Assumption audit trail
Market-implied expectation explanation
```

---

## Phase 5: Lifecycle and Special Cases

Add:

```text
Young growth company model
Declining/distressed model
Financial services model
Commodity/cyclical model
Private company model
Sum-of-the-parts model
```

---

## Phase 6: Real Options and M&A

Add only after core engine is stable:

```text
Patent option
Natural resource option
Expansion option
Abandonment option
Distressed equity option
Synergy valuation
Control valuation
EVA/value enhancement module
```

---

## 22. Immediate Codex/Gemini Build Prompt from This Learning Layer

Use this prompt after the full engineering spec is created:

```text
You are building a Damodaran-style valuation agent inside the Market Intelligence Agent app. Do not build a generic DCF calculator. Build a deterministic valuation engine with AI-assisted guidance.

Core principles:
1. Separate intrinsic value from relative pricing.
2. Keep cash flow and discount rate types consistent.
3. Make growth dependent on reinvestment and return on capital.
4. Make terminal value internally consistent with stable growth economics.
5. Use bottom-up beta and current cost of capital logic where possible.
6. Track every assumption by source.
7. Generate diagnostics for unrealistic or inconsistent assumptions.
8. Let AI explain, audit, and translate narrative into assumptions, but do not let AI freehand valuation math.

First build target:
- FCFF DCF with manual and auto-filled inputs
- Assumption storage
- Forecast table
- Terminal value
- Equity bridge
- Value per share
- Basic scenario and sensitivity tables
- Diagnostics engine
- Clean API and data model so later modules can add FCFE, relative valuation, reverse DCF, accounting adjustments, and narrative-to-numbers.
```

---

## 23. What Not To Build Yet

Do not start with:

```text
Full real options engine
Complex M&A synergy module
Full private company illiquidity model
AI-generated valuations without formula transparency
Hundreds of inputs in the first UI
Automated SEC extraction before the manual model works
Overengineered peer regression before simple peer multiples work
```

The first version should make the math correct and transparent.

---

## 24. Open Questions Before Final Engineering Spec

Need answers from the current app/project:

```text
Frontend framework?
Backend framework?
Database?
Current company data source?
Current market price source?
Current SEC ingestion status?
Current LLM provider?
Does app already have company table?
Does app already have portfolio holdings table?
Does app already store filings/news/events?
Will valuations be tied to portfolio positions?
Should first version support US public companies only or India/global too?
```

Need additional Damodaran resources later:

```text
Spreadsheet templates
Current data spreadsheets for ERP, country risk premiums, betas, margins, industry averages
Financial service firm valuation notes
Young growth company valuation notes, if separate
R&D capitalization details, if separate
Employee options/SBC details, if separate
Commodity company valuation notes, if separate
```

---

## 25. Final Product Vision From These Lecture Notes

The valuation agent should feel like this:

```text
A serious valuation analyst that makes the user think clearly.
```

It should not just calculate. It should challenge.

It should ask:

```text
What is your story?
What numbers does that story require?
Are those numbers plausible?
How much reinvestment is needed?
What return on capital is implied?
What does the market price already assume?
What would change the valuation?
Where is the biggest risk of being wrong?
```

The most important feature is not a beautiful DCF table. It is an assumption discipline system.

A good Damodaran-style valuation agent should make bad assumptions harder to hide.

---

## 26. Condensed Checklist for the Next Build-Spec MD

The next MD should turn this learning layer into a code-ready build plan with:

```text
1. Exact product requirements
2. Exact database schema
3. Exact backend service architecture
4. Exact frontend screen/component structure
5. Exact formulas and validation rules
6. Exact API endpoints
7. Exact Codex task sequence
8. Exact test cases
9. Example valuation walkthrough
10. Integration plan with Market Intelligence Agent
```

Minimum viable serious valuation agent:

```text
FCFF DCF
WACC builder
Revenue/margin/reinvestment forecast
Terminal value discipline
Equity bridge
Sensitivity tables
Scenario engine
Relative valuation cross-check
Reverse DCF
Diagnostics
Narrative-to-numbers assistant
Valuation memo generator
```

That is the correct base for the Damodaran-style valuation agent.
