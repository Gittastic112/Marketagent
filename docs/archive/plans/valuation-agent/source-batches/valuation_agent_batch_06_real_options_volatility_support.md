# Valuation Agent Batch 06: Real Options, Volatility, and Optionality Support

## Source file analyzed

- `optvarIndia.xlsx`

## Purpose of this batch

This batch should become the valuation agent's **real options and volatility support layer**.

The earlier batches handle:

- intrinsic valuation
- relative pricing
- growth and reinvestment
- accounting normalization
- shareholder cash returns
- macro sensitivity

This batch handles situations where a standard DCF misses option-like value.

Examples:

```text
Patent value
Undeveloped natural resources
Expansion rights
Abandonment rights
Distressed equity
Convertible securities
Strategic flexibility
```

The most important point:

> Real options should be an advanced add-on, not a default valuation crutch.

Most assets do not deserve an option premium. The agent must apply strict tests before adding option value.

---

# 1. What the spreadsheet contributes

## 1.1 `optvarIndia.xlsx`

### Workbook structure

| Sheet | Role |
|---|---|
| `Variables & FAQ` | Defines standard deviation variables and how firm-value volatility is estimated |
| `Industry Averages` | India industry-level standard deviation in equity and firm value |

### Key variables

| Variable | Meaning | Agent use |
|---|---|---|
| Number of firms | Count of firms in industry grouping | Benchmark reliability |
| Standard Deviation in Equity | Average annualized standard deviation in stock prices | Equity volatility for listed-company risk and option inputs |
| Standard Deviation in Firm Value | Annualized operating-asset volatility estimate | Better input for real options on firm/project assets |
| E/(D+E) | Market equity as share of firm value | Capital structure weighting |
| D/(D+E) | Debt as share of firm value | Capital structure weighting |

### Source-file method for firm-value volatility

The spreadsheet estimates firm-value volatility by combining equity and debt volatility.

It assumes:

```text
Debt standard deviation = 40% of equity standard deviation
Correlation between debt and equity = 0.5
```

Then:

```text
Variance in Firm Value =
(Equity Volatility^2 × Equity Weight^2)
+ (Debt Volatility^2 × Debt Weight^2)
+ 2 × Correlation × Equity Volatility × Debt Volatility × Equity Weight × Debt Weight
```

Then:

```text
Standard Deviation in Firm Value = sqrt(Variance in Firm Value)
```

This is useful because many real options are options on the firm, project, reserves, or operating assets rather than on the traded equity.

---

# 2. Role inside the valuation agent

This batch should create:

```text
Volatility benchmark engine
Real option eligibility test
Real option valuation module
Optionality memo section
Double-counting guardrail
Distressed equity option view
```

It should **not** make every company more valuable because of "strategic optionality."

The agent should only add option value when the option is identifiable, material, and not already counted in the DCF.

---

# 3. Real option eligibility tests

Before valuing any real option, the agent must run 3 tests.

## 3.1 Option test

Ask:

```text
Is there a clearly defined underlying asset?
Is there a finite life?
Is there a clear exercise decision?
Is the payoff asymmetric?
```

Examples:

| Case | Underlying asset | Exercise decision | Option type |
|---|---|---|---|
| Patent | Product/project cash flows | Commercialize or abandon | Call |
| Natural resource reserve | Undeveloped reserve value | Develop/extract or wait | Call |
| Expansion opportunity | New market/product | Invest or do nothing | Call |
| Abandonment right | Existing project | Sell/abandon if bad outcome | Put |
| Distressed equity | Firm assets | Pay off debt or walk away | Call on assets |

---

## 3.2 Exclusivity test

Ask:

```text
Does the company have exclusive or semi-exclusive rights?
```

Option value is highest when exclusivity is strong.

| Exclusivity | Option value |
|---|---|
| Legal monopoly / patent / license | High |
| Contractual right | High to moderate |
| Scarce resource ownership | High to moderate |
| Brand advantage | Moderate, but harder to quantify |
| First-mover advantage only | Weak |
| No barrier to competition | Usually no option value |

### Agent rule

```text
If there is no exclusivity, do not add a real option premium unless the user explicitly overrides.
```

---

## 3.3 Pricing-model test

Ask:

```text
Can the underlying asset be valued?
Can volatility be estimated?
Is the exercise cost reasonably knowable?
Can the option life be estimated?
```

If the answer is weak, use:

```text
Decision tree
Scenario analysis
Qualitative optionality note
```

instead of Black-Scholes.

---

# 4. Volatility benchmark engine

## 4.1 When to use equity volatility

Use equity volatility when valuing:

```text
listed equity option-like claims
warrants
management options
convertibles where equity option is explicit
distressed equity cross-checks
```

---

## 4.2 When to use firm-value volatility

Use firm-value volatility when valuing:

```text
patents
natural resource reserves
expansion options
abandonment options
project flexibility
distressed equity as call on firm assets
```

---

## 4.3 When to override industry volatility

Industry average volatility is only a starting point.

Override when:

```text
company is much more levered than peers
company is early-stage
company is distressed
company has a concentrated product portfolio
commodity exposure is unusually high
project-specific volatility is observable
```

---

# 5. Core formulas

## 5.1 Firm-value volatility from equity and debt

Inputs:

```text
sigma_equity = annualized equity standard deviation
sigma_debt = 0.40 × sigma_equity
weight_equity = E / (D + E)
weight_debt = D / (D + E)
rho = 0.50
```

Formula:

```text
firm_value_variance =
(sigma_equity^2 × weight_equity^2)
+ (sigma_debt^2 × weight_debt^2)
+ 2 × rho × sigma_equity × sigma_debt × weight_equity × weight_debt

sigma_firm = sqrt(firm_value_variance)
```

---

## 5.2 Black-Scholes call option

Use for call-like real options only when assumptions are acceptable.

Inputs:

```text
S = value of underlying asset
K = exercise price / investment required
t = option life in years
r = risk-free rate matching option life
sigma = annualized volatility of underlying asset
y = dividend yield / cost of delay
```

Formula:

```text
d1 = [ln(S / K) + (r - y + sigma^2 / 2) × t] / [sigma × sqrt(t)]

d2 = d1 - sigma × sqrt(t)

Call Value =
S × exp(-y × t) × N(d1)
- K × exp(-r × t) × N(d2)
```

---

## 5.3 Black-Scholes put option

Use for abandonment options.

```text
Put Value =
K × exp(-r × t) × [1 - N(d2)]
- S × exp(-y × t) × [1 - N(d1)]
```

---

## 5.4 Option-adjusted value

```text
Option-Adjusted Value =
Base DCF Value
+ Real Option Value
- Double-Counted Growth/Option Value
```

The last line is crucial. If the base DCF already assumes the upside from a patent, expansion plan, or reserve development, do not add the option value again.

---

# 6. Real option modules

## 6.1 Patent / product-development option

### When to use

```text
biotech
pharma
deep tech
IP-heavy firms
early product pipeline companies
```

### Inputs

```text
S = PV of expected cash flows if commercialized today
K = PV of development/commercialization cost
t = remaining patent/protection life
sigma = volatility of project/product value
r = risk-free rate
y = cost of delay
```

### Output

```text
Patent option value
Probability-like option delta
Key assumptions
Double-counting warning
```

### Agent warning

```text
If the DCF already includes commercial success of the patent in revenue growth, do not add the patent option value separately.
```

---

## 6.2 Natural resource option

### When to use

```text
oil and gas reserves
mining reserves
undeveloped land with extraction rights
commodity-linked reserves
```

### Inputs

```text
S = value of reserves, net of production costs
K = development/extraction cost
t = concession/relinquishment life
sigma = commodity/reserve value volatility
r = risk-free rate
y = net production revenue / reserve value, or cost of delay
development_lag = years before production starts
```

### Output

```text
Value of developed reserves
Value of undeveloped reserves as option
Total resource value
```

### Agent warning

```text
Do not value undeveloped reserves both as future DCF cash flows and as a separate option.
```

---

## 6.3 Expansion option

### When to use

```text
first project creates access to a second market
platform business can expand into adjacent vertical
license creates option to enter new region
brand creates credible expansion path
```

### Inputs

```text
S = PV of expansion cash flows
K = cost of expansion
t = window to expand
sigma = volatility of expansion project value
r = risk-free rate
y = cost of delay
exclusivity_score = 0 to 1
```

### Formula

```text
Raw Expansion Option Value = Black-Scholes Call Value

Adjusted Expansion Option Value =
Raw Expansion Option Value × Exclusivity Score
```

### Agent warning

Most expansion options are overclaimed. The agent should only add value when there is a real barrier to competition or a credible prerequisite relationship.

---

## 6.4 Abandonment option

### When to use

```text
project has resale/salvage value
contract allows exit
assets can be sold
costs can be made variable
management can stop losses
```

### Inputs

```text
S = PV of remaining project cash flows
K = salvage value / abandonment value
t = period during which abandonment is possible
sigma = project value volatility
r = risk-free rate
y = cash-flow yield or cost of delay
```

### Formula

```text
Abandonment Option Value = Put Value
```

### Agent interpretation

Abandonment options are more valuable when:

```text
asset value volatility is high
salvage value is meaningful
fixed obligations are low
labor/customer contracts are flexible
management can actually exit
```

---

## 6.5 Distressed equity as a call option

### When to use

```text
firm value is below or near face value of debt
earnings are negative
leverage is high
equity market cap seems irrationally positive
company is close to default or restructuring
```

### Inputs

```text
S = value of firm assets
K = face value of debt
t = average debt maturity
sigma = firm value volatility
r = risk-free rate
```

### Formula

```text
Equity Value = Call Option on Firm Assets
```

This helps explain why equity can still have value even when accounting equity is negative.

### Agent warning

```text
This is not a normal DCF valuation. It is a distressed-claim valuation and should be presented as a separate lens.
```

---

# 7. Data model

## 7.1 `industry_volatility_benchmarks`

```sql
CREATE TABLE industry_volatility_benchmarks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    country TEXT NOT NULL,
    region TEXT,
    data_date DATE,
    industry_name TEXT NOT NULL,

    number_of_firms INTEGER,
    equity_standard_deviation NUMERIC,
    firm_value_standard_deviation NUMERIC,
    equity_value_weight NUMERIC,
    debt_value_weight NUMERIC,

    assumed_debt_to_equity_vol_ratio NUMERIC DEFAULT 0.40,
    assumed_debt_equity_correlation NUMERIC DEFAULT 0.50,

    source_file TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT now(),

    UNIQUE(country, data_date, industry_name, source_file)
);
```

---

## 7.2 `real_option_assumptions`

```sql
CREATE TABLE real_option_assumptions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    valuation_id UUID NOT NULL REFERENCES valuations(id),
    company_id UUID REFERENCES companies(id),

    option_type TEXT NOT NULL,
    option_name TEXT,

    underlying_asset_value NUMERIC NOT NULL,
    exercise_price NUMERIC NOT NULL,
    option_life_years NUMERIC NOT NULL,
    risk_free_rate NUMERIC NOT NULL,
    volatility NUMERIC NOT NULL,
    dividend_yield_or_cost_of_delay NUMERIC DEFAULT 0,

    exclusivity_score NUMERIC DEFAULT 1,
    development_lag_years NUMERIC,
    source_of_volatility TEXT,
    source_of_underlying_value TEXT,

    created_at TIMESTAMP DEFAULT now()
);
```

---

## 7.3 `real_option_results`

```sql
CREATE TABLE real_option_results (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    real_option_assumption_id UUID NOT NULL REFERENCES real_option_assumptions(id),
    valuation_id UUID NOT NULL REFERENCES valuations(id),

    d1 NUMERIC,
    d2 NUMERIC,
    nd1 NUMERIC,
    nd2 NUMERIC,

    raw_option_value NUMERIC,
    adjusted_option_value NUMERIC,
    option_delta NUMERIC,
    option_value_pct_base_dcf NUMERIC,

    eligibility_passed BOOLEAN,
    eligibility_warnings JSONB,
    double_counting_warnings JSONB,

    created_at TIMESTAMP DEFAULT now()
);
```

---

## 7.4 `option_eligibility_tests`

```sql
CREATE TABLE option_eligibility_tests (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    valuation_id UUID NOT NULL REFERENCES valuations(id),
    option_type TEXT NOT NULL,

    has_underlying_asset BOOLEAN,
    has_finite_life BOOLEAN,
    has_clear_exercise_price BOOLEAN,
    has_asymmetric_payoff BOOLEAN,
    has_exclusivity BOOLEAN,
    can_estimate_volatility BOOLEAN,
    can_estimate_underlying_value BOOLEAN,

    eligibility_score NUMERIC,
    recommendation TEXT,

    created_at TIMESTAMP DEFAULT now()
);
```

---

# 8. Backend services

## 8.1 `VolatilityBenchmarkIngestionService`

### Responsibilities

- Parse `optvarIndia.xlsx`
- Extract `Industry Averages`
- Normalize industry volatility data
- Store equity and firm-value volatility benchmarks

### Required normalization

```text
"Industry Name" -> industry_name
"Number of Firms" -> number_of_firms
"Std Deviation in Equity" -> equity_standard_deviation
"Std Deviation in Firm Value" -> firm_value_standard_deviation
"E/(D+E)" -> equity_value_weight
"D/(D+E)" -> debt_value_weight
```

---

## 8.2 `VolatilityEstimationService`

### Responsibilities

- Fetch industry volatility benchmark
- Let user choose equity volatility or firm-value volatility
- Compute firm-value volatility if only equity volatility and capital structure exist
- Allow manual override
- Store source and confidence

### Output

```ts
type VolatilityEstimate = {
  volatility: number
  volatilityType: "equity" | "firm_value" | "project" | "commodity" | "manual"
  source: string
  confidence: "low" | "medium" | "high"
  warnings: string[]
}
```

---

## 8.3 `RealOptionEligibilityService`

### Responsibilities

Run the option test, exclusivity test, and pricing-model test.

### Output

```ts
type RealOptionEligibilityResult = {
  eligibilityPassed: boolean
  eligibilityScore: number
  recommendation: "value_with_option_model" | "use_decision_tree" | "qualitative_only" | "do_not_add_option_value"
  warnings: string[]
}
```

### Scoring suggestion

| Test | Weight |
|---|---:|
| Underlying asset clearly identifiable | 20% |
| Finite life | 10% |
| Clear exercise price | 15% |
| Asymmetric payoff | 15% |
| Exclusivity | 25% |
| Volatility and asset value estimable | 15% |

---

## 8.4 `BlackScholesRealOptionService`

### Responsibilities

- Calculate d1
- Calculate d2
- Calculate N(d1)
- Calculate N(d2)
- Calculate call or put value
- Apply exclusivity adjustment when relevant
- Return intermediate values for transparency

### Validation rules

```text
S > 0
K > 0
t > 0
sigma > 0
risk_free_rate must match currency and option life
dividend_yield_or_cost_of_delay >= 0
exclusivity_score between 0 and 1
```

---

## 8.5 `RealOptionIntegrationService`

### Responsibilities

- Add option value to base DCF only when allowed
- Check double counting
- Add option value as separate line item
- Generate option-adjusted valuation output

### Required output structure

```text
Base DCF value
+ Patent option value
+ Expansion option value
+ Abandonment option value
+ Resource option value
= Option-adjusted value
```

Never bury option value inside revenue growth without showing it.

---

# 9. API design

## 9.1 Get volatility benchmark

```http
GET /api/valuation/options/volatility?country=India&industry=Auto%20Parts
```

### Response

```json
{
  "country": "India",
  "industry": "Auto Parts",
  "numberOfFirms": 120,
  "equityStandardDeviation": 0.393,
  "firmValueStandardDeviation": 0.365,
  "equityValueWeight": 0.84,
  "debtValueWeight": 0.16,
  "assumptions": {
    "debtToEquityVolatilityRatio": 0.4,
    "debtEquityCorrelation": 0.5
  }
}
```

---

## 9.2 Run real option eligibility test

```http
POST /api/valuation/options/eligibility
```

### Request

```json
{
  "valuationId": "uuid",
  "optionType": "expansion",
  "description": "Company can enter adjacent software market using current customer base.",
  "hasUnderlyingAsset": true,
  "hasFiniteLife": true,
  "hasClearExercisePrice": false,
  "hasAsymmetricPayoff": true,
  "hasExclusivity": false,
  "canEstimateVolatility": true,
  "canEstimateUnderlyingValue": true
}
```

### Response

```json
{
  "eligibilityPassed": false,
  "eligibilityScore": 0.55,
  "recommendation": "qualitative_only",
  "warnings": [
    "The expansion opportunity has weak exclusivity.",
    "Exercise cost is not clearly defined.",
    "Do not add a full option premium to the DCF."
  ]
}
```

---

## 9.3 Value a real option

```http
POST /api/valuation/options/value
```

### Request

```json
{
  "valuationId": "uuid",
  "optionType": "patent",
  "optionName": "Drug Candidate A",
  "underlyingAssetValue": 3422,
  "exercisePrice": 2875,
  "optionLifeYears": 17,
  "riskFreeRate": 0.067,
  "volatility": 0.473,
  "dividendYieldOrCostOfDelay": 0.0589,
  "exclusivityScore": 1.0
}
```

### Response

```json
{
  "d1": 1.1362,
  "d2": -0.8512,
  "nd1": 0.872,
  "nd2": 0.2076,
  "rawOptionValue": 907,
  "adjustedOptionValue": 907,
  "warnings": [
    "Check whether patent success is already reflected in base DCF revenue growth."
  ]
}
```

---

# 10. Frontend requirements

## 10.1 Real option tab

Only show this in advanced mode.

Sections:

```text
Option type selector
Eligibility test
Volatility source
Option assumptions
Option value output
Double-counting warning
```

---

## 10.2 Option type selector

Options:

```text
Patent / Product option
Natural resource option
Expansion option
Abandonment option
Distressed equity option
Convertible / warrant option
Custom option
```

---

## 10.3 Eligibility test card

Show checklist:

| Test | Status |
|---|---|
| Underlying asset exists | Pass / Fail |
| Finite life | Pass / Fail |
| Exercise cost known | Pass / Fail |
| Asymmetric payoff | Pass / Fail |
| Exclusivity | Pass / Fail |
| Volatility estimable | Pass / Fail |
| Underlying value estimable | Pass / Fail |

Then show:

```text
Recommended treatment:
- Add option value
- Use scenario analysis instead
- Qualitative note only
- Do not include
```

---

## 10.4 Volatility source panel

Options:

```text
Industry equity volatility
Industry firm-value volatility
Company historical equity volatility
Commodity volatility
Project simulation volatility
Manual override
```

Always display:

```text
Volatility selected:
Source:
Confidence:
Reason:
```

---

## 10.5 Option value output

Display:

```text
Base DCF value
Real option value
Option-adjusted value
Option value as % of base DCF
Sensitivity to volatility
Sensitivity to exercise price
Sensitivity to option life
```

---

# 11. Integration with DCF engine

## 11.1 Add options below the base valuation

The DCF output should look like:

```text
Value of operating assets from DCF
+ Cash and non-operating assets
- Debt
= Base equity value

+ Separately valued real options
= Option-adjusted equity value
```

Do not hide option value in terminal value.

---

## 11.2 Double-counting guardrail

The agent must ask:

```text
Is the upside from this option already included in revenue growth, margin expansion, or terminal value?
```

If yes:

```text
Do not add full option value separately.
```

Possible treatments:

```text
remove option upside from base DCF and add explicit option value
or keep base DCF as-is and show option value only as a sensitivity
```

---

## 11.3 Scenario alternative

If option criteria are weak, use scenario analysis:

```text
Base case: no exercise
Upside case: option exercised
Probability-weighted value
```

This is often better than Black-Scholes for vague strategic options.

---

# 12. Agent behavior rules

## 12.1 Do not add "strategic option value" casually

The agent must not say:

```text
The company has strategic options, so add a premium.
```

It should say:

```text
There may be optionality, but the option should not be valued separately unless there is a clear underlying asset, finite life, exercise cost, asymmetric payoff, and some exclusivity.
```

---

## 12.2 Always show base DCF and option value separately

```text
Base DCF value: X
Option value: Y
Option-adjusted value: X + Y
```

---

## 12.3 Prefer qualitative treatment for weak expansion options

Most expansion options have weak exclusivity. The agent should usually treat them as scenario upside, not as a hard valuation add-on.

---

## 12.4 Treat higher volatility carefully

In option pricing, higher volatility can increase option value. But the agent must explain why:

```text
For options, downside is limited and upside remains open, so higher volatility can increase option value. This does not mean higher risk always increases business value in a normal DCF.
```

---

## 12.5 Distressed equity warning

For distressed companies:

```text
Equity can have option value even when debt exceeds firm value, but this is a speculative claim on volatility and recovery, not evidence that the operating business is healthy.
```

---

# 13. Diagnostics and warnings

## 13.1 Weak exclusivity warning

```text
The option has weak exclusivity. A full option-pricing premium is probably not justified.
```

## 13.2 Exercise cost warning

```text
The exercise price is not clearly defined. Option value is highly unreliable.
```

## 13.3 Volatility source warning

```text
Industry firm-value volatility is a rough proxy. Use project-specific volatility if available.
```

## 13.4 Double-counting warning

```text
The base DCF already appears to include this upside. Adding option value separately may double count.
```

## 13.5 Black-Scholes limitation warning

```text
Black-Scholes assumes a tradable underlying asset and continuous price process. Real options often violate these assumptions, so treat the result as approximate.
```

---

# 14. Implementation checklist for Codex/Gemini

## Phase 1: Volatility benchmark ingestion

- [ ] Parse `optvarIndia.xlsx`
- [ ] Store industry equity volatility
- [ ] Store industry firm-value volatility
- [ ] Store E/(D+E) and D/(D+E)
- [ ] Store source assumptions for debt volatility and debt/equity correlation

## Phase 2: Volatility service

- [ ] Add volatility source selector
- [ ] Compute firm-value volatility from equity/debt weights if needed
- [ ] Allow manual override
- [ ] Store selected volatility source and confidence

## Phase 3: Eligibility engine

- [ ] Add option test
- [ ] Add exclusivity test
- [ ] Add pricing-model test
- [ ] Return recommendation
- [ ] Prevent option value inclusion when eligibility fails unless user overrides

## Phase 4: Option valuation engine

- [ ] Implement Black-Scholes call
- [ ] Implement Black-Scholes put
- [ ] Implement dividend/cost-of-delay adjustment
- [ ] Return d1, d2, N(d1), N(d2), raw value, adjusted value
- [ ] Add sensitivity to volatility, exercise price, and option life

## Phase 5: DCF integration

- [ ] Add separate real options line item
- [ ] Add option-adjusted value
- [ ] Add double-counting warning
- [ ] Add scenario treatment fallback

## Phase 6: UI and agent

- [ ] Add advanced real option tab
- [ ] Add eligibility checklist
- [ ] Add volatility source panel
- [ ] Add option value bridge
- [ ] Add memo explanation section

---

# 15. Minimal Codex prompt

```text
Build the valuation agent's real options and volatility support module using the Batch 06 specification.

Implement ingestion for optvarIndia.xlsx, storing industry equity volatility, firm-value volatility, E/(D+E), and D/(D+E). Add a volatility estimation service, real option eligibility service, and Black-Scholes real option valuation service for call and put options with dividend/cost-of-delay adjustment.

Real options must be advanced-mode only. The system must run eligibility tests before adding option value and must warn against double counting. The backend should calculate all option values deterministically. The LLM should explain optionality, flag weak assumptions, and recommend scenario analysis when option pricing is not justified.
```

---

# 16. Bottom line

This batch gives the agent a controlled way to handle optionality.

The key implementation principle is:

> Real options can add value, but only when the option is identifiable, exclusive, finite, and not already counted in the DCF.

