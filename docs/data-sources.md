# Data Sources & Ingestion Flow

## Principle
Start with clean, legal, source-backed inputs. Prioritize public, stable, structured sources.

This file explains what data sources exist, how ingestion flows operate (manual vs. automatic), and what data is preserved.

---

## 1. Current Ingestion Flow

```text
manual setup, provider status check, or ingestion trigger
-> Source / ProcessingRun / RawDocument / provider-specific table
-> optional Event extraction
-> deterministic Event scoring
-> Alert if priority is high enough
-> DailyBrief reads scored Events and Alerts
-> optional valuation/fundamentals candidate review path
```

AI is not the primary ingestion layer. Current ingestion and scoring should remain deterministic and source-backed. AI-adjacent services exist for memos, narrative-to-numbers, summaries, and event-to-thesis impact classification, but their outputs must be treated as interpretations requiring provenance and human review.

### 1.1 Automatic Steps
- **RSS Ingestion:** Stores each feed item as a `RawDocument`. Links a company only when deterministic matching finds exactly one active company by ticker, company name, or alias.
- **SEC Ingestion:** Stores filing metadata and available filing text as `RawDocument` records for US companies when `SEC_USER_AGENT` is configured. It accepts an optional source id, validates a supplied SEC source, otherwise resolves an active SEC source or creates the local `SEC EDGAR` source record.
- **Market-Aware Filing Acquisition:** `GET /api/companies/{company_id}/filings/discover` returns US SEC candidates or an explicit India manual-only state. `POST /api/companies/{company_id}/filings/manual-link` stores reviewed manual filing links/text as traceable `RawDocument` records.
- **Financial Candidate Extraction:** `POST /api/filings/{filing_id}/extract-financials` creates first-pass candidates from reviewed filing text with typed line/page/section locators. `POST /api/companies/{company_id}/extract-xbrl` creates SEC `companyfacts` candidates with concept, unit, fiscal period, filing, accession, and frame locators. Warning codes and confidence expose missing units, inferred fiscal years, and ambiguous source lines.
- **PDF Filing Upload, Extraction, and Evidence Rendering:** Authenticated `POST /api/companies/{company_id}/filings/pdf` stores a validated original PDF, optional official source URL, extracted page text, and deterministic candidates. Files may be up to 40MB and 1,000 pages. Full scans stop at 500 pages; longer reports require explicit `page_ranges` covering at most 75 pages. `pdf_targeted_v5` preserves facing-page regions, fiscal-range end years and complete Indian number groups, and adds explicit statement totals, banking/cash-flow rows and bounded wrapped-label handling. Original row text and absolute highlight coordinates remain. Observed embedded ITFRupee header symbols retain font/position evidence and a review warning; unembedded fonts and bare letters do not establish currency. Explicit per-share currency and local share-count scales remain separate from monetary scales. Bank cash, deposits, interest, borrowing components, group/parent profit and cash-flow adjustments keep distinct meanings. Investment scope requires review; borrowing/lease rows are not automatically summed. EPS tokens with explicit rupee prefixes or uniquely matched embedded ITFRupee glyphs are supported with retained evidence. A repeated, geometrically separate right-margin navigation number can be excluded from cash-flow rows only after verifying year-column alignment; the original text and exclusion warning remain. Conflicting currencies, unverified glyphs and unexplained extra columns stay rejected. Existing v2/v3/v4 records are not rewritten. Locators preserve page/row/cell references and bounding boxes where available; certification accepts legacy and bounded regional locations. Processing limits remain enforced: select fewer pages when a batch exceeds them. `GET /api/raw-documents/{id}/asset` returns metadata only; authenticated `GET /api/raw-documents/{id}/asset/content` streams the original source. Authenticated `GET /api/raw-documents/{id}/asset/pages/{page}.png` renders a bounded stored page for exact evidence overlays; it is not a generic URL or arbitrary-PDF renderer.
- **Screener Workbook Extraction:** `POST /api/companies/{company_id}/fundamentals/screener` accepts `.xlsx` files up to 2MB. It hashes bytes, rejects duplicates, creates source/raw-document/processing-run records, removes temporary files, and emits reviewable candidates with sheet, row label, column header, cell coordinate, and reporting unit.
- **Financial Candidate Review:** Review, reject, override, and promote endpoints exist. A reporting unit is mandatory before review/override. Promotion writes legacy metrics plus canonical normalized snapshots, persists currency source/confidence, and blocks conflicting currencies.
- **Post-Ingestion Pipeline:**
  - Extracts events from raw documents that do not already have events.
  - Scores those events deterministically.
  - Generates alerts for events whose priority passes the alert threshold.
- **Processing Runs:** SEC/RSS/FRED ingestion, PDF/Screener upload, filing text extraction, SEC XBRL extraction, and normalized backfill preview/apply attempts create `ProcessingRun` records with statuses, counts, timestamps, safe errors, metadata, and source/company links. Direct ingestion endpoints remain synchronous. The valuation source-refresh workflow below adds a persisted queue and separate worker, not a general ingestion-job system.
- **Provider Health:** `GET /api/providers/health` reports configuration plus
  never-run, running, partial, successful, stale, and failing evidence for SEC
  EDGAR, RSS, FRED, market data, AI, OpenFIGI, Damodaran benchmarks, and India
  manual filing support. Run-backed providers expose attempts, recent run count,
  consecutive failures, age thresholds, and required action. RSS coverage is
  the count of active shared catalog sources; these are not owner-private rows.
  AI health recognizes the implemented Gemini adapter only and uses audited
  fixed-prompt probes for the currently configured GEMINI_MODEL. An unrelated
  model's success or a configured unsupported provider key is not working proof.
- **Source Capability Matrix:** `GET /api/source-capabilities?market=US|IN` reports whether each source class is available, manual-only, not configured, or unsupported for the selected market.
  Price status follows the selected adapter and its own configuration. FMP remains
  unsupported even with a key; personal-use prices need no key. SEC requires a
  valid contact and implemented FRED ingestion requires its key. Configuration is
  separate from fetch success, coverage, freshness and reviewed facts.
- **Daily Brief:** Automatically pulls the highest-priority scored events and latest alerts when requested.
- **FRED to Market Regime:** Authenticated FRED import persists the provider name,
  official series URL, dated observations, and an audited Processing Run. The
  Market Regime NFCI preflight is read-only and uses the latest stored observation
  on or before today. Apply creates one exact-record-linked provider input using
  `clamp(-NFCI × 50, -100, 100)`. It does not make a network request. Stale,
  missing, future-only, unverified, or malformed evidence remains explicit.

### Price boundaries and explicit connectivity

India discovery exposes a dated official issuer source only when the company's
NSE symbol and ISIN match the fixed research scope. The source checklist supplies
report years and required notes; it neither downloads nor approves financial values.
Upload the report or paste the exact excerpt with source date, page, currency,
scale and consolidated/standalone basis, then use candidate review. Unknown or
mismatched identities retain the generic manual-only path without a guessed link.

The fixed scope and official identity sources live in
[research-scope.json](../data/research-scope.json); this is a dated selection,
not an automatically refreshed market-cap ranking. US/India history excludes the
current market-local date using America/New_York/Asia/Kolkata, bounded to 1-3650
calendar days. Prior-date bars are provider data, not independently certified
exchange closes. Current quote source timestamps/delay may remain unknown.

The personal-use SDK runs in a one-use resource-limited Linux child, terminated
on deadline or cancellation. No app secrets or proxy environment are inherited.
FRED/Alpha Vantage share a fixed-host, no-redirect/no-proxy bounded JSON transport;
required query keys stay out of HTTPX URL logs. No fallback is introduced.
Price writes validate the selected security and serialize after fetching. Failures
and cancellations are audited without partial writes. Separate explicit public
connectivity probes create Processing Runs, never price or financial coverage.

### Review-required valuation drafts

`POST /api/companies/{company_id}/valuation-source-refresh` queues an owned job
and returns immediately. `GET` on that path returns schedule/latest-run status;
`GET /api/valuation-source-refresh/{run_id}` returns only the caller's run.
The local worker imports FRED DGS10/NFCI, supported SEC annual companyfacts and
available prices. Companyfacts streams have a 32 MiB decoded-byte cap, no redirects,
20-second I/O timeout and an elapsed deadline checked between chunks. Invalid or
wrong-issuer payloads fail before persistence. It then refreshes the owner's draft.
Provider steps retain their
own Processing Runs and failures. A partial source failure does not hide the
other results or change the date on an older price.

The user-approved policy is the latest completed financial year, not TTM.
SEC v3 keeps debt components distinct and appends revised candidates. Derived
amounts require matching annual source bases; unreviewed absolute values never
fill gaps in a reviewed million-scale financial basis. DGS10 supplies a dated
USD risk-free proxy only. Benchmark priors keep their source currency/scope.
Mock-marked prices are excluded. All suggestions require review before saving
a model; no canonical financial approval or saved-model overwrite is performed.

Edited draft fields survive refresh. Changed evidence or newly stale sources
clear the affected review, while an ordinary daily age increment does not.
Weekday 07:00 America/New_York scheduling is opt-in and requires the local worker.
Interrupted jobs and their running child attempts are marked failed on the next
cycle; already completed children remain intact. Retry is explicit, with
no missed-date backfill. Setup and commands belong in the
[operations guide](operations.md#valuation-source-refresh).

### Local extraction evaluation

The authenticated `/evaluations` page runs the local text-line extractor against
an independently reviewed, complete reference for one company-linked stored
document. Load the source basis, inspect its text and line numbers, enter up to
200 reference rows, explicitly classify Mock Data versus a genuine source, and
confirm the reference review/completeness. The backend checks the exact text
SHA-256 before execution and stores an owner-scoped report with reference hash,
extractor/evaluator versions, precision, recall and per-field comparisons.

An exact match needs metric, line, value, unit and fiscal period. Missing units
are errors, not inferred successes. Empty predictions produce unavailable
precision and zero recall. This is a bounded local evaluation, not provider
ingestion: no external API call, candidate promotion or source mutation occurs.
It does not evaluate PDF layout, XBRL, AI or forecast outcomes. Historical empty
run creation remains compatible but explicitly says it has not executed.

### Private research text and PDFs

Daily Brief has a separate owner-private inbox. `POST /brief-sources` saves
pasted text; `POST /brief-sources/pdf` stores an original PDF and selected-page
text. Limits are 12 MB, 1,000 total pages, 20 selected pages and 60,000 extracted
characters. This is not the shared financial-candidate upload path above, which
has different limits and review responsibilities. No OCR or chart analysis occurs.

Saving does not call AI. An explicitly disclosed `POST /brief-sources/{id}/analyze`
sends only the selected source text/date, public company identity and field names.
Ranked findings retain exact passages and links to 14 core valuation inputs;
they do not change those inputs, approve facts or join scheduled brief snapshots.
Imports/scans have Processing Runs. Owned source detail and original-PDF reads
are private/no-store; collection responses omit text and binary bodies.
Inbox search covers original titles/text with company, format, scan and lifecycle
filters. Active sources are the default. Version-checked archive/restore keeps
original evidence and completed findings readable; it is not deletion or approval.
Reimporting the same source leaves its archive state intact. Archived sources
must be restored before scanning. No archive action changes a valuation.

`GET /brief-sources/triage?company_id=...` compares stored findings by core
valuation field. It examines the newest 50 active sources for that owner/company,
discloses older/unscanned/unusable exclusions, and excludes Mock Data by default.
Exact-span receipts, successful execution, source identity and human review state
gate inclusion. The comparison itself neither fetches sources nor calls AI.
Opposing directions are inspection prompts, not semantic contradiction detection;
different periods, horizons or business scopes can explain them. Source dates and
all supporting passages remain available for independent review.

### 1.2 Damodaran Source Layers

Damodaran data has two distinct locations:

- `damodaran_knowledge_base_v1/` is the canonical evidence and doctrine layer.
  It contains immutable originals, SHA-256 hashes, source dates, date confidence,
  status, processing decisions, model references, and review items.
- `data/damodaran/raw/` is the application runtime mirror used by backend import
  tooling. Presence in this folder does not mean the workbook is parsed or shown
  in the UI.

Before source or valuation work, run:

```bash
python3 damodaran_knowledge_base_v1/tools/audit_kb.py
```

New originals go only to `damodaran_knowledge_base_v1/raw/inbox/`. Process them
under the nested `AGENTS.md`, then update the catalog, processing ledger, hash
ledger, manifest, derived references, and review queue. Never edit a routed raw
file. Current source state and prioritized follow-up are in
`damodaran_knowledge_base_v1/PROCESSING_PLAN.md`.

`GET /data-health/damodaran-coverage` is the application-ingestion truth
boundary for the 41-workbook runtime mirror. It combines a versioned
source/metric registry with live source presence, dataset metadata, typed
destination row counts, freshness, omissions, and required actions. A workbook
is `ingested` only when source-specific typed rows exist. A successful generic
admin parse is `metadata_only` and must not be presented as a usable benchmark.
See [Current State](current-state.md) for the latest recorded counts and
their evidence date. This document does not certify live database contents.

Capex, ROE, Margin, Working Capital, Dividend, FCFE, Volatility, PE, PBV, PS,
EV/EBITDA, and Country Statistics use
`DamodaranDatasetVersionService`. The importer hashes the actual runtime source,
records byte size and canonical source metadata, verifies same-hash row counts,
preserves changed versions, and exposes the active version in Data Health. The
source-specific parsers require their tested workbook headers before version
creation, reject empty sources transactionally, preserve firm counts, exclude
aggregate Total Market rows, and preserve null source cells.

Source semantics are strict. Margin `ebit_margin` maps to `Pre-tax Unadjusted
Operating Margin`; it and EBITDA are not substitutes for lease/R&D-adjusted
margins. Those adjusted-prior fields remain unavailable. FCFE maps `Net Income`, `FCFE (before debt cash flows)`, and
`FCFE (after debt cash flows)`. The workbook does not provide separate Capex
minus depreciation, working-capital change, or net-debt-issued columns, so those
legacy fields remain null. Compatibility `fcfe` mirrors the after-debt value.

The explicit US intake uses six dated January 5, 2026 mirrors for beta, cost of
capital, margins, reinvestment, ROE and working capital. It verifies the embedded
US population and date before using the existing typed parsers, writes Processing
Runs, and preserves India versions. US WACC creates no artificial INR methods.
Industry selection still requires analyst confirmation; current Treasury proxies
and dated workbook ERP may use different sovereign-risk conventions. See the
[source intake record](../damodaran_knowledge_base_v1/reference/us_benchmark_intake_2026.md)
and [import command](operations.md#us-benchmark-intake).

Volatility requires exact `optvarIndia.xls` headers and both source assumption
rows. It stores the source's relative bond/equity volatility ratio (`0.40`) and
stock/bond correlation (`0.50`) explicitly. Active reads require a linked active
dataset version; old unlinked rows are preserved but ignored. Legitimate zeros
and nulls remain unchanged. The API returns a stable not-found error instead of
generic fallback values.

Use scoped ingestion to avoid refreshing unrelated legacy sources:

```bash
docker compose exec backend python /workspace/scripts/ingest_damodaran.py --only roe
docker compose exec backend python /workspace/scripts/ingest_damodaran.py --only capex roe
docker compose exec backend python /workspace/scripts/ingest_damodaran.py --only margin working_capital dividend fcfe
docker compose exec backend python /workspace/scripts/ingest_damodaran.py --only volatility
docker compose exec backend python /workspace/scripts/ingest_damodaran.py --only pe pbv ps vebitda
docker compose exec backend python /workspace/scripts/ingest_damodaran.py --only country_stats
```

The command reports active version ID, full SHA-256, source date, row count,
and the current coverage/provenance summary. Generic admin uploads are
`metadata_only` and inactive. Pricing rows are version-safe but intentionally
remain source-separated; relative-valuation reads assemble only active rows and
return source provenance per method. Country-statistics reads likewise require
the active hashed version and expose it with the country facts. All current
source-specific typed Damodaran importers are version-safe; unsupported mirror
files remain unimplemented rather than implicitly covered.

### 1.3 Manual Inputs
- Companies, Sources, Raw Documents, Events, Alerts, and Thesis Notes can all be added manually via `POST` routes or their respective UI pages.
- RSS sources use the existing Source record with `source_type="rss"`, a feed URL in `base_url`, manual `reliability_score`, and `active` status.
- India filings are manual-first. Use reviewed links/text until a compliant NSE/BSE/vendor data source is selected and implemented.
- Manual PDF upload is available for both markets. Long text-based reports can
  use bounded target page ranges. Scanned PDFs still need OCR; arbitrary merged
  layouts and operating/non-operating accounting classification still require
  review or a later layout-aware parser.
- Market/rate context can be entered manually through country/market context endpoints. Missing values must return not-configured states, not fabricated defaults.
- Alert review status and notes are manual human feedback.
- Daily briefs have persisted deterministic generation and an opt-in local
  scheduler. Explicit AI refresh is separate; scheduling does not call external AI.

---

## 2. Source-Specific Strategies (Design Brief Alignment)

### 2.1 SEC EDGAR Strategy
SEC ingestion exists in `backend/app/services/sec_ingestion.py`.
- **SEC User-Agent:** SEC APIs require respectful access. The system must enforce a valid `SEC_USER_AGENT` environment variable (e.g., `MarketIntelligenceApp/0.1 contact: email@example.com`) before any SEC API calls are made.
- **CIK Lookup:** US company lookup routes through SEC EDGAR and can return CIK/regulatory identity. India lookup is not equivalent and must stay explicit about manual or not-implemented provider status.
- **Filing Diffs:** When filing text is present, event extraction compares the current filing with the prior stored filing for the same company and form type. If the text changed, it creates a `filing_text_change` event with prior/current RawDocument IDs, source URLs, and a first-pass line diff.
- **Bounded Downstream Text:** Generated event and alert summaries are concise, HTML-stripped, and bounded. Full filing text remains in the raw document and is not copied into event descriptions, alerts, or collection payloads.
- **SEC XBRL Candidate Extraction:** `backend/app/services/sec_xbrl_extractor.py` reads SEC `companyfacts`, creates or resolves the SEC source without hardcoded ids, selects a deterministic unit, stores typed fact locators, and emits reviewable candidates. It is not filing-specific statement reconstruction and does not prove completeness.

### 2.2 RSS / News Strategy
RSS ingestion exists in `backend/app/services/rss_ingestion.py`.
- RSS is the current lowest-risk news ingestion route.
- Structured News APIs are future/provider-backed work and must appear as not configured or unavailable until keys and provider logic are present.
- The pipeline may use `NEWS_API_KEY` or equivalent provider keys later, but UI claims must not imply live provider coverage before it exists.

### 2.3 Price Data Strategy
- Manual prices and market context are supported.
- `POST /api/market/ingest` is the canonical quote-plus-history ingestion route. `POST /market-prices/fetch-latest` is a quote-only compatibility route. Both use the configured `MarketDataProvider` factory and the same persistence boundary.
- Both routes delegate to services/market_data/ingestion.py. History windows are
  bounded to 1-3,650 days. The Processing Run precedes provider configuration and
  network calls; prices/history and caller-owned divergence alerts commit together.
  Configuration or downstream failures retain an audited failed run without partial
  price writes. Same-date quote/history rows are flushed before duplicate checks.
  The response identifies the explicitly selected adapter, not a fallback wrapper.
- Normalized quote/history results carry provider, provider symbol, market, exchange, ticker, currency, source/observed time, price type, delay, adjustment state, and warnings. Stored `market_prices` and `company_market_data` rows expose this provenance; manual rows are labeled `manual` and legacy rows are labeled `legacy_unknown`.
- `/market-prices` renders source/timing labels and warning details so manual, legacy, unofficial, and configured-provider rows are distinguishable without inspecting the API.
- Alpha Vantage and explicit `yfinance_personal` adapters are implemented. yfinance is unofficial and personal-use oriented, never a silent fallback, and emits a warning on every result. FMP is an explicit non-operational placeholder and returns `PROVIDER_NOT_IMPLEMENTED`.
- The personal provider is pinned to yfinance 1.7.0 after live checks found the
  old 0.2.37 dependency failed for both US and NSE symbols. Latest quotes still
  have unknown source time/delay, not verified real-time status. Daily history
  requests and filters dates strictly before the current UTC date, conservatively
  excluding an unfinished current-day bar even after that market has closed.
  Refresh is available on demand and through the opt-in weekday valuation-source
  worker described above. It is not a streaming or intraday polling service.
- Explicit market-context routes avoid ambiguous symbols. Legacy ticker-only routes reject cross-market or cross-exchange ambiguity.
- Missing credentials, unsupported providers/symbols, rate limits, timeouts, invalid responses, identity/currency mismatches, and provider failures return stable public errors. Provider failure does not become zero, mock, or silent fallback data.
- Provider-backed data must expose configured/missing/failing/stale states through provider health and API metadata.
- Price routing/provenance is repaired, but this is not a certified US/India market-data layer. AAPL/APSEZ financial reference paths have dated test evidence, not universal live-source certification. Broader India coverage and Tiingo/Upstox adapters remain incomplete.
- Dated free/public provider research and terms constraints are preserved in the [archived provider landscape](archive/research/free-api-provider-landscape-2026-08-01.md). It is research evidence, not proof that a listed provider is integrated.
- A Google Sheets bridge is not implemented. The user's accepted 20-minute quote
  delay does not remove GOOGLEFINANCE's international-coverage and historical
  API-access restrictions. Do not publish private holdings to build a quote feed.
  [Google's source restrictions](https://support.google.com/docs/answer/3093281?hl=en).

### 2.4 Financial Statement and Fundamentals Strategy
- First-pass extraction from reviewed filing text exists.
- SEC XBRL `companyfacts` candidate extraction exists for US companies with CIKs.
- India fundamentals remain manual-first unless a compliant structured provider is selected.
- `financial_extraction_candidates` are review candidates, not trusted normalized statements.
- `normalized_financial_snapshots` and `normalized_financial_metrics` are the canonical read path when a snapshot exists. Coverage and reconciliation endpoints expose stale, missing, mismatched, or normalized-only metrics before valuation use.
- Assumption autofill must not silently use placeholder actuals as if they were source-backed financial data.
- The APSEZ reference flow uses the latest annual-report comparative for each
  year, stores NCI and associates separately, sums exact reported debt
  components with a Calculation warning, and refuses to invent operating EBIT.
  See `archive/checkpoints/2026/adani-ports-real-source-checkpoint-2026-08-01.md`.

### 2.5 Social / Forum Strategy
- The system will NOT scrape Reddit or X/Twitter HTML.
- Will only use official/approved APIs. Social posts must maintain exact source URLs and hashes.

---

## 3. Data Freshness & Trust Rules
Trust is the app's primary feature. If the data is broken, the user must know.

### 3.1 Data Freshness Definitions
- **Healthy:** Data fetched successfully within expected timeframes.
- **Stale:** Stored data is older than its configured freshness threshold.
- **Unavailable/failed:** A request or run failed; this is not successful stale data.
- **Not Configured:** The user has not provided required API keys or User-Agents.
- **Partial:** Some sources for a company succeeded, others failed.

### 3.2 Stale Data Rules
If data is stale, the frontend must clearly display a warning (e.g., `"Sentiment score may be stale. Last successful ingestion: May 28, 2026."`). The backend must support this by returning `last_updated` and `is_stale` in the `meta` envelope of the API response.

### 3.3 Mock Data Labeling
Mock Data is allowed only as an explicitly labeled fixture/demo. A missing
endpoint must show Not available yet, not invented intelligence. Provider or
transport failures must never fall back to mock success.

---

## 4. Data Provenance Requirements
Every source record must store:
- provider
- source type
- source URL
- published timestamp
- ingestion timestamp
- raw text or raw payload
- content hash
- linked company if applicable

Financial extraction candidates and normalized financial metrics must additionally preserve:

- source document id or source provider
- extraction method
- review status
- reviewed/overridden value when applicable
- currency/unit
- warning or provenance notes
- whether the value is candidate, reviewed, overridden, rejected, or promoted

---

## 5. Security Notes
- Treat imported CSV, markdown, RSS, social posts, and AI output as untrusted inputs.
- Treat SEC/RSS/provider text as untrusted display content even when the source itself is reputable.
- Do not store broker passwords.
- Do not sync brokers until OAuth is fully implemented.

## Market Data & Financials

Market data uses the `MarketDataProvider` interface for Alpha Vantage or the
explicit `yfinance_personal` adapter when configured. FMP is not implemented.
Manual prices and manual country/market context remain valid and are labeled.
Tiingo and Upstox are approved roadmap choices, not current integrations.

Financial trends can be drafted from SEC `companyfacts` using `SEC_USER_AGENT`, but extraction outputs are candidates until reviewed. Do not treat extracted or autofilled numbers as valuation-ready without user review, source labels, warnings, and deterministic calculation support.
