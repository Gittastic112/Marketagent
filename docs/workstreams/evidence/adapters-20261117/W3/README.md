# W3 market, identity and calendar adapter evidence

Baseline: `371b58c02cfd2b80429f28dbc13629165b5e392d`. Implementation and checks were performed in the isolated W3 worktree. No database migration, deployment, paid-provider call, holding mutation, identity merge or AI disclosure was performed.

## Implemented scope

1. FMP stable US equity profile and quote; inclusive dated history using documented split-adjusted `close`. Quote currency and venue are verified through the profile. Unknown subscription delay stays unknown. Unadjusted FMP history requests are explicitly unsupported by this selected endpoint.
2. Massive US equity reference, last-trade snapshot, inclusive daily aggregates and current `/stocks/v1/splits` and `/stocks/v1/dividends`. Pagination only extracts a bounded cursor for the same allowlisted endpoint. Missing last-trade access never substitutes the previous-day close. Explicit split adjustment is distinct from total return.
3. Official NSE MCP `cm_get_stock_quote`, `get_stock_history` and `get_corporate_actions`. Initialization, session headers, tools/list schema checks and JSON/SSE responses use protocol `2025-03-26`. Only exact EQ identities are accepted. Dated quotes derive from actual history dates; the bare-number `get_ltp_by_date` tool is deliberately not used for date resolution. Mixed settlement series create explicit gaps. Current quotes use `latestTimestamp`, interpreting offset-free source timestamps in Asia/Kolkata; cache `updatedAt` is not the price timestamp.
4. OpenFIGI candidate mapping, explicit exchange/MIC filter and unlisted-equity choice. Several candidates remain ambiguous. No accepted identity or historical validity is invented.
5. pandas_market_calendars 5.6.1 schedule adapter for XNYS/XNAS/XNSE/XBOM. The application bounds supported dates and exposes package/override versions. An override can add a weekend session or remove a session, with source URL and user-source status. Overrides are not independently fetched or verified. NASDAQ uses the library's NYSE alias; Indian exceptional weekend sessions require overrides.
6. Seven authenticated POST routes under `/api/data-adapters`, all using typed API envelopes and owner-scoped Processing Runs. Successful public responses are preserved in existing RawDocuments without rewriting originals. Result snapshots, source IDs, configuration, coverage and hashes are retained in the run. These inspection endpoints do not update accepted prices or holdings. The existing ingestion owner can select FMP/Massive/NSE through the one authoritative provider factory. Legacy list-returning history ingestion rejects partial results; dated inspection exposes partial points and gaps.

The pure market request/quote/history contracts were moved into `app/schemas/data_adapters.py` and re-exported from the existing `services/market_data/base.py` import path. Existing callers retain compatibility. Provider health and connectivity were reconciled with implemented capability and public OpenFIGI access.

## Request and storage bounds

The fixed-host transport uses urllib to avoid HTTPX INFO logs containing FMP query keys. It rejects redirects, environment proxies, unallowlisted hosts/ports, compressed responses and oversized/invalid JSON. Socket timeout is 15 seconds, response elapsed limit 25 seconds, body limit 5 MB and operation request budget 32. The consuming workflow has a 120-second deadline. Requests are not automatically retried. SSE parsing stops only on a matching response ID; truncated streams are errors. Authentication values are excluded from request provenance; successful credential echoes are rejected before preservation. No session headers are saved.

Quote inspection metadata treats source timestamps older than 20 minutes as stale and explains that the market may be closed. This is a display policy, not a claim about an exchange session or provider entitlement. Source timestamps and local observation time remain separate. History request dates are inclusive and must precede the current market-local date. Source publication time remains unknown unless supplied; download time is never backdated.

## Primary implementation references

* [FMP quote](https://site.financialmodelingprep.com/developer/docs/stable/quote), [profile](https://site.financialmodelingprep.com/developer/docs/stable/profile), [full history and adjustment FAQ](https://site.financialmodelingprep.com/developer/docs/stable/historical-price-eod-full).
* [Massive snapshot](https://massive.com/docs/rest/stocks/snapshots/single-ticker-snapshot), [aggregates](https://massive.com/docs/rest/stocks/aggregates/custom-bars), [splits](https://massive.com/docs/rest/stocks/corporate-actions/splits), [dividends](https://massive.com/docs/rest/stocks/corporate-actions/dividends).
* [Official NSE MCP](https://www.nseindia.in/nse-mcp), [MCP transport protocol](https://modelcontextprotocol.io/specification/2025-03-26/basic/transports).
* [OpenFIGI API](https://www.openfigi.com/api/documentation).
* [Calendar package 5.6.1](https://pypi.org/project/pandas_market_calendars/5.6.1/), [calendar source](https://github.com/rsheftel/pandas_market_calendars/blob/master/pandas_market_calendars/calendars/nse.py), [schedule/interruptions API](https://pandas-market-calendars.readthedocs.io/en/stable/usage.html).

Adapters are original implementation against these APIs. The calendar package is used as a pinned dependency under its MIT license; no upstream application source was copied. OpenBB was not added because the selected official endpoints already provide the requested capabilities without another platform dependency. Root owns dependency locks, notices, settings and route registration.

## Source samples and runtime distinction

The adjacent `nse-*-tools.json` and `nse-*-sample.json` files are exact bounded public responses retrieved during the authorized protocol check, not Mock Data. They contain no API keys/session headers. They document the tool schemas, bare-number dated-price behavior, EQ/T0 mixture, dividend prose and separate price/cache timestamps. Unit tests using these files do not make live calls; additional synthetic test payloads are labeled Mock Data.

Initialization, tools/list and selected public tool calls succeeded through the environment's permitted network route. A separate probe through the application's proxy-free transport failed on its first outbound request with sanitized `PROVIDER_UNAVAILABLE`; see `nse-adapter-compatibility.json`. Consequently full live execution through the production transport is **not verified in this environment**. FMP/Massive entitlements and live OpenFIGI responses were not exercised.

## Validation

Using the coordinator's Python 3.14.10 environment, baseline hashed dependencies and optional calendar 5.6.1:

```text
python -m pytest -q -p no:cacheprovider \
  backend/tests/adapters_market \
  backend/tests/test_provider_health.py \
  backend/tests/test_provider_connectivity.py \
  backend/tests/test_source_capabilities.py \
  backend/tests/test_schema_boundaries.py \
  backend/tests/test_market_data_market_context.py \
  backend/tests/test_market_ingestion_workflow.py \
  backend/tests/test_market_history_window.py \
  backend/tests/test_provider_transport_limits.py
```

135 tests passed after the final source-capability follow-up. Checks cover actual HTTP request construction/SSE parsing, secret exclusion, date/identity/currency/basis rejection, partial pagination, captured NSE mapping, real calendar early-close/DST behavior, duplicate source preservation, owner-isolated run visibility, cancellation, router authorization and typed envelopes. Calendar libraries emit NumPy timedelta deprecation warnings with the pinned baseline; tested schedules still pass. SQLite tests do not prove PostgreSQL concurrency, and local router tests do not replace root's combined registration/route-security checks.

## Core test image compatibility repair

November 18, 2026: hosted run `44226913614` exposed two test-environment assumptions: the core test image excludes optional calendar dependencies and does not copy the documentation directory. The repair starts from published commit `788855f319abcb82de597097b91c7147ed2ab32d` and changes only W3 tests, their captured fixtures and this receipt.

The four calendar tests now skip only when the `pandas-market-calendars` distribution is absent. Package imports and actual schedule checks still execute when it is installed, so broken installed dependencies are not treated as optional skips. The five captured JSON files consumed by the NSE tests are copied byte for byte into `backend/tests/adapters_market/fixtures`; the original public evidence remains here. The tests no longer depend on documentation being present in an image.

Verification:

* The installed optional profile runs all market adapter tests: **44 passed**, including all four calendar tests.
* A new Python 3.14.10 environment containing only the hashed core/test lock runs the same tests: **40 passed, 4 skipped**. All seven NSE tests pass. This check used a temporary tree containing only the backend application, market tests and their parent fixture file, with no `docs` directory.
* All five fixture copies were checked for byte equality with the preserved public responses. No provider calls, Dockerfile changes or test assertions were removed.

These checks establish the two Python test environments locally. The repaired hosted container run remains the coordinator's release check.
