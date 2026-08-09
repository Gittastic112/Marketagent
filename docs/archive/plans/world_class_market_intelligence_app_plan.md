# World-Class Market Intelligence + Portfolio Intelligence App Plan

## 0. Blunt Product Reframe

This app should not become another portfolio dashboard, another AI summarizer, or another Bloomberg-lite clone.

The strongest version is:

```text
A private, source-backed investment operating system that connects:
portfolio exposure
+ filings
+ news
+ fundamentals
+ valuation
+ narratives
+ thesis assumptions
+ alerts
+ auditability
```

The core question should be:

```text
What changed?
Why does it matter?
How credible is it?
What does it affect in my thesis?
How much money am I exposed to?
What should I verify next?
```

It should **not** answer:

```text
Should I buy or sell this stock?
```

That creates liability, bad incentives, and low-quality behavior. The app should support judgment, not replace it.

---

## 1. Current App Reality Check

Based on the uploaded docs, the app already has a serious source-backed foundation:

- FastAPI backend
- Next.js frontend
- PostgreSQL through Docker
- companies
- sources
- raw documents
- SEC/RSS ingestion
- event extraction
- scoring
- alerts
- thesis notes
- daily briefs
- portfolio records
- holdings
- transactions
- cash balances
- snapshots
- manual company classification
- some portfolio-aware alert design
- security threat model
- AI provenance plan

However, the docs also show a **status inconsistency**:

- `current-state.md` claims many advanced milestones are complete, including DCF, AI provenance, social/narratives, thesis changes, macro, import/export, and alert portfolio impact.
- `README.md`, `roadmap.md`, `execution-runbook.md`, and `portfolio-expansion-plan.md` still describe several of these as next or later work.

Before adding complexity, Codex must verify actual code, not trust docs blindly.

### First Codex rule

```text
Do not trust documentation status claims unless the code, migrations, routes, frontend pages, and tests prove the feature exists.
```

---

## 2. Product Vision

## Name

Working name:

```text
MarketIntel OS
```

Better product description:

```text
A local-first investment intelligence system that unifies portfolio exposure, source-backed market research, SEC filings, fundamentals, DCF valuation, sentiment, narratives, and thesis tracking into one auditable dashboard.
```

## What makes it different

Most existing tools fail in one of four ways:

| Tool type | Problem |
|---|---|
| Broker apps | Show holdings and returns, but weak research and thesis context |
| Portfolio trackers | Show allocation, but not source-backed event intelligence |
| AI finance tools | Summarize text, but hallucinate, lose provenance, and ignore actual exposure |
| Market data terminals | Powerful, expensive, noisy, and not personalized to thesis assumptions |

This app’s edge should be:

```text
portfolio-aware source-backed intelligence
```

Not just:

```text
more charts
more data
more AI
```

---

## 3. North Star User Experience

The app should open into a calm, simple command center.

## Main screen

The user should see:

1. Portfolio value
2. Biggest positions
3. Biggest exposure risks
4. Highest priority alerts
5. Thesis drift warnings
6. Important filing changes
7. Narrative shifts
8. DCF upside/downside summary
9. Data freshness and missing-data warnings

## Ideal dashboard example

```text
Portfolio: $125,430
Today’s key issue: 42% of portfolio exposed to AI semiconductor supply chain.

Top Alert:
NVIDIA 10-Q risk factor language around export restrictions changed materially.
Portfolio exposure: 18.2%
Thesis affected: "GPU demand remains supply constrained, not regulation constrained"
Action: review changed filing section and update assumption if needed.

Concentration Warning:
Top 3 positions = 61% of portfolio.
Semiconductors + AI infrastructure = 44%.
USD exposure = 82%.

Valuation Watch:
AAPL base-case DCF upside: 7%
NVDA reverse DCF implies 24% revenue CAGR for 5 years.
TSLA bear case now below current price by 31%.

Narrative Shift:
"AI capex overbuild" cluster increased 3.4x across news/RSS/social imports this week.
Credibility: medium
Evidence count: 17 sources
```

---

## 4. Design Principles

## 4.1 Simpler UI, deeper system

The system can be complex. The interface should not be.

Bad UI:

```text
Companies | Sources | Raw Documents | Events | Alerts | Thesis Notes | DCF | Social | Narratives | Macro | Processing Runs | etc.
```

Better UI:

```text
Overview
Portfolio
Companies
Research
Valuation
Alerts
Data
Settings
```

Detailed objects can exist in the backend without cluttering the sidebar.

## 4.2 Every conclusion must be traceable

Every alert, summary, sentiment score, DCF output, or thesis-change flag should link back to:

- source record
- company
- timestamp
- calculation assumptions
- model/prompt version if AI-generated
- confidence or limitation note

## 4.3 AI is a worker, not the database

Never make the architecture:

```text
User asks chatbot -> chatbot searches loose sources -> chatbot answers
```

Use:

```text
source -> stored raw document -> event -> score -> alert/brief -> AI explanation with provenance
```

## 4.4 Local-first until security matures

The app stores private financial data. It should remain local-first until:

- authentication exists
- authorization exists
- secrets are managed
- HTTPS is configured
- backups are designed
- broker tokens are encrypted
- audit logs exist

---

## 5. Simplified Navigation Architecture

## Recommended sidebar

```text
1. Overview
2. Portfolio
3. Companies
4. Research
5. Valuation
6. Alerts
7. Data
8. Settings
```

## What each tab contains

### Overview

Purpose:

```text
Tell me what matters now.
```

Sections:

- portfolio value
- daily change, when price data exists
- top owned exposures
- top active alerts
- thesis drift
- data freshness
- recent filings
- recent narrative shifts
- upcoming earnings/calendar events

### Portfolio

Purpose:

```text
Tell me what I own and where I am exposed.
```

Subsections:

- holdings
- transactions
- cash
- allocation
- exposure
- performance
- concentration
- portfolio snapshots
- import/export

### Companies

Purpose:

```text
Tell me everything about one company.
```

Company detail should include:

- overview
- holding status
- portfolio weight
- thesis
- alerts
- filings
- news
- fundamentals
- DCF
- narratives
- sentiment
- notes

### Research

Purpose:

```text
Show me source-backed evidence.
```

Subsections:

- documents
- filings
- news/RSS
- filing diffs
- AI summaries
- saved briefs
- processing history

### Valuation

Purpose:

```text
Build and compare valuations.
```

Subsections:

- DCF models
- financial metrics
- sensitivity tables
- reverse DCF
- peer comparison
- assumptions library

### Alerts

Purpose:

```text
Review what needs attention.
```

Filters:

- owned companies
- watchlist companies
- high portfolio impact
- thesis contradiction
- filing changes
- sentiment shifts
- unreviewed
- false positives
- needs follow-up

### Data

Purpose:

```text
Manage sources and API ingestion.
```

Subsections:

- SEC
- RSS/news
- market prices
- fundamentals
- macro
- social imports
- CSV imports
- provider status
- API usage
- failed runs

### Settings

Purpose:

```text
Control risk, security, and app behavior.
```

Sections:

- API keys
- data providers
- alert thresholds
- scoring weights
- security checks
- backups
- exports
- local environment health

---

## 6. Recommended File Structure Simplification

The app should not collapse into one giant backend route file or dozens of random frontend pages.

## Target root structure

```text
market-intelligence-engine/
├── README.md
├── docker-compose.yml
├── .env.example
├── docs/
├── skills/
├── backend/
├── frontend/
├── scripts/
└── tests/
```

## Backend structure

```text
backend/
├── app/
│   ├── main.py
│   ├── core/
│   │   ├── config.py
│   │   ├── security.py
│   │   └── logging.py
│   ├── db/
│   │   ├── base.py
│   │   └── session.py
│   ├── models/
│   │   ├── company.py
│   │   ├── source.py
│   │   ├── document.py
│   │   ├── event.py
│   │   ├── alert.py
│   │   ├── portfolio.py
│   │   ├── valuation.py
│   │   ├── ai.py
│   │   ├── narrative.py
│   │   └── macro.py
│   ├── api/
│   │   ├── schemas/
│   │   ├── routers/
│   │   └── helpers.py
│   ├── services/
│   │   ├── ingestion/
│   │   ├── scoring/
│   │   ├── portfolio/
│   │   ├── valuation/
│   │   ├── filings/
│   │   ├── ai/
│   │   ├── sentiment/
│   │   ├── narratives/
│   │   └── security/
│   └── providers/
│       ├── sec.py
│       ├── rss.py
│       ├── market_data.py
│       ├── fundamentals.py
│       ├── fred.py
│       ├── reddit.py
│       └── openai.py
├── alembic/
└── tests/
```

## Frontend structure

```text
frontend/
├── app/
│   ├── page.tsx
│   ├── portfolio/
│   ├── companies/
│   ├── research/
│   ├── valuation/
│   ├── alerts/
│   ├── data/
│   ├── settings/
│   └── api/backend/[...path]/route.ts
├── components/
│   ├── layout/
│   ├── charts/
│   ├── cards/
│   ├── tables/
│   ├── forms/
│   ├── alerts/
│   └── empty-states/
├── lib/
│   ├── api.ts
│   ├── calculations.ts
│   ├── formatting.ts
│   └── validation.ts
└── tests/
```

## Important simplification

Backend should have many domain modules. Frontend should have few user-facing tabs.

---

## 7. Cybersecurity Baseline

Security is not optional. This app stores:

- portfolio holdings
- transactions
- cost basis
- thesis notes
- DCF assumptions
- private research
- future API keys
- future broker tokens

## 7.1 Immediate security requirements

### Secrets

- `.env` must never be committed.
- `.env.example` must contain placeholders only.
- API keys must not appear in logs.
- Provider tokens must not be returned to frontend.
- Codex should run secret scans before commits.

### Frontend proxy

The frontend proxy must never become:

```text
/api/backend?url=https://anything.com
```

It should only forward to the known FastAPI backend.

### External URLs

For RSS/source URLs:

- validate URL scheme
- allow only `http` and `https`
- block localhost/private network fetches if public deployment ever happens
- add timeouts
- log failures
- store raw response hash

This reduces SSRF risk.

### Rendering

Never render imported text as trusted HTML.

All of the following are untrusted:

- RSS descriptions
- SEC text
- imported markdown
- social posts
- AI output
- CSV content
- API provider responses

Use escaped/plain text rendering unless a sanitizer is explicitly added.

### CSV import/export

CSV import must:

- validate every row
- reject impossible values
- show row-level errors
- avoid partial silent import
- require preview before commit

CSV export must escape cells starting with:

```text
=
+
-
@
```

This prevents spreadsheet formula injection.

### AI safety

AI output must:

- be stored in `AiOutput`
- include model name
- include prompt version
- include input hash
- link to source record
- include limitations
- require human review status
- never silently overwrite prior output
- never generate buy/sell recommendations

### Broker sync

Broker sync should remain deferred.

When built:

- use official OAuth or token flow
- do not store broker passwords
- encrypt refresh tokens
- support token revocation
- log sync metadata, not raw secrets
- allow read-only scope first

### Public deployment

Do not deploy publicly until these exist:

- authentication
- authorization
- HTTPS
- CSRF review
- CORS policy
- rate limits
- backup/restore
- encrypted secrets
- audit logs
- production logging without sensitive data
- dependency vulnerability scanning

---

## 8. Security Checklist for Codex

Create `skills/security-review/SKILL.md`.

Codex must run this checklist before features involving:

- imports
- external APIs
- AI
- social data
- broker integrations
- deployment
- file upload
- markdown rendering
- CSV export
- secrets

## Required security questions

```text
1. Does this feature touch secrets, private financial data, uploaded files, external URLs, AI, or third-party APIs?
2. What are the untrusted inputs?
3. Where are those inputs validated?
4. Can the feature leak API keys or portfolio data?
5. Can user input trigger arbitrary URL fetches?
6. Can imported text execute as HTML, markdown, CSV formula, or script?
7. Are errors visible enough for debugging but not leaking secrets?
8. Are tests mocked instead of calling live APIs?
9. Are destructive actions blocked or confirmed?
10. Is there a rollback path if import/sync partially fails?
```

---

## 9. Required APIs and Providers

## Provider strategy

Do not start with every API.

Use a staged provider stack:

```text
Stage 1: SEC + RSS + manual prices
Stage 2: one market data API
Stage 3: one fundamentals API
Stage 4: FRED macro API
Stage 5: AI API
Stage 6: official Reddit/social APIs
Stage 7: broker APIs, only after security design
```

## 9.1 SEC EDGAR

Use for:

- company lookup
- CIK lookup
- 10-K, 10-Q, 8-K metadata
- filing text
- filing diffs
- source-backed company research

Needed key:

```text
No API key, but a proper SEC_USER_AGENT is required.
```

Recommended `.env`:

```text
SEC_USER_AGENT="MarketIntelOS/0.1 your_email@example.com"
```

Implementation notes:

- respect SEC fair access behavior
- use timeouts
- store filing URL
- store accession number
- store raw text
- store raw payload
- store content hash
- avoid repeated aggressive requests

## 9.2 RSS feeds

Use for:

- company news
- publication monitoring
- official company IR feeds
- investor relations updates
- regulator updates
- market commentary

Needed key:

```text
None for normal RSS feeds.
```

Good feeds to start:

- company investor relations RSS, where available
- SEC press releases
- Federal Reserve feeds
- reputable financial news feeds with allowed RSS
- industry publications

Rules:

- source reliability must be manually set
- duplicate by URL and content hash
- ambiguous company matches stay unlinked
- do not scrape pages when RSS exists

## 9.3 Market price API

Use for:

- latest price
- historical daily prices
- portfolio market value
- P&L
- charting
- benchmark comparison
- drawdown

Recommended first provider:

```text
Alpha Vantage or Financial Modeling Prep
```

Why:

- simpler to start than institutional feeds
- broad endpoint coverage
- enough for a local personal research app

Alternative if you need stronger price/intraday data:

```text
Polygon / Massive
```

Provider options:

| Provider | Best for | Notes |
|---|---|---|
| Alpha Vantage | cheap/simple prices, fundamentals, macro-ish data, indicators | Good beginner API, but rate limits can be restrictive |
| Financial Modeling Prep | fundamentals, statements, profiles, historical prices, news | Good for DCF/fundamental workflows |
| Finnhub | quotes, fundamentals, news sentiment, economic data | Useful if you want sentiment/news endpoints |
| Polygon/Massive | high quality US market data, historical bars, tickers, corporate actions | Better for data-heavy work; may be overkill early |
| Tiingo | historical prices and fundamentals | Good alternative if pricing/data coverage fits |

Recommended `.env` placeholders:

```text
MARKET_DATA_PROVIDER="alpha_vantage"
ALPHA_VANTAGE_API_KEY=""
FMP_API_KEY=""
FINNHUB_API_KEY=""
POLYGON_API_KEY=""
TIINGO_API_KEY=""
```

Implementation rule:

```text
Build provider adapter interface first. Then plug in one provider.
```

Do not hardwire the app to one vendor.

## 9.4 Fundamentals API

Use for:

- revenue
- EBIT
- EBITDA
- net income
- free cash flow
- capex
- working capital
- shares outstanding
- balance sheet
- debt
- cash
- margins
- ratios
- peer comps

Recommended first provider:

```text
Financial Modeling Prep
```

Reason:

- fundamentals and statements are central to DCF
- easier than parsing everything from SEC XBRL at the start

Alternative:

```text
Alpha Vantage fundamentals
```

Better long-term:

```text
SEC XBRL companyfacts API + provider fallback
```

Long-term ideal:

- SEC XBRL for source-backed official fundamentals
- FMP/Alpha Vantage/Finnhub for convenience and enrichment
- manual override always available

## 9.5 FRED API

Use for:

- interest rates
- CPI
- unemployment
- Fed funds
- treasury yields
- credit spreads
- GDP
- inflation expectations
- macro factor dashboards

Needed key:

```text
FRED_API_KEY=""
```

Use after portfolio analytics and DCF, not before.

## 9.6 OpenAI API

Use for:

- source-backed document summaries
- filing section summaries
- claim extraction
- thesis contradiction explanation
- narrative label generation
- DCF assumption explanation
- query interface over stored records

Required:

```text
OPENAI_API_KEY=""
OPENAI_MODEL=""
```

Rules:

- never send private portfolio/thesis data unless feature explicitly says so
- log model name and prompt version
- store input hash
- store source links
- store limitations
- mocked tests only
- no autonomous buy/sell recommendation

## 9.7 Reddit API

Use for:

- official Reddit data where allowed
- ticker discussion monitoring
- community narrative tracking
- sentiment and topic clustering

Required:

```text
REDDIT_CLIENT_ID=""
REDDIT_CLIENT_SECRET=""
REDDIT_USER_AGENT=""
```

Rules:

- official API only
- no HTML scraping
- store URL, subreddit, timestamp, raw text, hash
- treat social sentiment as attention data, not truth

## 9.8 X/Twitter API

Use only later.

Required:

```text
X_API_KEY=""
X_API_SECRET=""
X_BEARER_TOKEN=""
```

Rules:

- official API or licensed provider only
- no browser scraping
- no bypassing terms
- cache minimally
- store source links and timestamps

## 9.9 Broker APIs

Defer.

Possible later providers:

- Alpaca
- Interactive Brokers
- Plaid Investments, depending on account/institution coverage
- SnapTrade
- Zerodha Kite Connect, if India portfolio support matters
- Upstox, Groww, or other Indian brokers only if official APIs and terms allow

Rules:

- read-only first
- OAuth/token only
- no password storage
- encrypt refresh tokens
- sync logs
- user-controlled disconnect

---

## 10. What to Download / Install

## Required local tools

Already implied by project:

```text
VS Code
Git
GitHub
Docker Desktop
Python 3.11+
Node.js LTS
npm
```

## Helpful VS Code extensions

```text
Python
Pylance
ESLint
Prettier
Docker
Markdown All in One
GitLens
```

## Backend packages likely needed later

Only add when needed:

```text
pandas
numpy
httpx
pydantic
python-multipart
beautifulsoup4
lxml
defusedxml
tenacity
cryptography
scikit-learn
```

Notes:

- `defusedxml` is useful for safer XML parsing.
- `tenacity` helps with controlled retries.
- `cryptography` is needed before storing encrypted tokens.
- Do not add heavy NLP/vector libraries until narrative clustering actually needs them.

## Frontend packages likely needed

For world-class charts and UI:

```text
recharts
lucide-react
clsx
date-fns
```

Possible later:

```text
tanstack/react-table
zod
react-hook-form
```

Avoid adding a giant component framework unless the UI is becoming unmanageable.

## Security/dev tooling

```text
detect-secrets
pip-audit
npm audit
ruff
mypy
eslint
prettier
pytest
```

Potential later:

```text
bandit
semgrep
trivy
snyk
```

Start simple:

```text
pytest
npm test
npm run typecheck
pip-audit
npm audit
detect-secrets scan
```

---

## 11. Codex Skills to Create

Create a `/skills` folder at the project root.

```text
skills/
├── source-backed-development/
├── database-migration/
├── portfolio-math/
├── financial-valuation/
├── api-integration/
├── security-review/
├── frontend-dashboard/
├── ai-provenance/
├── filing-intelligence/
├── sentiment-narratives/
├── testing-discipline/
└── beginner-reporting/
```

Each skill should have a `SKILL.md`.

## 11.1 source-backed-development

Purpose:

```text
Prevent unsourced intelligence.
```

Rules:

- every intelligence output links to source objects
- store URL, timestamp, raw text/payload, hash
- no unsupported conclusions
- no buy/sell recommendations
- preserve human review state

## 11.2 database-migration

Purpose:

```text
Keep schema changes safe.
```

Rules:

- inspect current models first
- add SQLAlchemy model
- add Alembic migration
- update schemas
- update routes
- add tests
- report `alembic upgrade head`
- no destructive migration without explicit approval

## 11.3 portfolio-math

Purpose:

```text
Make returns, P&L, weights, and exposures correct.
```

Must test:

- cost basis
- average cost
- market value
- unrealized P&L
- realized P&L
- cash balance effects
- transaction reversal
- splits
- bonus shares
- dividends
- fees
- taxes
- multi-currency placeholder behavior

## 11.4 financial-valuation

Purpose:

```text
Make DCF and valuation math defensible.
```

Must test:

- revenue growth
- operating margin
- tax rate
- reinvestment
- free cash flow
- WACC
- terminal value
- net debt
- share count
- fair value per share
- sensitivity table
- reverse DCF

## 11.5 api-integration

Purpose:

```text
Add APIs without hardcoded keys or messy provider logic.
```

Rules:

- adapter pattern
- `.env` config
- mocked tests
- timeout
- retry policy
- provider error handling
- `ProcessingRun`
- no secrets in logs
- raw response preservation where legally allowed

## 11.6 security-review

Purpose:

```text
Block dangerous feature additions.
```

Required for:

- imports
- external URLs
- API keys
- AI
- broker sync
- social data
- deployment
- file upload

## 11.7 frontend-dashboard

Purpose:

```text
Keep UI simple and useful.
```

Rules:

- reduce sidebar clutter
- use cards, tables, charts, empty states
- no raw backend-object dumping on main views
- advanced controls behind detail pages
- charts must explain the decision they support

## 11.8 ai-provenance

Purpose:

```text
AI must be auditable.
```

Rules:

- `AiOutput` table
- source link
- model name
- prompt version
- input hash
- generated timestamp
- limitations
- review status
- no silent overwrite

## 11.9 filing-intelligence

Purpose:

```text
Move from filing diff to filing understanding.
```

Features:

- section parser
- Item 1A
- MD&A
- liquidity
- legal proceedings
- segment discussion
- section-level diffs
- materiality tags

## 11.10 sentiment-narratives

Purpose:

```text
Track what the market is starting to believe.
```

Rules:

- official APIs or manual imports only
- social = attention, not truth
- separate sentiment, credibility, and narrative velocity
- cluster claims
- show supporting and contradicting sources

## 11.11 testing-discipline

Purpose:

```text
No feature without tests.
```

Workflow:

```text
inspect -> failing tests -> smallest implementation -> run tests -> report
```

## 11.12 beginner-reporting

Purpose:

```text
Codex must explain what changed in plain English.
```

Every Codex result ends with:

```text
What changed
Files changed
Commands run
Tests passed/failed
Manual browser steps
Known limitations
Next task
```

---

## 12. Interactive Graphs and Visualizations

Charts should not be decoration. Each chart should answer a question.

## 12.1 Portfolio charts

Use:

```text
recharts
```

Charts:

| Chart | Question answered |
|---|---|
| Portfolio value line chart | Is my portfolio growing over time? |
| Allocation pie/donut | What do I own? |
| Sector bar chart | Where am I concentrated? |
| Industry treemap | What hidden clusters exist? |
| Position weight bar chart | Which holdings dominate risk? |
| Unrealized P&L waterfall | Where did gains/losses come from? |
| Cash vs invested area chart | Am I underinvested or fully exposed? |
| Drawdown chart | How bad have portfolio declines been? |
| Contribution chart | Which holdings drove performance? |

## 12.2 Company charts

Charts:

- price history
- revenue history
- margin history
- free cash flow history
- debt/cash history
- valuation multiple history
- filing change timeline
- alert timeline
- thesis drift timeline

## 12.3 DCF charts

Charts:

- bear/base/bull valuation bars
- sensitivity heatmap
- reverse DCF implied growth
- FCF forecast line chart
- revenue/margin assumption chart
- terminal value share of valuation warning

## 12.4 Narrative charts

Charts:

- narrative velocity over time
- source credibility mix
- positive/negative/neutral sentiment trend
- supporting vs contradicting claims
- attention spike chart

## 12.5 Macro charts

Charts:

- rates over time
- inflation over time
- credit spreads
- unemployment
- yield curve
- macro exposure map

## 12.6 UI rule

Every chart must have:

```text
title
plain-English interpretation
data freshness label
source/provider label
empty state
```

Bad:

```text
A beautiful unlabeled chart.
```

Good:

```text
Sector Exposure: Semiconductors are 41% of invested value.
Data: manual holdings + latest manual prices.
Warning: NVDA price is stale by 12 days.
```

---

## 13. Required Feature Roadmap

## Phase 0: Codebase Reality Audit

Goal:

```text
Resolve docs/code mismatch before building more.
```

Codex tasks:

- inspect models
- inspect migrations
- inspect API routers
- inspect frontend pages
- inspect tests
- produce feature matrix

Output table:

```text
Feature | Docs say | Code proves | Tests prove | Browser verified | Status
```

Acceptance criteria:

- one true `current-state.md`
- stale docs corrected
- no duplicate roadmap confusion

---

## Phase 1: UI Simplification

Goal:

```text
Make the app easier to use before adding more tabs.
```

Tasks:

- reduce sidebar to 8 main tabs
- move raw backend tables under Data or Research
- create overview cards
- add empty states
- add consistent page headers
- add reusable chart/card/table components
- remove duplicate forms where possible
- make detail pages do the heavy lifting

Acceptance criteria:

- no more than 8 sidebar items
- overview page tells user what matters
- raw objects are still accessible but not dominant

---

## Phase 2: Security Hardening

Goal:

```text
Make future complexity safe.
```

Tasks:

- add `backend/app/core/security.py`
- add URL validation helper
- add SSRF guard placeholder
- add safe text rendering conventions
- add CSV formula escaping helper
- add secret scan docs
- add security checklist test/doc
- add provider key redaction in logs
- add error response policy

Acceptance criteria:

- security tests exist for URL validation and CSV export escaping
- no API keys in logs
- proxy cannot fetch arbitrary URLs
- imported text treated as untrusted

---

## Phase 3: Provider Adapter Layer

Goal:

```text
Make APIs swappable and controlled.
```

Tasks:

- create `backend/app/providers/`
- define provider interface
- add provider registry
- add mock provider
- add API usage/audit table if needed
- route all external API calls through providers
- add timeout/retry policy
- add `ProcessingRun` integration

Acceptance criteria:

- one provider can be swapped without touching business logic
- tests use mocked provider
- provider errors show clear UI messages

---

## Phase 4: Manual Price + Portfolio Valuation

Goal:

```text
Turn holdings into actual portfolio value.
```

Tasks:

- verify or add `MarketPrice`
- latest price service
- valuation service
- stale price warning
- portfolio value card
- holding value table
- position weights
- unrealized P&L
- cash integration
- transaction cash effects

Acceptance criteria:

- holdings show market value
- portfolio shows total value
- stale/missing prices are visible
- buy/sell/deposit/withdrawal/dividend/fee/tax effects are handled or explicitly marked unsupported

---

## Phase 5: Portfolio Analytics

Goal:

```text
Show where risk actually is.
```

Tasks:

- sector exposure
- industry exposure
- country exposure
- currency exposure
- asset type exposure
- ETF exposure rules
- concentration score
- diversification warnings
- top position risk
- hidden exposure tags

Acceptance criteria:

- user can see least diversified areas
- exposure charts are interactive
- warnings are deterministic and explainable

---

## Phase 6: Fundamentals + DCF

Goal:

```text
Make valuation first-class.
```

Tasks:

- financial statement periods
- metrics table
- manual metric entry
- provider import later
- DCF assumptions
- DCF output
- bear/base/bull
- sensitivity heatmap
- reverse DCF
- valuation history
- assumptions audit log

Acceptance criteria:

- DCF math is deterministic and tested
- assumptions are saved
- outputs link to assumptions
- user can compare scenarios

---

## Phase 7: SEC Filing Intelligence

Goal:

```text
Make filings useful, not just stored.
```

Tasks:

- filing section parser
- section-level diff
- Item 1A diff
- MD&A diff
- liquidity diff
- legal proceedings diff
- segment discussion diff
- materiality score
- company filing timeline
- changed-section alerts

Acceptance criteria:

- user can see exactly what changed
- filing alert links to changed section
- parser failures are visible, not hidden

---

## Phase 8: AI With Provenance

Goal:

```text
Use AI safely.
```

First AI features:

1. raw document summary
2. filing section summary
3. changed-section explanation
4. thesis contradiction explanation
5. narrative label suggestion

Tasks:

- verify/add `AiOutput`
- provider adapter for OpenAI
- prompt version registry
- input hash
- source links
- limitations field
- review status
- retry policy
- mocked tests

Acceptance criteria:

- every AI output is source-linked
- user can review AI outputs
- regenerated outputs create new records
- no buy/sell recommendation

---

## Phase 9: Sentiment + Narrative Tracking

Goal:

```text
Track attention and belief formation.
```

Tasks:

- manual social import
- Reddit API later
- X API later
- sentiment scoring
- topic extraction
- narrative claims
- narrative clusters
- narrative velocity
- contradiction tracking
- portfolio exposure link

Acceptance criteria:

- social data is source-linked
- sentiment is separate from credibility
- narratives show supporting and opposing sources
- no prohibited scraping

---

## Phase 10: Portfolio-Aware Alerts

Goal:

```text
Prioritize what matters to the user’s money and thesis.
```

Tasks:

- `AlertPortfolioImpact`
- portfolio priority score
- ownership filter
- exposure amount
- affected thesis assumptions
- valuation sensitivity
- narrative velocity adjustment
- alert review feedback loop

Acceptance criteria:

- alert rank changes when position size changes
- watchlist alerts remain visible
- owned high-exposure alerts are clearly prioritized

---

## Phase 11: Import / Export

Goal:

```text
Make the app usable with real portfolio history.
```

Tasks:

- holdings CSV import
- transaction CSV import
- price CSV import
- DCF export
- memo export
- CSV validation preview
- row-level errors
- duplicate detection
- rollback on failed import

Acceptance criteria:

- user can import real transactions safely
- import preview prevents bad data from polluting DB
- exported CSV is formula-injection safe

---

## Phase 12: Macro + Factor Exposure

Goal:

```text
Add broader risk context.
```

Tasks:

- FRED integration
- macro series
- macro observations
- company exposure tags
- portfolio factor map
- rate sensitivity
- inflation sensitivity
- FX exposure
- oil/commodity sensitivity

Acceptance criteria:

- macro charts exist
- portfolio exposure to macro factors is visible
- source/provider labels are shown

---

## Phase 13: Broker Sync

Goal:

```text
Reduce manual entry after security is ready.
```

Only after:

- auth design
- token encryption
- read-only OAuth/token handling
- audit logs
- backup system

Tasks:

- read-only broker integration
- official API only
- token encryption
- sync logs
- manual reconciliation
- disconnect flow
- no trading execution

Acceptance criteria:

- no password storage
- user controls sync
- imported records remain auditable

---

## 14. Features That Would Make This World-Class

## 14.1 Thesis graph

Turn thesis notes into structured assumptions.

Example:

```text
Thesis: NVIDIA can sustain premium margins.
Assumptions:
1. GPU demand remains supply constrained.
2. Hyperscaler capex remains strong.
3. Export controls do not materially impair data center revenue.
4. Competition from ASICs remains manageable.
```

Every alert maps to one or more assumptions.

## 14.2 Filing change monitor

Not just:

```text
A 10-K was filed.
```

But:

```text
The company added new risk language around customer concentration.
This appears in Item 1A.
The language did not exist last year.
Portfolio exposure: 9.7%.
Relevant thesis assumption: revenue durability.
```

## 14.3 Reverse DCF

Show what the market price implies.

Example:

```text
Current price implies:
Revenue CAGR: 18%
Terminal EBIT margin: 27%
WACC: 9%
Terminal growth: 3%
```

This is often more useful than a normal DCF.

## 14.4 Data freshness panel

Most tools hide stale data. This app should show it.

```text
AAPL price: fresh, 1 day old
MSFT fundamentals: stale, 94 days old
NVDA filing text: fresh
Reddit sentiment: not configured
DCF: stale, last updated 4 months ago
```

## 14.5 Contradiction engine

Track when sources disagree.

Example:

```text
Company says demand is strong.
Customer forum complaints suggest cancellations.
Analysts cut estimates.
Social sentiment is negative but low credibility.
```

## 14.6 Personal exposure map

Not generic market news.

```text
Your portfolio is exposed to:
AI capex
USD strength
US rates
India consumer discretionary
semiconductor export controls
cloud infrastructure spending
```

## 14.7 Decision journal

Every time the user updates a thesis or DCF assumption, save:

- old assumption
- new assumption
- reason
- source
- date
- related alert
- portfolio impact

This becomes a private investment memory.

## 14.8 Research inbox

A queue where all new source-backed information lands.

Each item can be marked:

- reviewed
- useful
- false positive
- thesis relevant
- valuation relevant
- ignore source
- create task
- create thesis change
- create DCF update

## 14.9 Model risk warnings

DCF page should warn:

- terminal value is too much of valuation
- margin assumption is above historical range
- growth assumption exceeds industry history
- WACC sensitivity is high
- stale financials
- missing dilution/share count update

## 14.10 Evidence-first chat

Later, a chat interface can exist. But it should only answer from stored records.

Bad:

```text
Ask anything about Tesla.
```

Good:

```text
Ask your stored Tesla research, filings, thesis notes, DCFs, and alerts.
```

---

## 15. Things Not to Build Yet

Do not build now:

- buy/sell recommendations
- automated trading
- broker sync
- public deployment
- mobile app
- options flow
- real-time alerts
- X/Twitter scraping
- Reddit scraping
- vector database
- LangChain-heavy architecture
- Kubernetes
- Kafka
- team accounts
- billing

These are distractions before the core product is stable.

---

## 16. Immediate Codex Execution Plan

## Prompt 1: Reality audit

```text
Read AGENTS.md, README.md, docs/current-state.md, docs/roadmap.md,
docs/execution-runbook.md, docs/portfolio-expansion-plan.md,
docs/database-schema.md, docs/security-threat-model.md, backend/app,
frontend/app, backend/alembic, and tests.

Do not add features yet.

Create docs/feature-reality-audit.md with a table:
Feature | Claimed in docs | Code exists | Migration exists | API exists | Frontend exists | Tests exist | Browser verification needed | Actual status

Identify contradictions across docs.

Then update docs/current-state.md only if the audit proves it is wrong.
Do not delete historical rationale.
Do not build new product features.
```

## Prompt 2: UI simplification

```text
Using docs/feature-reality-audit.md, simplify the frontend navigation.

Target sidebar:
- Overview
- Portfolio
- Companies
- Research
- Valuation
- Alerts
- Data
- Settings

Do not delete existing pages. Move links into grouped sections where needed.
Create reusable page section/card/table/chart placeholder components if useful.
Add empty states and clearer page descriptions.

Run frontend tests and TypeScript checks.
Report files changed and manual browser test steps.
```

## Prompt 3: Security hardening

```text
Read docs/security-threat-model.md.

Implement the security utilities needed before more APIs/imports:
- URL validation helper for external source URLs.
- CSV formula escaping helper.
- provider secret redaction helper.
- tests for each helper.
- documentation note in docs/security-threat-model.md if needed.

Do not add auth.
Do not add broker sync.
Do not add external APIs.
Do not change public behavior except safer validation where directly relevant.
```

## Prompt 4: Provider adapter foundation

```text
Create a provider adapter layer for future market data and fundamentals APIs.

Add:
- backend/app/providers/base.py
- backend/app/providers/registry.py
- backend/app/providers/mock_market_data.py
- provider config placeholders in settings.
- mocked tests.

Do not call live APIs.
Do not add actual Alpha Vantage/FMP/Finnhub/Polygon integration yet.
The goal is architecture only.
```

## Prompt 5: Manual prices and portfolio valuation

```text
Implement manual market prices and deterministic portfolio valuation.

Add or verify:
- MarketPrice model and migration.
- CRUD routes.
- latest price lookup service.
- portfolio valuation service.
- holdings market value.
- cost basis.
- unrealized P&L.
- position weight.
- stale price warning.
- frontend portfolio valuation summary and holdings table update.
- backend math tests and frontend payload/type tests.

Do not add live market APIs.
Do not add DCF.
Do not add AI.
```

---

## 17. Final Product Standard

A world-class version of this app should meet this bar:

```text
I can open it and immediately know:
1. What I own.
2. Where I am overexposed.
3. What changed today.
4. Which changes matter because I own the company.
5. Which changes matter because they affect my thesis.
6. Which valuations are stale or stretched.
7. Which narratives are accelerating.
8. Which data is stale, missing, or low-confidence.
9. What evidence supports every alert.
10. What I need to review next.
```

If a feature does not serve one of those, it is probably noise.

---

## 18. Preferred Build Order Summary

```text
0. Reality audit
1. UI simplification
2. Security utilities
3. Provider adapter layer
4. Manual prices
5. Portfolio valuation
6. Portfolio analytics charts
7. Fundamentals
8. DCF
9. SEC section intelligence
10. AI summaries with provenance
11. Sentiment and narrative tracking
12. Portfolio-aware alert ranking
13. Import/export
14. Macro/factor exposure
15. Broker sync later
```

This is the right order because it keeps the product useful, auditable, secure, and personalized before adding high-risk automation.
