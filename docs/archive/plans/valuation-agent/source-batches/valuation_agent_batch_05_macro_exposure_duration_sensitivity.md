# Valuation Agent Batch 05: Macro Exposure, Duration, Cyclicality, Inflation, and Currency Sensitivity

## Source files analyzed

- `macro.xlsx`
- `macrodur.xlsx`

## Purpose of this batch

This batch should become the valuation agent's **macro sensitivity layer**.

The earlier batches answer:

- What does the business earn?
- What does it reinvest?
- How does it compare to peers?
- What cash can equity holders receive?

This batch answers:

> How sensitive is this company's value and operating income to interest rates, economic growth, inflation, and currency movements?

That matters because a Damodaran-style valuation agent should not simply use one static WACC and one static revenue-growth assumption. A serious valuation tool should explain how macro changes affect:

- discount rates
- revenue growth
- operating margins
- reinvestment
- terminal value
- scenario probabilities
- relative pricing
- investment risk

---

# 1. What each spreadsheet contributes

## 1.1 `macro.xlsx`

### Workbook structure

| Sheet | Role |
|---|---|
| `Annual Data` | Annual macro series: Treasury bond rate, GDP, CPI, weighted dollar, and changes |
| `Quarterly Data` | Quarterly macro series: Treasury bond rate, GDP, CPI, major currency rates, and changes |

### Key variables

| Variable | Meaning | Agent use |
|---|---|---|
| T.Bond Rate | Long-term interest rate | Risk-free rate / duration sensitivity |
| Change in rate | Period-over-period change in long-term rate | Regression input for duration |
| GDP / Real GDP | Economic output | Cyclicality input |
| % Change in GDP | GDP growth | Revenue and earnings cyclicality |
| CPI | Inflation measure | Inflation sensitivity |
| Change in CPI | Inflation shock/change | Margin and pricing-power diagnostics |
| Weighted Dollar | Broad dollar index | Currency exposure |
| % Change in Dollar | Currency movement | FX sensitivity |

### Important note

The uploaded `macro.xlsx` appears to be a supporting macro dataset with annual and quarterly variables. The more directly useful file for the agent is `macrodur.xlsx`, because it combines macro data with a calculator and sector averages.

The app should still store macro raw data separately, because it can support future regressions, charts, and scenario engines.

---

## 1.2 `macrodur.xlsx`

### Workbook structure

| Sheet | Role |
|---|---|
| `Read me first` | Explains that the model estimates how firm cash flows and value change with macro variables |
| `Inputs for top down` | User/company inputs: operating income, market cap, total debt by period |
| `Duration Calculator` | Regression output and top-down macro sensitivities |
| `Bottom up Estimator` | Weighted SIC/business exposure estimator |
| `Annual Data` | Updated macro series |
| `Quarterly Data` | Updated macro series |
| `Sector Averages by SIC` | Sector-level duration, cyclicality, inflation, and currency sensitivities |

### Key outputs in the spreadsheet

| Output | Meaning |
|---|---|
| Duration of firm's assets | Sensitivity to interest-rate changes |
| Cyclicality of firm's assets | Sensitivity to GDP/economic growth |
| Sensitivity to inflation | How operating income/value changes with inflation |
| Sensitivity to dollar movements | How operating income/value changes with currency movements |

### Top-down method

The model asks for historical company data:

```text
Operating Income
Market Cap
Total Debt
```

Then computes:

```text
Firm Value = Market Cap + Total Debt
Change in Operating Income
Change in Firm Value
```

Then it compares those changes against macro changes:

```text
Change in long-term bond rate
Change in GDP
Change in inflation
Change in currency
```

### Bottom-up method

The model also allows a bottom-up estimate using SIC or business classifications:

```text
Business/SIC segment
Value or revenue weight
Sector duration
Sector cyclicality
Sector inflation sensitivity
Sector currency sensitivity
Weighted average company sensitivity
```

This is the better method when the company has too little history, bad data, or noisy regression outputs.

---

# 2. Core product role inside the valuation agent

This batch should create a **macro diagnostics and scenario module**.

It should not replace the DCF. It should improve the DCF by showing how assumptions change under macro shocks.

The module should answer:

```text
Is this company rate-sensitive?
Is this company cyclical?
Does inflation help or hurt the company?
Does currency movement help or hurt the company?
Should the DCF have a macro bear/base/bull scenario?
Does the company's valuation deserve a higher uncertainty band?
```

---

# 3. Top-down sensitivity engine

## 3.1 Required company inputs

For each period:

```text
period
operating_income
market_cap
total_debt
```

Optional:

```text
cash
enterprise_value
revenue
ebitda
currency
filing_date
```

### Derived variable

```text
Firm Value = Market Cap + Total Debt
```

Use enterprise value if available and consistently defined.

---

## 3.2 Required macro inputs

For the same periods:

```text
long_term_bond_rate
change_in_long_term_bond_rate
gdp_growth
inflation_change
currency_change
```

---

## 3.3 Regression method

The agent should support 2 dependent variables:

```text
Change in Firm Value
Change in Operating Income
```

And 4 independent macro variables:

```text
Change in long-term bond rate
GDP growth
Change in inflation
Change in currency
```

### Single-factor regressions

For each dependent variable:

```text
dependent_variable = alpha + beta * macro_variable
```

This produces:

```text
interest_rate_slope
gdp_slope
inflation_slope
currency_slope
```

### Multi-factor regression, optional advanced mode

```text
dependent_variable =
alpha
+ beta_rate * change_in_long_term_rate
+ beta_gdp * gdp_growth
+ beta_inflation * change_in_inflation
+ beta_currency * currency_change
```

### Important warning

The spreadsheet itself warns that top-down regressions should be read carefully because few observations and outliers can distort results. The agent must say this when showing regression-based macro sensitivity.

---

## 3.4 Duration calculation

The spreadsheet logic implies:

```text
Duration = max(0, -1 * slope_vs_interest_rate_change)
```

Reason:

- If value falls when rates rise, the slope is negative and duration is positive.
- If the slope is positive, duration should not be interpreted as normal asset duration.

### Example

```text
Slope vs interest-rate change = -1.78
Duration = 1.78
```

If:

```text
Slope vs interest-rate change = +0.39
Duration = 0
```

### Agent interpretation

| Duration | Interpretation |
|---:|---|
| 0 to 1 | Low rate sensitivity |
| 1 to 3 | Moderate rate sensitivity |
| 3 to 6 | High rate sensitivity |
| > 6 | Very high rate sensitivity; likely long-duration cash flows or noisy regression |

---

## 3.5 Cyclicality calculation

```text
Cyclicality = slope of value or operating-income change vs GDP growth
```

### Interpretation

| Cyclicality | Meaning |
|---:|---|
| < 0 | Countercyclical or noisy |
| 0 to 0.5 | Defensive |
| 0.5 to 1.5 | Moderately cyclical |
| > 1.5 | Highly cyclical |

### Agent behavior

The agent should distinguish:

```text
Value cyclicality
Operating income cyclicality
```

A company can have defensive operating income but rate-sensitive valuation.

---

## 3.6 Inflation sensitivity

```text
Inflation Sensitivity = slope of value or operating-income change vs change in CPI
```

### Interpretation

Positive inflation sensitivity may mean:

- pricing power
- commodity-linked revenues
- nominal revenue uplift
- asset-heavy replacement value benefit

Negative inflation sensitivity may mean:

- cost inflation pressure
- fixed-price contracts
- weak pricing power
- wage or input cost squeeze

The agent should not assume inflation is always bad.

---

## 3.7 Currency sensitivity

```text
Currency Sensitivity = slope of value or operating-income change vs currency movement
```

The agent must define the currency variable clearly. In the source data, currency movement may reflect changes in a dollar index or exchange rate series. The direction matters.

### Agent warning

```text
Currency sensitivity is only meaningful if the currency series direction is clearly defined. A positive coefficient can mean benefit or harm depending on whether the variable represents dollar strength, rupee depreciation, yen per dollar, or another exchange-rate convention.
```

---

# 4. Bottom-up macro exposure estimator

## 4.1 Why bottom-up is often better

Top-down regression requires good company history. It can fail when:

- the company has fewer than 3 years of data
- business mix changed
- market cap was distorted by bubbles or crashes
- operating income has one-time items
- leverage changed sharply
- the sample period is too short
- macro variables are correlated

Bottom-up is better for:

- private companies
- IPOs
- companies with short trading histories
- conglomerates
- companies whose business mix changed
- emerging market firms with noisy market data

---

## 4.2 Bottom-up formula

For each business segment:

```text
Segment Weight = Segment Value / Total Segment Value
```

Then:

```text
Company Duration =
Σ(Segment Weight × Segment Duration)

Company Cyclicality =
Σ(Segment Weight × Segment Cyclicality)

Company Inflation Sensitivity =
Σ(Segment Weight × Segment Inflation Sensitivity)

Company Currency Sensitivity =
Σ(Segment Weight × Segment Currency Sensitivity)
```

### Value weights preferred

Use segment value where possible.

Fallback hierarchy:

```text
segment enterprise value
segment operating income capitalized by industry multiple
segment revenue × industry EV/Sales
segment revenue
```

---

# 5. Data model

## 5.1 `macro_time_series`

```sql
CREATE TABLE macro_time_series (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    source_file TEXT NOT NULL,
    frequency TEXT NOT NULL, -- annual, quarterly, monthly
    period_label TEXT NOT NULL,
    period_end_date DATE,

    tbond_rate NUMERIC,
    change_in_rate NUMERIC,
    gdp_level NUMERIC,
    gdp_growth NUMERIC,
    cpi_level NUMERIC,
    change_in_cpi NUMERIC,
    weighted_dollar NUMERIC,
    change_in_weighted_dollar NUMERIC,

    yen_dollar NUMERIC,
    change_vs_yen NUMERIC,
    dollar_euro NUMERIC,
    change_vs_euro NUMERIC,
    dollar_bp NUMERIC,
    change_vs_bp NUMERIC,

    created_at TIMESTAMP DEFAULT now(),

    UNIQUE(source_file, frequency, period_label)
);
```

---

## 5.2 `sector_macro_sensitivity_benchmarks`

```sql
CREATE TABLE sector_macro_sensitivity_benchmarks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    source_file TEXT NOT NULL,
    data_date DATE,
    sic_code INTEGER,
    industry_name TEXT NOT NULL,

    firm_value_duration NUMERIC,
    firm_value_cyclicality NUMERIC,
    firm_value_inflation_sensitivity NUMERIC,
    firm_value_currency_sensitivity NUMERIC,

    operating_income_duration NUMERIC,
    operating_income_cyclicality NUMERIC,
    operating_income_inflation_sensitivity NUMERIC,
    operating_income_currency_sensitivity NUMERIC,

    created_at TIMESTAMP DEFAULT now(),

    UNIQUE(source_file, data_date, sic_code, industry_name)
);
```

---

## 5.3 `company_macro_inputs`

```sql
CREATE TABLE company_macro_inputs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    company_id UUID NOT NULL REFERENCES companies(id),
    period_label TEXT NOT NULL,
    period_end_date DATE,

    operating_income NUMERIC,
    market_cap NUMERIC,
    total_debt NUMERIC,
    cash NUMERIC,
    enterprise_value NUMERIC,

    source_document_id UUID,
    created_at TIMESTAMP DEFAULT now(),

    UNIQUE(company_id, period_label)
);
```

---

## 5.4 `company_macro_sensitivity_results`

```sql
CREATE TABLE company_macro_sensitivity_results (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    company_id UUID NOT NULL REFERENCES companies(id),
    valuation_id UUID REFERENCES valuations(id),

    method TEXT NOT NULL, -- top_down, bottom_up, blended
    dependent_variable TEXT NOT NULL, -- firm_value, operating_income
    observation_count INTEGER,

    duration NUMERIC,
    cyclicality NUMERIC,
    inflation_sensitivity NUMERIC,
    currency_sensitivity NUMERIC,

    rate_slope NUMERIC,
    gdp_slope NUMERIC,
    inflation_slope NUMERIC,
    currency_slope NUMERIC,

    regression_r_squared JSONB,
    confidence_label TEXT,
    warnings JSONB,

    created_at TIMESTAMP DEFAULT now()
);
```

---

## 5.5 `company_macro_segment_exposures`

```sql
CREATE TABLE company_macro_segment_exposures (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    company_id UUID NOT NULL REFERENCES companies(id),
    valuation_id UUID REFERENCES valuations(id),

    segment_name TEXT NOT NULL,
    sic_code INTEGER,
    benchmark_industry_name TEXT,
    segment_value NUMERIC,
    segment_revenue NUMERIC,
    segment_weight NUMERIC,

    duration NUMERIC,
    cyclicality NUMERIC,
    inflation_sensitivity NUMERIC,
    currency_sensitivity NUMERIC,

    created_at TIMESTAMP DEFAULT now()
);
```

---

# 6. Backend services

## 6.1 `MacroDataIngestionService`

### Responsibilities

- Parse `macro.xlsx`
- Parse `macrodur.xlsx`
- Extract annual and quarterly macro time series
- Normalize period labels
- Store data in `macro_time_series`

### Required logic

```text
Date values like 2025.12, 2025.09, 2025.06, 2025.03 should be normalized as quarterly period labels.
```

Example:

```text
2025.12 -> 2025 Q4
2025.09 -> 2025 Q3
2025.06 -> 2025 Q2
2025.03 -> 2025 Q1
```

---

## 6.2 `SectorMacroSensitivityIngestionService`

### Responsibilities

- Parse `Sector Averages by SIC` from `macrodur.xlsx`
- Extract SIC code, industry name, and macro sensitivity values
- Store both firm-value-based and operating-income-based outputs

### Required columns

```text
SIC
Industry
Duration
Cyclicality
Inflation
Currency
```

The sheet contains two blocks:

```text
Using firm value
Using operating income
```

The parser must map both.

---

## 6.3 `TopDownMacroSensitivityService`

### Responsibilities

- Fetch company historical operating income, market cap, and total debt
- Fetch matching macro data
- Compute percentage changes
- Run regressions
- Calculate duration, cyclicality, inflation sensitivity, and currency sensitivity
- Assign confidence score
- Generate warnings

### Minimum observation rule

```text
If observations < 8 annual periods or < 12 quarterly periods:
    confidence = low
    use bottom-up as default
```

The source spreadsheet says that if a firm has been listed for 3 years or less, skip the top-down spreadsheet. The app should follow this principle.

---

## 6.4 `BottomUpMacroSensitivityService`

### Responsibilities

- Map company segments to SIC or industry benchmarks
- Estimate segment weights
- Compute weighted macro sensitivities
- Use this as fallback when top-down regression is noisy

### Segment mapping hierarchy

```text
1. User-provided SIC code
2. Company filing segment description
3. Industry classification
4. Manual mapping by user
5. LLM-suggested mapping requiring user confirmation
```

The LLM can suggest mappings, but the final mapping should be visible and editable.

---

## 6.5 `MacroScenarioTranslationService`

### Responsibilities

Translate macro shocks into DCF assumption changes.

Example inputs:

```json
{
  "rateShock": 0.01,
  "gdpShock": -0.02,
  "inflationShock": 0.015,
  "currencyShock": 0.05
}
```

Example outputs:

```json
{
  "estimatedValueImpactPct": -0.08,
  "operatingIncomeImpactPct": -0.04,
  "affectedAssumptions": [
    "risk_free_rate",
    "revenue_growth",
    "operating_margin",
    "terminal_value",
    "currency_translation"
  ]
}
```

---

# 7. API design

## 7.1 Get macro data

```http
GET /api/valuation/macro/data?frequency=annual&start=2015&end=2025
```

---

## 7.2 Get sector macro benchmark

```http
GET /api/valuation/macro/sector?sic=5311
```

---

## 7.3 Run top-down macro sensitivity

```http
POST /api/valuation/macro/top-down
```

### Request

```json
{
  "companyId": "uuid",
  "valuationId": "uuid",
  "frequency": "annual",
  "periods": [
    {
      "period": "2025",
      "operatingIncome": 27801,
      "marketCap": 231814,
      "totalDebt": 54136
    }
  ]
}
```

### Response

```json
{
  "method": "top_down",
  "observationCount": 11,
  "firmValue": {
    "duration": 0,
    "cyclicality": -1.81,
    "inflationSensitivity": -0.56,
    "currencySensitivity": 0.54
  },
  "operatingIncome": {
    "duration": 1.78,
    "cyclicality": 0.20,
    "inflationSensitivity": 0.30,
    "currencySensitivity": -0.06
  },
  "confidenceLabel": "medium",
  "warnings": [
    "Regression output should be interpreted with caution because sample size is limited."
  ]
}
```

---

## 7.4 Run bottom-up macro sensitivity

```http
POST /api/valuation/macro/bottom-up
```

### Request

```json
{
  "companyId": "uuid",
  "valuationId": "uuid",
  "segments": [
    {
      "name": "Retail",
      "sicCode": 5311,
      "value": 100
    }
  ]
}
```

### Response

```json
{
  "method": "bottom_up",
  "duration": 3.01,
  "cyclicality": -0.30,
  "inflationSensitivity": 1.91,
  "currencySensitivity": 0.69,
  "segmentExposures": [
    {
      "name": "Retail",
      "sicCode": 5311,
      "weight": 1,
      "duration": 3.01,
      "cyclicality": -0.30,
      "inflationSensitivity": 1.91,
      "currencySensitivity": 0.69
    }
  ]
}
```

---

## 7.5 Run macro scenario

```http
POST /api/valuation/macro/scenario
```

### Request

```json
{
  "valuationId": "uuid",
  "method": "bottom_up",
  "rateShock": 0.01,
  "gdpShock": -0.02,
  "inflationShock": 0.015,
  "currencyShock": 0.05
}
```

---

# 8. Frontend requirements

## 8.1 Macro sensitivity summary card

Display:

```text
Rate sensitivity: Low / Medium / High
Cyclicality: Defensive / Moderate / Highly cyclical
Inflation exposure: Helped / Hurt / Neutral / Unclear
Currency exposure: Helped / Hurt / Neutral / Direction needs review
```

---

## 8.2 Top-down regression view

Show:

| Metric | Firm value based | Operating income based |
|---|---:|---:|
| Duration | 0.0 | 1.8 |
| Cyclicality | -1.8 | 0.2 |
| Inflation sensitivity | -0.6 | 0.3 |
| Currency sensitivity | 0.5 | -0.1 |

Include:

```text
Observation count
Frequency
R-squared
Outlier warning
Regression confidence
```

---

## 8.3 Bottom-up exposure builder

User can add rows:

| Segment | SIC / Industry | Value | Weight | Duration | Cyclicality | Inflation | Currency |
|---|---|---:|---:|---:|---:|---:|---:|

The LLM may suggest SIC mapping, but user can override.

---

## 8.4 Macro scenario panel

User inputs:

```text
Interest rates +100 bps
GDP growth -2%
Inflation +150 bps
Currency +5%
```

The UI outputs:

```text
Estimated impact on operating income
Estimated impact on firm value
DCF assumptions affected
Scenario valuation impact
```

---

# 9. Integration with DCF engine

## 9.1 Risk-free rate

The macro module should feed the cost of capital engine:

```text
risk_free_rate = selected long-term government bond rate in valuation currency
```

But it should not automatically normalize the rate unless the user explicitly chooses normalized assumptions.

---

## 9.2 Scenario-based DCF

The macro module should create scenario variants:

| Scenario | Macro setup | DCF impact |
|---|---|---|
| Base | Current rates and growth | Current DCF |
| Rate shock | Higher risk-free rate | Higher WACC, lower terminal value |
| Recession | Lower GDP growth | Lower revenue growth, lower margins |
| Inflation shock | Higher CPI | Higher nominal revenue but margin pressure depending on pricing power |
| Currency shock | Stronger/weaker currency | Translation and cost impact |

---

## 9.3 Terminal value discipline

Macro assumptions should affect terminal value carefully.

Rules:

```text
Terminal growth cannot exceed long-term nominal growth without warning.
Nominal terminal growth should be consistent with inflation plus real growth.
If using real cash flows, use real discount rates.
If using nominal cash flows, use nominal discount rates.
```

---

## 9.4 Narrative-to-numbers integration

The macro module should help convert narratives into valuation assumptions.

Examples:

```text
Narrative: "Rates will stay higher for longer."
Numbers: higher risk-free rate, higher WACC, lower terminal value, possibly lower market multiple.

Narrative: "India infrastructure cycle will accelerate."
Numbers: higher revenue growth for cyclical/infrastructure companies, possibly higher reinvestment, cyclicality risk.

Narrative: "Inflation benefits this company because it has pricing power."
Numbers: stable or expanding margins under inflation scenario, but higher nominal discount rate.

Narrative: "Currency weakness helps exporters."
Numbers: revenue uplift or margin expansion if costs are domestic and sales are foreign.
```

---

# 10. Agent behavior rules

## 10.1 Always distinguish macro fact from valuation judgment

The agent may say:

```text
Rates rose by X.
```

But the valuation judgment is:

```text
Given the company's duration and reinvestment profile, higher rates likely pressure value through WACC and terminal value.
```

---

## 10.2 Do not overfit regression outputs

The spreadsheet itself warns that these regressions can be distorted by few observations and outliers. The agent should say:

```text
This is a directional sensitivity estimate, not a precise forecast.
```

---

## 10.3 Prefer bottom-up when history is weak

If a company has limited trading history, major restructuring, or less than 3 years of data:

```text
Use bottom-up sector sensitivity instead of top-down regression.
```

---

## 10.4 Watch sign conventions

Currency sensitivity must be explained based on the currency series.

The app should show:

```text
Currency variable used:
Direction:
Interpretation:
```

Do not let the agent say "currency helps" or "currency hurts" without this.

---

## 10.5 Link macro to assumptions, not just commentary

Every macro event should map to affected DCF assumptions:

```text
revenue growth
operating margin
tax rate
reinvestment
WACC
terminal growth
terminal value
scenario probability
```

---

# 11. Diagnostics and warnings

## 11.1 Regression warning

```text
Top-down macro sensitivity is based on limited historical observations. Treat it as directional unless the relationship is economically intuitive and statistically stable.
```

## 11.2 Outlier warning

```text
One or more periods show extreme firm value or operating income changes. Regression output may be dominated by outliers.
```

## 11.3 Business mix warning

```text
Historical macro sensitivity may not reflect the current business if the company has changed segment mix, leverage, or geographic exposure.
```

## 11.4 Currency warning

```text
Currency sensitivity depends on the exchange-rate convention used. Confirm whether the variable represents domestic currency depreciation, dollar strength, or another exchange rate.
```

## 11.5 Real vs nominal warning

```text
Do not mix real cash flows with nominal discount rates, or nominal cash flows with real discount rates.
```

---

# 12. Implementation checklist for Codex/Gemini

## Phase 1: Macro data ingestion

- [ ] Parse `macro.xlsx`
- [ ] Parse `macrodur.xlsx`
- [ ] Store annual macro time series
- [ ] Store quarterly macro time series
- [ ] Normalize period labels
- [ ] Preserve source file and data date

## Phase 2: Sector sensitivity ingestion

- [ ] Parse `Sector Averages by SIC`
- [ ] Store firm-value-based duration/cyclicality/inflation/currency sensitivities
- [ ] Store operating-income-based duration/cyclicality/inflation/currency sensitivities
- [ ] Add SIC lookup support

## Phase 3: Top-down calculator

- [ ] Add company historical input model
- [ ] Compute firm value
- [ ] Compute changes in OI and firm value
- [ ] Match macro periods
- [ ] Run regressions
- [ ] Calculate duration as max(0, -rate slope)
- [ ] Store confidence and warnings

## Phase 4: Bottom-up calculator

- [ ] Build segment exposure input UI
- [ ] Map SIC codes to sector benchmarks
- [ ] Compute weighted macro sensitivity
- [ ] Allow user overrides

## Phase 5: Scenario engine

- [ ] Add macro shock inputs
- [ ] Translate macro shocks into assumption impacts
- [ ] Generate scenario valuation deltas
- [ ] Add macro scenario charts

## Phase 6: Agent layer

- [ ] Explain macro sensitivity in plain English
- [ ] Link macro changes to DCF assumptions
- [ ] Flag overfitting and sign-convention issues
- [ ] Generate macro-risk section in valuation memo

---

# 13. Minimal Codex prompt

```text
Build the valuation agent's macro sensitivity module using the Batch 05 specification.

Implement ingestion for macro.xlsx and macrodur.xlsx. Store annual and quarterly macro time series, sector macro sensitivity benchmarks by SIC, and company macro input histories. Add services for top-down regression-based duration/cyclicality/inflation/currency sensitivity, bottom-up segment-weighted macro sensitivity, and macro scenario translation into DCF assumption impacts.

The backend must perform deterministic calculations and regressions. The LLM should only explain results, suggest segment mappings, flag noisy regressions, and connect macro changes to valuation assumptions. Do not let the LLM directly compute valuation outputs.
```

---

# 14. Bottom line

This batch gives the valuation agent a macro brain.

The key implementation principle is:

> Macro should not be generic commentary. It should flow into valuation assumptions, scenario probabilities, and risk diagnostics.

