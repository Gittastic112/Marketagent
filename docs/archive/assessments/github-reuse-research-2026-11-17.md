# Marketagent: Consolidated GitHub Research and Implementation Handoff

**Updated November 17, 2026, America/New_York. Version 2.**

**Coverage: 93 repositories, 60 with code/example inspection, 33 screened through documentation/tree/license material; two additional official service candidates.**

**Purpose:** a complete, portable Markdown file for planning and implementing selected Marketagent improvements. Includes all six user-supplied repositories, the full original survey, additional research, exact source references, integration contracts, 16 build tickets, acceptance cases and five copyable implementation prompts. No application changes have been made.

## Contents

1. [How to use this handoff](#how-to-use-this-handoff)
2. [Recommendation](#recommendation)
3. [What was checked](#what-was-checked)
4. [Missing capabilities found in the follow-up](#missing-capabilities-found-in-the-follow-up)
5. [The six repositories supplied by the user](#the-six-repositories-supplied-by-the-user)
6. [Recommended feature packages](#recommended-feature-packages)
7. [Detailed reuse notes](#detailed-reuse-notes)
8. [Additional technical findings from the new repositories](#additional-technical-findings-from-the-new-repositories)
9. [Adapter contracts and integration map](#adapter-contracts-and-integration-map)
10. [Implementation backlog](#implementation-backlog)
11. [A practical implementation sequence](#a-practical-implementation-sequence)
12. [Acceptance cases shared across packages](#acceptance-cases-shared-across-packages)
13. [Copyable implementation prompts](#copyable-implementation-prompts)
14. [Decisions to resolve during the selected build](#decisions-to-resolve-during-the-selected-build)
15. [Licensing under the user's personal-project scope](#licensing-under-the-users-personal-project-scope)
16. [Original repository inventory](#original-repository-inventory)
17. [Additional repository inventory](#additional-repository-inventory)
18. [Additional source references](#additional-source-references)
19. [Verification and completeness limits](#verification-and-completeness-limits)

## How to use this handoff

This is a standalone research and implementation brief for Marketagent. It retains the original repository survey and adds focused gap research, adapter specifications, repair dependencies, implementation tickets, and prompts that can be pasted into a coding session.

**Yes, implementation can be requested in this same chat.** A useful instruction is: “Implement MA-01, the EdgarTools adapter, in Marketagent using this handoff.” The work can include inspecting current source, implementing the adapter and its integration, adding meaningful tests, updating configuration/docs, and preparing a reviewable change. Checks that cannot be run must be identified. Access to a repository is not evidence that a new integration has been installed or tested.

Choose one bounded package at a time. This file describes possible work; it does not mean every dependency should be installed. The engineering recommendations should be reconciled with the actual repository instructions and current source when implementation begins. The reference commit in this report is an evidence snapshot, not an instruction to ignore subsequent fixes.

The most useful starting options are:

| Starting objective | First package | Reason |
|---|---|---|
| Improve financial inputs | MA-01: EdgarTools candidate adapter | Builds directly on existing SEC and reviewed-fact workflows |
| Improve Indian market coverage | MA-02: official NSE MCP adapter prototype | Newly identified official source; validate protocol and payloads before production integration |
| Improve daily research usability | MA-07: workbench and evidence viewer | Connects existing models, peer review and source documents |
| Add a substantial analytical feature | MA-06: Portfolio Lab | Uses validated returns to explore constrained allocations |
| Make a small visible improvement | MA-09: memo rendering/export alignment | Existing memo output can be presented more clearly, with saved-version semantics preserved |
## Recommendation

The strongest immediate application donor is **OpenStock** for market browsing and search interactions. **Wealthfolio** is the strongest additional application reference for reviewing portfolio imports. **Ghostfolio** is useful for portfolio rules and comparison design, although its Angular frontend makes direct porting more expensive.

For libraries, prioritize **PyPortfolioOpt**, **EdgarTools**, **Docling**, **TanStack Table**, selected **shadcn/ui** components, **React-PDF**, **pgvector**, **openapi-typescript**, and a bounded **DBOS** prototype. Use **bt** for portfolio rebalancing experiments. Add Promptfoo to evaluate AI changes against existing financial and evidence cases.

This ranking incorporates the user's clarification that Marketagent is a personal project. Copyleft is not treated as a reason to discard technically useful software. Integration fit, marginal capability, numerical correctness, dependency cost, and inspectability drive the ranking.
## What was checked

**The consolidated screen covers 93 unique external repositories: 60 with implementation or concrete code-example inspection and 33 with documentation, metadata, tree and/or license screening.** The first pass covered 71 repositories (39 Code and 32 Docs); the follow-up adds 22 (21 Code and one Docs). Two newly reviewed official services, NSE MCP and BSE Self Data Feed, are counted separately. Companion repositories such as pgvector-python and Langfuse's Python SDK count separately. The inventory below identifies the depth for every entry.

No external project was installed or executed. No Marketagent application changes, provider calls, database changes, trades, or deployments were made. These are source-informed recommendations, not completed integrations or independent certifications of financial correctness. Repository branches and package versions can move; pin the actual source chosen for implementation.

### Marketagent source baseline

Main was rechecked during this consolidation and remained unchanged. The source snapshot examined is [Gittastic112/Marketagent at 371b58c02cfd2b80429f28dbc13629165b5e392d](https://github.com/Gittastic112/Marketagent/tree/371b58c02cfd2b80429f28dbc13629165b5e392d).

Read material included root and frontend/backend AGENTS.md, README, docs/HANDOFF.md, current-state.md, architecture.md, relevant code-map entries, limitations.md, frontend/package.json, backend/requirements.txt, and implementation excerpts in:

1. [backend/app/core/config.py](https://github.com/Gittastic112/Marketagent/blob/371b58c02cfd2b80429f28dbc13629165b5e392d/backend/app/core/config.py)
2. [backend/app/providers/ai_provider.py](https://github.com/Gittastic112/Marketagent/blob/371b58c02cfd2b80429f28dbc13629165b5e392d/backend/app/providers/ai_provider.py)
3. [backend/app/services/evidence_search.py](https://github.com/Gittastic112/Marketagent/blob/371b58c02cfd2b80429f28dbc13629165b5e392d/backend/app/services/evidence_search.py)
4. [backend/app/services/portfolio_risk_return.py](https://github.com/Gittastic112/Marketagent/blob/371b58c02cfd2b80429f28dbc13629165b5e392d/backend/app/services/portfolio_risk_return.py)
5. [backend/app/workers/valuation_source_scheduler.py](https://github.com/Gittastic112/Marketagent/blob/371b58c02cfd2b80429f28dbc13629165b5e392d/backend/app/workers/valuation_source_scheduler.py)
6. [frontend/styles/foundation.css](https://github.com/Gittastic112/Marketagent/blob/371b58c02cfd2b80429f28dbc13629165b5e392d/frontend/styles/foundation.css)
7. [frontend/components/valuation/peer-set-view.tsx](https://github.com/Gittastic112/Marketagent/blob/371b58c02cfd2b80429f28dbc13629165b5e392d/frontend/components/valuation/peer-set-view.tsx)
8. [frontend/components/valuation/valuation-memo-panel.tsx](https://github.com/Gittastic112/Marketagent/blob/371b58c02cfd2b80429f28dbc13629165b5e392d/frontend/components/valuation/valuation-memo-panel.tsx)
9. [frontend/lib/api/valuation.ts](https://github.com/Gittastic112/Marketagent/blob/371b58c02cfd2b80429f28dbc13629165b5e392d/frontend/lib/api/valuation.ts)
10. [backend/app/schemas/valuation_outputs.py](https://github.com/Gittastic112/Marketagent/blob/371b58c02cfd2b80429f28dbc13629165b5e392d/backend/app/schemas/valuation_outputs.py)

The inspected manifests use Next.js 16.4.1, React 19.2.3, TypeScript, Tailwind 4, Recharts 2.15, FastAPI, SQLAlchemy, Alembic, PostgreSQL, pandas, HTTPX, pdfplumber, pypdfium2, openpyxl, and pydantic-settings. Source confirms existing configuration, provider, evidence search, financial review, and presentation boundaries.

Marketagent already has DCF and specialized models, scenario/reverse analysis, peer review, portfolio replay and returns, source provenance, run records, and explicit AI consent. New libraries should add capabilities through those boundaries. Installing a second DCF app, second portfolio ledger, or second authentication/database stack would create overlap.
## Missing capabilities found in the follow-up

### Official NSE access changes the India recommendation

[NSE's official MCP page](https://www.nseindia.in/nse-mcp) documents two public endpoints:

```text
https://mcp.nseindia.in/bhavcopy/cm/mcp
https://mcp.nseindia.in/cmmkt/mcp
```

The page describes informational, noncommercial access without registration or an API key. It documents five years of end-of-day history, at most three months per history call, corporate actions, symbol search, and intraday data delayed by approximately one to three minutes. Historical prices are unadjusted for splits/bonuses. A holiday price request can resolve to the preceding trading session. These are documented capabilities, not a successful live integration test.

**Recommendation:** investigate this official route before adopting an unofficial NSE website scraper. Begin with explicit historical-price, dated-quote and corporate-action tools. The documented capabilities do not establish comprehensive Indian financial statement or filing coverage.

Our proposed adapter should retain the requested date/window, actual returned trading date, original provider symbol, currency, price type and adjustment basis. It should disclose any previous-session substitution. Multi-call history retrieval needs a visible bounded request budget, deduplication at window boundaries and explicit partial-coverage results. A raw price series must not silently become a total-return series.

The [official MCP Python SDK](https://github.com/modelcontextprotocol/python-sdk) is MIT licensed. Its inspected current [client example](https://github.com/modelcontextprotocol/python-sdk/blob/main/docs_src/client_transports/tutorial002.py) uses `Client`, while current [transport documentation](https://github.com/modelcontextprotocol/python-sdk/blob/main/docs/client/transports.md) describes `httpx2`. Older tutorials use a different API. Pin a compatible release, use its corresponding documentation, and test the actual transport. The existing application's HTTPX test helpers do not automatically cover a different HTTP library.

For BSE corporate filings and announcements, [BSE Self Data Feed](https://marketdata.bseindia.com/) is an official route worth investigating. Registration, entitlement, dataset coverage, retention and payload specifications must be confirmed for the selected plan before coding against it. This report does not claim a registered feed or verified live response.

### Point-in-time macro data needs a vintage-aware extension

Marketagent already has [FredProvider](https://github.com/Gittastic112/Marketagent/blob/371b58c02cfd2b80429f28dbc13629165b5e392d/backend/app/providers/fred_provider.py). Its inspected observation request fetches the latest available values and does not set real-time or vintage parameters. The limitation ledger also records that complete vintage storage is absent.

The official [FRED real-time period documentation](https://fred.stlouisfed.org/docs/api/fred/realtime_period.html), [observations endpoint](https://fred.stlouisfed.org/docs/api/fred/series_observations.html), and [vintage-date endpoint](https://fred.stlouisfed.org/docs/api/fred/series_vintagedates.html) distinguish an observation's economic date from when its value was available. That matters whenever a historical scenario or backtest claims to use only information available at the time.

Use [mortada/fredapi](https://github.com/mortada/fredapi) as a behavioral reference, not an automatic transport replacement. Its inspected [fred.py](https://github.com/mortada/fredapi/blob/master/fredapi/fred.py) supports revision retrieval, but `get_series_as_of_date` filters eligible releases without collapsing them to one latest eligible revision per observation. Its direct `urlopen` helper also lacks the explicit request bounds used by Marketagent.

Our proposed implementation should extend the existing bounded provider, retain revision intervals, select the latest eligible release explicitly, preserve missing values, and keep original observations alongside revisions. A data point downloaded today can have an old publication date, but its local `observed_at` must remain today. Absence of a vintage must produce unavailable historical coverage rather than silently substituting today's revised value.

### Earnings transcripts need an availability contract

The inspected [FMP provider](https://github.com/Gittastic112/Marketagent/blob/371b58c02cfd2b80429f28dbc13629165b5e392d/backend/app/services/market_data/fmp.py) is a market-data placeholder that raises `PROVIDER_NOT_IMPLEMENTED`. A configured FMP key does not mean quotes or transcripts are implemented.

[FMP's latest-transcript documentation](https://site.financialmodelingprep.com/developer/docs/stable/latest-transcripts) says list ordering follows the call date, not when FMP makes a transcript available. Older calls can therefore appear later in the feed. A simple cursor that only takes calls newer than the last call date can miss records.

Build transcript intake as a research-document capability. Preserve call date, provider publication/availability time when supplied, local first-seen time, fiscal quarter/year, version, document hash, speaker labels and paragraph/segment locators. Use an overlapping bounded polling window plus stable-ID/hash deduplication. If actual historical availability is unknown, do not invent it from the call date.

Original transcript text can support cited summaries, management-guidance extraction and changes across quarters. Extracted claims remain candidates under the existing evidence and review system. Provider-generated summaries and original transcripts should carry different source types.

### Identity, corporate actions and calendars are separate capabilities

Ticker text is not a durable security identity. A useful mapping records issuer, listed security/share class, venue, provider symbol and validity interval. Marketagent's current `Company.cik` uniqueness and shared-issuer handling do not constitute a complete issuer/security master. [The limitation ledger](https://github.com/Gittastic112/Marketagent/blob/371b58c02cfd2b80429f28dbc13629165b5e392d/docs/limitations.md) explicitly leaves this area open.

An identifier mapping service should produce candidates and preserve ambiguity. It must not merge different share classes or NSE/BSE listings solely because names match. Corporate actions should be retained with their own identity, announcement/ex-date/payment dates where available, action type, terms and source revision. An action announcement and a reconstructed total-return series are different outputs.

Calendar support should identify venue, timezone, supported date range, special sessions and the version used. Both ordinary weekday assumptions and an unqualified fixed 252-day annualization can be misleading across markets. Library holiday tables need validation against the relevant exchange, including exceptional weekend sessions. Unsupported calendar dates should be explicit.

### Existing functionality and repair dependencies must be respected

The follow-up confirmed these existing foundations:

| Existing component | Implication for the new work |
|---|---|
| Source preservation and source-fact revisions | Add manifests and adapter metadata to the existing provenance model |
| Lakh/crore/thousand/million/billion conversions | Reuse financial-unit logic; do not add a generic units library to solve a problem already covered |
| Typed market quote/history results | Map providers into existing price type, adjustment and timestamp fields |
| Explicit provider selection | Do not add an invisible provider fallback chain |
| Existing financial, transport and no-network tests | Extend relevant tests and fixtures rather than claim a test foundation is absent |
| Memo panel and sensitivity matrices | Improve current rendering and behavior before adding a second editor or chart engine |

The reviewed limitation ledger identifies unresolved save/export, memo/evidence-link and return-method alignment issues. These are dependencies of the proposed features. A polished editor that loses in-flight edits, an export of the wrong saved version, or an optimizer fed inconsistent returns would remain incorrect.
## The six repositories supplied by the user

| Repository | Assessment | Most useful part | Main technical consideration |
|---|---|---|---|
| [OpenStock](https://github.com/Open-Dev-Society/OpenStock) | Best immediate application donor | Ticker search, list interactions, market panels, compact source timing | Adapt its React code to existing APIs; do not import MongoDB/auth/jobs wholesale |
| [PyPortfolioOpt](https://github.com/PyPortfolio/PyPortfolioOpt) | Best direct analytical extension | Constrained allocations, covariance estimation, risk allocation, reviewed views | A valuation gap is not automatically an annual expected return |
| [Ghostfolio](https://github.com/ghostfolio/ghostfolio) | Useful selective domain/product reference | Portfolio rules, benchmark presentation, account/holding drilldowns | Angular/Nest differs from Next/FastAPI; existing capabilities overlap |
| [backtesting.py](https://github.com/kernc/backtesting.py) | Good optional research feature | Interactive single-instrument strategy sandbox | Portfolio allocation/rebalancing has a more direct fit in PyPortfolioOpt and bt |
| [Eiten](https://github.com/tradytics/eiten) | Do not use as a calculation foundation | Educational portfolio-method ideas | Inspected cumulative performance code adds simple returns instead of compounding |
| [Financial_freedom](https://github.com/codeman008/Financial_freedom) | Not an application code donor | Reading/resource collection | Inspected tree contains README and book PDFs, not a reusable app |

### Eiten: concrete reason for the negative verdict

In [backtester.py](https://github.com/tradytics/eiten/blob/master/backtester.py), the return helper produces ordinary percentage changes and the backtest uses numpy.cumsum on those returns for its cumulative-return chart. That is not compounded portfolio growth. For example, +10% followed by -10% is a 1% loss, not a zero return.

The inspected data_loader.py also uses unadjusted closes after dropping Adj Close and filters series by length instead of establishing a robust date-aligned total-return contract. requirements.txt contains old package pins. These are technical reasons to prefer alternatives, independent of its GPL license.
## Recommended feature packages

These are proposed additions. They are not claims that the upstream applications already provide the complete Marketagent workflow.

| Order | Feature | Repositories to use | Useful first result | Relative effort |
|---|---|---|---|---|
| 1 | Research workbench | OpenStock, shadcn/ui, Geist, TanStack Table, react-resizable-panels | Search a company, compare peers and inspect assumptions in one compact workspace | Medium |
| 2 | Inspectable source evidence | React-PDF, EdgarTools; Docling or Camelot where required | Clicking a factual input opens the exact document/page with period and units visible | Medium to high |
| 3 | Portfolio evidence import review | Wealthfolio patterns plus current Marketagent evidence-import services | Review price/FX rows, retain source identity, fix errors and apply an exact-hash preview; transaction import is separate scope | Medium |
| 4 | Portfolio allocation laboratory | PyPortfolioOpt | Compare hypothetical constrained weights against current holdings, with diagnostics | Medium |
| 5 | Better research retrieval | pgvector and pgvector-python | Semantic plus lexical filing search retaining original evidence and date filters | Medium |
| 6 | Reliable processing | DBOS on one workflow | Resume interrupted refresh/extraction steps with visible attempts and bounded retries | Medium to high |
| 7 | Configuration and contract consistency | Existing pydantic-settings, openapi-typescript, Promptfoo | Versioned run presets, generated API types and comparable evaluation runs | Low to medium |
| 8 | Research simulation and reporting | bt, QuantStats; backtesting.py/vectorbt for specific research needs | Compare rebalancing policies and export reproducible performance reports | Medium to high |

Effort is a relative engineering judgment, not a time estimate. Data identity, return definitions, source review, and existing open save/export issues can dominate the work.
## Detailed reuse notes

### 1. OpenStock: port a few useful frontend modules

[Repository](https://github.com/Open-Dev-Society/OpenStock) · [License](https://github.com/Open-Dev-Society/OpenStock/blob/main/LICENSE)

Its Next.js/React/Tailwind/shadcn frontend is compatible in direction with Marketagent. The most useful inspected source is [SearchCommand.tsx](https://github.com/Open-Dev-Society/OpenStock/blob/main/components/SearchCommand.tsx), [watchlist-lists.ts](https://github.com/Open-Dev-Society/OpenStock/blob/main/lib/watchlist-lists.ts), [TradingViewWidget.tsx](https://github.com/Open-Dev-Society/OpenStock/blob/main/components/TradingViewWidget.tsx), and [DataFreshness.tsx](https://github.com/Open-Dev-Society/OpenStock/blob/main/components/DataFreshness.tsx).

Port the search and list interactions, including adding a symbol to a named research list. Use existing Marketagent transport, identity resolution, and stale-response protection. The chart component offers useful fullscreen lifecycle behavior. Persistent ticker tabs are another promising feature, but their implementation was not deeply inspected in this review.

There is a source-level caveat: DataFreshness renders its live label from the realtime configuration flag without checking the supplied trade timestamp's age in that branch. Marketagent should retain freshness derived from source timestamps and provider state.

[MARKET_SUPPORT.md](https://github.com/Open-Dev-Society/OpenStock/blob/main/MARKET_SUPPORT.md) makes the distinction between globally searchable symbols and actually available quotes/charts clear. India support in the documented free setup includes BSE end-of-day charting and no Finnhub free quote access. A UI port does not create a reliable NSE price or company-fundamentals feed.

### 2. Wealthfolio: reuse the import review interaction

[Repository](https://github.com/wealthfolio/wealthfolio) · [License](https://github.com/wealthfolio/wealthfolio/blob/main/LICENSE)

The inspected [import-review-grid.tsx](https://github.com/wealthfolio/wealthfolio/blob/main/apps/frontend/src/pages/activity/import/components/import-review-grid.tsx) handles valid, warning, error, skipped and duplicate record states. Its props include field updates, row selection, bulk currency/account changes, skipping, and import profile configuration.

This is relevant to consolidating portfolio information. The first bounded integration should improve Marketagent's existing price/FX evidence importer with row statuses, source identity, duplicate/error navigation and exact-hash preview/apply. A broader broker transaction importer with column/account mapping is a separate future feature and must use the portfolio ledger/replay contracts.

Port the component's interaction/state ideas and the supporting validation behavior as a bounded feature. It depends on Wealthfolio's UI package, translation system, asset semantics and adapters, so it is not a single file that can be dropped into Marketagent unchanged. Current Marketagent evidence rules determine which price/FX rows are accepted. Transaction imports would additionally require ledger/replay validation.

### 3. Ghostfolio: select missing risk-rule and comparison behavior

[Repository](https://github.com/ghostfolio/ghostfolio) · [License](https://github.com/ghostfolio/ghostfolio/blob/main/LICENSE)

Inspected files include [rules.service.ts](https://github.com/ghostfolio/ghostfolio/blob/main/apps/api/src/app/portfolio/rules.service.ts), the [benchmark comparator](https://github.com/ghostfolio/ghostfolio/blob/main/apps/client/src/app/components/benchmark-comparator/benchmark-comparator.component.ts), and [home watchlist](https://github.com/ghostfolio/ghostfolio/blob/main/apps/client/src/app/components/home-watchlist/home-watchlist.component.ts).

The best potential addition is a portfolio review surface that turns specific risk rules into clear findings and drilldowns. It is worth studying how rules return standardized results and how benchmark comparisons present their basis.

The frontend is Angular, and the backend is NestJS with Prisma. For Marketagent, adapt small domain logic and recreate the rendering in React. Its entire returns calculator was not audited here; do not treat this review as support for replacing Marketagent's TWR/MWR calculations.

### 4. PyPortfolioOpt: a constrained allocation laboratory

[Repository](https://github.com/PyPortfolio/PyPortfolioOpt) · [License](https://github.com/PyPortfolio/PyPortfolioOpt/blob/main/LICENSE)

Implementation examined: [black_litterman.py](https://github.com/PyPortfolio/PyPortfolioOpt/blob/main/pypfopt/black_litterman.py), [risk_models.py](https://github.com/PyPortfolio/PyPortfolioOpt/blob/main/pypfopt/risk_models.py), [efficient_frontier.py](https://github.com/PyPortfolio/PyPortfolioOpt/blob/main/pypfopt/efficient_frontier/efficient_frontier.py), and corresponding efficient-frontier tests.

A first feature should accept a date-aligned return matrix and explicit concentration constraints, then compare current holdings with hypothetical minimum-volatility or risk-diversified weights. Show excluded assets, estimation window, covariance method, input gaps and sensitivity.

Later, Black-Litterman can combine prior returns with reviewed views and their uncertainty. A DCF's price-to-value gap should not be inserted directly as an expected annual return. The horizon, distributions/dividends, dilution and convergence assumptions need to be explicit.

Keep proposed weights separate from actual holdings and use the existing deterministic backend to calculate and validate outputs.

### 5. EdgarTools and Docling: improve ingestion without bypassing review

[EdgarTools](https://github.com/dgunning/edgartools) supplies SEC filing parsing and period-aware financial APIs. Its inspected [financials.py](https://github.com/dgunning/edgartools/blob/main/edgar/financials.py) explicitly handles period identities, instant/duration facts, quarter and year-to-date distinctions.

[Docling](https://github.com/docling-project/docling) is a broader document conversion candidate. The inspected [document_converter.py](https://github.com/docling-project/docling/blob/main/docling/document_converter.py) exposes configurable pipelines for documents, including PDF and XBRL. Its structured outputs and OCR support are relevant to scanned reports and Indian filings.

Use a narrow adapter that emits original source IDs, document hash, page/section location, filing/publication date, fiscal period, units, currency, dimensions and extraction method. Extracted rows remain candidates.

Marketagent's current annual-only promotion boundary should remain until its period contract supports quarters/YTD correctly. Better parsing alone does not authorize treating every extracted period as a reviewed annual input.

### 6. Camelot and Marker: credible alternatives worth a targeted comparison

[Camelot](https://github.com/camelot-dev/camelot) is a focused table-extraction option. [camelot/parsers/ml.py](https://github.com/camelot-dev/camelot/blob/master/camelot/parsers/ml.py) separates inferred table structure from cell text. This is useful for inspectability, but incorrect cell association is still possible. Current docs describe optional OCR/ML functionality; benchmark the actual selected release and inputs.

[Marker](https://github.com/datalab-to/marker) offers local document conversion and OCR modes. Current code is Apache 2.0; its README separately describes modified OpenRAIL terms for model weights. Do not treat the code license as covering every model dependency.

Run a small real-filing comparison before selecting a heavier parser: difficult tables, page continuations, negative amounts, units in headings, consolidated/standalone statements, scans and mixed layouts. Use the existing parser where it already works. Do not install every extraction framework.

### 7. Geist, shadcn, TanStack and resizable panels: one coherent visual system

[Geist fonts](https://github.com/vercel/geist-font), [shadcn/ui](https://github.com/shadcn-ui/ui), [TanStack Table](https://github.com/TanStack/table), and [react-resizable-panels](https://github.com/bvaughn/react-resizable-panels) form a strong foundation for the requested minimal style.

Use restrained neutral surfaces, modest borders, compact spacing, tabular financial numerals, and semantic colors only where they communicate changes or problems. For a company workspace, put navigation/research lists on the left, the model or peer table in the center, and original evidence on the right. Allow the evidence pane to grow.

The inspected TanStack [sticky-column example](https://github.com/TanStack/table/blob/main/examples/react/column-pinning-sticky/src/main.tsx) is useful for wide peer tables. Its spreadsheet example is explicitly experimental. Its current source has moved to v9; avoid mixing old v8 examples into a new integration.

[Current shadcn AI Elements](https://ui.shadcn.com/docs/ai-elements) include citations, sources and tool status compositions. The [old Vercel AI Elements README](https://github.com/vercel/ai-elements/blob/main/README.md) announces CLI deprecation at the end of November 2026. Use the current successor.

Marketagent uses Recharts 2.15; the inspected current shadcn chart package uses Recharts 3.8. Adapt styling or upgrade deliberately. This research does not imply that the newest wrapper can be pasted into the existing project unchanged.

### 8. React Data Grid and React-PDF: editing plus evidence

[React Data Grid](https://github.com/Comcast/react-data-grid) is the preferred editing prototype for a modest financial model. The inspected [AllFeatures.tsx](https://github.com/Comcast/react-data-grid/blob/main/website/routes/AllFeatures.tsx) demonstrates editing-related interaction. Its current package peer requirement matches React 19.2, although the inspected version is a beta; pin the chosen build.

Use it to paste forecast rows, edit assumptions and compare scenarios. Add explicit financial parsing for percentages, parenthesized negatives, currencies, thousand separators, units and blanks. Do not execute financial formulas in the frontend just because a grid can display them.

[React-PDF](https://github.com/wojtekmaj/react-pdf) can show the original filing in an evidence pane. The inspected [Page.tsx](https://github.com/wojtekmaj/react-pdf/blob/main/packages/react-pdf/src/Page.tsx) provides text/annotation layers and rendering callbacks. Exact highlighting still needs reliable page/span or coordinate locators from ingestion.

### 9. OpenBB, FinanceDatabase and FinanceToolkit: selective financial capability

The original [OpenBB-finance/OpenBB](https://github.com/OpenBB-finance/OpenBB) URL now resolves to [openbq-org/OpenBB](https://github.com/openbq-org/OpenBB), the same GitHub repository ID 323048702. The current develop source's [license](https://github.com/openbq-org/OpenBB/blob/fac2bd450fac5e0b69ca33f11c931f8b1b0b79fa/LICENSE) is Apache 2.0. Historical releases should be checked separately.

Its [fetcher abstraction](https://github.com/openbq-org/OpenBB/blob/develop/openbb_platform/core/openbb_core/provider/abstract/fetcher.py) separates query transformation, extraction and output transformation. Use selected adapters for a missing dataset such as transcripts, estimates or economic series. Keep Marketagent's authoritative provider factory and contracts.

[FinanceDatabase](https://github.com/JerBouma/FinanceDatabase) is useful for discovering candidate peers. Its inspected [equities controller](https://github.com/JerBouma/FinanceDatabase/blob/main/financedatabase/equities/equities_controller.py) filters listing attributes and excludes delisted securities by default. It should not supply a historical backtest universe.

[FinanceToolkit](https://github.com/JerBouma/FinanceToolkit) has a current MIT license and useful financial ratios and diagnostics. Select individual calculations and reconcile their definitions with Marketagent's periods, units and accounting policy. A matching formula name does not guarantee the same economic definition.

### 10. bt, backtesting.py, vectorbt, skfolio and QuantStats: choose by research task

[bt](https://github.com/pmorissette/bt) is the first choice for portfolio rebalancing experiments. Its inspected [algos.py](https://github.com/pmorissette/bt/blob/master/bt/algos.py) includes date-indexed target weights, monthly schedules and rebalance logic. Use a separate simulated ledger with explicit costs and information cutoffs.

[backtesting.py](https://github.com/kernc/backtesting.py) is a good personal-project addition for individual strategy experiments. [vectorbt](https://github.com/polakowo/vectorbt) becomes more attractive under the user's personal-use clarification for larger parameter sweeps. Its current license includes the Commons Clause; that is a scope note, not a reason to discard private experimentation.

[skfolio](https://github.com/skfolio/skfolio) is compelling when repeated out-of-sample evaluation becomes central. The inspected [walk-forward splitter](https://github.com/skfolio/skfolio/blob/main/src/skfolio/model_selection/_walk_forward.py) offers sequential train/test windows and a purge gap. Use it instead of accumulating overlapping optimizer frameworks without a division of responsibility.

[QuantStats](https://github.com/ranaroussi/quantstats) is useful for HTML reports. Its inspected [reports.py](https://github.com/ranaroussi/quantstats/blob/main/quantstats/reports.py) accepts return and benchmark series plus reporting assumptions. Feed it validated Marketagent returns; align currencies, total-return definitions, dates, cash flows and annualization before comparing metrics.

None of these supplies complete point-in-time fundamentals, delisted companies, adjusted prices or data rights automatically.

### 11. pgvector: extend the search that already exists

[pgvector](https://github.com/pgvector/pgvector) and its [Python adapter](https://github.com/pgvector/pgvector-python) fit the existing database. The adapter's inspected [RRF example](https://github.com/pgvector/pgvector-python/blob/master/examples/hybrid_search/rrf.py) combines keyword and semantic results.

Marketagent already implements PostgreSQL full-text search. Add semantic matching for questions whose wording differs from the filing. Preserve issuer, owner, document version, availability date and source-type filters in both retrieval branches.

Embedding similarity should affect retrieval rank, not certify a financial fact. A source excerpt still needs exact provenance. Begin with a small labeled retrieval set, and choose exact versus approximate indexing based on measured requirements.

### 12. DBOS: make one existing background workflow recoverable

[DBOS Python](https://github.com/dbos-inc/dbos-transact-py) supplies database-backed workflows, steps and queues. Inspected source includes [_queue.py](https://github.com/dbos-inc/dbos-transact-py/blob/main/dbos/_queue.py) and [workflow-management tests](https://github.com/dbos-inc/dbos-transact-py/blob/main/tests/test_workflow_management.py).

A first prototype could split a filing refresh into fetch, preserve, parse, validate and record-result steps. Expose which step failed and allow bounded recovery. Retain current Processing Runs as the application record, and link execution identifiers rather than creating a competing history.

Retry policy is a product decision. Do not introduce automatic unbounded backfills or repeated model spending. A durable workflow cannot guarantee a remote provider will never be called twice; deduplication and external side-effect handling remain necessary.

### 13. Configuration: extend what is already installed

Marketagent's [Settings class](https://github.com/Gittastic112/Marketagent/blob/371b58c02cfd2b80429f28dbc13629165b5e392d/backend/app/core/config.py) already uses pydantic-settings. No second settings framework is needed.

The useful feature is a versioned run preset that records:

1. Task and as-of date.
2. Permitted source/providers and freshness bounds.
3. Model/provider identity and prompt version.
4. Timeout, retry and cost limits.
5. Retrieval settings and source filters.
6. Required evidence and validation rules.
7. Input snapshot/hash and the existing permission receipt.
8. Actual provider/model used, including any explicitly allowed fallback.

Use backend validation for these presets. Frontend controls should expose meaningful choices, not every internal engine parameter. Secrets stay in the existing server configuration.

[LiteLLM](https://github.com/BerriAI/litellm) becomes useful when provider diversity creates actual duplication. Keep it behind the current provider boundary. [Langfuse](https://github.com/langfuse/langfuse) is optional for cost, timing and trace inspection; its SDK can be used without adopting its full application. Neither replaces financial review receipts.

### 14. openapi-typescript, Promptfoo and Pandera: reduce preventable failures

[openapi-typescript](https://github.com/openapi-ts/openapi-typescript) can generate TypeScript declarations from FastAPI's OpenAPI schema. Its inspected [generator entry point](https://github.com/openapi-ts/openapi-typescript/blob/main/packages/openapi-typescript/src/index.ts) handles validation/bundling and schema transformation. Generate types while retaining Marketagent's existing signed/authenticated transport and response envelope. Generated types are not runtime validation.

[Promptfoo](https://github.com/promptfoo/promptfoo) can compare model and prompt changes through its inspected [Python provider example](https://github.com/promptfoo/promptfoo/blob/main/examples/provider-python/provider.py). Reuse existing fixtures for absent facts, invalid citations, contradictory sources, future-dated data, missing units and provider failure. Deterministic assertions should check arithmetic and evidence; a model judge can assess prose separately.

[Pandera](https://github.com/unionai-oss/pandera) can validate dataframe rows and relationships, using [checks.py](https://github.com/unionai-oss/pandera/blob/main/pandera/api/checks.py). It is useful where table-level constraints exceed current schema validation. Negative income/cash flow must remain allowed; financial checks need domain-specific definitions.
## Additional technical findings from the new repositories

### Indian filing discovery and statement normalization

[NseIndiaApi](https://github.com/BennyThadikaran/NseIndiaApi/blob/main/src/nse/NSE.py) exposes filing metadata with period, audit/consolidation flags and optional XBRL links. Its `financial_results()` is not a table of revenue/EPS values. Its separate `results_comparison()` documents monetary amounts in rupees lakhs. The [announcement sample](https://github.com/BennyThadikaran/NseIndiaApi/blob/main/src/samples/announcements.json) contains ISIN, attachment references, submission-related dates and `exchdisstime`.

[BseIndiaApi](https://github.com/BennyThadikaran/BseIndiaApi/blob/main/src/bse/BSE.py) includes paginated announcements and total counts. Its [sample](https://github.com/BennyThadikaran/BseIndiaApi/blob/main/src/samples/announcements.json) distinguishes `News_submission_dt` and `DissemDT`; statement snapshots include unit/period information. This is useful reference code for adapters, although website-backed access still depends on endpoint stability and applicable data access terms. [jugaad-data's historical client](https://github.com/jugaad-py/jugaad-data/blob/master/jugaad_data/nse/history.py) depends on NSE website-session cookies, making it a weaker default than the documented official MCP route.

Proposed mapping: preserve original keys and values in provenance, then map submission, dissemination, period end and ingestion into separate fields. If a source timestamp lacks an offset, retain the original string and record the exchange-timezone interpretation explicitly. Reuse Marketagent's unit converter for lakh/crore transformations. Do not confuse a metadata-discovery API with verified financial extraction, or quarterly results with reviewed annual inputs.

### Security identity: OpenFIGI and Massive

[OpenFIGI's official API](https://www.openfigi.com/api/documentation) returns listing/composite/share-class mappings and supports exchange filtering. It can return several candidates. Unlisted equities are excluded by default unless requested, which matters for historical holdings. The [Python example](https://github.com/OpenFIGI/api-examples/blob/main/python/example.py) is a small request example, not a complete production adapter.

Use a local identity record, explicit ambiguity review, validity intervals, and provider aliases. Do not choose the first mapping result or claim that a current mapping is a historical security master. A historical as-of mapping capability was not verified in this research.

[Massive's reference client](https://github.com/massive-com/client-python/blob/master/massive/rest/reference.py) exposes ticker/reference operations and corporate actions. The [dividend model](https://github.com/massive-com/client-python/blob/master/massive/rest/models/dividends.py) preserves declaration, ex-dividend, record and payment dates; the [split model](https://github.com/massive-com/client-python/blob/master/massive/rest/models/splits.py) preserves execution date and ratio. Its `get_ticker_details(date=...)` documentation refers to period-of-report timing for some SEC information. That parameter alone is not proof that every returned field was available to investors by the requested date.

Use the SDK if it fills a specific entitled reference/action gap. Preserve downloaded snapshots and observed times. Announcement date, effective date, and arrival in a provider feed should remain separate. A split should change share quantity and per-share basis consistently; dividend cash accounting must not duplicate dividends already included in a total-return series.

### Calendar limitations are visible in the implementation

The inspected [pandas_market_calendars NSE source](https://github.com/rsheftel/pandas_market_calendars/blob/master/pandas_market_calendars/calendars/nse.py) documents coverage from 1996 through 2026. It states that dates outside coverage continue with regular hours, and that weekend Muhurat sessions such as 2023-11-12 cannot be represented by its Monday-to-Friday weekmask. Weekday special sessions and interruptions have dedicated support.

The [exchange_calendars XBOM implementation](https://github.com/gerrymanoim/exchange_calendars/blob/master/exchange_calendars/exchange_calendar_xbom.py) contains holiday entries through 2026 and special Saturday handling, while its class documentation refers to holidays through 2025. This requires version-specific checking rather than relying on the project description.

Implement one application calendar interface with coverage validation and exchange-announcement overrides. Pin both library and override versions in research manifests. Evaluate an exceptional weekend session, US early close, daylight-saving transition, year outside supported coverage and local-date/UTC boundary. A returned weekday schedule is not exchange confirmation.

### EarningsCall: useful structured transcript evidence

[EarningsCall's transcript model](https://github.com/EarningsCall/earningscall-python/blob/master/earningscall/transcript.py) includes speakers, prepared remarks/Q&A and word timing structures. Its [event model](https://github.com/EarningsCall/earningscall-python/blob/master/earningscall/event.py) carries fiscal year/quarter and conference date. Its [API implementation](https://github.com/EarningsCall/earningscall-python/blob/master/earningscall/api.py) handles retryable failures and `Retry-After` behavior.

Wrap the selected capabilities with Marketagent's own call budget and source contract. Availability of speaker/audio detail depends on the selected data access. Record the provider API version explicitly. Conference date is not a transcript-publication timestamp; if publication timing is absent, preserve first-observed time and unknown historical availability.

Potential features: reviewed guidance changes, linked quotes from prepared remarks versus Q&A, speaker-aware search, and side-by-side comparison with an earlier call. Audio-linked citations require the relevant entitled payload and preserved timestamps. Avoid adding generic sentiment scoring unless it answers a specific research question with an evaluation set.

### HTTP fixtures and replay

[RESPX's router](https://github.com/lundberg/respx/blob/master/respx/router.py) can assert that requests are mocked and expected routes are called. Use it when it simplifies new HTTPX adapter tests; existing no-network tests remain useful. It is not a universal network blocker for urllib, HTTPX2 or arbitrary SDK clients.

[VCR.py's HTTPX stubs](https://github.com/kevin1024/vcrpy/blob/master/vcr/stubs/httpx_stubs.py) currently accept HTTPX or HTTPX2 module paths; [cassette handling](https://github.com/kevin1024/vcrpy/blob/master/vcr/cassette.py) supports recording/replay. Test the exact installed version and streaming transport before relying on it. Normal test runs should replay fixed responses with recording disabled. Remove credentials, private content and account identifiers before retaining recordings. A replayed provider response is a fixture, not a financial correctness oracle.

### Data engines and larger benchmark corpora

[DuckDB](https://github.com/duckdb/duckdb) and its [Python Parquet tests](https://github.com/duckdb/duckdb-python/blob/main/tests/fast/api/test_read_parquet.py) suggest an optional local analytical engine over fixed exports. A first experiment should compare one real peer-screen or return-matrix workload against current pandas/PostgreSQL behavior. Select exact file hashes rather than a mutable directory glob.

[Polars' Parquet implementation](https://github.com/pola-rs/polars/blob/main/py-polars/src/polars/io/parquet/functions.py) supplies lazy scanning and schema controls. It is a candidate for a measured large transformation bottleneck. Explicitly fix decimal/float conversion, null policy, sorting, date alignment and timezone handling across pandas interfaces. Do not convert all tables to a second dataframe representation by default.

[DVC's reproduction implementation](https://github.com/treeverse/dvc/blob/main/dvc/repo/reproduce.py) is relevant when permitted parser/evaluation datasets outgrow ordinary fixtures. Use it for offline benchmark management if needed. DVC metadata does not preserve missing underlying objects or replace application source/review storage. The current repository is `treeverse/dvc`; the former organization name should not be counted as another project.

[Pint's currency documentation](https://github.com/hgrecco/pint/blob/master/docs/advanced/currencies.rst) distinguishes variable exchange-rate relationships from fixed physical conversions. Marketagent already handles financial scales. Pint becomes more useful if future models include energy, mass, capacity or other operating units; it does not supply dated FX rates or company accounting definitions.

### Memo presentation, editing and analytical UI

The current [memo panel](https://github.com/Gittastic112/Marketagent/blob/371b58c02cfd2b80429f28dbc13629165b5e392d/frontend/components/valuation/valuation-memo-panel.tsx) displays `memo_markdown` as preserved whitespace and exports `.txt`. [react-markdown](https://github.com/remarkjs/react-markdown/blob/main/lib/index.js) is a direct presentation improvement, with a separately verified GFM plugin required for tables. Keep raw HTML disabled and use a deliberate URL policy. Resolve citation IDs against authorized persisted evidence rather than treating any generated link as valid. Keep review state, saved basis and generation metadata outside the generated memo body.

The inspected react-markdown package accepts React 18 and newer. [Perspective's React viewer](https://github.com/perspective-dev/perspective/blob/master/packages/react/src/viewer.tsx) supports saved pivot/view configuration and callbacks, but its consumer owns table/client lifecycle. [ECharts' heatmap implementation](https://github.com/apache/echarts/blob/master/src/chart/heatmap/HeatmapView.ts) is useful for a future advanced chart requirement. Marketagent's current [sensitivity panel](https://github.com/Gittastic112/Marketagent/blob/371b58c02cfd2b80429f28dbc13629165b5e392d/frontend/components/valuation/sensitivity-tables-panel.tsx) already contains an accessible colored matrix, saved basis, units, calculation time and unavailable-cell reasons. Preserve those capabilities.

[Lexical's change plugin](https://github.com/meta/lexical/blob/main/packages/lexical-react/src/LexicalOnChangePlugin.ts) and [Markdown utilities](https://github.com/meta/lexical/blob/main/packages/lexical-markdown/src/index.ts) are relevant to structured authoring. [Tiptap's React editor lifecycle](https://github.com/ueberdosis/tiptap/blob/main/packages/react/src/useEditor.ts) handles SSR-related integration; its inspected package explicitly supports React 19. Choose one only after defining generated original, user-edited derivative, unsaved draft and exported version. The inspected open-source license does not establish terms for separate hosted/commercial editor services.

For a future Perspective trial, use a representative large dataset and measure grouping correctness, null/currency/date handling, saved view restoration, cleanup and bundle cost. For ECharts, demonstrate a required interaction absent from current charts and retain a readable table alternative. For an editor, test citation round trips, unsaved recovery, background refresh and exact-version export.

### Current import scope and resource limits

The current [portfolio evidence importer](https://github.com/Gittastic112/Marketagent/blob/371b58c02cfd2b80429f28dbc13629165b5e392d/frontend/components/portfolio/portfolio-evidence-importer.tsx) imports source-labeled **price and FX observations**. It is not a generic broker transaction importer. Its current UI states 2 MiB/5,000-row limits, duplicate skipping and conflict-blocked apply. It previews server-side and applies the exact content hash. Wealthfolio's review interactions should first improve this flow. A broker transaction importer is a separately scoped future feature that must integrate with portfolio replay.

The inspected [PDF job wrapper](https://github.com/Gittastic112/Marketagent/blob/371b58c02cfd2b80429f28dbc13629165b5e392d/backend/app/services/pdf_jobs.py) limits input to 40 MiB, output to 16 MiB, memory to 512 MiB, CPU to eight seconds, wall time to twelve seconds and concurrency to two slots. These worker limits are distinct from narrower upload/page limits in individual app workflows. Docling or model-based OCR may require a separate measured extraction profile.

Existing [PDF candidates](https://github.com/Gittastic112/Marketagent/blob/371b58c02cfd2b80429f28dbc13629165b5e392d/backend/app/services/pdf_financial_extraction.py) already hold page/table/row/column locations and warnings. Add coordinate origin, page dimensions, rotation and text-span metadata only where available. Verify that clicking a candidate highlights the original value rather than a shifted cell. Confidence describes extraction behavior, not reviewed financial truth.
## Adapter contracts and integration map

### Reuse the boundaries that already exist

All paths below were observed in the inspected repository. A path identifies an integration owner; it does not imply every file was exhaustively reviewed.

| Capability | Existing owner or contract | Proposed integration |
|---|---|---|
| Filing discovery | `backend/app/providers/filings/base.py`, `filings/sec_edgar.py`, `services/filing_acquisition.py` | Preserve `FilingProvider.preview_filings`; add parsing/normalization behind existing acquisition and candidate review |
| SEC statement extraction | `services/sec_xbrl_extractor.py`, `sec_xbrl_ingestion.py`, `financial_extraction.py` | Map EdgarTools output into existing candidate/provenance contracts |
| Period and statement identity | `financial_period_basis.py`, `financial_period_context.py`, `financial_statement_identity.py` | Preserve instant/duration, annual/YTD/quarter, entity and consolidation distinctions |
| Market prices | `services/market_data/base.py`, `factory.py`, `persistence.py`, `providers/market_data/yfinance_provider.py` | Add explicitly selectable adapters and retain normalized quote/history results |
| FMP | `services/market_data/fmp.py` | Replace the placeholder only for the selected market-data capability; keep transcripts a distinct research-document concern |
| Macroeconomic observations | `providers/fred_provider.py`, `services/macro_ingestion.py` | Add bounded vintage-aware retrieval and revision selection |
| Documents and extraction | `services/pdf_jobs.py`, `pdf_financial_extraction.py`, `pdf_page_rendering.py`, `workers/pdf_parse_worker.py` | Add a measured parser profile that emits candidates and reliable page locations |
| Original evidence and revisions | `source_preservation.py`, `source_fact_history.py`, `evidence_integrity.py` | Retain immutable originals and revision provenance; link all new outputs |
| Units | `valuation_input_units.py` | Normalize only with known scale/currency and retain transformation evidence |
| Portfolio analytics | `portfolio_risk_return.py`, `portfolio_performance.py`, `portfolio_replay.py` | Build allocations/simulations alongside the actual ledger using explicitly defined return inputs |
| Search | `evidence_search.py` | Extend existing PostgreSQL full-text search with optional semantic retrieval |
| AI execution and consent | `ai_provider.py`, `services/ai_contract.py`, `ai_consent.py`, `processing_runs.py` | Preserve provider/action disclosure, request receipts and run identity |
| Frontend API contract | `frontend/lib/api/transport.ts`, `contract.ts`, domain API modules | Generate types without replacing authenticated transport or response reconciliation |
| Valuation frontend | `frontend/components/valuation/` | Extend peer, source, scenario and memo surfaces with compatible components |
| Portfolio evidence imports | `frontend/components/portfolio/portfolio-evidence-importer.tsx`, `services/portfolio_evidence_import.py` | Improve price/FX evidence review while retaining exact preview-hash and apply rules; transaction imports require separate scope |

Repository source index: [code map](https://github.com/Gittastic112/Marketagent/blob/371b58c02cfd2b80429f28dbc13629165b5e392d/docs/code-map.md).

### Minimum normalized result contract

The current `MarketDataRequest` contains identity fields, not an as-of date or explicit historical window; `get_historical_prices` currently accepts `days`. Dated access therefore needs a narrow validated request/method extension. Preserve compatibility for current quote/history callers, and retain the requested window separately from returned record dates. Return a dated end-of-day lookup through historical or dedicated dated-result semantics; never write an old price into the current-quote path merely to fit an existing type. This is proposed integration work, not an existing capability.

This is a proposed checklist for mapping to existing types, not a new universal dataclass that must replace them.

| Field group | Required meaning |
|---|---|
| Provider | Exact provider, endpoint/tool, provider response version if available |
| Identity | Internal company/security reference, provider identifier, venue, share class where known |
| Requested scope | As-of cutoff, observation window, source filters and requested currency/basis |
| Time | Economic/event date, provider publication/availability time, retrieval/observation time, known precision |
| Value | Typed value, currency, scale, units, adjustment basis and period identity |
| Evidence | Original source ID/hash, page/section/row/segment locator and raw response reference |
| Completeness | Complete/partial/unavailable result, exclusions, coverage gaps and warnings |
| Provenance | Adapter version, source revision, transformation steps, run ID and input/configuration hashes |

Do not fill a missing timestamp with a different timestamp just to satisfy a schema. A filing date, market-session date, transcript call time and observation time answer different questions. Treat `unknown` as a legitimate state. A public-availability cutoff and a cutoff on what this application had already observed are different policies. Record both timing dimensions and select the intended policy explicitly; do not rewrite observation history to simulate prior knowledge.

### Failure behavior

Map errors to the existing `MarketDataProviderError` or appropriate domain error rather than returning fabricated empty success responses. Distinguish unsupported capability, unconfigured credentials, entitlement failure, unknown/ambiguous identity, rate limit, transient transport failure, parse/schema change, invalid financial basis, and partial historical coverage.

An empty valid dataset, a failed request, and a date with no trading session should be distinguishable. Retry only explicitly retryable failures within configured bounds. Preserve successful partial results as partial, with coverage and retry context visible.

### Reproducible run manifest

A saved configuration plus a current API query does not reproduce an old research result. The following is a **proposed conceptual JSON shape**, not an existing API response or executable configuration:

```json
{
  "manifest_version": 1,
  "run_id": "existing-processing-run-id",
  "task": "portfolio-allocation-scenario",
  "app_commit": "actual-implementation-commit",
  "preset_version_id": "saved-preset-version",
  "valuation_as_of": "2026-11-17T21:00:00Z",
  "knowledge_cutoff_policy": "public_availability",
  "public_availability_cutoff": "2026-11-17T21:00:00Z",
  "application_observed_cutoff": null,
  "snapshot_created_at": "2026-11-18T01:00:00Z",
  "input_snapshot_hash": "computed-hash",
  "source_revision_ids": ["existing-source-revision-id"],
  "provider": "explicitly-selected-provider",
  "adapter_version": "pinned-package-or-source-version",
  "return_basis": "explicitly-defined-basis",
  "currency": "USD",
  "calendar_version": "selected-calendar-and-overrides",
  "calculation_parameters_hash": "computed-hash",
  "model_and_prompt_version": null,
  "permission_receipt_id": null,
  "outputs_hash": "computed-hash",
  "warnings": []
}
```

Actual fields should fit existing schemas. In this illustrative manifest, public availability is the selected cutoff and the snapshot is assembled later; it does not claim the application held those records at the valuation time. A run using an application-observed cutoff must select that policy and populate the corresponding timestamp. Each referenced source retains its actual publication, observation and precision metadata. AI-specific fields are present only for a run that uses AI. Preserve originals, results and versions according to current storage rules. A replay should report whether it reused saved artifacts, recalculated locally, or fetched updated data. Do not label all three operations “reproduce.”
## Implementation backlog

Each ticket below is a proposal. Priority means usefulness for Marketagent, not a promise that every prerequisite is already complete. Relative effort includes integration and verification, and is not a time estimate.

### MA-01: EdgarTools financial candidate adapter

**Priority:** high. **Effort:** medium. **Donor:** EdgarTools.

Implement a narrow adapter for one supported SEC annual-statement path. Reuse original filing acquisition, source preservation, period/statement identity and reviewed financial candidates. Explicitly set each candidate's period type; the existing model's annual default is not a reliable substitute for parsing the source period. Keep the existing source parser available during comparison. Avoid network calls hidden inside arbitrary library properties; inspect the chosen library call path and isolate its transport.

**Acceptance:** one original and one amended filing; instant versus duration facts; same metric in different units; annual versus YTD/quarter; duplicate accession; multiple share classes; absent value; source publication after the research cutoff. Compare candidate output and source locators with existing fixtures. Quarterly/YTD rows remain ineligible for promotion until the period contract supports them.

**Deliverable:** adapter, integration at the existing owner, targeted tests, chosen dependency pin, configuration/source notes and an example reviewed candidate flow.

### MA-02: official NSE MCP market-data prototype

**Priority:** high for India. **Effort:** medium, with protocol/payload uncertainty. **Donor:** official MCP Python SDK; **data source:** NSE.

First capture the supported tools, schemas and a small explicitly requested sample. Then implement dated historical quotes/history and corporate-action retrieval through an allowlisted endpoint/tool set. Add a narrow validated dated-query contract/method because current MarketDataRequest has no date/window fields and current history only accepts days. Preserve current caller compatibility and validate requested start/end/session dates explicitly. Map quotes and history to current market-data result types. Preserve corporate actions as separately typed, versioned evidence records, adding a narrow result contract where needed. This ticket retrieves action evidence; applying actions to holdings or constructing adjusted/total-return series requires a separate calculation contract. Record requested versus returned date and unadjusted basis. Historical end-of-day results must not overwrite or appear as current quotes. Use explicitly verified listing identities and validated session handling for the prototype; the complete MA-15 identity migration can follow separately. Keep market data available independently of LLM-generated narration.

**Acceptance:** valid symbol, ambiguous/unknown symbol, market holiday, special session, a split/bonus period, overlapping history windows, rate limit, tool/schema change, partial multi-call retrieval and a dropped connection. Show delayed intraday data as delayed. Never treat a provider-reported return as verified total return without reconciling its basis.

**Deliverable:** bounded prototype and fixtures, followed by explicit provider-factory integration after compatibility is demonstrated. No live compatibility test was performed for this report.

### MA-03: FMP or another entitled market-data adapter

**Priority:** conditional on the chosen provider account. **Effort:** medium. **Donor:** selected official SDK or OpenBB adapter.

Replace the FMP placeholder only if FMP is the chosen dataset source. Otherwise add the selected provider through the same factory. Map quote/history fields into existing types and preserve original response identity/timing. Code availability and a provider account's dataset entitlement are separate prerequisites.

**Acceptance:** wrong market/venue, stale quote, missing currency, unknown adjustment basis, pagination, zero/negative invalid price, authentication failure, rate limit and provider outage. Confirm no implicit fallback to a differently licensed or differently adjusted dataset.

### MA-04: document extraction profile

**Priority:** high when current parsing fails. **Effort:** medium to high. **Donor:** Docling or Camelot; Marker as a comparison candidate.

Benchmark a small real-filing set with reference rows and source pages. Preserve current candidate types and review semantics. The inspected PDF worker uses a tight resource budget; a heavier OCR/model pipeline needs its own measured bounded profile or worker. Increasing the default limits for every parse is not a demonstrated solution.

**Acceptance:** page-spanning table, scanned page, row-label continuation, negatives, units in heading, two statement scopes, missing OCR, unsupported file and timeout. Verify source navigation and record the extraction profile/version. Record unavailable or uncertain cells explicitly.

### MA-05: vintage-aware macro observations

**Priority:** high before historical macro claims. **Effort:** medium. **References:** ALFRED and fredapi.

Extend the existing FredProvider and storage path with a selected vintage/as-of mode. Define initial-release, latest-current and latest-known-at-cutoff modes explicitly. Keep observation date, revision interval and local observation time separate.

**Acceptance:** two revisions of one observation; cutoff before first release; cutoff between revisions; missing value marker; unchanged release; pagination; invalid date; preserved historic snapshot after a later refresh. No fallback to latest data for an unavailable vintage.

### MA-06: Portfolio Lab

**Priority:** high new feature. **Effort:** medium. **Donor:** PyPortfolioOpt.

Add a proposed allocation scenario with a saved estimation window, return basis, covariance method, eligible assets and concentration constraints. Use existing holdings and risk/performance contracts. Expose excluded assets and infeasible constraints. Keep optimized allocations separate from booked holdings.

**Acceptance:** aligned mixed-currency inputs or explicit rejection; missing interior dates; insufficient history; zero variance; singular covariance; infeasible bounds; deterministic repeat with fixed inputs; constraints satisfied within documented solver tolerance; input change invalidates the old result. Convert to numerical-library floats only at the explicit analysis boundary and validate finite outputs.

Begin with a constrained minimum-volatility case. Expected-return views require a separate reviewed horizon and uncertainty contract. Solver success alone is not evidence of economic validity.

### MA-07: company research workbench

**Priority:** high UI. **Effort:** medium. **Donors:** OpenStock, shadcn/ui, TanStack Table, react-resizable-panels, React-PDF, Geist.

Build one company workflow: search, named research list, peer table, saved model and source pane. Adapt the inspected OpenStock interactions to current company APIs and request-scoping conventions. Use a deliberate component/version set with existing styling tokens.

Keep company lookup and existing stored-evidence search as distinct palette sections. Search/highlighting alone must not create a company or modify a list. Named lists need verified server-side ownership, identity, persistence and mutation behavior; split that work into a separate ticket if equivalent endpoints are absent. Failed mutations must not leave a successful-looking local list.

**Acceptance:** rapid company switching; stale responses; keyboard operation; narrow viewport; saved versus unsaved assumptions; source-pane resizing; unavailable PDF; exact source/page navigation; delayed versus stale quote; retained context after returning from evidence. Known save/version repairs are dependencies of editable areas.

### MA-08: portfolio evidence import review

**Priority:** high if import work is frequent. **Effort:** medium. **Donor:** Wealthfolio.

Extend the existing source-labeled price/FX evidence importer with clear row status, filtering, source identity, duplicate review and preview/apply separation. The current flow previews server-side and applies the exact `content_sha256` as `expected_sha256`; it is not a transaction importer. Begin with error navigation and filtering. If cells become editable, serialize the revised dataset and obtain a new server preview/hash before enabling apply. Account mapping and broker transactions are a separate future package tied to ledger replay.

**Acceptance:** create/skip/error totals match the server; original CSV row identities survive sorting/filtering; exact duplicates skip; conflicting price/FX evidence blocks apply; new file or edit invalidates the old preview; late responses for another portfolio cannot appear as current success; repeated apply is idempotent. Preserve provider, source URL, source timestamp, the 2 MiB/5,000-row limits and existing scope rules. A future transaction importer additionally needs opening-history, cash-flow, oversell and corporate-action checks.

### MA-09: memo rendering and exact-version export

**Priority:** high bounded UI improvement. **Effort:** low to medium, depending on existing repair scope. **Donor:** react-markdown.

Render the current `memo_markdown` as structured headings, lists and citations, adding a verified GFM plugin for tables. Keep the source Markdown canonical. Resolve citation markers through existing evidence records; unknown markers remain visibly unresolved. Disable raw HTML. Permit external http/https links and validated application routes/document anchors; reject javascript, data, unsupported schemes and unvalidated network-path links. Resolve citation targets only through authorized persisted evidence IDs and show unknown IDs as unresolved. Keep calculation identity, saved basis, AI Interpretation label and review state outside the generated body. A renderer does not repair broken memo contracts or saved-version selection.

**Acceptance:** long table, missing citation, unsupported URL, raw HTML-like input, source unavailable, model switch during generation, stale saved version, export matches the selected memo/version. Use an appropriate `.md` download for raw Markdown. Defer a rich editor until editing, versioning and export expectations are settled.

### MA-10: transcript and guidance research

**Priority:** medium. **Effort:** medium. **Sources:** entitled FMP/EarningsCall or selected official provider.

Ingest transcripts as versioned evidence with segment locators. Add reviewed guidance extraction and comparison with an earlier call. Separate the call event from provider availability. Use bounded overlap polling to catch late-added records.

**Acceptance:** late publication of an older call; corrected transcript; absent speaker; missing fiscal label; changed paragraph boundaries; duplicate provider record; unsupported coverage; no subscription; before-cutoff availability unknown. The same original segment must remain traceable after summary regeneration.

### MA-11: hybrid evidence retrieval

**Priority:** medium after retrieval evaluation. **Effort:** medium. **Donor:** pgvector and pgvector-python.

Add semantic retrieval beside current lexical search. Define a small set of actual questions and expected source passages before indexing. Apply ownership, issuer, date, document-version and source-type filters consistently to both branches. Store embedding model/version with indexed content.

**Acceptance:** paraphrased question, exact metric, ambiguous company name, old revision, source after cutoff, private/public separation, absent embedding, changed chunking and no evidence. Compare retrieval relevance with the existing search baseline; similarity is not factual approval.

### MA-12: durable processing pilot

**Priority:** medium. **Effort:** medium to high. **Donor:** DBOS.

Select one refresh/extraction workflow. Separate fetch, preservation, extraction, validation and recorded-result steps. Link DBOS execution to current Processing Runs. Keep retry budgets, cancellation and no-change/blocked outcomes visible.

**Acceptance:** process interruption between steps; retry after a successful remote response but before local persistence; duplicate invocation; cancellation; expired ownership/permission; deterministic failure; unavailable database. Verify idempotent writes and acknowledge that remote side effects can require separate deduplication.

### MA-13: generated contracts and run presets

**Priority:** high enabling work. **Effort:** low to medium. **Donors:** openapi-typescript and existing pydantic-settings.

Generate TypeScript types from the actual FastAPI schema while preserving current transport, authentication, aliases, envelopes and response reconciliation. Add versioned presets only for user-meaningful choices. Preserve a manifest linking input snapshots and exact provider/calculation versions.

**Acceptance:** nullable financial field; enum; aliases; structured error envelope; stale schema check; preset version isolation; secret exclusion; replay using saved inputs. Type generation does not replace backend validation or establish runtime JSON conformance.

### MA-14: fixture-based provider and agent evaluation

**Priority:** high companion to adapters. **Effort:** low to medium. **Donors:** RESPX where HTTPX applies, VCR.py where justified, Promptfoo, optional Pandera.

Reuse existing tests and evaluation fixtures. Add representative success, failure and schema-change fixtures at each actual transport boundary. Use redacted recordings only where collection and storage are appropriate. Default test runs should be deterministic and should not require paid API calls.

**Acceptance:** unmocked request fails; credentials/private content excluded from fixtures; rate limit; timeout; malformed response; missing facts; false/future citation; currency/unit mismatch; model refusal/provider failure; prompt version change. VCR cassette availability is not proof of endpoint compatibility or current entitlement. Test MCP streaming against the selected SDK/transport explicitly.

### MA-15: issuer/security and exchange-calendar services

**Priority:** high dependency for cross-market history; scope carefully. **Effort:** medium to high. **References:** OpenFIGI, exchange calendar libraries, official exchange sources.

Add an explicit mapping/ambiguity workflow for issuers, securities, listings and provider identifiers. Preserve validity dates and provenance. Add a calendar adapter with finite coverage, timezone and exchange override versions. Plan any schema migration against existing `Company.cik` and portfolio identity assumptions.

**Acceptance:** shared issuer with multiple share classes; dual listing; ticker rename/reuse; delisting; mapping returns several candidates; NSE versus BSE symbol; weekend Muhurat/special session; US DST/early close; unsupported future calendar date; local date versus UTC boundary. Calendar-aware session checks and annualization policy are separate decisions.

### MA-16: simulation and report exports

**Priority:** medium after portfolio input contracts. **Effort:** medium to high. **Donors:** bt and QuantStats; backtesting.py/vectorbt for specific research goals.

Use a separate simulated ledger. Save the universe, available information, rebalancing schedule, costs, execution timing and input snapshot. Feed report tools the same validated return series and benchmark basis used in the app.

**Acceptance:** contribution versus investment return; dividend/split; transaction costs; cash; missing asset/FX dates; delisted member; rebalance on a holiday; signal unavailable at execution time; consistent cumulative compounding; report reproduces the saved simulation. A current company universe is not a historical investable universe.
## A practical implementation sequence

### Package A: complete one company research workflow

Start with the current company/valuation pages and existing theme. Add the OpenStock search/list interactions, Geist typography, selected shadcn controls, and a TanStack peer table. Use resizable panes and React-PDF to keep original evidence beside the model.

Acceptance should include company switching without stale responses, saved versus unsaved assumptions, missing/stale data, keyboard navigation, mobile layout and exact source navigation. Preserve existing save/version and review semantics.

### Package B: improve evidence coverage

Evaluate EdgarTools on selected difficult SEC filings and Docling/Camelot on a small set of actual PDFs. For an India-first package, prototype the documented official NSE adapter and validate identity/calendar/adjustment behavior before expanding coverage. Record extraction errors by document/period/metric instead of only reporting an overall success rate. Preserve original assets and source hashes.

Extend supported period identity and promotion rules before making quarterly/YTD inputs eligible. Source completeness is more valuable than importing another financial-model implementation.

### Package C: build Portfolio Lab

Use validated holdings/returns and PyPortfolioOpt to compare hypothetical allocations. Expose concentration constraints and covariance assumptions. Show infeasible constraints explicitly. Keep outputs as scenarios.

Add bt only when the product needs to compare rebalancing policies. Use availability dates and transaction-cost assumptions, and preserve a separate actual portfolio ledger.

### Package D: operational and evaluation follow-through

Generate API types; add versioned presets to existing Pydantic contracts; evaluate prompt/model changes with Promptfoo. Prototype DBOS on one workflow and measure recovery behavior. Add semantic retrieval when a labeled set of real questions demonstrates the need.

### Packages to defer

Do not replace the whole backend with OpenBB, OpenStock or Ghostfolio. Do not add several agent frameworks, queue engines, vector databases or optimizers concurrently. Qlib and LEAN are serious research platforms but would expand the project into a substantially different product.

The current Marketagent limitation ledger still records source-intake, saved-editor/export and return-method work. Features that depend on those paths should include those repairs in their acceptance scope rather than obscure them with a new interface.
## Acceptance cases shared across packages

These are proposed meaningful checks for the selected implementation, not a request to run every test for every UI edit.

| Area | Case that should be demonstrated |
|---|---|
| Period identity | A quarter, YTD duration and annual duration do not collapse into the same fact |
| Revisions | A later amendment does not appear in a result claiming an earlier knowledge cutoff |
| Units | USD millions, INR crore, raw shares and millions of shares retain distinct basis |
| Missingness | Zero, absent, unavailable and invalid do not become interchangeable |
| Identity | Two listed share classes are not merged because they share a CIK |
| Prices | Requested holiday date and returned session date remain visible |
| Corporate actions | A split/bonus is not mistaken for an investment loss or adjusted twice |
| Total returns | Dividends and flows are handled according to the declared return definition |
| Calendars | Exceptional sessions and unsupported calendar years are handled explicitly |
| Parsing | Original bytes, page and metric location survive extraction and review |
| Failure | A schema change or timeout cannot become a successful empty result |
| Retries | Repeated imports/runs do not duplicate accepted ledger or source records |
| UI state | Old responses cannot overwrite a newer company/model/version selection |
| Exports | Downloaded values and warnings correspond to the exact selected saved version |
| Retrieval | Private, future and superseded evidence is excluded according to the selected policy |
| AI | Invalid citations, unsupported claims and missing numerical basis remain visible |
## Copyable implementation prompts

Attach this complete Markdown file before using a prompt in a new chat or coding session. Each prompt names the repository and selects a bounded task; the attachment supplies the detailed contracts and acceptance cases. In this same chat the research context is already available. Interpret each prompt with the user's actual authorization and current repository instructions.

### Prompt A: first SEC adapter

```text
Implement MA-01 from this Marketagent handoff: an EdgarTools adapter for one supported annual SEC financial-statement path.

Use https://github.com/Gittastic112/Marketagent and the attached consolidated Markdown handoff. Inspect current HEAD and applicable AGENTS.md, HANDOFF, code-map and limitations. Report the implementation commit and any material differences from research snapshot 371b58c02cfd2b80429f28dbc13629165b5e392d.

Integrate with existing filing acquisition, source preservation, period/statement identity, candidate review and promotion contracts. Preserve original sources and current annual-only eligibility. Keep missing values, units, currency, filing availability and amendments explicit. Inspect and bound the selected dependency's actual outbound behavior.

Add meaningful offline fixtures and targeted tests for period, unit, amendment and duplicate cases. Prepare a reviewable code change with dependency pin, attribution and docs. State exactly what ran, what passed, and what remains unverified. Complete the adapter and integration within this scope; do not expand into a backend rewrite.
```

### Prompt B: official India data prototype

```text
Implement MA-02 from this Marketagent handoff as a bounded official NSE MCP prototype.

Use https://github.com/Gittastic112/Marketagent and the attached consolidated Markdown handoff. Inspect current HEAD, applicable AGENTS.md and the relevant HANDOFF/code-map/limitations before changing code. Inspect the official NSE MCP documentation. Verify the current protocol, tool schemas and selected SDK version before writing mappings. Start with dated quotes/history and corporate-action evidence using the documented NSE endpoints.

The existing MarketDataRequest has identity fields but no date/window, and existing history only accepts days. Add a narrow validated dated-query contract/method while preserving existing callers. Reuse existing identity and MarketQuoteResult/MarketHistoryResult output fields through the provider factory and Processing Runs, retaining requested date/window in query provenance. Historical end-of-day results must remain historical and must not overwrite current quotes. Preserve corporate actions as separately typed, versioned evidence, with a narrow contract if needed. This prototype retrieves action evidence; it does not apply actions to holdings or construct adjusted/total-return series. Use explicitly verified listings and validated sessions while a fuller identity service remains separate. Preserve requested date versus actual session date, delayed/end-of-day labels, unadjusted price basis, raw response provenance and partial coverage. Use explicit request/time/size budgets and no hidden provider fallback.

Add offline tests for holidays, splits/bonuses, overlapping windows, partial failure and schema drift. Report whether live compatibility was actually exercised. Keep calculations and holdings unchanged unless required by this narrowly defined integration.
```

### Prompt C: research workbench

```text
Implement MA-07 from this Marketagent handoff in the existing Next.js frontend.

Use https://github.com/Gittastic112/Marketagent and the attached consolidated Markdown handoff. Inspect current HEAD, applicable AGENTS.md and relevant HANDOFF/code-map/limitations. Adapt OpenStock company-search and named-list interactions, selected shadcn controls, TanStack peer-table behavior, Geist typography and resizable evidence panes. Use existing APIs, identity, request scoping and design tokens. Preserve existing stored-evidence search separately from company lookup. Named lists require verified server persistence, ownership and identity; split them into a separate ticket if equivalent endpoints are absent.

Complete one company research flow: find company, open saved valuation, compare peers, inspect source evidence and return with context preserved. Reconcile existing save/version and source-navigation issues that block this flow. Pin compatible packages and preserve third-party notices.

Verify keyboard behavior, narrow layout, rapid company switching, missing/stale data, saved versus unsaved state and exact source navigation. Deliver the implemented flow with screenshots or runnable verification where available, and clearly identify any unavailable checks.
```

### Prompt D: Portfolio Lab

```text
Implement MA-06 from this Marketagent handoff: a PyPortfolioOpt allocation scenario feature.

Use https://github.com/Gittastic112/Marketagent and the attached consolidated Markdown handoff. Inspect current HEAD, applicable AGENTS.md and relevant HANDOFF/code-map/limitations. Use existing portfolio holdings and validated return contracts. Start with constrained minimum-volatility weights, explicit estimation window/covariance method, concentration limits, exclusions and infeasibility diagnostics. Keep proposed allocations separate from actual holdings and preserve the current ledger.

Do not convert valuation upside directly into an expected annual return. Save the input snapshot, return basis, currency, constraints and calculation versions. Reconcile any current return-method mismatch affecting this feature.

Add targeted tests for missing dates, insufficient history, singular covariance, infeasible constraints, finite output and deterministic repeatability. Implement backend and a compact comparison UI, with run provenance and limitations visible.
```

### Prompt E: small memo improvement

```text
Implement MA-09 from this Marketagent handoff: render the existing valuation memo Markdown and align its export.

Use https://github.com/Gittastic112/Marketagent and the attached consolidated Markdown handoff. Inspect current HEAD, applicable AGENTS.md and relevant HANDOFF/code-map/limitations. Inspect valuation-memo-panel.tsx and the current memo/version contracts. Use react-markdown with raw HTML disabled. Permit external http/https links plus validated app routes/anchors; reject javascript/data and unsupported schemes or unvalidated network-path targets. Resolve citations only through authorized persisted evidence IDs and show unknown references as unresolved. Preserve the Markdown source, exact model/version identity and existing review behavior. Export raw Markdown with the correct format and filename.

Address the specific existing memo/export defects that block this flow. Verify tables, missing citations, rejected URL schemes, model switching during generation and export matching the selected saved memo. Avoid introducing a rich editor or new chart engine for this task.
```
## Decisions to resolve during the selected build

These do not block the research file. They become relevant when a corresponding package is selected.

| Decision | Sensible starting position |
|---|---|
| First supported market | Match the selected package: SEC for MA-01, NSE for MA-02 |
| Data subscriptions | Use existing explicit access; select a plan only when its dataset is needed |
| Historical truth claim | Require known availability and explicit gaps; distinguish latest-data analysis |
| Price/return basis | Preserve raw and derived series separately with a declared adjustment policy |
| Parser profile | Measure on real inputs before selecting resource limits and a default |
| UI/editor scope | Improve current component and fix saved-version behavior first |
| Optimizer input | Start with risk-based constrained allocation; reviewed expected returns later |
| Storage expansion | Reuse PostgreSQL and existing source stores; add analytical engines only for a measured need |
| Deployment | Implement and verify a bounded change; deployment is a separate requested action |

For copied code, retain a third-party record with repository URL, exact commit/tag, copied paths, license/NOTICE files, local modifications and update strategy. Prefer a pinned dependency where the library's public interface is sufficient; use adapted source where component-level changes are the point. These are maintenance choices, not a ranking by GitHub stars.
## Licensing under the user's personal-project scope

Private personal use makes GPL/AGPL far less of a selection concern. These licenses are not blanket prohibitions on reuse or charging money. Credit is useful but is not a substitute for the actual terms.

Marketagent is presently a public repository. Publishing copied code there is still redistribution even if the app has one user. Relevant license text, copyright/NOTICE files, modification notices and any applicable source-license requirements must be retained. AGPL also contains a source-offer requirement for users interacting remotely with a modified covered program.

Primary references: [GNU GPL FAQ](https://www.gnu.org/licenses/gpl-faq.html), [AGPL section 13](https://www.gnu.org/licenses/agpl-3.0.html#section13), and [GitHub's repository licensing guide](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/licensing-a-repository).

For implementation, keep a small THIRD_PARTY_NOTICES record with repository, exact commit/tag, copied paths, license and changes. This makes attribution and future updates easier. Unlicensed code, model weights, trademarks and market data can have distinct permissions. A publicly visible API wrapper does not grant access to a paid dataset.

Notable current observations:

1. OpenStock, Ghostfolio, Wealthfolio and backtesting.py are AGPL projects. They remain candidates for this personal project.
2. OpenBB's inspected current develop source is Apache 2.0, and FinanceToolkit's inspected current source is MIT. Do not repeat older blanket license descriptions.
3. vectorbt includes the Commons Clause. Personal research and selling a service based substantially on its functionality are different cases.
4. Marker has Apache 2.0 code and separate model-weight terms.
5. Langfuse and LiteLLM identify separately licensed enterprise directories.
6. Phoenix uses Elastic License 2.0; Inngest's server terms differ from its Apache-licensed Python SDK.
7. Dexter's README states MIT, but the inspected tree had no license file and [issue 224](https://github.com/virattt/dexter/issues/224) requests clarification. Treat the grant as unresolved rather than inventing a restriction or permission.
8. Financial_freedom's book PDFs do not become reusable product content merely because they are in a public repository.
## Original repository inventory

**Depth key:** Code = implementation or concrete code examples inspected, plus relevant supporting material. Docs = screening from README, tree, project documentation, metadata and/or license, without implementation review. Neither means the complete repository was audited or executed.

### Finance, valuation, filings, and portfolio research

| Repository | License observed | Depth | Decision | Fit and caveat |
|---|---|---|---|---|
| [dgunning/edgartools](https://github.com/dgunning/edgartools) | MIT | Code | Priority | Broader SEC parsing, filing sections and financial period handling; adapt into existing reviewed-fact contracts. |
| [openbq-org/OpenBB](https://github.com/openbq-org/OpenBB) | Apache-2.0 on develop | Code | Selective | Add one missing provider/dataset at a time. Original OpenBB-finance/OpenBB URL redirects here; data subscriptions remain separate. |
| [JerBouma/FinanceToolkit](https://github.com/JerBouma/FinanceToolkit) | MIT | Code | Selective | Ratio definitions, diagnostic calculations and independent comparisons; existing Marketagent valuation engine should remain authoritative. |
| [JerBouma/FinanceDatabase](https://github.com/JerBouma/FinanceDatabase) | MIT | Code | Useful | Candidate peers and symbol discovery by country, sector, exchange and listing. Not a historical universe or current fundamentals feed. |
| [docling-project/docling](https://github.com/docling-project/docling) | MIT; model terms separate | Code | Priority | Extract structured tables and OCR from filings into reviewable candidates with retained original pages. |
| [Unstructured-IO/unstructured](https://github.com/Unstructured-IO/unstructured) | Apache-2.0 | Docs | Alternative | Alternative document partitioning stack. Benchmark against Docling on actual filings instead of adopting both automatically. |
| [virattt/dexter](https://github.com/virattt/dexter) | README states MIT; grant needs clarification | Code | Reference | Research tool selection and execution logs. No license file found in inspected tree; public issue asks for clarification. |
| [virattt/ai-hedge-fund](https://github.com/virattt/ai-hedge-fund) | MIT | Code | Selective | Information cutoffs, filing timestamps and paper-ledger replay patterns. Avoid replacing the existing portfolio ledger. |
| [jadchaar/sec-edgar-downloader](https://github.com/jadchaar/sec-edgar-downloader) | MIT | Docs | Alternative | Small SEC download utility when retrieval alone is needed; less parsing scope than EdgarTools. |
| [halessi/DCF](https://github.com/halessi/DCF) | No license found in inspected tree | Docs | Defer | Simpler DCF duplicates existing functionality; no compelling additional capability found. |
| [stockvaluation-io/stockvaluation_io](https://github.com/stockvaluation-io/stockvaluation_io) | Apache-2.0 | Code | Selective | Source provenance and requested-versus-effective scenario contracts; Java engine is a poor replacement for existing Python math. |
| [kernc/backtesting.py](https://github.com/kernc/backtesting.py) | AGPL-3.0 | Code | Useful optional | Readable single-instrument strategy sandbox. Personal-use suitability is good; multiasset allocation first favors bt. |
| [codeman008/Financial_freedom](https://github.com/codeman008/Financial_freedom) | No license found in inspected tree | Docs | Exclude as code donor | README and book PDFs; no reusable application implementation observed. |
| [PyPortfolio/PyPortfolioOpt](https://github.com/PyPortfolio/PyPortfolioOpt) | MIT | Code | Priority | Constrained allocation scenarios, covariance shrinkage, risk allocation and explicit investment views. |
| [tradytics/eiten](https://github.com/tradytics/eiten) | GPL-3.0 | Code | Reject implementation | Cumulative simple returns are added with cumsum; weak date/adjustment handling and old dependency pins. Ideas remain educational. |
| [ranaroussi/quantstats](https://github.com/ranaroussi/quantstats) | Apache-2.0 | Code | Useful | HTML reports and selected return diagnostics from Marketagent-owned return series. |
| [polakowo/vectorbt](https://github.com/polakowo/vectorbt) | Apache-2.0 plus Commons Clause | Docs | Useful optional | Fast research sweeps can be attractive for personal experimentation. Reassess distribution/service terms if scope changes. |
| [pmorissette/bt](https://github.com/pmorissette/bt) | MIT | Code | Priority for simulation | Date-indexed target weights, periodic rebalance and cash handling for a separate research simulator. |
| [skfolio/skfolio](https://github.com/skfolio/skfolio) | BSD-3-Clause | Code | Alternative | Stronger research-validation orientation, walk-forward splits and portfolio model selection. Choose coherent scope with PyPortfolioOpt. |
| [dcajasn/Riskfolio-Lib](https://github.com/dcajasn/Riskfolio-Lib) | BSD-3-Clause | Docs | Later | Advanced portfolio risk and risk-budgeting methods if simpler allocation tools become insufficient. |
| [LuisSousaSilva/ds4finance](https://github.com/LuisSousaSilva/ds4finance) | MIT | Docs | Low incremental value | Small performance metrics helpers overlap existing calculation services. |
| [Arelle/Arelle](https://github.com/Arelle/Arelle) | Apache-2.0; dependencies separately licensed | Docs | Later | Detailed XBRL validation and taxonomy handling for complex filing ingestion. |

### Interface, financial workbench, and product references

| Repository | License observed | Depth | Decision | Fit and caveat |
|---|---|---|---|---|
| [shadcn-ui/ui](https://github.com/shadcn-ui/ui) | MIT | Code | Priority | Copy selected navigation, dialogs, inputs, evidence and current AI Elements compositions into existing tokens. |
| [TanStack/table](https://github.com/TanStack/table) | MIT | Code | Priority | Headless peer, assumptions and source tables with pinning, filtering, visibility and sorting. |
| [bvaughn/react-resizable-panels](https://github.com/bvaughn/react-resizable-panels) | MIT | Code | Priority | Resizable research/model/evidence panes with saved layouts. |
| [vercel/geist-font](https://github.com/vercel/geist-font) | SIL OFL-1.1 | Docs | Priority | Geist Sans and Mono typography; fonts do not supply Vercel's complete design system. |
| [wojtekmaj/react-pdf](https://github.com/wojtekmaj/react-pdf) | MIT | Code | Priority | Render original PDF pages and support text/annotation layers in evidence drawers. |
| [Comcast/react-data-grid](https://github.com/Comcast/react-data-grid) | MIT | Code | Prototype | Editable assumption cells, paste, fill, frozen columns and keyboard workflows; prototype current React-compatible build. |
| [vercel/chatbot](https://github.com/vercel/chatbot) | Apache-2.0 | Code | Selective | Versioned research artifacts beside chat. The example sheet editor is a CSV grid, not a financial formula engine. |
| [dip/cmdk](https://github.com/dip/cmdk) | MIT | Code | Useful | One command palette across companies, filings, models and actions, preferably through shadcn Command. |
| [tradingview/lightweight-charts](https://github.com/tradingview/lightweight-charts) | Apache-2.0; attribution requirements | Code | Conditional | Financial time-series interaction and event/valuation overlays. Keep existing Recharts for ordinary analytical charts. |
| [Open-Dev-Society/OpenStock](https://github.com/Open-Dev-Society/OpenStock) | AGPL-3.0 | Code | Strong app donor | Ticker search, persistent tabs, market browsing and watchlist interactions fit React/Next. Adapt to existing backend and truthful freshness. |
| [ghostfolio/ghostfolio](https://github.com/ghostfolio/ghostfolio) | AGPL-3.0 | Code | Product/domain reference | Portfolio rule explanations, benchmark and account drilldowns. Angular/Nest architecture makes direct UI porting expensive. |
| [tremorlabs/tremor](https://github.com/tremorlabs/tremor) | Apache-2.0 | Code | Selective | Compact analytical components such as BarList and Tracker; avoid introducing a competing visual system. |
| [assistant-ui/assistant-ui](https://github.com/assistant-ui/assistant-ui) | MIT | Docs | Conditional | Dedicated chat runtime/components if conversational interaction becomes a primary workflow. |
| [vercel/ai-elements](https://github.com/vercel/ai-elements) | Apache-2.0 | Code | Use successor | Old CLI scheduled for deprecation at end of November 2026. Current shadcn AI Elements docs are live. |
| [ag-grid/ag-grid](https://github.com/ag-grid/ag-grid) | MIT community; enterprise commercial | Docs | Alternative | Capable grid option. Determine which required features belong to which package before adopting. |
| [handsontable/hyperformula](https://github.com/handsontable/hyperformula) | GPL-3.0 or proprietary | Docs | Conditional | Actual spreadsheet formula engine if arbitrary spreadsheet interoperability becomes a requirement; not needed for backend-owned DCF. |
| [DanielArnould/react-pdf-highlighter-extended](https://github.com/DanielArnould/react-pdf-highlighter-extended) | MIT | Docs | Defer compatibility | Inspected package declares React 18 peer dependency; Marketagent is React 19. |
| [glideapps/glide-data-grid](https://github.com/glideapps/glide-data-grid) | MIT | Code | Alternative | Canvas grid for demanding data editing; number parsing and financial semantics still need application-specific work. |

### Backend, configuration, retrieval, evaluation, and reliability

| Repository | License observed | Depth | Decision | Fit and caveat |
|---|---|---|---|---|
| [pgvector/pgvector](https://github.com/pgvector/pgvector) | PostgreSQL License | Docs | Priority | Vector retrieval in existing PostgreSQL; combine with current lexical search and exact source filters. |
| [pgvector/pgvector-python](https://github.com/pgvector/pgvector-python) | MIT | Code | Priority companion | SQLAlchemy vector integration and reciprocal-rank-fusion hybrid search example. |
| [dbos-inc/dbos-transact-py](https://github.com/dbos-inc/dbos-transact-py) | MIT | Code | Prototype | Postgres-backed durable steps and job recovery; test one existing refresh workflow before wider use. |
| [promptfoo/promptfoo](https://github.com/promptfoo/promptfoo) | MIT | Code | Priority | Configurable prompt/model regression runs through a Python provider; reuse existing financial/evidence fixtures. |
| [unionai-oss/pandera](https://github.com/unionai-oss/pandera) | MIT | Code | Selective | Dataframe-level validation and multiple error reporting for imports and financial normalization. |
| [langfuse/langfuse](https://github.com/langfuse/langfuse) | MIT except listed enterprise paths | Code | Optional | Trace inspection and prompt/experiment operations; full self-host adds infrastructure. |
| [langfuse/langfuse-python](https://github.com/langfuse/langfuse-python) | MIT | Code | Optional companion | Scoped traces, latency/cost metadata and input/output capture controls around existing provider boundary. |
| [BerriAI/litellm](https://github.com/BerriAI/litellm) | MIT except enterprise directory | Code | Conditional | Provider routing and budgets when multiple providers are actually required; preserve per-provider consent and receipts. |
| [HypothesisWorks/hypothesis](https://github.com/HypothesisWorks/hypothesis) | MPL-2.0; noted third-party exceptions | Docs | Useful developer tool | Generated numerical edge cases and valuation invariants with clearly stated assumptions. |
| [karpetrosyan/hishel](https://github.com/karpetrosyan/hishel) | BSD-3-Clause | Docs | Conditional | HTTPX caching; default cache policy needs deliberate RFC behavior and isolation; not an evidence archive. |
| [pydantic/pydantic-settings](https://github.com/pydantic/pydantic-settings) | MIT | Code | Already present | Extend existing Settings and versioned run presets; do not add another configuration framework. |
| [pydantic/pydantic-ai](https://github.com/pydantic/pydantic-ai) | MIT | Docs | Later | Typed iterative tool-using agents if that becomes an actual product requirement. |
| [langchain-ai/langgraph](https://github.com/langchain-ai/langgraph) | MIT for checked core/checkpoint packages | Docs | Later | Complex branching workflows and checkpoints; overlaps existing bounded run state today. |
| [567-labs/instructor](https://github.com/567-labs/instructor) | MIT | Docs | Conditional | Structured output adapters when current schema generation no longer meets requirements. |
| [temporalio/sdk-python](https://github.com/temporalio/sdk-python) | MIT for SDK | Docs | Later | Cross-service durable orchestration; more infrastructure than current local Python/Postgres app needs. |
| [rq/rq](https://github.com/rq/rq) | BSD-2-Clause | Docs | Alternative | Simple Python jobs with Redis; credible if a broker is already part of the design. |
| [Bogdanp/dramatiq](https://github.com/Bogdanp/dramatiq) | LGPL-3.0-or-later | Docs | Alternative | Task queues and retries through RabbitMQ/Redis; consider operational fit rather than rejecting for copyleft. |
| [triggerdotdev/trigger.dev](https://github.com/triggerdotdev/trigger.dev) | Apache-2.0 root | Docs | Alternative | TypeScript workflows and long tasks if orchestration moves to the Next.js side. |
| [inngest/inngest](https://github.com/inngest/inngest) | SSPL with delayed Apache terms | Docs | Alternative service | Event-driven orchestration server; distinguish server license from SDK and managed service use. |
| [inngest/inngest-py](https://github.com/inngest/inngest-py) | Apache-2.0 | Docs | Alternative companion | Python integration for Inngest without copying its server. |
| [qdrant/qdrant](https://github.com/qdrant/qdrant) | Apache-2.0 | Docs | Later | Dedicated vector database when measured requirements exceed PostgreSQL. |
| [Arize-ai/phoenix](https://github.com/Arize-ai/phoenix) | Elastic License 2.0 | Docs | Alternative | AI tracing/evaluation; source-available terms differ from MIT, personal internal use remains a relevant case. |

### Additional cross-checks and alternatives

| Repository | License observed | Depth | Decision | Fit and caveat |
|---|---|---|---|---|
| [wealthfolio/wealthfolio](https://github.com/wealthfolio/wealthfolio) | AGPL-3.0 | Code | Strong app donor | React import-review grid, account and holdings presentation, local portfolio UX. Backend/domain adapters still need porting. |
| [portfolio-performance/portfolio](https://github.com/portfolio-performance/portfolio) | EPL-1.0 | Code | Validation reference | Mature portfolio workflows and IRR regression examples; Java desktop architecture is not a drop-in backend. |
| [Fincept-Corporation/FinceptTerminal](https://github.com/Fincept-Corporation/FinceptTerminal) | AGPL-3.0-or-later on current main | Docs | Product reference | Broad terminal and data-connector ideas. Current C++/Qt application is a poor base for this Next/FastAPI project. |
| [openapi-ts/openapi-typescript](https://github.com/openapi-ts/openapi-typescript) | MIT | Code | Priority | Generate TypeScript contracts from FastAPI OpenAPI while preserving existing authenticated transport. |
| [hey-api/hey-api](https://github.com/hey-api/hey-api) | MIT | Docs | Alternative | Generate full SDKs and validators if type-only generation proves insufficient; avoid duplicate client layers. |
| [QuantConnect/Lean](https://github.com/QuantConnect/Lean) | Apache-2.0 | Docs | Later/reference | Extensive event-driven backtesting and corporate-action modeling, with C# engine and Python integrations; much larger scope. |
| [microsoft/qlib](https://github.com/microsoft/qlib) | MIT | Docs | Later/reference | ML quant research and point-in-time data patterns; not a replacement for reviewed fundamental valuation. |
| [camelot-dev/camelot](https://github.com/camelot-dev/camelot) | MIT | Code | Useful extraction alternative | Targeted financial table recovery, including optional structure models; benchmark against existing parser and Docling. |
| [datalab-to/marker](https://github.com/datalab-to/marker) | Apache-2.0 code; separate modified OpenRAIL model terms | Docs | Extraction alternative | PDF to structured formats, OCR options and local modes; compare on real filings rather than vendor benchmark claims. |
## Additional repository inventory

The follow-up adds **22 unique repositories: 21 at Code depth and one at Docs depth**. Together with the initial 71, the consolidated screen covers **93 repositories: 60 Code and 33 Docs**. NSE MCP and BSE Self Data Feed are official services, not extra GitHub repositories. Official SEC, FRED/ALFRED, OpenFIGI and provider documentation was also consulted without inflating the repository count.

| Repository | License observed | Depth | Decision | Fit and caveat | Source inspected |
|---|---|---|---|---|---|
| [OpenFIGI/api-examples](https://github.com/OpenFIGI/api-examples) | Apache-2.0 | Code | Useful identity adapter | Candidate mapping among identifiers, listings and share classes; preserve ambiguity and unlisted instruments. | [Source](https://github.com/OpenFIGI/api-examples/blob/main/python/example.py) |
| [rsheftel/pandas_market_calendars](https://github.com/rsheftel/pandas_market_calendars) | MIT | Code | Conditional calendar backend | Dedicated NSE calendar, with finite coverage and documented weekend-session limits; add explicit overrides. | [Source](https://github.com/rsheftel/pandas_market_calendars/blob/master/pandas_market_calendars/calendars/nse.py) |
| [gerrymanoim/exchange_calendars](https://github.com/gerrymanoim/exchange_calendars) | Apache-2.0 | Code | Alternative calendar backend | International sessions and XBOM calendar; validate Indian special dates and coverage before adoption. | [Source](https://github.com/gerrymanoim/exchange_calendars/blob/master/exchange_calendars/exchange_calendar_xbom.py) |
| [EarningsCall/earningscall-python](https://github.com/EarningsCall/earningscall-python) | MIT | Code | Optional transcript provider | Fiscal events, transcript sections/speakers and timing; API entitlement and publication-time gaps remain. | [Source](https://github.com/EarningsCall/earningscall-python/blob/master/earningscall/transcript.py) |
| [massive-com/client-python](https://github.com/massive-com/client-python) | MIT | Code | Conditional U.S. reference feed | Corporate actions and security reference; event/report dates do not prove historical feed availability. | [Source](https://github.com/massive-com/client-python/blob/master/massive/rest/reference.py) |
| [BennyThadikaran/NseIndiaApi](https://github.com/BennyThadikaran/NseIndiaApi) | GPL-3.0 | Code | Discovery/parser reference | Indian filing metadata, announcement timings and optional XBRL links; website dependency is the main limitation. | [Source](https://github.com/BennyThadikaran/NseIndiaApi/blob/main/src/nse/NSE.py) |
| [BennyThadikaran/BseIndiaApi](https://github.com/BennyThadikaran/BseIndiaApi) | GPL-3.0 | Code | Discovery/parser reference | Paginated announcements, attachments, corporate actions and statement units; official feed preferred when available. | [Source](https://github.com/BennyThadikaran/BseIndiaApi/blob/main/src/bse/BSE.py) |
| [jugaad-py/jugaad-data](https://github.com/jugaad-py/jugaad-data) | Custom YOLO v2 public-domain declaration | Code | Defer core dependency | Historical NSE parsing depends on website-session cookies; official NSE MCP is a stronger first option. | [Source](https://github.com/jugaad-py/jugaad-data/blob/master/jugaad_data/nse/history.py) |
| [lundberg/respx](https://github.com/lundberg/respx) | BSD-3-Clause | Code | Useful with new HTTPX adapters | Mock actual HTTPX requests and assert calls/failures; does not cover every transport automatically. | [Source](https://github.com/lundberg/respx/blob/master/respx/router.py) |
| [kevin1024/vcrpy](https://github.com/kevin1024/vcrpy) | MIT | Code | Optional fixture replay | Record and replay sanitized interactions; verify chosen release and actual transport/streaming compatibility. | [Source](https://github.com/kevin1024/vcrpy/blob/master/vcr/stubs/httpx_stubs.py) |
| [duckdb/duckdb](https://github.com/duckdb/duckdb) | MIT | Docs | Conditional analytics | Embedded SQL over explicit fixed snapshots; PostgreSQL remains the application's system of record. | [Source](https://github.com/duckdb/duckdb) |
| [duckdb/duckdb-python](https://github.com/duckdb/duckdb-python) | MIT | Code | Conditional companion | Python Parquet/analytical-query interface if one measured workload justifies DuckDB. | [Source](https://github.com/duckdb/duckdb-python/blob/main/tests/fast/api/test_read_parquet.py) |
| [pola-rs/polars](https://github.com/pola-rs/polars) | MIT | Code | Defer until profiling | Lazy transforms and Parquet scanning for large data; preserve dtypes/nulls/times across pandas boundaries. | [Source](https://github.com/pola-rs/polars/blob/main/py-polars/src/polars/io/parquet/functions.py) |
| [hgrecco/pint](https://github.com/hgrecco/pint) | BSD-3-Clause | Code | Defer current valuation use | Broader dimensional units; existing financial scale and FX rules remain authoritative. | [Source](https://github.com/hgrecco/pint/blob/master/pint/facets/context/objects.py) |
| [treeverse/dvc](https://github.com/treeverse/dvc) | Apache-2.0 | Code | Optional developer tool | Version a larger permitted benchmark corpus/pipeline; unnecessary for small fixtures and live app records. | [Source](https://github.com/treeverse/dvc/blob/main/dvc/repo/reproduce.py) |
| [remarkjs/react-markdown](https://github.com/remarkjs/react-markdown) | MIT | Code | Immediate bounded UI improvement | Render existing memo Markdown with raw HTML disabled and separately validated citation targets. | [Source](https://github.com/remarkjs/react-markdown/blob/main/lib/index.js) |
| [perspective-dev/perspective](https://github.com/perspective-dev/perspective) | Apache-2.0 | Code | Defer to large screener | Interactive pivot/grid/chart exploration; extra lifecycle and data/bundle costs need a real requirement. | [Source](https://github.com/perspective-dev/perspective/blob/master/packages/react/src/viewer.tsx) |
| [apache/echarts](https://github.com/apache/echarts) | Apache-2.0 plus component notices | Code | Defer | Advanced linked charts or dense matrices; current Recharts and accessible sensitivity tables already serve current scope. | [Source](https://github.com/apache/echarts/blob/master/src/chart/heatmap/HeatmapView.ts) |
| [meta/lexical](https://github.com/meta/lexical) | MIT | Code | Later editor alternative | Structured user-authored notes and citation nodes after version/draft/export contracts are defined. | [Source](https://github.com/meta/lexical/blob/main/packages/lexical-react/src/LexicalOnChangePlugin.ts) |
| [ueberdosis/tiptap](https://github.com/ueberdosis/tiptap) | MIT for inspected open-source repo | Code | Later editor alternative | Conventional rich memo editing with React/SSR handling; select one editor after a focused prototype. | [Source](https://github.com/ueberdosis/tiptap/blob/main/packages/react/src/useEditor.ts) |
| [modelcontextprotocol/python-sdk](https://github.com/modelcontextprotocol/python-sdk) | MIT | Code | Conditional NSE transport | Current Client example and transport docs inspected; pin actual version/protocol and integrate bounded transport. | [Source](https://github.com/modelcontextprotocol/python-sdk/blob/main/docs_src/client_transports/tutorial002.py) |
| [mortada/fredapi](https://github.com/mortada/fredapi) | Apache-2.0 | Code | ALFRED behavioral reference | Revision methods are useful; extend existing bounded FredProvider and explicitly select latest eligible revision. | [Source](https://github.com/mortada/fredapi/blob/master/fredapi/fred.py) |

### Official service additions

| Service | Source | Decision and verification limit |
|---|---|---|
| NSE MCP | [Official documentation](https://www.nseindia.in/nse-mcp) | Strong personal-research candidate for Indian prices/actions; documented endpoints, no live protocol/payload test in this research |
| BSE Self Data Feed | [Official product page](https://marketdata.bseindia.com/) | Corporate financials, disclosures, announcements and actions are offered; obtain relevant access/specification before implementing concrete calls |
## Additional source references

The following files add implementation evidence behind the secondary candidates.

| Repository | Source examined or primary reference | Why it matters |
|---|---|---|
| StockValuation.io | [source_provenance.py](https://github.com/stockvaluation-io/stockvaluation_io/blob/main/valuation-agent/source_provenance.py), [scenario_book.py](https://github.com/stockvaluation-io/stockvaluation_io/blob/main/valuation-agent/scenario_book.py) | Distinguish input source quality and requested/effective assumptions; fixed staleness policies need adaptation |
| AI Hedge Fund | [models.py](https://github.com/virattt/ai-hedge-fund/blob/main/hedge_fund/data/models.py), [clock.py](https://github.com/virattt/ai-hedge-fund/blob/main/hedge_fund/pipeline/clock.py), [ledger.py](https://github.com/virattt/ai-hedge-fund/blob/main/hedge_fund/paper/ledger.py) | Filing availability, information cutoffs and replay integrity |
| Vercel Chatbot | [artifact.tsx](https://github.com/vercel/chatbot/blob/main/components/chat/artifact.tsx), [sheet-editor.tsx](https://github.com/vercel/chatbot/blob/main/components/chat/sheet-editor.tsx) | Versioned outputs beside chat; its sheet surface does not establish formula correctness |
| Glide Data Grid | [repository](https://github.com/glideapps/glide-data-grid) | Number rendering/clipboard code requires explicit financial parsing semantics |
| Langfuse Python | [observe.py](https://github.com/langfuse/langfuse-python/blob/main/langfuse/_client/observe.py) | Scoped tracing and input/output capture controls |
| Langfuse | [prompts.ts](https://github.com/langfuse/langfuse/blob/main/packages/shared/src/domain/prompts.ts), [docker-compose.yml](https://github.com/langfuse/langfuse/blob/main/docker-compose.yml) | Prompt versioning and the actual cost of self-hosted infrastructure |
| LiteLLM | [router.py](https://github.com/BerriAI/litellm/blob/main/litellm/router.py) | Retry/fallback/budget configuration must be reconciled with app consent and provider receipts |
| Hishel | [HTTPX documentation](https://github.com/karpetrosyan/hishel/blob/master/docs/httpx.md) | Default cache policy and user isolation require explicit decisions |
| Portfolio Performance | [IRRTest.java](https://github.com/portfolio-performance/portfolio/blob/master/name.abuchen.portfolio.tests/src/name/abuchen/portfolio/math/IRRTest.java) | Concrete cash-flow/IRR edge cases for independent comparison |
| OpenStock | [market-clock.test.ts](https://github.com/Open-Dev-Society/OpenStock/blob/main/__tests__/market-clock.test.ts) | Session-time cases, not a complete exchange holiday calendar |
| shadcn/ui | [sidebar.tsx](https://github.com/shadcn-ui/ui/blob/main/apps/v4/registry/new-york-v4/ui/sidebar.tsx), [chart.tsx](https://github.com/shadcn-ui/ui/blob/main/apps/v4/registry/new-york-v4/ui/chart.tsx) | Interaction details and chart-version compatibility |
| react-resizable-panels | [useDefaultLayout.ts](https://github.com/bvaughn/react-resizable-panels/blob/main/lib/flex/hooks/useDefaultLayout.ts) | Persisted panes and server-rendering considerations |
## Verification and completeness limits

This handoff is based on source inspection and primary documentation. Upstream projects were not installed or executed, and the official NSE/BSE/transcript services were not integration-tested. No application code, database records, credentials, provider configuration or deployments were changed while preparing it.

The repository survey is broad but not exhaustive. Source reading can reveal integration fit and concrete defects; it cannot establish runtime reliability, financial correctness across all cases, or licensed access to every dataset. The proposed acceptance cases identify what the selected build should prove.

The file is self-contained. It includes the original donor survey, complete inventory, new sources, implementation owners, task definitions, prompts and unresolved questions. No earlier chat response is required to understand the recommendations.
