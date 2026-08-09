# Provider Data Execution Plan

**Status:** Active. Batch 1 completed; Batch 2 US side passed and India side is staged for review.

**Reviewed:** 2026-08-01

**Input reviewed:** `market_valuation_agent_free_data_api_implementation_blueprint.md`

## 1. Executive Decision

Use the blueprint's source hierarchy, cache-first routing, quota controls,
Tiingo recommendation, and Upstox recommendation. Do not implement its full
schema or ten phases literally because this repository already contains much
of that foundation.

The next sequence is:

```text
provider routing honesty
-> real-source US/India certification
-> minimal request gateway and quota ledger
-> Tiingo adjusted US end-of-day prices
-> Upstox India identity and prices
-> Upstox fundamentals as review candidates
-> official India document reconciliation
-> risk-free-rate and assumption-source hardening
-> optional fallback providers
```

This plan deliberately does not begin with six providers, a new valuation
engine, a broker sync, a scheduler, or an AI provider.

## 2. What From The Blueprint We Will Use

| Blueprint proposal | Decision | Repository-specific treatment |
|---|---|---|
| Database/cache first | Adopt | Existing normalized records, raw documents, processing runs, and prices remain the first read path |
| Official facts outrank aggregators | Adopt | SEC and reviewed India exchange/company filings remain canonical; Upstox creates candidates until reconciled |
| Preserve raw payloads and provenance | Adopt | Extend existing `Source`, `RawDocument`, `DocumentAsset`, and `ProcessingRun`; do not create duplicate raw-source systems |
| Separate facts, calculations, assumptions, and AI interpretations | Adopt | Keep existing claim types, AI contract, reviewed assumptions, and evidence links |
| Source trust hierarchy | Adopt | Store trust/use policy in provider capability metadata and show conflicts rather than silently picking values |
| Tiingo for US adjusted EOD | Adopt for personal/internal MVP | Add one provider adapter after routing and market-price provenance are repaired |
| Upstox for India | Adopt for operational data | Use read-only Analytics Token only; no order/trading operations and no account portfolio import in this phase |
| Alpha Vantage protected reserve | Adopt later | Add only after the request/quota ledger exists; it is not the primary route |
| OpenFIGI/GLEIF identity enrichment | Defer one phase | Existing company identity fields are sufficient for the first certification pair; add OpenFIGI before broader company onboarding |
| Full quota broker | Reduce to an MVP control plane | Implement request ledger, configured limits, reserves, redaction, and dry-run explanations before concurrency/scheduling complexity |
| New legal entity/security/listing schema | Defer | Existing `Company` already stores market, exchange, symbol, CIK, ISIN, FIGI, regulatory ID, currency, and security type |
| New source-document/request tables | Do not duplicate | Extend existing source/raw-document/processing-run boundaries where fields are missing |
| New financial-facts schema | Do not duplicate | Extend existing candidates, normalized snapshots/metrics, and source-fact revisions after real-source evidence exposes specific gaps |
| Rebuild SEC ingestion | Reject | SEC submissions, filing text, company lookup, XBRL candidates, processing runs, and evidence already exist |
| Rebuild valuation engine | Reject | FCFF/FCFE, WACC, reverse DCF, scenarios, sensitivity, diagnostics, and assumption drafts already exist |
| Add many fallback providers immediately | Reject | Finish and certify one path per market before adding fallbacks |
| Add news before source data is reliable | Reject | RSS/SEC remain; GDELT and provider news wait until price/fundamental paths pass |

## 3. Current Repository Reality

Already present and reusable:

- SEC ticker/CIK lookup, submissions, filing metadata/text, and company-facts
  extraction
- market-aware company setup and manual India filing acquisition
- reviewed PDF and Screener upload with source custody, hashes, and locators
- financial extraction candidates and review/reject/override/promotion
- normalized financial snapshots/metrics and first point-in-time revisions
- `Source`, `RawDocument`, `DocumentAsset`, and `ProcessingRun`
- `MarketSourceCapability` and provider-health endpoints/UI
- company market, exchange, symbol, CIK, ISIN, FIGI, regulatory identity,
  currency, and security-type fields
- Alpha Vantage interface and partial adapter
- FRED provider
- imported/versioned Damodaran datasets and industry mappings
- FCFF, FCFE, WACC, reverse DCF, scenarios, sensitivity, diagnostics, and
  durable valuation setup drafts
- fail-closed real-source certification harness
- normalized market quote/history contract, configured provider routing,
  stable provider errors, and stored quote/price provenance
- explicit `yfinance_personal` adapter with personal/unofficial warnings

Missing or defective:

- external HTTP behavior is split across `httpx`, `urllib`, provider classes,
  and services without one request/quota/redaction boundary
- provider capability metadata does not record reviewed license/use scope,
  quota state, terms-review date, or active endpoint entitlement
- OpenFIGI is represented in provider health but no real adapter exists
- FMP is a placeholder
- one real-source US history is eligible; India remains review-gated
- India company lookup, prices, fundamentals, and automated filing support are
  incomplete or manual-only

## 4. Execution Batches

Each batch is intended to be reviewable independently. Do not start a later
provider before the current batch passes its acceptance gate.

### Batch 1: Market Routing And Provenance Repair

**Status:** Completed 2026-08-01 at Alembic head `i5i5i5i5i5i5`.

**Purpose:** Remove the hidden yfinance bypass and make market-price source
identity honest before adding a vendor.

Engineering work:

1. [x] Route `POST /market-prices/fetch-latest` through the same configured
   `MarketDataProvider` boundary as `/api/market/ingest`.
2. [x] Remove direct database writes from the yfinance provider.
3. [x] Make yfinance an explicit `yfinance_personal` option or disable it until
   explicitly selected.
4. [x] Add one normalized quote/history result contract with provider, market,
   exchange, symbol, currency, source time, observed time, delay/venue label,
   adjustment state, and warnings.
5. [x] Persist provider/source metadata with market-price records without breaking
   existing manual prices.
6. [x] Return stable missing-key, unsupported-symbol, empty-response, rate-limit,
   timeout, and provider-failure codes.
7. [x] Replace the empty yfinance test with mocked contract tests.
8. [x] Reconcile the duplicate market-price route surfaces and document which one
   is canonical.

Acceptance gate:

- no production route imports or invokes yfinance directly
- manual and provider prices are visibly distinguishable
- a provider failure never becomes a zero price, stale unlabeled price, or
  another provider's silent success
- focused market API/provider tests pass

Credentials required: none.

Validation evidence:

- 20 focused market/provider tests passed as part of the final suite
- all 367 backend tests passed; four warnings are third-party `openpyxl`
  Python 3.14 deprecations
- all 73 frontend unit tests, TypeScript, and the production build passed
- all six isolated product-integrity browser tests passed, including rendered
  manual-price provenance
- migration upgraded and reports one head at `i5i5i5i5i5i5`
- live `GET /api/health` returned `200 OK`
- Python compilation and the repository secret scan passed; Ruff is not
  installed in the backend image

### Batch 2: Real-Source Certification Pair

**Purpose:** Close the current highest trust gap before broad provider
expansion.

Recommended pair:

- US: Apple (`AAPL`), because SEC data and filing structures are stable
- India: Adani Ports (`INE742F01042`), because project valuation material and a
  likely official financial PDF already exist locally

Engineering work:

1. [x] Ingest AAPL SEC Company Facts through the existing route.
2. [x] Review and promote the authorized AAPL FY2022-FY2025 core window.
3. [x] Verify exact evidence, period, unit, currency, normalization, and zero reconciliation mismatches for AAPL.
4. [x] Store the supplied APSEZ FY2024-25 and FY2023-24 reports with official NSE URLs and verified local hashes.
5. [x] Store the Q1 FY27 investor presentation as supplementary evidence and link the revised consolidated NSE iXBRL.
6. [x] Stage 48 APSEZ FY2023-FY2025 consolidated candidates without promotion.
7. [x] Reconstruct and review APSEZ operating EBIT and preserve the approved industry mapping as an editable revenue-weighted mix.
8. [x] Promote the approved APSEZ set into normalized history and reconcile.
9. [x] Run the two-market manifest-backed certification report.
10. [x] Record parser/normalization gaps without weakening the certification gate.

Acceptance gate:

- at least one real US and one real India history is certified
- synthetic/mock fixtures remain labeled and separate
- every certified core metric has exact evidence, period, unit, currency,
  review state, and source identity
- official documents outrank vendor/research-report values
- the FY2023-24 qualified audit opinion and related limitation remain visible
  in evidence and valuation-readiness output

Credentials required: existing SEC configuration only. It is already present
in the local `.env`; no value should be exposed in documentation or chat.

### Batch 3: Minimal Provider Request Control Plane

**Purpose:** Add only the control needed to safely operate free-tier providers.

Engineering work:

1. Add a provider policy record or extend capability metadata with:
   official/unofficial status, personal/internal/commercial use scope,
   redistribution rule, attribution requirement, terms URL, terms-review date,
   credential requirement, enabled state, and freshness expectation.
2. Add a provider request ledger with request ID, provider, endpoint family,
   company/security identity, priority, timestamps, status, quota cost, bytes,
   cache hit, retry count, and safe failure class.
3. Centralize timeout, headers, secret/query redaction, response-size limits,
   stable error classification, and bounded retry.
4. Add configured per-window limits and reserves. Do not scrape pricing pages
   automatically.
5. Add P0 active-user, P1 portfolio, P2 watchlist, and P3 backfill priorities.
6. Add a dry-run route explanation that states cache/provider choice and why no
   call was made.
7. Extend Provider Health with policy, quota, last success/failure, and
   entitlement-test state.

Acceptance gate:

- keys and signed URLs cannot appear in logs or API responses
- a disabled/dry-run provider makes no network request
- quota/reserve behavior is deterministic and tested
- retries honor `Retry-After` and do not retry invalid credentials
- processing runs and request IDs remain correlated

Credentials required: none for unit/fixture tests.

### Batch 4: Tiingo US Adjusted EOD

**Purpose:** Establish one bounded US historical-price path for valuation and
portfolio work.

Engineering work:

1. Implement Tiingo metadata and adjusted EOD history behind the repaired
   market-data contract.
2. Preserve raw and adjusted close, currency, date, source, corporate-action
   fields, and observed time needed by the current product.
3. Cache symbol metadata and historical ranges.
4. Add split/dividend fixtures and response-drift tests.
5. Add provider-health entitlement and quota visibility.
6. Run an opt-in AAPL live smoke test without making live calls part of the
   deterministic suite.

Acceptance gate:

- AAPL adjusted history and a known split/dividend fixture reconcile
- repeated warm reads make zero external calls
- source, adjustment state, terms/use scope, timestamp, and stale state are
  visible
- Tiingo cannot silently fall back to yfinance or Alpha Vantage

Credential required: `TIINGO_API_KEY`.

### Batch 5: Upstox India Identity And Prices

**Purpose:** Add a read-only operational India path without introducing broker
trading or undocumented exchange scraping.

Upstox's official documentation confirms that the Analytics Token is read-only,
valid for one year, and supports market data, historical data, fundamentals,
news, and related GET APIs. Only one Analytics Token can be active per account.

Engineering work:

1. Add Upstox instrument/ISIN resolution into the existing company setup
   provider boundary.
2. Store instrument key, ISIN, exchange, local symbol, and source confidence.
3. Add current quote and non-deprecated historical-candle support.
4. Keep NSE and BSE listing identity explicit; default the first Adani workflow
   to its reviewed primary listing.
5. Add expiry metadata and a provider-health warning before token expiry.
6. Add invalid-ISIN, missing-instrument, token-expired, `429`, currency, and
   schema-drift tests.
7. Do not call account holdings, orders, funds, or trade APIs.

Acceptance gate:

- three reviewed India securities resolve by ISIN and exchange without ticker
  ambiguity
- price results identify exchange, currency, timestamp, delay/price type, and
  provider
- token failure is visible and does not fall back silently
- no trading permission or operation exists

Credential required: `UPSTOX_ANALYTICS_TOKEN`.

Official references:

- [Upstox Analytics Token](https://upstox.com/developer/api-documentation/analytics-token/)
- [Upstox rate limits](https://upstox.com/developer/api-documentation/rate-limiting/)

### Batch 6: Upstox Fundamentals As Review Candidates

**Purpose:** Accelerate India normalization while retaining official documents
as the source of truth.

Engineering work:

1. Add profile, income statement, balance sheet, cash flow, shareholding,
   ratios, corporate actions, and competitors as separate capabilities.
2. Preserve Upstox's INR crore source unit before any conversion.
3. Preserve consolidated and standalone records separately; default to
   consolidated for the approved India workflow while keeping the scope
   explicit on every candidate, snapshot, and valuation draft.
4. Store the raw payload with provider/source metadata allowed by the current
   terms.
5. Convert provider lines into financial extraction candidates, not directly
   into trusted normalized metrics.
6. Reuse current review, override, evidence, promotion, and reconciliation
   workflows.
7. Add entitlement smoke tests for every enabled endpoint family.

Acceptance gate:

- Adani Ports plus two other India companies produce review candidates
- no Upstox fact overwrites a reviewed official-file fact
- statement scope and INR crore conversion are explicit and tested
- material provider/official conflicts enter a review queue

Official reference:

- [Upstox Company Fundamentals API](https://upstox.com/developer/api-documentation/announcements/company-fundamentals-api/)

### Batch 7: India Official-Document Reconciliation

**Purpose:** Make Upstox useful without lowering the product's evidence
standard.

Engineering work:

1. Expand the existing manual India filing path for reviewed BSE/NSE/company
   XBRL, Excel, HTML, or PDF files only as concrete real documents require.
2. Map missing Indian statement labels discovered in the certification set.
3. Compare latest material periods against Upstox candidates.
4. Prefer the official value by default and preserve both records.
5. Create durable issues for unit, scope, period, restatement, or material-value
   conflicts.
6. Add corporate-action review for split, bonus, rights, merger, and demerger.

Acceptance gate:

- official annual and quarterly documents validate or dispute the operational
  provider record
- no undocumented exchange JSON endpoint is used
- every discrepancy is reviewable and reproducible

Credentials required: none beyond the existing document workflow.

### Approved India Consolidation And Ownership Policy

The first Adani workflow uses consolidated INR statements and an NSE primary
listing. Apply the following Damodaran-style treatment:

1. Value 100% of operations that are line-by-line consolidated, including
   majority-controlled subsidiaries. Do not multiply consolidated revenue,
   EBIT, reinvestment, or FCFF by the parent's ownership percentage.
2. Deduct non-controlling/minority interests once in the enterprise-to-equity
   bridge. Prefer an estimated market value; use book value only as a labeled
   estimate with a review warning.
3. Do not include equity-accounted associates or joint ventures in operating
   FCFF unless their statements are actually consolidated. Value the owned
   stake separately and add it as a cross-holding/non-operating asset.
4. Add other passive or strategic minority holdings at the value of the owned
   stake, not at 100% of the investee value.
5. Reconcile parent-attributable profit and diluted shares, but do not use
   parent-attributable net income to replace consolidated operating FCFF.
6. Prevent double counting: an entity cannot contribute both consolidated
   operating cash flow and a separate cross-holding value.
7. Use revenue-weighted operating-country ERP when reviewed geographic revenue
   is available. Until then, use the approved India ERP as a visibly
   provisional fallback rather than inferring risk from the NSE listing alone.

### Batch 8: Rates And Assumption Sources

**Purpose:** Complete the minimum USD/INR valuation context after facts and
prices are trustworthy.

Engineering work:

1. Keep the existing FRED provider and add current-series fixtures/health.
2. Add direct US Treasury yield retrieval only if it improves the current
   risk-free-rate workflow over FRED.
3. Add reviewed RBI/CCIL file ingestion for INR risk-free rates; do not assume
   a stable RBI API.
4. Import the approved April/January 2025 Damodaran source pair as a locked,
   versioned assumption set. Preserve workbook hash, sheet, cell, value,
   source vintage, and transformation formula for every assumption.
5. Keep newer Damodaran vintages inactive until reviewed.
6. Verify USD and INR rate/currency consistency in valuation drafts and runs.

Acceptance gate:

- one USD and one INR valuation use dated, source-backed, currency-consistent
  risk-free rates
- approved ERP low/base/high values point to exact source cells or pages
- importing a new dataset cannot alter an old valuation run

Credentials required: FRED is already configured. No additional key is needed
for the first RBI manual-file path.

### Batch 9: Optional Fallbacks And Intelligence

Only after Batches 1 through 8 pass, evaluate individually:

- OpenFIGI without a key, then optional key for batch throughput
- Alpha Vantage with a protected five-call reserve
- Twelve Data for labeled US/FX fallback
- GDELT as discovery, not fact authority
- Groq or NVIDIA NIM for AI evaluation after source-backed data certification

Do not add FMP, Finnhub, Alpaca, DhanHQ, Marketaux, EIA, IMF, ECB, or GLEIF
without a concrete missing capability that the current selected providers do
not satisfy.

## 5. What The User Must Do

### 5.1 Decisions recorded on 2026-08-01

No additional product decision blocks Batches 1 or 2.

| Decision | Approved value |
|---|---|
| Product scope | Personal/internal and local-only for now |
| Certification pair | AAPL and Adani Ports (`INE742F01042`) |
| India statement scope | Consolidated, with the ownership policy above |
| Adani primary price listing | NSE; retain BSE as alternate evidence/listing |
| Mature-market ERP source | `ERPApril25.xlsx` |
| India country-risk source | `ctryprem.xlsx` combined with the approved mature-market ERP vintage |
| Adani annual PDFs | Official issuer content linked to NSE archive URLs; FY2024-25 and FY2023-24 stored separately |
| Valuation cutoff | 2026-08-01, Asia/Kolkata |

Approved assumption-set seed:

| Input | Source locator | Value |
|---|---|---:|
| Mature ERP, low scenario | `ERPApril25.xlsx`, `Impl premium calculator!G24` | 4.24796875% |
| Mature ERP, base/current April 2025 | `ERPApril25.xlsx`, `Impl premium calculator!C42` | 4.58761430% |
| Mature ERP, high scenario | `ERPApril25.xlsx`, `Impl premium calculator!G25` | 6.45000000% |
| India country-risk increment | `ctryprem.xlsx`, `ERPs by country!F72` | 2.93317868% |
| India total ERP, low/base/high | Mature ERP scenario + India increment | 7.18114743% / 7.52079298% / 9.38317868% |

Version-lock inputs by SHA-256:

```text
ERPApril25.xlsx  a58d5fa832e5d4aca2ee4355ebc50ae86dda16291dc5e3ec0bab04db66fdbf30
ctryprem.xlsx    04c55506c9fecfc437acf6be733dd58b9935832868ee0bf7bdd451d68436e35a
```

`ctryprem.xlsx` contains a 4.33% mature-market base and a 7.26317868%
rating-based India total ERP. Do not import that total unchanged into the
April set. The approved transformation retains its 2.93317868% India
country-risk increment and adds the April mature-market scenario value. This
mixed-vintage transformation must remain explicit in provenance.

The active supplied APSEZ package is version-locked as follows:

```text
FY2024-25 annual report  2ec4e75290acf3845677ab4a2efd64869d5c9ea5c472a3f0421d9d1611527262
FY2023-24 annual report  7f4ff812ea46d1d1c091e58f2161719285fee9ad39ea5e29c3b4beca13aea03f
Q1 FY2026-27 materials  f02e198abf211727c24adeea41b9b861dd6ff0afbb5d96664a1271dcad2edafd
```

The annual reports are local documents `3` and `4` with official NSE source
URLs. The Q1 materials are document `5`, classified as an official Source
Summary and linked to the revised unaudited consolidated NSE iXBRL. The earlier
`e14479...` local file is not part of the active certification set.

The SEC User-Agent and FRED key are already configured locally. Do not send
their values in chat.

### 5.2 Accounts to create

Create these two accounts before their implementation batches:

1. [Tiingo](https://www.tiingo.com/account/api/token)
   - create a free personal account
   - generate an API token
   - do not paste it into chat
   - the free plan is internal-use only
2. [Upstox Developer](https://account.upstox.com/developer/apps)
   - create/use an Upstox account
   - open the Analytics tab
   - generate the one-year read-only Analytics Token
   - record the displayed expiry date
   - do not enable or provide trading credentials
   - do not paste the token into chat

Do not create Twelve Data, FMP, Finnhub, Alpaca, DhanHQ, Marketaux, EIA,
OpenFIGI, NVIDIA, or Groq credentials yet. They do not unblock the next four
batches.

### 5.3 Local secret setup

Only after the relevant adapter exists, add these to the repository-root
`.env`:

```dotenv
TIINGO_API_KEY=""
UPSTOX_ANALYTICS_TOKEN=""
```

Put the real values between the quotes locally. Never add them to
`.env.example`, source code, screenshots, logs, or chat. The committed
`.env.example` should contain empty placeholders only after the application
actually supports the variables.

After adapter implementation, restart and check health:

```bash
cd "/Users/mananmaheshwari/Documents/Codex/Market Intelligence App/market-intelligence-md-files copy"
docker compose up --build -d
docker compose exec backend alembic upgrade head
curl http://localhost:8000/api/health
curl http://localhost:8000/api/providers/health
```

### 5.4 Decisions that can use the recommended default

If the user does not override them, use these defaults for planning:

| Decision | Default |
|---|---|
| Product license mode | Personal/internal local-only |
| Certification pair | AAPL and Adani Ports |
| India statement scope | Consolidated |
| Adani primary listing | NSE |
| India ownership bridge | Consolidated operations; deduct NCI once; add unconsolidated stakes separately |
| ERP assumption set | Versioned April 2025 mature ERP plus January 2025 India CRP increment |
| US price history | Tiingo adjusted EOD |
| India operational provider | Upstox read-only Analytics Token |
| Official India facts | Reviewed issuer/BSE/NSE documents |
| Live/tick prices | Out of MVP; use clearly labeled EOD/current snapshots |
| New Damodaran vintages | Imported inactive until review |
| Missing provider data | Manual upload/input with visible limitation |

## 6. Exact Next Task

Batch 2 certification is complete. AAPL FY2022-FY2025 and APSEZ FY2023-FY2025
are promoted, trust-ready, and exactly reconciled; FY2021 remains untouched.
The two-market manifest passes. The next data task is to replace APSEZ's
preserved 100% single-industry user assumption with reviewed segment revenue
weights and expose per-component benchmark completeness. Tiingo and Upstox
remain deferred until that provenance workflow and data-health visibility are
complete.

Exact AAPL status:
`docs/roadmaps/aapl-real-source-certification-checkpoint-2026-08-01.md`.

Exact Adani status:
`docs/roadmaps/adani-ports-real-source-checkpoint-2026-08-01.md`.

## 7. Stop Rules

Stop provider implementation if:

- the user intends public/commercial use but the selected plan is personal or
  internal-use only
- a provider term does not allow the required storage/display behavior
- an endpoint requires trading permission
- an official and provider fact conflict without a review path
- a migration would duplicate or replace existing source/evidence tables
- a secret appears in logs, browser code, test fixtures, or API responses
- provider failure becomes mock, zero, or silent fallback data
- real-source certification is weakened to make a dataset pass
