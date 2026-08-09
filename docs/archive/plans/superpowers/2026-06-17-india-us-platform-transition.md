# India/US Platform Transition Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Convert the app from a US-first research tool with India valuation files into a first-class India/US market intelligence platform with explicit market identity, source provenance, country-aware valuation, market data, filings, macro context, and UI flows.

**Architecture:** Add a market identity layer first, then route company lookup, filings, market data, macro, and valuation through country-aware provider interfaces. Keep all outputs source-labeled and do not synthesize unavailable India data as real. Use manual/provider-backed fallbacks when official APIs are absent or unstable.

**Tech Stack:** FastAPI, SQLAlchemy, Alembic, PostgreSQL, Pydantic, pytest, Next.js App Router, TypeScript, existing `ApiResponse` envelope.

---

## Current Reality

The backend already has partial country/currency fields on `companies`, holdings, market prices, DCF assumptions, and portfolio analytics. It is not enough.

Current gaps:
- `ticker` is globally unique, which breaks dual-market symbols.
- `companies/lookup` is SEC-only.
- SEC filings are modeled as if every company can have a CIK.
- market data provider interface only accepts a raw ticker string.
- India source ingestion is mostly Damodaran XLS files, not exchange/company filings.
- valuation priors default heavily toward India files in some places and US SEC data in others.
- frontend pages do not force users to choose market/country/currency consistently.
- macro Batch 05 uses SIC codes and India-focused Damodaran files but does not expose an India/US selector.
- no explicit source capability matrix exists, so the UI cannot honestly say which features are available for India vs US.

Target outcome:
- Company identity is `(market, exchange, ticker)` rather than ticker alone.
- US path supports SEC CIK/submissions/companyfacts.
- India path supports NSE/BSE symbols, exchange announcements, manual financials, and India benchmark files first.
- Both markets support manual portfolio, manual prices, valuation workflows, macro sensitivity, evidence labeling, and data health.
- Unsupported features show `Not available yet` or `Provider not configured`, never fake data.

---

## External Source Notes

Use only compliant, source-backed integrations.

US:
- SEC EDGAR APIs provide submissions history and XBRL company facts without API keys, updated throughout the day.
- SEC fair access currently states 10 requests/second maximum. Preserve user-agent validation and rate limiting.

India:
- NSE has public corporate filings, financial results, shareholding, corporate actions, and historical reports pages.
- BSE has public corporate announcements pages.
- Treat NSE/BSE website endpoints as unstable unless an official documented API or licensed data feed is used.
- Do not scrape aggressively. Add provider health, rate limits, and terms-review notes.
- First production-safe implementation should support manual uploads/links and official exchange page references before relying on undocumented JSON endpoints.

---

## New Domain Concepts

### Market Codes

Use these enum-like strings everywhere:

```text
US
IN
```

### Exchange Codes

Initial allowed values:

```text
US: NASDAQ, NYSE, AMEX, OTC
IN: NSE, BSE
```

### Filing Systems

```text
US_SEC_EDGAR
IN_NSE_CORPORATE_FILINGS
IN_BSE_CORPORATE_ANNOUNCEMENTS
MANUAL_UPLOAD
RSS
```

### Currencies

```text
US -> USD
IN -> INR
```

Allow non-default currency only when explicitly selected and warn if valuation currency does not match cash-flow currency.

---

## Data Model Changes

### Task 1: Market Identity Columns - Completed 2026-06-17

**Files:**
- Modify: `backend/app/models/company.py`
- Modify: `backend/app/api/schemas.py`
- Add migration: `backend/alembic/versions/<next>_add_market_identity.py`
- Test: `backend/tests/test_company_market_identity.py`

Add to `companies`:

```python
market: Mapped[str] = mapped_column(String(10), default="US", index=True)
primary_exchange: Mapped[str | None] = mapped_column(String(20), index=True)
local_symbol: Mapped[str | None] = mapped_column(String(40), index=True)
isin: Mapped[str | None] = mapped_column(String(20), index=True)
figi: Mapped[str | None] = mapped_column(String(32), index=True)
regulatory_id: Mapped[str | None] = mapped_column(String(40), index=True)
regulatory_id_type: Mapped[str | None] = mapped_column(String(40))
```

Rules:
- `ticker` remains for display/backward compatibility.
- `local_symbol` stores exchange-native symbol, e.g. `RELIANCE` or `AAPL`.
- `regulatory_id_type = "CIK"` for US SEC companies.
- India may use `ISIN` where available. Do not invent CIN unless a real provider supplies it.
- Add uniqueness on `(market, primary_exchange, local_symbol)`.
- Remove or relax global unique constraint on `ticker`. If dropping the old constraint risks data, stop and inspect existing DB state first.

API schema changes:
- `CompanyCreate` accepts `market`, `primary_exchange`, `local_symbol`, `isin`, `regulatory_id`, `regulatory_id_type`.
- `CompanyRead` returns all of the above.
- Default create behavior:
  - if `market` omitted, use `US` for backward compatibility.
  - if `local_symbol` omitted, use uppercase `ticker`.
  - if `currency` omitted, infer `USD` for US and `INR` for India.

Tests:
- creating `US/NASDAQ/ABC` and `IN/NSE/ABC` should both succeed.
- duplicate `IN/NSE/ABC` should fail with 409.
- omitted market should create US company.

Implemented:
- Added `market`, `primary_exchange`, `local_symbol`, `isin`, `figi`, `regulatory_id`, and `regulatory_id_type` to `companies`.
- Relaxed global ticker uniqueness. The API now rejects duplicates by `(market, primary_exchange, local_symbol)` instead.
- Existing and legacy create payloads default to `US`, `USD`, `United States`, and uppercase `ticker` as `local_symbol`.
- India create payloads default to `INR`, `India`, uppercase `primary_exchange`, and uppercase `local_symbol`.
- Added migration `418h1d347c24_add_company_market_identity.py` and verified the local database is at that head.
- Added focused tests in `backend/tests/test_company_market_identity.py`.

---

### Task 2: Source Capability Matrix - Completed 2026-06-17

**Files:**
- Create: `backend/app/models/market_source.py`
- Add migration: `backend/alembic/versions/<next>_add_market_source_capabilities.py`
- Create: `backend/app/services/source_capability.py`
- Create: `backend/app/api/routers/source_capabilities.py`
- Modify: `backend/app/api/routes.py`
- Test: `backend/tests/test_source_capabilities.py`

New table:

```text
market_source_capabilities
- id
- market
- source_type
- provider_name
- capability
- status: available | manual_only | not_configured | not_supported
- requires_api_key
- freshness_expected_seconds
- notes
- updated_at
```

Initial seed data:

```text
US SEC filings: available if SEC_USER_AGENT valid
US SEC fundamentals: available if SEC_USER_AGENT valid
US market prices: provider-backed or manual_only
IN exchange announcements: manual_only initially
IN financial statements: manual_only initially
IN market prices: provider-backed if Alpha Vantage/FMP supports selected symbol, else manual_only
IN Damodaran benchmarks: available
IN macro sensitivity: available from imported Damodaran files
```

New endpoint:

```http
GET /api/source-capabilities?market=IN
```

Response:

```json
{
  "data": [
    {
      "market": "IN",
      "source_type": "filings",
      "provider_name": "NSE/BSE",
      "capability": "corporate_announcements",
      "status": "manual_only",
      "requires_api_key": false,
      "notes": "Official pages exist, automated provider not enabled."
    }
  ],
  "meta": {
    "status": "success",
    "source": "internal",
    "is_stale": false,
    "is_mock": false
  },
  "errors": []
}
```

Frontend will use this to decide whether to show buttons, disabled states, or `Provider not configured`.

Implemented:
- Added `market_source_capabilities` with `(market, source_type, provider_name, capability)` uniqueness.
- Added seeded US/India capability rows for SEC filings/fundamentals, market prices, India NSE/BSE/manual workflows, Damodaran benchmarks, and macro sensitivity.
- Added `GET /api/source-capabilities?market=IN|US`.
- The service lazily seeds defaults for fresh local/test databases.
- Market price capabilities return `not_configured` until `ALPHA_VANTAGE_API_KEY` or `FMP_API_KEY` is configured.
- Added focused tests in `backend/tests/test_source_capabilities.py`.
- Added migration `419i1d347c25_add_market_source_capabilities.py` and verified the local database is at that head.

---

## Provider Layer

### Task 3: Company Lookup Provider Interface - Completed 2026-06-17

**Files:**
- Create: `backend/app/providers/company_lookup/base.py`
- Create: `backend/app/providers/company_lookup/sec.py`
- Create: `backend/app/providers/company_lookup/manual.py`
- Create: `backend/app/providers/company_lookup/india_exchange_stub.py`
- Create: `backend/app/services/company_lookup.py`
- Modify: `backend/app/api/routers/companies.py`
- Test: `backend/tests/test_company_lookup_providers.py`

Provider contract:

```python
class CompanyLookupResult(BaseModel):
    market: str
    exchange: str | None
    ticker: str
    local_symbol: str
    name: str
    currency: str
    country: str
    regulatory_id: str | None = None
    regulatory_id_type: str | None = None
    isin: str | None = None
    source: str
    warnings: list[str] = []
```

New endpoint:

```http
GET /api/companies/lookup?market=US&ticker=AAPL
GET /api/companies/lookup?market=IN&exchange=NSE&ticker=RELIANCE
```

US behavior:
- route to SEC provider.
- return CIK as `regulatory_id`, `regulatory_id_type="CIK"`.

India behavior:
- phase 1 returns `404` unless a local company exists or manual lookup table exists.
- do not fake name/ISIN.
- response message should say `India company lookup provider not implemented; add company manually or configure provider`.

Later India provider options:
- official exchange/company master downloads where permitted.
- licensed data provider.
- user-imported security master CSV.

Do not rely on undocumented NSE/BSE JSON without a terms review.

Implemented:
- Added `backend/app/providers/company_lookup/` with a shared result contract, SEC provider, local/manual provider, and India exchange stub.
- `GET /companies/lookup` now accepts `market`, `exchange`, and `ticker`.
- US lookup routes to SEC and returns CIK as `regulatory_id`, `regulatory_id_type="CIK"`, and compatibility `cik`.
- India lookup first returns an existing local company when present.
- India lookup without a local match returns `404` with `India company lookup provider not implemented; add company manually or configure provider`.
- Unsupported markets return `400`.
- Added focused tests in `backend/tests/test_company_lookup_providers.py`.

---

### Task 4: Market Data Provider Contract Upgrade - Completed 2026-06-17

**Files:**
- Modify: `backend/app/services/market_data/base.py`
- Modify: `backend/app/services/market_data/alpha_vantage.py`
- Modify: `backend/app/services/market_data/fmp.py`
- Modify: `backend/app/services/market_data/factory.py`
- Modify: `backend/app/api/routers/market.py`
- Test: `backend/tests/test_market_data_market_context.py`

Replace ticker-only calls with:

```python
class MarketDataRequest(BaseModel):
    market: str
    exchange: str | None
    ticker: str
    currency: str | None
```

Provider methods:

```python
async def get_quote(self, request: MarketDataRequest) -> MarketQuote | None
async def get_historical_prices(self, request: MarketDataRequest, days: int = 365) -> list[MarketPricePoint]
```

New endpoints:

```http
GET  /api/market/quote?market=US&exchange=NASDAQ&ticker=AAPL
GET  /api/market/quote?market=IN&exchange=NSE&ticker=RELIANCE
POST /api/market/ingest
```

Keep old endpoints:

```http
GET /api/market/quote/{ticker}
POST /api/market/ingest/{ticker}
```

But mark old routes as compatibility wrappers that resolve company by ticker. If ambiguous, return 409:

```json
{
  "detail": "Ticker is ambiguous across markets. Use market and exchange."
}
```

Rules:
- returned quote must include `currency`, `market`, `exchange`, `provider_name`, `as_of`.
- if provider returns USD for an Indian security, do not silently store as INR.
- manual prices remain valid for both countries.

Implemented:
- Added `MarketDataRequest` with `market`, `exchange`, `ticker`, and `currency`.
- Updated Alpha Vantage and FMP provider interfaces to accept `MarketDataRequest`.
- Added `GET /api/market/quote?market=US|IN&exchange=...&ticker=...`.
- Added `POST /api/market/ingest` with market-aware payload.
- Kept ticker-only compatibility routes, but they now reject ambiguous tickers with `409`.
- Market ingestion now passes full market context to providers and rejects currency mismatches instead of silently storing the wrong currency.
- Added focused tests in `backend/tests/test_market_data_market_context.py`.

---

### Task 5: Filing Provider Split - Completed 2026-06-17

**Files:**
- Create: `backend/app/providers/filings/base.py`
- Move/adapt: `backend/app/services/sec_ingestion.py` into `backend/app/providers/filings/sec_edgar.py` or wrap it
- Create: `backend/app/providers/filings/india_manual.py`
- Modify: `backend/app/api/routers/ingestion.py`
- Modify: `backend/app/api/routers/companies.py`
- Test: `backend/tests/test_filing_provider_routing.py`

Provider contract:

```python
class FilingProvider(Protocol):
    provider_name: str
    market: str
    def preview_filings(company: Company, form_type: str | None, limit: int) -> list[FilingMetadata]
    def ingest_filings(company: Company, payload: FilingIngestionRequest) -> ProcessingRunResult
```

New endpoints:

```http
GET  /api/companies/{company_id}/filings/preview?source=auto&limit=20
POST /api/companies/{company_id}/filings/ingest
POST /api/companies/{company_id}/filings/manual
```

US:
- `source=auto` routes to SEC.
- requires CIK.

India:
- `source=auto` returns `not_configured` until exchange provider is approved.
- manual filing upload/link is supported immediately.
- accepted document types: `annual_report`, `quarterly_result`, `investor_presentation`, `exchange_announcement`, `shareholding_pattern`, `corporate_action`.

Do not keep adding SEC-specific endpoints for India. Keep old SEC preview as compatibility route.

Implemented:
- Added `backend/app/providers/filings/` with a shared provider contract, SEC EDGAR wrapper, and India manual/not-configured provider.
- Added `GET /companies/{company_id}/filings/preview?source=auto`.
- US `source=auto` routes to SEC EDGAR and requires CIK.
- India `source=auto` returns `409` with `India automated filing provider not configured; use manual filing upload/link`.
- Added `POST /companies/{company_id}/filings/manual` for manual filing links/text.
- Manual filing creates a traceable `RawDocument` with `source_kind="manual_filing"`, `filing_system="MANUAL_UPLOAD"`, market/exchange/symbol metadata, and a content hash.
- Accepted manual filing types are `annual_report`, `quarterly_result`, `investor_presentation`, `exchange_announcement`, `shareholding_pattern`, and `corporate_action`.
- Kept the old `/companies/{company_id}/sec-filings/preview` compatibility route.
- Added focused tests in `backend/tests/test_filing_provider_routing.py`.

---

## Valuation and Macro

### Task 6: Country-Aware Valuation Context - Completed 2026-06-17

**Files:**
- Modify: `backend/app/models/dcf.py`
- Modify: `backend/app/api/schemas.py`
- Modify: `backend/app/api/routers/valuations.py`
- Modify: `backend/app/services/industry_assumption.py`
- Test: `backend/tests/test_valuation_country_context.py`

Add to valuation models or assumption sets if not already present:

```text
market
country
currency
cash_flow_currency
discount_rate_currency
benchmark_country
benchmark_source
```

New endpoint:

```http
GET /api/valuation/context/company/{company_id}
```

Response:

```json
{
  "company_id": 1,
  "market": "IN",
  "country": "India",
  "default_currency": "INR",
  "available_benchmark_countries": ["India", "United States"],
  "recommended_benchmark_country": "India",
  "warnings": [
    "Cash flows and discount rate must be in the same currency."
  ]
}
```

Rules:
- Indian company defaults to INR valuation.
- US company defaults to USD valuation.
- If user chooses USD valuation for India company, require either USD cash flows or explicit FX conversion assumptions.
- Do not use US risk-free rate with INR cash flows without a warning.

Implemented:
- Added `GET /api/valuation/context/company/{company_id}`.
- Indian companies return INR cash-flow and discount-rate currency defaults, India benchmark recommendation, and currency/risk-free-rate warnings.
- US companies return USD defaults and United States benchmark recommendation.
- Added `ValuationCompanyContextRead` schema and `valuation_context` service.
- This is a read/context endpoint only. It does not yet alter DCF assumptions, run FX conversion, or enforce valuation currency constraints during model creation.
- Added focused tests in `backend/tests/test_valuation_country_context.py`.

---

### Task 7: Country-Aware Macro Batch 05 - Completed 2026-06-18

**Files:**
- Modify: `backend/app/models/macro_sensitivity.py`
- Modify: `backend/app/services/bottom_up_macro_sensitivity.py`
- Modify: `backend/app/services/macro_scenario_translation.py`
- Modify: `backend/app/api/routers/macro_valuation.py`
- Test: `backend/tests/test_macro_country_context.py`

Add country/market to `sector_macro_sensitivity_benchmarks`:

```text
market
country
classification_system: SIC | DAMODARAN_INDUSTRY | GICS | NIC
currency_context
currency_variable_description
```

Current data migration:
- Existing `macrodur.xls` rows become:
  - `market = "IN"`
  - `country = "India"`
  - `classification_system = "SIC"` if currently stored by SIC
  - `currency_variable_description = "Source file currency movement convention not fully verified."`

Endpoint changes:

```http
GET  /api/valuation/macro/sector?market=IN&country=India&sic=5311
POST /api/valuation/macro/scenario
POST /api/valuation/macro/bottom-up
```

Request additions:

```json
{
  "market": "IN",
  "country": "India",
  "currencyVariableDirection": "stronger_usd"
}
```

Rules:
- Preserve source coefficient signs.
- Add interpretation fields separately:
  - `raw_duration`
  - `duration_magnitude`
  - `duration_interpretation`
- Negative duration is not “fixed”; it is flagged:

```text
Negative raw duration means the sector coefficient is positive to rate changes or source convention differs. Treat as source coefficient, not normal bond-like duration.
```

This closes the current known limitation without corrupting source data.

Implemented:
- Added market, country, classification system, and currency context fields to `sector_macro_sensitivity_benchmarks`.
- Added migration `420j1d347c26_add_macro_country_context.py`; existing rows are backfilled as `IN`, `India`, `SIC`, and `INR`.
- `GET /api/valuation/macro/sector` now accepts `market` and `country` filters with India defaults for compatibility.
- `POST /api/valuation/macro/scenario` now accepts `market`, `country`, and `currencyVariableDirection`.
- `POST /api/valuation/macro/bottom-up` now accepts `market` and `country` and returns segment-level market/classification context.
- Source duration signs are preserved. Responses add `raw_duration`, `duration_magnitude`, and `duration_interpretation`; negative raw duration adds the explicit warning text above.
- Added focused coverage in `backend/tests/test_macro_country_context.py`.

---

### Task 8: Risk-Free Rate and Macro Provider Context - Completed 2026-06-18

**Files:**
- Create: `backend/app/models/country_market_data.py`
- Create: `backend/app/services/country_market_context.py`
- Create: `backend/app/api/routers/country_market.py`
- Modify: `backend/app/api/routes.py`
- Test: `backend/tests/test_country_market_context.py`

New table:

```text
country_market_context
- id
- market
- country
- currency
- risk_free_rate
- risk_free_rate_source
- equity_risk_premium
- country_risk_premium
- inflation_rate
- fx_rate_to_usd
- as_of_date
- is_manual
- notes
```

Endpoints:

```http
GET  /api/market-context?market=IN
POST /api/market-context/manual
GET  /api/valuation/risk-free-rate?currency=INR
```

Phase 1:
- manual entry only.
- default examples may be absent, not hardcoded.

Later provider candidates:
- FRED for US rates and macro.
- RBI official data/manual CSV import for India rates/macro after provider review.
- Damodaran country ERP files if already imported.

Implemented:
- Added `country_market_context` with one manual context row per market.
- Added migration `421k1d347c27_add_country_market_context.py`; no default rates are seeded.
- Added `GET /api/market-context?market=US|IN`. Missing manual rows return a standard error envelope instead of a fabricated default.
- Added `POST /api/market-context/manual` for manual country, currency, risk-free-rate, ERP, inflation, FX, and notes.
- Added `GET /api/valuation/risk-free-rate?currency=USD|INR`. It only returns a rate when a stored row has both `risk_free_rate` and `risk_free_rate_source`.
- Added focused coverage in `backend/tests/test_country_market_context.py`.
- Verified local Alembic head is `421k1d347c27`.
- Verified focused backend transition suite passes: `42 passed`.

---

## Frontend Plan

### Task 9: Market Selector and Company Form - Completed 2026-06-18

**Files:**
- Modify: `frontend/app/companies/page.tsx`
- Modify: `frontend/components/form-fields.tsx`
- Modify: `frontend/lib/form-payloads.ts`
- Modify: `frontend/lib/api.ts`
- Test: `frontend/lib/form-payloads.test.ts`

UI behavior:
- Company create/edit form has Market selector: `United States`, `India`.
- Exchange options change by market.
- Currency defaults:
  - US -> USD
  - India -> INR
- CIK field only shown for US.
- ISIN field shown for India.
- SEC lookup button only enabled for US.
- India lookup panel says:

```text
India lookup provider not configured. Add the company manually or import a security master.
```

No fake lookup result.

---

Implemented:
- Company create/edit forms capture market, primary exchange, local symbol, ISIN, regulatory ID, and regulatory ID type.
- Market selection defaults currency/country/exchange fields for US and India.
- Company lookup passes market and exchange context.
- Indian company detail pages avoid SEC automation and show the India filing provider limitation honestly.
- Added frontend payload/API coverage for market-aware company form and lookup behavior.

---

### Task 10: Data Page Source Capability Matrix - Completed 2026-06-18

**Files:**
- Modify: `frontend/app/data/page.tsx`
- Create: `frontend/components/source-capability-matrix.tsx`
- Modify: `frontend/lib/api.ts`

Show two columns:
- United States
- India

Rows:
- Company lookup
- Filings/announcements
- Fundamentals
- Market prices
- Macro/rates
- Valuation benchmarks
- Portfolio/manual entries

States:
- Available
- Manual only
- Provider not configured
- Not supported yet

This prevents the app from pretending India has SEC-style automation.

Implemented:
- Added `frontend/components/source-capability-matrix.tsx`.
- Added frontend `SourceCapability` types.
- `frontend/app/data/page.tsx` now fetches US and India capability rows from `/api/source-capabilities` and renders a two-country capability matrix.
- Matrix includes company lookup, filings/announcements, fundamentals, market prices, macro/rates, valuation benchmarks, and portfolio/manual entries.
- Verified `/data` renders the matrix from the running app.

---

### Task 11: Batch 05 Macro UI - Completed 2026-06-18

**Files:**
- Modify: `frontend/app/macro/page.tsx`
- Create: `frontend/components/macro/macro-workbench.tsx`
- Create: `frontend/components/macro/macro-sensitivity-table.tsx`
- Create: `frontend/components/macro/macro-scenario-form.tsx`
- Create: `frontend/components/macro/macro-bottom-up-form.tsx`
- Create: `frontend/components/macro/macro-top-down-form.tsx`
- Modify: `frontend/lib/api.ts`

UI tabs:

```text
Series | Sector Lookup | Scenario | Top-Down | Bottom-Up
```

Country selector:
- India
- United States

Initial behavior:
- India uses existing Batch 05 Damodaran-backed endpoints.
- US sector lookup shows `Not available yet` unless US benchmark rows exist.

Required labels:
- Fact
- Calculation
- Source Summary
- User Assumption

Required warnings:
- coefficient signs preserved from source
- no automatic DCF assumption mutation
- currency direction must be defined
- missing SIC coverage reduces confidence

Implemented:
- Added planned macro component split:
  - `frontend/components/macro/macro-workbench.tsx`
  - `frontend/components/macro/macro-sensitivity-table.tsx`
  - `frontend/components/macro/macro-scenario-form.tsx`
  - `frontend/components/macro/macro-bottom-up-form.tsx`
  - `frontend/components/macro/macro-top-down-form.tsx`
- Added `frontend/lib/macro-workbench.ts` and coverage for tab parsing.
- `frontend/app/macro/page.tsx` now uses `Series`, `Sector Lookup`, `Scenario`, `Top-Down`, and `Bottom-Up` tabs.
- The page keeps the required claim labels and warnings visible: Fact, Calculation, Source Summary, User Assumption; source signs preserved; no automatic DCF mutation; currency direction required; missing SIC reduces confidence.
- Build and typecheck pass.

---

### Task 12: Valuation Page Market Context - Completed 2026-06-18

**Files:**
- Modify: `frontend/app/valuation/page.tsx`
- Modify: company valuation detail pages under `frontend/app/companies/[id]/valuation/`
- Create: `frontend/components/valuation/market-context-panel.tsx`
- Create: `frontend/components/valuation/currency-consistency-warning.tsx`

UI behavior:
- Show company market/currency at top of valuation workflow.
- Show benchmark country selector.
- If company is India but valuation currency is USD, show warning.
- If risk-free currency differs from cash-flow currency, block save or require explicit override note.
- Surface available macro sensitivity endpoint for company market.

Implemented:
- Added `frontend/components/valuation/market-context-panel.tsx`.
- Added `frontend/components/valuation/currency-consistency-warning.tsx`.
- Added `frontend/lib/valuation-context.ts` and focused coverage for India/USD warnings and risk-free/cash-flow mismatch blocking.
- Company valuation pages fetch `GET /api/valuation/context/company/{company_id}` and display market/country/default currency/recommended benchmark context.
- The advanced valuation workspace shows cash-flow currency and discount-rate/risk-free currency fields.
- Save is blocked when risk-free/discount-rate currency differs from cash-flow currency without an override note. With an override note, the save is allowed but still warns.
- The valuation hub shows market and currency columns before entering company models.
- Added API coverage to ensure `fetchValuationContext` calls `/api/valuation/context/company/{company_id}`.
- Build, typecheck, and frontend tests pass.

---

## API Inventory to Add or Change

### Company Identity

```http
GET  /api/companies?market=IN&exchange=NSE
POST /api/companies
PATCH /api/companies/{company_id}
GET  /api/companies/lookup?market=US&ticker=AAPL
GET  /api/companies/lookup?market=IN&exchange=NSE&ticker=RELIANCE
```

### Source Capabilities

```http
GET /api/source-capabilities
GET /api/source-capabilities?market=IN
```

### Filings

```http
GET  /api/companies/{company_id}/filings/preview?source=auto
POST /api/companies/{company_id}/filings/ingest
POST /api/companies/{company_id}/filings/manual
```

### Market Data

```http
GET  /api/market/quote?market=IN&exchange=NSE&ticker=RELIANCE
GET  /api/market/history?market=US&exchange=NASDAQ&ticker=AAPL&range=1y
POST /api/market/ingest
```

### Market Context

```http
GET  /api/market-context?market=IN
POST /api/market-context/manual
GET  /api/valuation/risk-free-rate?currency=INR
```

### Valuation Context

```http
GET /api/valuation/context/company/{company_id}
GET /api/valuation/assumption-priors?country=India&industry=Auto%20Parts
GET /api/valuation/benchmarks/fundamentals?country=India&industry=Auto%20Parts
```

### Macro

```http
GET  /api/valuation/macro/data?market=IN&frequency=annual
GET  /api/valuation/macro/sector?market=IN&country=India&sic=5311
POST /api/valuation/macro/scenario
POST /api/valuation/macro/top-down
POST /api/valuation/macro/bottom-up
```

---

## Execution Order

1. Market identity schema and tests.
2. Company lookup routing by market.
3. Source capability matrix.
4. Filing provider split and manual India filing support.
5. Market data provider contract upgrade.
6. Valuation market/currency context.
7. Macro country context and raw-sign interpretation.
8. Country market context manual API.
9. Frontend company market selector.
10. Frontend source capability matrix.
11. Frontend Batch 05 macro workbench.
12. Frontend valuation market context panels.
13. Docs reconciliation and runbook update.

Do not start with UI. The UI depends on capability and market identity APIs to avoid fake India support.

---

## Stop Conditions

Stop and ask before proceeding if:
- dropping the old unique ticker constraint risks existing data.
- NSE/BSE automated fetching requires undocumented endpoints.
- India filings integration requires scraping pages without terms review.
- a provider returns prices in a currency different from company currency.
- valuation code would discount INR cash flows using USD risk-free rates.
- any UI panel would need mock India data to look complete.

---

## Verification Plan

Backend:

```bash
docker compose exec backend pytest backend/tests/test_company_market_identity.py -q
docker compose exec backend pytest backend/tests/test_company_lookup_providers.py -q
docker compose exec backend pytest backend/tests/test_source_capabilities.py -q
docker compose exec backend pytest backend/tests/test_market_data_market_context.py -q
docker compose exec backend pytest backend/tests/test_filing_provider_routing.py -q
docker compose exec backend pytest backend/tests/test_valuation_country_context.py -q
docker compose exec backend pytest backend/tests/test_macro_country_context.py -q
docker compose exec backend pytest backend/tests/test_country_market_context.py -q
```

Frontend:

```bash
docker compose exec frontend npm test
docker compose exec frontend npm run typecheck
```

Manual:

```bash
curl "http://localhost:8000/api/source-capabilities?market=IN"
curl "http://localhost:8000/api/companies/lookup?market=US&ticker=AAPL"
curl "http://localhost:8000/api/companies/lookup?market=IN&exchange=NSE&ticker=RELIANCE"
curl "http://localhost:8000/api/valuation/context/company/1"
```

Expected:
- US lookup works when SEC is configured.
- India lookup returns honest provider-not-implemented/manual path until an approved provider is added.
- India company can be created manually with INR currency.
- India valuation context warns on currency mismatch.
- Macro UI shows real India Batch 05 data and clear limitations.

---

## Definition of Done

The India/US transition is done when:
- the app can hold US and India companies with overlapping local symbols.
- every company has explicit market, exchange, country, and currency.
- US SEC-specific features are not shown as available for India.
- India manual filing and manual market data paths work.
- valuation context blocks or warns on currency mismatch.
- Batch 05 macro UI supports India with real imported data and shows US as unavailable unless US benchmark data exists.
- data health shows source capability by market.
- no mocked India intelligence appears as real.
