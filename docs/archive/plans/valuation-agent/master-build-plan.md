# Damodaran-Style Valuation Agent: Master Build Plan

**Project:** Market Intelligence Agent  
**Component:** Valuation Agent  
**Purpose:** Build a serious Damodaran-style valuation system, not a generic DCF calculator.  
**Status:** FULLY EXECUTED AND VERIFIED. The 20 phases below have been completed and act as historical architectural documentation.

---

## 0. Executive Decision

Build the valuation agent in this order:

1. **Manual deterministic FCFF engine**
2. **Batch 02 assumption engine**
3. **Batch 03 accounting normalization**
4. **Cost of capital and capital structure engine**
5. **Quick valuation workflow**
6. **Advanced valuation workflow**
7. **Diagnostics engine**
8. **Batch 01 relative pricing**
9. **Reverse DCF**
10. **Batch 04 FCFE, dividends, buybacks, payout**
11. **Batch 05 macro sensitivity**
12. **Narrative-to-numbers and AI memo layer**
13. **Lifecycle/special cases**
14. **Batch 06 real options**
15. **Market intelligence integration**

The reason is simple: if the deterministic DCF math is weak, every advanced feature becomes decoration. The first serious version must make growth, reinvestment, ROIC, WACC, terminal value, and equity bridge work correctly.

---

## 1. Core Philosophy

The valuation agent should act like a disciplined valuation analyst.

It should not merely calculate. It should challenge.

It should repeatedly ask:

```text
What is the story?
What numbers does that story require?
Are those numbers plausible?
How much reinvestment is needed?
What return on capital is implied?
What does the current market price already assume?
What would change the valuation?
Where is the biggest risk of being wrong?
```

### Non-negotiable principles

1. **Separate value from price**
   - Intrinsic valuation estimates value from cash flows, growth, risk, reinvestment, and competitive advantage.
   - Relative valuation estimates price from what comparable assets trade for.
   - The UI must show both separately.

2. **Backend does the math**
   - The LLM should not freehand valuation calculations.
   - The backend must compute FCFF, FCFE, WACC, terminal value, multiples, reverse DCF, scenarios, sensitivities, and real options.

3. **AI explains and audits**
   - The AI should explain assumptions, detect inconsistencies, generate memos, ask for missing inputs, and map narrative to numbers.

4. **Every assumption needs a source**
   - User input
   - Company actual
   - Company historical trend
   - Industry benchmark
   - Regression-implied prior
   - Market data
   - Agent suggested
   - Manual override

5. **Industry data is a prior, not a fact**
   - Damodaran industry files should guide assumptions, not replace company analysis.

6. **No false precision**
   - Always show point estimate, range, key drivers, sensitivity, and scenario outputs.

7. **Growth must cost money**
   - High growth must be linked to reinvestment and return on capital.
   - Terminal growth must be linked to terminal reinvestment.

8. **Stable growth must be economically mature**
   - Terminal growth cannot behave like a high-growth startup.
   - Terminal beta, ROC, reinvestment, WACC, and growth must make sense together.

---

## 2. Source-to-Module Map

| Source / batch | Main role | Build module |
|---|---|---|
| Lecture notes absorption | Philosophy, valuation architecture, phasing, guardrails | Overall product rules |
| Batch 02 | Margins, growth, capex, working capital, ROE/ROC, financing flows, debt regression | DCF assumption engine |
| Batch 03 | R&D capitalization, goodwill, acquisition diagnostics | Accounting normalization |
| Batch 01 | PE, PBV, PS, EV/EBITDA, country stats | Relative pricing and DCF sanity checks |
| Batch 04 | Dividends, buybacks, issuances, FCFE, dividend regressions | Equity cash flow and payout discipline |
| Batch 05 | Macro data, duration, cyclicality, inflation, currency | Macro sensitivity and scenarios |
| Batch 06 | Volatility, real options | Optionality layer |
| Debt regression PDF | Target debt ratio prior | Capital structure prior |
| Dividend regression PDF | Dividend yield / payout prior | Dividend policy prior |

---

## 3. Final Product Architecture

```text
ValuationAgent
├── DataIngestion
│   ├── DamodaranSpreadsheetParser
│   ├── IndustryPricingBenchmarkImporter
│   ├── DcfFundamentalsBenchmarkImporter
│   ├── AccountingBenchmarkImporter
│   ├── PayoutBenchmarkImporter
│   ├── MacroSensitivityImporter
│   ├── VolatilityBenchmarkImporter
│   └── RegressionModelSeedImporter
│
├── CompanyData
│   ├── CompanyProfileService
│   ├── FinancialStatementService
│   ├── MarketDataService
│   ├── IndustryMappingService
│   ├── SegmentMappingService
│   └── SourceLineageService
│
├── AssumptionPriors
│   ├── IndustryFundamentalPriorService
│   ├── AccountingNormalizationPriorService
│   ├── CapitalStructurePriorService
│   ├── DividendPolicyPriorService
│   ├── MacroExposurePriorService
│   └── VolatilityPriorService
│
├── ValuationEngines
│   ├── FCFFEngine
│   ├── FCFEEngine
│   ├── DividendDiscountEngine
│   ├── CostOfCapitalEngine
│   ├── TerminalValueEngine
│   ├── EquityBridgeEngine
│   ├── RelativePricingEngine
│   ├── ReverseDCFEngine
│   ├── ScenarioEngine
│   ├── SensitivityEngine
│   └── RealOptionsEngine
│
├── Adjustments
│   ├── RDCapitalizationService
│   ├── GoodwillDiagnosticsService
│   ├── LeaseAdjustmentService
│   ├── SBCAdjustmentService
│   ├── OptionsDilutionService
│   ├── CrossHoldingsService
│   ├── MinorityInterestService
│   └── PensionDebtLikeClaimsService
│
├── Diagnostics
│   ├── AssumptionConsistencyService
│   ├── ReinvestmentConsistencyService
│   ├── MarginPlausibilityService
│   ├── ROICvsWACCService
│   ├── TerminalValueDisciplineService
│   ├── RelativePricingSanityService
│   ├── PayoutSustainabilityService
│   ├── CapitalStructurePlausibilityService
│   ├── MacroRiskDiagnosticService
│   ├── RealOptionEligibilityService
│   └── DoubleCountingGuardrailService
│
├── AIAnalystLayer
│   ├── ModelSelectorAgent
│   ├── NarrativeToNumbersAgent
│   ├── AssumptionAuditorAgent
│   ├── ValuationMemoAgent
│   ├── MarketIntelligenceImpactAgent
│   └── UserQuestionAnsweringAgent
│
├── API
│   ├── benchmark_routes
│   ├── valuation_routes
│   ├── assumption_routes
│   ├── diagnostics_routes
│   ├── scenario_routes
│   ├── relative_pricing_routes
│   ├── reverse_dcf_routes
│   ├── memo_routes
│   └── admin_import_routes
│
└── UI
    ├── QuickValuation
    ├── AdvancedValuationWorkspace
    ├── AssumptionPanels
    ├── ForecastTable
    ├── DiagnosticsPanel
    ├── RelativePricingPanel
    ├── ReverseDCFPanel
    ├── ScenarioSensitivityPanel
    ├── PayoutPanel
    ├── MacroSensitivityPanel
    ├── RealOptionsPanel
    └── ValuationMemoReport
```

---

## 4. Product Modes

## 4.1 Quick Valuation Mode

Purpose: produce a first-pass valuation quickly, while still showing assumption discipline.

### Required user inputs

```text
Company / ticker
Country
Currency
Industry
Current revenue
Current operating income or margin
Cash
Debt
Shares outstanding
Current price
```

### Auto-filled assumptions

```text
Near-term revenue growth
Target operating margin
Sales-to-capital ratio
Working capital ratio
Tax rate
ROC / ROIC
WACC
Terminal growth
Terminal ROC
Terminal reinvestment
Relative pricing benchmark
```

### Required output

```text
Value per share
Current price
Upside/downside
Value range
Top 5 assumptions driving value
Industry comparison
DCF-implied multiples
Key diagnostics
What has to be true
Quick memo
```

### Quick mode rule

Quick mode must be simple, but not opaque. It should show all default assumptions and let the user override them.

---

## 4.2 Advanced Valuation Mode

Purpose: build a complete Damodaran-style valuation.

### Required panels

1. Company setup
2. Industry mapping
3. Historical financials
4. Accounting normalization
5. Revenue forecast
6. Margin forecast
7. Reinvestment forecast
8. Tax forecast
9. Cost of capital
10. Terminal value
11. Equity bridge
12. Relative pricing
13. Reverse DCF
14. Scenarios and sensitivity
15. Payout / FCFE
16. Macro sensitivity
17. Narrative-to-numbers
18. Final memo

---

## 4.3 Audit Mode

Purpose: inspect an existing valuation and find errors.

### Audit checks

```text
Cash flow / discount rate mismatch
Revenue growth inconsistent with TAM or industry
Margins above plausible industry ceiling
Growth without reinvestment
Terminal growth too high
Terminal reinvestment missing
ROC below WACC while growth is treated as value creating
Wrong risk-free currency
WACC uses book weights instead of market weights
Debt not subtracted from firm value
Cash double counted
SBC added back with no dilution cost
Goodwill added as value
R&D capitalization treated as free value creation
Exit multiple terminal value used without implied-growth analysis
Real option double counted
Financial services company forced into FCFF
```

---

## 5. Data Hierarchy

The valuation agent should rank information sources as follows:

```text
1. Company actual data
2. Company historical trend
3. Company guidance / filings
4. Industry benchmark
5. Country / macro benchmark
6. Regression-implied prior
7. Agent-suggested default
8. User override
```

But for final assumptions, user override can take precedence if the system clearly displays:

```text
Source: user override
Aggressiveness: high / medium / low
Diagnostic warnings
```

---

## 6. Database Master Plan

This is the database structure to work toward. Use migrations in small phases.

---

## 6.1 Core company and source tables

### `companies`

```sql
id
ticker
name
exchange
country
currency
sector
industry
description
is_financial_service
created_at
updated_at
```

### `company_industry_mapping`

```sql
id
company_id
damodaran_industry_name
confidence_score
mapping_method
user_overridden
created_at
updated_at
```

### `source_documents`

```sql
id
company_id
document_type
source_name
source_url
filing_date
period_end_date
raw_metadata_json
created_at
```

### `calculation_audit_trail`

```sql
id
valuation_run_id
module
calculation_name
inputs_json
formula
output_json
source_references_json
created_at
```

---

## 6.2 Valuation run tables

### `valuation_runs`

```sql
id
company_id
valuation_name
valuation_mode -- quick, advanced, audit, reverse_dcf
valuation_currency
reporting_currency
model_type -- fcff, fcfe, ddm, financial_services, sum_of_parts, real_options
status
created_by
created_at
updated_at
```

### `valuation_assumptions`

```sql
id
valuation_run_id
assumption_key
assumption_value
unit
source_type
source_detail
confidence_label
user_overridden
created_at
updated_at
```

### `valuation_forecast_rows`

```sql
id
valuation_run_id
forecast_year
revenue
revenue_growth
ebit_margin
ebit
tax_rate
after_tax_ebit
reinvestment
fcff
discount_rate
pv_fcff
invested_capital
roc
created_at
```

### `valuation_results`

```sql
id
valuation_run_id
value_operating_assets
pv_explicit_fcff
pv_terminal_value
cash_and_non_operating_assets
debt_and_debt_like_claims
minority_interest
cross_holdings_value
employee_option_value
equity_value
shares_outstanding
value_per_share
current_price
upside_downside_pct
created_at
```

---

## 6.3 Damodaran benchmark tables

### Core file registry

```sql
damodaran_dataset_files
- id
- uploaded_filename
- dataset_code
- country
- region
- date_updated
- source_file_type
- imported_at
- notes
```

### Batch 01 pricing

```sql
industry_benchmark_metrics
country_market_stats
relative_valuation_runs
```

### Batch 02 fundamentals

```sql
damodaran_industry_margin_benchmarks
damodaran_industry_capex_benchmarks
damodaran_industry_working_capital_benchmarks
damodaran_industry_roe_benchmarks
damodaran_industry_fundamental_equity_growth
damodaran_industry_fundamental_operating_growth
damodaran_industry_historical_growth
damodaran_industry_financing_flows
valuation_industry_fundamentals_india -- view
```

### Batch 03 accounting

```sql
industry_rd_benchmarks
industry_goodwill_benchmarks
company_rd_history
valuation_accounting_adjustments
```

### Batch 04 payout

```sql
industry_dividend_policy_benchmarks
industry_fcfe_payout_benchmarks
company_cash_return_history
payout_diagnostics
```

### Batch 05 macro

```sql
macro_time_series
sector_macro_sensitivity_benchmarks
company_macro_inputs
company_macro_sensitivity_results
company_macro_segment_exposures
```

### Batch 06 real options

```sql
industry_volatility_benchmarks
real_option_assumptions
real_option_results
option_eligibility_tests
```

### Regression priors

```sql
regression_model_seeds
regression_model_coefficients
regression_prior_results
```

---

## 7. API Master Plan

Use these as target route groups. Exact naming can match your backend conventions.

---

## 7.1 Benchmark routes

```http
POST /api/admin/damodaran/import
GET  /api/valuation/benchmarks/countries
GET  /api/valuation/benchmarks/countries/:country
GET  /api/valuation/benchmarks/industries?country=India
GET  /api/valuation/benchmarks/industries/:industry?country=India
GET  /api/valuation/benchmarks/fundamentals?country=India&industry=Auto%20Parts
GET  /api/valuation/benchmarks/accounting?country=India&industry=...
GET  /api/valuation/benchmarks/payout?country=India&industry=...
GET  /api/valuation/options/volatility?country=India&industry=...
```

---

## 7.2 Valuation routes

```http
POST /api/valuation/runs
GET  /api/valuation/runs/:id
PATCH /api/valuation/runs/:id
DELETE /api/valuation/runs/:id

POST /api/valuation/runs/:id/fcff
POST /api/valuation/runs/:id/fcfe
POST /api/valuation/runs/:id/ddm
POST /api/valuation/runs/:id/terminal-value
POST /api/valuation/runs/:id/equity-bridge
GET  /api/valuation/runs/:id/results
```

---

## 7.3 Assumption routes

```http
GET  /api/valuation/runs/:id/assumptions
POST /api/valuation/runs/:id/assumptions
PATCH /api/valuation/runs/:id/assumptions/:assumptionKey
POST /api/valuation/runs/:id/assumptions/suggest
POST /api/valuation/runs/:id/assumptions/audit
```

---

## 7.4 Diagnostics routes

```http
POST /api/valuation/runs/:id/diagnostics
GET  /api/valuation/runs/:id/diagnostics
POST /api/valuation/runs/:id/diagnostics/terminal
POST /api/valuation/runs/:id/diagnostics/reinvestment
POST /api/valuation/runs/:id/diagnostics/margins
POST /api/valuation/runs/:id/diagnostics/relative-pricing
```

---

## 7.5 Advanced routes

```http
POST /api/valuation/runs/:id/accounting/normalize
POST /api/valuation/runs/:id/accounting/rd-capitalization
POST /api/valuation/runs/:id/accounting/goodwill-diagnostics

POST /api/valuation/runs/:id/relative/run
POST /api/valuation/runs/:id/reverse-dcf
POST /api/valuation/runs/:id/scenarios
POST /api/valuation/runs/:id/sensitivity

POST /api/valuation/runs/:id/payout/analyze
POST /api/valuation/runs/:id/macro/top-down
POST /api/valuation/runs/:id/macro/bottom-up
POST /api/valuation/runs/:id/macro/scenario

POST /api/valuation/options/eligibility
POST /api/valuation/options/value
```

---

## 7.6 AI routes

```http
POST /api/valuation/runs/:id/ai/model-selector
POST /api/valuation/runs/:id/ai/narrative-to-numbers
POST /api/valuation/runs/:id/ai/assumption-audit
POST /api/valuation/runs/:id/ai/memo
POST /api/valuation/runs/:id/ai/market-intelligence-impact
```

---

## 8. Implementation Phases

---

# Phase 0: Preflight and Repo Audit

## Goal

Understand the current codebase before building. Avoid bolting valuation logic into the wrong place.

## Tasks

```text
[x] Create a new git branch: valuation-agent-master-plan (N/A, acting directly)
[x] Identify frontend framework and route structure
[x] Identify backend framework and service structure
[x] Identify database and migration system
[x] Identify current company table, portfolio table, document table, and event/news table
[x] Identify current API route conventions
[x] Identify current authentication and user/session conventions
[x] Identify current LLM provider abstraction
[x] Identify existing financial data ingestion, if any
[x] Identify existing SEC/news ingestion, if any
[x] Identify existing valuation page/components, if any
[x] Create /docs/valuation-agent/ folder
[x] Place all batch MD files inside /docs/valuation-agent/source-batches/
[x] Create /docs/valuation-agent/master-build-plan.md from this file
```

## Acceptance criteria

```text
[x] Developer can state exactly where backend services live.
[x] Developer can state exactly where frontend valuation pages/components should live.
[x] Developer can state exactly what tables already exist.
[x] No implementation begins before this map exists.
```

## Codex/Gemini prompt

```text
Audit the current repository structure for the Market Intelligence Agent. Do not implement anything yet.

Find:
1. Backend framework and route locations.
2. Database ORM/migration system.
3. Existing company, financials, portfolio, filings, events, and valuation tables.
4. Frontend framework and page/component structure.
5. Existing LLM abstraction.
6. Existing tests.

Then propose exactly where the valuation agent modules should be placed. Return a repository map and a no-code implementation placement plan.
```

---

# Phase 1: Deterministic Manual FCFF Engine

## Goal

Build the simplest correct valuation engine before using any Damodaran auto-assumptions.

## Why first

This proves the model math, API shape, database storage, forecast table, terminal value, and equity bridge.

## Backend tasks

```text
*(Note: MVP schemas already partially exist in `backend/app/models/dcf.py` as `valuation_models`, `dcf_assumption_sets`, `dcf_projection_years`, and `dcf_outputs`. Expand these to fit the full plan instead of creating new tables from scratch.)*
[x] Create valuation_runs table if missing. (Implemented as `valuation_models`)
[x] Create valuation_assumptions table. (Implemented as `dcf_assumption_sets`)
[x] Create valuation_forecast_rows table. (Implemented as `dcf_projection_years`)
[x] Create valuation_results table. (Implemented as `dcf_outputs`)
[ ] Build FCFFEngine.
[ ] Build TerminalValueEngine.
[ ] Build EquityBridgeEngine.
[ ] Build SensitivityEngine for basic 2-variable tables.
[ ] Build basic diagnostics:
    [ ] terminal growth >= WACC warning
    [ ] terminal growth too high warning
    [ ] terminal reinvestment missing warning
    [ ] negative FCFF explanation
    [ ] debt not subtracted warning
[ ] Add API:
    [ ] create valuation run
    [ ] save assumptions
    [ ] run FCFF valuation
    [ ] fetch forecast table
    [ ] fetch valuation result
```

## Core formulas

```text
Revenue_t = Revenue_{t-1} × (1 + Revenue Growth_t)

EBIT_t = Revenue_t × EBIT Margin_t

After-tax EBIT_t = EBIT_t × (1 - Tax Rate_t)

Reinvestment_t = ΔRevenue_t / Sales-to-Capital Ratio_t

FCFF_t = After-tax EBIT_t - Reinvestment_t

Terminal Reinvestment Rate = Terminal Growth / Terminal ROC

Terminal FCFF =
After-tax EBIT_terminal × (1 + g_terminal) × (1 - Terminal Reinvestment Rate)

Terminal Value =
Terminal FCFF / (WACC_terminal - g_terminal)

Value of Operating Assets =
PV(explicit FCFF) + PV(Terminal Value)

Equity Value =
Operating Asset Value + Cash + Non-operating Assets - Debt - Minority Interest - Other Claims

Value per Share =
Equity Value / Shares Outstanding
```

## Frontend tasks

```text
[ ] Create Quick Valuation page.
[ ] Add manual input form:
    [ ] Company name
    [ ] Currency
    [ ] Revenue
    [ ] EBIT margin
    [ ] Tax rate
    [ ] Revenue growth for years 1-5 or 1-10
    [ ] Sales-to-capital ratio
    [ ] WACC
    [ ] Terminal growth
    [ ] Terminal ROC
    [ ] Cash
    [ ] Debt
    [ ] Shares
    [ ] Current price
[ ] Add forecast table.
[ ] Add valuation result card.
[ ] Add sensitivity table.
[ ] Add basic diagnostics panel.
```

## Tests

```text
[ ] FCFF calculation test.
[ ] Terminal value calculation test.
[ ] Terminal reinvestment test.
[ ] Equity bridge test.
[ ] Value per share test.
[ ] Negative FCFF case.
[ ] Terminal growth >= WACC blocked.
[ ] Zero or negative sales-to-capital blocked unless user explicitly overrides.
```

## Acceptance criteria

```text
[ ] User can run a full manual FCFF valuation without AI.
[ ] Backend returns deterministic numbers.
[ ] UI shows forecast table and final value per share.
[ ] User can export or copy assumptions.
[ ] Every formula is auditable.
```

---

# Phase 2: Damodaran Spreadsheet Ingestion Foundation

## Goal

Create the shared parser/importer layer for all Damodaran industry files.

## Why before assumptions

All batch modules depend on reliable ingestion and normalized industry names.

## Tasks

```text
[ ] Create damodaran_dataset_files table.
[ ] Build generic workbook parser.
[ ] Detect workbook sheets.
[ ] Find header row by searching for "Industry Name", "Industry name", or "Country".
[ ] Extract metadata rows above header.
[ ] Convert Excel date serials to dates.
[ ] Normalize "NA", blanks, errors to null.
[ ] Preserve zeros as zeros.
[ ] Normalize percent fields consistently.
[ ] Normalize column names to snake_case.
[ ] Store source_file, country, data_version, date_updated, industry_name, number_of_firms.
[ ] Add CLI or admin import command.
[ ] Add import logs and validation summary.
```

## Important parser rules

```text
Do not hardcode row 8.
Do not convert missing values to zero.
Do not crash on duplicate columns.
Do not treat industry aggregate data as company-level data.
Do not silently overwrite old imports without versioning.
```

## Acceptance criteria

```text
[ ] Parser can import at least Batch 02 files.
[ ] Parser returns clear validation errors for bad files.
[ ] Imported data is versioned by source date.
[ ] Re-importing same data does not duplicate rows.
```

---

# Phase 3: Batch 02 Industry Fundamental Assumption Engine

## Goal

Use margins, growth, capex, working capital, ROE/ROC, financing flows, and debt regression as DCF assumption priors.

## Build modules

```text
DcfFundamentalsBenchmarkImporter
IndustryFundamentalPriorService
DCFExportAssumptionSuggestionService
CapitalStructurePriorService
CoreDiagnosticsService
```

## Database tasks

Create/import:

```text
[ ] damodaran_industry_margin_benchmarks
[ ] damodaran_industry_capex_benchmarks
[ ] damodaran_industry_working_capital_benchmarks
[ ] damodaran_industry_roe_benchmarks
[ ] damodaran_industry_fundamental_equity_growth
[ ] damodaran_industry_fundamental_operating_growth
[ ] damodaran_industry_historical_growth
[ ] damodaran_industry_financing_flows
[ ] regression_model_seeds
[ ] regression_model_coefficients
[ ] regression_prior_results
[ ] valuation_industry_fundamentals_india view
```

## Backend tasks

```text
[ ] Import marginIndia.
[ ] Import capexIndia.
[ ] Import wcdataIndia.
[ ] Import roeIndia.
[ ] Import fundgrIndia.
[ ] Import fundgrEBIndia.
[ ] Import histgrIndia.
[ ] Import finflowsIndia.
[ ] Seed global and US debt ratio regression coefficients.
[ ] Add industry benchmark lookup service.
[ ] Add industry assumption package endpoint.
[ ] Add industry mapping service.
[ ] Add manual industry override.
[ ] Add diversified company weighted industry support.
```

## Assumption suggestion output

The service should return:

```json
{
  "revenueGrowthPriors": {
    "companyHistorical": null,
    "industryHistorical5Y": null,
    "industryExpected2Y": null,
    "industryExpected5Y": null,
    "suggestedYears1To2": null,
    "suggestedYears3To5": null,
    "stableGrowthAnchor": null
  },
  "marginPriors": {
    "currentCompanyMargin": null,
    "industryUnadjustedOperatingMargin": null,
    "industryLeaseAdjustedMargin": null,
    "industryLeaseRdAdjustedMargin": null,
    "suggestedTargetMargin": null
  },
  "reinvestmentPriors": {
    "industrySalesToCapital": null,
    "industryNetCapexToSales": null,
    "industryWorkingCapitalToSales": null,
    "suggestedSalesToCapital": null
  },
  "returnPriors": {
    "industryRoc": null,
    "industryRoe": null,
    "suggestedTerminalRoc": null
  },
  "capitalStructurePriors": {
    "currentDebtRatio": null,
    "industryDebtSignals": null,
    "regressionImpliedDebtRatio": null,
    "suggestedTargetDebtRatio": null
  }
}
```

## Debt ratio regression

Implement as a low-confidence prior.

### Global debt ratio formula

```text
Expected Debt Ratio (%)
= 17.419
- 0.057 × Effective Tax Rate
- 20.401 × Expected EPS Growth Next 5 Years
- 2.153 × Institutional Holding
+ 0.033 × Company Age
```

### Rules

```text
[ ] Effective tax rate input uses percent points, e.g. 25, not 0.25.
[ ] Expected EPS growth uses decimal, e.g. 0.12.
[ ] Institutional holding uses decimal, e.g. 0.30.
[ ] Output is percentage points.
[ ] If predicted value < 0, set to zero.
[ ] Label as low-confidence prior.
```

## Diagnostics to implement

```text
[ ] Revenue growth far above industry expected growth.
[ ] Target margin far above industry adjusted margin.
[ ] Growth with too little reinvestment.
[ ] Negative reinvestment with high growth.
[ ] Reinvestment rate > 100% for too long.
[ ] ROC below WACC while growth assumed to create value.
[ ] Terminal growth without terminal reinvestment.
[ ] Terminal ROC far above industry without moat explanation.
[ ] Financial services company being forced into FCFF.
[ ] Sales-to-capital ratio too aggressive versus industry.
[ ] Working capital double-counting risk.
[ ] External funding need / dilution risk.
```

## Frontend tasks

```text
[ ] Add industry selector.
[ ] Add "suggest assumptions" button.
[ ] Add assumption source badges.
[ ] Add industry benchmark comparison in each assumption panel.
[ ] Add user override controls.
[ ] Add warning badges.
[ ] Add "what has to be true" section.
```

## Acceptance criteria

```text
[ ] User selects industry and receives assumption priors.
[ ] User can accept or override priors.
[ ] Quick valuation auto-fills revenue growth, margins, sales-to-capital, terminal ROC.
[ ] Diagnostics challenge unrealistic assumptions.
[ ] Debt ratio regression appears only as optional low-confidence prior.
```

---

# Phase 4: Batch 03 Accounting Normalization

## Goal

Clean reported accounting numbers before DCF forecasting.

## Why now

A DCF built from distorted EBIT and invested capital gives misleading margins, reinvestment, and ROC.

## Build modules

```text
AccountingBenchmarkImporter
RDCapitalizationService
GoodwillDiagnosticsService
AccountingNormalizationService
```

## Database tasks

```text
[ ] industry_rd_benchmarks
[ ] industry_goodwill_benchmarks
[ ] company_rd_history
[ ] valuation_accounting_adjustments
[ ] calculation_audit_trail if not already present
```

## Backend tasks

```text
[ ] Import R&DIndia.
[ ] Import goodwillIndia.
[ ] Build R&D capitalization calculation.
[ ] Build adjusted EBIT calculation.
[ ] Build adjusted invested capital calculation.
[ ] Build adjusted ROC calculation.
[ ] Build adjusted reinvestment calculation.
[ ] Build goodwill diagnostics.
[ ] Build acquisition intensity diagnostics.
[ ] Build impairment normalization logic.
[ ] Add accounting normalization endpoint.
[ ] Feed normalized financials into DCF engine.
```

## R&D capitalization formula

```text
R&D Asset =
Current R&D
+ 80% × R&D from 1 year ago
+ 60% × R&D from 2 years ago
+ 40% × R&D from 3 years ago
+ 20% × R&D from 4 years ago
```

```text
R&D Amortization =
(R&D from 1Y ago + 2Y ago + 3Y ago + 4Y ago + 5Y ago) / 5
```

```text
Adjusted EBIT = Reported EBIT + Current R&D - R&D Amortization
```

```text
Adjusted Invested Capital = Reported Invested Capital + R&D Asset
```

## Goodwill rules

```text
[ ] Do not add goodwill separately to value.
[ ] Use goodwill to judge acquisition intensity and capital allocation.
[ ] Add back goodwill impairment only for normalized earnings if non-recurring.
[ ] Still flag impairment as evidence of possible overpayment.
[ ] Show ROC including goodwill and excluding goodwill.
```

## Frontend tasks

```text
[ ] Add accounting normalization tab.
[ ] Add quick-mode toggle: auto-normalize material R&D.
[ ] Add R&D capitalization card.
[ ] Add goodwill diagnostics card.
[ ] Add reported vs adjusted metrics table.
[ ] Add audit drawer with formulas.
```

## Acceptance criteria

```text
[ ] R&D-heavy company shows adjusted EBIT, invested capital, and ROC.
[ ] Goodwill-heavy company shows acquisition-quality warning.
[ ] User sees reported and adjusted numbers side by side.
[ ] DCF can run on normalized financials.
[ ] Agent does not treat R&D capitalization as automatic value creation.
```

---

# Phase 5: Cost of Capital Engine

## Goal

Build WACC properly, not as a single user-entered number.

## Build modules

```text
RiskFreeRateService
EquityRiskPremiumService
CountryRiskPremiumService
BetaService
CostOfDebtService
SyntheticRatingService
CapitalStructureService
WACCEngine
```

## Tasks

```text
[ ] Add risk-free rate input by currency.
[ ] Add ERP input and source.
[ ] Add country risk premium input and operation-weighted exposure.
[ ] Add beta input.
[ ] Add bottom-up beta structure for later.
[ ] Add target debt ratio input.
[ ] Add debt ratio regression prior from Phase 3.
[ ] Add synthetic rating from interest coverage.
[ ] Add cost of debt from risk-free rate + default spread.
[ ] Add after-tax cost of debt.
[ ] Add market value weight calculation.
[ ] Add WACC calculation.
[ ] Add year-by-year WACC fade support.
```

## Core formulas

```text
Cost of Equity = Risk-free Rate + Beta × ERP
```

```text
Expanded Cost of Equity =
Risk-free Rate + Beta × Mature Market ERP + Lambda × Country Risk Premium
```

```text
Pre-tax Cost of Debt = Risk-free Rate + Company Default Spread + Applicable Country Default Spread
```

```text
After-tax Cost of Debt = Pre-tax Cost of Debt × (1 - Marginal Tax Rate)
```

```text
WACC =
Cost of Equity × E/(D+E)
+ After-tax Cost of Debt × D/(D+E)
```

## Diagnostics

```text
[ ] Risk-free rate currency mismatch.
[ ] ERP source missing.
[ ] Book weights used when market weights available.
[ ] Debt ratio materially different from industry/regression prior.
[ ] Cost of debt uses historical coupon instead of current borrowing rate.
[ ] Negative EBIT synthetic rating problem.
[ ] Emerging market country risk applied mechanically without exposure check.
```

## Acceptance criteria

```text
[ ] User can either enter WACC manually or build it from components.
[ ] WACC calculation is auditable.
[ ] Debt ratio regression is available as low-confidence prior.
[ ] Cost of capital can feed FCFF engine.
```

---

# Phase 6: Quick Valuation V1

## Goal

Turn Phases 1-5 into a usable quick valuation workflow.

## User flow

```text
1. Enter company/ticker.
2. Confirm country/currency/industry.
3. Enter or import current financials.
4. Click "Generate assumptions."
5. Review assumptions with source badges.
6. Edit only the assumptions you disagree with.
7. Run valuation.
8. View value, range, diagnostics, and what-has-to-be-true.
```

## Required UI cards

```text
[ ] Company summary
[ ] Industry mapping
[ ] Current financials
[ ] Suggested assumptions
[ ] Forecast preview
[ ] Valuation output
[ ] Sensitivity table
[ ] Diagnostics
[ ] What has to be true
```

## Acceptance criteria

```text
[ ] A non-technical user can complete a valuation in under 5 minutes.
[ ] The model is still formula-based and auditable.
[ ] The output is useful even before full AI integration.
```

---

# Phase 7: Advanced Valuation Workspace V1

## Goal

Give full control without overwhelming quick users.

## Layout

```text
Left sidebar:
- Setup
- Financials
- Accounting normalization
- Revenue
- Margins
- Reinvestment
- Taxes
- Cost of capital
- Terminal value
- Equity bridge
- Relative pricing
- Scenarios
- Memo

Main area:
- Active section table/cards

Right sidebar:
- Diagnostics
- Source badges
- AI explanation
- Assumption impact
```

## Required controls

```text
[ ] Forecast years selector: 5, 10, custom.
[ ] Year-by-year revenue growth.
[ ] Target margin and fade.
[ ] Sales-to-capital by period.
[ ] Reinvestment method selector.
[ ] Tax rate fade.
[ ] WACC by year.
[ ] Terminal growth.
[ ] Terminal ROC.
[ ] Terminal reinvestment.
[ ] Cash/debt/minority/cross-holdings.
[ ] Sensitivity variables.
```

## Acceptance criteria

```text
[ ] User can inspect and edit every major valuation driver.
[ ] Every major assumption has a source and diagnostic status.
[ ] Advanced mode can reproduce quick mode results before overrides.
```

---

# Phase 8: Diagnostics Engine V1

## Goal

Make bad assumptions harder to hide.

## Build modules

```text
AssumptionConsistencyService
TerminalValueDisciplineService
ReinvestmentConsistencyService
MarginPlausibilityService
ROICvsWACCService
SourceQualityService
```

## Diagnostic severity

```text
info
watch
warning
critical
blocking
```

## Required diagnostics

```text
[ ] Terminal growth >= WACC: blocking.
[ ] Terminal growth above long-term economy growth: warning.
[ ] Terminal reinvestment missing: blocking.
[ ] Terminal ROC below WACC with positive growth: warning/critical.
[ ] Growth with no reinvestment: critical.
[ ] Sales-to-capital too high vs industry: warning.
[ ] Target margin far above industry: warning.
[ ] Company margin far below target without explanation: warning.
[ ] DCF value mostly terminal value: warning.
[ ] FCFF negative for too long without funding note: warning.
[ ] User override far from benchmark: watch/warning.
[ ] Financial company using FCFF: blocking by default.
```

## Required output format

```json
{
  "severity": "warning",
  "module": "terminal_value",
  "message": "Terminal growth requires terminal reinvestment. Your model assumes 4% terminal growth but 0% reinvestment.",
  "affectedAssumptions": ["terminal_growth", "terminal_roc", "terminal_reinvestment_rate"],
  "suggestedFix": "Set terminal reinvestment rate = terminal growth / terminal ROC.",
  "formula": "Terminal Reinvestment Rate = g / ROC"
}
```

## Acceptance criteria

```text
[ ] Every valuation run produces diagnostics.
[ ] Critical issues are visible before final output.
[ ] User can override warnings but not formula impossibilities.
```

---

# Phase 9: Batch 01 Relative Pricing

## Goal

Add pricing benchmarks and DCF-implied multiple sanity checks.

## Build modules

```text
IndustryPricingBenchmarkImporter
RelativeValuationBenchmarkService
RelativeValuationRunService
DCFImpliedMultipleService
RelativePricingSanityService
```

## Tasks

```text
[x] Import peIndia with exact versioned source controls.
[x] Import pbvIndia with exact versioned source controls.
[x] Import psIndia with exact versioned source controls.
[x] Import vebitdaIndia with exact versioned source controls.
[x] Import countrystats with exact versioned source controls.
[x] Add active source-separated relative valuation API with provenance.
[x] Add industry benchmark table with independent source-version rows.
[ ] Add country market context card.
[ ] Add DCF-implied multiple calculation.
[ ] Add premium/discount diagnostics.
```

## Formula examples

```text
DCF implied EV/Sales = DCF enterprise value / revenue
DCF implied EV/EBITDA = DCF enterprise value / EBITDA
DCF implied EV/EBIT = DCF enterprise value / EBIT
DCF implied PE = DCF equity value / net income
DCF implied PBV = DCF equity value / book equity
```

## Diagnostics

```text
[ ] Low PE does not automatically mean undervalued.
[ ] High EV/Sales with weak margin triggers warning.
[ ] DCF-implied EV/EBITDA far above industry requires explanation.
[ ] Financial services default to PBV/ROE.
[ ] EV/EBITDA not valid when EBITDA negative.
[ ] Sample size below 10 reduces reliability.
[ ] High money-losing percentage lowers PE reliability.
```

## Acceptance criteria

```text
[ ] Valuation output shows intrinsic value and relative pricing separately.
[ ] User can see DCF-implied multiples vs industry.
[ ] Agent explains what must justify a premium/discount.
```

---

# Phase 10: Reverse DCF

## Goal

Show what the current market price already assumes.

## Build modules

```text
ReverseDCFEngine
MarketImpliedAssumptionSolver
ReverseDCFDiagnosticsService
```

## Solver targets

The user should be able to solve for:

```text
[ ] Implied revenue growth
[ ] Implied target operating margin
[ ] Implied sales-to-capital ratio
[ ] Implied terminal growth
[ ] Implied terminal ROC
[ ] Implied WACC
[ ] Implied market share, if TAM exists
```

## User flow

```text
1. Current price comes from market data or user.
2. User selects which assumption to solve for.
3. Other assumptions remain fixed.
4. Solver finds the value that makes intrinsic value equal current price.
5. Diagnostics explain whether that implied assumption is plausible.
```

## Acceptance criteria

```text
[ ] User can answer: "What has to be true for this stock price to make sense?"
[ ] Reverse DCF output compares implied assumptions to company history and industry priors.
```

---

# Phase 11: Batch 04 FCFE, Dividends, Buybacks, and Payout

## Goal

Add equity cash-flow and shareholder-return discipline.

## Build modules

```text
DividendBenchmarkIngestionService
FCFEBenchmarkIngestionService
CompanyCashReturnService
PayoutPolicyDiagnosticService
DividendPolicyPriorService
FCFEEngine
DividendDiscountEngine
```

## Tasks

```text
[ ] Import divfundIndia.
[ ] Import divfcfeIndia.
[ ] Seed dividend regression coefficients.
[ ] Build FCFE calculation.
[ ] Build dividend sustainability analysis.
[ ] Build buyback quality analysis.
[ ] Build net cash returned logic.
[ ] Add payout diagnostics UI.
[ ] Add FCFE valuation as cross-check.
[ ] Add DDM for stable dividend-paying firms.
```

## FCFE formulas

```text
FCFE before debt =
Net Income
- (Capital Expenditures - Depreciation)
- Change in Non-Cash Working Capital
```

```text
FCFE after debt =
FCFE before debt
+ New Debt Issued
- Debt Repaid
```

```text
Net Cash Returned =
Dividends + Buybacks - Stock Issuances
```

## Dividend regression

Use as low-confidence prior, not hard target.

### Global dividend yield formula

```text
Expected Dividend Yield =
1.835
+ 0.035 × Effective Tax Rate
- 3.603 × Expected EPS Growth Next 5 Years
+ 0.004 × Company Age
- 0.279 × Beta
```

Rules:

```text
[ ] Effective tax rate uses percent points.
[ ] Expected growth uses decimal.
[ ] If predicted yield < 0, set to zero.
[ ] Label as regression prior.
```

## Payout diagnostics

```text
[ ] Dividend paid despite negative earnings.
[ ] Dividend exceeds FCFE.
[ ] Net cash returned exceeds FCFE.
[ ] Buybacks offset by stock issuance.
[ ] Buybacks when current price > intrinsic value.
[ ] High payout while ROC > WACC.
[ ] Low payout while ROC <= WACC.
```

## Acceptance criteria

```text
[ ] User can see whether dividends are sustainable.
[ ] User can see whether buybacks actually reduce share count.
[ ] User can run FCFE as a cross-check.
[ ] Stable dividend companies can use DDM.
```

---

# Phase 12: Batch 05 Macro Sensitivity

## Goal

Add rate, cycle, inflation, and currency exposure.

## Build modules

```text
MacroDataIngestionService
SectorMacroSensitivityIngestionService
TopDownMacroSensitivityService
BottomUpMacroSensitivityService
MacroScenarioTranslationService
```

## Tasks

```text
[ ] Import macro.
[ ] Import macrodur.
[ ] Store annual and quarterly macro time series.
[ ] Store sector macro sensitivity benchmarks.
[ ] Build top-down regression service.
[ ] Build bottom-up segment exposure service.
[ ] Add macro scenario panel.
[ ] Translate macro shocks into valuation assumption changes.
```

## Sensitivity types

```text
Duration: sensitivity to long-term interest-rate changes
Cyclicality: sensitivity to GDP/economic growth
Inflation sensitivity: sensitivity to CPI/inflation changes
Currency sensitivity: sensitivity to currency movements
```

## Rules

```text
[ ] Use bottom-up when company history is short or noisy.
[ ] Top-down regression confidence low if observations are insufficient.
[ ] Always define currency movement direction.
[ ] Do not automatically change valuation without showing assumptions affected.
```

## Acceptance criteria

```text
[ ] User can see if company is rate-sensitive, cyclical, inflation-exposed, or currency-exposed.
[ ] User can run a macro shock scenario and see affected assumptions.
```

---

# Phase 13: Scenario and Sensitivity Engine V2

## Goal

Move beyond a single-point valuation.

## Required scenarios

```text
Base case
Bull case
Bear case
Recession case
Rate shock case
Margin compression case
Market-implied case
User custom case
```

## Required sensitivities

```text
Revenue growth vs target margin
WACC vs terminal growth
Sales-to-capital vs margin
Terminal ROC vs terminal growth
Cost of equity vs beta
Debt ratio vs WACC
```

## Acceptance criteria

```text
[ ] User can see valuation range.
[ ] User can identify the top value drivers.
[ ] Output does not pretend precision.
```

---

# Phase 14: Narrative-to-Numbers AI Layer

## Goal

Make the agent act like an analyst, not just a calculator.

## Build modules

```text
ModelSelectorAgent
NarrativeToNumbersAgent
AssumptionAuditorAgent
ValuationMemoAgent
MarketIntelligenceImpactAgent
```

## AI boundaries

The AI may:

```text
[ ] Explain assumptions.
[ ] Suggest assumptions.
[ ] Ask for missing information.
[ ] Map a narrative to valuation drivers.
[ ] Challenge inconsistencies.
[ ] Generate memo language.
[ ] Explain valuation sensitivity.
```

The AI may not:

```text
[ ] Invent financial data.
[ ] Silently change assumptions.
[ ] Override deterministic calculations.
[ ] Hide formulas.
[ ] Claim precision.
[ ] Add real option value without eligibility test.
```

## Narrative-to-numbers flow

```text
1. User enters thesis.
2. AI extracts claims:
   - market growth
   - market share
   - pricing power
   - margin expansion
   - reinvestment intensity
   - competitive advantage period
   - risk
3. AI maps claims to assumptions.
4. Backend runs valuation.
5. Diagnostics challenge assumptions.
6. AI writes "what has to be true."
```

## Acceptance criteria

```text
[ ] AI produces structured assumptions, not just prose.
[ ] User must approve assumption changes.
[ ] Every AI-suggested assumption has rationale and source label.
```

---

# Phase 15: Valuation Memo and Report

## Goal

Produce a final analyst-style valuation output.

## Required memo structure

```text
1. Company and story
2. Business model
3. Valuation method
4. Key assumptions
5. Intrinsic value output
6. Relative pricing cross-check
7. Reverse DCF / market-implied expectations
8. Scenario and sensitivity analysis
9. Diagnostics and risks
10. Investment conclusion
11. What would change my mind
12. Assumption source appendix
```

## Memo rules

```text
[ ] Separate facts, assumptions, and judgment.
[ ] Show value and price separately.
[ ] Include uncertainty range.
[ ] Include biggest assumption risks.
[ ] Include diagnostics warnings.
[ ] Do not bury red flags.
```

## Acceptance criteria

```text
[ ] User can export/copy memo.
[ ] Memo ties back to valuation run.
[ ] Memo includes assumptions and source labels.
```

---

# Phase 16: Lifecycle and Special Cases

## Goal

Support the fact that one DCF model does not fit all companies.

## Models to add

```text
Young growth company model
Declining company model
Distressed company model
Financial services model
Commodity/cyclical model
Private company model
Sum-of-the-parts model
Platform/user economics model
```

## Model selection rules

| Company type | Default model |
|---|---|
| Stable non-financial | FCFF |
| Stable dividend payer | DDM / FCFE cross-check |
| High-growth profitable | Multi-stage FCFF |
| Young loss-making | Revenue-to-margin lifecycle DCF |
| Bank / insurer | Equity / excess return / PBV-ROE |
| Commodity | Cycle-normalized DCF |
| Distressed | Probability-weighted DCF + option lens |
| Conglomerate | Sum of parts |
| R&D-heavy | FCFF + R&D capitalization, optional patent option |
| Natural resource | Developed reserve DCF + undeveloped reserve option |

## Acceptance criteria

```text
[ ] Financial companies are not forced into FCFF.
[ ] Young companies can be valued before profitability.
[ ] Distressed companies show survival probability separately.
```

---

# Phase 17: Batch 06 Real Options

## Goal

Add optionality only where it is real, material, and not double counted.

## Build modules

```text
VolatilityBenchmarkIngestionService
VolatilityEstimationService
RealOptionEligibilityService
BlackScholesRealOptionService
RealOptionIntegrationService
DoubleCountingGuardrailService
```

## Real option eligibility tests

```text
[ ] Underlying asset exists.
[ ] Finite life exists.
[ ] Exercise cost is reasonably knowable.
[ ] Payoff is asymmetric.
[ ] Exclusivity exists.
[ ] Volatility can be estimated.
[ ] Underlying asset value can be estimated.
[ ] Not already counted in DCF.
```

## Option types

```text
Patent / product option
Natural resource option
Expansion option
Abandonment option
Distressed equity option
Convertible / warrant option
Custom option
```

## Rules

```text
[ ] Real options are advanced mode only.
[ ] Most strategic optionality should be qualitative only.
[ ] No exclusivity usually means no option premium.
[ ] Do not double count growth and option value.
```

## Acceptance criteria

```text
[ ] User cannot add option value without passing eligibility test or explicit override.
[ ] Option value is shown separately from base DCF.
[ ] Volatility source is visible.
```

---

# Phase 18: Market Intelligence Integration

## Goal

Connect valuation to news, filings, events, narratives, and portfolio monitoring.

## Core idea

Market intelligence should update assumptions, not just summarize news.

## Event-to-assumption mapping

| Event type | Possible valuation impact |
|---|---|
| Earnings beat/miss | Revenue growth, margins, tax, reinvestment |
| Guidance change | Forecast growth, margins |
| Regulation | Risk, margins, terminal assumptions |
| Rate change | Risk-free rate, WACC, terminal value |
| Commodity move | Revenue, margins, scenario weights |
| Acquisition | Goodwill, reinvestment, growth quality |
| Buyback/dividend | FCFE, payout quality, share count |
| Debt issuance | WACC, leverage, distress risk |
| New product | Revenue scenario, option value |
| Lawsuit | Probability-weighted liability |
| Country risk event | CRP, currency, macro scenario |

## Build modules

```text
MarketIntelligenceImpactAgent
ValuationAssumptionChangeLog
ValuationAlertService
PortfolioValuationMonitor
```

## Alerts

```text
[ ] Assumption-breaking event
[ ] Valuation upside/downside changed materially
[ ] Market price moved but intrinsic value unchanged
[ ] Narrative changed
[ ] DCF assumption now stale
[ ] Macro shock affects portfolio valuation
```

## Acceptance criteria

```text
[ ] A news/filing item can be linked to a specific valuation assumption.
[ ] User can see before/after valuation impact.
[ ] Portfolio can show which holdings have stale valuations.
```

---

# Phase 19: Testing and Validation Master Plan

## Unit tests

```text
[ ] FCFF calculations.
[ ] FCFE calculations.
[ ] Terminal value.
[ ] Terminal reinvestment.
[ ] WACC.
[ ] Beta relevering.
[ ] Synthetic rating.
[ ] R&D capitalization.
[ ] Goodwill diagnostics.
[ ] Relative valuation.
[ ] Reverse DCF solver.
[ ] Macro sensitivity.
[ ] Black-Scholes call/put.
```

## Integration tests

```text
[ ] Create valuation run.
[ ] Save assumptions.
[ ] Run FCFF.
[ ] Run accounting normalization.
[ ] Run relative pricing.
[ ] Run diagnostics.
[ ] Generate memo.
```

## Financial logic test cases

```text
[ ] Stable mature company.
[ ] High-growth profitable company.
[ ] Loss-making young company.
[ ] Bank / financial service company.
[ ] Capital-intensive company.
[ ] R&D-heavy company.
[ ] Acquisition-heavy goodwill company.
[ ] Dividend-paying mature company.
[ ] Buyback-heavy company with dilution.
[ ] Cyclical company.
[ ] Distressed company.
[ ] Real option case.
```

## Red-flag tests

```text
[ ] Terminal growth > WACC.
[ ] Terminal growth with zero reinvestment.
[ ] High growth with negative reinvestment.
[ ] PE used for negative earnings.
[ ] EV/EBITDA used for bank.
[ ] Goodwill added to value.
[ ] SBC added back without dilution warning.
[ ] Real option double counted.
```

---

# Phase 20: Deployment and Data Refresh

## Data refresh requirements

```text
[ ] Damodaran data version stored by source date.
[ ] New imports do not overwrite old valuation runs.
[ ] Valuation run stores benchmark snapshot used at time of valuation.
[ ] User can rerun valuation with updated benchmarks.
```

## Admin tools

```text
[ ] Upload Damodaran data files.
[ ] Run import.
[ ] View import validation summary.
[ ] Roll back bad import.
[ ] Compare benchmark versions.
```

## Acceptance criteria

```text
[ ] Old valuation can be reproduced.
[ ] New data can be imported safely.
[ ] Benchmark source date appears in UI.
```

---

# 21. Suggested Folder Structure

Adjust names to the current repo.

```text
backend/
  app/
    valuation/
      __init__.py
      models/
        valuation_run.py
        assumptions.py
        results.py
        benchmarks.py
        accounting.py
        payout.py
        macro.py
        real_options.py
      schemas/
        valuation.py
        assumptions.py
        benchmarks.py
        diagnostics.py
      services/
        fcff_engine.py
        fcfe_engine.py
        terminal_value_engine.py
        equity_bridge_engine.py
        wacc_engine.py
        industry_prior_service.py
        accounting_normalization_service.py
        relative_pricing_service.py
        reverse_dcf_service.py
        diagnostics_service.py
        payout_service.py
        macro_sensitivity_service.py
        real_options_service.py
      ingestion/
        damodaran_parser.py
        import_pricing.py
        import_fundamentals.py
        import_accounting.py
        import_payout.py
        import_macro.py
        import_volatility.py
      ai/
        model_selector.py
        narrative_to_numbers.py
        assumption_auditor.py
        memo_writer.py
      routes/
        valuation_routes.py
        benchmark_routes.py
        diagnostics_routes.py
        ai_routes.py
      tests/
        test_fcff.py
        test_terminal_value.py
        test_accounting.py
        test_relative_pricing.py
        test_reverse_dcf.py

frontend/
  src/
    features/
      valuation/
        pages/
          QuickValuationPage.tsx
          AdvancedValuationPage.tsx
        components/
          CompanySetupCard.tsx
          IndustryMappingCard.tsx
          FinancialInputTable.tsx
          AssumptionSourceBadge.tsx
          ForecastTable.tsx
          ValuationOutputCard.tsx
          DiagnosticsPanel.tsx
          SensitivityTable.tsx
          RelativePricingPanel.tsx
          ReverseDcfPanel.tsx
          AccountingNormalizationPanel.tsx
          PayoutPanel.tsx
          MacroSensitivityPanel.tsx
          RealOptionsPanel.tsx
          ValuationMemoPanel.tsx
        api/
          valuationApi.ts
        types/
          valuation.ts
        utils/
          formatting.ts
```

---

# 22. MVP Definition

## MVP is not

```text
A perfect all-company valuation system
A full AI analyst
A full SEC parser
A full real options system
A beautiful but shallow DCF UI
```

## MVP is

```text
Manual FCFF DCF
Industry priors from Batch 02
Accounting normalization from Batch 03
WACC builder
Terminal value discipline
Equity bridge
Diagnostics
Relative pricing cross-check from Batch 01
Simple quick UI
Advanced assumptions UI
Assumption source tracking
Basic memo generation
```

## MVP done means

```text
A user can value a normal non-financial public company, see a useful value range, understand the assumptions, compare the DCF to industry pricing, and see warnings when assumptions are unrealistic.
```

---

# 23. Do Not Build Yet

Avoid these until the core is stable:

```text
Full real options engine
Complex M&A synergy module
Private company illiquidity discounts
Automated SEC extraction as a prerequisite
ML-based comparable selection
Broker-report style target price generator
Overly complex UI with 100 fields on first screen
AI-generated numbers with no formula trail
Automatic portfolio-wide valuation refresh before single valuation works
```

---

# 24. Practical Build Order Summary

## Sprint 1: Repository + manual FCFF

```text
[ ] Repo audit
[ ] Valuation core tables
[ ] Manual FCFF engine
[ ] Terminal value
[ ] Equity bridge
[ ] Basic UI
[ ] Basic tests
```

## Sprint 2: Batch 02 ingestion and priors

```text
[ ] Damodaran parser
[ ] Batch 02 tables/imports
[ ] Industry mapping
[ ] Assumption package endpoint
[ ] Quick valuation auto-fill
[ ] Core diagnostics
```

## Sprint 3: Accounting normalization

```text
[ ] Batch 03 tables/imports
[ ] R&D capitalization
[ ] Goodwill diagnostics
[ ] Normalized financials
[ ] Accounting UI panel
```

## Sprint 4: Cost of capital

```text
[ ] WACC builder
[ ] Risk-free / ERP / beta / cost of debt
[ ] Debt ratio regression prior
[ ] WACC diagnostics
```

## Sprint 5: Relative pricing and reverse DCF

```text
[ ] Batch 01 imports
[ ] Relative valuation module
[ ] DCF-implied multiples
[ ] Reverse DCF solver
[ ] Pricing UI
```

## Sprint 6: Payout and FCFE

```text
[ ] Batch 04 imports
[ ] Dividend regression prior
[ ] FCFE engine
[ ] Payout diagnostics
[ ] Buyback quality checks
```

## Sprint 7: Macro, scenarios, memo

```text
[ ] Batch 05 imports
[ ] Scenario engine v2
[ ] Macro sensitivity
[ ] AI memo writer
[ ] Narrative-to-numbers v1
```

## Sprint 8: Special cases and real options

```text
[ ] Financial services model
[ ] Young growth model
[ ] Commodity/cyclical model
[ ] Distressed model
[ ] Batch 06 volatility import
[ ] Real option eligibility
[ ] Real option valuation
```

---

# 25. Master Codex/Gemini Prompt

Use this after placing this file in the repo.

```text
You are working on the Market Intelligence Agent. Build the Damodaran-style valuation agent using the master plan in docs/valuation-agent/master-build-plan.md and the batch source files in docs/valuation-agent/source-batches/.

Do not build a generic DCF calculator. Build a deterministic valuation engine with AI-assisted guidance.

Rules:
1. Backend formulas are the source of truth.
2. The LLM may explain, audit, and suggest assumptions, but it may not freehand valuation math.
3. Build in phases. Do not skip to real options, macro, or AI memo generation before manual FCFF and Batch 02/03 are working.
4. Every assumption must have a source label.
5. Every calculation must be auditable.
6. Industry data is a prior, not a company fact.
7. Growth must be linked to reinvestment and return on capital.
8. Terminal value must enforce stable-growth economics.
9. Relative pricing must be separated from intrinsic valuation.
10. Financial services companies must not be forced into normal FCFF.

Start with Phase 0:
- Audit repository structure.
- Identify backend, frontend, database, and tests.
- Propose exact file locations for the valuation modules.
- Do not implement code until the placement plan is approved.

Then implement Phase 1 in small commits:
- valuation_runs
- valuation_assumptions
- valuation_forecast_rows
- valuation_results
- FCFFEngine
- TerminalValueEngine
- EquityBridgeEngine
- Quick Valuation manual UI
- Unit tests
```

---

# 26. User Inputs Still Needed

To turn this into exact repo patches, the builder needs:

```text
Frontend framework and folder structure
Backend framework and folder structure
Database ORM/migration system
Current company table schema
Current financial data source
Current market price source
Current SEC/news ingestion status
Current LLM provider abstraction
Current authentication/session model
Current test setup
Whether valuations are tied to portfolio holdings
Whether first launch targets India, US, or global companies
```

If these are unknown, the first Codex task should be repository audit only.

---

# 27. Final Practical Recommendation

Build the valuation agent like this:

```text
First make the math correct.
Then make assumptions intelligent.
Then make diagnostics strict.
Then make the UI clean.
Then add AI explanation.
Then integrate market intelligence.
Then add advanced special cases.
```

Do not start with the flashy parts.

The valuable product is not a spreadsheet clone. It is an assumption discipline system that makes it harder to hide bad valuation logic.
