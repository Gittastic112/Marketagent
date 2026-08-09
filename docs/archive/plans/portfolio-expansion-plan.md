# Portfolio Tracker Expansion Implementation Plan (Completed)

> [!NOTE]  
> **Status: Completed and Superseded.**
> Milestones A through K in this document have been fully implemented on the backend and frontend. The future direction of the app is now governed by `docs/world_class_market_intelligence_app_plan.md`. This file remains for historical reference.

**Goal:** Expand the local-first Market Intelligence Engine into a source-backed portfolio intelligence system.

**Architecture:** Keep the existing source-backed evidence chain and add a portfolio layer before AI, social sentiment, DCFs, or broker integrations. Portfolio holdings and exposure should become an additional ranking layer on top of existing company, document, event, alert, thesis, scoring, and daily brief records.

**Tech Stack:** Next.js frontend, FastAPI backend, PostgreSQL, SQLAlchemy, Alembic, pytest, Node test runner, Docker Compose.

---

## Product Direction

The product is now a local-first market intelligence and portfolio tracker.

The core question expands from:

```text
What changed, why does it matter, and how credible is it?
```

to:

```text
What changed, why does it matter, how credible is it, does it affect my thesis, and how exposed am I through my portfolio?
```

The next real product layer is:

```text
portfolio holdings -> market value -> exposure analytics -> portfolio-aware intelligence
```

Do not jump to AI, social scraping, broker sync, options flow, or trading recommendations before the portfolio foundation is locally verified and stable.

## Security Baseline

All expansion work must follow these rules:

- Do not hardcode API keys, broker credentials, model keys, or tokens.
- Store secrets only in `.env` or an approved secret store later.
- Never commit `.env`.
- Do not store broker passwords directly.
- Broker integrations, when built later, must use official OAuth or token flows.
- Do not scrape sites that prohibit scraping or unauthorized automated access.
- Prefer official APIs, licensed data, approved exports, or manual imports.
- Tests must not call live external APIs.
- Imported CSV/markdown/text must be validated and treated as untrusted input.
- User-provided URLs must not become open SSRF primitives.
- AI outputs must always link to source records and must not produce buy/sell recommendations.
- The app remains local-first until auth, deployment, and production security are explicitly designed.

## Milestone A: Verify Current App

Goal: prove the existing SEC/RSS/local workflow works before adding portfolio tables.

- [ ] Run migrations against local PostgreSQL.
- [ ] Confirm the local browser app opens.
- [ ] Add a company using ticker lookup.
- [ ] Confirm SEC title and CIK populate.
- [ ] Preview 10-K, 10-Q, and 8-K filings.
- [ ] Import one selected filing.
- [ ] Confirm a `RawDocument` is created.
- [ ] Confirm event extraction runs.
- [ ] Confirm scoring runs.
- [ ] Confirm alert generation works.
- [ ] Confirm daily brief save works.
- [ ] Confirm RSS feed ingestion works on at least three real feeds.
- [ ] Record failures in `docs/known-issues.md`.

Acceptance criteria:

- Current app works before portfolio features start.
- Existing docs match the actual code.
- No new product scope is added in this milestone.

## Milestone B: Portfolio MVP

Goal: add manual portfolio tracking without market prices or external broker integrations.

Status: mostly implemented in repo. Backend tables, migrations, schemas, CRUD
routes, and tests exist. The `/portfolio` page supports manual portfolio,
holding, and transaction records. `/portfolio/[id]` and frontend controls for
cash balances and snapshots are not built yet.

### Backend Tables

- `Portfolio`
- `PortfolioHolding`
- `PortfolioTransaction`
- `PortfolioCashBalance`
- `PortfolioSnapshot`

### Backend Routes

- `POST /portfolios`
- `GET /portfolios`
- `GET /portfolios/{id}`
- `PATCH /portfolios/{id}`
- `DELETE /portfolios/{id}`
- `POST /portfolio-holdings`
- `GET /portfolio-holdings`
- `GET /portfolio-holdings/{id}`
- `PATCH /portfolio-holdings/{id}`
- `DELETE /portfolio-holdings/{id}`
- `POST /portfolio-transactions`
- `GET /portfolio-transactions`
- `GET /portfolio-transactions/{id}`
- `PATCH /portfolio-transactions/{id}`
- `DELETE /portfolio-transactions/{id}`
- `POST /portfolio-cash-balances`
- `GET /portfolio-cash-balances`
- `GET /portfolio-cash-balances/{id}`
- `PATCH /portfolio-cash-balances/{id}`
- `DELETE /portfolio-cash-balances/{id}`
- `POST /portfolio-snapshots`
- `GET /portfolio-snapshots`
- `GET /portfolio-snapshots/{id}`
- `PATCH /portfolio-snapshots/{id}`
- `DELETE /portfolio-snapshots/{id}`

### Frontend

- `/portfolio`
- `/portfolio/[id]` not built yet
- portfolio create form
- holding create form
- transaction create form
- holdings table
- transactions table
- cash balance and snapshot frontend controls not built yet

### Tests

- create/list/get/update/delete portfolio
- create/list/update/delete holding
- create/list/update/delete transaction
- prevent unsafe portfolio deletion while linked records exist, or block with a clear conflict
- validate quantity, price, and fees
- validate transaction type
- frontend payload conversion tests

Acceptance criteria:

- User can create a portfolio.
- User can add holdings.
- User can add transactions.
- User can view holdings and transactions.
- No market data dependency exists yet.

## Milestone C: Company Classification

Goal: make diversification analytics possible.

Status: implemented in repo. Company records now support manual classification
fields, and the Companies list/detail UI exposes them for editing and review.

Add manual classification fields to `Company`:

- `country`
- `region`
- `currency`
- `asset_type`
- `security_type`
- `market_cap_category`
- `is_etf`
- `etf_provider`

Acceptance criteria:

- Every holding can be classified by sector, industry, country, currency, and asset type.
- Frontend lets the user edit these fields.
- No external lookup is required.

Current limitation:

- Classification is manual. No external enrichment or automatic classifier has
  been added.

## Milestone D: Manual Market Prices And Valuation

Goal: turn holdings into market value without live APIs.

Add:

- `MarketPrice`
- manual price entry endpoint
- latest price lookup service
- portfolio valuation service
- stale price warning

Acceptance criteria:

- User can enter prices manually.
- Portfolio page calculates total value.
- Holdings show market value, cost basis, unrealized P&L, and weight.
- Missing prices do not crash the page.

## Milestone E: Portfolio Analytics Dashboard

Goal: answer what the user owns and where risk is concentrated.

Add:

- portfolio value summary
- cash
- invested value
- unrealized P&L
- top positions
- top gains/losses
- sector exposure
- industry exposure
- country exposure
- currency exposure
- asset type exposure
- concentration score
- diversification warnings

Acceptance criteria:

- Portfolio page shows exposure and concentration clearly.
- Calculations are deterministic and tested.

## Milestone F: Fundamentals And DCF

Goal: support valuation work.

Add fundamentals first:

- `FinancialStatementPeriod`
- `FinancialMetric`
- manual financial metric endpoints
- company fundamentals page/table

Then add DCF:

- `ValuationModel`
- `DcfAssumptionSet`
- `DcfOutput`
- `ValuationSnapshot`
- deterministic DCF calculation service
- bear/base/bull scenarios
- sensitivity table
- reverse DCF later

Acceptance criteria:

- User can store financial metrics.
- User can enter DCF assumptions.
- App saves assumptions and outputs.
- DCF math is tested.

## Milestone G: SEC Filing Intelligence

Goal: move from whole-document text diff to section-aware filing analysis.

Add:

- `FilingSection`
- `FilingSectionDiff`
- deterministic section parser
- section-level diff service
- company filing view for parsed sections and changed sections

Acceptance criteria:

- Imported filings can be parsed into sections when text exists.
- Comparable sections can be diffed.
- Parser fails gracefully and does not invent missing sections.

## Milestone H: AI With Provenance

Goal: introduce AI only after source and portfolio context are stable.

First AI feature:

- source-backed raw document summaries

Add:

- `AiOutput`
- model name
- prompt version
- input hash
- output text
- limitations
- confidence label
- human review status
- source links

Acceptance criteria:

- Every AI output links to source records.
- Tests use mocked model responses.
- No buy/sell recommendations are generated.

## Milestone I: Compliant Sentiment And Narratives

Goal: add social and narrative intelligence legally and conservatively.

First version:

- manual/imported social posts
- official APIs or approved exports only
- no HTML scraping of Reddit, X/Twitter, or forums
- rule-based sentiment before AI

Future tables:

- `SocialPost`
- `SentimentScore`
- `NarrativeClaim`
- `NarrativeMention`
- `NarrativeCluster`
- `NarrativeClusterMember`

Acceptance criteria:

- User can manually import social posts.
- Source URL, raw text, payload, content hash, and timestamps are preserved.
- No illegal or brittle scraping is introduced.

## Milestone J: Thesis And Portfolio-Aware Alerts

Goal: connect evidence to thesis assumptions and portfolio exposure.

Add:

- `ThesisAssumption`
- `ThesisChange`
- `AlertPortfolioImpact`
- portfolio-aware alert priority
- owned/watchlist alert filters
- thesis drift score

Acceptance criteria:

- User can break thesis into assumptions.
- Events can be linked to assumptions.
- Alerts for owned companies show portfolio exposure.
- User remains in control of thesis changes.

## Milestone K: Macro, Import/Export, And Later Integrations

Add only after portfolio MVP is stable:

- `ExposureTag`
- `CompanyExposureTag`
- `MacroSeries`
- `MacroObservation`
- holdings CSV import/export
- transactions CSV import/export
- price CSV import/export
- investment memo export

Broker integrations are later convenience work, not core product foundation.

Security rule:

- Do not store broker credentials directly.
- Use official APIs and OAuth/token flows only.

## Explicit Non-Goals For Now

- trading execution
- buy/sell recommendations
- Twitter/X scraping
- Reddit HTML scraping
- broker account syncing
- options flow
- vector database
- LangChain-heavy architecture
- Kubernetes
- Kafka
- multi-user auth
- payments
- production SaaS deployment
