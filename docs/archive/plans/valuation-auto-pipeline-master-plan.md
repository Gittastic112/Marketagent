# Market Intelligence + Valuation Agent: Automated Research-to-Valuation Master Build Plan

**Document purpose:** This is the next-step execution plan for turning the current local-first Market Intelligence Engine into a stronger investment research and valuation system.

**Target end-state:**

```text
Choose company
→ automatically fetch all relevant filings and source documents
→ extract financial statements and key disclosures
→ normalize all company metrics
→ map company to industry and country context
→ auto-fill valuation assumptions with source labels
→ run deterministic valuation automatically
→ show diagnostics, reverse DCF, relative valuation, and thesis impact
→ monitor future filings/news/events for changes to the thesis and valuation
```

**Important principle:** The system should become more automated, but not less auditable. Every number must have a source, formula, confidence label, and review status.

**Latest checkpoint:** See [trust-and-evidence-checkpoint-2026-07-22.md](trust-and-evidence-checkpoint-2026-07-22.md) for the implemented evidence/coverage/source-age foundation and the acceptance criteria for proposed follow-up work. That checkpoint supersedes stale statements in this long-form plan where code has already advanced.

---

## Current Priority - Source-Grounded Autofill First

The next roadmap work must start with source-grounded reviewed financials and source-labeled assumptions. The current autofill foundation exists, but it is not a trusted automation workflow yet because company actual extraction is still incomplete and placeholder defaults can still enter draft assumptions.

Required next order:

1. Harden source-grounded reviewed financials.
2. Decide and document the canonical normalized financial read/write path.
3. Add assumption source metadata for every autofilled field.
4. Generate safe autofill drafts with warnings instead of silently creating trusted assumptions.
5. Build a review UI before automatic valuation model creation.

Defer advanced wizard polish, AI memo automation, and broader provider expansion until actuals, provenance, and review status are stable.

---

# 0. Executive Summary

The existing app already has a serious foundation:

- FastAPI backend.
- Database-backed companies, sources, documents, events, alerts, portfolios, market prices, valuation models, thesis notes, evidence, decisions, narratives, AI outputs, macro data, and Damodaran benchmarks.
- Deterministic valuation services including FCFF DCF, WACC, diagnostics, sensitivity analysis, reverse DCF, relative valuation, macro sensitivity, and real-options support.
- RSS and SEC ingestion foundations.
- India support structurally present, but mostly manual.
- Strong backend test coverage.
- Broad frontend routes, but uneven trust/parity across pages.

The next product direction should be:

> **Valuation-first investment research cockpit.**

The product should not be positioned as an AI stock picker. It should be positioned as a system that helps users turn filings, financial statements, benchmarks, assumptions, and thesis notes into **auditable valuations and monitored investment theses**.

The near-term product should focus on one killer workflow:

```text
Company setup
→ filing/data acquisition
→ financial extraction and review
→ industry mapping
→ valuation assumption autofill
→ deterministic DCF
→ relative valuation and reverse DCF
→ diagnostics
→ AI-assisted memo
→ thesis monitoring
```

This document breaks that into implementation phases, backend/database/API/UI requirements, data-source requirements, security requirements, and acceptance criteria.

---

# 1. Non-Negotiable Product Principles

## 1.1 Deterministic math first, AI second

The valuation engine must calculate numbers through deterministic backend code.

AI may:

- Explain results.
- Summarize filings.
- Map narrative into suggested assumptions.
- Draft memos.
- Highlight missing data.
- Challenge assumptions.
- Classify events as thesis-supporting, thesis-weakening, or irrelevant.

AI must not:

- Invent financial statement values.
- Freehand valuation math.
- Silently change assumptions.
- Treat benchmark averages as company facts.
- Issue buy/sell recommendations.
- Hide source uncertainty.

## 1.2 Every output needs provenance

Every displayed number or conclusion needs metadata:

```text
value
source_type
source_name
source_document_id
source_line_or_section
calculation_formula
calculation_version
confidence_label
review_status
last_updated_at
user_override_status
```

Example:

```text
Revenue FY2025: ₹X
Source: Uploaded annual report
Source section: Consolidated statement of profit and loss
Extraction method: PDF table extraction
Review status: User reviewed
Confidence: High
```

Example:

```text
Target operating margin: 28%
Source: User override
Industry benchmark: Damodaran India Transportation margin
Status: Aggressive versus benchmark
Reason required: Yes
```

## 1.3 No black-box valuation

The app should never simply say:

```text
Fair value = ₹X
```

It should say:

```text
Base value: ₹X/share
Range: ₹A to ₹B/share
Current price: ₹Y
Main drivers:
- target operating margin
- revenue growth fade
- sales-to-capital ratio
- WACC
- terminal growth
Warnings:
- terminal value is 71% of total value
- target margin exceeds industry benchmark
- current industry mapping is unreviewed
```

## 1.4 Automation should stop before judgment

The system can fetch, extract, normalize, calculate, and flag. The user still needs to approve:

- Company identity.
- Filings used.
- Extracted financial statements.
- Industry mapping.
- Key assumptions.
- Valuation model.
- Final memo.
- Thesis impact.
- Any portfolio decision.

## 1.5 Security is product quality, not a later add-on

This product will handle private research, portfolio data, API keys, uploaded filings, AI prompts, and potentially sensitive investment notes. It must remain local-first until security is upgraded.

Do not build public deployment, broker sync, or multi-user access until the security foundation is complete.

---

# 2. Current State: What Exists vs What Needs Work

## 2.1 Strong existing areas

| Area | Current state | What to do next |
|---|---|---|
| Backend architecture | Broad FastAPI service layer exists | Preserve and harden |
| Database models | Many core models exist | Add provenance/versioning where missing |
| Valuation engine | Strongest module | Consolidate into guided workflow |
| DCF math | Exists | Add assumption source labels and review gates |
| WACC / diagnostics / reverse DCF | Exists | Improve UI and integration |
| Damodaran benchmark ingestion | Partially working | Make it a first-class autofill engine |
| SEC ingestion | Working for configured US companies | Extend into automatic statement extraction |
| RSS/news ingestion | Working | Improve event-to-thesis workflow |
| Portfolio tracking | Working | Add valuation gap and freshness labels |
| AI memo generation | Partially working | Add strict review/source/limitation UI |
| Data-state UI | Exists | Apply consistently across all routes |

## 2.2 Weak or incomplete areas

| Area | Current problem | Fix |
|---|---|---|
| Frontend parity | Some pages may imply more than backend supports | Route-by-route trust audit |
| Market regime | Mock page can be misleading | Hide, quarantine, or build real backend |
| India support | Mostly manual, no complete NSE/BSE automation | Build manual-first India workflow, then add providers |
| Financial statement ingestion | Not fully trusted | Build extraction + review + normalization pipeline |
| Industry mapping | Fragile | Add user confirmation and mapping confidence |
| Market prices | May be manual/stale | Add provider health and price freshness |
| AI outputs | May sound too confident | Add review workflow and no-advice language |
| Security | No public-ready auth/authorization | Keep local-first, build security baseline |
| Evidence trail | Models exist but UX is weak | Build source-to-alert-to-thesis traceability |
| Docs drift | Docs can become stale | Add documentation update requirements per phase |

---

# 3. Target End-to-End Workflow

## 3.1 The ideal automated workflow

```text
1. User chooses company
2. System resolves identity
3. System detects country, exchange, ticker, identifiers, currency
4. System fetches available filings and disclosures
5. System downloads selected filings
6. System extracts financial statements and key notes
7. System maps raw line items into canonical financial metrics
8. System normalizes operating metrics
9. System maps company to Damodaran/industry benchmark
10. System auto-fills assumption priors
11. User reviews and overrides assumptions
12. System runs FCFF DCF
13. System runs WACC, sensitivity, scenarios, reverse DCF, and relative valuation
14. System generates diagnostics
15. AI drafts memo using deterministic outputs and source-backed facts
16. User reviews memo and saves thesis/decision
17. Future filings/news/events are monitored against thesis and valuation assumptions
```

## 3.2 The realistic near-term workflow

Until full automation is built, use this staged version:

```text
1. User chooses company
2. App creates normalized company record
3. User configures or confirms sources
4. US: app fetches SEC filings
5. India: user uploads annual report / filing manually
6. App extracts financial statement candidates
7. User reviews extracted statements
8. User confirms industry mapping
9. App auto-fills assumptions from Damodaran industry data
10. User edits assumptions
11. App runs DCF and diagnostics
12. App generates memo
13. User saves thesis and evidence
```

## 3.3 Product promise after next major build

The product should be able to say:

> “Give me a company and its filings. I will build a source-labeled valuation draft, show what assumptions matter, compare it to industry pricing, and tell you what needs to be true.”

---

# 4. Master Architecture

## 4.1 High-level module map

```text
Market Intelligence + Valuation Agent
│
├── Company Identity Layer
│   ├── company setup wizard
│   ├── ticker/exchange/currency normalization
│   ├── CIK / ISIN / FIGI mapping
│   ├── India symbol mapping
│   └── company source capability profile
│
├── Source & Provider Layer
│   ├── SEC EDGAR provider
│   ├── India filings provider
│   ├── RSS/news provider
│   ├── market data provider
│   ├── macro provider
│   ├── benchmark provider
│   └── provider health monitor
│
├── Filing & Document Layer
│   ├── filing search
│   ├── filing download
│   ├── document storage
│   ├── document parsing
│   ├── document sectioning
│   ├── evidence snippets
│   └── extraction audit trail
│
├── Financial Statement Extraction Layer
│   ├── XBRL parser
│   ├── PDF/table parser
│   ├── manual statement entry
│   ├── statement review screen
│   ├── canonical line-item mapper
│   └── metric normalizer
│
├── Valuation Input Layer
│   ├── company historical metrics
│   ├── industry benchmark priors
│   ├── country/macro assumptions
│   ├── WACC assumptions
│   ├── user overrides
│   └── assumption provenance
│
├── Valuation Engine Layer
│   ├── FCFF DCF
│   ├── FCFE / DDM
│   ├── WACC
│   ├── relative valuation
│   ├── reverse DCF
│   ├── sensitivity analysis
│   ├── scenario analysis
│   ├── macro sensitivity
│   └── real options advanced mode
│
├── Diagnostics Layer
│   ├── terminal value discipline
│   ├── growth vs reinvestment
│   ├── margin plausibility
│   ├── ROIC vs WACC
│   ├── industry mapping confidence
│   ├── stale/missing data flags
│   ├── source-confidence warnings
│   └── AI output review status
│
├── Thesis & Evidence Layer
│   ├── thesis notes
│   ├── assumption tracker
│   ├── evidence ledger
│   ├── event-to-thesis mapping
│   ├── decision records
│   └── valuation change log
│
├── Monitoring Layer
│   ├── new filing monitor
│   ├── RSS/news monitor
│   ├── event extraction
│   ├── alert generation
│   ├── daily brief
│   └── thesis-impact classifier
│
├── AI Analyst Layer
│   ├── narrative-to-numbers
│   ├── filing summarizer
│   ├── assumption challenger
│   ├── memo writer
│   ├── missing-data detector
│   └── source-grounded Q&A
│
└── Security & Governance Layer
    ├── authentication
    ├── authorization
    ├── secrets management
    ├── upload scanning
    ├── audit logging
    ├── data retention
    ├── provider key protection
    ├── AI privacy controls
    └── deployment hardening
```

## 4.2 Core backend rule

Keep each layer separate.

Bad:

```text
valuation route directly fetches filing, parses PDF, calls AI, calculates DCF, and writes memo
```

Good:

```text
valuation route
→ valuation workflow service
→ financial statement service
→ industry assumption service
→ deterministic valuation service
→ diagnostics service
→ memo service
```

---

# 5. Data Sources and APIs to Find / Configure

## 5.1 Required immediately

### SEC EDGAR API

Use for:

- US company submissions.
- 10-K/10-Q/8-K metadata.
- XBRL company facts.
- Financial concepts.
- Filing documents.

Implementation notes:

- No API key required.
- Must use a proper `SEC_USER_AGENT`.
- Respect polite access and rate limits.
- Store raw SEC response snapshots and filing accession numbers.

Required environment variable:

```text
SEC_USER_AGENT="Your Name your.email@example.com"
```

Build endpoints/services:

```text
SecCompanyResolver
SecFilingSearchService
SecFilingDownloadService
SecXbrlCompanyFactsService
SecStatementExtractionService
```

Reference to verify before implementation:

```text
https://www.sec.gov/search-filings/edgar-application-programming-interfaces
```

### FRED API

Use for:

- Macro series.
- US rates.
- Inflation.
- GDP.
- Unemployment.
- Selected macro context.

Required environment variable:

```text
FRED_API_KEY=...
```

Reference:

```text
https://fred.stlouisfed.org/docs/api/fred/
```

### OpenFIGI API

Use for:

- Mapping ticker/ISIN/local symbols to FIGI.
- Improving company identity resolution.
- Handling cross-listings and ticker ambiguity.

Required environment variable:

```text
OPENFIGI_API_KEY=optional_but_preferred
```

Reference:

```text
https://www.openfigi.com/api/documentation
```

### AI provider

Use for:

- Memo generation.
- Filing summarization.
- Narrative-to-numbers.
- Assumption explanation.
- Classification assistance.

Suggested environment variables:

```text
GEMINI_API_KEY=...
OPENAI_API_KEY=...
ANTHROPIC_API_KEY=...
```

Only one is required initially. The app should support provider abstraction.

## 5.2 Market prices and fundamentals providers

Choose one primary provider first. Do not integrate five at once.

### Option A: Financial Modeling Prep

Potential use:

- Financial statements.
- Ratios.
- Prices.
- Market caps.
- Historical data.
- Key metrics.

Pros:

- Broad feature set.
- Easier for fundamentals.
- Useful for startup build speed.

Risks:

- Data licensing.
- Pricing / tier limitations.
- Coverage quality varies by country.

Reference:

```text
https://site.financialmodelingprep.com/
```

### Option B: Tiingo

Potential use:

- US fundamentals.
- Historical prices.
- Clean EOD data.
- News.

Pros:

- Clean API reputation.
- Relatively simple pricing.
- Useful for US equities.

Risks:

- India coverage may not be enough.
- Paid tiers likely needed.

Reference:

```text
https://www.tiingo.com/documentation/
```

### Option C: Alpha Vantage

Potential use:

- Prices.
- Company overview.
- Income statement.
- Balance sheet.
- Cash flow.
- Technical indicators.

Pros:

- Easy to start.
- Has free tier.
- Quick prototype support.

Risks:

- Rate limits.
- Coverage and normalization limitations.
- May not be enough for serious fundamentals.

Reference:

```text
https://www.alphavantage.co/documentation/
```

### Option D: Finnhub

Potential use:

- Global financial statements.
- Filings.
- Transcripts.
- Prices.
- Company data.

Pros:

- Broad global data.
- Useful if you want transcripts/filings.

Risks:

- Price/tier constraints.
- Licensing restrictions.

Reference:

```text
https://finnhub.io/docs/api
```

### Option E: Polygon / Massive

Potential use:

- High-quality prices.
- Market data.
- Trades/quotes.

Pros:

- Strong market data.

Risks:

- Less central for valuation fundamentals.
- Real-time data is not necessary for the early valuation workflow.

Reference:

```text
https://massive.com/docs/rest/stocks/overview
```

## 5.3 India data sources

India is harder. Build manual-first, then automate.

### Official NSE Data & Analytics

Potential use:

- Corporate filings.
- Market data.
- Corporate data.
- End-of-day data.

Risks:

- Likely paid.
- May require formal subscription.
- Access terms matter.

Reference:

```text
https://www.nseindia.com/static/market-data/real-time-data-subscription
```

### BSE Corporate Announcements

Potential use:

- Corporate announcements.
- Results.
- Filings.
- Shareholding disclosures.
- Corporate actions.

Risks:

- Official website access may not be API-friendly.
- Scraping may violate terms.
- Need a proper vendor or manual upload workflow.

Reference:

```text
https://www.bseindia.com/corporates
```

### StockInsights / other India data vendors

Potential use:

- Tagged BSE/NSE announcements.
- AI-tagged corporate disclosures.
- Corporate event feeds.

Risks:

- Paid.
- Verify reliability, licensing, and redistribution rights.

Reference example:

```text
https://docs.stockinsights.ai/api-reference/india_endpoints/announcements-tagged-feed
```

### Screener.in

Potential use:

- Indian financial summaries.
- Annual reports.
- Ratios.
- Excel exports.

Risks:

- Do not scrape unless permitted.
- No assumption of official API.
- Safest use is user-downloaded export upload or official permitted workflow.

Reference:

```text
https://www.screener.in/
```

### Best India approach for now

```text
Phase 1: manual annual report / results upload
Phase 2: BSE/NSE link ingestion with user-provided URLs
Phase 3: official/vendor API integration
Phase 4: automated India filing monitor
```

## 5.4 Data-source selection matrix

| Need | Early solution | Later solution |
|---|---|---|
| US filings | SEC EDGAR | SEC + improved XBRL parser |
| US financial statements | SEC XBRL / provider | SEC + provider cross-check |
| India filings | Manual upload/link | NSE/BSE/vendor API |
| India financials | User upload / manual review | Vendor API + report extraction |
| Market prices | Manual + one provider | Provider health + freshness |
| Macro | FRED + manual India macro | RBI/FRED/world data provider |
| Industry benchmarks | Damodaran files | Scheduled versioned benchmark updates |
| Company identifiers | Manual + OpenFIGI | OpenFIGI + provider metadata |
| AI | Gemini/OpenAI abstraction | Multi-provider with privacy controls |

---

# 6. Data Model Additions and Changes

The current database is broad. The next step is not to add random tables. It is to add provenance, normalized statements, and workflow state.

## 6.1 Add `data_provenance` or equivalent embedded provenance

Create a universal provenance pattern that can be used for financial metrics, assumptions, AI outputs, and alerts.

```sql
CREATE TABLE data_provenance (
    id UUID PRIMARY KEY,
    entity_type TEXT NOT NULL,
    entity_id UUID NOT NULL,
    field_name TEXT,
    source_type TEXT NOT NULL,
    source_id UUID,
    source_name TEXT,
    source_document_id UUID,
    source_section_id UUID,
    source_url TEXT,
    source_period TEXT,
    extraction_method TEXT,
    confidence_label TEXT,
    review_status TEXT NOT NULL DEFAULT 'unreviewed',
    reviewed_by TEXT,
    reviewed_at TIMESTAMP,
    notes TEXT,
    created_at TIMESTAMP DEFAULT now()
);
```

Source types:

```text
manual
uploaded_document
sec_xbrl
provider_api
damodaran_benchmark
calculated
ai_suggested
csv_import
system_default
mock
unknown
```

Review statuses:

```text
unreviewed
needs_review
reviewed
rejected
overridden
stale
not_applicable
```

## 6.2 Normalized financial statements

Add canonical financial statement tables if not already sufficient.

```sql
CREATE TABLE financial_statement_snapshots (
    id UUID PRIMARY KEY,
    company_id UUID NOT NULL,
    fiscal_year INTEGER,
    fiscal_period TEXT,
    period_end_date DATE,
    statement_type TEXT NOT NULL,
    source_document_id UUID,
    currency TEXT,
    reporting_standard TEXT,
    consolidation_scope TEXT,
    extraction_status TEXT,
    review_status TEXT,
    created_at TIMESTAMP DEFAULT now()
);
```

```sql
CREATE TABLE financial_statement_line_items (
    id UUID PRIMARY KEY,
    snapshot_id UUID NOT NULL,
    canonical_metric_code TEXT NOT NULL,
    reported_label TEXT,
    value NUMERIC,
    unit TEXT,
    scale TEXT,
    source_page TEXT,
    source_section TEXT,
    confidence_label TEXT,
    review_status TEXT,
    user_override_value NUMERIC,
    created_at TIMESTAMP DEFAULT now()
);
```

Canonical metric examples:

```text
revenue
ebit
ebitda
net_income
tax_expense
interest_expense
depreciation_amortization
capex
change_non_cash_working_capital
cash_and_equivalents
short_term_debt
long_term_debt
lease_liabilities
book_equity
shares_outstanding_basic
shares_outstanding_diluted
dividends_paid
share_buybacks
stock_issuance
goodwill
minority_interest
preferred_stock
```

## 6.3 Company setup workflow state

```sql
CREATE TABLE company_setup_workflows (
    id UUID PRIMARY KEY,
    company_id UUID NOT NULL,
    current_step TEXT NOT NULL,
    identity_status TEXT,
    source_status TEXT,
    filing_status TEXT,
    financial_extraction_status TEXT,
    industry_mapping_status TEXT,
    valuation_readiness_status TEXT,
    security_review_status TEXT,
    created_at TIMESTAMP DEFAULT now(),
    updated_at TIMESTAMP DEFAULT now()
);
```

Steps:

```text
identity
source_setup
filing_fetch
financial_extraction
financial_review
industry_mapping
assumption_review
valuation_run
memo_review
thesis_save
monitoring
```

## 6.4 Assumption provenance

Extend valuation assumptions so every assumption stores:

```text
source_type
source_reference
benchmark_comparison
confidence
review_status
user_override
justification
```

If the current model does not support this cleanly, add a separate table:

```sql
CREATE TABLE valuation_assumption_provenance (
    id UUID PRIMARY KEY,
    valuation_model_id UUID NOT NULL,
    assumption_name TEXT NOT NULL,
    assumption_value NUMERIC,
    source_type TEXT NOT NULL,
    source_detail JSONB,
    benchmark_value NUMERIC,
    benchmark_source TEXT,
    confidence_label TEXT,
    review_status TEXT,
    user_justification TEXT,
    created_at TIMESTAMP DEFAULT now()
);
```

## 6.5 Provider health

```sql
CREATE TABLE provider_health_checks (
    id UUID PRIMARY KEY,
    provider_name TEXT NOT NULL,
    capability TEXT NOT NULL,
    market TEXT,
    status TEXT NOT NULL,
    last_success_at TIMESTAMP,
    last_failure_at TIMESTAMP,
    failure_reason TEXT,
    latency_ms INTEGER,
    rate_limit_remaining INTEGER,
    freshness_label TEXT,
    created_at TIMESTAMP DEFAULT now()
);
```

Statuses:

```text
configured
missing_key
working
rate_limited
failing
unsupported_market
disabled
unknown
```

---

# 7. Backend Services to Build or Update

## 7.1 CompanyIdentityService

Purpose:

Resolve and normalize company identity.

Responsibilities:

```text
- normalize ticker/local symbol
- identify market and exchange
- store currency and reporting currency
- fetch CIK for US companies
- attempt OpenFIGI mapping
- support manual India identity entry
- detect duplicates and cross-listings
- return confidence and alternatives
```

Inputs:

```text
company_name
ticker
exchange
country
market
isin
figi
manual override
```

Outputs:

```text
normalized company record
candidate matches
confidence label
missing identifiers
next recommended setup step
```

## 7.2 FilingDiscoveryService

Purpose:

Find relevant filings/disclosures for the company.

Responsibilities:

```text
- US: use SEC submissions and filings
- India: use manual upload/link first, later NSE/BSE/vendor provider
- classify filing type
- detect annual/quarterly/current-event filings
- store filing metadata
- avoid duplicates
- track provider health
```

Filing types:

```text
10-K
10-Q
8-K
annual_report
quarterly_results
investor_presentation
earnings_release
credit_rating
shareholding_pattern
corporate_announcement
transcript
other
```

## 7.3 FilingDownloadService

Responsibilities:

```text
- download filing document
- validate URL/domain
- enforce file size limits
- store raw document
- compute hash for deduplication
- record provenance
- quarantine unsafe files
```

Security requirement:

Never allow arbitrary internal URLs. Protect against SSRF.

## 7.4 FinancialStatementExtractionService

Purpose:

Extract raw financial statement line items.

Subservices:

```text
SecXbrlExtractor
PdfTableExtractor
HtmlTableExtractor
CsvStatementImporter
ManualStatementEntryService
```

Responsibilities:

```text
- extract income statement
- extract balance sheet
- extract cash flow statement
- detect reporting period
- detect currency and scale
- detect consolidated vs standalone
- map raw labels to canonical metric codes
- produce confidence score
- produce source references
```

## 7.5 FinancialStatementReviewService

Purpose:

Let user verify extracted data.

Responsibilities:

```text
- list extracted metrics
- show source evidence
- allow user override
- mark reviewed/rejected
- block full auto valuation if core metrics are unreviewed
```

Core metrics requiring review:

```text
revenue
ebit
net_income
tax_expense
depreciation_amortization
capex
cash
debt
shares_outstanding
working_capital components
```

## 7.6 MetricNormalizationService

Purpose:

Turn raw line items into valuation-ready metrics.

Responsibilities:

```text
- calculate EBIT if not explicitly available
- calculate EBITDA
- calculate NOPAT
- calculate effective tax rate
- calculate net debt
- calculate non-cash working capital
- calculate reinvestment
- calculate ROIC
- calculate ROE
- calculate sales-to-capital
- normalize for one-time items if marked
- handle consolidated vs standalone financials
```

Output:

```text
normalized metric package
metric provenance
confidence labels
warnings
```

## 7.7 IndustryMappingService

Update existing service to support:

```text
- suggested Damodaran industries
- confidence score
- rationale
- user confirmation
- diversified/segment-weighted mapping
- historical saved mapping
```

Industry mapping should never silently drive assumptions without user confirmation.

## 7.8 IndustryAssumptionService

Purpose:

Return auto-fill priors after country and industry are confirmed.

Autofill categories:

```text
revenue growth priors
operating margin priors
EBITDA margin
sales-to-capital
capex intensity
working capital ratios
ROE
ROC
fundamental EBIT growth
fundamental EPS growth
relative valuation multiples
payout behavior
macro sensitivity
volatility
```

Output every assumption with:

```text
value
source_file
source_industry
data_date
sample_size
confidence
warning
```

## 7.9 ValuationAutofillService

Purpose:

Merge company actuals, industry priors, country context, and user preferences into a first valuation draft.

Hierarchy:

```text
1. user-reviewed company actuals
2. company historical trends
3. company-specific provider data
4. industry benchmark priors
5. country/macro context
6. regression priors
7. system fallback
```

Never override user-reviewed values.

## 7.10 ValuationWorkflowService

Purpose:

Orchestrate the full workflow.

```text
create valuation draft
load normalized company metrics
load industry assumptions
load country context
generate assumptions
run DCF
run diagnostics
run relative valuation
run reverse DCF
store outputs
prepare memo inputs
```

## 7.11 TrustStateService

Purpose:

Return trust status for every page/module.

Trust states:

```text
real
partial
mock
manual
stale
missing
ai_unreviewed
unconfigured
error
```

## Phase 11: Stronger Financial Extraction (XBRL) [COMPLETED]
**Goal:** Transition from naive regex text extraction to reliable SEC XBRL extraction for US companies.

1. **SEC Provider & Parsing Layer:**
   - [x] Create `sec_xbrl_extractor.py` to hit the SEC EDGAR CompanyFacts API.
   - [x] Define a mapping dictionary from `us-gaap` taxonomy tags to internal `metric_code`s (e.g., `Revenues` -> `revenue`).
   - [x] Extract facts and populate `FinancialExtractionCandidate` records with `extraction_method="sec_xbrl_v1"` and `confidence_label="high"`.
   - [x] Persist deterministic unit selection plus concept, period, accession, filing, and frame evidence locators.
   - [x] Record success, duplicate, and failure outcomes through the shared processing-run lifecycle.

2. **API Layer:**
   - [x] Add endpoint `POST /api/companies/{company_id}/extract-xbrl` in `routers/fundamentals.py`.

3. **UI Integration:**
   - [x] Add "Extract via SEC XBRL" button to `frontend/app/companies/[id]/filings/page.tsx`.
   - [x] Link financial candidates to selected evidence context in their owning document.

## 7.12 ProviderHealthService

Purpose:

Monitor external/provider availability.

Responsibilities:

```text
- check API key presence
- perform lightweight health check
- track last success/failure
- rate limit status
- provider coverage by market
- freshness of last successful data
```

---

# 8. API Routes to Add or Update

## 8.1 Company setup

```http
POST /api/company-setup/start
GET /api/company-setup/{company_id}
PATCH /api/company-setup/{company_id}/step
POST /api/company-setup/{company_id}/resolve-identity
POST /api/company-setup/{company_id}/confirm-identity
```

## 8.2 Filing discovery and acquisition

```http
GET /api/companies/{company_id}/filings/discover
POST /api/companies/{company_id}/filings/fetch
POST /api/companies/{company_id}/filings/manual-link
POST /api/companies/{company_id}/filings/upload
GET /api/companies/{company_id}/filings
GET /api/filings/{filing_id}
```

## 8.3 Financial statement extraction and review

```http
POST /api/filings/{filing_id}/extract-financials
GET /api/companies/{company_id}/financial-statements/extracted
GET /api/companies/{company_id}/financial-statements/normalized
PATCH /api/financial-line-items/{line_item_id}/review
PATCH /api/financial-line-items/{line_item_id}/override
POST /api/companies/{company_id}/financial-statements/mark-reviewed
```

## 8.4 Industry mapping

```http
GET /api/companies/{company_id}/industry-mapping/suggestions
POST /api/companies/{company_id}/industry-mapping/confirm
PATCH /api/companies/{company_id}/industry-mapping/override
GET /api/valuation/industry-priors?country=India&industry=Transportation
```

## 8.5 Valuation autofill and run

```http
POST /api/companies/{company_id}/valuation/draft
GET /api/valuation/{valuation_id}/assumptions/provenance
PATCH /api/valuation/{valuation_id}/assumptions/{assumption_name}
POST /api/valuation/{valuation_id}/run
POST /api/valuation/{valuation_id}/diagnostics
POST /api/valuation/{valuation_id}/reverse-dcf
POST /api/valuation/{valuation_id}/relative-check
POST /api/valuation/{valuation_id}/memo/draft
PATCH /api/valuation/{valuation_id}/memo/review
```

## 8.6 Trust and provider health

```http
GET /api/trust/page-state?route=/valuation
GET /api/providers/health
POST /api/providers/{provider_name}/health-check
GET /api/data-freshness
```

## 8.7 Evidence and thesis impact

```http
POST /api/events/{event_id}/classify-thesis-impact
POST /api/events/{event_id}/link-valuation-assumption
GET /api/companies/{company_id}/evidence-trail
GET /api/valuation/{valuation_id}/change-log
POST /api/valuation/{valuation_id}/save-decision
```

---

# 9. UI / UX Master Plan

The existing UI base is useful. Build on it instead of replacing everything.

## 9.1 Global UI rules

Every page should have:

```text
page title
data state badge
last updated time
source/provider status
primary action
secondary actions
empty state
error state
review status where relevant
```

Global badges:

```text
Real Data
Partial Data
Manual Data
Benchmark Derived
AI Suggested
Mock Data
Stale Data
Provider Missing
Needs Review
Reviewed
```

## 9.2 Main navigation restructure

Recommended top-level navigation:

```text
Dashboard
Companies
Valuation
Research
Events & Alerts
Portfolio
Data Sources
Data Health
Settings
Admin
```

Sub-navigation under company:

```text
Overview
Filings
Financials
Valuation
Thesis
Evidence
Decisions
Alerts
```

## 9.3 Company setup wizard

### Screen 1: Choose company

Fields:

```text
Company name
Ticker/local symbol
Country
Exchange
Currency
Optional ISIN/FIGI/CIK
```

UI behavior:

```text
- show candidate matches
- show confidence score
- show missing identifiers
- ask user to confirm
```

### Screen 2: Source readiness

Show:

| Source | Status | Action |
|---|---|---|
| SEC EDGAR | Configured / Missing | Add SEC user agent |
| NSE/BSE | Manual only / Provider unavailable | Upload filing |
| Market data | Configured / Missing | Add API key |
| FRED | Configured / Missing | Add key |
| AI | Configured / Mock | Add provider key |
| Damodaran benchmarks | Imported / Missing | Import files |

### Screen 3: Filing discovery

For US:

```text
Recent 10-K
Recent 10-Q
Recent 8-K
Annual reports
Exhibits
```

For India:

```text
Upload annual report
Paste BSE/NSE filing URL
Upload quarterly results
Upload investor presentation
```

Show:

```text
filing type
period
source
download status
extraction status
review status
```

### Screen 4: Financial statement extraction

Show three tabs:

```text
Income Statement
Balance Sheet
Cash Flow
```

Each table:

| Metric | Extracted value | Source | Confidence | Review | Override |
|---|---:|---|---|---|---|

Actions:

```text
Accept all high-confidence rows
Review flagged rows
Override value
View source snippet/page
Mark statement reviewed
```

### Screen 5: Industry mapping

Show candidates:

| Candidate industry | Confidence | Why suggested | Benchmark coverage | Select |
|---|---:|---|---|---|

For Adani Ports, possible candidates might include:

```text
Transportation
Shipping
Infrastructure-like category
Engineering/Construction
```

User must confirm.

### Screen 6: Assumption draft

Display:

| Assumption | Suggested value | Source | Benchmark | Status | User override |
|---|---:|---|---:|---|---|

Sections:

```text
Revenue growth
Margins
Reinvestment
Working capital
ROIC/ROC
Tax
WACC
Terminal value
Relative valuation multiples
Macro sensitivity
Payout/FCFE
```

### Screen 7: Run valuation

Cards:

```text
Base DCF value
Valuation range
Current price
Upside/downside
DCF implied multiples
Reverse DCF
Sensitivity table
Scenario summary
Diagnostics
Warnings
```

### Screen 8: Memo and decision

Tabs:

```text
Valuation memo
Assumption audit
Evidence trail
What has to be true
What would change my mind
Decision record
```

Memo status:

```text
AI draft
Needs review
Reviewed
Approved
Rejected
```

## 9.4 Valuation dashboard UI

Recommended layout:

```text
Top: company, price, currency, data freshness, review status

Left column:
- workflow checklist
- missing inputs
- provider health
- source coverage

Center:
- valuation result card
- forecast chart
- sensitivity matrix
- scenario range
- reverse DCF

Right:
- diagnostics
- assumptions requiring review
- industry benchmark comparison
- AI memo status
```

## 9.5 Evidence trail UI

For each alert/event:

```text
Alert
→ Event
→ Evidence snippet
→ Raw document
→ Source
→ Company
→ Thesis assumption affected
→ Valuation assumption affected
```

Show:

```text
supports thesis
weakens thesis
neutral/noise
requires review
```

## 9.6 Data Health page

This should become important.

Show:

| Provider | Capability | Market | Status | Last success | Freshness | Action |
|---|---|---|---|---|---|---|

Providers:

```text
SEC
RSS
FRED
Market data provider
Damodaran benchmark importer
AI provider
India filings
Manual uploads
```

---

# 10. Step-by-Step Implementation Roadmap

## Phase 0: Documentation and workspace alignment

Goal:

Make sure docs match current code and planned build.

Tasks:

```text
- update README
- update architecture docs
- update database docs
- update API docs
- update security docs
- add this plan under docs/valuation-agent or docs/roadmaps
- add current capability limitations link
- mark stale docs
```

Acceptance criteria:

```text
Future Codex sessions know exactly what exists, what is planned, and what not to build yet.
```

Codex prompt:

```text
Audit current docs against the repo and this master plan. Update docs to reflect the valuation-first workflow and automated research-to-valuation roadmap. Do not implement code yet.
```

## Phase 1: Trust-state audit across frontend

Goal:

Make the app honest before making it more powerful.

Tasks:

```text
- inspect every frontend route
- classify route as real / partial / mock / stale / missing / AI / manual
- add badges where missing
- ensure market regime page is clearly mock or hidden
- add page-level data-state metadata
```

Acceptance criteria:

```text
No page can be mistaken for a complete live product if it is partial or mock.
```

## Phase 2: Provider health and configuration

Goal:

Users know what sources are configured and working.

Tasks:

```text
- create provider health service
- add health endpoints
- check SEC user agent
- check FRED key
- check market data key
- check AI provider key
- check Damodaran benchmark import status
- show provider health in UI
```

Acceptance criteria:

```text
Data Health page shows configured/missing/failing/stale status for each provider.
```

## Phase 3: Company setup wizard

Goal:

Turn company creation into a guided workflow.

Tasks:

```text
- add company setup workflow model
- create wizard UI
- add identity resolution service
- add OpenFIGI optional mapping
- add CIK lookup for US
- support manual India identity
- store setup state
```

Acceptance criteria:

```text
User can create Adani Ports or Apple through a guided setup flow and see source readiness.
```

## Phase 4: Filing discovery and acquisition

Goal:

Fetch or collect source documents.

Tasks:

```text
- enhance SEC filing discovery
- add recent filings UI
- support manual India filing upload/link
- validate source domains
- store filing metadata
- deduplicate by accession/hash
- add extraction status tracking
```

Acceptance criteria:

```text
US company can fetch recent 10-K/10-Q. India company can upload annual report or paste filing URL.
```

## Phase 5: Financial statement extraction

Goal:

Extract financial statements from filings.

Tasks:

```text
- SEC XBRL companyfacts parser
- filing-specific XBRL statement parser
- PDF table extraction for uploaded annual reports
- raw line-item storage
- canonical metric mapping
- source references
- confidence labels
```

Acceptance criteria:

```text
For a supported US company, the app extracts revenue, EBIT, net income, cash, debt, capex, and shares from filings. For India, uploaded annual report extraction creates candidate line items for review.
```

## Phase 6: Financial statement review screen

Goal:

Prevent bad extraction from contaminating valuation.

Tasks:

```text
- build review tables
- show source references
- allow user override
- mark metric reviewed/rejected
- block auto valuation if core metrics are unreviewed
- show extraction confidence
```

Acceptance criteria:

```text
User can review/override every key financial metric before valuation.
```

## Phase 7: Metric normalization engine

Goal:

Create valuation-ready metrics.

Tasks:

```text
- map reviewed line items to normalized metrics
- compute EBITDA, NOPAT, effective tax rate, net debt, working capital, reinvestment, ROIC, ROE
- store normalized metric snapshot
- attach provenance
- produce warnings for missing/odd metrics
```

Acceptance criteria:

```text
Company has a normalized metric package that can feed valuation.
```

## Phase 8: Industry mapping confirmation

Goal:

Use Damodaran benchmarks safely.

Tasks:

```text
- improve industry suggestions
- show candidates and rationale
- require user confirmation
- support segment-weighted mapping later
- store confirmed mapping
```

Acceptance criteria:

```text
User confirms industry before benchmark priors are applied.
```

## Phase 9: Assumption autofill engine

Goal:

Auto-fill draft valuation assumptions.

Tasks:

```text
- combine company actuals
- combine company history
- combine Damodaran industry priors
- combine country context
- combine user preferences
- label every assumption source
- create draft assumptions
```

Acceptance criteria:

```text
After financials + industry mapping, app creates a full DCF assumption draft with source labels.
```

## Phase 10: Guided FCFF valuation workflow

Goal:

Make valuation usable end-to-end.

Tasks:

```text
- create guided valuation page
- run FCFF DCF
- show assumptions, outputs, diagnostics
- show sensitivity/scenarios
- show terminal value discipline
- show assumptions requiring review
```

Acceptance criteria:

```text
User can run a complete valuation from reviewed statements and confirmed assumptions.
```

## Phase 11: Relative valuation and reverse DCF integration [COMPLETED]

Goal:

Add market-pricing context.

Tasks:

```text
- show current company multiples
- show industry benchmark multiples
- show DCF-implied multiples
- run reverse DCF from current price
- show what has to be true
```

Acceptance criteria:

```text
Valuation page reconciles DCF value with market price and industry pricing.
```

## Phase 12: AI memo with review [COMPLETED]

Goal:

Use AI for explanation, not calculation.

Tasks:

```text
- draft memo from deterministic output
- include assumptions and warnings
- include source limitations
- prevent buy/sell language
- require user review
- store reviewed memo
```

Acceptance criteria:

```text
AI memo clearly states facts, assumptions, valuation result, risks, and limitations without investment advice.
```

## Phase 13: Evidence trail and thesis impact

Goal:

Connect intelligence to valuation.

Tasks:

```text
- link events to thesis assumptions
- link events to valuation assumptions
- classify impact
- show evidence chain
- allow user to update assumptions from new evidence
```

Acceptance criteria:

```text
New filing/news can be traced to what it changes in the valuation or thesis.
```

## Phase 14: Portfolio valuation view [COMPLETED]

Goal:

Make portfolio useful beyond tracking.

Tasks:

```text
- show intrinsic value vs current price by holding
- show confidence/review status
- show stale/missing data
- show thesis status
- show top risks and alerts by position
```

Acceptance criteria:

```text
Portfolio page shows valuation gap and research confidence, not just holdings.
```

## Phase 15: India automation upgrade

Goal:

Move beyond manual India support.

Tasks:

```text
- evaluate NSE Data & Analytics subscription
- evaluate BSE corporate announcement data options
- evaluate StockInsights/other vendor APIs
- build official/provider-backed filing discovery if feasible
- add India market price provider
- add India fundamentals provider or user-export ingestion
```

Acceptance criteria:

```text
India company workflow can fetch or ingest filings with less manual effort while staying license-compliant.
```

## Phase 16: Security hardening for private beta

Goal:

Prepare for controlled external users.

Tasks:

```text
- add auth
- add authorization
- add user isolation
- encrypt secrets
- lock down file uploads
- add audit logs
- add rate limiting
- add secure CORS
- add backup/restore
- add AI privacy controls
```

Acceptance criteria:

```text
A small private beta can run without exposing user data or API keys.
```

---

# 11. Cybersecurity Master Plan

Security should be designed as if the app may eventually hold:

```text
private portfolio data
investment theses
uploaded filings
API keys
AI prompts and outputs
user notes
potential broker tokens later
```

## 11.1 Current rule

Until security is upgraded:

```text
localhost only
single user only
no public deployment
no broker sync
no sensitive credentials beyond local env keys
```

## 11.2 Authentication and authorization

Before public/private beta:

```text
- add login
- add session management
- add per-user database ownership
- add role-based access control
- protect every API route
- protect admin routes separately
```

Roles:

```text
owner
analyst
viewer
admin
```

Minimum rule:

```text
No user can access another user's companies, documents, portfolio, valuations, AI outputs, or API keys.
```

## 11.3 Secrets management

Never store provider keys in plaintext in the database.

For local:

```text
.env
.gitignored
.env.example only contains placeholders
```

For cloud:

```text
managed secret store
encrypted environment variables
key rotation
no secrets in logs
```

## 11.4 File upload security

Critical because users will upload PDFs, Excel files, CSVs, annual reports, and maybe HTML.

Requirements:

```text
- file size limits
- allowed MIME types
- extension validation
- content sniffing
- virus/malware scanning
- reject executable files
- strip macros where possible
- do not execute uploaded spreadsheets
- store uploads outside public web root
- randomize filenames
- hash files
- quarantine before parsing
```

Allowed file types initially:

```text
pdf
csv
xlsx
xls only if conversion is sandboxed
txt
html only from trusted filing providers
```

Do not allow:

```text
exe
js
sh
bat
docm
xlsm unless explicitly sanitized
zip unless sandboxed
```

## 11.5 URL ingestion security

When user pastes filing URL:

```text
- block localhost/internal IPs
- block private network ranges
- block file:// URLs
- allowlist official domains where possible
- enforce HTTPS
- limit redirects
- set timeout
- limit response size
- record final URL
```

This protects against SSRF.

## 11.6 API security

Requirements:

```text
- strict Pydantic validation
- no raw exception leakage
- rate limiting
- request size limits
- CORS allowlist
- CSRF protection where applicable
- security headers
- OpenAPI schema review
- input sanitization
- SQL injection prevention through ORM/parameterized queries
```

## 11.7 AI privacy controls

Before sending anything to AI provider:

```text
- show user what data will be sent
- redact API keys/secrets
- optionally redact portfolio size
- do not send unrelated documents
- store prompt version and input hash
- mark AI output as AI-generated
- require review before use in memo/decision
```

## 11.8 Audit logging

Log:

```text
login/logout
file upload
document ingestion
financial metric override
valuation assumption override
AI memo generation
memo approval
decision save
API key update
admin action
provider failures
```

Audit log fields:

```text
user_id
action
entity_type
entity_id
timestamp
ip_address
user_agent
before_value_hash
after_value_hash
```

## 11.9 Dependency and infrastructure security

Add:

```text
dependency scanning
secret scanning
static analysis
container scanning
database backup
migration rollback plan
error monitoring
structured logs
```

Suggested tools/categories:

```text
pip-audit / safety
npm audit
GitHub secret scanning
Semgrep or CodeQL
Docker image scanning
Sentry or similar error tracking
```

## 11.10 Broker sync security

Do not build now.

Only build after:

```text
official broker OAuth
encrypted token storage
token revocation
read-only permissions first
no trade execution initially
separate threat model
legal review
audit logs
user consent screens
```

---

# 12. Existing Features to Fix / Update

## 12.1 Market regime page

Current problem:

```text
mock UI can look real
```

Fix:

```text
- hide it from main nav or add explicit prototype label
- build backend endpoint before real use
- require data sources and formulas
```

## 12.2 AI memo wording

Current problem:

```text
AI can sound like recommendation
```

Fix:

```text
- use "decision readiness" language
- avoid buy/sell recommendation wording
- include limitations
- require user review
```

## 12.3 Admin Damodaran compare

Current problem:

```text
mock comparison endpoint can mislead
```

Fix:

```text
- implement real dataset diff
- or label as mock/not implemented
```

## 12.4 CSV export response shape

Current problem:

```text
file downloads may be wrapped awkwardly in ApiResponse
```

Fix:

```text
- test CSV download in browser
- return raw file response when appropriate
```

## 12.5 India provider stubs

Current problem:

```text
India support can be overstated
```

Fix:

```text
- label manual-only
- build manual upload workflow
- add provider evaluation doc
```

## 12.6 Financial statement ingestion

Current problem:

```text
not fully audited
```

Fix:

```text
- extraction confidence
- review screen
- normalized metrics
- provenance
```

## 12.7 Route parity

Current problem:

```text
frontend breadth exceeds verified backend workflows
```

Fix:

```text
- route-by-route audit
- data state badges
- remove misleading CTAs
```

---

# 13. Feature Backlog by Priority

## Priority 1: Must build next

```text
trust badges everywhere
provider health dashboard
company setup wizard
filing acquisition workflow
financial extraction review screen
normalized metrics package
industry mapping confirmation
valuation assumption provenance
guided FCFF valuation workflow
AI memo review flow
evidence trail UX
```

## Priority 2: Serious upgrades

```text
reverse DCF "what has to be true" UI
relative valuation integration
portfolio valuation gap
event-to-thesis impact classifier
data freshness engine
India manual filing workflow
source-backed research memo
browser-level tests
```

## Priority 3: Advanced features

```text
full India provider integration
automated financial statement extraction across markets
market regime backend
macro scenario engine with real data
source-grounded Q&A over filings
falsification/contradiction engine
segment-level valuation
holding-company valuation
bank/financial services valuation
```

## Priority 4: Later

```text
public SaaS deployment
team collaboration
broker sync
real-time data
advanced social sentiment
option-flow/gamma/positioning
mobile app
white-label/API product
```

---

# 14. What You Need to Add / Decide

## 14.1 API keys/accounts

Minimum:

```text
SEC_USER_AGENT
FRED_API_KEY
one market/fundamentals provider key
one AI provider key
OpenFIGI key optional
```

Market data provider decision:

```text
Pick exactly one primary provider first.
Do not integrate multiple at once.
```

Suggested first choice:

```text
If valuation-first and global-ish fundamentals matter: evaluate FMP or Finnhub.
If US fundamentals quality matters more: evaluate Tiingo.
If quick prototype/free matters: Alpha Vantage.
If price data matters more than fundamentals: Polygon/Massive.
```

## 14.2 India data decision

Choose one near-term India path:

```text
A. Manual upload-first
B. User-provided Screener/BSE/NSE exports
C. Paid vendor API
D. Official NSE/BSE data subscription
```

Recommendation:

```text
Start with A + B. Evaluate C/D later.
```

## 14.3 Product wedge decision

Choose one:

```text
valuation-first
portfolio-first
filings intelligence-first
market regime-first
```

Recommendation:

```text
valuation-first
```

## 14.4 Deployment decision

For now:

```text
local-only
```

Before monetization:

```text
private beta with auth and user isolation
```

## 14.5 Legal / compliance posture

You need:

```text
disclaimer language
no investment advice positioning
AI output limitations
data licensing review
terms of use if public
privacy policy if external users
```

---

# 15. Acceptance Criteria for the Full Automated Workflow

The following should work for a US company first.

## 15.1 US company test

Example company:

```text
Apple / Microsoft / Tesla
```

Workflow should:

```text
1. Create company
2. Resolve CIK
3. Fetch latest 10-K and 10-Q
4. Extract financial statement values
5. Show extraction review table
6. User marks core metrics reviewed
7. Suggest industry mapping
8. User confirms industry
9. Auto-fill DCF assumptions
10. User edits assumptions
11. Run DCF
12. Show sensitivity and diagnostics
13. Run reverse DCF
14. Show relative valuation
15. Generate AI memo
16. User reviews memo
17. Save thesis/decision
```

Pass condition:

```text
The user can trace every key number back to a source, formula, benchmark, or manual override.
```

## 15.2 India company test

Example company:

```text
Adani Ports
```

Workflow should:

```text
1. Create company with NSE/BSE metadata manually
2. Upload annual report
3. Extract candidate financial statement values
4. User reviews/overrides values
5. Confirm Damodaran industry
6. Auto-fill assumptions from India benchmarks
7. Run DCF and relative valuation
8. Generate memo
9. Save thesis
```

Pass condition:

```text
India workflow is honest about what is manual and what is automated.
```

---

# 16. Codex Execution Prompts

## 16.1 Start prompt

```text
Read this master plan and the existing capability documentation. Do not implement yet. Audit the repository and return a placement plan for the automated research-to-valuation workflow.

Return:
- current relevant files
- existing services to reuse
- missing services
- database migrations needed
- frontend routes/components to update
- risks
- proposed implementation phases

Do not code yet.
```

## 16.2 Phase 1 prompt

```text
Implement Phase 1: route trust audit and visible data-state badges.

Requirements:
- inspect every frontend route
- add/standardize badges for real, partial, mock, stale, manual, benchmark-derived, AI-suggested, missing, and not configured states
- do not change backend business logic
- do not add new features
- ensure market regime is clearly mock/prototype or hidden
- update docs

Return changed files and tests run.
```

## 16.3 Provider health prompt

```text
Implement ProviderHealthService and Data Health UI.

Requirements:
- detect configured/missing API keys for SEC user agent, FRED, market data provider, AI provider, OpenFIGI, and Damodaran imports
- store or compute last success/failure from processing runs where available
- expose GET /api/providers/health
- update data-health frontend page
- show market/capability support
- add tests
```

## 16.4 Company setup prompt

```text
Implement the guided company setup workflow.

Requirements:
- create company setup workflow state
- build frontend wizard
- support US CIK lookup
- support manual India setup
- show provider/source readiness
- do not build full filing extraction yet
- add tests and docs
```

## 16.5 Financial extraction prompt

```text
Implement financial statement extraction and review foundation.

Requirements:
- create normalized statement snapshot and line item models if missing
- extract core US XBRL values from SEC where available
- support manual/PDF-upload candidate extraction for India as partial
- build review table UI
- every metric must have source, confidence, and review status
- block valuation autofill until core metrics are reviewed
```

## 16.6 Valuation autofill prompt

```text
Implement valuation assumption autofill.

Requirements:
- use reviewed company financials
- use confirmed industry mapping
- use Damodaran benchmark priors
- use country context where available
- label every assumption by source
- allow user override
- do not treat industry priors as company facts
- run deterministic FCFF DCF only after user review
```

---

# 17. What Not to Build Yet

Do not build:

```text
broker sync
public deployment
multi-user team system
real-time trading data
trading recommendations
automatic buy/sell signals
advanced options/flow dashboard
fully automated social scraping
market regime claims without backend data
broker credential storage
payment/billing before security
```

---

# 18. Final Recommended Build Order

```text
0. Update docs and workspace alignment
1. Route trust audit and data-state badges
2. Provider health dashboard
3. Company setup wizard
4. Filing discovery/acquisition
5. Financial statement extraction
6. Financial review screen
7. Metric normalization
8. Industry mapping confirmation
9. Assumption autofill
10. Guided FCFF valuation workflow
11. Relative valuation + reverse DCF integration
12. AI memo review
13. Evidence trail / thesis impact
14. Portfolio valuation gap
15. India data/provider upgrade
16. Security hardening for private beta
17. Private beta
18. Monetization experiments
```

---

# 19. Final Product Shape

The strongest version of this app is:

> **A source-backed valuation workspace that turns filings, financial statements, industry benchmarks, and user judgment into auditable investment memos and thesis monitoring.**

The app should not compete with Bloomberg on real-time data. It should compete with:

```text
messy spreadsheets
unstructured ChatGPT chats
scattered filing notes
manual valuation work
unsupported investment theses
```

The winning workflow is:

```text
financials
+ filings
+ benchmark priors
+ deterministic valuation
+ AI explanation
+ source-backed thesis monitoring
```

Keep the build narrow until this workflow is excellent.
