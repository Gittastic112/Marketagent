# Valuation Agent Batch 02: DCF Fundamentals, Growth, Margins, Reinvestment, and Financing Benchmarks

## Purpose of this batch

This batch turns Damodaran's India industry fundamental datasets into the **assumption engine** for the valuation agent.

Batch 01 gave the agent market-pricing context: PE, PBV, EV/Sales, EV/EBITDA, and country-level pricing benchmarks. Batch 02 is more important for a Damodaran-style valuation tool because it feeds the actual drivers of intrinsic value:

- Revenue growth
- Operating margins
- Reinvestment needs
- Working capital needs
- ROE and ROC/ROIC quality
- Sustainable growth
- Historical and expected growth
- Financing dependence
- Dividend, buyback, equity issuance, debt issuance, and lease debt behavior

The key role of this batch is to let the agent move from this weak valuation style:

```text
User enters revenue growth, margin, WACC, terminal growth.
Tool outputs DCF value.
```

To this stronger Damodaran-style valuation style:

```text
Tool starts with industry economics.
Tool studies company history.
Tool proposes assumption ranges.
User edits assumptions.
Tool checks whether growth, margins, reinvestment, and returns are internally consistent.
Tool explains what has to be true for the valuation to work.
```

This batch should become the agent's **operating forecast prior layer** and **DCF sanity-check layer**.

---

## Files included in Batch 02

| File | Dataset role | Core use in the agent |
|---|---|---|
| `marginIndia.xls` | Industry profitability and expense ratios | Operating margin assumptions, target margin checks, EBITDA margin checks, R&D/Sales, SG&A/Sales, SBC/Sales, lease expense/Sales |
| `capexIndia.xls` | Capital expenditures, depreciation, acquisitions, R&D, and sales/invested capital | Reinvestment forecasting, sales-to-capital assumptions, capital intensity, net capex sanity checks |
| `wcdataIndia.xls` | Working capital ratios as percent of sales | Non-cash working capital forecasting, working capital drag, receivables/inventory/payables checks |
| `roeIndia.xls` | ROE, unadjusted and R&D-adjusted | Equity return quality, PBV interpretation, equity-growth sanity checks |
| `fundgrIndia.xls` | Fundamental sustainable growth in equity income | EPS growth sanity check using ROE × retention ratio |
| `fundgrEBIndia.xls` | Fundamental sustainable growth in operating income | EBIT growth sanity check using ROC × reinvestment rate |
| `histgrIndia.xls` | Historical and expected growth rates | Revenue growth and EPS growth priors, analyst expectation checks |
| `finflowsIndia.xls` | Financing cash flows by industry | Payout behavior, equity/debt issuance reliance, leverage change, lease debt change |
| `debt regression.pdf` | Cross-sectional debt ratio regression, US and global | Target/expected debt ratio prior for WACC, capital structure diagnostics, and debt-capacity sanity checks |

Files intentionally held for later batches:

| Later batch | Files | Reason |
|---|---|---|
| Batch 03: Accounting normalization and intangibles | `R&DIndia.xls`, `goodwillIndia.xls` | These require a dedicated accounting-adjustment module. |
| Batch 04: Equity cash flow and payout | `divfundIndia.xls`, `divfcfeIndia.xls` | These are more specific to FCFE, dividends, buybacks, and payout modeling. |
| Batch 05: Macro exposure and duration | `macro.xls`, `macrodur.xls` | These support top-down macro factor sensitivity. |
| Batch 06: Option valuation and volatility | `optvarIndia.xls` | This supports real options, equity-as-option, and volatility modules. |

---

## High-level lesson from Batch 02

These files are not just miscellaneous industry tables. Together, they form the core of a Damodaran-style **narrative-to-numbers bridge**.

A serious valuation is not driven by arbitrary growth and margin inputs. It is driven by a linked chain:

```text
Narrative
→ revenue growth
→ target margins
→ reinvestment needs
→ return on capital
→ free cash flow
→ cost of capital
→ terminal value
→ value per share
```

Batch 02 gives the agent the data needed to check whether that chain is coherent.

Example:

```text
Narrative:
"The company will grow revenue quickly for 5 years."

Required checks:
- Is that revenue growth consistent with historical and expected industry growth?
- What sales-to-capital ratio is needed to support that growth?
- Does the company have the reinvestment capacity to fund it?
- Does the resulting ROC exceed WACC?
- Does the margin path imply unrealistic industry outperformance?
- Does the terminal period assume a mature company or an immortal high-growth company?
```

The valuation agent should not merely calculate. It should **challenge the assumptions**.

---

## Dataset structure learned

The Batch 02 India files share a common Damodaran data structure:

```text
Sheet 1: Variables & FAQ
Sheet 2: Industry Averages
```

Typical structure:

```text
Rows 1 to 7: metadata, source links, update date, creator, region
Row 8 or 9: industry column headers
Rows below: Damodaran industry rows
```

Observed used ranges:

| File | `Industry Averages` used range | Header row pattern |
|---|---:|---|
| `marginIndia.xlsx` | `A1:S105` | Row 8 has category labels, row 9 has actual fields |
| `capexIndia.xlsx` | `A1:J104` | Row 8 has actual fields |
| `wcdataIndia.xlsx` | `A1:F104` | Row 8 has actual fields |
| `roeIndia.xlsx` | `A1:I104` | Row 8 has actual fields |
| `fundgrIndia.xlsx` | `A1:I104` | Row 8 has actual fields |
| `fundgrEBIndia.xlsx` | `A1:I104` | Row 8 has actual fields |
| `histgrIndia.xlsx` | `A1:G104` | Row 8 has actual fields |
| `finflowsIndia.xlsx` | `A1:L104` | Row 8 has actual fields |

Implementation implication:

```text
Do not assume every Damodaran file has the same header row.
Build a loader that searches for the row containing "Industry Name".
Use all non-empty rows below that as data rows.
```

---

## Core design principle for the agent

The Batch 02 datasets should be used as **priors**, not hardcoded answers.

The agent should think like this:

```text
Industry data gives a starting point.
Company history gives the current base.
Narrative gives the direction of change.
User assumptions give the final explicit case.
Diagnostics check whether the case is internally consistent.
```

The agent should not say:

```text
The industry operating margin is 14%, so the company should have a 14% margin.
```

The agent should say:

```text
The industry operating margin is around 14%. The company currently earns 9%. A target margin of 16% requires a credible explanation: pricing power, scale, cost cuts, mix shift, or lower competition.
```

---

# File-by-file learning

## 1. `marginIndia.xls`: Profitability and cost structure

### Dataset purpose

`marginIndia.xls` measures industry profitability and expense ratios across Indian companies.

This file is the most important Batch 02 file for the agent's **margin forecast module**.

### Key fields

| Field | Meaning | Agent use |
|---|---|---|
| `Industry Name` | Damodaran industry grouping | Industry matching |
| `Number of firms` | Sample size | Data confidence |
| `Gross Margin` | Gross profit / revenue | Direct cost structure, pricing power |
| `Net Margin` | Net income / revenue | Equity profitability, after all expenses |
| `Pre-tax, Pre-stock compensation Operating Margin` | Operating profit before tax and stock comp / revenue | Operating profitability before SBC |
| `Pre-tax Unadjusted Operating Margin` | As-reported EBIT / revenue | Raw operating margin |
| `After-tax Unadjusted Operating Margin` | EBIT after effective tax / revenue | Raw after-tax operating margin |
| `Pre-tax Lease adjusted Margin` | EBIT adjusted for lease treatment / revenue | Better operating margin when leases matter |
| `After-tax Lease Adjusted Margin` | After-tax lease-adjusted operating margin | DCF operating margin candidate |
| `Pre-tax Lease & R&D adj Margin` | EBIT adjusted for leases and R&D capitalization / revenue | Best pre-tax operating margin for R&D-heavy sectors |
| `After-tax Lease & R&D adj Margin` | After-tax EBIT adjusted for leases and R&D / revenue | Best after-tax normalized margin candidate |
| `EBITDA/Sales` | EBITDA / revenue | Cash operating profitability |
| `EBITDASG&A/Sales` | EBITDA plus SG&A / revenue | Cash profitability before SG&A |
| `EBITDAR&D/Sales` | EBITDA plus R&D / revenue | Cash profitability before R&D |
| `COGS/Sales` | Direct costs / sales | Cost structure |
| `R&D/Sales` | R&D expense / sales | Intangible reinvestment intensity |
| `SG&A/Sales` | SG&A expense / sales | Selling/admin intensity |
| `Stock-Based Compensation/Sales` | SBC / sales | Dilution and expense quality warning |
| `Lease Expense/Sales` | Current lease expense / sales | Lease-heavy business warning |

### Important accounting lesson

The file explicitly treats lease and R&D adjustments as operating-income adjustments:

```text
Lease-adjusted operating income
= Operating income + current lease expense - depreciation on lease asset

R&D-adjusted operating income
= Operating income + current R&D expense - amortization of R&D asset
```

This should directly influence the valuation agent.

### Agent implementation rule

Use margin data in a hierarchy:

| Situation | Preferred margin field |
|---|---|
| Simple quick valuation | `After-tax Unadjusted Operating Margin` or `Pre-tax Unadjusted Operating Margin` with tax applied separately |
| Lease-heavy business | Lease-adjusted margin |
| R&D-heavy / intangible-heavy business | Lease & R&D adjusted margin |
| EBITDA cross-check | `EBITDA/Sales` |
| SBC-heavy business | Compare pre-stock compensation operating margin to unadjusted margin |

### Agent warning logic

The agent should flag:

```text
Target margin > industry adjusted operating margin by large amount
Current company margin materially below industry margin
Current company margin materially above industry margin
High SBC/Sales
High R&D/Sales
High lease expense/Sales
Gross margin inconsistent with target operating margin
```

### UI requirement

In advanced valuation mode, the margin panel should show:

```text
Company current gross margin
Company current operating margin
Company current EBITDA margin
Industry median/aggregate gross margin
Industry adjusted operating margin
Industry EBITDA margin
User-selected target margin
Justification required for target outperformance
```

---

## 2. `capexIndia.xls`: Reinvestment and capital intensity

### Dataset purpose

`capexIndia.xls` measures how much companies reinvest into long-term assets. It is a key file for the DCF reinvestment engine.

### Key fields

| Field | Meaning | Agent use |
|---|---|---|
| `Industry Name` | Damodaran industry grouping | Industry matching |
| `Number of Firms` | Sample size | Data confidence |
| `Capital Expenditures (US $ millions)` | Sum of capex | Gross investment in long-term assets |
| `Depreciation & Amort` | Sum of D&A | Accounting depreciation/amortization |
| `Cap Ex/Deprecn` | Capex / depreciation | Maintenance vs growth capex sanity check |
| `Acquisitions (US $ millions)` | Cash acquisitions | Acquisition-driven reinvestment |
| `Net R&D (US $ millions)` | R&D expense minus R&D amortization | Intangible reinvestment |
| `Net Cap Ex/Sales` | Net capex / sales | Capital intensity |
| `Net Cap Ex/ EBIT (1-t)` | Net capex / after-tax EBIT | Reinvestment burden |
| `Sales/ Invested Capital (LTM)` | Sales / invested capital | Core sales-to-capital input |

### Why this file matters

The weakest part of most amateur DCFs is reinvestment. They forecast high growth without paying for it.

Damodaran-style valuation forces this link:

```text
Growth requires reinvestment.
Reinvestment has to be funded by operating cash flow, debt, or equity.
The quality of growth depends on return on capital.
```

### Core formulas for the agent

The agent should support 3 reinvestment methods.

#### Method A: Sales-to-capital method

Best default for revenue-driven valuation.

```text
Incremental revenue_t = Revenue_t - Revenue_{t-1}
Reinvestment_t = Incremental revenue_t / Sales-to-capital ratio
```

Use industry `Sales/Invested Capital (LTM)` as the initial prior.

#### Method B: Reinvestment-rate method

Best for mature companies with stable ROC.

```text
Reinvestment rate = Growth rate / ROC
Reinvestment_t = EBIT_t(1 - tax rate) × Reinvestment rate
FCFF_t = EBIT_t(1 - tax rate) - Reinvestment_t
```

#### Method C: Detailed operating method

Best for advanced mode.

```text
Reinvestment_t = Net capex_t + acquisitions_t + net R&D_t + change in non-cash working capital_t
```

### Agent implementation rule

In quick valuation mode:

```text
Use sales-to-capital as default.
Use industry sales-to-capital ratio as the prior.
Let user override.
Show implied reinvestment as a percent of after-tax operating income.
```

In advanced mode:

```text
Let user choose:
- Sales-to-capital method
- Reinvestment-rate method
- Detailed capex + WC + acquisition method
```

### Diagnostics

The agent should check:

```text
Is sales-to-capital ratio unrealistically high?
Is growth high but reinvestment near zero?
Is reinvestment rate greater than 100% for too long?
Is net capex negative while revenue is growing aggressively?
Is acquisition spending a major driver of growth?
Is the company being treated as asset-light when the industry is capital-intensive?
```

---

## 3. `wcdataIndia.xls`: Working capital drag

### Dataset purpose

`wcdataIndia.xls` measures working capital components as a percent of sales.

This file should feed the agent's **working capital forecast module**.

### Key fields

| Field | Meaning | Agent use |
|---|---|---|
| `Industry Name` | Damodaran industry grouping | Industry matching |
| `Number of firms` | Sample size | Data confidence |
| `Acc Rec/ Sales` | Accounts receivable / sales | Credit sales cash drag |
| `Inventory/Sales` | Inventory / sales | Inventory cash drag |
| `Acc Pay/ Sales` | Accounts payable / sales | Supplier financing source |
| `Non-cash WC/ Sales` | Non-cash working capital / sales | Main working capital forecast input |

Non-cash working capital is defined as:

```text
Non-cash working capital
= (Current assets - cash) - (Current liabilities - short-term interest-bearing debt)
```

### Core forecast formula

```text
Non-cash WC_t = Revenue_t × Non-cash WC/Sales_t
Change in non-cash WC_t = Non-cash WC_t - Non-cash WC_{t-1}
```

Then:

```text
FCFF_t = EBIT_t(1 - tax rate) - net capex_t - change in non-cash WC_t
```

Or, under sales-to-capital method:

```text
Reinvestment_t already captures net capex and working capital together.
Do not double count working capital separately.
```

### Important double-count rule

The agent must avoid this error:

```text
Reinvestment = ΔRevenue / Sales-to-capital
Then separately subtract ΔNWC again.
```

That double counts working capital if sales-to-capital already reflects invested capital needs.

### Agent implementation rule

In the DCF model, the user should select one of these approaches:

| Reinvestment approach | Working capital treatment |
|---|---|
| Sales-to-capital | Working capital embedded, do not separately subtract ΔNWC |
| Detailed capex + working capital | Forecast ΔNWC explicitly |
| Reinvestment-rate method | Working capital embedded in reinvestment rate |

### Diagnostics

The agent should flag:

```text
Negative non-cash WC/Sales industries should not automatically be treated as bad.
They may have supplier financing or customer prepayments.
High receivables/sales means growth may consume cash.
High inventory/sales means growth may consume cash and creates obsolescence risk.
High payables/sales means supplier financing may reverse if growth slows.
```

---

## 4. `roeIndia.xls`: Return on equity quality

### Dataset purpose

`roeIndia.xls` provides unadjusted and R&D-adjusted ROE by industry.

This file supports equity return analysis, PBV interpretation, and equity growth sanity checks.

### Key fields

| Field | Meaning | Agent use |
|---|---|---|
| `Industry Name` | Damodaran industry grouping | Industry matching |
| `Number of firms` | Sample size | Data confidence |
| `ROE (unadjusted)` | Net income / book equity | Raw equity return quality |
| `ROE (adjusted for R&D)` | Net income adjusted for R&D / book equity adjusted for capitalized R&D | Better ROE for R&D-heavy sectors |

### Agent implementation rule

Use ROE for:

```text
Equity valuation
Dividend discount models
FCFE models
PBV diagnostics
EPS growth sanity checks
Bank/financial-services valuation support
```

Do not use ROE as the primary return measure for FCFF valuations of operating companies. For FCFF, use ROC/ROIC.

### Core formula

```text
Expected growth in equity income = ROE × retention ratio
```

Where:

```text
Retention ratio = 1 - payout ratio
```

### PBV diagnostic

The agent should connect PBV to ROE:

```text
A company deserves PBV > 1 only if it can sustainably earn ROE > cost of equity.
A company with ROE < cost of equity can be correctly priced below book.
```

### Advanced behavior

For banks and financial firms:

```text
Use equity valuation rather than FCFF.
Use ROE, cost of equity, payout, book equity, and PBV.
Do not use EV/EBITDA or sales-to-capital as primary methods.
```

---

## 5. `fundgrIndia.xls`: Fundamental sustainable growth in equity income

### Dataset purpose

`fundgrIndia.xls` estimates sustainable growth in equity income/EPS by industry, assuming margins and ROE are stable.

### Key fields

| Field | Meaning | Agent use |
|---|---|---|
| `Industry Name` | Damodaran industry grouping | Industry matching |
| `Number of Firms` | Sample size | Data confidence |
| `ROE` | Return on equity | Equity return driver |
| `Retention Ratio` | Retained earnings / net income | Equity reinvestment driver |
| `Fundamental Growth` | ROE × retention ratio | Sustainable EPS growth prior |

### Critical caveat

The file itself notes that these fundamental growth rates apply only if margins and ROE are stable.

The agent should explicitly warn:

```text
This sustainable growth rate is not valid if margins are changing materially.
For margin-expansion stories, use a full forecast rather than ROE × retention as the only growth estimate.
```

### Agent use

Use this dataset for:

```text
EPS growth sanity check
Dividend discount model support
FCFE model support
PBV/ROE consistency
Equity growth plausibility
```

Do not use it as the main revenue growth forecast for operating DCFs.

---

## 6. `fundgrEBIndia.xls`: Fundamental sustainable growth in operating income

### Dataset purpose

`fundgrEBIndia.xls` estimates sustainable growth in EBIT by industry, assuming margins and ROC are stable.

This is one of the most important files for the FCFF DCF engine.

### Key fields

| Field | Meaning | Agent use |
|---|---|---|
| `Industry Name` | Damodaran industry grouping | Industry matching |
| `Number of Firms` | Sample size | Data confidence |
| `ROC` | After-tax operating income / invested capital | Operating return quality |
| `Reinvestment Rate` | Reinvestment / after-tax operating income | Operating reinvestment intensity |
| `Expected Growth in EBIT` | ROC × reinvestment rate | Sustainable operating income growth |

### Core formula

```text
Expected growth in EBIT = ROC × Reinvestment Rate
```

This is central to Damodaran-style valuation.

### Agent implementation rule

The valuation engine should never allow growth to float independently from reinvestment forever.

In explicit forecast years, the user can tell a story with high growth and changing margins. But by terminal year, the model must force consistency:

```text
Terminal reinvestment rate = Terminal growth rate / Terminal ROC
```

Then:

```text
Terminal FCFF = EBIT_terminal × (1 - tax rate) × (1 - terminal reinvestment rate)
```

### Critical caveat

The file notes that this formula works when margins and ROC are stable. If margins are changing, use a full operating forecast.

Agent language:

```text
Because your valuation assumes margin expansion, the simple ROC × reinvestment-rate growth estimate is a sanity check, not the forecast itself.
```

### Diagnostics

The agent should flag:

```text
High growth with low or negative reinvestment rate.
High growth with ROC below WACC.
Terminal ROC below WACC while terminal growth is positive.
Reinvestment rate above 100% for too many years.
Negative reinvestment paired with high growth.
ROC far above industry without a moat narrative.
```

---

## 7. `histgrIndia.xls`: Historical and expected growth

### Dataset purpose

`histgrIndia.xls` reports historical compounded growth rates and expected growth rates for Indian industries.

This file should feed the agent's **growth forecast prior module**.

### Key fields

| Field | Meaning | Agent use |
|---|---|---|
| `Industry Name` | Damodaran industry grouping | Industry matching |
| `Number of Firms` | Sample size | Data confidence |
| `CAGR in Net Income - Last 5 years` | Historical net income CAGR | Past earnings growth check |
| `CAGR in Revenues - Last 5 years` | Historical revenue CAGR | Past sales growth check |
| `Expected Growth in Revenues - Next 2 years` | Near-term expected revenue growth | Short-term forecast prior |
| `Expected Growth in Revenues - Next 5 years` | Medium-term expected revenue growth | Explicit forecast prior |
| `Expected Growth in EPS - Next 5 years` | Expected EPS growth | Equity earnings sanity check |

### Agent implementation rule

Growth forecasting should triangulate 4 sources:

```text
1. Company historical revenue growth
2. Industry historical revenue growth
3. Industry expected revenue growth
4. User/company narrative
```

The agent should not mechanically use historical growth as future growth.

### Quick valuation default

For quick valuation mode, a practical default can be:

```text
Year 1-2 revenue growth: closer to industry expected revenue growth next 2 years
Year 3-5 revenue growth: fade toward industry expected revenue growth next 5 years
Years 6-10: fade toward stable growth / nominal economy growth
Terminal growth: constrained by currency and economy
```

### Diagnostics

The agent should flag:

```text
User revenue growth > industry expected growth by large amount
Historical growth negative but user assumes strong growth without turnaround narrative
Net income growth far above revenue growth because of margin expansion
Expected EPS growth much higher than revenue growth due to implied operating leverage
Terminal growth above long-term nominal GDP / risk-free-rate consistency bounds
```

---

## 8. `finflowsIndia.xls`: Financing behavior and capital access

### Dataset purpose

`finflowsIndia.xls` measures cash flows from financing by Indian industry.

This is not a direct FCFF input, but it is important for:

```text
Debt capacity
Equity dilution risk
External funding dependence
Payout behavior
Capital structure change
Lease debt movement
```

### Key fields

| Field | Meaning | Agent use |
|---|---|---|
| `Industry Name` | Damodaran industry grouping | Industry matching |
| `Number of Firms` | Sample size | Data confidence |
| `Dividends in $ millions` | Industry dividends | Payout tendency |
| `Buybacks in $ millions` | Industry buybacks | Shareholder return tendency |
| `Equity Issuance in $ millions` | New equity issued | Dilution/funding dependence |
| `Net Equity Change in $ millions` | Equity issuance - buybacks - dividends | Net equity funding |
| `Net Equity Change as % of Book Equity` | Net equity change / book equity | Equity financing intensity |
| `Debt Repaid in $ millions` | Debt repayment | Deleveraging / refinancing |
| `Debt Raised in $ millions` | New debt raised | Leverage/funding dependence |
| `Net Debt Change in $ millions` | Debt raised - debt repaid | Net debt funding |
| `Net Change in Debt as % of Total Debt` | Net debt change / total debt | Leverage momentum |
| `Change in Lease Debt in $ millions` | Change in lease debt | Lease-heavy expansion or contraction |

### Agent implementation rule

Use financing flows as a **risk and plausibility diagnostic**, not as a direct FCFF valuation driver.

For FCFF:

```text
Debt issuance and equity issuance do not directly affect operating asset value.
They affect equity value through capital structure, cost of capital, dilution, and risk.
```

For FCFE:

```text
Net debt issuance directly affects FCFE.
Equity issuance affects share count and dilution.
```

### Diagnostics

The agent should flag:

```text
High growth valuation requires external funding.
Industry commonly issues equity, suggesting dilution risk.
Company assumes no dilution despite negative FCFE.
Debt funding is rising in an industry with weak operating cash flow.
Lease debt is rising, meaning lease-adjusted leverage should be checked.
```

---

# How Batch 02 should improve the valuation agent

## 1. Build an industry assumption engine

The agent needs a backend service that produces a structured assumption package for a company based on its mapped Damodaran industry.

### Suggested output object

```json
{
  "company": "Example Ltd",
  "country": "India",
  "damodaran_industry": "Auto Parts",
  "data_version": "2026-01",
  "confidence": {
    "sample_size": 120,
    "industry_match_quality": "high",
    "warnings": []
  },
  "margin_priors": {
    "gross_margin": 0.3865,
    "pre_tax_operating_margin": 0.0691,
    "after_tax_operating_margin": 0.0526,
    "lease_rd_adjusted_after_tax_margin": 0.0522,
    "ebitda_margin": 0.1025,
    "rd_to_sales": 0.0030,
    "sga_to_sales": 0.1507,
    "sbc_to_sales": 0.0004,
    "lease_expense_to_sales": 0.0025
  },
  "reinvestment_priors": {
    "sales_to_invested_capital": 1.8682,
    "net_capex_to_sales": 0.0262,
    "net_capex_to_after_tax_ebit": 0.5146,
    "capex_to_depreciation": 1.6213
  },
  "working_capital_priors": {
    "accounts_receivable_to_sales": 0.1411,
    "inventory_to_sales": 0.1218,
    "accounts_payable_to_sales": 0.1718,
    "non_cash_wc_to_sales": 0.0889
  },
  "return_priors": {
    "roe_unadjusted": 0.1389,
    "roe_rd_adjusted": 0.1347,
    "roc": 0.0958
  },
  "growth_priors": {
    "revenue_cagr_5y": 0.1748,
    "expected_revenue_growth_2y": 0.1334,
    "expected_revenue_growth_5y": 0.0631,
    "expected_eps_growth_5y": 0.2186,
    "fundamental_eps_growth": 0.0999,
    "fundamental_ebit_growth": 0.0538
  },
  "financing_priors": {
    "net_equity_change_to_book_equity": 0.0658,
    "net_debt_change_to_total_debt": -0.0646,
    "lease_debt_change": 141.193
  }
}
```

Numbers above are examples from a sample industry row and must not be hardcoded.

---

## 2. Upgrade quick valuation mode

Quick valuation should become materially better after Batch 02.

### Current weak version

```text
User manually enters:
- revenue growth
- margin
- WACC
- terminal growth
```

### Improved version

The user enters:

```text
Company / ticker
Country
Industry
Current revenue
Current operating income or margin
Net debt
Shares outstanding
```

The agent proposes:

```text
Near-term revenue growth: based on company + industry expected growth
Target operating margin: based on company current margin + industry adjusted margin
Sales-to-capital ratio: based on industry benchmark
Working capital ratio: based on industry benchmark
ROC: based on company history + industry ROC
Terminal growth: based on currency/economy constraints
Terminal ROC: based on industry/mature-company economics
```

Then the user can override assumptions.

### Quick valuation output

```text
Estimated value per share
Current price
Upside/downside
Key assumptions
Top 5 assumptions driving value
Industry comparison
Sanity checks
What has to be true
```

---

## 3. Upgrade advanced valuation mode

Advanced mode should let the user build a complete Damodaran-style operating model.

### Required panels

| Panel | Batch 02 support |
|---|---|
| Revenue forecast | `histgrIndia.xls` |
| Margin forecast | `marginIndia.xls` |
| Reinvestment forecast | `capexIndia.xls`, `wcdataIndia.xls`, `fundgrEBIndia.xls` |
| ROIC/ROC analysis | `fundgrEBIndia.xls`, `capexIndia.xls` |
| Equity return analysis | `roeIndia.xls`, `fundgrIndia.xls` |
| Financing/dilution risk | `finflowsIndia.xls` |
| Diagnostics | All Batch 02 files |

### Advanced assumption controls

The advanced valuation screen should include:

```text
Revenue growth by year
Target revenue growth fade
Gross margin by year
Operating margin by year
Tax rate
Sales-to-capital ratio by year
Net capex as % of sales
Working capital as % of sales
Acquisition reinvestment
R&D capitalization toggle
Lease adjustment toggle
ROIC/ROC target
Terminal growth
Terminal ROC
Terminal reinvestment rate
```

---

# Core DCF formulas Batch 02 should enable

## Revenue forecast

```text
Revenue_t = Revenue_{t-1} × (1 + Revenue Growth_t)
```

## Operating income forecast

```text
EBIT_t = Revenue_t × Pre-tax Operating Margin_t
After-tax EBIT_t = EBIT_t × (1 - Tax Rate_t)
```

## Reinvestment using sales-to-capital

```text
Incremental Revenue_t = Revenue_t - Revenue_{t-1}
Reinvestment_t = Incremental Revenue_t / Sales-to-Capital Ratio_t
```

## Reinvestment using ROC

```text
Reinvestment Rate_t = Growth in EBIT_t / ROC_t
Reinvestment_t = After-tax EBIT_t × Reinvestment Rate_t
```

## Detailed reinvestment method

```text
Reinvestment_t = Net Capex_t + Acquisitions_t + Net R&D_t + Change in Non-cash Working Capital_t
```

## FCFF

```text
FCFF_t = After-tax EBIT_t - Reinvestment_t
```

## Operating invested capital

```text
Invested Capital_t = Invested Capital_{t-1} + Reinvestment_t
```

## ROC / ROIC

```text
ROC_t = After-tax EBIT_t / Invested Capital_{t-1}
```

## Fundamental operating growth

```text
Expected EBIT Growth = ROC × Reinvestment Rate
```

## Fundamental equity growth

```text
Expected EPS Growth = ROE × Retention Ratio
```

## Terminal reinvestment rate

```text
Terminal Reinvestment Rate = Terminal Growth / Terminal ROC
```

## Terminal FCFF

```text
Terminal FCFF = After-tax EBIT_terminal × (1 + g_terminal) × (1 - Terminal Reinvestment Rate)
```

## Terminal value

```text
Terminal Value = Terminal FCFF / (WACC_terminal - g_terminal)
```

## Value of operating assets

```text
Value of Operating Assets = Sum(PV of explicit FCFF) + PV of Terminal Value
```

## Equity value

```text
Equity Value = Value of Operating Assets + Cash + Non-operating Assets - Debt - Minority Interests - Other Claims
```

## Value per share

```text
Value per Share = Equity Value / Diluted Shares Outstanding
```

---

# Critical implementation guardrails

## Guardrail 1: Do not confuse equity growth and operating growth

`fundgrIndia.xls` gives sustainable growth in equity income/EPS:

```text
EPS growth = ROE × retention ratio
```

`fundgrEBIndia.xls` gives sustainable growth in operating income:

```text
EBIT growth = ROC × reinvestment rate
```

The agent must not use EPS growth as the operating-income growth input in an FCFF model.

## Guardrail 2: Do not double count working capital

If using sales-to-capital:

```text
Reinvestment = ΔRevenue / Sales-to-capital
```

Then do not also subtract working capital separately unless the model has explicitly decomposed sales-to-capital into fixed capital and working capital.

## Guardrail 3: Stable growth must be internally consistent

In stable growth:

```text
Terminal growth cannot be free.
Terminal growth requires terminal reinvestment.
Terminal reinvestment must be linked to terminal ROC.
```

Therefore:

```text
Terminal Reinvestment Rate = g / ROC
```

If ROC = WACC, growth adds no value. If ROC < WACC, growth destroys value.

## Guardrail 4: Industry data is not company data

The agent should use these files as:

```text
- priors
- bounds
- comparables
- diagnostic references
- starting assumptions
```

Not as:

```text
- guaranteed forecasts
- company-specific truths
- automatic target assumptions
```

## Guardrail 5: NAs are meaningful

Some industries, especially banks and financial services, contain `NA` for metrics like ROC, sales-to-capital, or operating metrics.

The agent should not force FCFF valuation onto financial services.

Behavior:

```text
If industry is bank, insurance, financial services, brokerage, or related:
- switch default valuation to equity valuation
- use ROE, book equity, cost of equity, payout, and PBV
- disable or warn against EV/EBITDA and FCFF operating valuation
```

## Guardrail 6: Negative reinvestment and negative working capital require interpretation

Negative reinvestment or negative non-cash working capital may be valid.

Examples:

```text
Negative non-cash working capital may indicate supplier financing, customer advances, or working capital efficiency.
Negative net capex may indicate mature/declining capital base, not necessarily efficiency.
Negative reinvestment with high growth is usually not sustainable.
```

## Guardrail 7: Margin improvement has to come from somewhere

If the valuation assumes margin expansion, the agent should ask what drives it:

```text
- pricing power
- operating leverage
- product mix
- cost reduction
- scale effects
- lower SG&A/Sales
- lower COGS/Sales
- lower R&D/Sales after maturity
- lower lease intensity
- reduced SBC
```

The UI should force a note if target margin exceeds industry adjusted margin materially.

---

# Database design

## Staging tables

Create separate raw/staging tables for each Damodaran file. This makes ingestion auditable and avoids forcing everything into one universal table too early.

### `damodaran_industry_margin_benchmarks`

```sql
CREATE TABLE damodaran_industry_margin_benchmarks (
  id UUID PRIMARY KEY,
  geography TEXT NOT NULL DEFAULT 'India',
  data_version TEXT NOT NULL,
  source_file TEXT NOT NULL,
  source_update_date DATE,
  industry_name TEXT NOT NULL,
  number_of_firms INTEGER,
  gross_margin NUMERIC,
  net_margin NUMERIC,
  pre_tax_pre_sbc_operating_margin NUMERIC,
  pre_tax_unadjusted_operating_margin NUMERIC,
  after_tax_unadjusted_operating_margin NUMERIC,
  pre_tax_lease_adjusted_margin NUMERIC,
  after_tax_lease_adjusted_margin NUMERIC,
  pre_tax_lease_rd_adjusted_margin NUMERIC,
  after_tax_lease_rd_adjusted_margin NUMERIC,
  ebitda_to_sales NUMERIC,
  ebitda_sga_to_sales NUMERIC,
  ebitda_rd_to_sales NUMERIC,
  cogs_to_sales NUMERIC,
  rd_to_sales NUMERIC,
  sga_to_sales NUMERIC,
  stock_based_comp_to_sales NUMERIC,
  lease_expense_to_sales NUMERIC,
  created_at TIMESTAMP DEFAULT now(),
  UNIQUE (geography, data_version, industry_name)
);
```

### `damodaran_industry_capex_benchmarks`

```sql
CREATE TABLE damodaran_industry_capex_benchmarks (
  id UUID PRIMARY KEY,
  geography TEXT NOT NULL DEFAULT 'India',
  data_version TEXT NOT NULL,
  source_file TEXT NOT NULL,
  source_update_date DATE,
  industry_name TEXT NOT NULL,
  number_of_firms INTEGER,
  capital_expenditures_usd_mn NUMERIC,
  depreciation_amortization_usd_mn NUMERIC,
  capex_to_depreciation NUMERIC,
  acquisitions_usd_mn NUMERIC,
  net_rd_usd_mn NUMERIC,
  net_capex_to_sales NUMERIC,
  net_capex_to_after_tax_ebit NUMERIC,
  sales_to_invested_capital_ltm NUMERIC,
  created_at TIMESTAMP DEFAULT now(),
  UNIQUE (geography, data_version, industry_name)
);
```

### `damodaran_industry_working_capital_benchmarks`

```sql
CREATE TABLE damodaran_industry_working_capital_benchmarks (
  id UUID PRIMARY KEY,
  geography TEXT NOT NULL DEFAULT 'India',
  data_version TEXT NOT NULL,
  source_file TEXT NOT NULL,
  source_update_date DATE,
  industry_name TEXT NOT NULL,
  number_of_firms INTEGER,
  accounts_receivable_to_sales NUMERIC,
  inventory_to_sales NUMERIC,
  accounts_payable_to_sales NUMERIC,
  non_cash_working_capital_to_sales NUMERIC,
  created_at TIMESTAMP DEFAULT now(),
  UNIQUE (geography, data_version, industry_name)
);
```

### `damodaran_industry_roe_benchmarks`

```sql
CREATE TABLE damodaran_industry_roe_benchmarks (
  id UUID PRIMARY KEY,
  geography TEXT NOT NULL DEFAULT 'India',
  data_version TEXT NOT NULL,
  source_file TEXT NOT NULL,
  source_update_date DATE,
  industry_name TEXT NOT NULL,
  number_of_firms INTEGER,
  roe_unadjusted NUMERIC,
  roe_adjusted_for_rd NUMERIC,
  created_at TIMESTAMP DEFAULT now(),
  UNIQUE (geography, data_version, industry_name)
);
```

### `damodaran_industry_fundamental_equity_growth`

```sql
CREATE TABLE damodaran_industry_fundamental_equity_growth (
  id UUID PRIMARY KEY,
  geography TEXT NOT NULL DEFAULT 'India',
  data_version TEXT NOT NULL,
  source_file TEXT NOT NULL,
  source_update_date DATE,
  industry_name TEXT NOT NULL,
  number_of_firms INTEGER,
  roe NUMERIC,
  retention_ratio NUMERIC,
  fundamental_growth_eps NUMERIC,
  created_at TIMESTAMP DEFAULT now(),
  UNIQUE (geography, data_version, industry_name)
);
```

### `damodaran_industry_fundamental_operating_growth`

```sql
CREATE TABLE damodaran_industry_fundamental_operating_growth (
  id UUID PRIMARY KEY,
  geography TEXT NOT NULL DEFAULT 'India',
  data_version TEXT NOT NULL,
  source_file TEXT NOT NULL,
  source_update_date DATE,
  industry_name TEXT NOT NULL,
  number_of_firms INTEGER,
  roc NUMERIC,
  reinvestment_rate NUMERIC,
  expected_growth_ebit NUMERIC,
  created_at TIMESTAMP DEFAULT now(),
  UNIQUE (geography, data_version, industry_name)
);
```

### `damodaran_industry_historical_growth`

```sql
CREATE TABLE damodaran_industry_historical_growth (
  id UUID PRIMARY KEY,
  geography TEXT NOT NULL DEFAULT 'India',
  data_version TEXT NOT NULL,
  source_file TEXT NOT NULL,
  source_update_date DATE,
  industry_name TEXT NOT NULL,
  number_of_firms INTEGER,
  net_income_cagr_5y NUMERIC,
  revenue_cagr_5y NUMERIC,
  expected_revenue_growth_2y NUMERIC,
  expected_revenue_growth_5y NUMERIC,
  expected_eps_growth_5y NUMERIC,
  created_at TIMESTAMP DEFAULT now(),
  UNIQUE (geography, data_version, industry_name)
);
```

### `damodaran_industry_financing_flows`

```sql
CREATE TABLE damodaran_industry_financing_flows (
  id UUID PRIMARY KEY,
  geography TEXT NOT NULL DEFAULT 'India',
  data_version TEXT NOT NULL,
  source_file TEXT NOT NULL,
  source_update_date DATE,
  industry_name TEXT NOT NULL,
  number_of_firms INTEGER,
  dividends_usd_mn NUMERIC,
  buybacks_usd_mn NUMERIC,
  equity_issuance_usd_mn NUMERIC,
  net_equity_change_usd_mn NUMERIC,
  net_equity_change_to_book_equity NUMERIC,
  debt_repaid_usd_mn NUMERIC,
  debt_raised_usd_mn NUMERIC,
  net_debt_change_usd_mn NUMERIC,
  net_debt_change_to_total_debt NUMERIC,
  change_in_lease_debt_usd_mn NUMERIC,
  created_at TIMESTAMP DEFAULT now(),
  UNIQUE (geography, data_version, industry_name)
);
```

---

## Unified view

After staging tables are created, build a unified view for the agent.

```sql
CREATE VIEW valuation_industry_fundamentals_india AS
SELECT
  m.geography,
  m.data_version,
  m.industry_name,
  m.number_of_firms AS margin_sample_size,
  m.gross_margin,
  m.net_margin,
  m.pre_tax_unadjusted_operating_margin,
  m.after_tax_unadjusted_operating_margin,
  m.after_tax_lease_adjusted_margin,
  m.after_tax_lease_rd_adjusted_margin,
  m.ebitda_to_sales,
  m.rd_to_sales,
  m.sga_to_sales,
  m.stock_based_comp_to_sales,
  m.lease_expense_to_sales,
  c.sales_to_invested_capital_ltm,
  c.net_capex_to_sales,
  c.net_capex_to_after_tax_ebit,
  c.capex_to_depreciation,
  wc.non_cash_working_capital_to_sales,
  wc.accounts_receivable_to_sales,
  wc.inventory_to_sales,
  wc.accounts_payable_to_sales,
  roe.roe_unadjusted,
  roe.roe_adjusted_for_rd,
  fge.fundamental_growth_eps,
  fgo.roc,
  fgo.reinvestment_rate,
  fgo.expected_growth_ebit,
  hg.revenue_cagr_5y,
  hg.expected_revenue_growth_2y,
  hg.expected_revenue_growth_5y,
  hg.expected_eps_growth_5y,
  ff.net_equity_change_to_book_equity,
  ff.net_debt_change_to_total_debt,
  ff.change_in_lease_debt_usd_mn
FROM damodaran_industry_margin_benchmarks m
LEFT JOIN damodaran_industry_capex_benchmarks c
  ON c.geography = m.geography AND c.data_version = m.data_version AND c.industry_name = m.industry_name
LEFT JOIN damodaran_industry_working_capital_benchmarks wc
  ON wc.geography = m.geography AND wc.data_version = m.data_version AND wc.industry_name = m.industry_name
LEFT JOIN damodaran_industry_roe_benchmarks roe
  ON roe.geography = m.geography AND roe.data_version = m.data_version AND roe.industry_name = m.industry_name
LEFT JOIN damodaran_industry_fundamental_equity_growth fge
  ON fge.geography = m.geography AND fge.data_version = m.data_version AND fge.industry_name = m.industry_name
LEFT JOIN damodaran_industry_fundamental_operating_growth fgo
  ON fgo.geography = m.geography AND fgo.data_version = m.data_version AND fgo.industry_name = m.industry_name
LEFT JOIN damodaran_industry_historical_growth hg
  ON hg.geography = m.geography AND hg.data_version = m.data_version AND hg.industry_name = m.industry_name
LEFT JOIN damodaran_industry_financing_flows ff
  ON ff.geography = m.geography AND ff.data_version = m.data_version AND ff.industry_name = m.industry_name;
```

---

# Backend services to build

## 1. Damodaran file ingestion service

Service name:

```text
damodaranBenchmarkIngestionService
```

Responsibilities:

```text
Load uploaded Damodaran xls/xlsx files.
Find the Industry Averages sheet.
Find the header row containing Industry Name.
Normalize column names.
Convert percentages to decimals.
Convert "NA" strings to null.
Store raw rows into staging tables.
Create or update data_version.
Log ingestion status.
```

Implementation requirements:

```text
Do not hardcode row 8 as header for every file.
Do not assume all files have the same number of metadata rows.
Do not crash when NA appears in numeric fields.
Do not coerce missing industry values into zero.
Do not use zeros for unknown values.
```

## 2. Industry matching service

Service name:

```text
industryMappingService
```

Responsibilities:

```text
Map company industry/sector to Damodaran industry.
Allow manual override.
Store chosen mapping.
Provide confidence score.
Keep alternate possible industries.
```

Required fields:

```text
company_id
detected_sector
detected_industry
damodaran_industry
confidence_score
mapping_source
manual_override
created_at
updated_at
```

Agent behavior:

```text
If mapping confidence is low, ask the user to select among candidate industries.
If the company is diversified, allow weighted industry mapping.
```

## 3. Assumption suggestion service

Service name:

```text
valuationAssumptionSuggestionService
```

Input:

```json
{
  "company_id": "...",
  "valuation_type": "fcff",
  "country": "India",
  "damodaran_industry": "Auto Parts",
  "company_financials": {
    "revenue": 1000,
    "ebit": 100,
    "tax_rate": 0.25,
    "invested_capital": 900,
    "non_cash_wc": 90
  },
  "mode": "quick"
}
```

Output:

```json
{
  "suggested_assumptions": {
    "revenue_growth_year_1_2": 0.12,
    "revenue_growth_year_3_5": 0.07,
    "target_pre_tax_operating_margin": 0.10,
    "sales_to_capital_ratio": 1.8,
    "non_cash_wc_to_sales": 0.09,
    "terminal_roc": 0.10,
    "terminal_reinvestment_rate": 0.35
  },
  "industry_priors": {},
  "diagnostics": [],
  "required_user_confirmations": []
}
```

## 4. DCF diagnostics service

Service name:

```text
valuationDiagnosticsService
```

Responsibilities:

```text
Check growth assumptions.
Check margin assumptions.
Check reinvestment assumptions.
Check ROC/WACC consistency.
Check terminal assumptions.
Check working capital treatment.
Check financing/dilution risk.
Return severity-tagged warnings.
```

Severity levels:

```text
info
watch
warning
critical
```

Example output:

```json
{
  "severity": "warning",
  "category": "reinvestment_consistency",
  "message": "The valuation assumes 18% revenue growth but only 2% of sales in reinvestment. This is below the industry net capex and sales-to-capital benchmark. Growth may be underfunded.",
  "affected_assumption": "sales_to_capital_ratio",
  "suggested_action": "Lower growth, lower sales-to-capital, or explain why this company is more capital efficient than the industry."
}
```

---

# API routes

## Benchmark routes

```text
GET /api/valuation/benchmarks/india/industries
GET /api/valuation/benchmarks/india/industry/{industryName}/fundamentals
GET /api/valuation/benchmarks/india/industry/{industryName}/margins
GET /api/valuation/benchmarks/india/industry/{industryName}/reinvestment
GET /api/valuation/benchmarks/india/industry/{industryName}/growth
GET /api/valuation/benchmarks/india/industry/{industryName}/financing-flows
```

## Assumption routes

```text
POST /api/valuation/assumptions/suggest
POST /api/valuation/assumptions/diagnose
POST /api/valuation/assumptions/compare-to-industry
```

## DCF routes

```text
POST /api/valuation/dcf/fcff/run
POST /api/valuation/dcf/fcff/reverse
POST /api/valuation/dcf/fcff/scenarios
```

## Industry mapping routes

```text
GET /api/valuation/industry-mapping/{companyId}
POST /api/valuation/industry-mapping/{companyId}
GET /api/valuation/industry-mapping/suggestions?query={query}
```

---

# Frontend requirements

## 1. Industry benchmark panel

Add a panel inside the valuation tool:

```text
Selected Damodaran Industry
Sample size
Data version
Margin benchmarks
Reinvestment benchmarks
Growth benchmarks
Return benchmarks
Financing behavior
```

This panel should be visible in both quick and advanced mode.

## 2. Assumption workbench

The central valuation screen should show assumptions like this:

| Assumption | Company current | Industry prior | User case | Diagnostic |
|---|---:|---:|---:|---|
| Revenue growth | 8% | 6% | 12% | Requires explanation |
| Pre-tax operating margin | 9% | 11% | 15% | Aggressive |
| Sales-to-capital | 1.4x | 1.9x | 2.5x | More efficient than industry |
| Non-cash WC/Sales | 12% | 9% | 8% | Reasonable |
| ROC | 10% | 12% | 18% | Needs moat explanation |

## 3. Quick valuation screen

Suggested structure:

```text
Step 1: Company and industry
Step 2: Current financials
Step 3: Auto-suggested assumptions
Step 4: User confirms or edits assumptions
Step 5: Valuation output
Step 6: Diagnostics and what-has-to-be-true
```

## 4. Advanced valuation screen

Suggested tabs:

```text
Overview
Revenue
Margins
Reinvestment
Working Capital
Returns
Cost of Capital
Terminal Value
Scenarios
Diagnostics
Report
```

## 5. Diagnostics panel

The diagnostics panel should be mandatory, not optional.

Each warning should show:

```text
Severity
Assumption affected
Why it matters
Industry benchmark
User assumption
Suggested fix
```

---

# Agent behavior rules

## Rule 1: Separate facts, assumptions, and judgments

The agent should format explanations like this:

```text
Fact: The selected industry has an after-tax adjusted operating margin of X%.
Assumption: Your model assumes a target margin of Y%.
Judgment: This is aggressive because it is materially above the industry benchmark.
What must be true: The company needs durable pricing power or cost advantages.
```

## Rule 2: Do not use industry data mechanically

Bad:

```text
The industry margin is 10%, so I used 10%.
```

Good:

```text
The industry margin is 10%. The company is currently at 6%. I use a fade to 9% in the base case because the company is below industry but has some scale potential. A move to 12% belongs in the bull case unless there is stronger evidence.
```

## Rule 3: Challenge unsupported growth

If the user assumes high growth, ask:

```text
What drives it?
Is it volume, pricing, market share, new markets, acquisitions, or inflation?
What reinvestment is needed?
Does the company earn enough ROC to make this growth value-creating?
```

## Rule 4: Challenge unsupported margin expansion

If target margin exceeds industry benchmark, ask:

```text
What changes structurally?
Gross margin?
SG&A leverage?
R&D scaling?
Lower SBC?
Lower lease costs?
Operating leverage?
```

## Rule 5: Challenge terminal assumptions most aggressively

The terminal period is where DCF manipulation usually happens.

The agent should check:

```text
Terminal growth <= long-term nominal economy growth
Terminal ROC is plausible for a mature company
Terminal reinvestment rate = terminal growth / terminal ROC
Terminal value is not an excessive share of total value without warning
Terminal margin is not permanently above industry without moat explanation
```

## Rule 6: Explain growth quality

Not all growth is valuable.

The agent should explain:

```text
Growth creates value only if ROC > WACC.
Growth is neutral if ROC = WACC.
Growth destroys value if ROC < WACC.
```

## Rule 7: Do not force FCFF on financial firms

If the industry is bank, insurance, brokerage, financial services, or similarly financial:

```text
Disable default FCFF.
Recommend equity valuation.
Use ROE, book equity, payout, and cost of equity.
Use PBV as relative valuation support.
```

---

# Diagnostic library to implement

## Growth diagnostics

```text
GROWTH_ABOVE_INDUSTRY_EXPECTED
GROWTH_ABOVE_HISTORICAL_WITHOUT_NARRATIVE
REVENUE_GROWTH_TERMINAL_TOO_HIGH
EPS_GROWTH_DISCONNECTED_FROM_REVENUE
OPERATING_GROWTH_DISCONNECTED_FROM_REINVESTMENT
```

## Margin diagnostics

```text
TARGET_MARGIN_ABOVE_INDUSTRY
MARGIN_EXPANSION_WITHOUT_DRIVER
GROSS_MARGIN_TOO_LOW_FOR_TARGET_OPERATING_MARGIN
SBC_HEAVY_MARGIN_QUALITY_WARNING
LEASE_HEAVY_MARGIN_QUALITY_WARNING
RD_HEAVY_MARGIN_ADJUSTMENT_REQUIRED
```

## Reinvestment diagnostics

```text
HIGH_GROWTH_LOW_REINVESTMENT
SALES_TO_CAPITAL_ABOVE_INDUSTRY
REINVESTMENT_RATE_ABOVE_100_PERCENT
NEGATIVE_REINVESTMENT_WITH_POSITIVE_GROWTH
DOUBLE_COUNTED_WORKING_CAPITAL
ACQUISITION_DRIVEN_GROWTH_WARNING
```

## Return diagnostics

```text
ROC_BELOW_WACC_WITH_GROWTH
TERMINAL_ROC_BELOW_WACC
TERMINAL_ROC_FAR_ABOVE_INDUSTRY
ROE_BELOW_COST_OF_EQUITY
ROE_DOES_NOT_SUPPORT_PBV_PREMIUM
```

## Financing diagnostics

```text
VALUATION_REQUIRES_EXTERNAL_EQUITY
VALUATION_IGNORES_DILUTION
DEBT_FUNDING_RISK
LEASE_DEBT_RISING
PAYOUT_INCONSISTENT_WITH_REINVESTMENT_NEEDS
```

## Data quality diagnostics

```text
LOW_INDUSTRY_SAMPLE_SIZE
INDUSTRY_MAPPING_LOW_CONFIDENCE
METRIC_NOT_APPLICABLE_FOR_INDUSTRY
NA_VALUE_PRESENT
OUTLIER_INDUSTRY_VALUE
```

---

# Suggested build sequence for Codex/Gemini

## Phase 1: Ingest Batch 02 datasets

Tasks:

```text
1. Create staging tables.
2. Build generic Damodaran spreadsheet parser.
3. Search for header row containing Industry Name.
4. Normalize column names.
5. Convert NA to null.
6. Convert numeric percentages correctly.
7. Store source file and data version.
8. Create unified industry fundamentals view.
9. Add tests with at least 3 industries.
```

Acceptance criteria:

```text
All 8 Batch 02 files load without errors.
Each industry row can be retrieved by industry name.
NA values are null, not zero.
Margin file handles two-row header structure correctly.
Unified view returns one row per industry.
```

## Phase 2: Build benchmark API

Tasks:

```text
1. Add routes for industry list.
2. Add route for full fundamental benchmark package.
3. Add route for individual modules: margins, reinvestment, growth, financing.
4. Add response schemas.
5. Add sample-size and missing-data flags.
```

Acceptance criteria:

```text
Frontend can request all Batch 02 assumptions for a selected industry.
API response clearly separates margin, growth, reinvestment, return, WC, and financing data.
```

## Phase 3: Build assumption suggestion engine

Tasks:

```text
1. Create suggested revenue growth algorithm.
2. Create suggested target margin algorithm.
3. Create suggested sales-to-capital algorithm.
4. Create suggested working capital algorithm.
5. Create suggested terminal ROC algorithm.
6. Return assumptions with explanations and confidence.
```

Acceptance criteria:

```text
Given a company and industry, the system proposes a coherent starting DCF case.
Every suggested assumption includes source and rationale.
User can override every assumption.
```

## Phase 4: Build diagnostics engine

Tasks:

```text
1. Implement growth diagnostics.
2. Implement margin diagnostics.
3. Implement reinvestment diagnostics.
4. Implement return-spread diagnostics.
5. Implement terminal diagnostics.
6. Implement financing/dilution diagnostics.
7. Return severity and suggested fixes.
```

Acceptance criteria:

```text
The system catches high-growth low-reinvestment cases.
The system catches terminal growth and terminal ROC inconsistencies.
The system catches unsupported margin expansion.
The system catches FCFF misuse for financial firms.
```

## Phase 5: Wire into quick DCF

Tasks:

```text
1. Add industry selector.
2. Pull Batch 02 benchmarks into quick valuation.
3. Auto-populate suggested assumptions.
4. Show diagnostics before output.
5. Let user save valuation scenario.
```

Acceptance criteria:

```text
A user can run a quick DCF with industry-informed assumptions in under 2 minutes.
The output shows value, assumptions, and diagnostic warnings.
```

## Phase 6: Wire into advanced DCF

Tasks:

```text
1. Add advanced margin forecast panel.
2. Add reinvestment method selector.
3. Add sales-to-capital and working-capital panels.
4. Add ROC and terminal reinvestment logic.
5. Add scenario comparison.
6. Add exportable valuation memo.
```

Acceptance criteria:

```text
Advanced users can build a full 10-year FCFF forecast.
The model links growth to reinvestment and ROC.
Terminal value is constrained by reinvestment and ROC logic.
```

---

# Prompt for Codex/Gemini to implement this batch

Use this prompt after giving Codex/Gemini the current repo and this MD file.

```text
You are extending the Market Intelligence Agent's valuation module.

Implement Batch 02: DCF Fundamentals, Growth, Margins, Reinvestment, and Financing Benchmarks using the Damodaran India spreadsheet datasets:

- marginIndia.xls/xlsx
- capexIndia.xls/xlsx
- wcdataIndia.xls/xlsx
- roeIndia.xls/xlsx
- fundgrIndia.xls/xlsx
- fundgrEBIndia.xls/xlsx
- histgrIndia.xls/xlsx
- finflowsIndia.xls/xlsx

Build this as the valuation agent's industry fundamental assumption engine.

Requirements:
1. Create database staging tables for each dataset.
2. Build a generic Damodaran spreadsheet parser that finds the header row containing "Industry Name" instead of hardcoding row numbers.
3. Convert "NA" to null, never zero.
4. Normalize column names into stable snake_case database fields.
5. Store source_file, geography, source_update_date, data_version, industry_name, and number_of_firms.
6. Create a unified view called valuation_industry_fundamentals_india.
7. Add API endpoints to list industries and retrieve benchmark packages by industry.
8. Build an assumption suggestion service for FCFF valuation using revenue growth, target margin, sales-to-capital, working capital, ROC, and terminal reinvestment logic.
9. Build a diagnostics service that checks growth, margin, reinvestment, ROC/WACC consistency, terminal value assumptions, and financing/dilution risk.
10. Wire the benchmark package into quick valuation mode and advanced valuation mode.
11. Add tests for normal industries, capital-intensive industries, R&D-heavy industries, and financial-service industries.

Do not treat industry averages as company facts. Use them as priors, sanity checks, and starting assumptions.
Do not force FCFF valuation on banks or financial services.
Do not double count working capital when using sales-to-capital based reinvestment.
Do not allow terminal growth without terminal reinvestment.

Return a step-by-step implementation plan first, then implement in small commits or patches.
```

---

# What this batch enables in the final valuation agent

After Batch 02 is implemented, the valuation agent can do something materially useful:

```text
1. Identify the company's Damodaran industry.
2. Pull industry growth, margin, reinvestment, working capital, ROE, ROC, and financing priors.
3. Suggest a quick valuation case.
4. Let the user override assumptions.
5. Run a DCF.
6. Diagnose whether the DCF is internally consistent.
7. Explain what has to be true for the valuation to work.
```

This is the point where the valuation tool stops being a spreadsheet clone and starts becoming an actual valuation analyst.

---

# Next batch recommendation

The next batch should be:

```text
Batch 03: Accounting Normalization and Intangibles
Files: R&DIndia.xls, goodwillIndia.xls
```

Why next:

```text
Batch 02 already introduced lease and R&D adjusted margins.
Batch 03 should now build the actual adjustment logic for R&D capitalization, goodwill/acquisition quality, and intangible-heavy companies.
```

That batch will improve the agent's ability to value software, pharma, consumer brands, platform companies, and acquisition-heavy companies without blindly trusting accounting earnings.


---

# Regression Addendum: Debt Ratio Regression PDF

## Where this file fits

New source file added:

```text
/debt regression.pdf
Title: Debt Ratio Regression: January 2025
```

This file belongs primarily in **Batch 02**, not Batch 04 or Batch 05.

Reason:

```text
Debt ratio is a core DCF and WACC assumption.
It affects cost of capital, levered beta, after-tax cost of debt, equity value bridge, and target capital structure.
It is not a payout dataset by itself, though it interacts with dividends and buybacks.
```

Use it as a **capital structure prior**, not as a hard rule.

---

## What the regression contributes

The debt regression gives the valuation agent a statistical prior for estimating a company's expected or normal market debt ratio when the user does not have a clear target capital structure.

The dependent variable is:

```text
Debt Ratio = Debt / (Market Value of Equity + Debt)
```

Preferred debt input:

```text
Use market value of debt if available.
If market value of debt is unavailable, use book value of debt.
```

Inputs used by the regression:

| Input | Meaning | Unit convention for implementation |
|---|---|---|
| Effective tax rate | Most recent effective tax rate | Use percent points, e.g. `25`, not `0.25` |
| Expected EPS growth, next 5 years | Analyst estimate, user estimate, or historical proxy | Use decimal, e.g. `0.12` for 12% |
| Institutional holding | Percent of shares held by institutions | Use decimal, e.g. `0.30` for 30% |
| Company age | Years since founding, listing, or usable proxy | Number of years |

Important data-quality rule:

```text
If the predicted value is below zero, set predicted debt ratio to zero.
Do not allow negative debt ratios.
```

The model output is in **percentage points**.

---

## Global debt ratio regression

Use this as the default regression for non-US companies unless the app later builds market-specific versions.

```text
Expected Debt Ratio (%)
= 17.419
- 0.057 × Effective Tax Rate
- 20.401 × Expected EPS Growth Next 5 Years
- 2.153 × Institutional Holding
+ 0.033 × Company Age
```

Example from the source:

```text
Effective tax rate = 25
Expected EPS growth = 0.12
Institutional holding = 0.30
Company age = 37

Expected Debt Ratio
= 17.419 - 0.057(25) - 20.401(0.12) - 2.153(0.30) + 0.033(37)
= 14.12%
```

Implementation:

```python
predicted_debt_ratio_pct = 17.419 - 0.057 * effective_tax_rate_pct - 20.401 * expected_eps_growth_decimal - 2.153 * institutional_holding_decimal + 0.033 * company_age_years
predicted_debt_ratio_pct = max(0, predicted_debt_ratio_pct)
predicted_debt_ratio_decimal = predicted_debt_ratio_pct / 100
```

Model quality:

```text
Global R² ≈ 6.6%.
This is weak.
Use the regression as a loose prior and diagnostic reference, not as an authoritative target.
```

---

## US debt ratio regression

Use only for US companies.

```text
Expected Debt Ratio (%)
= 1.666
- 0.176 × Effective Tax Rate
- 26.978 × Expected EPS Growth Next 5 Years
+ 18.519 × Institutional Holding
+ 0.065 × Company Age
```

Model quality:

```text
US R² ≈ 19.3%.
This is better than the global model but still not strong enough to use mechanically.
```

---

## How this should change the DCF engine

### 1. Add a capital-structure prior service

Create a backend service:

```text
CapitalStructurePriorService
```

Responsibilities:

```text
Input company-level tax rate, expected EPS growth, institutional ownership, company age, country/region.
Select US or global regression.
Return predicted debt ratio, model confidence, and explanation.
Compare predicted debt ratio against current debt ratio.
Suggest whether current leverage is below, near, or above regression-implied leverage.
```

### 2. Add target debt ratio choices in advanced valuation

In advanced valuation mode, user should be able to choose:

| Option | Meaning |
|---|---|
| Current market debt ratio | Use current debt/(debt + market equity) |
| Industry median debt ratio | Use Damodaran industry benchmark from existing data |
| Regression-implied debt ratio | Use this debt regression output |
| User override | User enters explicit target debt ratio |
| Time-varying debt ratio | Fade current ratio toward target ratio over forecast period |

Default behavior:

```text
Use current market debt ratio for near-term WACC.
Use industry median or user target for terminal WACC.
Use regression-implied debt ratio as a sanity check and explanatory diagnostic.
```

### 3. Add leverage diagnostics

Add diagnostic labels:

| Condition | Label |
|---|---|
| Current debt ratio within ±5 percentage points of regression estimate | Normal leverage relative to regression prior |
| Current debt ratio more than 10 percentage points above regression estimate | Higher-than-regression leverage |
| Current debt ratio more than 10 percentage points below regression estimate | Lower-than-regression leverage |
| High expected growth and high debt ratio | Growth funded with leverage risk |
| Low tax rate and high debt ratio | Weak tax-shield rationale |
| Old company, stable cash flow, very low debt | Possible unused debt capacity |

The agent should explain that regression-implied leverage is only a benchmark.
It should not tell the user that the company “should” have that exact debt ratio.

---

## Database additions

Create table:

```sql
CREATE TABLE valuation_debt_ratio_regression_models (
    id UUID PRIMARY KEY,
    model_name TEXT NOT NULL,
    geography TEXT NOT NULL,
    model_date DATE,
    dependent_variable TEXT NOT NULL,
    r_squared NUMERIC,
    adjusted_r_squared NUMERIC,
    intercept NUMERIC NOT NULL,
    effective_tax_rate_coefficient NUMERIC,
    expected_eps_growth_5y_coefficient NUMERIC,
    institutional_holding_coefficient NUMERIC,
    company_age_coefficient NUMERIC,
    output_unit TEXT NOT NULL DEFAULT 'percentage_points',
    source_file TEXT NOT NULL,
    notes TEXT,
    created_at TIMESTAMP DEFAULT now()
);
```

Seed rows:

```text
US Debt Ratio Regression, January 2025
Global Debt Ratio Regression, January 2025
```

Create company-level output table:

```sql
CREATE TABLE valuation_capital_structure_priors (
    id UUID PRIMARY KEY,
    valuation_id UUID NOT NULL,
    model_id UUID REFERENCES valuation_debt_ratio_regression_models(id),
    effective_tax_rate_pct NUMERIC,
    expected_eps_growth_5y NUMERIC,
    institutional_holding NUMERIC,
    company_age_years NUMERIC,
    predicted_debt_ratio_pct NUMERIC,
    predicted_debt_ratio_decimal NUMERIC,
    current_debt_ratio_decimal NUMERIC,
    industry_debt_ratio_decimal NUMERIC,
    selected_target_debt_ratio_decimal NUMERIC,
    selected_target_source TEXT,
    confidence_label TEXT,
    diagnostic_summary TEXT,
    created_at TIMESTAMP DEFAULT now()
);
```

---

## API additions

```text
GET /api/valuation/regression-models/debt-ratio
POST /api/valuation/{valuation_id}/capital-structure-prior
POST /api/valuation/{valuation_id}/target-debt-ratio
```

Example request:

```json
{
  "geography": "Global",
  "effective_tax_rate_pct": 25,
  "expected_eps_growth_5y": 0.12,
  "institutional_holding": 0.30,
  "company_age_years": 37,
  "current_debt_ratio_decimal": 0.18
}
```

Example response:

```json
{
  "predicted_debt_ratio_pct": 14.12,
  "predicted_debt_ratio_decimal": 0.1412,
  "current_debt_ratio_decimal": 0.18,
  "spread_vs_current_pct_points": 3.88,
  "confidence_label": "low_statistical_confidence",
  "diagnostic_summary": "The company's current leverage is modestly above the global regression-implied debt ratio. Use this as a loose benchmark, not a mechanical target."
}
```

---

## UI additions

Add to advanced valuation:

```text
Capital Structure Panel
```

Panel fields:

```text
Current debt ratio
Industry median debt ratio
Regression-implied debt ratio
User-selected target debt ratio
Debt ratio fade schedule
WACC impact
Levered beta impact
```

Add a small warning below regression-implied debt ratio:

```text
Regression-implied debt ratio is a loose statistical prior. It should not override company-specific debt capacity, credit rating, cyclicality, management policy, or regulatory constraints.
```

---

## Agent behavior rules

The agent should say:

```text
The regression suggests a normal debt ratio around X%, but the explanatory power is limited. I would use it as a benchmark, not as a target.
```

The agent should not say:

```text
The correct debt ratio is X%.
```

The agent should connect debt ratio to:

```text
Cost of capital
Levered beta
Default spread
Interest coverage
Tax shield
Financial distress risk
Terminal capital structure
Equity value bridge
```

---

## Codex/Gemini implementation addition

Add this to the Batch 02 implementation prompt:

```text
Also implement the January 2025 debt ratio regression models as a capital-structure prior service. Store US and global regression coefficients, expose an endpoint to calculate regression-implied debt ratio, compare it against current and industry debt ratios, and allow the user to choose current, industry, regression-implied, or custom target debt ratio for WACC. Treat the regression output as a low-confidence prior, not a hard target.
```
