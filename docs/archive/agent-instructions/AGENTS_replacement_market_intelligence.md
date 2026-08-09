# AGENTS.md Replacement: Market Intelligence Engine Agent Operating Manual

**Purpose:** Replace the existing `AGENTS.md` with a sharper, more operational version for Codex, Antigravity, Claude Code, Cursor, or any AI coding agent working in this repository.

**Core idea:** This file is not a product brochure. It is an operating manual for agents. It should prevent common AI-agent failures: giant diffs, fake completed features, unsafe migrations, frontend mock data presented as real, fragile API changes, undocumented security risks, and feature creep.

---

# 0. How To Use This File

## 0.1 Placement

Place this file at the repository root as:

```text
AGENTS.md
```

If the repo later becomes large, create narrower `AGENTS.md` files inside specific directories, for example:

```text
backend/AGENTS.md
frontend/AGENTS.md
docs/AGENTS.md
```

More specific directory instructions should override root instructions for files inside that directory.

## 0.2 Agent instruction priority

When working in this repo, follow instructions in this order:

1. User's direct request in the current task
2. This `AGENTS.md`
3. More specific nested `AGENTS.md` files, if present
4. Current docs in `docs/`
5. Existing code and tests
6. General framework conventions

If instructions conflict, stop and report the conflict. Do not guess silently.

---

# 1. Project Summary

This repo is a local-first Market Intelligence Engine and portfolio tracker for public equity research.

It combines:

- company watchlists
- SEC filings
- RSS/news ingestion
- raw document storage
- event extraction
- explainable scoring
- alerts
- thesis notes
- portfolio holdings and transactions
- manual or provider-backed market prices
- valuation/DCF workflows
- data health monitoring
- future source-backed AI research

The core product question is:

```text
What changed, why does it matter, how credible is it, does it affect my thesis, and how exposed am I through my portfolio?
```

The product should become a source-backed investment cockpit, not a generic AI chatbot or a fake Bloomberg clone.

---

# 2. Product North Star

Every major feature should help answer at least one of these:

1. What changed since I last checked?
2. What evidence supports the claim?
3. How reliable is the information?
4. Is the data fresh, stale, partial, mocked, or missing?
5. Does this affect my thesis?
6. Does this affect a portfolio holding or exposure?
7. What assumptions drive the valuation?
8. What would falsify the investment thesis?
9. What should I inspect next?

If a proposed feature does not help answer one of these questions, do not build it without explicit approval.

---

# 3. Non-Negotiable Product Rules

## 3.1 No fake intelligence

Do not present mock, placeholder, hardcoded, guessed, or synthetic data as real.

If data is mocked, show a visible label:

```text
Mock Data
```

If a backend endpoint is missing, the frontend must show:

```text
Not available yet
```

or:

```text
Backend endpoint not implemented
```

Do not invent frontend numbers to make the UI look complete.

## 3.2 No buy/sell recommendations

The app may show:

- valuation attractiveness
- market regime support
- risk warnings
- evidence strength
- thesis support or contradiction
- decision readiness
- portfolio impact

The app must not say:

```text
Buy this stock
Sell this stock
You should buy now
Guaranteed upside
```

Acceptable language:

```text
Market structure appears supportive for cautious accumulation.
```

```text
The setup is incomplete because the latest filing has not been reviewed.
```

```text
The model suggests upside under the user's assumptions, but terminal value dependence is high.
```

## 3.3 Every claim must have a type

Any meaningful insight should be labeled as one of:

- Fact
- Source Summary
- Calculation
- User Assumption
- AI Interpretation
- Estimate
- Mock Data

## 3.4 Every important output needs traceability

For alerts, summaries, scores, DCF outputs, narrative claims, and AI outputs, preserve or display:

- source
- timestamp
- data freshness
- calculation basis
- confidence or uncertainty
- linked raw document or input assumption
- what would change the conclusion where applicable

---

# 4. Documentation Source of Truth

## 4.1 Docs reading order

Before major changes, read these files:

```text
docs/00-current-state.md
docs/01-product-brief.md
docs/02-architecture.md
docs/03-database-schema.md
docs/04-data-sources-and-ingestion.md
docs/05-scoring-framework.md
docs/06-security-threat-model.md
docs/07-local-development.md
docs/08-execution-runbook.md
docs/10-design-brief.md
```

Also read these expansion supplements if present:

```text
docs/world_class_expansion_supplement_master_plan.md
docs/next_steps_world_class_market_intelligence_plan.md
```

If they live outside `docs/`, search the repo before assuming they are absent.

## 4.2 Code beats docs

Docs may be stale. The agent must verify the actual code before claiming a feature exists.

For any requested change, inspect:

```text
backend/app/
backend/alembic/versions/
backend/tests/
frontend/app/
frontend/components/
frontend/lib/
frontend/types/
docker-compose.yml
.env.example
```

Do not rely only on `README.md` or planning docs.

## 4.3 Update docs only when reality changes

When code changes affect behavior, update the relevant docs in the same task.

But do not rewrite all docs casually. Update only the docs affected by the change.

---

# 5. Standard Agent Workflow

Every coding task must follow this sequence.

## 5.1 Step 1: Restate the task briefly

State what you are about to do in one or two sentences.

Example:

```text
I will add the API response envelope to the health endpoint and one low-risk read endpoint, then update the frontend fetcher to tolerate both old and new response shapes.
```

## 5.2 Step 2: Inspect before editing

Before making changes, inspect relevant files.

Minimum inspection by task type:

| Task type | Files to inspect |
|---|---|
| Backend API | router, schema, service, model, tests |
| Database change | model, existing migrations, current schema docs, tests |
| Frontend page | page file, components, fetch client, types, existing styles |
| Ingestion | provider/service, processing run model, tests, security doc |
| DCF/valuation | valuation models, service, tests, finance formulas |
| Security | `.env.example`, config, logs, proxy, routes, user input paths |
| Docs | current-state, runbook, architecture, relevant feature doc |

## 5.3 Step 3: Make a small plan

Before editing, produce:

```text
Plan:
1. ...
2. ...
3. ...

Files likely to change:
- ...
```

If the change would touch more than 10 files, split it into phases unless the user explicitly asked for a large refactor.

## 5.4 Step 4: Add tests first where practical

For backend behavior, add or update tests before implementation.

For frontend utility logic, add tests where the repo already has a test pattern.

For visual-only changes, add tests only if the repo has a feasible component or snapshot test setup.

## 5.5 Step 5: Implement the smallest safe change

Avoid broad rewrites. Do not reformat unrelated files.

## 5.6 Step 6: Run focused validation

Run the smallest relevant tests first. Then run broader tests if reasonable.

## 5.7 Step 7: Report exactly

At the end, report:

```text
Files changed:
- ...

Tests run:
- ...

Manual checks:
- ...

Known limitations:
- ...

Next recommended task:
- ...
```

Do not say "done" unless tests or manual checks support it.

---

# 6. Stop Conditions

Stop and ask for direction if any of these occur:

1. Alembic migration chain is broken.
2. A migration would drop or rewrite existing data.
3. A requested change requires storing broker credentials.
4. A requested change exposes API keys to frontend code.
5. A frontend feature would require fake data to look complete.
6. A test failure appears unrelated to the current task.
7. The requested change requires scraping a site that may prohibit scraping.
8. The task would require a public deployment security model.
9. The implementation touches more than 10 files without a clear reason.
10. Docs and code strongly contradict each other.
11. You cannot verify whether a feature is real or mocked.
12. The task would create buy/sell recommendation language.

When stopping, include:

```text
Blocked because:
Options:
Recommended option:
```

---

# 7. Git and Diff Discipline

## 7.1 No giant diffs

Keep changes narrow.

Good:

```text
Add API envelope to health endpoint and frontend fetcher compatibility.
```

Bad:

```text
Refactor backend, redesign dashboard, add DCF, change schema, update all docs.
```

## 7.2 Commit-sized phases

Prefer tasks that could become a single clean commit.

Suggested commit scopes:

```text
chore: stabilize healthcheck
feat: add api response envelope foundation
feat: add data state components
feat: add processing run status endpoint
feat: add revenue-driven dcf service
feat: add dcf guardrail warnings
feat: add market regime manual inputs
test: add valuation engine coverage
docs: reconcile current state with code
```

## 7.3 Never hide unrelated changes

If you touch unrelated files accidentally, revert them or explain why they changed.

---

# 8. Local Development Rules

## 8.1 Standard local commands

Use these commands from repo root.

Start all services:

```bash
docker compose up -d
```

Rebuild services:

```bash
docker compose up --build -d
```

Stop services:

```bash
docker compose down
```

Delete local database volume, only if explicitly acceptable:

```bash
docker compose down -v
```

Check containers:

```bash
docker compose ps
```

Backend logs:

```bash
docker compose logs backend --tail=100
```

Frontend logs:

```bash
docker compose logs frontend --tail=100
```

Backend health:

```bash
curl http://localhost:8000/api/health
```

Run migrations:

```bash
docker compose exec backend alembic upgrade head
```

Inspect migration heads:

```bash
docker compose exec backend alembic heads
```

Inspect DB migration version:

```bash
docker compose exec postgres psql -U marketintel -d marketintel -c "SELECT * FROM alembic_version;"
```

## 8.2 Docker socket permission

If Docker says:

```text
permission denied while trying to connect to the docker API at unix:///var/run/docker.sock
```

Do not recommend:

```bash
sudo chmod 666 /var/run/docker.sock
```

Instead:

1. Confirm Docker Desktop is running.
2. Restart Docker Desktop.
3. Check Docker context.
4. Run commands in normal Mac Terminal, not inside a restricted sandbox.

## 8.3 Frontend cannot reach backend

Use this checklist:

1. Is backend running?
2. Is frontend running?
3. Does `curl http://localhost:8000/api/health` work?
4. Does backend log show Python stack traces?
5. Is `NEXT_PUBLIC_API_BASE_URL` correct?
6. Is the frontend proxy using the correct backend URL?
7. Is CORS configured if direct browser calls are used?
8. Are migrations failing at backend startup?

## 8.4 Alembic missing revision

Known error:

```text
Can't locate revision identified by 'a2afaa43a162'
```

Do not immediately run destructive commands.

First inspect:

```bash
ls backend/alembic/versions
grep -R "a2afaa43a162" backend/alembic/versions || true
docker compose exec postgres psql -U marketintel -d marketintel -c "SELECT * FROM alembic_version;"
docker compose exec backend alembic heads
```

If this is disposable local data, the clean reset may be acceptable:

```bash
docker compose down -v
docker compose up --build -d
docker compose exec backend alembic upgrade head
```

If preserving data matters, do not wipe volumes. Restore missing migration or stamp carefully only after explaining risk.

---

# 9. Backend Rules

## 9.1 Architecture

Backend uses:

- FastAPI
- SQLAlchemy
- PostgreSQL
- Alembic
- Pydantic schemas
- pytest

Routes should be thin.

Business logic belongs in services.

Database models should not leak directly to frontend responses.

## 9.2 Suggested backend structure

Target structure:

```text
backend/app/
  api/
    routers/
      health.py
      dashboard.py
      portfolio.py
      companies.py
      ingestion.py
      scores.py
      valuation.py
      narratives.py
      research.py
      data_health.py

  models/
    company.py
    portfolio.py
    document.py
    event.py
    alert.py
    score.py
    valuation.py
    narrative.py
    research.py
    processing_run.py

  schemas/
    api_response.py
    company.py
    portfolio.py
    valuation.py
    score.py
    narrative.py
    ingestion.py

  services/
    valuation_service.py
    scoring_service.py
    portfolio_analytics_service.py
    ingestion_status_service.py
    thesis_service.py
    narrative_service.py

  providers/
    market_data/
    fundamentals/
    macro/
    news/
    ai/
```

Do not reorganize the full backend in one task. Move one module group at a time.

## 9.3 API response envelope

All new endpoints should use:

```json
{
  "data": {},
  "meta": {
    "status": "success",
    "source": "internal",
    "last_updated": "2026-05-30T10:00:00Z",
    "is_stale": false,
    "is_mock": false,
    "warnings": [],
    "confidence": "medium"
  },
  "errors": []
}
```

Error format:

```json
{
  "data": null,
  "meta": {
    "status": "error",
    "source": "SEC",
    "last_updated": null,
    "is_stale": true,
    "is_mock": false,
    "warnings": []
  },
  "errors": [
    {
      "code": "SEC_USER_AGENT_MISSING",
      "message": "SEC ingestion requires SEC_USER_AGENT in .env."
    }
  ]
}
```

During migration, frontend fetcher may need to support both legacy and envelope responses.

## 9.4 Error handling

Backend errors should be specific but not leak secrets.

Good error code examples:

```text
SEC_USER_AGENT_MISSING
PROVIDER_NOT_CONFIGURED
INGESTION_TIMEOUT
DUPLICATE_DOCUMENT
VALIDATION_ERROR
STALE_DATA
SOURCE_UNAVAILABLE
MIGRATION_REQUIRED
```

Bad:

```text
Internal error at line 98 with full stack and environment variables
```

## 9.5 Processing runs

Every ingestion or external provider action should create or update a processing run.

Track:

```text
run_type
source_type
source_id
company_id
started_at
finished_at
status
fetched_count
created_count
skipped_duplicate_count
error_count
error_details_json
metadata_json
```

No silent ingestion failures.

---

# 10. Frontend Rules

## 10.1 Architecture

Frontend uses:

- Next.js
- app router
- reusable components
- centralized API client
- centralized types
- centralized formatting helpers

Target structure:

```text
frontend/
  app/
    dashboard/
    portfolio/
    companies/
      [ticker]/
    narratives/
    research/
    valuation/
    data-health/
    settings/

  components/
    layout/
    ui/
    finance/
    intelligence/
    charts/
    data/
    forms/
    tables/

  lib/
    api/
    formatting/
    validation/
    constants/
    scoring/

  types/
    api.ts
    company.ts
    portfolio.ts
    valuation.ts
    score.ts
    narrative.ts
    research.ts
    ingestion.ts
```

Do not create 800-line page files. If a page grows too large, extract components.

## 10.2 UI design principle

Use dense, calm, professional dashboard design.

Avoid:

- decorative gradients
- huge empty cards
- too many colors
- unlabelled charts
- low contrast text
- mock intelligence
- marketing-style UI
- random visual complexity

Prefer:

- compact layout
- clear active navigation state
- tabular numerals
- consistent card styles
- clear hierarchy
- evidence drawers
- data freshness badges
- loading/error/empty/stale states

## 10.3 Required data states

Every major data component should support:

- Loading
- Empty
- Error
- Stale
- Partial
- Not Configured
- Mock Data
- Success

Required components:

```text
EmptyState
ErrorState
LoadingState
StaleDataBanner
MockDataBadge
NotConfiguredState
PartialDataNotice
DataFreshnessIndicator
```

## 10.4 Empty states must be actionable

Bad:

```text
No active alerts.
```

Good:

```text
No active alerts.
Run ingestion or add companies to generate alerts.
[Run Ingestion] [Add Company]
```

Bad:

```text
0 companies
```

Good:

```text
No tracked companies yet.
Add a company or import a watchlist.
[Add Company] [Import Watchlist]
```

## 10.5 Chart rules

Every chart must show:

- title
- units
- source
- last updated
- tooltip
- loading state
- empty state
- error state
- stale state

Avoid:

- decorative charts
- pie charts for complex exposure
- 3D charts
- charts without units
- charts without timestamps

---

# 11. Security Rules

## 11.1 Secrets

Never commit:

```text
.env
API keys
bearer tokens
broker tokens
model keys
database passwords beyond local placeholders
```

`.env.example` must contain placeholders only.

Frontend must never contain:

```text
DATABASE_URL
SEC_USER_AGENT
OPENAI_API_KEY
GEMINI_API_KEY
ALPHA_VANTAGE_API_KEY
FRED_API_KEY
broker tokens
```

## 11.2 External input

Treat these as untrusted:

- RSS feed content
- SEC filing text
- CSV imports
- markdown/text uploads
- user-provided URLs
- social posts
- AI output
- provider API responses

Do not render imported HTML as trusted HTML.

## 11.3 URL fetching and SSRF

Do not allow user-controlled URLs to make backend fetch arbitrary internal resources.

If adding URL ingestion:

- validate scheme
- allow only `http` and `https`
- block localhost/private IP ranges
- use timeouts
- limit response size
- log provider errors safely

## 11.4 CSV import/export

Before CSV import:

- validate every row
- validate dates, quantities, prices, currencies
- return row-level errors
- enforce file size limits

Before CSV export:

- escape cells starting with:
  - `=`
  - `+`
  - `-`
  - `@`

## 11.5 AI security

Before AI features:

- create AI output provenance storage
- store model name
- store prompt version
- store input hash
- store generated timestamp
- link source IDs
- store limitations
- store confidence label
- store review status

Do not send private portfolio data, thesis notes, or DCF assumptions to external AI unless the feature explicitly requires it and logs the action.

## 11.6 Broker integrations

Do not store broker passwords.

Broker sync requires:

- official OAuth/token flow
- encrypted token storage if persisted
- explicit permission model
- audit logging
- revocation path

Do not build broker sync until security design is approved.

## 11.7 Public deployment

Do not expose this app beyond localhost until these exist:

- authentication
- authorization
- HTTPS
- CSRF review
- strict CORS
- rate limiting
- secret manager
- backup policy
- privacy model
- audit logging

---

# 12. Data and Ingestion Rules

## 12.1 Source priority

Immediate and acceptable:

- manual portfolio entries
- manual market prices
- SEC EDGAR
- RSS feeds
- user thesis notes
- user-entered DCF assumptions

Later:

- FRED
- Alpha Vantage or FMP
- GDELT
- official Reddit API
- official broker APIs
- options chain providers

Avoid for now:

- Twitter/X scraping
- Reddit HTML scraping
- broker credential collection
- real-time trading feeds
- expensive microstructure feeds

## 12.2 Provider abstraction

Do not hardcode one data provider everywhere.

Use provider interfaces:

```text
MarketDataProvider
FundamentalsProvider
MacroDataProvider
NewsProvider
AiProvider
OptionsDataProvider
```

Suggested structure:

```text
backend/app/providers/
  market_data/
    base.py
    manual.py
    alpha_vantage.py
    fmp.py
  macro/
    fred.py
  news/
    rss.py
    gdelt.py
  ai/
    mock.py
    openai.py
    gemini.py
```

## 12.3 Provider health

For every provider, track:

- configured or not
- last successful run
- last failure
- error count
- rate limit status
- stale status
- coverage gaps

Expose this on Data Health page.

---

# 13. Valuation and DCF Rules

## 13.1 Current simple DCF is not enough

Do not build only:

```text
Current FCF × growth rate → discounted value
```

A serious valuation tool must connect:

```text
Story → Revenue → Margins → Reinvestment → ROIC → WACC → Terminal value → Equity bridge → Sensitivity → Reverse DCF
```

## 13.2 Required DCF assumptions

At minimum:

```text
starting_revenue
revenue_growth_years_json
current_operating_margin
target_operating_margin
tax_rate
sales_to_capital_ratio
starting_invested_capital
risk_free_rate
equity_risk_premium
beta
cost_of_equity
pre_tax_cost_of_debt
debt_to_capital
equity_to_capital
wacc_start
wacc_terminal
terminal_growth_rate
terminal_roic
cash
debt
minority_interests
preferred_stock
employee_options_value
diluted_shares
current_market_price
```

## 13.3 DCF calculation rules

Use FCFF:

```text
Revenue
× EBIT margin
= EBIT
× (1 - tax rate)
= NOPAT
- Reinvestment
= FCFF
```

Default reinvestment:

```text
Reinvestment = Change in Revenue / Sales-to-Capital Ratio
```

ROIC:

```text
ROIC = NOPAT / Invested Capital
```

Equity bridge:

```text
Enterprise Value
+ Cash
+ Non-operating assets
- Debt
- Minority interests
- Preferred stock
- Employee options value
= Equity Value
/ Diluted Shares
= Intrinsic Value Per Share
```

## 13.4 DCF guardrails

Warn if:

- terminal growth exceeds risk-free rate
- terminal value exceeds 80% of EV
- WACC is below risk-free rate
- positive growth has no reinvestment
- ROIC is below WACC during high growth
- share count is missing
- user uses basic shares instead of diluted shares
- WACC is manually entered without support
- model has no bear/base/bull scenarios
- no reverse DCF has been run

## 13.5 DCF UI tabs

Use:

```text
Story | Assumptions | Forecast | Valuation | Sensitivity | Reverse DCF | Notes
```

## 13.6 DCF tests

Test:

- FCFF calculation
- reinvestment calculation
- ROIC calculation
- WACC calculation
- terminal value calculation
- equity bridge
- sensitivity table generation
- warning generation
- reverse DCF solver
- bad input validation

---

# 14. Market Regime Rules

## 14.1 Purpose

Market regime should answer:

```text
Is the broader market structure supportive for adding risk?
```

Do not call it a buy/sell signal.

Better labels:

- Market Structure Score
- Entry Timing Readiness
- Risk-On/Risk-Off Regime
- Liquidity Regime
- Market Support Score

## 14.2 Initial modules

Use these modules:

| Module | Weight |
|---|---:|
| Options and derivatives | 30% |
| Institutional flow and liquidity | 25% |
| Volume and participation | 15% |
| Market breadth and momentum | 15% |
| Macro, credit, volatility | 15% |

## 14.3 Metrics

Options:

- put-call ratio
- gamma regime
- open interest change
- IV rank
- skew

Flows:

- FII/DII if Indian market
- ETF/fund flows if available
- liquidity proxy

Volume:

- volume multiplier
- delivery percentage if available
- volume at price later

Breadth:

- percent above 50-day and 200-day moving averages
- advance/decline line
- new highs/new lows
- Hurst exponent as supporting metric only

Macro/credit/volatility:

- VIX level and trend
- VIX term structure
- credit spreads
- rates
- financial conditions

## 14.4 Build order

Do not start with expensive or fragile microstructure data.

Build order:

1. Manual market regime inputs
2. OHLCV and volume multiplier
3. VIX and credit spreads
4. Breadth if data exists
5. Options chain
6. Gamma model
7. Microstructure only much later

## 14.5 Market regime score output

Every score must return:

```text
score
label
confidence
drivers
blockers
warnings
last_updated
data_sources
formula
```

---

# 15. Investment Decision Workflow Rules

## 15.1 The app should structure judgment

Do not just show data. Build tools that help the user think.

Core decision modules:

- thesis assumptions
- falsification triggers
- evidence ledger
- contradiction engine
- variant perception map
- price-implied expectations
- decision journal
- pre-mortem
- opportunity cost view
- portfolio marginal impact simulator
- signal decay tracker
- catalyst calendar

## 15.2 Thesis assumptions

Break thesis notes into assumptions:

```text
assumption_text
category
importance
confidence
status
falsification_trigger
supporting_evidence
contradicting_evidence
last_reviewed
```

Statuses:

```text
supported
weakening
contradicted
unknown
stale
needs_review
```

## 15.3 Evidence ledger

For every meaningful conclusion, preserve:

```text
claim
evidence
source
date
direction
confidence
linked_entity
```

Direction values:

```text
supports
weakens
contradicts
neutral
```

## 15.4 Decision journal

Every decision record should include:

```text
company
portfolio
decision_type
price
position_size
thesis_summary
valuation_case
market_regime
supporting_evidence
contradicting_evidence
risks
what_would_change_my_mind
review_date
review_notes
```

## 15.5 Portfolio marginal impact

Before adding a position, simulate:

- sector exposure change
- industry exposure change
- theme exposure change
- top holding concentration change
- currency exposure change
- portfolio beta change if available
- downside contribution
- rule breaches

---

# 16. Testing Rules

## 16.1 Backend tests

Use pytest.

Test:

- route success
- validation errors
- missing resources
- duplicate records
- security-sensitive input handling
- service calculations
- migrations where feasible
- mocked provider responses
- ingestion failures
- stale data states

## 16.2 Frontend tests

Use existing repo test patterns.

Test:

- API fetcher behavior
- envelope parsing
- payload conversion
- formatting helpers
- score calculation helpers
- component states if test setup exists

## 16.3 External APIs

Never call live external APIs in tests.

Use mocked responses for:

- SEC
- RSS
- FRED
- market data providers
- AI providers
- options providers

## 16.4 Manual browser checks

For UI tasks, provide manual checks:

```text
1. Open http://localhost:3000
2. Navigate to ...
3. Confirm ...
4. Trigger ...
5. Confirm error/empty/stale state ...
```

---

# 17. Documentation Update Rules

Update docs when changing:

- API response shape
- database schema
- migrations
- environment variables
- data providers
- ingestion flow
- scoring formulas
- security assumptions
- local setup commands
- UI architecture
- feature status

Do not mark a feature complete in docs unless:

1. backend exists
2. frontend exists if user-facing
3. tests or manual checks pass
4. mock data is removed or clearly labeled
5. limitations are documented

---

# 18. Agent Response Format

Every agent response after a coding task should use:

```text
Summary:
- ...

Files changed:
- ...

Tests run:
- ...

Manual checks:
- ...

Security notes:
- ...

Known limitations:
- ...

Next task:
- ...
```

If blocked:

```text
Blocked:
- ...

Evidence:
- ...

Options:
1. ...
2. ...

Recommended:
- ...
```

---

# 19. Exact Prompts Agents Should Use Internally

## 19.1 Reality audit prompt

```text
Do not edit files yet.

Inspect the repo and compare actual code against docs.

Return:
- implemented features
- partial features
- mocked or hardcoded features
- missing backend endpoints
- missing frontend pages
- inconsistent API response shapes
- Alembic migration status
- Docker/local startup risks
- hardcoded secret risks
- next 5 safe tasks
```

## 19.2 API envelope prompt

```text
Implement API response envelope foundation only.

Add ApiResponse, ApiMeta, and ApiError schemas.
Convert GET /api/health and one low-risk read endpoint only.
Update frontend fetcher to support both legacy and envelope responses.
Add ErrorState, EmptyState, LoadingState, and StaleDataBanner if missing.
Add tests.

Do not refactor all routes.
Do not add product features.
```

## 19.3 DCF engine prompt

```text
Implement backend DCF engine only.

Add or verify DCF models and schemas.
Implement revenue-driven FCFF calculations:
Revenue, EBIT, NOPAT, reinvestment, FCFF, ROIC, WACC, terminal value, equity bridge.
Add guardrail warnings.
Add sensitivity table generation.
Add tests.

Do not redesign frontend yet.
Do not add live market APIs.
```

## 19.4 Market regime prompt

```text
Implement manual market regime scoring only.

Add models for MarketRegimeSnapshot and MarketRegimeInput.
Add scoring service with module weights.
Add API endpoint for manual inputs and score breakdown.
Add tests.

Do not add live options data.
Do not add gamma model yet.
Do not call external APIs.
```

## 19.5 Security review prompt

```text
Perform security review only.

Inspect:
- .env.example
- docker-compose.yml
- backend config
- frontend API proxy
- ingestion services
- file import paths
- AI/provider code
- logs

Return:
- secret leakage risks
- SSRF risks
- XSS risks
- CSV injection risks
- unsafe external API handling
- broker credential risks
- required fixes
```

---

# 20. Final Rule

The best version of this repo is not the one with the most features.

It is the one where every number, alert, insight, chart, and valuation output can be traced back to:

1. a source,
2. a calculation,
3. a user assumption, or
4. a clearly labeled model interpretation.

If a change does not preserve that standard, do not make it.
