# Codex Implementation Prompt: Valuation Agent Autofill Workflow

## Autofill Workflow Completion Status

Bottom line: the review-to-model workflow is implemented, but source coverage is incomplete. Autofilled assumptions remain draft inputs until explicitly reviewed and atomically promoted.

| Area | Status | Current reality | What remains |
|---|---|---|---|
| Damodaran benchmark ingestion | Partially working | Damodaran benchmark tables and industry prior lookup foundations exist. | Confirm current lookup output matches the fields consumed by the autofill engine and add source metadata per field. |
| Company industry mapping | Working foundation | A persisted revenue-weighted segment mix, strict taxonomy/100% validation, optional source-document provenance, blended priors, draft signature invalidation, and valuation-page editor exist. `companies.damodaran_industry` remains the highest-weight compatibility field. | Add broader authenticated browser coverage and enter reviewed company segment weights; do not infer them. |
| Financial extraction candidates | Working foundation | Filing text, SEC XBRL, and Screener extraction create reviewable candidates with typed text-line, XBRL-fact, or spreadsheet-cell locators. Review deep-links to the owning document; review/override requires a unit; conflicts block promotion; extraction attempts create processing runs. | Add audited PDF bounding boxes, PDF table reconstruction, comparative-column total checks, and broader filing-specific statement mapping. |
| Basic autofill route | Partially working | `/companies/{company_id}/valuation-models/autofill` returns draft assumptions with per-field provenance, placeholder flags, source-age diagnostics, and `source_metadata` promotion-readiness summary. Financial actuals older than 550 days and market prices older than 7 days require review. | Replace remaining generic fallback defaults with source-grounded actuals where possible and make age thresholds configurable only when a concrete use case requires it. |
| Deterministic valuation engine | Working once assumptions exist | The backend can run DCF calculations from an assumption set. | Do not create assumption sets automatically from unreviewed autofill drafts. |
| Full valuation setup draft object | Working | `valuation_setup_drafts` stores owned assumptions, provenance, metadata, warnings, edited fields, reviewed fields, readiness, archive status, and promoted model id. Optimistic version checks reject stale UI writes. | Add automatic expiry only if draft volume becomes material. |
| Per-field assumption source records | Working in draft aggregate | Per-field provenance and review state are persisted in the draft JSON aggregate before model creation. | Consider normalized child rows only if field-level querying/auditing requires them. |
| Source-grounded actual extraction for autofill | Working foundation | Autofill prefers normalized metrics and falls back to promoted legacy metrics only when canonical coverage is absent. Coverage and reconciliation report stale/missing snapshots, currency conflicts, exact values, mismatches, and gaps. Basic shares, acquisitions, lease liabilities, minority interests, preferred stock, and employee options normalize with provenance. | Load representative India/US histories, add broader historical trend use, and remove legacy fallback only after reconciliation proves no loss. |
| Source-labeled assumption UI | Working and durable | The draft page shows provenance, reporting currency, source date range, stale fields, and unknown-freshness fields. It persists edits/reviews, supports refresh/reset/archive, and rejects stale UI writes. | Add focused authenticated browser automation for the complete interaction flow. |
| Safe override handling | Working | Refresh preserves edited assumptions, source changes invalidate stale reviews, and per-field reset restores the latest source-backed value. | Consider a field-level audit table only if aggregate JSON history becomes insufficient. |

### Known Unsafe Placeholders

- `AssumptionAutofillEngine._extract_latest_actuals()` reads the current valuation bridge metrics but does not yet build historical capex or working-capital trend assumptions.
- The autofill engine still falls back to generic values for missing actuals, market price, tax rate, beta, capital structure, and other assumptions when source data is missing. These are labeled `[PLACEHOLDER]` and surfaced through `source_metadata.placeholder_fields`.
- Reporting currency can still fall back to the company or system default when reviewed units, filing metadata, and SEC XBRL units omit an ISO currency. The fallback now carries low confidence and a visible warning.
- Legacy fallback remains necessary when no normalized snapshot exists or when backfill cannot safely reconcile a period. The backfill action reports these gaps and currency conflicts.
- Source age is a review signal, not proof that a value is wrong. A stale source can be accepted only through explicit review or replaced with a user assumption; replacement removes obsolete stale metadata.
- Industry suggestions and every segment allocation require explicit user confirmation. A saved mix is a `User Assumption`; its blended benchmark priors are `Estimate` outputs.
- If one segment lacks a benchmark field, that blended field remains unavailable. The engine does not silently renormalize the remaining weights.

### Revenue-Weighted Industry Mix Contract

`GET/PUT /companies/{company_id}/industry-allocations` stores one current mix
per company. Each allocation separates the company-facing segment label from
the Damodaran taxonomy name and stores `weight_percent`. The implemented basis
is revenue, and weights must total 100% within 0.01 percentage points.

The autofill engine computes each numeric benchmark prior as:

```text
blended prior = sum(segment benchmark value * segment revenue weight)
```

Provenance uses `source_type=industry_benchmark_blend`, includes the full mix
and a stable mix signature, and uses `claim_type=Estimate`. Changing an
allocation invalidates the prior signature and refreshes unedited draft fields
without overwriting user-edited assumptions.

### Approved India Consolidated-Statement Policy

For the initial Adani Ports workflow, use consolidated INR statements and keep
the statement scope visible in extraction candidates, normalized snapshots,
autofill fields, and valuation runs.

- Majority-controlled subsidiaries contribute 100% of consolidated operating
  revenue, EBIT, reinvestment, and FCFF. Do not multiply those operating values
  by the parent's ownership percentage.
- Deduct non-controlling/minority interests once in the equity bridge. Prefer
  an estimated market value; book value is an explicitly labeled estimate.
- Equity-accounted associates and joint ventures stay outside operating FCFF.
  Add only the value of the owned stake as a cross-holding/non-operating asset.
- Never include the same investee in both consolidated operations and the
  cross-holdings adjustment.
- Parent-attributable profit and diluted shares are reconciliation inputs; they
  do not replace consolidated operating FCFF.
- Use a reviewed revenue-weighted operating-country ERP when geographic
  revenue is available. India country ERP is a provisional fallback, not a
  conclusion derived from the NSE listing.

### Next Required Build Sequence

| Phase | Build item | Why now | Acceptance criteria |
|---|---|---|---|
| A | Test and harden financial candidate review/promote | Autofill cannot be trusted until reviewed financials are reliable. | Main-path API tests cover review, override, reject, promote, and currency/unit handling; add edge-case source preservation tests as needed. |
| B | Harden canonical normalized financial storage | The autofill engine needs one authoritative actuals path. | Implemented policy: normalized snapshots win; same-period bridge fallback is limited and labeled; snapshot-absent legacy use remains temporary. |
| C | Complete source-grounded actual extraction | Generic actuals are unsafe valuation inputs. | `_extract_latest_actuals()` returns warnings and source metadata for missing values and supports broader actual fields. |
| D | Return source-labeled autofill drafts | Users and agents need to see where every number came from. | Autofill response includes value, source type, source id/document, formula where relevant, confidence, review status, stale/mock/placeholder flags, and warnings. |
| E | Build review-first UI | Model creation should follow review, not precede it. | Implemented with durable drafts: every assumption is labeled and flagged fields require valid values plus explicit review. |
| F | Create valuation model only from reviewed draft | Prevents placeholder assumptions from becoming official models. | Implemented atomically in the backend; incomplete or foreign-owned drafts are rejected. |

### Defer For Now

- Advanced wizard polish before actuals and provenance are stable.
- AI memo automation based on unreviewed autofill data.
- Automatic model creation from unreviewed draft assumptions.
- Broad provider integrations before the reviewed-financials and source-metadata path is reliable.

## Context

We are building a Damodaran-style valuation agent inside the Market Intelligence Agent app.

The goal is not to make the AI guess a valuation. The goal is to build a structured valuation workflow where:

```text
User selects company
+ uploads financial statements
+ chooses country, industry, model, and forecast options
→ app extracts company actuals
→ app pulls Damodaran industry benchmark priors
→ app autofills a draft valuation
→ user reviews and overrides assumptions
→ backend calculates valuation deterministically
→ AI explains, audits, and writes the valuation memo
```

Important principle:

```text
Do not hardcode values directly into valuation formulas.
Use uploaded Damodaran XLS/XLSX files as seed benchmark datasets.
Store benchmark values in normalized database tables or seed JSON.
Then use services to fetch assumptions based on country + Damodaran industry.
```

Bad implementation:

```ts
if (company === "Adani Ports") {
  operatingMargin = 0.28;
  salesToCapital = 1.4;
}
```

Good implementation:

```text
Company: Adani Ports
Country: India
Mapped Damodaran industry: Transportation / Infrastructure-like category
→ fetch industry benchmark priors
→ show source, confidence, and user override controls
```

---

# 1. Product Goal

Build a valuation setup flow where the app can do three things:

1. Extract actual company financials from uploaded statements.
2. Autofill assumption priors from Damodaran industry datasets based on dropdown selections.
3. Clearly separate what is actual company data, what is industry benchmark data, what is formula-derived, and what the user must judge manually.

The user experience should feel like this:

```text
I choose Adani Ports.
I upload the annual report or financial statements.
The app extracts the base-year financials.
The app asks me to confirm the country, currency, Damodaran industry, valuation model, forecast style, and reinvestment method.
Once I confirm those dropdowns, the app autofills a draft DCF and benchmark comparison.
I then edit the assumptions I actually believe.
```

---

# 2. Core User Flow

## Step 1: Company selection

User enters or selects:

```text
Company name: Adani Ports
Ticker: optional
Country: India
Currency: INR
Fiscal year: FY2025, or user-selected year
```

The app should create a valuation setup draft.

Required backend object:

```ts
type ValuationSetupDraft = {
  companyName: string;
  ticker?: string;
  country: string;
  currency: string;
  fiscalYear?: string;
  selectedIndustry?: string;
  selectedModel?: ValuationModel;
  selectedForecastStyle?: ForecastStyle;
  selectedReinvestmentMethod?: ReinvestmentMethod;
  uploadedStatementIds: string[];
  status: "draft" | "ready_for_review" | "ready_to_value";
};
```

---

## Step 2: Financial statement upload

User uploads an annual report, financial statement, or manually enters base-year financials.

The app should try to extract actual company numbers.

### Autofill from uploaded financial statements

These are company-specific actuals, not assumptions:

| Category | Fields to extract |
|---|---|
| Income statement | revenue, EBIT, EBITDA if disclosed, net income, interest expense, tax expense |
| Cash flow statement | depreciation and amortization, capex, acquisitions, dividends paid, buybacks, stock issuance, debt issued, debt repaid |
| Balance sheet | cash, debt, lease liabilities, receivables, inventory, payables, total assets, book equity, goodwill |
| Share data | basic shares, diluted shares, share count change, if available |
| Segment data | segment revenue, segment EBIT, geography, if available |

### Required behavior

Every extracted value must have:

```text
value
currency
period
source document
source page or section if available
confidence level
manual override flag
```

Suggested data type:

```ts
type ExtractedFinancialLineItem = {
  companyId: string;
  statementId: string;
  fiscalPeriod: string;
  lineItem: string;
  value: number | null;
  currency: string;
  sourceLabel?: string;
  sourceLocation?: string;
  confidence: "high" | "medium" | "low";
  userOverride: boolean;
};
```

If extraction confidence is low, the UI should ask the user to confirm or manually edit.

---

## Step 3: Dropdowns that drive autofill

These fields should become structured dropdowns, not free-text only.

### Dropdown A: Country

Example:

```text
India
United States
Global
```

For now, prioritize India because the uploaded Damodaran files are India-specific.

Country controls:

```text
which Damodaran country dataset to use
which industry benchmark set to use
which relative pricing file to query
which macro sensitivity file to query
which currency and country-risk warnings to show
```

---

### Dropdown B: Currency

Example:

```text
INR
USD
```

Rules:

```text
Cash flows and discount rate must be in the same currency.
If user chooses INR, WACC inputs should be INR-consistent.
If user chooses USD, cash flows must be converted or modeled in USD.
```

Block or warn against:

```text
INR cash flows discounted using USD risk-free rate without conversion.
```

---

### Dropdown C: Damodaran Industry

The app should suggest likely industries, but user must confirm.

For Adani Ports, candidates might include:

```text
Transportation
Shipping
Infrastructure-like category if available
Engineering/Construction if closest available
Utility/Infrastructure proxy only if justified
```

Do not assume the first match is correct.

The UI should show:

```text
Suggested Damodaran industry
Confidence
Why it was suggested
Alternate industries
User override option
```

Required service:

```ts
IndustryMappingService.suggestDamodaranIndustries(companyProfile)
IndustryMappingService.confirmIndustry(companyId, industryName)
```

Suggested return type:

```ts
type IndustryMappingCandidate = {
  industryName: string;
  confidence: "high" | "medium" | "low";
  reason: string;
  benchmarkAvailability: {
    margins: boolean;
    capex: boolean;
    workingCapital: boolean;
    growth: boolean;
    multiples: boolean;
    payout: boolean;
    macro: boolean;
    volatility: boolean;
  };
};
```

---

### Dropdown D: Valuation model

Options:

```text
FCFF DCF
FCFE DCF
Dividend Discount Model
Relative Valuation
Reverse DCF
```

Default rules:

| Company type | Default model |
|---|---|
| Normal non-financial operating business | FCFF DCF |
| Stable dividend-paying company | FCFF plus FCFE or dividend check |
| Bank or insurer | Equity valuation, not FCFF |
| Loss-making young company | Revenue-to-margin lifecycle DCF |
| Commodity/cyclical | Normalized scenario DCF |
| Distressed company | Probability-weighted or distressed claim model |

For Adani Ports, default should be:

```text
Primary: FCFF DCF
Secondary: relative valuation cross-check
Optional: FCFE/payout check
```

Validation:

```text
FCFF must use WACC.
FCFE must use cost of equity.
Dividend model must use cost of equity.
Do not mix claimholder cash flows and discount rates.
```

---

### Dropdown E: Forecast style

Options:

```text
Simple forecast
Industry-based forecast
Custom manual forecast
Segment-level forecast
```

Behavior:

| Forecast style | App behavior |
|---|---|
| Simple forecast | Minimal inputs, broad defaults, limited detail |
| Industry-based forecast | Use Damodaran industry priors as starting assumptions |
| Custom manual forecast | User enters assumptions, app still shows benchmarks |
| Segment-level forecast | User enters business segments and maps each to an industry |

For v1, build:

```text
Simple forecast
Industry-based forecast
Custom manual forecast
```

Segment-level can be phase 2.

---

### Dropdown F: Reinvestment method

Options:

```text
Sales-to-capital method
Detailed capex + working capital method
Reinvestment-rate method
```

Default for quick valuations:

```text
Sales-to-capital method
```

Reason:

```text
It links revenue growth to reinvestment and prevents fake free cash flow.
```

Formula:

```text
Incremental Revenue_t = Revenue_t - Revenue_{t-1}
Reinvestment_t = Incremental Revenue_t / Sales-to-Capital Ratio_t
FCFF_t = EBIT_t × (1 - Tax Rate_t) - Reinvestment_t
```

Important guardrail:

```text
If using sales-to-capital, do not separately subtract change in working capital unless the model explicitly decomposes fixed capital and working capital.
```

---

### Dropdown G: Accounting normalization

Options:

```text
Use reported numbers
Adjust for leases
Adjust for R&D
Run goodwill/acquisition diagnostics
Advanced normalization
```

For Adani Ports, likely defaults:

```text
Use reported numbers as base
Check lease adjustment if lease liabilities are material
Run goodwill/acquisition diagnostics if acquisitions/goodwill are material
Do not default to R&D capitalization unless R&D is material
```

Required behavior:

```text
Show reported metrics and adjusted metrics side by side.
Do not silently change EBIT or invested capital.
Every adjustment needs formula, source, and explanation.
```

---

### Dropdown H: Relative valuation method

Options:

```text
EV/EBITDA
EV/EBIT
EV/Sales
PE
PBV
EV/Invested Capital
```

For non-financial infrastructure/transportation companies, suggest:

```text
Primary: EV/EBITDA, EV/EBIT, EV/Sales, EV/Invested Capital
Secondary: PE
Lower priority: PBV, unless equity return analysis is central
```

Required comparisons:

```text
Company current multiple
Damodaran industry benchmark multiple
DCF-implied multiple
Country-level benchmark multiple
```

Example output:

```text
Your DCF implies 18.2x EV/EBITDA.
The selected Damodaran industry benchmark is 13.5x.
This premium needs to be justified by higher growth, higher margins, lower risk, or better ROC.
```

---

### Dropdown I: Payout and FCFE check

Options:

```text
Ignore payout for now
Dividend sustainability check
FCFE valuation
Buyback quality check
```

For v1, implement:

```text
Dividend sustainability check
FCFE cross-check
```

Autofill from uploaded financials:

```text
dividends paid
buybacks
stock issuances
net income
capex
depreciation
working capital change
net debt issued
```

Autofill from Damodaran benchmarks:

```text
industry dividend payout
industry dividend yield
industry net cash returned to FCFE
industry FCFE behavior
```

---

### Dropdown J: Macro sensitivity

Options:

```text
No macro scenario
Interest-rate sensitivity
GDP cyclicality
Inflation sensitivity
Currency sensitivity
Full macro scenario
```

For v1, implement benchmark lookup and display only.

Do not make macro automatically change valuation assumptions yet unless the user chooses a scenario.

Autofill from Damodaran macro files:

```text
industry duration
industry cyclicality
industry inflation sensitivity
industry currency sensitivity
```

Output:

```text
Rate sensitivity: low / medium / high
Cyclicality: defensive / moderate / high
Inflation exposure: helped / hurt / unclear
Currency exposure: direction needs review
```

---

# 3. What the App Should Autofill

## 3.1 Autofill from uploaded company financials

These are actual company values.

```text
Revenue
EBIT
EBITDA
Net income
Depreciation and amortization
Capital expenditures
Change in working capital
Cash
Debt
Lease liabilities
Interest expense
Tax expense
Effective tax rate
Goodwill
Acquisitions
Dividends
Buybacks
Stock issuances
Shares outstanding
Book equity
Total assets
```

Derived from company financials:

```text
Operating margin = EBIT / Revenue
EBITDA margin = EBITDA / Revenue
Effective tax rate = Tax expense / Pre-tax income
Net debt = Debt - Cash
Reinvestment = Net capex + Change in non-cash working capital
Current ROC = EBIT(1 - tax rate) / Invested capital
Current ROE = Net income / Book equity
FCFF = EBIT(1 - tax rate) - Reinvestment
FCFE = Net income - Net capex - Change in non-cash working capital + Net debt issued
```

---

## 3.2 Autofill from Damodaran industry dropdowns

Once country and industry are selected, the app can autofill priors.

| Module | Autofill fields |
|---|---|
| Margin prior | gross margin, operating margin, lease-adjusted margin, R&D-adjusted margin, EBITDA margin |
| Reinvestment prior | sales-to-capital ratio, net capex/sales, capex/depreciation |
| Working capital prior | receivables/sales, inventory/sales, payables/sales, non-cash WC/sales |
| Return prior | ROE, R&D-adjusted ROE, ROC, reinvestment rate |
| Growth prior | historical revenue CAGR, expected revenue growth, expected EPS growth, sustainable EBIT growth |
| Financing prior | net equity issuance behavior, net debt change, lease debt change |
| Relative pricing prior | PE, PBV, EV/Sales, EV/EBITDA, EV/EBIT, EV/Invested Capital |
| Payout prior | dividend payout, dividend yield, net cash returned to FCFE |
| Macro prior | duration, cyclicality, inflation sensitivity, currency sensitivity |
| Volatility prior | equity volatility, firm value volatility |

Every prior must show:

```text
value
source file
source industry
country
data date/version
sample size if available
confidence
user override status
```

---

## 3.3 Autofill from formulas

The backend can calculate:

```text
Revenue forecast
EBIT forecast
After-tax EBIT
Reinvestment
FCFF
Terminal reinvestment rate
Terminal value
Operating asset value
Equity value
Value per share
DCF-implied EV/Sales
DCF-implied EV/EBITDA
DCF-implied PE
Sensitivity table
Scenario table
Reverse DCF implied growth or margin
```

---

# 4. What the User Must Add Manually

The system should make this clear in the UI.

The user must provide or confirm:

```text
Business story
Correct industry mapping
Forecast assumptions they actually believe
Company-specific drivers
Terminal value story
Cost of capital judgment if data is incomplete
Whether to use reported or adjusted accounting numbers
Whether current year is normal or unusual
Whether growth is organic or acquisition-driven
Whether industry benchmarks are good comparables
```

For Adani Ports, user-specific drivers may include:

```text
Cargo volume growth
Port capacity expansion
Tariff/realization assumptions
Utilization
Logistics segment growth
SEZ contribution
Capex pipeline
Debt-funded expansion plan
Regulatory/concession risk
Competition from other ports
India trade and infrastructure thesis
```

The AI may suggest questions, but it should not invent the thesis.

---

# 5. Required Data Architecture

## 5.1 Raw Damodaran file storage

Create a folder like:

```text
/data/damodaran/raw/
```

Store uploaded XLS/XLSX files there.

Do not delete source files after ingestion.

---

## 5.2 Normalized benchmark tables

Use or adapt tables from the existing valuation batch MDs.

Minimum v1 tables:

```text
damodaran_dataset_files
company_industry_mapping
industry_benchmark_metrics
country_market_stats
damodaran_industry_margin_benchmarks
damodaran_industry_capex_benchmarks
damodaran_industry_working_capital_benchmarks
damodaran_industry_roe_benchmarks
damodaran_industry_fundamental_operating_growth
damodaran_industry_historical_growth
industry_dividend_policy_benchmarks
industry_fcfe_payout_benchmarks
sector_macro_sensitivity_benchmarks
industry_volatility_benchmarks
```

If the existing app prefers JSON seed files instead of DB tables for v1, that is acceptable, but keep the same logical schema.

---

## 5.3 Company financial actuals tables

Minimum v1 tables:

```text
companies
company_financial_statements
company_financial_line_items
valuation_runs
valuation_assumptions
valuation_outputs
assumption_sources
```

Suggested assumption source record:

```ts
type AssumptionSource = {
  assumptionKey: string;
  value: number | string | null;
  sourceType: "company_actual" | "industry_benchmark" | "formula" | "user_input" | "agent_suggestion";
  sourceFile?: string;
  sourceIndustry?: string;
  sourceDocumentId?: string;
  sourceLocation?: string;
  confidence: "high" | "medium" | "low";
  overriddenByUser: boolean;
};
```

---

# 6. Required Backend Services

## 6.1 DamodaranBenchmarkIngestionService

Responsibilities:

```text
Read XLS/XLSX files from raw folder.
Detect the Industry Averages sheet.
Find header row dynamically by locating Industry Name.
Normalize column names.
Convert NA and blanks to null.
Convert percentages consistently.
Store source metadata.
Store normalized benchmark rows.
Log ingestion status.
```

Do not hardcode row numbers.

---

## 6.2 CompanyFinancialExtractionService

Responsibilities:

```text
Parse uploaded financial statement data.
Extract key line items.
Store company actuals.
Attach source and confidence.
Allow manual correction.
```

For v1, manual entry is acceptable if document extraction is not ready.

But the data model should support uploaded-document extraction later.

---

## 6.3 IndustryMappingService

Responsibilities:

```text
Suggest Damodaran industries for a company.
Show candidate industries.
Require user confirmation when confidence is not high.
Store mapping.
Allow override.
Support diversified companies later.
```

---

## 6.4 IndustryAssumptionService

Responsibilities:

```text
Given country + Damodaran industry, return assumption priors.
Merge margin, reinvestment, working capital, growth, return, payout, pricing, macro, and volatility benchmarks.
Attach source metadata.
Return confidence levels and warnings.
```

Suggested API:

```http
GET /api/valuation/assumption-priors?country=India&industry=Transportation
```

Suggested response shape:

```json
{
  "country": "India",
  "industry": "Transportation",
  "dataVersion": "2026-01",
  "marginPriors": {},
  "reinvestmentPriors": {},
  "workingCapitalPriors": {},
  "returnPriors": {},
  "growthPriors": {},
  "relativePricingPriors": {},
  "payoutPriors": {},
  "macroPriors": {},
  "volatilityPriors": {},
  "warnings": [],
  "sourceSummary": []
}
```

---

## 6.5 ValuationSetupAutofillService

Responsibilities:

```text
Combine company actuals + industry priors + formula-derived fields.
Produce a valuation setup draft.
Mark every field by source type.
Never overwrite user-edited fields without confirmation.
```

Suggested behavior:

```text
If user selects a new industry, recalculate benchmark priors.
If user already overrode an assumption, ask before replacing it.
If company actuals conflict with industry priors, show the difference.
```

---

## 6.6 ValuationDiagnosticsService

Responsibilities:

```text
Flag unreasonable assumptions.
Compare company vs industry.
Compare DCF-implied multiples vs industry multiples.
Warn about growth without reinvestment.
Warn about terminal growth without terminal reinvestment.
Warn about wrong valuation model for financial companies.
Warn if user selected weak industry mapping.
```

Required diagnostics:

```text
Growth above industry without story
Margin above industry without story
Sales-to-capital too aggressive
ROC below WACC but growth assumed to create value
Terminal growth too high
Terminal reinvestment missing
DCF-implied multiple far above industry
Dividend exceeds FCFE
Industry benchmark sample size weak
```

---

# 7. Required API Endpoints

Use existing app conventions if they differ, but implement this functionality.

```http
POST /api/valuation/company/select
POST /api/valuation/financials/upload
POST /api/valuation/financials/manual
GET  /api/valuation/industries/suggest?companyId=...
POST /api/valuation/industries/confirm
GET  /api/valuation/assumption-priors?country=India&industry=...
POST /api/valuation/setup/autofill
PATCH /api/valuation/setup/assumption
POST /api/valuation/run/fcff
GET  /api/valuation/run/:id/diagnostics
```

For v1, `financials/upload` can store file metadata and allow manual input if parser is not implemented yet.

---

# 8. Required Frontend Screens

## 8.1 Valuation setup wizard

Steps:

```text
1. Company
2. Financials
3. Country, currency, industry
4. Valuation model
5. Forecast style
6. Reinvestment method
7. Accounting normalization
8. Review autofilled assumptions
9. Run valuation
```

---

## 8.2 Financial actuals review screen

Show extracted company values:

```text
Revenue
EBIT
EBITDA
Net income
Tax
Debt
Cash
Capex
Depreciation
Working capital
Shares
Dividends
```

Each field should show:

```text
value
source
confidence
edit button
```

---

## 8.3 Industry and benchmark screen

Show:

```text
Selected country
Selected currency
Suggested Damodaran industry
Alternate industries
Benchmark availability
Confirm industry button
```

---

## 8.4 Autofilled assumptions screen

Use a table:

| Assumption | Value | Source | Confidence | User override |
|---|---:|---|---|---|
| Revenue growth Y1 | 8.0% | industry expected growth + company trend | medium | edit |
| Target EBIT margin | 27.0% | selected industry margin | medium | edit |
| Sales-to-capital | 1.3x | Damodaran capex file | medium | edit |
| Terminal growth | 5.0% | user/default macro constraint | low | edit |

Color or label source type:

```text
Company actual
Industry prior
Formula-derived
User input
Agent suggestion
```

---

## 8.5 What user must decide panel

Show this explicitly:

```text
The app has built a first draft. You still need to decide:
- Is this the right industry benchmark?
- Is current year normal?
- What revenue growth do you actually believe?
- What target margin is realistic?
- How much reinvestment is needed?
- What should the mature company look like?
- Does the story justify the valuation premium or discount?
```

---

# 9. Implementation Phases

## Phase 0: Audit placement

Before coding, inspect current repo architecture.

Tasks:

```text
Find existing valuation-related files.
Find backend framework and route conventions.
Find database migration setup.
Find frontend structure.
Find where docs should live.
Read existing AGENTS.md or equivalent instructions.
```

Output:

```text
Where to place ingestion code
Where to place valuation services
Where to place frontend valuation wizard
Which docs need updating
Any conflicts with existing architecture
```

Do not implement yet in Phase 0.

---

## Phase 1: Damodaran file ingestion and lookup

Build ingestion for the uploaded benchmark files.

Acceptance criteria:

```text
Can ingest India margin/capex/working capital/growth/multiple/payout/macro/volatility files.
Can lookup benchmark priors by country + industry.
Can return source metadata and sample size.
NA values are preserved as null.
No benchmark values are hardcoded inside formulas.
```

---

## Phase 2: Company financial actuals

Build manual entry first if document extraction is hard.

Acceptance criteria:

```text
User can input or confirm Adani Ports base-year financials.
System stores actuals with source type company_actual.
Derived metrics calculate correctly.
User can edit extracted values.
```

---

## Phase 3: Industry mapping and dropdown autofill

Acceptance criteria:

```text
User can select company, country, currency, and Damodaran industry.
Industry dropdown fetches benchmark availability.
Selected industry populates assumption priors.
User can override industry.
```

---

## Phase 4: Valuation setup autofill

Acceptance criteria:

```text
App combines company actuals and industry priors into a draft valuation setup.
Every autofilled assumption has source metadata.
User overrides are preserved.
Changing industry updates priors only after confirmation.
```

---

## Phase 5: Basic FCFF run from autofilled assumptions

Acceptance criteria:

```text
System can run a simple FCFF DCF using autofilled and user-confirmed assumptions.
Outputs revenue forecast, EBIT forecast, reinvestment, FCFF, terminal value, equity bridge, and value per share.
Diagnostics run after valuation.
```

---

# 10. Guardrails

Implement these as validation rules or warnings.

```text
Do not treat industry priors as company facts.
Do not hardcode Adani Ports-specific assumptions.
Do not use EPS growth as FCFF operating growth.
Do not double count working capital when using sales-to-capital.
Do not allow terminal growth without terminal reinvestment.
Do not mix FCFF with cost of equity or FCFE with WACC.
Do not silently overwrite user assumptions.
Do not use EV/EBITDA for banks and insurers as primary valuation.
Do not add real option value by default.
Do not let the LLM calculate final valuation values without deterministic backend formulas.
```

---

# 11. Specific Adani Ports Example to Test

Create a test flow using placeholder data if real financials are not available yet.

Test scenario:

```text
Company: Adani Ports
Country: India
Currency: INR
Valuation model: FCFF DCF
Forecast style: Industry-based forecast
Reinvestment method: Sales-to-capital
Industry: user-selected from suggested Damodaran industries
Relative checks: EV/EBITDA and EV/Sales
Payout check: dividend sustainability
Macro: display industry macro sensitivity only
```

Expected behavior:

```text
App extracts or accepts company actuals.
App asks user to confirm industry.
App pulls industry priors.
App autofills draft assumptions.
App shows source labels for every assumption.
App allows overrides.
App runs a deterministic FCFF valuation.
App compares DCF-implied multiples to industry multiples.
App lists warnings and what the user still needs to decide.
```

---

# 12. Docs to Update

After implementation or architecture placement, update:

```text
README.md
architecture docs
database schema docs
API docs
local development docs
execution runbook
AGENTS.md or coding-agent instructions
valuation agent docs
```

Docs should explain:

```text
Where Damodaran raw files live
How ingestion works
How industry mapping works
How assumption autofill works
Difference between company actuals, industry priors, formula outputs, and user inputs
How to run ingestion locally
How to test Adani Ports flow
```

---

# 13. Final Instruction to Codex

Start with Phase 0 and Phase 1 only.

Do not build the full valuation engine immediately.

First create the data foundation:

```text
Damodaran file ingestion
normalized benchmark storage
industry lookup service
industry assumption prior API
source metadata and confidence labels
```

Then implement the valuation setup autofill workflow.

Only after that should the FCFF valuation engine use these autofilled assumptions.
