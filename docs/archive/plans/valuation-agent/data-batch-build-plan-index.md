# Valuation Agent Data-Batch Build Plan: Completed Batch Map

This file summarizes the batch sequence created from the uploaded Damodaran India spreadsheets and supporting files.

## Completed batch files

| Batch | File | Role |
|---|---|---|
| Batch 01 | `valuation_agent_batch_01_relative_pricing_benchmarks.md` | Relative pricing benchmarks: PE, PBV, PS, EV/EBITDA, country stats |
| Batch 02 | `valuation_agent_batch_02_dcf_fundamentals_growth_reinvestment.md` | DCF assumptions: margins, growth, capex, working capital, ROE/ROC, financing flows |
| Batch 03 | `valuation_agent_batch_03_accounting_normalization_intangibles.md` | R&D capitalization, goodwill, acquisition-quality diagnostics |
| Batch 04 | `valuation_agent_batch_04_equity_cash_flow_dividends_buybacks_fcfe.md` | Dividends, buybacks, stock issuance, FCFE, payout sustainability |
| Batch 05 | `valuation_agent_batch_05_macro_exposure_duration_sensitivity.md` | Macro duration, cyclicality, inflation sensitivity, currency sensitivity |
| Batch 06 | `valuation_agent_batch_06_real_options_volatility_support.md` | Volatility benchmarks and real options support |

## Recommended implementation order

Build in this order:

1. **Batch 02**
   - Core DCF assumption engine.
   - Highest priority.

2. **Batch 03**
   - Accounting normalization.
   - Needed before serious ROIC, margins, and reinvestment.

3. **Batch 01**
   - Relative pricing benchmarks.
   - Useful for sanity checks and market pricing comparison.

4. **Batch 04**
   - FCFE and shareholder cash-return analysis.
   - Adds equity-owner lens.

5. **Batch 05**
   - Macro sensitivity.
   - Adds scenario intelligence and rate/cycle/inflation/currency exposure.

6. **Batch 06**
   - Real options.
   - Advanced mode only.

## Build philosophy

The valuation agent should be structured as deterministic finance math plus AI explanation.

Backend:
- calculations
- formulas
- database storage
- ingestion
- validation
- scenario runs

LLM:
- explains assumptions
- asks for missing inputs
- flags unrealistic assumptions
- maps narrative to numbers
- writes memo sections
- warns about double counting and false precision

The LLM should not be trusted to directly calculate valuations without backend formulas.

## Product architecture

The final valuation agent should have these modules:

```text
ValuationAgent
├── DataIngestion
│   ├── IndustryPricingBenchmarks
│   ├── DcfFundamentalsBenchmarks
│   ├── AccountingNormalizationBenchmarks
│   ├── PayoutAndFcfeBenchmarks
│   ├── MacroSensitivityBenchmarks
│   └── VolatilityBenchmarks
│
├── ValuationEngines
│   ├── FCFF DCF
│   ├── FCFE DCF
│   ├── Dividend Discount
│   ├── Relative Pricing
│   ├── Reverse DCF
│   ├── Scenario Valuation
│   └── Real Options
│
├── Diagnostics
│   ├── Terminal Value Discipline
│   ├── Reinvestment Consistency
│   ├── Margin Plausibility
│   ├── ROC vs WACC
│   ├── Payout Sustainability
│   ├── Macro Exposure
│   ├── Relative Pricing Sanity Checks
│   └── Double Counting Warnings
│
└── AI Analyst Layer
    ├── Narrative-to-Numbers
    ├── Assumption Challenge Mode
    ├── Valuation Memo Writer
    ├── Source/Assumption Explainer
    └── User Question Answering
```

## Practical next step

Use Batch 02 and Batch 03 first to build the serious DCF core. Do not start with real options or macro. Those are valuable, but they are advanced modules. If the DCF engine is weak, every advanced feature becomes decoration.


---

## Regression PDF update

Two additional PDF files were added after the original batch map:

| Source file | Actual content | Primary batch | Why it belongs there |
|---|---|---|---|
| `global regression debt.pdf` | Dividend regressions: dividend yield and dividend payout, US and global, January 2025 | Batch 04 | Improves dividend-yield priors, payout diagnostics, DDM suitability, and dividend-trap warnings |
| `debt regression.pdf` | Debt ratio regression, US and global, January 2025 | Batch 02 | Improves target debt ratio priors, WACC assumptions, capital structure diagnostics, and leverage sanity checks |

Important naming note:

```text
The uploaded file named global regression debt.pdf is actually a dividend regression file.
Do not place it in the debt/capital-structure module.
```

## Updated implementation order with regression PDFs

Build order remains mostly unchanged:

1. **Batch 02: DCF fundamentals and capital structure**
   - Add debt ratio regression prior service here.

2. **Batch 03: accounting normalization**
   - No direct change from these PDFs.

3. **Batch 01: relative pricing**
   - No direct change from these PDFs.

4. **Batch 04: FCFE, payout, dividends, buybacks**
   - Add dividend yield and payout regression prior service here.

5. **Batch 05: macro exposure**
   - No direct change from these PDFs.

6. **Batch 06: real options**
   - No direct change from these PDFs.

## Updated module architecture

```text
ValuationAgent
├── DataIngestion
│   ├── IndustryPricingBenchmarks
│   ├── DcfFundamentalsBenchmarks
│   ├── AccountingNormalizationBenchmarks
│   ├── PayoutAndFcfeBenchmarks
│   ├── MacroSensitivityBenchmarks
│   ├── VolatilityBenchmarks
│   └── RegressionModelSeeds
│       ├── DebtRatioRegressionModels
│       └── DividendPolicyRegressionModels
│
├── ValuationEngines
│   ├── FCFF DCF
│   ├── FCFE DCF
│   ├── Dividend Discount
│   ├── Relative Pricing
│   ├── Reverse DCF
│   ├── Scenario Valuation
│   └── Real Options
│
├── AssumptionPriors
│   ├── IndustryFundamentalPriors
│   ├── CapitalStructurePriorService
│   └── DividendPolicyPriorService
│
├── Diagnostics
│   ├── Terminal Value Discipline
│   ├── Reinvestment Consistency
│   ├── Margin Plausibility
│   ├── ROC vs WACC
│   ├── Payout Sustainability
│   ├── Capital Structure Plausibility
│   ├── Dividend Trap Detection
│   ├── Macro Exposure
│   ├── Relative Pricing Sanity Checks
│   └── Double Counting Warnings
│
└── AI Analyst Layer
    ├── Narrative-to-Numbers
    ├── Assumption Challenge Mode
    ├── Valuation Memo Writer
    ├── Source/Assumption Explainer
    └── User Question Answering
```

## Practical rule for Codex/Gemini

These regressions should be seeded as model coefficients and used as **low-confidence priors**.
They should not replace direct company data, industry benchmarks, management guidance, or user assumptions.

Use hierarchy:

```text
1. Company actual data
2. Company historical trend
3. Industry benchmark
4. Regression-implied prior
5. User override
```

But for target assumptions, let the user explicitly choose between:

```text
Current company value
Industry median
Regression-implied value
Custom user input
```
