# Valuation Agent Batch 01: India Relative Pricing Benchmarks

> **Implementation status, 2026-08-08:** `peIndia.xls`, `pbvIndia.xls`,
> `psIndia.xls`, `vebitdaIndia.xls`, and `countrystats.xls` are exact,
> independently versioned, and source-complete. Pricing rows are assembled only
> from active versions; country facts also require their active source and carry
> provenance through `/api/valuation/relative/*`. See
> `../../roadmaps/next-5-damodaran-versioned-country-statistics-checkpoint-2026-08-08.md`.

## Purpose of this batch

This batch turns Damodaran's India market multiple files into a usable **relative valuation and pricing benchmark layer** for the market intelligence agent.

This is the right first batch because it gives the agent immediate valuation usefulness without needing the full DCF engine first. It lets the agent answer:

- What are comparable Indian industries trading at?
- Is a company's DCF output sane relative to market pricing?
- What multiple is the market implicitly assigning to revenue, earnings, EBITDA, book equity, or invested capital?
- Which valuation method should be used as a cross-check, based on company type?
- Is the stock cheap, expensive, or merely low quality?

This batch should **not** replace intrinsic valuation. It should become a benchmark, cross-check, and pricing module that sits beside the Damodaran-style DCF engine.

---

## Files included in Batch 01

| File | Dataset role | Core use in the agent |
|---|---|---|
| `peIndia.xls` | India industry PE multiples | Equity earnings multiple benchmarks, PEG checks, profitable company pricing |
| `pbvIndia.xls` | India industry price/book and EV/invested capital | Bank/financial valuation support, ROE/ROIC quality checks |
| `psIndia.xls` | India industry revenue multiples | Revenue-stage, low-margin, or loss-making company cross-checks |
| `vebitdaIndia.xls` | India industry EV/EBITDA, EV/EBIT, EV/after-tax EBIT | Operating business pricing, enterprise value cross-checks |
| `countrystats.xls` | Global country-level market statistics | India market-level context and country cross-country comparison |

Files intentionally held for later batches:

| Later batch | Files | Reason |
|---|---|---|
| Batch 02: DCF fundamentals and reinvestment | `marginIndia.xls`, `capexIndia.xls`, `wcdataIndia.xls`, `roeIndia.xls`, `fundgrIndia.xls`, `fundgrEBIndia.xls`, `histgrIndia.xls`, `finflowsIndia.xls` | These feed operating forecasts, ROIC, growth, and reinvestment assumptions. |
| Batch 03: Accounting normalization and intangibles | `R&DIndia.xls`, `goodwillIndia.xls` | These support R&D capitalization, goodwill, acquisition quality, and adjusted returns. |
| Batch 04: Equity cash flow and payout | `divfundIndia.xls`, `divfcfeIndia.xls` | These support dividend, buyback, FCFE, and shareholder return logic. |
| Batch 05: Macro exposure and duration | `macro.xls`, `macrodur.xls` | These support macro sensitivity and top-down risk modules. |
| Batch 06: Option valuation and volatility | `optvarIndia.xls` | This supports real options, equity-as-option, and volatility-based modules. |

---

## What I learned from Batch 01

### 1. The files are Damodaran industry benchmark datasets, not company-level datasets

The India files are aggregated by industry. They do not give individual company rows. The valuation agent should treat them as **industry priors**, not company data.

The standard structure is:

```text
Rows 1 to 7: metadata and source information
Row 8 or 9: column headers
Rows below: industry averages / aggregates
```

Most India industry files contain around **96 industry rows**. `vebitdaIndia.xls` has one extra row structure because it separates positive EBITDA firms from all firms.

### 2. These are pricing datasets, not intrinsic valuation datasets

The PE, PBV, PS, and EV multiple datasets tell the agent how the market prices comparable firms. They do **not** prove that a business is intrinsically cheap or expensive.

The agent should use these datasets as:

- A quick pricing estimate
- A DCF sanity check
- A market mood indicator
- A way to understand what the current price implies
- A diagnostic tool for the user's assumptions

The agent should not say:

```text
This company has a lower PE than the sector, therefore it is undervalued.
```

The agent should say:

```text
The company trades below the sector PE, but the gap is only meaningful after checking growth, risk, margin quality, reinvestment needs, ROE/ROIC, and sample quality.
```

### 3. Each multiple must be tied to the correct claimholder

This is critical for Codex/Gemini to implement correctly.

| Multiple type | Numerator | Denominator | Claimholder consistency |
|---|---:|---:|---|
| PE | Equity value | Net income / EPS | Equity to equity |
| PBV | Equity value | Book equity | Equity to equity |
| Price/Sales | Equity value | Revenue | Imperfect, can be distorted by debt and cash |
| EV/Sales | Enterprise value | Revenue | Firm to firm, better than P/S for leveraged firms |
| EV/EBITDA | Enterprise value | EBITDA | Firm to firm |
| EV/EBIT | Enterprise value | EBIT | Firm to firm |
| EV/EBIT after tax | Enterprise value | EBIT after tax | Firm to firm |
| EV/Invested Capital | Enterprise value | Invested capital | Firm to firm |

The agent should actively flag mismatches, especially if users compare PE to EBITDA or EV to net income.

---

## Dataset-level findings

### A. `peIndia.xls`: Price earnings multiples

**End game in the file:** estimate ratios of market value of equity to equity earnings in different forms.

Main columns:

| Column | Meaning | Agent use |
|---|---|---|
| `Industry Name` | Damodaran industry grouping | Industry matching |
| `Number of firms` | Sample size | Reliability score |
| `% of Money Losing firms (Trailing)` | Share of firms with trailing losses | Warning signal for PE reliability |
| `Current PE` | Price / latest fiscal year EPS, averaged across money-making firms | Current earnings pricing |
| `Trailing PE` | Price / trailing 12-month EPS | More current earnings pricing |
| `Forward PE` | Price / expected next 4 quarters EPS | Consensus-like forward pricing |
| `Aggregate Mkt Cap/ Net Income (all firms)` | Aggregate equity value / aggregate net income | Weighted sector PE including losers |
| `Aggregate Mkt Cap/ Trailing Net Income (only money making firms)` | Aggregate equity value / aggregate net income for profitable firms only | Cleaner weighted PE |
| `Expected growth - next 5 years` | Expected EPS growth | Growth adjustment |
| `PEG Ratio` | Current PE / expected EPS growth | Quick but imperfect growth adjustment |

Important implementation rules:

- PE is unreliable when `% of Money Losing firms` is high.
- Forward PE depends on forecasted EPS and should be labeled as estimate-based.
- PEG should not be treated as growth-neutral. It still embeds risk, payout, and growth quality.
- Aggregate PE is better for market weighting but can be distorted by losses.
- Simple averaged PE can be distorted by outliers.

Agent behavior:

```text
Use PE only when the company has normalized positive earnings.
If earnings are temporarily depressed, normalize earnings first.
If earnings are structurally negative, do not use PE as a primary valuation method.
```

---

### B. `pbvIndia.xls`: Price/book and EV/invested capital

**End game in the file:** estimate equity and firm value relative to book equity and invested capital, with ROE and ROIC as companion variables.

Main columns:

| Column | Meaning | Agent use |
|---|---|---|
| `Industry Name` | Damodaran industry grouping | Industry matching |
| `Number of firms` | Sample size | Reliability score |
| `PBV` | Aggregate market capitalization / aggregate book equity | Equity book multiple |
| `ROE` | Aggregate net income / aggregate book equity | Equity return quality |
| `EV/ Invested Capital` | Aggregate EV / invested capital | Firm value relative to capital base |
| `ROIC` | After-tax operating income / invested capital | Operating return quality |

Important implementation rules:

- PBV is not meaningful without ROE.
- EV/invested capital is not meaningful without ROIC.
- A company trading below book is not automatically cheap. If ROE is below cost of equity, a sub-1 PBV may be justified.
- A company deserves a higher PBV when ROE sustainably exceeds cost of equity.
- A company deserves a higher EV/invested capital when ROIC sustainably exceeds WACC.

Agent behavior:

```text
For banks, insurers, and financial services, prefer PBV + ROE over EV/EBITDA.
For operating companies, use EV/invested capital + ROIC as a quality diagnostic, not as the only valuation method.
```

---

### C. `psIndia.xls`: Revenue multiples

**End game in the file:** estimate revenue-based equity and enterprise multiples, with margins as companion variables.

Main columns:

| Column | Meaning | Agent use |
|---|---|---|
| `Industry Name` | Damodaran industry grouping | Industry matching |
| `Number of firms` | Sample size | Reliability score |
| `Price/Sales` | Aggregate market cap / aggregate revenue | Equity revenue multiple |
| `Net Margin` | Aggregate net income / aggregate revenue | Equity profitability quality |
| `EV/Sales` | Aggregate EV / aggregate revenue | Firm revenue multiple |
| `Pre-tax Operating Margin` | Aggregate operating income / aggregate revenue | Operating profitability quality |

Important implementation rules:

- EV/Sales is usually better than Price/Sales for companies with meaningful debt or cash.
- Revenue multiples require margin normalization.
- A high EV/Sales can be justified by high future margins, high growth, low reinvestment needs, or low risk.
- A low EV/Sales can be deserved if margins are poor, scale economics are weak, or reinvestment needs are high.

Agent behavior:

```text
Use EV/Sales for negative earnings companies, early-stage companies, cyclical trough years, or companies where EBITDA is not yet normalized.
Always pair EV/Sales with current margin and target margin.
```

---

### D. `vebitdaIndia.xls`: Enterprise value operating multiples

**End game in the file:** measure market value of operating assets relative to operating fundamentals.

Main columns:

| Column group | Meaning | Agent use |
|---|---|---|
| `Only positive EBITDA firms` | Multiples computed only for firms with positive EBITDA | Cleaner for EBITDA-based pricing |
| `All firms` | Multiples across all firms | Broader but can contain denominator distortions |
| `EV/EBITDAR&D` | EV / EBITDAR&D | Useful when treating R&D as capital expense |
| `EV/EBITDA` | EV / EBITDA | Standard operating cash flow multiple |
| `EV/EBIT` | EV / EBIT | Operating earnings multiple before tax |
| `EV/EBIT (1-t)` | EV / after-tax EBIT | Closest to after-tax operating income pricing |

Important implementation rules:

- This file has duplicate column labels because it separates positive EBITDA firms from all firms. The parser must rename them explicitly.
- EV/EBITDA is inappropriate for banks and many financial companies.
- EV/EBITDA can make capital-intensive companies look cheap if depreciation is economically real.
- EV/EBITDAR&D is useful for R&D-heavy companies, but only if the agent explains that R&D is being treated as capital investment.

Recommended normalized column names:

```text
positive_ebitda_ev_ebitda
positive_ebitda_ev_ebit
positive_ebitda_ev_ebit_after_tax
positive_ebitda_ev_ebitda_rd
all_firms_ev_ebitda
all_firms_ev_ebit
all_firms_ev_ebit_after_tax
all_firms_ev_ebitda_rd
```

Agent behavior:

```text
For profitable non-financial operating companies, EV/EBITDA and EV/EBIT should be primary relative valuation cross-checks.
For capital-intensive industries, EV/EBIT or EV/EBIT after tax should receive more weight than EV/EBITDA.
```

---

### E. `countrystats.xls`: Global country statistics

**End game in the file:** country-level market multiples and corporate finance statistics.

This file is useful for broad market context. The India row shows:

| Metric | India value from file |
|---|---:|
| Number of listed firms in country dataset | 4,520 |
| Market capitalization, US dollars | 4,013,915.843 million |
| Enterprise value, US dollars | 4,573,904.582 million |
| Median current PE | 25.59x |
| Median trailing PE | 24.81x |
| Median forward PE | 28.04x |
| Median PEG | 2.03x |
| Median PBV | 2.15x |
| Median P/S | 1.71x |
| Median EV/EBIT | 19.89x |
| Median EV/EBITDA | 15.99x |
| Median EV/Invested Capital | 1.94x |
| Median EV/Sales | 2.02x |
| Dividend yield | 1.15% |

Important implementation rules:

- Use `countrystats.xls` for market context, not direct company valuation.
- Country median multiples help answer whether a whole market looks expensive or cheap relative to other markets.
- They do not replace industry-specific multiples.
- The agent should prioritize industry benchmarks first, country benchmarks second.

Agent behavior:

```text
When valuing an Indian company, show both:
1. The relevant Indian industry multiple.
2. The broad India country median multiple.

This helps separate company-specific pricing from country-level market mood.
```

---

## How this improves the valuation agent

### 1. Adds a proper relative valuation module

The agent should have 3 valuation outputs:

| Output | Purpose |
|---|---|
| Intrinsic value | Value based on cash flows, growth, risk, and reinvestment |
| Relative pricing estimate | What similar firms are priced at today |
| Market-implied expectations | What the current stock price requires to be justified |

Batch 01 supports the second and part of the third.

### 2. Gives the agent industry priors

Before the user has entered detailed assumptions, the agent can use industry benchmarks as priors:

| Assumption type | Benchmark source |
|---|---|
| Normalized PE | `peIndia.xls` |
| Normalized EV/EBITDA | `vebitdaIndia.xls` |
| Normalized EV/Sales | `psIndia.xls` |
| Normalized PBV | `pbvIndia.xls` |
| Return quality | `pbvIndia.xls` ROE and ROIC |
| Margin quality | `psIndia.xls` net margin and operating margin |
| India market context | `countrystats.xls` |

### 3. Adds DCF output diagnostics

After the DCF engine calculates value, the agent should calculate implied multiples:

```text
DCF implied EV/Sales = DCF enterprise value / current revenue
DCF implied EV/EBITDA = DCF enterprise value / current EBITDA
DCF implied EV/EBIT = DCF enterprise value / current EBIT
DCF implied PE = DCF equity value / normalized net income
DCF implied PBV = DCF equity value / book equity
DCF implied EV/Invested Capital = DCF enterprise value / invested capital
```

Then compare those implied multiples to industry benchmarks.

Example diagnostic:

```text
Your DCF implies 28.0x EV/EBITDA. The Indian industry benchmark is 16.0x. That does not automatically make your DCF wrong, but your assumptions need to justify the premium through higher growth, higher margins, lower risk, better ROIC, or lower reinvestment needs.
```

### 4. Adds method selection logic

The agent should select relative valuation methods based on company type.

| Company type | Primary relative methods | Avoid or de-emphasize |
|---|---|---|
| Stable profitable non-financial | PE, EV/EBITDA, EV/EBIT | EV/Sales as primary |
| High-growth profitable | Forward PE, PEG, EV/Sales, EV/EBITDA | Trailing PE alone |
| Loss-making with revenue | EV/Sales with target margin analysis | PE, trailing EV/EBIT |
| Bank or insurer | PBV + ROE | EV/EBITDA, EV/Sales |
| Capital-intensive industrial | EV/EBIT, EV/EBIT after tax, EV/Invested Capital + ROIC | EV/EBITDA alone |
| R&D-heavy business | EV/EBITDAR&D, adjusted operating metrics | Unadjusted EBIT alone |
| Cyclical company | Normalized earnings multiples | Point-in-cycle PE |
| Company with large cash balance | EV multiples | Price/Sales alone |
| Highly levered company | EV multiples | Equity multiples without leverage warning |

---

## Data model proposal

### Table: `damodaran_dataset_files`

Stores source metadata for every Damodaran dataset.

```sql
CREATE TABLE damodaran_dataset_files (
  id UUID PRIMARY KEY,
  uploaded_filename TEXT NOT NULL,
  dataset_code TEXT NOT NULL,
  country TEXT,
  date_updated DATE,
  created_by TEXT,
  source_homepage TEXT,
  source_data_website TEXT,
  source_company_list_url TEXT,
  source_variable_definitions_url TEXT,
  original_file_type TEXT,
  imported_at TIMESTAMP NOT NULL DEFAULT NOW(),
  notes TEXT
);
```

Recommended `dataset_code` values:

```text
india_pe_multiples
india_pbv_roe_multiples
india_revenue_multiples
india_enterprise_multiples
country_market_stats
```

### Table: `industry_benchmark_metrics`

Normalized long-format table. This is better than storing one wide table per file.

```sql
CREATE TABLE industry_benchmark_metrics (
  id UUID PRIMARY KEY,
  dataset_file_id UUID REFERENCES damodaran_dataset_files(id),
  country TEXT NOT NULL,
  industry_name TEXT NOT NULL,
  metric_name TEXT NOT NULL,
  metric_value NUMERIC,
  metric_unit TEXT,
  sample_size INTEGER,
  period_label TEXT,
  denominator_filter TEXT,
  source_row_number INTEGER,
  created_at TIMESTAMP NOT NULL DEFAULT NOW()
);
```

Example rows:

| country | industry_name | metric_name | metric_value | unit | denominator_filter |
|---|---|---:|---:|---|---|
| India | Advertising | current_pe | 43.476 | x | money_making_firms |
| India | Advertising | expected_eps_growth_5y | 0.293 | percent_decimal | all_available_firms |
| India | Advertising | ev_sales | 2.908 | x | all_firms |
| India | Advertising | net_margin | 0.0807 | percent_decimal | all_firms |
| India | Advertising | positive_ebitda_ev_ebitda | 15.589 | x | positive_ebitda_firms |

### Table: `country_market_stats`

```sql
CREATE TABLE country_market_stats (
  id UUID PRIMARY KEY,
  dataset_file_id UUID REFERENCES damodaran_dataset_files(id),
  country TEXT NOT NULL,
  firm_count INTEGER,
  market_cap_usd_millions NUMERIC,
  total_debt_usd_millions NUMERIC,
  firm_value_usd_millions NUMERIC,
  cash_usd_millions NUMERIC,
  enterprise_value_usd_millions NUMERIC,
  median_current_pe NUMERIC,
  median_trailing_pe NUMERIC,
  median_forward_pe NUMERIC,
  median_peg NUMERIC,
  median_pbv NUMERIC,
  median_ps NUMERIC,
  median_ev_ebit NUMERIC,
  median_ev_ebitda NUMERIC,
  median_ev_invested_capital NUMERIC,
  median_ev_sales NUMERIC,
  dividend_yield NUMERIC,
  date_updated DATE,
  created_at TIMESTAMP NOT NULL DEFAULT NOW()
);
```

### Table: `company_industry_mapping`

```sql
CREATE TABLE company_industry_mapping (
  id UUID PRIMARY KEY,
  company_id UUID NOT NULL,
  damodaran_industry_name TEXT NOT NULL,
  confidence_score NUMERIC,
  mapping_method TEXT,
  user_overridden BOOLEAN DEFAULT FALSE,
  created_at TIMESTAMP NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);
```

Mapping methods:

```text
manual_user_selection
sic_naics_mapping
company_description_llm_mapping
sector_keyword_mapping
prior_saved_mapping
```

The agent should let the user override the industry mapping.

### Table: `relative_valuation_runs`

```sql
CREATE TABLE relative_valuation_runs (
  id UUID PRIMARY KEY,
  company_id UUID NOT NULL,
  valuation_run_id UUID,
  country TEXT NOT NULL,
  industry_name TEXT NOT NULL,
  selected_methods JSONB NOT NULL,
  input_financials JSONB NOT NULL,
  benchmark_metrics JSONB NOT NULL,
  output_values JSONB NOT NULL,
  diagnostics JSONB NOT NULL,
  created_at TIMESTAMP NOT NULL DEFAULT NOW()
);
```

---

## Parser and ingestion rules

### Rule 1: Detect the real header row

Do not hardcode one universal header row. Use detection.

```python
header_markers = ["Industry Name", "Industry name", "Country"]
```

For most India files, the header row is 8. For `vebitdaIndia.xls`, the detailed header row is 9. For `countrystats.xls`, the header row is 9.

### Rule 2: Preserve metadata

Extract these fields where present:

```text
date_updated
created_by
what_is_this_data
home_page
data_website
companies_in_each_industry_url
variable_definitions_url
country_or_region
```

### Rule 3: Convert values consistently

| Raw value | Stored value |
|---|---|
| `NA` | `null` |
| blank | `null` |
| percentage shown as decimal | keep decimal, label unit `percent_decimal` |
| multiples | keep raw numeric, label unit `x` |
| dollar values | store in US dollars millions when file says `US $ millions` |

### Rule 4: Resolve duplicate columns in `vebitdaIndia.xls`

`vebitdaIndia.xls` repeats the same labels under different groups. The parser must name them explicitly.

```text
positive_ebitda_ev_ebitda_rd
positive_ebitda_ev_ebitda
positive_ebitda_ev_ebit
positive_ebitda_ev_ebit_after_tax
all_firms_ev_ebitda_rd
all_firms_ev_ebitda
all_firms_ev_ebit
all_firms_ev_ebit_after_tax
```

### Rule 5: Attach sample size to every metric

The sample size is not a side detail. It should appear in UI and diagnostics.

Example:

```text
EV/EBITDA: 15.99x, based on 4,520 Indian companies at country level.
Industry EV/EBITDA: 17.01x, based on 24 Advertising firms.
```

### Rule 6: Flag low reliability benchmarks

Create `benchmark_reliability_score` from:

| Factor | Risk |
|---|---|
| Sample size below 10 | weak benchmark |
| High money-losing share | PE unreliable |
| `NA` values | method unavailable |
| Extreme multiple | outlier-prone |
| Financial services industry | EV multiples often inappropriate |
| Negative or tiny denominator | multiple likely distorted |

Reliability categories:

```text
high
medium
low
not_applicable
```

---

## Backend service design

### 1. `DamodaranBenchmarkIngestionService`

Responsibilities:

```text
- Read uploaded Damodaran files.
- Detect metadata, country, date, and header row.
- Normalize industry names.
- Convert all metrics into long format.
- Store source and import metadata.
- Run validation checks.
```

Core functions:

```ts
parseDamodaranWorkbook(filePath: string): ParsedDamodaranWorkbook
extractDatasetMetadata(workbook: Workbook): DatasetMetadata
findHeaderRow(sheet: Sheet): number
normalizeMetricName(rawColumn: string, context?: string): string
normalizeIndustryMetrics(rows: RawRow[]): IndustryMetric[]
saveBenchmarkSnapshot(parsed: ParsedDamodaranWorkbook): Promise<void>
```

### 2. `RelativeValuationBenchmarkService`

Responsibilities:

```text
- Retrieve industry and country benchmark metrics.
- Return only relevant metrics for company type.
- Attach reliability scores.
- Provide industry comparison tables.
```

Core functions:

```ts
getIndustryBenchmarks(country: string, industryName: string): Promise<IndustryBenchmarkSet>
getCountryMarketStats(country: string): Promise<CountryMarketStats>
getRecommendedMultiples(companyProfile: CompanyProfile): RecommendedMultiple[]
scoreBenchmarkReliability(metric: BenchmarkMetric): BenchmarkReliability
```

### 3. `RelativeValuationRunService`

Responsibilities:

```text
- Run relative valuation using selected multiples.
- Convert between enterprise value and equity value.
- Calculate per-share estimates.
- Produce diagnostics.
```

Core formulas:

```text
Enterprise Value from EV/Sales = Revenue × EV/Sales
Enterprise Value from EV/EBITDA = EBITDA × EV/EBITDA
Enterprise Value from EV/EBIT = EBIT × EV/EBIT
Equity Value from PE = Net Income × PE
Equity Value from PBV = Book Equity × PBV
Equity Value from Firm Value = Enterprise Value - Debt + Cash + Non-operating Assets - Minority Interest
Value per share = Equity Value / Diluted Shares Outstanding
```

### 4. `ValuationDiagnosticsService`

Responsibilities:

```text
- Compare DCF-implied multiples to industry benchmarks.
- Warn when valuation requires unjustified premium.
- Explain what assumptions must be true.
- Distinguish cheap from low-quality.
```

Diagnostic examples:

```text
- DCF implies EV/Sales 2.5x vs industry 1.4x.
- DCF implies PE 45x vs industry forward PE 25x.
- Company has lower PE but lower expected growth and lower ROIC, so discount may be justified.
- Company has higher EV/EBITDA but materially higher margins and ROIC, so premium may be justified.
```

---

## API design

### `GET /api/valuation/benchmarks/countries`

Returns all countries available in `countrystats`.

### `GET /api/valuation/benchmarks/countries/:country`

Returns market-level stats.

Example output:

```json
{
  "country": "India",
  "firmCount": 4520,
  "medianCurrentPE": 25.59,
  "medianTrailingPE": 24.81,
  "medianForwardPE": 28.04,
  "medianPBV": 2.15,
  "medianEVEBITDA": 15.99,
  "medianEVSales": 2.02,
  "dividendYield": 0.0115,
  "dateUpdated": "2026-01-05"
}
```

### `GET /api/valuation/benchmarks/industries?country=India`

Returns list of available Damodaran industry names.

### `GET /api/valuation/benchmarks/industries/:industryName?country=India`

Returns all benchmark metrics for one industry.

### `POST /api/valuation/relative/run`

Input:

```json
{
  "companyId": "...",
  "country": "India",
  "industryName": "Auto Parts",
  "financials": {
    "revenue": 1000,
    "ebitda": 150,
    "ebit": 100,
    "netIncome": 75,
    "bookEquity": 500,
    "investedCapital": 800,
    "debt": 200,
    "cash": 50,
    "dilutedShares": 100
  },
  "methods": ["ev_ebitda", "ev_sales", "pe", "pbv"]
}
```

Output:

```json
{
  "industryName": "Auto Parts",
  "relativeValues": [
    {
      "method": "EV/EBITDA",
      "benchmarkMultiple": 23.17,
      "enterpriseValue": 3475.2,
      "equityValue": 3325.2,
      "valuePerShare": 33.25,
      "reliability": "medium"
    }
  ],
  "range": {
    "low": 24.1,
    "base": 31.4,
    "high": 38.8
  },
  "diagnostics": []
}
```

### `POST /api/valuation/diagnostics/implied-multiples`

Input:

```json
{
  "enterpriseValue": 5000,
  "equityValue": 4200,
  "financials": {
    "revenue": 1000,
    "ebitda": 200,
    "ebit": 120,
    "netIncome": 80,
    "bookEquity": 900,
    "investedCapital": 1100
  },
  "country": "India",
  "industryName": "Auto Parts"
}
```

Output:

```json
{
  "impliedMultiples": {
    "evSales": 5.0,
    "evEbitda": 25.0,
    "evEbit": 41.67,
    "pe": 52.5,
    "pbv": 4.67,
    "evInvestedCapital": 4.55
  },
  "benchmarkComparison": [],
  "warnings": []
}
```

---

## Frontend requirements

### 1. Relative Valuation Panel

The company valuation page should include a section called:

```text
Relative Pricing Benchmarks
```

It should show:

| Component | Purpose |
|---|---|
| Industry selector | User can confirm or override Damodaran industry |
| Country selector | Defaults to India for these files |
| Multiples table | Shows industry metrics and sample size |
| Method recommendation card | Explains which multiples matter for this company |
| Relative value range | Low/base/high pricing range |
| DCF implied multiple comparison | Shows whether DCF output is market-plausible |
| Warnings | Flags unreliable or inappropriate multiples |

### 2. Benchmark table

Suggested columns:

```text
Metric
Industry value
Country median
Company actual
DCF implied
Reliability
Interpretation
```

Example:

| Metric | Industry | India median | Company | DCF implied | Reliability | Interpretation |
|---|---:|---:|---:|---:|---|---|
| EV/EBITDA | 15.99x | 15.99x | 12.0x | 20.0x | Medium | DCF assumes premium pricing |
| PE | 25.59x | 25.59x | 18.0x | 32.0x | Low | PE may be distorted by earnings cycle |

### 3. Warning language

Use direct warnings, not vague tooltips.

Examples:

```text
PE is unreliable here because 40% of the industry is money-losing.
```

```text
EV/EBITDA may overstate cheapness because this is a capital-intensive business.
```

```text
PBV is only meaningful if paired with ROE. A low PBV can be deserved when ROE is weak.
```

```text
The DCF value implies a much higher EV/Sales than the industry. The valuation needs a strong target margin story.
```

---

## Agent behavior rules

### Rule 1: Never equate low multiple with undervaluation

Bad:

```text
The company is undervalued because it trades at 12x PE versus the industry at 20x.
```

Good:

```text
The company trades at a PE discount to the industry. To judge whether that discount is attractive, we need to compare expected growth, ROE, margins, leverage, reinvestment needs, and risk.
```

### Rule 2: Always explain why a multiple was selected

Example:

```text
I am using EV/EBITDA as the main relative valuation method because this is a profitable operating company and EV/EBITDA avoids differences in leverage. I am using PE only as a secondary check because net income can be affected by capital structure and one-time items.
```

### Rule 3: Always show sample size and data date

Example:

```text
The benchmark comes from Damodaran's India dataset updated on 2026-01-05 and includes 120 Auto Parts firms.
```

### Rule 4: Always separate value and price

Relative valuation is pricing. DCF is intrinsic value.

The UI should label outputs accordingly:

```text
Intrinsic DCF value
Relative pricing estimate
Market-implied expectation
```

### Rule 5: Use country medians only as background

Industry benchmarks should be primary. Country medians should be context.

Bad:

```text
The stock should trade at India's median PE.
```

Good:

```text
The stock trades above the India market median, but the more relevant comparison is its own industry group.
```

---

## Recommended scoring logic

The agent can generate a qualitative relative valuation score.

### Inputs

```text
multiple_discount_or_premium
company_growth_vs_industry_growth
company_margin_vs_industry_margin
company_roe_vs_industry_roe
company_roic_vs_industry_roic
leverage_vs_industry
money_losing_industry_share
benchmark_sample_size
```

### Output categories

```text
possibly_underpriced
fairly_priced
possibly_overpriced
inconclusive
not_applicable
```

### Scoring principles

| Situation | Interpretation |
|---|---|
| Lower multiple + better fundamentals | Potentially underpriced |
| Lower multiple + worse fundamentals | Discount may be deserved |
| Higher multiple + better fundamentals | Premium may be justified |
| Higher multiple + worse fundamentals | Potentially overpriced |
| Weak sample or high loss share | Inconclusive |

The score should never be treated as an investment recommendation by itself.

---

## Testing plan

### Parser tests

```text
- Correctly detects header row in peIndia.xls.
- Correctly detects header row 9 in vebitdaIndia.xls.
- Converts NA to null.
- Keeps percentages as decimals.
- Preserves source date 2026-01-05.
- Stores sample size for every metric.
- Correctly separates positive EBITDA and all-firm EV multiples.
```

### Relative valuation tests

```text
- EV/EBITDA calculation uses enterprise value, not equity value.
- PE calculation uses equity value, not enterprise value.
- Equity value from EV subtracts debt and adds cash.
- Per-share value uses diluted shares.
- Negative EBITDA prevents EV/EBITDA valuation unless user explicitly overrides.
- Financial services companies default to PBV/ROE.
```

### Diagnostic tests

```text
- Low PE with lower growth does not produce automatic undervaluation.
- High EV/Sales with weak margins triggers warning.
- DCF-implied multiple above benchmark triggers assumption challenge.
- Sample size below 10 lowers benchmark reliability.
- High money-losing percentage lowers PE reliability.
```

---

## Codex implementation checklist

### Phase 1: Ingestion

- [ ] Add parser for Damodaran `.xls` or converted `.xlsx` benchmark files.
- [ ] Store dataset metadata.
- [ ] Normalize industry metrics into long format.
- [ ] Normalize country-level stats into `country_market_stats`.
- [ ] Add tests for each Batch 01 file.
- [ ] Add seed/import command:

```bash
python scripts/import_damodaran_benchmarks.py --country India --input-dir data/damodaran/india
```

### Phase 2: Benchmark retrieval

- [ ] Add API route for available countries.
- [x] Add active API route for country stats with source provenance.
- [ ] Add API route for available industries.
- [ ] Add API route for one industry's full benchmark set.
- [ ] Add reliability scoring.

### Phase 3: Relative valuation calculations

- [ ] Add EV/Sales valuation.
- [ ] Add EV/EBITDA valuation.
- [ ] Add EV/EBIT valuation.
- [ ] Add PE valuation.
- [ ] Add PBV valuation.
- [ ] Add enterprise-to-equity bridge.
- [ ] Add value per share calculation.
- [ ] Add low/base/high range using selected multiples.

### Phase 4: DCF diagnostics

- [ ] Calculate DCF-implied multiples.
- [ ] Compare implied multiples to industry benchmarks.
- [ ] Generate warnings.
- [ ] Show what must be true for the valuation premium or discount to be justified.

### Phase 5: UI

- [ ] Add industry selector.
- [ ] Add benchmark table.
- [ ] Add relative value range card.
- [ ] Add DCF-implied multiple comparison.
- [ ] Add warning and diagnostic panel.
- [ ] Add source date and sample size display.

---

## What not to build yet

Do not build these in Batch 01:

```text
- Full DCF forecasting engine
- R&D capitalization engine
- Lease capitalization engine
- Country risk premium engine
- Macro duration model
- Real options valuation
- Automated broker-style comparable company selection
- ML-based multiple prediction
```

Those belong in later batches.

Batch 01 should stay focused: **ingest benchmarks, retrieve benchmarks, run relative valuation, and diagnose DCF output against market pricing.**

---

## Next batch recommendation

The next batch should be:

```text
Batch 02: DCF Fundamentals, Growth, Margins, ROIC, and Reinvestment
```

Files to analyze next:

```text
marginIndia.xls
capexIndia.xls
wcdataIndia.xls
roeIndia.xls
fundgrIndia.xls
fundgrEBIndia.xls
histgrIndia.xls
finflowsIndia.xls
```

That batch will let the agent move from pricing to Damodaran-style intrinsic valuation assumptions.
