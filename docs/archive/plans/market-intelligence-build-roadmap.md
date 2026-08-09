# Market Intelligence App: Next-Step Master Plan

## Purpose

This file is the next execution guide for turning the current app into a serious market intelligence and portfolio decision system.

It incorporates the latest discussion around:

- local setup blockers
- frontend/backend reliability
- UI simplification
- cybersecurity
- API and data provider strategy
- DCF maker redesign in the spirit of Aswath Damodaran-style valuation
- investment decision support features
- unique features that most portfolio trackers and research tools do not provide
- exact next steps for Codex/Antigravity

The goal is not to add random complexity. The goal is to build a tool that helps answer:

```text
What changed?
Why does it matter?
How reliable is it?
How does it affect my thesis?
How exposed am I?
What would change my mind?
What should I inspect next?
```

For the latest shipped/proposed split, read [trust-and-evidence-checkpoint-2026-07-22.md](trust-and-evidence-checkpoint-2026-07-22.md). Its acceptance criteria take precedence over older unverified implementation assumptions in this plan.

---

# 0. Immediate Next Step

## The next step is not more features.

The next step is:

```text
Stabilize the app → audit reality against docs → standardize backend responses → fix data states → then upgrade valuation and intelligence workflows.
```

You currently have signs of a common early-stage app problem:

- docs say many things are built
- UI shows advanced pages
- database migrations have previously broken
- frontend has sometimes failed to reach backend
- some views may be real, mocked, partial, or hardcoded

Before asking Codex to build more, force it to verify what is real.

## Immediate task order

1. Fix local Docker/backend/migration startup.
2. Run a code reality audit against the docs.
3. Confirm which backend endpoints actually exist.
4. Confirm which frontend pages actually call real APIs.
5. Confirm what is mocked or hardcoded.
6. Implement the API response envelope.
7. Add global loading, empty, error, stale, partial, and not-configured states.
8. Only then improve the DCF tool and decision intelligence features.

---

# 1. Why this order matters

A market intelligence app fails if it looks impressive but cannot be trusted.

The dangerous failure modes are:

| Failure | Why it is bad |
|---|---|
| Frontend invents intelligence | User trusts data that does not exist |
| Mock data looks real | User makes decisions on fake state |
| Broken ingestion is hidden | User thinks they are up to date when they are not |
| DCF output looks precise but assumptions are weak | False confidence |
| AI summarizes without source links | Hallucination risk |
| Scoring has no explanation | User cannot trust or debug it |
| Portfolio exposure ignores actual position size | Wrong prioritization |
| Backend APIs differ across pages | Frontend becomes fragile |
| Migration chain breaks | App cannot run reliably |

The app should earn trust before it earns features.

---

# 2. Current diagnosis based on the app and docs

## What looks promising

The app has the right general direction:

- local-first setup
- FastAPI backend
- Next.js frontend
- PostgreSQL database
- SEC/RSS ingestion direction
- portfolio layer direction
- scoring and alerting direction
- valuation/DCF page direction
- dark financial dashboard design direction
- source-backed intelligence principle

## What still feels incomplete or risky

### 1. Reliability gap

You have already seen:

```text
Can't locate revision identified by 'a2afaa43a162'
```

and:

```text
frontend can't reach backend
```

These need to be resolved before feature work.

### 2. Documentation mismatch risk

Some documents claim advanced milestones are complete. Other documents say those same features are planned or missing. Codex must inspect actual code and stop trusting docs blindly.

### 3. UI sophistication ahead of backend certainty

The UI now looks like a real application, but the user needs to know whether each card, score, chart, and summary is:

- real
- mocked
- stale
- partially available
- calculated locally
- AI-generated
- user-entered
- sourced from SEC/RSS/API

### 4. DCF tool is too basic

The current DCF tool looks like a simple FCFF growth calculator. It needs to become a proper valuation system with revenue, margin, reinvestment, ROIC, WACC, terminal value guardrails, scenario analysis, sensitivity tables, and reverse DCF.

### 5. Investment decision process is not yet structured enough

Most tools show data. A truly useful tool should help structure judgment.

It should help the user identify:

- what they believe
- what the market believes
- what the price implies
- what the evidence supports
- what would falsify the thesis
- what risks are underweighted
- what the portfolio is actually exposed to

---

# 3. Product North Star

## The app should become a private investment decision cockpit

Not a trading terminal.
Not a dashboard collection.
Not an AI chatbot.
Not a fake Bloomberg.

The app should be a source-backed personal investment operating system.

## Core product loop

```text
Portfolio + Watchlist
→ Source ingestion
→ Event extraction
→ Evidence trail
→ Scoring
→ Thesis impact
→ Portfolio exposure impact
→ Decision prompt
→ Research memo / action log
```

## Core user questions

Every major screen should answer at least one of these:

1. What changed since I last checked?
2. What do I own and what am I exposed to?
3. What does the evidence say?
4. What does the market seem to believe?
5. What does the current price imply?
6. What assumptions drive my valuation?
7. What would change my mind?
8. What should I investigate next?

---

# 4. Immediate Technical Fixes

## 4.1 Fix migration chain and backend availability

Before coding more features, run:

```bash
docker compose ps
docker compose logs backend --tail=100
ls backend/alembic/versions
grep -R "a2afaa43a162" backend/alembic/versions || true
```

If this is local dev data you do not need, the cleanest fix is usually:

```bash
docker compose down -v
docker compose up --build -d
docker compose exec backend alembic upgrade head
curl http://localhost:8000/api/health
```

If you need to preserve data, do not wipe volumes. Instead, inspect:

```bash
docker compose exec postgres psql -U marketintel -d marketintel -c "SELECT * FROM alembic_version;"
docker compose exec backend alembic heads
```

Then decide whether to restore the missing migration file or stamp carefully.

## 4.2 Fix frontend/backend connectivity

Checklist:

```bash
docker compose ps
curl http://localhost:8000/api/health
docker compose logs backend --tail=100
docker compose logs frontend --tail=100
```

Confirm:

- backend container is running
- backend exposes port `8000`
- frontend exposes port `3000`
- frontend uses correct backend URL
- frontend proxy is not trying to call an internal Docker hostname from the browser
- backend CORS allows local frontend if direct calls are used

## 4.3 Add or verify health endpoint

Backend should expose:

```http
GET /api/health
```

Response:

```json
{
  "status": "ok",
  "timestamp": "2026-05-30T10:00:00Z"
}
```

This should not depend on external APIs.

---

# 5. Reality Audit Codex Must Run Before Building

Give Codex this before any feature work:

```text
Read docs/00-current-state.md, docs/08-execution-runbook.md, docs/agent_capabilities_and_limitations.md, docs/03-database-schema.md, docs/06-security-threat-model.md, README.md, backend/app, frontend/app, frontend/components, backend/alembic/versions, and docker-compose.yml. For historical UI context only, see docs/archive/needs-review/design-brief.md.

Do not code yet.

Perform a reality audit.

Return:
1. Which claimed features are actually implemented in code.
2. Which claimed features are only mocked or hardcoded.
3. Which claimed features are missing.
4. Which frontend pages call real backend APIs.
5. Which frontend pages use mock/static data.
6. Which backend endpoints exist.
7. Which backend endpoints return inconsistent shapes.
8. Which Alembic migrations exist and whether the chain is valid.
9. Whether local Docker startup is reliable.
10. Whether any secrets are hardcoded.
11. The exact next 5 implementation tasks in order.

Do not build anything until this audit is returned.
```

Expected output format:

```text
Reality Audit

Actually implemented:
- ...

Partially implemented:
- ...

Mocked/hardcoded:
- ...

Missing:
- ...

Broken/risky:
- ...

Next 5 tasks:
1. ...
2. ...
3. ...
4. ...
5. ...
```

---

# 6. Next Build Phase: API Response Envelope

## Why this is the next real engineering step

The frontend cannot handle stale data, errors, partial results, and mock warnings unless the backend returns consistent metadata.

Every endpoint should eventually return:

```json
{
  "data": {},
  "meta": {
    "status": "success",
    "source": "internal",
    "last_updated": "2026-05-30T10:00:00Z",
    "is_stale": false,
    "is_mock": false,
    "warnings": []
  },
  "errors": []
}
```

Error example:

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

## Backend requirements

Create:

```text
backend/app/schemas/api_response.py
```

With:

```text
ApiResponse[T]
ApiMeta
ApiError
```

Add helper functions:

```text
success_response(data, source="internal", warnings=[])
error_response(code, message, source="internal", status_code=400)
```

## Frontend requirements

Update fetch client to:

- parse envelope
- surface `errors`
- expose `meta`
- never white-screen on backend error
- show stale banners
- show mock-data badges
- show not-configured states

## Implementation rule

Do not refactor every endpoint in one giant change. Do this in batches:

1. health/data status endpoints
2. dashboard endpoints
3. portfolio endpoints
4. company endpoints
5. ingestion endpoints
6. valuation endpoints
7. narratives/research later

---

# 7. Data Honesty Layer

This is a core product feature, not a polish item.

Every major card/chart/table needs a state:

| State | Meaning |
|---|---|
| Loading | Request in progress |
| Empty | No data exists yet |
| Error | API failed |
| Stale | Last successful update is too old |
| Partial | Some data loaded, some failed |
| Not configured | API key/user agent/source missing |
| Mock | Data is fake/hardcoded for development |
| Success | Data is live or valid local data |

## Required global components

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

## Why this matters for investment decisions

A wrong number is bad. A stale number presented confidently is worse.

This app should make uncertainty visible.

---

# 8. UI Simplification Plan

## 8.1 Reduce to 8 primary tabs

Recommended sidebar:

```text
Dashboard
Portfolio
Companies
Narratives
Research
Valuation
Data Health
Settings
```

Avoid separate top-level pages for everything. Keep secondary features inside the relevant workflow.

## 8.2 Use the 4-layer hierarchy on every serious page

Every page should use:

```text
Layer 1: Executive summary
Layer 2: Key metrics
Layer 3: Evidence and sources
Layer 4: Deep dive
```

This avoids random dashboards.

## 8.3 Dashboard should answer one question

Question:

```text
What do I need to know today?
```

Sections:

- portfolio snapshot
- most important changes
- unresolved alerts
- new filings
- narrative shifts
- data freshness
- suggested research tasks

## 8.4 Portfolio should answer one question

Question:

```text
What am I actually exposed to?
```

Sections:

- total value
- top holdings
- sector exposure
- industry exposure
- theme exposure
- concentration warnings
- holdings affected by new events
- risk contribution

## 8.5 Company should answer one question

Question:

```text
Do I understand this company better after 5 minutes?
```

Sections:

- ticker header
- recent changes
- filing intelligence
- financial trends
- narratives
- risks
- valuation
- evidence

## 8.6 Valuation should answer one question

Question:

```text
What is this company worth under my assumptions, and are those assumptions internally consistent?
```

Sections:

- story
- assumptions
- valuation output
- sensitivity/reverse DCF
- warnings

---

# 9. DCF Maker Upgrade: Damodaran-Style Valuation Tool

## 9.1 Problem with current DCF screen

The current DCF screen is useful as a prototype, but it is too simple for serious valuation.

It appears to use:

- one FCF number
- one FCF growth rate
- one WACC
- one terminal growth rate
- one share count
- one net debt input

This creates a mathematically neat output but weak business logic.

## 9.2 What a serious DCF must do

It must connect:

```text
Story → Assumptions → Cash flows → Reinvestment → ROIC → Risk → Terminal value → Equity value → Decision context
```

## 9.3 New DCF page structure

Use tabs:

```text
Story | Assumptions | Valuation | Sensitivity | Reverse DCF | Notes
```

### Tab 1: Story

Fields:

- company story
- growth story
- margin story
- reinvestment story
- risk story
- what would break the thesis
- source/thesis note links

Purpose:

Force the user to write a business story before entering numbers.

### Tab 2: Assumptions

Sections:

1. Revenue
2. Margins
3. Taxes
4. Reinvestment
5. Cost of capital
6. Terminal value
7. Equity bridge

### Tab 3: Valuation

Show:

- intrinsic value per share
- current price
- upside/downside
- enterprise value
- equity value
- PV of explicit cash flows
- PV of terminal value
- terminal value as % of EV
- implied exit multiple
- implied terminal ROIC

### Tab 4: Sensitivity

Show:

- WACC vs terminal growth table
- revenue growth vs margin table
- scenario comparison
- valuation distribution later

### Tab 5: Reverse DCF

Show:

- what growth is implied by current price
- what margin is implied by current price
- what terminal value assumptions are implied
- what execution level the market is pricing in

### Tab 6: Notes

Show:

- assumptions rationale
- sources used
- risks
- decision log
- version history

---

# 10. DCF Data Model Required

Add or verify these tables.

## 10.1 ValuationModel

```text
id
company_id
ticker
model_name
model_type
base_currency
units
created_at
updated_at
```

Model types:

- fcff_dcf
- fcfe_dcf later
- dividend_discount later
- sum_of_parts later
- reverse_dcf later

## 10.2 DcfAssumptionSet

```text
id
valuation_model_id
scenario
story_text
growth_story
margin_story
reinvestment_story
risk_story
starting_revenue
revenue_growth_years_json
target_operating_margin
current_operating_margin
tax_rate
sales_to_capital_ratio
reinvestment_method
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
minority_interests
preferred_stock
debt
employee_options_value
diluted_shares
current_market_price
created_at
updated_at
```

## 10.3 DcfProjectionYear

```text
id
assumption_set_id
year_index
calendar_year
revenue
revenue_growth
ebit_margin
ebit
tax_rate
nopat
reinvestment
fcff
invested_capital
roic
wacc
discount_factor
pv_fcff
created_at
```

## 10.4 DcfOutput

```text
id
assumption_set_id
sum_pv_fcff
terminal_value
pv_terminal_value
enterprise_value
cash
non_operating_assets
debt
minority_interests
preferred_stock
employee_options_value
equity_value
diluted_shares
intrinsic_value_per_share
current_market_price
upside_downside_pct
terminal_value_pct_of_ev
implied_exit_multiple
implied_terminal_roic
model_quality_score
warnings_json
created_at
```

## 10.5 DcfSensitivityTable

```text
id
assumption_set_id
table_type
x_axis_json
y_axis_json
values_json
created_at
```

Table types:

- wacc_vs_terminal_growth
- growth_vs_margin
- sales_to_capital_vs_margin
- terminal_roic_vs_growth

## 10.6 DcfDecisionLog

```text
id
valuation_model_id
assumption_set_id
decision_type
user_note
price_at_decision
intrinsic_value_at_decision
upside_downside_at_decision
confidence_label
created_at
```

Decision types:

- watch
- research_more
- increase_interest
- decrease_interest
- reject
- update_thesis
- add_to_portfolio_later

Do not call these buy/sell recommendations.

---

# 11. DCF Calculation Engine

## 11.1 Revenue-driven FCFF forecast

Do not forecast only FCF growth.

Forecast:

```text
Revenue
× EBIT margin
= EBIT
× (1 - tax rate)
= NOPAT
- Reinvestment
= FCFF
```

## 11.2 Reinvestment logic

Default method:

```text
Reinvestment = Change in Revenue / Sales-to-Capital Ratio
```

Why it matters:

Growth requires capital. A DCF that grows FCF without reinvestment is often fantasy.

## 11.3 ROIC calculation

```text
ROIC = NOPAT / Invested Capital
```

Flag:

| Condition | Warning |
|---|---|
| ROIC > WACC | Growth creates value |
| ROIC near WACC | Growth is neutral |
| ROIC < WACC | Growth destroys value |

## 11.4 WACC builder

Allow two modes:

1. Manual WACC
2. Component-based WACC

Component-based inputs:

- risk-free rate
- equity risk premium
- beta
- cost of equity
- pre-tax cost of debt
- tax rate
- debt weight
- equity weight
- WACC

## 11.5 Terminal value guardrails

Warnings:

- terminal growth exceeds risk-free rate
- terminal growth exceeds long-run GDP-like assumption
- terminal value exceeds 80% of EV
- WACC below risk-free rate
- terminal ROIC is economically implausible
- positive growth with negative reinvestment
- high growth with ROIC below WACC
- terminal value denominator too small

## 11.6 Equity bridge

DCF should show:

```text
Enterprise Value
+ Cash
+ Non-operating assets
- Debt
- Minority interests
- Preferred stock
- Employee options value
= Equity Value
/ Diluted shares
= Value per share
```

This is necessary for public company valuation.

---

# 12. DCF UI Requirements

## 12.1 Better header

Current page hierarchy feels off. Use:

```text
Apple Inc. (AAPL)
Intrinsic Valuation
Scenario: Base Case
Last saved: May 30, 2026
```

## 12.2 Better output cards

Cards:

- Intrinsic Value / Share
- Current Market Price
- Upside / Downside
- Enterprise Value
- Equity Value
- Terminal Value % of EV
- Model Quality
- Main Warning

## 12.3 Better projection table

Show:

| Year | Revenue | Growth | EBIT Margin | EBIT | NOPAT | Reinvestment | FCFF | ROIC | WACC | PV FCFF |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|

## 12.4 Charts

Must-have charts:

1. Revenue forecast line chart
2. EBIT margin line chart
3. FCFF bar chart
4. PV contribution chart
5. Terminal value vs explicit period split
6. ROIC vs WACC chart
7. Scenario comparison chart
8. Sensitivity heatmap
9. Market price vs intrinsic value chart

## 12.5 Assumption warnings

Show a warning panel:

```text
Model warnings:
- Terminal value is 84% of EV.
- Terminal growth exceeds risk-free rate.
- WACC was entered manually without beta/debt support.
- Positive growth assumes no reinvestment.
```

## 12.6 Assumption quality score

Add:

```text
Model Quality Score: 72/100
```

Inputs:

- completeness of assumptions
- whether WACC is built from components
- whether terminal value is excessive
- whether reinvestment supports growth
- whether ROIC is plausible
- whether story and numbers conflict
- whether sources are attached

Do not present model quality as valuation truth. It is a model discipline score.

---

# 13. Investment Decision Features To Build

This is where the app can become genuinely differentiated.

Most platforms show data. This app should structure judgment.

## 13.1 Thesis Assumption Engine

Instead of one free-text thesis, break every thesis into assumptions.

Example:

```text
Thesis: Apple remains a high-quality compounder.

Assumptions:
1. Services revenue grows faster than hardware.
2. Gross margin remains above 43%.
3. Buybacks continue reducing share count.
4. China risk remains manageable.
5. AI device cycle creates replacement demand.
```

Each assumption should have:

```text
id
thesis_id
assumption_text
category
importance
confidence
status
last_reviewed
falsification_trigger
source_links
```

Categories:

- revenue growth
- margin
- capital allocation
- competitive position
- regulatory risk
- macro risk
- narrative
- valuation

## 13.2 Falsification Triggers

For each thesis assumption, define what would prove it wrong.

Example:

```text
Assumption: Services growth remains resilient.
Falsification trigger: Services growth falls below 5% YoY for 2 consecutive quarters.
```

This is powerful because it prevents emotional holding.

## 13.3 Evidence Ledger

Every company should have an evidence ledger:

| Evidence | Supports | Weakens | Contradicts | Source | Date | Confidence |
|---|---|---|---|---|---|---|

This lets the app answer:

```text
What evidence has accumulated for or against my thesis?
```

## 13.4 Variant Perception Map

A major investment question is:

```text
What do I believe that the market does not?
```

Create a feature called Variant Perception.

Fields:

```text
market_belief
my_belief
evidence_for_my_belief
evidence_against_my_belief
how_price_reflects_market_belief
what_would_close_the_gap
confidence
```

Example:

```text
Market belief: Margins have peaked.
My belief: Margins normalize slightly but remain structurally higher due to services mix.
Evidence: Recent segment trends, services growth, historical margin resilience.
Risk: Hardware weakness could offset services.
```

## 13.5 Price-Implied Expectations

Connect DCF with market price.

The app should answer:

```text
At the current price, what growth/margin/ROIC is the market implying?
```

This is often more useful than saying your DCF value is `$151.89`.

Features:

- implied revenue growth
- implied operating margin
- implied terminal ROIC
- implied reinvestment efficiency
- implied terminal multiple
- comparison to company history
- comparison to peer history

## 13.6 Decision Journal

Every investment decision should be logged.

Decision types:

- add to watchlist
- start research
- reject
- monitor
- increase conviction
- decrease conviction
- update valuation
- update thesis
- add to portfolio manually
- trim manually

Fields:

```text
company_id
portfolio_id nullable
decision_type
reason
supporting_evidence_ids
valuation_case_id
price_at_decision
portfolio_weight_at_decision
confidence
what_would_change_my_mind
created_at
```

This makes the app useful for learning from mistakes.

## 13.7 Pre-Mortem Generator

Before adding a company to portfolio/watchlist, ask:

```text
Assume this investment underperforms badly over the next 2 years. What were the most likely reasons?
```

Outputs:

- valuation risk
- execution risk
- margin risk
- competitive risk
- macro risk
- regulatory risk
- narrative reversal risk
- data uncertainty

This should be source-backed where possible.

## 13.8 Contradiction Engine

The app should actively search for evidence against the thesis.

For each company:

```text
Top evidence supporting thesis
Top evidence weakening thesis
Top evidence contradicting thesis
Unresolved questions
```

Most tools reinforce existing beliefs. This one should challenge them.

## 13.9 Decision Readiness Score

Before the user makes a decision, calculate readiness.

Not a buy/sell recommendation.

Example:

```text
Decision Readiness: 64/100

Missing:
- No reverse DCF completed
- No bear case written
- No peer comparison
- Latest 10-Q not reviewed
- Thesis assumptions not falsifiable
```

Inputs:

- thesis completeness
- valuation completeness
- evidence coverage
- risk coverage
- contradiction coverage
- portfolio impact understood
- data freshness

## 13.10 Opportunity Cost View

Every decision competes with alternatives.

Feature:

```text
Compare this company against current portfolio holdings and watchlist alternatives.
```

Questions:

- Is this better than adding to an existing holding?
- Is this better than cash?
- Is this better than a sector ETF?
- Does it duplicate an existing exposure?
- Does it improve or worsen diversification?

## 13.11 Portfolio Marginal Impact

Before adding a holding, show:

```text
If added at 5% weight, portfolio impact:
- Tech exposure increases from 42% to 47%
- AI infrastructure exposure increases from 25% to 31%
- Top 5 concentration increases from 63% to 67%
- Portfolio narrative correlation increases
```

This is much more useful than a holdings table.

## 13.12 Signal Decay Tracker

Some information matters for a day. Some matters for years.

Add `signal_half_life`:

| Signal type | Half-life |
|---|---:|
| Tweet/social rumor | hours/days |
| News headline | days/weeks |
| Earnings guidance | quarter |
| 10-K risk language | year+ |
| Structural thesis change | multi-year |

Use it to avoid over-weighting stale narratives.

## 13.13 Catalyst Calendar

Track future events:

- earnings date
- investor day
- product launch
- regulatory deadline
- court decision
- macro release
- lockup expiry
- dividend date
- index inclusion/rebalance

Each catalyst should link to:

- affected companies
- thesis assumptions
- expected evidence
- what to watch

## 13.14 Base Rate Library

Investors overfit stories. Add base rates.

Examples:

- high growth companies with declining margins
- companies trading above 30x earnings
- turnarounds with negative FCF
- cyclicals near peak margins
- serial acquirers
- high ROIC compounders

The app should eventually compare the company to historical base rates.

## 13.15 Narrative vs Fundamentals Divergence

Build a feature that flags:

```text
Narrative improving while fundamentals weakening
Fundamentals improving while narrative ignored
Valuation expanding faster than fundamentals
Risk language worsening while sentiment remains positive
```

This is a strong investment research edge.

## 13.16 Market Belief Timeline

Track how the market story changed:

```text
January: AI beneficiary
March: Margin pressure
May: Regulatory risk
June: Reacceleration thesis
```

For each narrative phase, show:

- sources
- price reaction
- volume reaction
- sentiment
- whether it was confirmed or contradicted later

## 13.17 Confidence vs Conviction Split

Do not use one generic confidence score.

Separate:

```text
Evidence Confidence: How reliable is the data?
Model Confidence: How complete is the valuation model?
Thesis Conviction: How strongly does the user believe the thesis?
Portfolio Risk: How much damage if wrong?
```

This avoids false precision.

## 13.18 What Would Change My Mind Panel

Every company page should include:

```text
What would change my mind?
```

Examples:

- revenue growth below X
- margin below Y
- debt above Z
- management guidance cut
- risk factor language worsens
- key narrative contradicted
- valuation exceeds my fair value range

This is one of the most important features.

---

# 14. Scoring System Upgrades

## 14.1 Keep event score separate from portfolio score

Event score should answer:

```text
How important is this information objectively?
```

Portfolio score should answer:

```text
How important is this information to me?
```

## 14.2 Scores needed

| Score | Meaning |
|---|---|
| Credibility | Is the source reliable? |
| Novelty | Is this new or repeated? |
| Impact | Could this affect business value? |
| Thesis relevance | Does this affect an assumption? |
| Portfolio relevance | Do I own this or related exposure? |
| Narrative velocity | Is the market story accelerating? |
| Valuation pressure | Is valuation stretched vs assumptions? |
| Data confidence | Is the data complete and fresh? |
| Decision readiness | Is there enough evidence to make a judgment? |

## 14.3 Portfolio priority formula

```text
portfolio_priority_score =
    event_priority_score * 0.40
  + ownership_weight_score * 0.20
  + thesis_relevance_score * 0.20
  + valuation_gap_score * 0.10
  + narrative_velocity_score * 0.05
  + data_confidence_score * 0.05
```

## 14.4 Score explanation format

Every score should return:

```json
{
  "score_name": "portfolio_priority",
  "value": 82,
  "label": "high",
  "direction": "worsening",
  "confidence": "medium",
  "inputs": [
    {
      "name": "event_priority_score",
      "value": 76,
      "weight": 0.40,
      "contribution": 30.4,
      "explanation": "High-priority SEC filing change."
    }
  ],
  "summary": "High priority because the company is 18% of the portfolio and the filing change affects a core thesis assumption."
}
```

---

# 15. API/Data Provider Strategy

## 15.1 Immediate sources

Use now:

- manual portfolio entries
- manual market prices
- SEC EDGAR
- RSS feeds
- user-entered thesis notes

## 15.2 Next sources

Add after stability:

- FRED for macro data
- Alpha Vantage or Financial Modeling Prep for prices/fundamentals
- GDELT for news/event/narrative layer
- official Reddit API only if legally needed
- OpenAI/Gemini only after AI provenance is implemented

## 15.3 Do not add yet

- broker sync
- X/Twitter scraping
- Reddit HTML scraping
- paid terminal integrations
- options flow
- real-time trading feeds

## 15.4 Provider abstraction

Do not hardcode one provider everywhere.

Create:

```text
MarketDataProvider
FundamentalsProvider
MacroDataProvider
NewsProvider
AiProvider
```

Each provider should return a normalized internal format.

Example:

```text
backend/app/providers/market_data/base.py
backend/app/providers/market_data/alpha_vantage.py
backend/app/providers/market_data/fmp.py
backend/app/providers/macro/fred.py
backend/app/providers/ai/mock.py
backend/app/providers/ai/openai.py
backend/app/providers/ai/gemini.py
```

## 15.5 API key security

Rules:

- `.env` only
- never frontend
- never logs
- no hardcoded fallback key
- provider status page should show configured/not configured, not the key itself

---

# 16. Cybersecurity Requirements

## 16.1 Must-have now

- `.env` ignored by Git
- `.env.example` has placeholders only
- no secrets in frontend
- no secrets in logs
- health endpoint does not leak config
- Docker setup documented
- backend input validation
- API errors do not expose stack traces to frontend
- narrow frontend proxy only
- no arbitrary user-controlled URL fetches

## 16.2 Must-have before imports

CSV import must:

- validate every row
- reject invalid quantities/prices/dates
- show row-level errors
- escape formula injection values starting with `=`, `+`, `-`, `@`
- never execute spreadsheet formulas

## 16.3 Must-have before AI

AI outputs must store:

- model name
- prompt version
- input hash
- generated timestamp
- source IDs
- limitations
- confidence label
- review status

AI must not:

- invent sources
- auto-change thesis notes
- auto-change DCF assumptions
- generate buy/sell recommendations
- receive private portfolio data unless explicitly required and logged

## 16.4 Must-have before deployment

Do not deploy publicly until you add:

- authentication
- authorization
- CSRF review
- CORS restriction
- HTTPS
- secure secret storage
- rate limits
- logging policy
- backup policy
- user data privacy review

## 16.5 Broker integration rule

Do not store broker passwords.

Broker sync later must use official OAuth/token flows only.

---

# 17. File Structure Simplification

## 17.1 Frontend target structure

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

## 17.2 Backend target structure

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

## 17.3 Rule

Do not reorganize the entire repo in one diff. Move one module group at a time only after tests pass.

---

# 18. Interactive Graph Roadmap

## 18.1 Priority charts

Build these first:

| Chart | Page | Why |
|---|---|---|
| Portfolio exposure bar chart | Portfolio | Shows concentration |
| Top holdings ranked bar | Portfolio | Shows biggest risk drivers |
| Portfolio value line | Portfolio | Tracks value over time |
| DCF sensitivity heatmap | Valuation | Shows assumption risk |
| Terminal value split | Valuation | Shows if DCF is terminal-value-driven |
| ROIC vs WACC line | Valuation | Shows value creation/destruction |
| Filing events timeline | Company | Shows primary-source changes |
| Narrative velocity line | Narratives | Shows story momentum |
| Evidence timeline | Research/Company | Shows source evolution |

## 18.2 Chart rules

Every chart must include:

- title
- units
- source
- last updated
- tooltip
- loading state
- empty state
- error state
- stale state

Avoid decorative charts.

---

# 19. Codex Skills To Build

Create skills or repeated prompt files for:

## 19.1 Reality Audit Skill

Purpose:

- compare docs vs code
- find mocked/hardcoded functionality
- list missing endpoints
- identify broken migrations

## 19.2 API Envelope Skill

Purpose:

- wrap backend responses
- update frontend fetch client
- add error/stale/mock handling

## 19.3 Security Review Skill

Purpose:

- check secrets
- check SSRF risks
- check CSV injection
- check unsafe proxying
- check AI provenance
- check broker credential risks

## 19.4 Portfolio Analytics Skill

Purpose:

- value holdings
- calculate exposure
- concentration warnings
- marginal impact
- portfolio-aware alerts

## 19.5 DCF Engine Skill

Purpose:

- revenue-driven DCF
- reinvestment
- ROIC
- WACC builder
- terminal guardrails
- sensitivity tables
- reverse DCF

## 19.6 Source-Backed AI Skill

Purpose:

- AI outputs with provenance
- source citations
- input hashes
- prompt versioning
- no recommendations

## 19.7 UI Component Skill

Purpose:

- reuse components
- avoid 800-line pages
- enforce loading/error/stale/empty states
- build charts consistently

---

# 20. Exact Next Codex Prompt

Use this now:

```text
Read docs/00-current-state.md, docs/08-execution-runbook.md, docs/agent_capabilities_and_limitations.md, docs/06-security-threat-model.md, backend/app, frontend/app, frontend/components, backend/alembic/versions, and docker-compose.yml. For historical UI context only, see docs/archive/needs-review/design-brief.md.

Do not build new product features yet.

Task 1: Reality audit.
Check actual code against the docs and return:
1. Implemented features.
2. Partially implemented features.
3. Mocked or hardcoded UI.
4. Missing backend endpoints.
5. Broken or inconsistent API response shapes.
6. Alembic migration chain status.
7. Docker/frontend/backend connection risks.
8. Any hardcoded secrets or unsafe environment handling.
9. Exact next 5 implementation tasks.

Task 2: If and only if the audit is complete, implement the smallest safe next step:
- Add or standardize GET /api/health if missing.
- Add ApiResponse, ApiMeta, and ApiError schemas.
- Convert only health and one low-risk read endpoint to the standard {data, meta, errors} envelope.
- Update frontend fetch client to handle both old and new response shapes during migration.
- Add ErrorState, LoadingState, EmptyState, and StaleDataBanner components if missing.
- Add tests.

Do not refactor all routes in one pass.
Do not build DCF changes yet.
Do not add AI.
Do not add social scraping.
Do not add live broker sync.
Do not expose secrets.

After completion, report:
- files inspected
- files changed
- tests run
- manual browser test steps
- known limitations
- next task
```

---

# 21. After API Envelope: Next 10 Build Tasks

Once the app runs and the response envelope is started, follow this order.

## Task 1: Complete API envelope migration

Convert routes gradually.

Priority:

1. health
2. dashboard
3. portfolio
4. companies
5. valuation
6. ingestion
7. scores
8. narratives
9. research

## Task 2: Data Health page

Build a Data Health page that shows:

- backend health
- database health
- SEC configured/not configured
- RSS status
- market data configured/not configured
- AI configured/not configured
- last successful ingestion
- failed processing runs
- stale data warnings

## Task 3: Portfolio valuation and exposure

If not already reliable:

- holdings market value
- cash
- total value
- cost basis
- unrealized P&L
- sector exposure
- industry exposure
- theme exposure
- concentration warnings

## Task 4: DCF engine backend

Build revenue-driven DCF service with tests.

Do not start with UI.

## Task 5: DCF UI redesign

Build:

- Story
- Assumptions
- Valuation
- Sensitivity
- Reverse DCF
- Notes

## Task 6: Score explainability

Build:

- ScoreBreakdown component
- score endpoints
- factor contribution display

## Task 7: Thesis assumption engine

Build:

- thesis assumptions
- falsification triggers
- evidence links
- assumption status

## Task 8: Evidence ledger

Build:

- evidence support/weakens/contradicts tagging
- evidence trail drawer
- source highlights later

## Task 9: Decision journal

Build:

- decision log
- price at decision
- valuation at decision
- evidence links
- what would change my mind

## Task 10: Narrative divergence engine

Build later:

- narrative vs fundamentals divergence
- sentiment vs filing contradiction
- valuation vs growth mismatch

---

# 22. What Should Guide Investment Decisions In This App

The app should not decide for the user. It should structure the decision.

The strongest decision inputs are:

## 22.1 Evidence quality

- primary source vs secondary source
- source recency
- source reliability
- corroboration
- contradiction
- data freshness

## 22.2 Business quality

- revenue growth
- margins
- ROIC
- reinvestment needs
- cash conversion
- balance sheet strength
- competitive durability

## 22.3 Valuation

- price-implied growth
- intrinsic value range
- margin of safety
- terminal value dependence
- sensitivity to WACC/growth/margins
- peer relative valuation

## 22.4 Thesis strength

- assumptions are explicit
- assumptions are falsifiable
- evidence supports assumptions
- contradictory evidence is acknowledged
- thesis has been updated when facts changed

## 22.5 Portfolio role

- position size
- exposure overlap
- diversification impact
- downside contribution
- correlation to existing holdings
- marginal improvement vs current portfolio

## 22.6 Narrative and sentiment

- narrative velocity
- evidence behind narrative
- whether narrative is priced in
- whether sentiment diverges from fundamentals
- whether narrative is rising or fading

## 22.7 Risk and uncertainty

- company-specific risk
- macro risk
- valuation risk
- regulatory risk
- liquidity risk
- data quality risk
- model risk

## 22.8 Decision discipline

- pre-mortem completed
- reverse DCF completed
- bear case written
- exit/falsification triggers defined
- opportunity cost reviewed
- decision logged

---

# 23. Unique Features Worth Building

These are the features that could make the app meaningfully better than most current personal finance or stock research tools.

## 23.1 Thesis-Price-Evidence Triangle

Show 3 things on one screen:

```text
My thesis
Market-implied expectations
Evidence trend
```

Flag mismatches:

- thesis bullish, evidence weakening
- thesis bullish, price already implies perfection
- evidence improving, market still pessimistic
- narrative rising, fundamentals not confirming

## 23.2 Assumption Heatmap

For each thesis/DCF assumption, show:

| Assumption | Importance | Confidence | Evidence trend | Last updated | Risk |
|---|---:|---:|---|---|---|

This makes the thesis inspectable.

## 23.3 Contrarian Evidence Inbox

An inbox that only shows evidence against your thesis.

Purpose:

- reduce confirmation bias
- prevent blind conviction
- force review of negative signals

## 23.4 Investment Autopsy

After a decision performs poorly, the app helps review:

- what you believed
- what evidence existed
- what you ignored
- which assumptions failed
- whether failure was bad process or bad luck

## 23.5 Watchlist Triage

Every watchlist company gets a status:

- ignore
- monitor
- research soon
- high priority
- waiting for valuation
- waiting for catalyst
- rejected

This prevents watchlists from becoming dumping grounds.

## 23.6 Evidence Aging

Every evidence item decays depending on type.

Example:

- social sentiment decays fast
- 10-K risk language decays slow
- thesis notes decay until reviewed
- price momentum decays medium-fast

## 23.7 Decision Checklist Generator

Before logging a decision, app asks:

- Did you review latest filing?
- Did you run reverse DCF?
- Did you define falsification triggers?
- Did you compare opportunity cost?
- Did you review contradictory evidence?
- Did you check portfolio concentration?

## 23.8 Signal Stack

For any company, show:

```text
Fundamentals: improving
Valuation: expensive
Narrative: rising
Sentiment: mixed
Filing risk: worsening
Portfolio exposure: high
Data confidence: medium
```

Then explain the conflict, not just average it.

## 23.9 Market Memory

Store what the app believed at past dates.

Examples:

- score history
- narrative history
- thesis changes
- valuation changes
- decision logs

This lets the user learn over time.

## 23.10 Decision Impact Simulator

Before adding a hypothetical position:

```text
If AAPL added at 5% weight:
- portfolio tech exposure rises by X
- top 5 concentration rises by Y
- USD exposure rises by Z
- AI narrative exposure rises by A
- downside scenario loss contribution is B
```

This is more useful than many normal portfolio trackers.

---

# 24. Non-Negotiables

1. No fake intelligence.
2. No unlabeled mock data.
3. No hidden stale data.
4. No frontend claims unsupported by backend.
5. No AI output without source provenance.
6. No buy/sell recommendations.
7. No public deployment without auth/security.
8. No broker passwords.
9. No social scraping that violates terms.
10. No giant Codex diffs.
11. No DCF output without assumption warnings.
12. No score without explanation.
13. No portfolio alert without position/exposure context.
14. No secrets in frontend.
15. No decorative charts.

---

# 25. Final Recommended Build Sequence

## Phase A: Stabilize

- fix Docker/backend/frontend
- fix migrations
- health endpoint
- app opens consistently

## Phase B: Audit

- docs vs code
- mocks vs real
- endpoints
- migrations
- secrets

## Phase C: Trust Infrastructure

- API envelope
- global data states
- Data Health page
- processing run visibility

## Phase D: Portfolio Intelligence

- valuation from prices
- exposures
- concentration
- portfolio-aware alerts
- marginal impact simulator

## Phase E: Serious DCF

- revenue-driven forecast
- reinvestment
- ROIC
- WACC builder
- equity bridge
- sensitivity
- reverse DCF
- model warnings

## Phase F: Thesis Intelligence

- assumptions
- falsification triggers
- evidence ledger
- contradiction engine
- thesis drift

## Phase G: Research Workspace

- source-backed AI
- research sessions
- evidence saving
- memo builder

## Phase H: Narrative Intelligence

- narrative clusters
- narrative velocity
- narrative vs fundamentals divergence
- priced-in tracker

## Phase I: Decision System

- decision journal
- readiness score
- pre-mortem
- opportunity cost view
- investment autopsy

---

# 26. The next thing to actually do

Do this now:

1. Get the app running reliably.
2. Run the reality audit prompt.
3. Implement API envelope on health + one low-risk endpoint only.
4. Add frontend states.
5. Then build the proper DCF backend engine.

Do not jump straight into redesigning the DCF UI before the backend and API state layer are trustworthy.

A serious app is not the one with the most screens. It is the one where every number, claim, score, and warning can be traced back to either:

- a source
- a calculation
- a user assumption
- or a clearly labeled model interpretation

That is the standard.
