# Valuation Agent Batch 04: Equity Cash Flow, Dividends, Buybacks, and FCFE

## Source files analyzed

- `divfundIndia.xlsx`
- `divfcfeIndia.xlsx`

## Purpose of this batch

This batch should become the valuation agent's **equity cash-flow and payout discipline layer**.

The earlier batches cover:
- relative pricing benchmarks
- DCF operating assumptions
- accounting normalization and intangibles

This batch adds the missing equity-owner question:

> After taxes, reinvestment, and financing choices, how much cash can actually be returned to shareholders, and is the company returning too much, too little, or the wrong kind of cash?

This matters because a Damodaran-style valuation agent should not treat dividends as a decorative output. Payout behavior gives information about:

- maturity of the business
- reinvestment opportunities
- cash-flow quality
- capital allocation discipline
- financing dependence
- dividend sustainability
- buyback quality
- dilution risk
- whether an FCFE valuation is more appropriate than FCFF

---

# 1. What each spreadsheet contributes

## 1.1 `divfundIndia.xlsx`

### Workbook structure

| Sheet | Role |
|---|---|
| `Variables & FAQ` | Defines dividend policy variables and why each variable matters |
| `Industry Averages` | India industry-level dividend payout, yield, market cap, ROE, institutional holding, and equity volatility |

### Key variables

| Variable | Meaning | Agent use |
|---|---|---|
| Number of firms | Count of firms in industry grouping | Benchmark quality confidence |
| Total Dividends | Aggregate dividends paid by the industry | Industry cash-return scale |
| Special Dividends as % of Total Dividends | One-off dividends as a share of total dividends | Detect non-recurring payout |
| Dividend Payout | Total dividends / net income | Core payout ratio |
| Dividend Yield | Total dividends / market capitalization | Cash yield to equity investors |
| Market Cap | Aggregate industry equity market value | Scale and weighting |
| ROE | Net income / book equity | Rough shareholder project-quality proxy |
| Institutional Holding | Institutional ownership share | Possible dividend preference and governance proxy |
| Standard Deviation of Equity | Annualized stock return volatility | Risk proxy, expected to correlate with lower payout |

### What this file teaches the agent

The agent should understand that dividend policy is not independent of fundamentals. Higher payout generally makes more sense when:

- growth opportunities are limited
- reinvestment needs are low
- business risk is lower
- cash flows are stable
- ROE is not meaningfully above cost of equity
- institutional ownership or investor clientele favors payout

Lower payout generally makes more sense when:

- the company has high-return reinvestment opportunities
- the company is young or volatile
- operating cash flow is still scaling
- leverage is high
- dividends would have to be funded by debt or equity issuance

---

## 1.2 `divfcfeIndia.xlsx`

### Workbook structure

| Sheet | Role |
|---|---|
| `Variables & FAQ` | Defines dividends, buybacks, issuances, and FCFE variants |
| `Industry Averages` | India industry-level cash returned to shareholders versus FCFE |

### Key variables

| Variable | Meaning | Agent use |
|---|---|---|
| Dividends | Aggregate dividends paid | Traditional cash return |
| Net Income | Aggregate accounting earnings | Denominator for payout |
| Payout | Dividends / net income | Conventional payout |
| Dividends + Buybacks | Broader shareholder return | Captures repurchases |
| Cash Return as % of Net Income | Dividends plus buybacks / net income | Total cash-return ratio |
| Dividends + Buybacks - Stock Issuances | Net cash returned after equity issuance | Best shareholder-level cash-return measure |
| FCFE before debt cash flows | Net income + depreciation - capex, using aggregate industry data | Owner-earnings style cash flow before debt financing |
| FCFE after debt cash flows | FCFE before debt cash flows + new debt - debt repaid | Full FCFE including debt financing |
| Net Cash Returned / FCFE pre-debt | Net cash returned relative to owner earnings | Payout sustainability before financing |
| Net Cash Returned / FCFE post-debt | Net cash returned relative to FCFE after debt cash flows | Payout sustainability after financing |

### What this file teaches the agent

The valuation agent should separate four concepts that many investors mix together:

1. **Earnings payout**
   - Dividends / net income
   - Easy but incomplete

2. **Gross cash return**
   - Dividends + buybacks
   - Better, but can be misleading if the company also issues shares

3. **Net cash return**
   - Dividends + buybacks - stock issuances
   - Best measure of actual cash returned to shareholders

4. **Payout against FCFE**
   - Net cash returned / FCFE
   - Best measure of sustainability

A company can look shareholder-friendly because it buys back stock, while actually diluting shareholders through stock issuance or stock-based compensation. The agent should catch this.

---

# 2. Core product role inside the valuation agent

This batch should create 4 product capabilities.

## 2.1 Dividend sustainability check

The agent should answer:

> Is the current dividend sustainable from FCFE?

It should compare:

```text
Dividend payout vs industry
Dividend yield vs industry
Dividend + buyback payout vs industry
Net cash returned vs FCFE
FCFE trend
Leverage trend
Cash balance
Debt maturity pressure
```

### Output labels

| Label | Meaning |
|---|---|
| Sustainable | Dividends are comfortably covered by FCFE and leverage is stable |
| Stretching | Dividends are covered only narrowly or depend on debt/cash drawdown |
| Unsustainable | Dividends exceed sustainable FCFE or require persistent financing |
| Not meaningful | Earnings or FCFE are negative, making the ratio misleading |

---

## 2.2 Buyback quality analysis

The agent should not treat all buybacks as good.

### Good buybacks

Buybacks are higher quality when:

- shares are undervalued relative to intrinsic value
- buybacks are funded from genuine excess FCFE
- buybacks exceed stock issuance meaningfully
- debt does not rise only to fund repurchases
- business reinvestment is not being starved

### Bad buybacks

Buybacks are lower quality when:

- the company is overvalued
- buybacks mainly offset employee stock compensation
- net share count does not fall
- debt rises materially
- the company is underinvesting in the business
- management is buying back shares while margins, ROIC, or revenue quality deteriorate

### Required agent statement

Every buyback analysis should state:

```text
Gross buybacks are not the same as value creation. The relevant measure is net cash returned after stock issuance, and whether shares were bought below intrinsic value.
```

---

## 2.3 FCFE valuation support

This batch should let the agent decide whether to run an FCFE valuation instead of or alongside FCFF.

### FCFE works best when

- the company has stable leverage
- debt policy is predictable
- the user specifically wants equity cash-flow value
- the company is mature and shareholder payout is central to the thesis
- financial leverage is part of the business model but not wildly changing

### FCFF is safer when

- capital structure is changing
- leverage is high or unstable
- company is distressed
- debt issuance/repayment is lumpy
- the company is young or reinvestment-heavy
- user wants enterprise value first

### Agent rule

```text
Default to FCFF for operating companies.
Use FCFE as a cross-check or primary model only when leverage policy is stable and equity cash flows are meaningful.
```

---

## 2.4 Capital allocation diagnostic

The agent should connect payout to reinvestment quality.

### Core logic

```text
If ROC > WACC and growth opportunities exist:
    high payout may destroy value by starving reinvestment.

If ROC <= WACC and growth opportunities are weak:
    higher payout may create value by preventing bad reinvestment.

If dividends exceed FCFE:
    payout is being funded by debt, cash depletion, or equity issuance.

If buybacks happen above intrinsic value:
    buybacks destroy value even if EPS rises.
```

---

# 3. Formulas the agent should implement

## 3.1 Dividend payout ratio

```text
Dividend Payout = Total Dividends / Net Income
```

### Warnings

```text
If Net Income <= 0:
    Dividend payout is not meaningful.
```

---

## 3.2 Dividend yield

```text
Dividend Yield = Total Dividends / Market Capitalization
```

### Warnings

```text
High dividend yield may signal value, distress, or a pending dividend cut.
Do not classify high yield as attractive without checking FCFE coverage.
```

---

## 3.3 Gross cash return ratio

```text
Gross Cash Return = Dividends + Buybacks

Gross Cash Return Ratio = (Dividends + Buybacks) / Net Income
```

---

## 3.4 Net cash returned

```text
Net Cash Returned = Dividends + Buybacks - Stock Issuances
```

This is more useful than gross buybacks.

---

## 3.5 FCFE before debt cash flows

Spreadsheet approximation:

```text
FCFE Before Debt Cash Flows =
Net Income + Depreciation - Capital Expenditures
```

The app should support the fuller Damodaran-style version:

```text
FCFE Before Debt Cash Flows =
Net Income
- (Capital Expenditures - Depreciation)
- Change in Non-Cash Working Capital
```

### Important implementation note

The Damodaran industry spreadsheet uses an aggregate simplified version. The app should store both:

```text
fcfe_pre_debt_spreadsheet_version
fcfe_pre_debt_full_version
```

The full company-level model should use the full version when working-capital data exists.

---

## 3.6 FCFE after debt cash flows

```text
FCFE After Debt Cash Flows =
FCFE Before Debt Cash Flows
+ New Debt Issued
- Debt Repaid
```

or:

```text
FCFE After Debt Cash Flows =
Net Income
- Net Reinvestment
+ Net Debt Issued
```

---

## 3.7 Net cash return to FCFE

```text
Net Cash Returned / FCFE Pre-Debt =
(Dividends + Buybacks - Stock Issuances) / FCFE Before Debt Cash Flows

Net Cash Returned / FCFE Post-Debt =
(Dividends + Buybacks - Stock Issuances) / FCFE After Debt Cash Flows
```

### Interpretation

| Ratio | Interpretation |
|---|---|
| < 0 | Company may be issuing more equity than it returns, or FCFE is negative |
| 0% to 50% | Conservative payout |
| 50% to 100% | Moderate to high payout |
| > 100% | Returning more than sustainable FCFE |
| Negative FCFE | Ratio often not meaningful; use dollar values and financing context |

---

# 4. Data model

## 4.1 `industry_dividend_policy_benchmarks`

```sql
CREATE TABLE industry_dividend_policy_benchmarks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    country TEXT NOT NULL,
    region TEXT,
    data_date DATE,
    industry_name TEXT NOT NULL,

    number_of_firms INTEGER,
    total_dividends_usd_millions NUMERIC,
    special_dividends_pct_total NUMERIC,
    dividend_payout_ratio NUMERIC,
    dividend_yield NUMERIC,
    market_cap_usd_millions NUMERIC,
    roe NUMERIC,
    institutional_holdings NUMERIC,
    equity_standard_deviation NUMERIC,

    source_file TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT now(),

    UNIQUE(country, data_date, industry_name, source_file)
);
```

---

## 4.2 `industry_fcfe_payout_benchmarks`

```sql
CREATE TABLE industry_fcfe_payout_benchmarks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    country TEXT NOT NULL,
    region TEXT,
    data_date DATE,
    industry_name TEXT NOT NULL,

    number_of_firms INTEGER,
    dividends_usd_millions NUMERIC,
    net_income_usd_millions NUMERIC,
    dividend_payout_ratio NUMERIC,
    dividends_plus_buybacks_usd_millions NUMERIC,
    cash_return_pct_net_income NUMERIC,
    net_cash_returned_usd_millions NUMERIC,
    fcfe_before_debt_usd_millions NUMERIC,
    fcfe_after_debt_usd_millions NUMERIC,
    net_cash_returned_to_fcfe_pre_debt NUMERIC,
    net_cash_returned_to_fcfe_post_debt NUMERIC,

    source_file TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT now(),

    UNIQUE(country, data_date, industry_name, source_file)
);
```

---

## 4.3 `company_cash_return_history`

```sql
CREATE TABLE company_cash_return_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    company_id UUID NOT NULL REFERENCES companies(id),
    fiscal_period TEXT NOT NULL,
    fiscal_year INTEGER,
    currency TEXT,

    net_income NUMERIC,
    dividends_paid NUMERIC,
    share_buybacks NUMERIC,
    stock_issuances NUMERIC,
    depreciation_amortization NUMERIC,
    capital_expenditures NUMERIC,
    change_non_cash_working_capital NUMERIC,
    new_debt_issued NUMERIC,
    debt_repaid NUMERIC,

    fcfe_before_debt NUMERIC,
    fcfe_after_debt NUMERIC,
    gross_cash_return NUMERIC,
    net_cash_returned NUMERIC,
    dividend_payout_ratio NUMERIC,
    gross_cash_return_ratio NUMERIC,
    net_cash_return_to_fcfe_pre_debt NUMERIC,
    net_cash_return_to_fcfe_post_debt NUMERIC,

    source_document_id UUID,
    created_at TIMESTAMP DEFAULT now()
);
```

---

## 4.4 `payout_diagnostics`

```sql
CREATE TABLE payout_diagnostics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    valuation_id UUID NOT NULL REFERENCES valuations(id),
    company_id UUID NOT NULL REFERENCES companies(id),

    dividend_sustainability_label TEXT,
    buyback_quality_label TEXT,
    payout_policy_label TEXT,

    dividend_coverage_comment TEXT,
    buyback_quality_comment TEXT,
    dilution_comment TEXT,
    financing_dependency_comment TEXT,
    reinvestment_tradeoff_comment TEXT,

    red_flags JSONB,
    created_at TIMESTAMP DEFAULT now()
);
```

---

# 5. Backend services

## 5.1 `DividendBenchmarkIngestionService`

### Responsibilities

- Parse `divfundIndia.xlsx`
- Extract `Industry Averages`
- Normalize headers
- Convert percent-like decimals into decimal ratios
- Preserve `NA` values as null
- Save to `industry_dividend_policy_benchmarks`

### Required normalization

```text
"Number of firms" -> number_of_firms
"Total Dividends (US $ millions)" -> total_dividends_usd_millions
"Special Dividends as % of Total Dividends" -> special_dividends_pct_total
"Dividend Payout" -> dividend_payout_ratio
"Dividend Yield" -> dividend_yield
"Market Cap (US $ millions)" -> market_cap_usd_millions
"ROE" -> roe
"Institutional Holdings" -> institutional_holdings
"Std Dev in Stock Prices" -> equity_standard_deviation
```

---

## 5.2 `FCFEBenchmarkIngestionService`

### Responsibilities

- Parse `divfcfeIndia.xlsx`
- Extract `Industry Averages`
- Normalize FCFE payout variables
- Save to `industry_fcfe_payout_benchmarks`

### Required normalization

```text
"Industry name" -> industry_name
"Dividends" -> dividends_usd_millions
"Net Income" -> net_income_usd_millions
"Payout" -> dividend_payout_ratio
"Dividends + Buybacks" -> dividends_plus_buybacks_usd_millions
"Cash Return as % of Net Income" -> cash_return_pct_net_income
"Dividends + Buybacks - Stock Issuances" -> net_cash_returned_usd_millions
"FCFE (before debt cash flows)" -> fcfe_before_debt_usd_millions
"FCFE (after debt cash flows)" -> fcfe_after_debt_usd_millions
"Net Cash Returned/FCFE (pre-debt)" -> net_cash_returned_to_fcfe_pre_debt
"Net Cash Returned/FCFE (post-debt)" -> net_cash_returned_to_fcfe_post_debt
```

---

## 5.3 `CompanyCashReturnService`

### Responsibilities

Given company financials, compute:

```text
dividend payout
gross cash return
net cash returned
FCFE before debt
FCFE after debt
cash returned to FCFE
share count change
dividend sustainability
buyback quality
```

### Inputs

```ts
type CompanyCashReturnInput = {
  netIncome: number | null
  dividendsPaid: number | null
  shareBuybacks: number | null
  stockIssuances: number | null
  depreciationAmortization: number | null
  capitalExpenditures: number | null
  changeNonCashWorkingCapital: number | null
  newDebtIssued: number | null
  debtRepaid: number | null
  marketCap: number | null
  shareCountBeginning?: number | null
  shareCountEnding?: number | null
  intrinsicValuePerShare?: number | null
  currentPrice?: number | null
}
```

### Outputs

```ts
type CompanyCashReturnOutput = {
  dividendPayoutRatio: number | null
  dividendYield: number | null
  grossCashReturn: number | null
  netCashReturned: number | null
  fcfeBeforeDebt: number | null
  fcfeAfterDebt: number | null
  netCashReturnedToFcfePreDebt: number | null
  netCashReturnedToFcfePostDebt: number | null
  shareCountChangePct: number | null

  dividendSustainabilityLabel: "sustainable" | "stretching" | "unsustainable" | "not_meaningful"
  buybackQualityLabel: "value_creating" | "neutral" | "value_destroying" | "insufficient_data"
  payoutPolicyLabel: "under_distributing" | "balanced" | "over_distributing" | "not_meaningful"

  diagnostics: string[]
  redFlags: string[]
}
```

---

## 5.4 `PayoutPolicyDiagnosticService`

### Diagnostic rules

#### Rule 1: Dividend paid despite negative earnings

```text
If net_income <= 0 and dividends_paid > 0:
    Flag: "Company is paying dividends despite negative net income."
```

#### Rule 2: Dividend exceeds FCFE

```text
If dividends_paid > fcfe_before_debt:
    Flag: "Dividend exceeds FCFE before debt cash flows. Check whether payout is funded by debt, cash drawdown, or asset sales."
```

#### Rule 3: Net cash return exceeds FCFE

```text
If net_cash_returned / fcfe_before_debt > 1:
    Flag: "Net cash returned exceeds FCFE before debt cash flows."
```

#### Rule 4: Buybacks offset by issuance

```text
If share_buybacks > 0 and stock_issuances / share_buybacks > 0.5:
    Flag: "A material share of buybacks is offset by stock issuance."
```

#### Rule 5: Buybacks above intrinsic value

```text
If current_price > intrinsic_value_per_share and share_buybacks > 0:
    Flag: "Buybacks appear to have occurred while the stock was above estimated intrinsic value."
```

#### Rule 6: High payout while excess returns are high

```text
If payout_ratio > industry_median and ROC > WACC by a meaningful margin:
    Flag: "High payout may be starving value-creating reinvestment."
```

#### Rule 7: Low payout while excess returns are poor

```text
If payout_ratio < industry_median and ROC <= WACC:
    Flag: "Low payout may indicate retained cash is being reinvested at weak returns."
```

---

# 6. API design

## 6.1 Get industry payout benchmarks

```http
GET /api/valuation/benchmarks/payout?country=India&industry=Auto%20Parts
```

### Response

```json
{
  "country": "India",
  "industry": "Auto Parts",
  "dividendPolicy": {
    "numberOfFirms": 120,
    "dividendPayoutRatio": 0.2813,
    "dividendYield": 0.0069,
    "roe": 0.1389,
    "institutionalHoldings": 0.1284,
    "equityStandardDeviation": 0.3934
  },
  "fcfePolicy": {
    "dividends": 774.666,
    "netIncome": 2753.367,
    "dividendsPlusBuybacks": 774.779,
    "netCashReturned": -529.674,
    "fcfeBeforeDebt": 1452.325,
    "fcfeAfterDebt": 598.412,
    "netCashReturnedToFcfePreDebt": -0.3647,
    "netCashReturnedToFcfePostDebt": -0.8851
  }
}
```

---

## 6.2 Analyze company payout policy

```http
POST /api/valuation/payout/analyze
```

### Request

```json
{
  "companyId": "uuid",
  "valuationId": "uuid",
  "industry": "Auto Parts",
  "country": "India",
  "financials": {
    "netIncome": 1000,
    "dividendsPaid": 150,
    "shareBuybacks": 100,
    "stockIssuances": 40,
    "depreciationAmortization": 300,
    "capitalExpenditures": 500,
    "changeNonCashWorkingCapital": 50,
    "newDebtIssued": 200,
    "debtRepaid": 100,
    "marketCap": 12000
  },
  "valuationContext": {
    "currentPrice": 100,
    "intrinsicValuePerShare": 125,
    "roc": 0.18,
    "wacc": 0.11
  }
}
```

### Response

```json
{
  "fcfeBeforeDebt": 750,
  "fcfeAfterDebt": 850,
  "grossCashReturn": 250,
  "netCashReturned": 210,
  "dividendPayoutRatio": 0.15,
  "netCashReturnedToFcfePreDebt": 0.28,
  "netCashReturnedToFcfePostDebt": 0.247,
  "dividendSustainabilityLabel": "sustainable",
  "buybackQualityLabel": "value_creating",
  "payoutPolicyLabel": "balanced",
  "redFlags": [],
  "diagnostics": [
    "Dividends are covered by FCFE before debt cash flows.",
    "Buybacks are not fully offset by stock issuances.",
    "Current price is below estimated intrinsic value, so buybacks may be value accretive."
  ]
}
```

---

# 7. Frontend requirements

## 7.1 Payout diagnostics card

Display:

```text
Dividend Sustainability: Sustainable / Stretching / Unsustainable
Buyback Quality: Value Creating / Neutral / Value Destroying
Payout Policy: Under-distributing / Balanced / Over-distributing
```

Add explanation text under each label.

---

## 7.2 Cash return waterfall

Show:

```text
Net income
+ Depreciation & amortization
- Capital expenditures
- Change in non-cash working capital
= FCFE before debt

+ New debt issued
- Debt repaid
= FCFE after debt

Dividends
+ Buybacks
- Stock issuances
= Net cash returned
```

This should be visible in both quick and advanced modes, but editable only in advanced mode.

---

## 7.3 Industry comparison table

| Metric | Company | Industry median / average | Interpretation |
|---|---:|---:|---|
| Dividend payout | 15% | 28% | Below industry |
| Dividend yield | 1.2% | 0.7% | Above industry |
| Net cash returned / FCFE | 28% | -36% | Stronger than industry |
| ROE | 18% | 14% | Better than industry |
| Equity volatility | 32% | 39% | Lower risk |

---

## 7.4 Buyback quality panel

Required fields:

```text
Gross buybacks
Stock issuances
Net buybacks
Share count change
Estimated value per share
Average repurchase price, if available
Buyback verdict
```

### Agent explanation example

```text
The company returned cash through buybacks, but this does not automatically mean buybacks created value. The key checks are whether share count fell, whether stock issuance offset the repurchases, and whether the shares were repurchased below intrinsic value.
```

---

# 8. Agent behavior rules

## 8.1 Do not over-trust payout ratios

The agent must not say:

```text
"The payout ratio is low, so the company is attractive."
```

Instead:

```text
"The payout ratio is low. This can be good if the company has high-return reinvestment opportunities, but bad if management is retaining cash and reinvesting at weak returns."
```

---

## 8.2 Do not treat dividends and buybacks the same

Dividends are generally sticky and recurring. Buybacks are more discretionary and can be value creating or value destroying depending on price paid.

The agent should say:

```text
Dividends are a commitment. Buybacks are a capital allocation choice.
```

---

## 8.3 Always distinguish gross and net buybacks

The agent should always check stock issuance.

```text
Buybacks should be assessed net of stock issuance. A company can report large repurchases while still failing to reduce share count.
```

---

## 8.4 Do not use FCFE when debt policy is unstable without warning

If debt issuance or repayment is volatile, the agent should say:

```text
FCFE after debt cash flows is noisy because debt policy is changing. FCFF is likely the cleaner primary valuation method.
```

---

## 8.5 Tie payout policy to the valuation narrative

Examples:

| Narrative | Payout implication |
|---|---|
| Mature compounder | Moderate payout plus disciplined reinvestment |
| High-growth company | Low payout is normal |
| Declining business | High payout may be rational if reinvestment opportunities are poor |
| Levered cyclical | High payout is dangerous |
| Cash-rich no-growth firm | Low payout may indicate poor capital allocation |

---

# 9. Integration with DCF engine

## 9.1 FCFF to equity bridge

Even when the core valuation uses FCFF, the agent should still compute owner cash flow.

```text
Value of operating assets
+ Cash and non-operating assets
- Debt
- Minority interests
- Option claims
= Equity value
```

Then payout analysis should answer:

```text
Does this company actually return cash to equity owners?
```

---

## 9.2 FCFE cross-check valuation

Formula:

```text
Equity Value =
PV(FCFE during explicit forecast period)
+ PV(Terminal Equity Value)
+ Cash not already captured
```

Terminal value:

```text
Terminal Equity Value =
FCFE_n+1 / (Cost of Equity - Stable Growth Rate)
```

### Consistency rules

```text
FCFE must be discounted at cost of equity.
FCFF must be discounted at WACC.
Do not mix equity cash flows with WACC.
Do not mix firm cash flows with cost of equity.
```

---

## 9.3 Dividend discount model fallback

Use only when:

```text
dividends are stable
payout policy is mature
dividends approximate FCFE
company is financial or regulated
```

Do not use DDM as the default for ordinary non-financial companies.

---

# 10. Implementation checklist for Codex/Gemini

## Phase 1: Ingest benchmarks

- [ ] Add parser for `divfundIndia.xlsx`
- [ ] Add parser for `divfcfeIndia.xlsx`
- [ ] Store industry dividend benchmarks
- [ ] Store industry FCFE payout benchmarks
- [ ] Preserve source file and data date
- [ ] Treat `NA` as null

## Phase 2: Company-level calculations

- [ ] Compute dividend payout
- [ ] Compute dividend yield
- [ ] Compute gross cash return
- [ ] Compute net cash returned
- [ ] Compute FCFE before debt
- [ ] Compute FCFE after debt
- [ ] Compute cash returned / FCFE ratios

## Phase 3: Diagnostics

- [ ] Add dividend sustainability label
- [ ] Add buyback quality label
- [ ] Add payout policy label
- [ ] Add red flags for over-distribution
- [ ] Add red flags for stock issuance offsetting buybacks
- [ ] Add warnings for negative FCFE or negative net income

## Phase 4: UI

- [ ] Add payout diagnostics card
- [ ] Add cash return waterfall
- [ ] Add industry comparison table
- [ ] Add buyback quality panel
- [ ] Add toggle for reported vs adjusted FCFE

## Phase 5: Agent layer

- [ ] Teach agent to distinguish dividends, buybacks, and net cash returned
- [ ] Teach agent to connect payout to ROC vs WACC
- [ ] Teach agent to warn when FCFE valuation is unreliable
- [ ] Add memo section: `Capital Allocation and Shareholder Returns`

---

# 11. Minimal Codex prompt

```text
Build the valuation agent's payout and FCFE module using the Batch 04 specification.

Implement ingestion for divfundIndia.xlsx and divfcfeIndia.xlsx, normalize industry benchmark data, create database tables for dividend policy and FCFE payout benchmarks, and build company-level payout calculations.

The module must calculate dividend payout, dividend yield, gross cash returned, net cash returned, FCFE before debt, FCFE after debt, and net cash returned relative to FCFE. Add diagnostics for dividend sustainability, buyback quality, stock issuance offset, over-distribution, and suitability of FCFE valuation.

Do not let the LLM perform arithmetic directly. The backend should calculate all metrics deterministically. The LLM should only explain results, flag assumptions, and generate memo language.
```

---

# 12. Bottom line

This batch turns the valuation agent from a pure enterprise-value model into a true equity-owner analysis tool.

The key implementation principle is:

> Cash returned to shareholders should be judged against FCFE, not just net income, and buybacks should be analyzed net of stock issuance and price paid.

