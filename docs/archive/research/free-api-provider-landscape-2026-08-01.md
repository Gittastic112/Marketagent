# Free API Provider Landscape

**Status:** Research and implementation plan, not proof of integration

**Reviewed:** 2026-08-01

**Scope:** Local-first US/India public-equity research, market data, macro data,
news discovery, security identity, and external AI inference

## 1. Decision Summary

There is no single free API that can safely supply this product's full data
layer. Free market-data plans are generally personal-use, delayed, tightly
rate-limited, restricted from redistribution, or too unstable for a canonical
record. The viable approach is a capability-based provider stack with honest
fallback states.

Recommended local stack:

| Capability | Primary source | Secondary source | Decision |
|---|---|---|---|
| US filings and reported financials | SEC EDGAR and SEC XBRL | Manual reviewed PDF | Keep as canonical |
| India filings and financials | Reviewed official downloads/manual upload | None approved | Keep manual-first |
| US end-of-day prices | Massive Basic or Tiingo Starter after account/terms review | Alpha Vantage | Add behind the existing provider contract |
| India prices | Manual reviewed price import | yfinance, explicitly personal/unofficial | Do not claim trusted automation yet |
| Instrument identity | OpenFIGI v3 | SEC CIK and manual exchange identity | Build next; key is optional |
| US macro | FRED | BLS, BEA, Treasury Fiscal Data | Expand after identity work |
| Global/India macro | World Bank | RBI official downloads | Build World Bank; keep RBI download-first |
| News discovery | Issuer/regulator RSS | GDELT DOC | Add GDELT as discovery, not as fact authority |
| AI evaluation | Gemini or NVIDIA NIM preview | Groq free plan | Optional and externally transmitted |
| AI production | Approved paid/self-hosted provider | None | Free preview endpoints do not satisfy this gate |

The first engineering task was completed on 2026-08-01. The quote-only
`POST /market-prices/fetch-latest` compatibility route and canonical
`POST /api/market/ingest` route now share the configured `MarketDataProvider`
and persistence boundaries. yfinance is explicit `yfinance_personal`, and
provider/source metadata is stored and shown before more vendors are added.

## 2. What The NVIDIA Article Gets Right And Wrong

The supplied PDF correctly shows an OpenAI-compatible request using:

```text
https://integrate.api.nvidia.com/v1
```

That makes NVIDIA NIM relatively easy to add. The article's broad "free" claim
is not a production contract. NVIDIA states that Developer Program API access
is for prototyping, research, development, testing, and evaluation. Per-model
rate limits vary, high-load requests may be slow, model availability can
change, and production use requires an NVIDIA AI Enterprise license or an
approved production hosting partner.

Official references:

- [NVIDIA NIM FAQ](https://forums.developer.nvidia.com/t/nvidia-nim-faq/300317)
- [Run NIM Anywhere and pricing](https://docs.api.nvidia.com/nim/docs/run-anywhere)
- [NVIDIA API Catalog](https://build.nvidia.com/models)

### 2.1 Safe product role

Use NVIDIA for:

- local development and evaluation
- benchmark comparisons across supported models
- non-sensitive filing summaries after explicit disclosure
- testing the provider abstraction and failure states

Do not use NVIDIA preview endpoints as:

- the sole production AI provider
- an automatic fallback that hides another provider failure
- a destination for private thesis notes, portfolio details, or valuation
  assumptions without explicit user confirmation
- a source of facts without linked source evidence and human review

### 2.2 Required application configuration

The application does not currently read these variables. Add support only with
the adapter described below.

```dotenv
AI_PROVIDER=nvidia
NVIDIA_API_KEY=
NVIDIA_BASE_URL=https://integrate.api.nvidia.com/v1
NVIDIA_MODEL=<model-id-selected-from-current-nvidia-catalog>
```

The key belongs in `.env`, never in `frontend/`, committed files, logs, or an
API response. Do not put a model from this document into `.env.example` as a
permanent default because catalog availability changes.

An account-level smoke test, outside the application, is:

```bash
curl https://integrate.api.nvidia.com/v1/chat/completions \
  -H "Authorization: Bearer $NVIDIA_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "<current-model-id>",
    "messages": [{"role": "user", "content": "Reply with the word ready."}],
    "max_tokens": 16
  }'
```

### 2.3 Implementation contract

Build one reusable `OpenAICompatibleAIProvider` rather than a provider class
for every OpenAI-shaped service. Its constructor should require:

```text
provider_name
base_url
api_key
model_name
timeout_seconds
capabilities
```

Then configure NVIDIA and, later, Groq as instances. Required behavior:

1. Use the existing `BaseAIProvider` and `AIProviderResult` boundary.
2. Add explicit `AI_PROVIDER`; do not infer the provider from whichever key is
   found first.
3. Persist provider, model, prompt version, input hash, external data classes,
   disclosure version, limitations, confidence, and review state through the
   existing AI contract.
4. Reject unsupported structured-output requests instead of pretending every
   catalog model follows a JSON schema.
5. Map timeout, authentication, model-not-found, quota, and provider errors to
   stable public codes.
6. Honor `Retry-After` for `429` responses with bounded retry. Do not retry bad
   credentials or invalid requests.
7. Record every execution as a processing run or equivalent provider-usage
   event with latency and token/rate-limit metadata, without prompt text.
8. Never silently fall back to mock output or another provider.
9. Add mocked HTTP tests for success, malformed content, timeout, `401`, `404`,
   `429`, capability rejection, and provenance persistence.

## 3. Yahoo And yfinance

Yahoo does not offer a documented public Finance API in its current developer
API directory. `yfinance` is an unofficial library. Its own documentation says
it is not affiliated with or vetted by Yahoo and that Yahoo Finance data is
intended for personal use.

Official/current references:

- [yfinance legal disclaimer](https://ranaroussi.github.io/yfinance/index.html)
- [Yahoo developer APIs](https://developer.yahoo.com/api/)
- [Yahoo API guidelines](https://legal.yahoo.com/us/en/yahoo/guidelines/ydn/index.html)

The repository has corrected this defect. Routes no longer invoke yfinance
directly, the adapter does not write to the database, selection is explicit,
and deterministic contract tests cover symbol mapping, provenance, and visible
unofficial-source warnings. This makes the route honest; it does not make
yfinance an official or certified source.

Completed correction:

1. [x] Route all market-price fetches through `get_market_data_provider()`.
2. [x] Make yfinance available only as `MARKET_DATA_PROVIDER=yfinance_personal`.
3. [x] Label every yfinance result as unofficial/personal-use data.
4. [x] Expose its status and restrictions in Provider Health.
5. [x] Never silently use yfinance when an approved provider is unavailable.
6. [x] Add deterministic symbol, contract, provenance, duplicate, and failure
   coverage. Broader live-provider drift testing remains opt-in future work.
7. Do not redistribute or present a service-level guarantee for its data.

For this local product, yfinance can remain a convenience source. It should not
be the canonical historical record or the basis for a public/commercial launch.

## 4. Market Data Candidates

Free-plan limits and terms change. Verify the account terms again immediately
before implementation and record the reviewed date in the provider registry.

| Provider | Current free offer | Useful for | Constraint | Recommendation |
|---|---|---|---|---|
| Alpha Vantage | 25 requests/day across most datasets | Very small US watchlists and fallback history | Real-time and 15-minute delayed US data are premium; current app adapter is partial | Keep, but not as the default daily portfolio backbone |
| FMP | Basic: 250 calls/day, end-of-day/reference access | Endpoint evaluation and limited US coverage | Free plan is individual/testing oriented, symbol/endpoint access is limited, display/redistribution needs an agreement; repo adapter is a placeholder | Complete only after checking target symbols and license |
| Twelve Data | Basic: 8 API credits/minute and 800/day; real-time US/FX/crypto | Small US quote/history workload | Full international and India coverage is paid; business/display use has separate plans | Good optional US adapter, not the India solution |
| Massive (formerly Polygon.io) | Stocks Basic: 5 calls/minute, two years, end-of-day, reference, actions, minute aggregates | US EOD prices and corporate-action prototypes | Individual/non-professional use | Strong US local-only candidate |
| Tiingo | Starter: 50 requests/hour, 1,000/day, 500 unique symbols/month | US/China EOD history for a bounded local portfolio | Internal use only; no sharing/display to others | Strongest simple local EOD candidate if terms fit |
| Marketstack | 100 requests/month, one year EOD | Tiny smoke tests | Too small for routine ingestion | Do not prioritize |
| Nasdaq Data Link | API access to free datasets; dataset-specific limits and licenses | Alternative and specialist datasets | Not one uniform free market-data feed | Add only for a named dataset and use case |
| Finnhub | Key placeholder exists in `.env.example` | Potential quotes/news/fundamentals | No adapter exists and current free/commercial terms were not verified in this review | Keep as provider decision, not configured capability |
| Yahoo/yfinance | No official supported Yahoo Finance contract | Personal local convenience and India symbol experiments | Unofficial, personal-use, unstable | Explicit opt-in fallback only |

Primary references:

- [Alpha Vantage limits](https://www.alphavantage.co/support/)
- [FMP pricing and licensing notice](https://site.financialmodelingprep.com/pricing-plans)
- [Twelve Data free trial limits](https://support.twelvedata.com/en/articles/5335783-trial)
- [Massive pricing](https://massive.com/pricing)
- [Tiingo pricing and use scope](https://www.tiingo.com/about/pricing)
- [Nasdaq Data Link getting started](https://docs.data.nasdaq.com/v1.0/docs/getting-started)

### 4.1 India reality

No reviewed source in this research produced a free, documented, stable,
production-ready API for comprehensive NSE/BSE quotes, corporate actions,
filings, and fundamentals. Do not automate undocumented exchange web endpoints.

Use this order:

1. Reviewed official NSE/BSE/SEBI downloadable reports with source URL, hash,
   observed-at time, and a terms review for each automated download.
2. Manual filing/PDF/Screener uploads already supported by this product.
3. Manual reviewed market prices for valuation and portfolio snapshots.
4. yfinance only as an explicitly unofficial personal-use convenience.
5. A licensed vendor when automatic India coverage becomes a release
   requirement.

Relevant policy source:

- [SEBI market data access and terms guidance](https://www.sebi.gov.in/legal/circulars/feb-2022/approach-to-securities-market-data-access-and-terms-of-usage-of-data-provided-by-data-sources-in-indian-securities-market_56420.html)

## 5. Official Public Data Worth Adding

These sources improve research quality without pretending to replace licensed
exchange data.

| Provider | Authentication / public limit | Product use | Priority |
|---|---|---|---|
| SEC EDGAR | No key; identify the client and stay within SEC access policy | Filings, submissions, company facts | Already primary |
| OpenFIGI v3 | No key: mapping 25/minute; optional free key raises capacity | Exchange-aware symbol/FIGI identity | Build next |
| FRED/ALFRED | Free key | Rates, credit, volatility, macro series and revisions | Existing provider; broaden curated series |
| BLS Public Data API | v1 no key: 25 queries/day; registered v2: 500/day | CPI, employment, wages, productivity | Build after World Bank |
| BEA API | Free registration key | GDP, industry accounts, international and regional data | Useful US macro extension |
| World Bank Indicators | Public REST API | Country-level growth, inflation, trade and development context | Build next |
| US Treasury Fiscal Data | Public REST datasets | Debt, cash balance and fiscal context | Later macro extension |
| GLEIF API | Public LEI data | Entity/legal identity and ownership support | Later identity extension |
| Eurostat dissemination API | Public REST API | European macro/company-country context | Defer until Europe scope exists |

Primary references:

- [SEC EDGAR APIs](https://www.sec.gov/search-filings/edgar-application-programming-interfaces)
- [SEC automated access limits](https://www.sec.gov/filergroup/announcements-old/new-rate-control-limits)
- [OpenFIGI v3 documentation and limits](https://www.openfigi.com/api/documentation)
- [FRED API](https://fred.stlouisfed.org/docs/api/fred/overview.html)
- [BLS API limits](https://www.bls.gov/developers/api_faqs.htm)
- [BEA API registration and datasets](https://apps.bea.gov/api/signup/)
- [World Bank API call structure](https://datahelpdesk.worldbank.org/knowledgebase/articles/898581-api-basic-call-structures)
- [Treasury Fiscal Data API](https://fiscaldata.treasury.gov/api-documentation/)
- [GLEIF API](https://www.gleif.org/en/lei-data/gleif-api/access-the-api)
- [Eurostat API introduction](https://ec.europa.eu/eurostat/web/user-guides/data-browser/api-data-access/api-introduction)

## 6. News And Discovery Candidates

| Provider | Free status | Correct role | Decision |
|---|---|---|---|
| Issuer/regulator RSS | Public feeds where offered | Primary announcement discovery | Keep primary |
| GDELT DOC 2.0 | Public search returning JSON/RSS | Broad multilingual discovery and corroboration candidate generation | Build with strict source linking; not a fact authority |
| NewsAPI | Developer tier is localhost/development-only, delayed, and capped | UI/prototype evaluation | Do not use as a free production source |
| Guardian Open Platform | Free developer access is non-commercial and capped | Named-publisher experiments | Do not make a default source |
| Social APIs | Terms and access vary | Optional reviewed signals only | No scraping; defer |

References:

- [GDELT DOC 2.0](https://blog.gdeltproject.org/gdelt-doc-2-0-api-debuts/)
- [NewsAPI pricing](https://newsapi.org/pricing)
- [Guardian Open Platform access](https://open-platform.theguardian.com/access/)

Only store article text when the source terms explicitly permit it. Otherwise
store discovery metadata, the source URL, publication time, hashes where
appropriate, and bounded user-visible excerpts.

## 7. AI API Candidates

| Provider | Current no-cost access | Constraint | Recommendation |
|---|---|---|---|
| Gemini | Free tier exists for selected models with project/model-specific limits | Data handling and limits vary by model | Keep existing adapter; make provider selection explicit |
| NVIDIA NIM catalog | No-cost hosted preview for Developer Program evaluation | Development/test only, variable limits and availability, no production SLA | Add through generic OpenAI-compatible adapter |
| Groq | Free plan with published per-model request/token limits | Limits and model catalog change | Good optional development fallback, never silent |
| OpenRouter | Free-model routes with low account-dependent daily limits | Additional processor/router; free models are not production-grade | Evaluate only when multi-provider routing is worth the privacy surface |
| Cloudflare Workers AI | 10,000 neurons/day free allocation | Requires Cloudflare account/runtime and neuron-based budgeting | Defer unless Cloudflare becomes infrastructure |
| Hugging Face Inference Providers | Very small monthly free credit | Not enough for routine app use | Model experiments only |
| Cerebras | Short trial credits, not a durable free plan | Payment verification and expiry | Do not call it free infrastructure |
| GitHub Models | Included free, rate-limited usage; paid usage is opt-in | GitHub describes the free experience as experimentation rather than production; adds a GitHub-hosted provider surface | Viable evaluation option, lower priority than the reusable direct-provider adapter |

References:

- [Gemini API billing](https://ai.google.dev/gemini-api/docs/billing)
- [Groq free-plan rate limits](https://console.groq.com/docs/rate-limits)
- [OpenRouter FAQ](https://openrouter.ai/docs/faq)
- [Cloudflare Workers AI pricing](https://developers.cloudflare.com/workers-ai/platform/pricing/)
- [Hugging Face inference pricing](https://huggingface.co/docs/inference-providers/en/pricing)
- [GitHub Models billing and included free usage](https://docs.github.com/en/billing/concepts/product-billing/github-models)

## 8. Provider Architecture Required Before Expansion

Do not let API keys determine architecture. Every provider must register a
reviewed contract containing:

```text
provider_id
capability
market_coverage
data_types
official_or_unofficial
use_scope
redistribution_allowed
attribution_required
reviewed_terms_url
terms_reviewed_at
requires_key
configured
quota_window
quota_limit
quota_remaining
last_request_at
last_success_at
last_failure_at
last_error_code
freshness_sla
```

Every provider result must include or permit derivation of:

```text
provider
source_url or provider record id
observed_at
source_timestamp
is_stale
is_partial
is_mock
currency and units where relevant
warnings
```

Operational rules:

1. Centralize outbound HTTP behavior: timeout, bounded response size, safe URL,
   retry policy, user agent, structured errors, and redacted logging.
2. Cache according to source freshness and license, not merely to reduce calls.
3. Preserve the raw response only where terms permit; otherwise preserve the
   permitted normalized record and retrieval provenance.
4. Create a processing run for ingestion and synchronization work.
5. Read rate-limit headers and expose quota/failure state in Data Health.
6. Return `not_configured`, `partial`, `stale`, or `source_unavailable`; do not
   replace failure with zero, old unlabeled data, mock data, or another source.
7. Require market, exchange/MIC, local symbol, and currency for price requests.
8. Keep all secrets server-side and run the secret scanner before release.
9. Add contract fixtures so provider response drift fails a test instead of
   corrupting normalized records.
10. Re-review pricing and terms quarterly and before any public/commercial use.

## 9. Feasible Delivery Sequence

The repository-specific sequence selected after reviewing the separate market
valuation blueprint is in
[Provider Data Execution Plan](provider-data-execution-plan-2026-08-01.md).
That plan overrides the generic ordering below where they differ.

### Phase A: Correctness first

1. [x] Replace the direct yfinance route call with the configured market-data
   factory.
2. [x] Add explicit provider identity and source timestamps to quote/history
   results.
3. [x] Add yfinance as an opt-in `yfinance_personal` adapter with a visible legal
   limitation.
4. [x] Replace the empty yfinance test with real mocked contract tests.
5. Add provider quota/use-scope fields to Provider Health.

### Phase B: High-value public sources

6. Implement OpenFIGI v3 mapping without requiring a key; use a key only for
   higher quotas.
7. Implement World Bank country indicators through the macro-provider boundary.
8. Add a small reviewed BLS series registry and v1/v2 adapter.
9. Add GDELT discovery with deduplication, source links, bounded excerpts, and
   explicit discovery-source labeling.
10. Add live-provider smoke tests that are opt-in and never required for the
    deterministic unit suite.

### Phase C: Market provider decision

11. Trial Massive Basic and Tiingo Starter against the actual US portfolio
    symbols.
12. Measure missing symbols, adjusted-price behavior, corporate actions,
    currencies, source times, and quota cost.
13. Select one US EOD primary and one explicit fallback.
14. Keep India manual-first until a licensed source decision is recorded.
15. Retire the unused FMP placeholder or complete it only if its tested coverage
    and terms beat the selected provider.

### Phase D: Optional AI evaluation

16. Implement the generic OpenAI-compatible AI adapter.
17. Add NVIDIA as a development/evaluation configuration.
18. Add Groq only as a separately selected provider, not an automatic fallback.
19. Extend AI disclosure to name the external provider and transmitted data
    classes before every request.
20. Run the existing citation/evaluation corpus for every selected model and
    block models that fail grounding thresholds.

## 10. Acceptance Gate For Any New Provider

A provider is not shipped because one HTTP request succeeded. It is shipped
only when:

- terms, allowed use, attribution, and redistribution are recorded
- secrets remain backend-only
- the configured/not-configured state is visible
- quota and `429` behavior are tested
- timeout, provider failure, malformed response, and empty data are tested
- source time, observed-at time, provider, units, and currency are persisted
- stale and partial results are visible
- no silent fallback exists
- processing-run/provider-health records update
- deterministic fixtures cover normalization
- one real account smoke test passes for declared target symbols/series
- current-state and runbook documentation are updated
