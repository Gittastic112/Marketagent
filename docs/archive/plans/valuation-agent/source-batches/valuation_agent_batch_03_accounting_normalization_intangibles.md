# Valuation Agent Batch 03: Accounting Normalization, R&D Capitalization, Goodwill, and Acquisition Quality

## Purpose of this batch

This batch turns Damodaran's India accounting-adjustment datasets into the valuation agent's **normalization layer**.

Batch 01 handled relative pricing benchmarks. Batch 02 handled the main DCF assumption engine: growth, margins, reinvestment, ROE/ROC, working capital, and financing behavior. Batch 03 is narrower but important: it teaches the valuation agent when **reported accounting numbers are not economically clean enough** for a Damodaran-style valuation.

The two big lessons are:

1. **R&D is often an investment, not merely an operating expense.**
2. **Goodwill is not an operating asset created by the business. It is an acquisition accounting residue that can reveal acquisition intensity, overpayment risk, and capital allocation quality.**

This batch should become the agent's **accounting clean-up and intangible-investment module**.

---

## Files included in Batch 03

| File | Dataset role | Core use in the agent |
|---|---|---|
| `R&DIndia.xls` / `R&DIndia.xlsx` | Industry R&D capitalization and R&D spending history | R&D capitalization, adjusted operating income, adjusted invested capital, adjusted ROC, innovation intensity diagnostics |
| `goodwillIndia.xls` / `goodwillIndia.xlsx` | Industry goodwill, goodwill change, and impairment | Acquisition intensity, goodwill burden, impairment risk, organic vs acquired growth diagnostics |

Both files follow the usual Damodaran structure:

```text
Sheet 1: Variables & FAQ
Sheet 2: Industry Averages
Rows 1 to 7: metadata and source links
Row 8: column headers
Rows below: Damodaran industry rows
```

Observed ranges:

| File | `Industry Averages` used range | Header row |
|---|---:|---:|
| `R&DIndia.xlsx` | `A1:L104` | Row 8 |
| `goodwillIndia.xlsx` | `A1:G104` | Row 8 |

Source metadata embedded in the files:

| Metadata field | Value observed |
|---|---|
| Created by | Aswath Damodaran |
| Home page | `http://www.damodaran.com` |
| Data website | `https://pages.stern.nyu.edu/~adamodar/New_Home_Page/data.html` |
| Companies in each industry | `https://pages.stern.nyu.edu/~adamodar/pc/datasets/indname.xls` |
| Variable definitions | `https://pages.stern.nyu.edu/~adamodar/New_Home_Page/datafile/variable.htm` |
| Region | India |
| Excel date serial observed | `46027`, corresponding to `2026-01-05` |

---

## Why this batch matters for the valuation agent

A basic DCF takes reported EBIT, reported invested capital, and reported margins at face value.

That is often wrong.

For technology, pharmaceuticals, biotech, software, healthcare products, aerospace, and other innovation-heavy businesses, reported EBIT can be understated because R&D is expensed immediately even when it creates benefits over multiple years.

For acquisitive companies, reported invested capital and balance sheet assets can be distorted by goodwill. Goodwill does not mean the company internally created value. It often means it paid for another company above the identifiable asset value. Goodwill impairments can also be evidence that management overpaid in the past.

So the valuation agent needs a normalization step between raw financial ingestion and forecast modeling:

```text
Raw financial statements
→ accounting normalization
→ adjusted operating metrics
→ DCF assumptions
→ valuation
```

Without this layer, the agent will produce weaker ROIC, margin, reinvestment, and growth analysis.

---

# Dataset-level observations from Batch 03

## India R&D dataset observations

The `R&DIndia` file covers **96 industry rows**, including total market rows.

For `Total Market (without financials)`, the file shows:

| Metric | Value |
|---|---:|
| Number of firms | 4,523 |
| Capitalized R&D estimate | $26,920.1m |
| Capitalized R&D as % of invested capital | 1.76% |
| R&D LTM | $8,842.9m |
| Current R&D as % of revenue | 0.52% |
| CAGR in R&D, last 5 years | -0.05% |

Top industries by current R&D as % of revenue:

| Industry | Firms | Current R&D / Revenue | R&D LTM |
| --- | --- | --- | --- |
| Drugs (Biotechnology) | 9 | 6.24% | $124.3m |
| Drugs (Pharmaceutical) | 188 | 4.21% | $2,009.6m |
| Aerospace/Defense | 23 | 3.44% | $331.3m |
| Auto & Truck | 19 | 3.33% | $3,784.5m |
| Utility (Water) | 1 | 2.15% | $8.6m |
| Software (System & Application) | 82 | 1.95% | $111.7m |
| Healthcare Products | 19 | 1.60% | $6.4m |
| Telecom. Equipment | 22 | 1.33% | $29.6m |

Top industries by capitalized R&D as % of invested capital:

| Industry | Firms | Capitalized R&D / Invested Capital | Capitalized R&D |
| --- | --- | --- | --- |
| Healthcare Products | 19 | 89.45% | $465.2m |
| Aerospace/Defense | 23 | 16.49% | $994.8m |
| Utility (Water) | 1 | 13.62% | $27.2m |
| Drugs (Pharmaceutical) | 188 | 11.99% | $5,877.6m |
| Drugs (Biotechnology) | 9 | 11.62% | $380.3m |
| Software (System & Application) | 82 | 10.88% | $348.0m |
| Auto & Truck | 19 | 9.48% | $11,607.1m |
| Furn/Home Furnishings | 52 | 3.36% | $142.2m |

Important interpretation:

```text
R&D is not equally important across sectors.
The accounting normalization should be automatic for R&D-heavy sectors, optional for low-R&D sectors, and disabled or ignored for financials unless specifically justified.
```

---

## India goodwill dataset observations

The `goodwillIndia` file covers **96 industry rows**, including total market rows.

For `Total Market (without financials)`, the file shows:

| Metric | Value |
|---|---:|
| Number of firms | 4,523 |
| Goodwill | $62,041.3m |
| Change in goodwill last year | $3,535.3m |
| Goodwill as % of total assets | 2.70% |
| Goodwill impairment LTM | $260.5m |
| Impairment as % of goodwill | 0.42% |

Top industries by goodwill as % of total assets:

| Industry | Firms | Goodwill / Total Assets | Goodwill |
| --- | --- | --- | --- |
| Information Services | 26 | 31.27% | $1,886.6m |
| Drugs (Biotechnology) | 9 | 26.83% | $1,965.5m |
| Precious Metals | 1 | 26.45% | $13.2m |
| Entertainment | 66 | 20.52% | $1,013.3m |
| Retail (Automotive) | 10 | 17.48% | $156.5m |
| Household Products | 43 | 16.80% | $2,714.8m |
| Heathcare Information and Technology | 25 | 14.43% | $1,140.9m |
| Retail (General) | 11 | 14.32% | $513.6m |

Top industries by impairment as % of goodwill:

| Industry | Firms | Impairment / Goodwill | Goodwill impairment LTM |
| --- | --- | --- | --- |
| Insurance (Life) | 9 | 20.64% | $0.2m |
| Chemical (Basic) | 152 | 13.69% | $62.4m |
| Business & Consumer Services | 75 | 11.21% | $48.9m |
| Transportation | 59 | 6.29% | $29.1m |
| Real Estate (Development) | 156 | 5.43% | $12.7m |
| Power | 33 | 3.05% | $11.9m |
| Auto & Truck | 19 | 1.88% | $8.9m |
| Furn/Home Furnishings | 52 | 1.42% | $8.1m |

Important interpretation:

```text
Goodwill is not a source of future cash flow by itself.
It is a signal about acquisition history, acquisition intensity, and possible capital allocation quality.
Goodwill impairment can be added back for normalized earnings when it is non-recurring, but it should still trigger a capital allocation warning.
```

---

# File-by-file learning

## 1. `R&DIndia.xls`: R&D capitalization and innovation investment

### Dataset purpose

`R&DIndia` estimates the value of capitalized R&D by industry using a **5-year straight-line amortization period**. The file aggregates current and historical R&D expenses across companies in each industry.

This dataset should improve the agent's ability to value companies where reported earnings understate economic earnings because R&D is treated as an expense instead of an investment.

### Key fields

| Field | Meaning | Agent use |
|---|---|---|
| `Industry Name` | Damodaran industry grouping | Industry matching |
| `Number of firms` | Sample size | Confidence score |
| `R&D Capitalized (my estimate in $ millions)` | Damodaran-style capitalized R&D asset estimate | Benchmark for R&D asset size |
| `Capitalized R&D as % of Invested Capital` | Capitalized R&D relative to adjusted capital base | Measures how material R&D capitalization is |
| `R&D - LTM` | Last twelve months R&D expense | Current innovation spend |
| `Current R&D as % of Revenue` | R&D intensity | Flag for R&D-heavy sectors |
| `R&D - 1 year ago` through `R&D - 5 years ago` | Historical R&D spending | Build capitalization schedule |
| `CAGR in R&D - Last 5 years` | Growth rate in R&D spending | Innovation investment trend |

### Exact R&D capitalization method inferred from the file

The file's capitalized R&D estimate is consistent with a 5-year straight-line amortization schedule:

```text
Capitalized R&D asset
= Current R&D
+ 80% × R&D from 1 year ago
+ 60% × R&D from 2 years ago
+ 40% × R&D from 3 years ago
+ 20% × R&D from 4 years ago
```

The R&D from 5 years ago is fully amortized and does not remain in the research asset.

Example from `Auto & Truck`:

```text
Capitalized R&D
= 3,784.492
+ 0.8 × 3,742.020
+ 0.6 × 3,862.988
+ 0.4 × 4,166.691
+ 0.2 × 4,222.795
= 11,607.136
```

This matches the file's capitalized R&D estimate for Auto & Truck.

### Required company-level R&D normalization logic

The agent should not directly apply the industry aggregate R&D asset to a company. It should use the industry file as a **benchmark** and use the company's own R&D history for the actual adjustment.

Required inputs:

| Input | Source |
|---|---|
| Current R&D expense | Company income statement |
| Prior 1 to 5 years of R&D expense | Company historical statements |
| Reported EBIT / operating income | Company income statement |
| Revenue | Company income statement |
| Invested capital | Balance sheet normalization engine |
| Book equity | Balance sheet |
| Tax rate | Valuation tax module |
| Amortization life | Default 5 years, user-editable by industry |

Default R&D capitalization formula:

```text
rd_asset =
current_rd
+ rd_t_minus_1 × 4/5
+ rd_t_minus_2 × 3/5
+ rd_t_minus_3 × 2/5
+ rd_t_minus_4 × 1/5
```

Default R&D amortization formula:

```text
rd_amortization =
(rd_t_minus_1 + rd_t_minus_2 + rd_t_minus_3 + rd_t_minus_4 + rd_t_minus_5) / 5
```

Adjusted operating income:

```text
adjusted_ebit = reported_ebit + current_rd - rd_amortization
```

Adjusted operating margin:

```text
adjusted_operating_margin = adjusted_ebit / revenue
```

Adjusted invested capital:

```text
adjusted_invested_capital = reported_invested_capital + rd_asset
```

Adjusted return on capital:

```text
adjusted_roc = adjusted_after_tax_operating_income / adjusted_invested_capital
```

Adjusted reinvestment for FCFF consistency:

```text
adjusted_reinvestment =
reported_net_capex
+ change_in_non_cash_working_capital
+ current_rd
- rd_amortization
```

Adjusted FCFF:

```text
adjusted_fcff = adjusted_ebit × (1 - tax_rate) - adjusted_reinvestment
```

Implementation warning:

```text
Do not let the R&D adjustment create fake value by increasing EBIT without also increasing reinvestment and invested capital.
```

The purpose of capitalizing R&D is not to magically improve free cash flow. It is to measure the business more accurately: operating income, margin, invested capital, and ROC become more meaningful.

---

## 2. `goodwillIndia.xls`: Goodwill, acquisition intensity, and impairment

### Dataset purpose

`goodwillIndia` measures industry-level goodwill, changes in goodwill, goodwill as a percent of total assets, goodwill impairment, and impairment as a percent of goodwill.

This dataset should improve the agent's ability to distinguish:

```text
Organic growth
versus
Acquisition-driven growth
```

and:

```text
Value-creating reinvestment
versus
Acquisition overpayment
```

### Key fields

| Field | Meaning | Agent use |
|---|---|---|
| `Industry Name` | Damodaran industry grouping | Industry matching |
| `Number of Firms` | Sample size | Confidence score |
| `Goodwill (in $ millions)` | Aggregate reported goodwill | Acquisition history intensity |
| `Change in Goodwill in last year` | Increase/decrease in goodwill | Recent acquisition activity |
| `Goodwill as % of Total Assets` | Goodwill burden on balance sheet | Acquisition-heavy business model warning |
| `Impairment of Goodwill in LTM in $ millions` | Recent write-downs | Evidence of past acquisition overpayment |
| `Impairment as % of Goodwill` | Impairment severity | Capital allocation quality warning |

### Required company-level goodwill logic

The agent should use company-specific goodwill data, not industry aggregate values, to run the core analysis.

Required inputs:

| Input | Source |
|---|---|
| Goodwill current period | Company balance sheet |
| Goodwill prior period | Company balance sheet |
| Total assets | Company balance sheet |
| Goodwill impairment | Income statement or notes |
| Acquisition spending | Cash flow statement |
| Revenue growth | Income statement |
| Segment/geographic growth, if available | Company filings |
| Invested capital | Normalization engine |
| Operating income | Income statement |

Goodwill metrics:

```text
goodwill_to_assets = goodwill / total_assets
```

```text
change_in_goodwill = goodwill_current - goodwill_prior
```

```text
goodwill_growth_rate = change_in_goodwill / goodwill_prior
```

```text
impairment_to_goodwill = goodwill_impairment / goodwill_beginning_or_average
```

```text
acquisition_intensity = acquisitions / revenue
```

Optional organic-growth approximation:

```text
organic_growth_proxy =
reported_revenue_growth
- acquisition_contribution_to_growth
```

If acquisition contribution is unavailable, the agent should not invent it. It should say:

```text
Acquisition contribution is not disclosed. Goodwill increased materially, so reported growth may not be purely organic.
```

### Goodwill treatment in valuation

Goodwill should not be treated as cash or separately added to value.

The agent should support 3 views of return on capital:

| View | Formula | Use |
|---|---|---|
| Reported ROC | After-tax operating income / reported invested capital | Direct accounting view |
| Goodwill-included ROC | After-tax operating income / invested capital including goodwill | Capital allocation view |
| Goodwill-excluded ROC | After-tax operating income / invested capital excluding goodwill | Operating asset efficiency view |

Default recommendation:

```text
Use goodwill-included ROC to judge whether management's acquisitions have created value.
Use goodwill-excluded ROC only as a secondary operating-efficiency view.
```

Reason:

```text
If a company paid for acquisitions, the capital spent should count when judging whether management earned adequate returns.
```

### Goodwill impairment treatment

Goodwill impairment is usually non-cash in the current period, but it is not economically meaningless.

The agent should handle it in two separate places:

| Area | Treatment |
|---|---|
| Normalized earnings | Add back impairment if it is non-recurring and clearly separated |
| Capital allocation diagnostics | Flag impairment as possible evidence of acquisition overpayment |
| Forecast | Do not project recurring goodwill impairment unless there is evidence of serial impairment |
| Risk section | Mention impairment as a governance/capital allocation risk |
| ROC analysis | Keep historical acquisition cost in the capital base when judging management returns |

The agent should not say:

```text
Goodwill impairment is non-cash, so ignore it.
```

It should say:

```text
Goodwill impairment is non-cash today, but it may reveal that past cash acquisition spending failed to earn adequate returns.
```

---

# Product design: where Batch 03 fits in the valuation workflow

## Updated valuation workflow

```text
1. Company intake
2. Industry matching
3. Financial statement ingestion
4. Accounting normalization
   4.1 Lease adjustment
   4.2 R&D capitalization
   4.3 One-time items
   4.4 Goodwill and acquisition diagnostics
5. Historical operating analysis
6. DCF assumption generation
7. User assumption overrides
8. Forecast engine
9. Terminal value engine
10. Relative-pricing cross-check
11. Diagnostics and investment memo
```

Batch 03 specifically owns step 4.2 and 4.4.

## Quick mode behavior

In quick valuation mode, the tool should not force the user through a full accounting clean-up.

Instead, show a compact toggle:

```text
Accounting normalization
[ ] Use reported numbers only
[x] Auto-normalize material R&D
[x] Flag goodwill/acquisition issues
```

Default behavior:

| Condition | Quick mode default |
|---|---|
| Company has no material R&D | Do not adjust |
| Company R&D/revenue below 1% and industry R&D/revenue below 1% | Do not adjust, just disclose |
| Company R&D/revenue above 2% or industry R&D/revenue above 2% | Auto-suggest R&D capitalization |
| Goodwill/assets above industry median or above 10% | Show goodwill warning |
| Goodwill impairment exists | Normalize earnings but show capital allocation warning |
| Acquisition spending is material | Ask whether growth is organic or acquisition-driven |

## Advanced mode behavior

Advanced mode should expose full controls:

```text
R&D capitalization
- Enable / disable
- Amortization life
- Current R&D
- R&D history
- R&D asset calculated
- R&D amortization calculated
- Adjusted EBIT
- Adjusted invested capital
- Adjusted ROC
```

```text
Goodwill and acquisitions
- Current goodwill
- Prior goodwill
- Goodwill / total assets
- Change in goodwill
- Goodwill impairment
- Impairment / goodwill
- Acquisition spending
- Reported revenue growth
- Organic-growth disclosure
- ROC with goodwill
- ROC excluding goodwill
```

---

# Database design

## Table: `industry_rd_benchmarks`

Purpose: store Damodaran industry R&D benchmark rows.

```sql
CREATE TABLE industry_rd_benchmarks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_name TEXT NOT NULL DEFAULT 'Damodaran',
    country TEXT NOT NULL,
    industry_name TEXT NOT NULL,
    number_of_firms INTEGER,
    rd_capitalized_usd_millions NUMERIC,
    rd_capitalized_pct_invested_capital NUMERIC,
    rd_ltm_usd_millions NUMERIC,
    current_rd_pct_revenue NUMERIC,
    rd_1y_ago_usd_millions NUMERIC,
    rd_2y_ago_usd_millions NUMERIC,
    rd_3y_ago_usd_millions NUMERIC,
    rd_4y_ago_usd_millions NUMERIC,
    rd_5y_ago_usd_millions NUMERIC,
    rd_cagr_5y NUMERIC,
    source_url TEXT,
    data_updated_at DATE,
    imported_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE(country, industry_name, data_updated_at)
);
```

## Table: `industry_goodwill_benchmarks`

Purpose: store Damodaran industry goodwill benchmark rows.

```sql
CREATE TABLE industry_goodwill_benchmarks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_name TEXT NOT NULL DEFAULT 'Damodaran',
    country TEXT NOT NULL,
    industry_name TEXT NOT NULL,
    number_of_firms INTEGER,
    goodwill_usd_millions NUMERIC,
    change_in_goodwill_last_year_usd_millions NUMERIC,
    goodwill_pct_total_assets NUMERIC,
    impairment_goodwill_ltm_usd_millions NUMERIC,
    impairment_pct_goodwill NUMERIC,
    source_url TEXT,
    data_updated_at DATE,
    imported_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE(country, industry_name, data_updated_at)
);
```

## Table: `company_rd_history`

Purpose: store company-specific R&D history used in the R&D capitalization calculation.

```sql
CREATE TABLE company_rd_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id UUID NOT NULL REFERENCES companies(id),
    fiscal_year INTEGER NOT NULL,
    rd_expense NUMERIC,
    currency TEXT NOT NULL,
    source_document_id UUID,
    source_line_item TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE(company_id, fiscal_year)
);
```

## Table: `valuation_accounting_adjustments`

Purpose: store normalization choices for each valuation run.

```sql
CREATE TABLE valuation_accounting_adjustments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    valuation_run_id UUID NOT NULL REFERENCES valuation_runs(id),

    use_rd_capitalization BOOLEAN NOT NULL DEFAULT false,
    rd_amortization_life_years INTEGER NOT NULL DEFAULT 5,
    rd_asset NUMERIC,
    rd_amortization NUMERIC,
    adjusted_ebit_for_rd NUMERIC,
    adjusted_invested_capital_for_rd NUMERIC,
    adjusted_roc_for_rd NUMERIC,

    use_goodwill_diagnostics BOOLEAN NOT NULL DEFAULT true,
    goodwill_current NUMERIC,
    goodwill_prior NUMERIC,
    goodwill_to_assets NUMERIC,
    change_in_goodwill NUMERIC,
    goodwill_impairment NUMERIC,
    impairment_to_goodwill NUMERIC,
    acquisitions NUMERIC,

    normalized_ebit NUMERIC,
    normalized_invested_capital NUMERIC,
    normalized_roc NUMERIC,

    explanation TEXT,
    warnings JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
```

## Table: `calculation_audit_trail`

Purpose: make every adjustment auditable.

```sql
CREATE TABLE calculation_audit_trail (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    valuation_run_id UUID NOT NULL REFERENCES valuation_runs(id),
    module TEXT NOT NULL,
    calculation_name TEXT NOT NULL,
    inputs JSONB NOT NULL,
    formula TEXT NOT NULL,
    output JSONB NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
```

Required principle:

```text
Every accounting adjustment must be traceable back to its source line items and formula.
```

---

# Backend services

## 1. `DamodaranAccountingBenchmarkImporter`

Responsibilities:

```text
- Import R&DIndia.xlsx
- Import goodwillIndia.xlsx
- Detect header row by finding "Industry Name"
- Normalize percent fields as decimals
- Convert "NA" to null
- Parse Excel serial date
- Store source metadata
- Upsert benchmark rows
```

Required behavior:

```text
Never hardcode row 8 forever.
Use row 8 as observed, but implement robust header detection.
```

## 2. `RDCapitalizationService`

Responsibilities:

```text
- Pull company R&D history
- Infer whether R&D capitalization is material
- Calculate R&D asset
- Calculate R&D amortization
- Adjust EBIT
- Adjust operating margin
- Adjust invested capital
- Adjust ROC
- Produce calculation audit trail
```

Core method signature:

```ts
calculateRDAdjustment(params: {
  currentRd: number;
  historicalRd: {
    tMinus1: number;
    tMinus2: number;
    tMinus3: number;
    tMinus4: number;
    tMinus5: number;
  };
  reportedEbit: number;
  revenue: number;
  investedCapital: number;
  taxRate: number;
  amortizationLifeYears?: number;
})
```

Expected output:

```ts
{
  rdAsset: number;
  rdAmortization: number;
  adjustedEbit: number;
  adjustedOperatingMargin: number;
  adjustedInvestedCapital: number;
  adjustedAfterTaxOperatingIncome: number;
  adjustedRoc: number;
  adjustedReinvestment: number;
  warnings: AccountingWarning[];
  auditTrail: CalculationStep[];
}
```

## 3. `GoodwillDiagnosticsService`

Responsibilities:

```text
- Pull company goodwill data
- Pull total assets
- Pull impairment
- Pull acquisition spending
- Calculate goodwill ratios
- Compare to industry benchmark
- Identify acquisition-heavy business model
- Distinguish earnings normalization from capital allocation diagnostics
```

Core method signature:

```ts
analyzeGoodwill(params: {
  goodwillCurrent: number;
  goodwillPrior: number;
  totalAssets: number;
  goodwillImpairment: number;
  acquisitions: number | null;
  revenue: number;
  revenueGrowth: number | null;
  industryBenchmark: GoodwillBenchmark | null;
})
```

Expected output:

```ts
{
  goodwillToAssets: number;
  changeInGoodwill: number;
  impairmentToGoodwill: number;
  acquisitionIntensity: number | null;
  isAcquisitionHeavy: boolean;
  impairmentWarning: boolean;
  organicGrowthConcern: boolean;
  normalizedEbitAdjustment: number;
  diagnostics: AccountingDiagnostic[];
  auditTrail: CalculationStep[];
}
```

## 4. `AccountingNormalizationService`

Responsibilities:

```text
- Run lease adjustments from Batch 02 if available
- Run R&D capitalization from this batch
- Run goodwill diagnostics from this batch
- Handle one-time item normalization
- Produce normalized financials for the DCF engine
```

Output should feed directly into:

```text
- Historical margin analysis
- ROC/ROIC analysis
- Sales-to-capital analysis
- FCFF forecast
- Terminal value diagnostics
```

---

# API design

## Import endpoints

```http
POST /api/admin/damodaran/accounting/import-rd
POST /api/admin/damodaran/accounting/import-goodwill
```

Expected body:

```json
{
  "country": "India",
  "filePath": "/data/damodaran/R&DIndia.xlsx",
  "dataUpdatedAt": "2026-01-05"
}
```

## Benchmark lookup endpoint

```http
GET /api/valuation/benchmarks/accounting?country=India&industry=Drugs%20(Pharmaceutical)
```

Response:

```json
{
  "industry": "Drugs (Pharmaceutical)",
  "country": "India",
  "rd": {
    "numberOfFirms": 188,
    "rdCapitalizedUsdMillions": 5877.604,
    "rdCapitalizedPctInvestedCapital": 0.1199,
    "currentRdPctRevenue": 0.0421,
    "rdCagr5y": null
  },
  "goodwill": {
    "numberOfFirms": 188,
    "goodwillUsdMillions": 4832.246,
    "goodwillPctTotalAssets": null,
    "impairmentPctGoodwill": null
  }
}
```

Implementation note:

```text
The example structure is illustrative. Use actual values from the database and preserve nulls where source values are NA.
```

## R&D adjustment endpoint

```http
POST /api/valuation/{valuationRunId}/accounting/rd-capitalization
```

Request:

```json
{
  "enabled": true,
  "amortizationLifeYears": 5,
  "currentRd": 1000,
  "historicalRd": {
    "tMinus1": 900,
    "tMinus2": 800,
    "tMinus3": 700,
    "tMinus4": 600,
    "tMinus5": 500
  },
  "reportedEbit": 2500,
  "revenue": 20000,
  "investedCapital": 15000,
  "taxRate": 0.25
}
```

Response:

```json
{
  "rdAsset": 2600,
  "rdAmortization": 700,
  "adjustedEbit": 2800,
  "adjustedOperatingMargin": 0.14,
  "adjustedInvestedCapital": 17600,
  "adjustedRoc": 0.1193,
  "warnings": [],
  "formula": "adjusted_ebit = reported_ebit + current_rd - rd_amortization"
}
```

## Goodwill diagnostics endpoint

```http
POST /api/valuation/{valuationRunId}/accounting/goodwill-diagnostics
```

Request:

```json
{
  "goodwillCurrent": 5000,
  "goodwillPrior": 4200,
  "totalAssets": 25000,
  "goodwillImpairment": 300,
  "acquisitions": 1500,
  "revenue": 20000,
  "reportedRevenueGrowth": 0.18,
  "industryName": "Computer Services",
  "country": "India"
}
```

Response:

```json
{
  "goodwillToAssets": 0.2,
  "changeInGoodwill": 800,
  "impairmentToGoodwill": 0.0714,
  "acquisitionIntensity": 0.075,
  "diagnostics": [
    {
      "severity": "warning",
      "message": "Goodwill is material relative to total assets. Reported growth may include acquisition-driven growth."
    },
    {
      "severity": "warning",
      "message": "Goodwill impairment is non-cash in the current period but may indicate prior acquisition overpayment."
    }
  ]
}
```

## Full normalization endpoint

```http
POST /api/valuation/{valuationRunId}/accounting/normalize
```

Purpose:

```text
Apply all enabled accounting adjustments and return normalized financials for DCF.
```

Response should include:

```json
{
  "reported": {
    "ebit": 2500,
    "investedCapital": 15000,
    "roc": 0.125
  },
  "normalized": {
    "ebit": 2800,
    "investedCapital": 17600,
    "roc": 0.1193
  },
  "adjustments": [
    "R&D capitalization",
    "Goodwill diagnostics"
  ],
  "warnings": []
}
```

---

# Frontend requirements

## 1. Accounting normalization panel

Location:

```text
Valuation workspace → Assumptions → Accounting normalization
```

Sections:

```text
- Summary card
- R&D capitalization
- Goodwill and acquisition diagnostics
- Reported vs adjusted metrics
- Warnings
- Calculation audit trail
```

## 2. Quick summary card

Show:

```text
Accounting normalization status
R&D materiality
Goodwill materiality
Adjusted EBIT impact
Adjusted ROC impact
Main warning
```

Example:

```text
Accounting normalization: Enabled
R&D capitalization: Material
Goodwill diagnostics: Warning
Reported EBIT: ₹10,000m
Adjusted EBIT: ₹11,200m
Reported ROC: 14.0%
Adjusted ROC: 12.7%
Main warning: Goodwill/assets is above industry benchmark. Review acquisition-driven growth.
```

## 3. R&D capitalization card

Required fields:

```text
Toggle: Enable R&D capitalization
Amortization life: 3 / 5 / 7 / custom years
Current R&D
R&D one year ago
R&D two years ago
R&D three years ago
R&D four years ago
R&D five years ago
Calculated R&D asset
Calculated R&D amortization
Reported EBIT
Adjusted EBIT
Reported margin
Adjusted margin
Reported ROC
Adjusted ROC
```

Required chart:

```text
R&D history bar chart:
Current, -1Y, -2Y, -3Y, -4Y, -5Y
```

Required explanation:

```text
R&D is treated as a multi-year investment. The adjustment adds current R&D back to EBIT, subtracts amortization of past R&D, and adds the unamortized research asset to invested capital.
```

## 4. Goodwill diagnostics card

Required fields:

```text
Current goodwill
Prior goodwill
Change in goodwill
Total assets
Goodwill/assets
Goodwill impairment
Impairment/goodwill
Acquisitions
Acquisitions/revenue
Industry goodwill/assets benchmark
```

Required warning states:

| Condition | Warning |
|---|---|
| `goodwill/assets > 10%` | Goodwill is material. Acquisition history matters. |
| `goodwill/assets > 2 × industry median/benchmark` | Goodwill burden is high relative to industry. |
| `change in goodwill > 5% of total assets` | Recent acquisition activity may distort growth. |
| `impairment/goodwill > 5%` | Material impairment. Possible acquisition overpayment. |
| `acquisitions/revenue > 5%` | Growth may be acquisition-driven, not organic. |

## 5. Reported vs adjusted metrics table

Columns:

```text
Metric
Reported
R&D adjusted
Goodwill view
Normalized
Change
Interpretation
```

Rows:

```text
EBIT
Operating margin
After-tax operating income
Invested capital
ROC
Sales-to-capital
Reinvestment rate
FCFF
```

## 6. Calculation audit drawer

Every adjustment should be explainable.

Example:

```text
R&D asset = current R&D + 0.8 × R&D(-1) + 0.6 × R&D(-2) + 0.4 × R&D(-3) + 0.2 × R&D(-4)
R&D amortization = average of R&D(-1) to R&D(-5)
Adjusted EBIT = reported EBIT + current R&D - R&D amortization
```

Do not hide these formulas. The user should be able to see exactly how the agent got the adjustment.

---

# Agent behavior rules

## R&D behavior

The agent should say:

```text
This company's reported EBIT may understate economic operating income because R&D is material and likely creates multi-year benefits.
```

It should not say:

```text
R&D capitalization makes the company more valuable.
```

Correct framing:

```text
R&D capitalization changes the measurement of operating income, invested capital, and ROC. It does not automatically create free cash flow or value.
```

## Goodwill behavior

The agent should say:

```text
Goodwill is material, so acquisition history should be examined. Reported growth may include acquired growth, and ROC should be judged both including and excluding goodwill.
```

It should not say:

```text
Goodwill is an asset, so add it to valuation.
```

Correct framing:

```text
Goodwill is already embedded in the capital invested in the business. It is useful for judging acquisition quality, not as a separate value add.
```

## Impairment behavior

The agent should say:

```text
The goodwill impairment can be added back when normalizing current earnings, but it should remain a warning about past acquisition quality.
```

It should not say:

```text
Goodwill impairment is non-cash, so ignore it.
```

## Missing data behavior

If R&D history is missing:

```text
The company discloses current R&D but not enough history to build a full capitalization schedule. I can use a simplified current-year adjustment, industry averages, or leave reported numbers unchanged.
```

If goodwill impairment is not disclosed:

```text
No goodwill impairment was found in the available data. That does not prove acquisitions were successful; it only means there is no impairment signal in the data used.
```

If acquisition contribution to revenue growth is missing:

```text
The company does not disclose enough information to separate organic from acquired growth. Goodwill increased materially, so reported growth should be interpreted cautiously.
```

---

# Diagnostics and sanity checks

## R&D diagnostics

| Diagnostic | Rule | Severity |
|---|---|---|
| R&D materiality | Company R&D/revenue > 2% | Info/warning |
| R&D industry materiality | Industry R&D/revenue > 2% | Info |
| Missing history | Current R&D exists but fewer than 5 prior years available | Warning |
| R&D decline | Current R&D materially below 5-year average | Warning if growth story depends on innovation |
| R&D capitalization impact | Adjusted EBIT differs from reported EBIT by >10% | Warning |
| Adjusted ROC change | Adjusted ROC differs from reported ROC by >300 bps | Warning |
| Innovation story mismatch | Narrative assumes innovation but R&D/revenue is low and falling | Warning |

## Goodwill diagnostics

| Diagnostic | Rule | Severity |
|---|---|---|
| Goodwill materiality | Goodwill/assets > 10% | Warning |
| Goodwill industry outlier | Company goodwill/assets > 2× industry benchmark | Warning |
| Recent acquisition activity | Change in goodwill > 5% of total assets | Warning |
| Impairment severity | Impairment/goodwill > 5% | Warning |
| Serial impairment | Impairments in 2+ years | Severe warning |
| Acquisition-funded growth | Acquisitions/revenue > 5% | Warning |
| Organic growth ambiguity | Revenue growth high and goodwill increasing materially | Warning |
| Capital allocation quality | High goodwill + low ROC | Severe warning |

## Forecast diagnostics

| Forecast issue | What the agent should check |
|---|---|
| High revenue growth | Is growth organic or acquired? |
| Margin expansion | Is margin expansion driven by real operating improvement or just accounting normalization? |
| High ROC | Is ROC high only because goodwill is excluded? |
| Terminal ROC | Does terminal ROC include acquisition capital if acquisitions are part of the business model? |
| Reinvestment | Does forecast reinvestment include R&D investment when R&D is capitalized? |
| Acquisition narrative | If acquisitions are part of the strategy, are acquisition costs included in reinvestment? |

---

# Integration with the DCF engine

## Normalized operating income

The DCF engine should accept both reported and normalized operating income:

```ts
type OperatingIncomeInput = {
  reportedEbit: number;
  normalizedEbit: number;
  normalizationAdjustments: AccountingAdjustment[];
};
```

The valuation run should store which version is being used:

```text
Valuation basis:
- Reported accounting
- R&D adjusted
- Lease adjusted
- R&D + lease adjusted
- Fully normalized
```

## Normalized invested capital

The DCF engine should store multiple capital bases:

```text
reported_invested_capital
lease_adjusted_invested_capital
rd_adjusted_invested_capital
goodwill_included_invested_capital
goodwill_excluded_invested_capital
normalized_invested_capital
```

The agent should default to:

```text
normalized_invested_capital = reported invested capital + lease adjustment + R&D asset
```

For goodwill:

```text
Use goodwill-included capital for capital allocation analysis.
Show goodwill-excluded capital as a supplementary operating efficiency view.
```

## Growth and reinvestment link

When R&D is capitalized, growth logic should still obey:

```text
Growth = Reinvestment Rate × Return on Capital
```

The reinvestment rate must include R&D investment:

```text
adjusted_reinvestment =
net_capex
+ change_in_non_cash_working_capital
+ acquisitions
+ current_rd
- rd_amortization
```

The adjusted ROC should use adjusted capital:

```text
adjusted_roc =
adjusted_after_tax_operating_income / adjusted_invested_capital
```

This prevents the agent from overstating growth quality.

## Terminal value impact

Terminal assumptions should be checked under normalized accounting.

Required checks:

```text
- If the company is innovation-heavy, terminal reinvestment should include maintenance R&D.
- If acquisitions are a recurring growth strategy, terminal reinvestment should include acquisition spending.
- Terminal ROC should not be calculated on goodwill-excluded capital only if goodwill is part of the company's growth model.
- Terminal margins should not mechanically use adjusted margins without explaining the accounting change.
```

---

# Testing plan

## Unit tests: R&D capitalization

Test case:

```json
{
  "currentRd": 1000,
  "rdTMinus1": 900,
  "rdTMinus2": 800,
  "rdTMinus3": 700,
  "rdTMinus4": 600,
  "rdTMinus5": 500,
  "reportedEbit": 2500,
  "revenue": 20000,
  "investedCapital": 15000,
  "taxRate": 0.25
}
```

Expected:

```text
rd_asset = 1000 + 0.8×900 + 0.6×800 + 0.4×700 + 0.2×600 = 2600
rd_amortization = (900 + 800 + 700 + 600 + 500) / 5 = 700
adjusted_ebit = 2500 + 1000 - 700 = 2800
adjusted_operating_margin = 2800 / 20000 = 14.0%
adjusted_invested_capital = 15000 + 2600 = 17600
adjusted_after_tax_operating_income = 2800 × 0.75 = 2100
adjusted_roc = 2100 / 17600 = 11.93%
```

## Unit tests: goodwill diagnostics

Test case:

```json
{
  "goodwillCurrent": 5000,
  "goodwillPrior": 4200,
  "totalAssets": 25000,
  "goodwillImpairment": 300,
  "acquisitions": 1500,
  "revenue": 20000
}
```

Expected:

```text
goodwill_to_assets = 5000 / 25000 = 20.0%
change_in_goodwill = 800
goodwill_growth_rate = 800 / 4200 = 19.05%
impairment_to_goodwill = 300 / 4200 or 300 / average goodwill, depending on selected method
acquisition_intensity = 1500 / 20000 = 7.5%
Warnings:
- goodwill materiality
- recent acquisition activity
- material impairment
- acquisition-driven growth risk
```

## Integration tests

| Test | Expected result |
|---|---|
| Pharma company with high R&D | R&D capitalization auto-suggested |
| Bank with zero R&D | R&D capitalization disabled |
| Software company with missing 5-year R&D history | Warning and fallback options |
| Acquisitive company with rising goodwill | Organic-growth warning |
| Company with impairment | Earnings normalization plus capital allocation warning |
| Goodwill-heavy low-ROC company | Severe capital allocation warning |
| Goodwill-excluded ROC much higher than goodwill-included ROC | Agent explains the difference |

---

# Codex implementation checklist

## Step 1: Importer

```text
[ ] Add DamodaranAccountingBenchmarkImporter
[ ] Build robust header detection by "Industry Name"
[ ] Import R&DIndia.xlsx
[ ] Import goodwillIndia.xlsx
[ ] Convert "NA" values to null
[ ] Convert percent fields to decimals
[ ] Store source metadata and update date
[ ] Add import tests
```

## Step 2: Database

```text
[ ] Add industry_rd_benchmarks migration
[ ] Add industry_goodwill_benchmarks migration
[ ] Add company_rd_history migration
[ ] Add valuation_accounting_adjustments migration
[ ] Add calculation_audit_trail migration if not already present
```

## Step 3: Services

```text
[ ] Build RDCapitalizationService
[ ] Build GoodwillDiagnosticsService
[ ] Build AccountingNormalizationService
[ ] Add audit trail generation for every calculation
[ ] Add missing-data handling
[ ] Add warning severity framework
```

## Step 4: API

```text
[ ] Add admin import endpoints
[ ] Add accounting benchmark lookup endpoint
[ ] Add R&D capitalization endpoint
[ ] Add goodwill diagnostics endpoint
[ ] Add full accounting normalization endpoint
[ ] Add validation schemas
```

## Step 5: Frontend

```text
[ ] Add Accounting Normalization tab/panel
[ ] Add quick-mode accounting toggle
[ ] Add R&D capitalization card
[ ] Add goodwill diagnostics card
[ ] Add reported vs adjusted metrics table
[ ] Add calculation audit drawer
[ ] Add warning badges
```

## Step 6: DCF integration

```text
[ ] Feed normalized EBIT into forecast engine
[ ] Feed adjusted invested capital into ROC calculations
[ ] Include R&D in reinvestment when capitalized
[ ] Add goodwill-included and goodwill-excluded ROC views
[ ] Add terminal value diagnostics for R&D and acquisition-heavy companies
```

## Step 7: Agent behavior

```text
[ ] Add rules for R&D materiality
[ ] Add rules for goodwill materiality
[ ] Add rules for impairment interpretation
[ ] Add organic vs acquired growth warning
[ ] Add explanation templates
[ ] Prevent the agent from treating goodwill as separate value
[ ] Prevent the agent from treating R&D capitalization as automatic value creation
```

---

# Prompt for Codex/Gemini

```text
You are working on the Market Intelligence valuation agent.

Implement Batch 03: Accounting Normalization, R&D Capitalization, Goodwill, and Acquisition Quality.

Context:
- Batch 01 already defined relative pricing benchmarks.
- Batch 02 already defined DCF fundamentals: growth, margins, reinvestment, ROE/ROC, working capital, and financing flows.
- Batch 03 adds the accounting normalization layer before DCF forecasting.

Use these files:
- R&DIndia.xlsx
- goodwillIndia.xlsx

Build:
1. Importer for Damodaran R&D and goodwill industry benchmarks.
2. Database tables:
   - industry_rd_benchmarks
   - industry_goodwill_benchmarks
   - company_rd_history
   - valuation_accounting_adjustments
   - calculation_audit_trail if not already present
3. Backend services:
   - RDCapitalizationService
   - GoodwillDiagnosticsService
   - AccountingNormalizationService
4. API endpoints:
   - benchmark lookup
   - R&D capitalization
   - goodwill diagnostics
   - full accounting normalization
5. Frontend:
   - accounting normalization panel
   - R&D capitalization card
   - goodwill diagnostics card
   - reported vs adjusted metrics table
   - calculation audit drawer
6. DCF integration:
   - adjusted EBIT
   - adjusted invested capital
   - adjusted ROC
   - adjusted reinvestment
   - goodwill-included and goodwill-excluded ROC views

Core rules:
- R&D capitalization improves measurement of EBIT, invested capital, ROC, and reinvestment. It does not automatically create value.
- Goodwill should not be added separately to valuation. It is a signal about acquisitions and capital allocation.
- Goodwill impairment can be added back for normalized earnings if non-recurring, but it must remain a capital allocation warning.
- Every adjustment must be auditable and formula-backed.
- The user must be able to see reported and adjusted numbers side by side.
```

---

# What this batch changes in the product vision

Before Batch 03, the valuation agent could build a reasonable DCF from reported financials and industry assumptions.

After Batch 03, it can start behaving more like a serious valuation analyst:

```text
It knows when accounting numbers are distorted.
It adjusts R&D-heavy companies more intelligently.
It distinguishes organic investment from acquisition-driven growth.
It treats goodwill impairments as information, not just accounting noise.
It prevents misleading ROC conclusions.
It makes assumptions auditable.
```

This is a major step toward a Damodaran-style valuation agent because it pushes the system away from naive spreadsheet output and toward economic interpretation.

---

# Next batch

The next logical batch is:

```text
Batch 04: Equity Cash Flow, Dividends, Buybacks, and FCFE
Files:
- divfundIndia.xls
- divfcfeIndia.xls
```

That batch should teach the agent how to handle payout, dividends, buybacks, FCFE, potential dividends, and equity cash flow valuation.
