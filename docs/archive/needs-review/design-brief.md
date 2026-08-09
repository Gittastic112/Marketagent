# Market Intelligence App: Frontend Redesign and Backend Alignment Brief

## Purpose of this document

This document is a full product, frontend, backend, and documentation amendment brief for the Market Intelligence App.

The goal is not to make the application prettier. The goal is to make it a serious, usable market intelligence system that helps a user understand:

1. What is happening in the market
2. Why it matters
3. What evidence supports the claim
4. How reliable the system thinks the claim is
5. What changed recently
6. What the user should investigate next

The existing app should be amended around this design direction. Any current documentation should be updated to reflect the product direction, frontend architecture, backend requirements, data model, API requirements, implementation checklist, and known issues described here.

This document should be treated as a guiding specification, not as a request to rewrite the app blindly.

---

# 1. Product north star

## 1.1 One-line description

The Market Intelligence App is a financial research and portfolio intelligence cockpit that combines portfolio analytics, company research, SEC filings, news flow, narrative tracking, sentiment, scoring, and valuation tools into a source-backed research workflow.

## 1.2 Core user question

Every screen should help answer:

> What is happening, why does it matter, how reliable is it, and what should I inspect next?

## 1.3 What the app should not become

The app should not become:

- A generic SaaS dashboard
- A crypto-style trading toy
- A random collection of charts
- An AI chatbot with dashboards attached
- A fake Bloomberg clone
- A student project with cards and placeholder data
- A beautiful but untrustworthy analytics app
- A frontend that invents features the backend cannot support

## 1.4 Design principle

The core design rule is:

> Never add visual complexity unless it improves decision clarity.

---

# 2. Target product personality

## 2.1 Desired feel

The interface should feel:

- Serious
- Analytical
- Trustworthy
- Fast
- Dense but readable
- Source-backed
- Calm
- Professional
- Useful for actual research

## 2.2 Useful product references

The app can borrow selectively from:

| Reference | What to borrow |
|---|---|
| Koyfin | Clean financial dashboard structure |
| Bloomberg Terminal | Dense information hierarchy, not visual clutter |
| Perplexity | Source-backed research answers |
| AlphaSense | Research workflow and document intelligence |
| PitchBook | Company and market data organization |
| TradingView | Chart interaction patterns |
| Linear | Crisp layout, navigation, and interaction quality |
| Notion | Research workspace flexibility |

The goal should be closer to:

> Koyfin + Perplexity + research cockpit

It should not try to become Bloomberg on day 1.

---

# 3. Primary workflows

The app should be redesigned around workflows, not pages.

## 3.1 Daily intelligence workflow

The user opens the app and sees:

1. Portfolio overview
2. Major market or watchlist changes
3. SEC filings that matter
4. News and narrative shifts
5. Risk changes
6. Suggested research tasks

Primary question:

> What changed since I last checked?

## 3.2 Portfolio monitoring workflow

The user wants to understand:

1. What they own
2. What they are exposed to
3. Where concentration exists
4. Which holdings changed most
5. Which narratives affect the portfolio
6. Which risks require attention

Primary question:

> What am I actually exposed to?

## 3.3 Company research workflow

The user searches a ticker and sees:

1. Snapshot
2. Price and financial metrics
3. AI summary
4. What changed recently
5. SEC filings
6. News flow
7. Narratives
8. Risks
9. Peer comparison
10. DCF or valuation view
11. Sources and evidence

Primary question:

> Do I understand this company better after 5 minutes?

## 3.4 Narrative intelligence workflow

The user wants to track market stories.

The system should show:

1. Narrative name
2. Related companies
3. Source velocity
4. Sentiment direction
5. Evidence strength
6. Contradictory evidence
7. Price reaction
8. Timeline of narrative evolution

Primary question:

> Is this narrative real, rising, fading, or already priced in?

## 3.5 Research workspace workflow

The user wants to investigate an idea.

The workspace should allow:

1. Asking a research question
2. Pulling relevant filings and news
3. Saving evidence
4. Comparing companies
5. Creating notes
6. Building an investment memo
7. Exporting or saving research

Primary question:

> Can I convert scattered information into a research view or memo?

## 3.6 Valuation workflow

The user wants to estimate value.

The DCF tool should allow:

1. Revenue growth assumptions
2. Margin assumptions
3. Reinvestment or capex assumptions
4. WACC
5. Terminal growth
6. Scenario comparison
7. Sensitivity table
8. Saved assumptions
9. Explanation of implied value

Primary question:

> How do my assumptions change the valuation?

---

# 4. Information hierarchy

Every major page should use a 4-layer hierarchy.

## 4.1 Layer 1: Executive summary

At the top of major pages, show:

- What changed
- Why it matters
- Current signal
- Main risks
- Confidence level
- Suggested next action

Example:

```text
Overall Signal: Neutral-positive
Narrative Momentum: Rising
Fundamental Risk: Moderate
Valuation Pressure: High
Latest Driver: Margin concerns offset by strong revenue growth
Confidence: Medium
Next Step: Review latest 10-Q and peer valuation spread
```

## 4.2 Layer 2: Key metrics

Show only the most important top-level metrics first.

Examples:

- Price change
- Market cap
- Revenue growth
- Margin trend
- Valuation multiple
- News velocity
- Sentiment score
- Narrative score
- Risk score
- Filing activity
- Portfolio weight
- Exposure contribution

Avoid dumping 30 metrics at once.

## 4.3 Layer 3: Evidence and sources

All important AI claims should connect to evidence.

Evidence types:

- SEC filing
- News article
- Earnings transcript
- Company presentation
- Market data
- Reddit or forum discussion
- Analyst note if available
- Internal calculation
- AI interpretation

Every claim should clearly distinguish between:

1. Fact
2. Calculation
3. Source summary
4. AI interpretation
5. User-entered assumption

## 4.4 Layer 4: Deep dive

Detailed views should live below summary and evidence.

Examples:

- Full chart
- Full filing summary
- News feed
- Narrative history
- Peer comparison
- Portfolio decomposition
- DCF assumptions
- Source list
- Scoring breakdown

---

# 5. Frontend design system

## 5.1 General visual direction

Use a dark-first financial dashboard interface.

Guidelines:

- Dark background, but not pure black
- Neutral surfaces
- Subtle borders
- Strong hierarchy
- Minimal gradients
- High contrast text
- Tables and charts should be highly readable
- Green and red should be used carefully
- Do not rely on color alone for meaning
- Use whitespace to separate thinking zones, not to make the app look empty

## 5.2 Typography

Use clean sans-serif typography.

Requirements:

- Clear hierarchy between page title, section title, metric value, label, and annotation
- Use tabular numerals for financial values
- Avoid oversized marketing-style headings inside the actual app
- Use compact but readable line heights in tables

CSS requirement:

```css
font-variant-numeric: tabular-nums;
```

Use this for:

- Prices
- Percentages
- Valuation numbers
- Financial statement figures
- Portfolio weights
- Scores
- Dates and times where alignment matters

## 5.3 Color system

The color system should be restrained.

Use color categories:

| Category | Use |
|---|---|
| Background | App base and page canvas |
| Surface | Cards, tables, panels |
| Border | Low-emphasis separators |
| Text primary | Main content |
| Text secondary | Labels and descriptions |
| Positive | Positive return, improving signal |
| Negative | Negative return, worsening signal |
| Warning | Stale data, moderate risk |
| Critical | Broken ingestion, severe risk |
| Neutral | Mixed or unchanged signal |
| Accent | Selected nav, primary action, active state |

Avoid:

- Random neon colors
- Purple AI gradients
- Heavy shadows
- Overly bright chart palettes
- Too many semantic colors on the same page

## 5.4 Layout

Preferred layout:

```text
Top bar:
  Global search
  Current date / data freshness
  User controls / settings

Left sidebar:
  Dashboard
  Portfolio
  Companies
  Narratives
  Research
  Valuation
  Data / Ingestion
  Settings

Main content:
  Page-specific intelligence view

Right panel where useful:
  Evidence
  Alerts
  Current research context
  AI explanation
```

## 5.5 Desktop-first, responsive-aware

The app is primarily a desktop research product.

Priority:

1. Desktop dashboard usability
2. Laptop layout
3. Tablet usability
4. Mobile read-only usability

Mobile does not need to expose every advanced feature immediately, but it should not break.

---

# 6. Core frontend pages

## 6.1 Dashboard / Intelligence Brief

### Purpose

The dashboard should answer:

> What do I need to know today?

### Required sections

1. Top intelligence summary
2. Portfolio snapshot
3. Top movers
4. Watchlist changes
5. SEC filing alerts
6. News velocity changes
7. Narrative shifts
8. Risk alerts
9. Suggested research tasks
10. Data freshness panel

### Required cards

- Portfolio value or placeholder if no portfolio exists
- Daily/weekly change
- Largest portfolio mover
- Highest-risk holding
- Highest narrative momentum
- Recent important filing
- Top unresolved alert

### Empty state

If the user has no portfolio:

```text
No portfolio added yet.
Add holdings or start with a watchlist to generate an intelligence brief.
```

Provide actions:

- Add holding
- Import CSV
- Create watchlist
- Search ticker

### Backend implications

The backend needs endpoints for:

- Dashboard summary
- Portfolio metrics
- Latest alerts
- Filing updates
- News velocity
- Narrative changes
- Data freshness
- Suggested research tasks

Proposed API:

```http
GET /api/dashboard/brief
GET /api/dashboard/freshness
GET /api/alerts/recent
```

---

## 6.2 Portfolio page

### Purpose

The portfolio page should answer:

> What am I actually exposed to?

### Required sections

1. Portfolio overview
2. Holdings table
3. Sector exposure
4. Industry exposure
5. Theme exposure
6. Concentration risk
7. Risk contribution
8. Narrative exposure
9. Holdings affected by recent filings or news
10. Portfolio notes

### Required table columns

Holdings table should include:

- Ticker
- Company
- Quantity
- Average cost if available
- Current price
- Market value
- Portfolio weight
- Daily change
- 1-week change
- 1-month change
- Sector
- Industry
- Active signal
- Risk level
- Last updated

### Exposure analysis

The app should not only show:

> You own 8 stocks.

It should infer:

> You own 3 major themes.

Example themes:

- AI infrastructure
- Indian capex cycle
- Rate-sensitive financials
- US mega-cap tech
- Consumer discretionary
- Energy transition
- Defense
- Cloud software

### Charts

Use:

- Bar chart for sector and theme exposure
- Ranked bar chart for largest positions
- Line chart for portfolio value over time
- Avoid pie charts for complex portfolio exposure
- Treemap is acceptable for portfolio weight if implemented cleanly

### Backend implications

Need models and endpoints for:

- Holdings
- Portfolio snapshots
- Price data
- Sector and industry classification
- Theme classification
- Risk contribution
- Portfolio alerts

Proposed API:

```http
GET /api/portfolio
POST /api/portfolio/holdings
PUT /api/portfolio/holdings/{holding_id}
DELETE /api/portfolio/holdings/{holding_id}
GET /api/portfolio/exposures
GET /api/portfolio/risk
GET /api/portfolio/narrative-exposure
```

---

## 6.3 Company intelligence page

### Purpose

The company page should answer:

> What is going on with this company?

### Route

```text
/companies/[ticker]
```

### Required sections

1. Ticker header
2. Intelligence summary
3. Price and key metrics
4. What changed recently
5. Financial trends
6. SEC filings
7. News flow
8. Narrative exposure
9. Sentiment
10. Risks
11. Peer comparison
12. Valuation
13. Sources

### Ticker header

Should include:

- Ticker
- Company name
- Exchange
- Sector
- Industry
- Market cap
- Current price
- Daily move
- Last updated
- Watchlist button
- Portfolio ownership indicator

### Intelligence summary

Should include:

- Overall signal
- Fundamental score
- Valuation score
- Narrative score
- Sentiment score
- Risk score
- Confidence
- Brief explanation
- Latest important event
- Suggested next action

### What changed recently

Should show recent changes across:

- Price
- News volume
- Sentiment
- Filings
- Narrative direction
- Financial estimates if available
- Risk indicators

### SEC filings section

Should show:

- Latest 10-K
- Latest 10-Q
- Latest 8-K
- Filing date
- Filing type
- AI summary
- Key excerpts
- Risks identified
- Link to source
- Ingestion status

### News flow section

Should show:

- Article title
- Source
- Date
- Related narrative
- Sentiment
- Relevance score
- Summary
- Source link

### Narrative section

Should show:

- Active narratives
- Direction
- Strength
- Evidence
- Contradictory signals
- Timeline

### Backend implications

Need company intelligence aggregation endpoint.

Proposed API:

```http
GET /api/companies/{ticker}
GET /api/companies/{ticker}/summary
GET /api/companies/{ticker}/metrics
GET /api/companies/{ticker}/filings
GET /api/companies/{ticker}/news
GET /api/companies/{ticker}/narratives
GET /api/companies/{ticker}/sentiment
GET /api/companies/{ticker}/risks
GET /api/companies/{ticker}/peers
GET /api/companies/{ticker}/valuation
GET /api/companies/search?q=
```

---

## 6.4 Narrative intelligence page

### Purpose

The narrative page should answer:

> What stories are moving or shaping the market?

### Required sections

1. Narrative list
2. Narrative detail panel
3. Source velocity chart
4. Sentiment trend
5. Related companies
6. Evidence
7. Contradictory evidence
8. Price reaction
9. Confidence
10. Timeline

### Narrative fields

Each narrative should include:

- Name
- Description
- Related tickers
- Related sectors
- Source count
- Source velocity
- Sentiment direction
- Evidence strength
- Confidence
- First seen date
- Last updated date
- Status

Statuses:

- Emerging
- Rising
- Stable
- Fading
- Contradicted
- Priced in
- Unclear

### Critical UX distinction

The UI must separate:

1. What people are saying
2. What data supports
3. What price has already reflected
4. What remains uncertain

### Backend implications

Need narrative extraction and tracking.

Proposed API:

```http
GET /api/narratives
GET /api/narratives/{narrative_id}
GET /api/narratives/{narrative_id}/timeline
GET /api/narratives/{narrative_id}/sources
GET /api/narratives/{narrative_id}/related-companies
GET /api/narratives/{narrative_id}/price-reaction
POST /api/narratives/extract
```

Backend tables likely needed:

- narratives
- narrative_sources
- narrative_company_links
- narrative_scores
- narrative_timeline_events

---

## 6.5 Research workspace

### Purpose

The research workspace should answer:

> Can I investigate an idea and turn it into structured research?

### Required sections

1. Research question input
2. Source search results
3. AI answer with evidence
4. Saved notes
5. Related companies
6. Related filings
7. Related narratives
8. Memo builder
9. Export or save research

### AI output rules

Every AI output must include:

- Claim
- Reasoning
- Evidence
- Confidence
- Timestamp
- Contradictory evidence if available
- Source links

Do not show vague claims like:

```text
This company is well-positioned for long-term growth.
```

Instead:

```text
The system sees improving narrative momentum, but confidence is medium because recent news volume is high while filing evidence is limited.
```

### Backend implications

Need research session model.

Proposed API:

```http
POST /api/research/sessions
GET /api/research/sessions
GET /api/research/sessions/{session_id}
POST /api/research/sessions/{session_id}/messages
POST /api/research/sessions/{session_id}/sources
POST /api/research/sessions/{session_id}/notes
POST /api/research/sessions/{session_id}/memo
```

Backend tables likely needed:

- research_sessions
- research_messages
- research_sources
- research_notes
- research_memos

---

## 6.6 Valuation / DCF page

### Purpose

The valuation page should answer:

> What is this company worth under my assumptions?

### Required sections

1. Company selector
2. Base assumptions
3. Revenue forecast
4. Margin forecast
5. Reinvestment or capex assumptions
6. Discount rate
7. Terminal value
8. Scenario outputs
9. Sensitivity table
10. Saved cases
11. Notes and rationale

### Required assumptions

- Starting revenue
- Revenue growth years 1 to 5
- Long-term revenue growth
- Operating margin
- Tax rate
- Reinvestment rate or sales-to-capital ratio
- WACC
- Terminal growth
- Net debt
- Shares outstanding

### Scenarios

At minimum:

- Bear
- Base
- Bull

### Backend implications

Need valuation models and saved assumptions.

Proposed API:

```http
GET /api/valuation/{ticker}
POST /api/valuation/{ticker}/cases
GET /api/valuation/{ticker}/cases
PUT /api/valuation/cases/{case_id}
DELETE /api/valuation/cases/{case_id}
POST /api/valuation/calculate
```

Backend tables likely needed:

- valuation_cases
- valuation_assumptions
- valuation_outputs

---

## 6.7 Data and ingestion page

### Purpose

The data page should answer:

> What data is working, stale, broken, or missing?

This is important for trust.

### Required sections

1. API connection status
2. SEC ingestion status
3. CIK lookup status
4. News ingestion status
5. Price data status
6. Sentiment pipeline status
7. Processing runs
8. Recent failures
9. Retry controls
10. Environment configuration checklist

### Status types

- Healthy
- Warning
- Failed
- Not configured
- Stale
- Partial
- Running

### Backend implications

Need ingestion status and processing run tracking.

Proposed API:

```http
GET /api/ingestion/status
GET /api/ingestion/runs
GET /api/ingestion/runs/{run_id}
POST /api/ingestion/sec/run
POST /api/ingestion/news/run
POST /api/ingestion/prices/run
POST /api/ingestion/retry/{run_id}
```

Backend tables likely needed:

- processing_runs
- ingestion_sources
- ingestion_errors
- sec_companies
- sec_filings
- news_articles
- price_snapshots

---

# 7. Component system

Antigravity should build reusable components, not one-off UI.

## 7.1 Required layout components

```text
components/layout/
  AppShell
  Sidebar
  TopBar
  PageHeader
  RightPanel
  SectionHeader
  EmptyState
  LoadingState
  ErrorState
  StaleDataBanner
```

## 7.2 Required financial components

```text
components/finance/
  TickerHeader
  MetricCard
  FinancialMetricGrid
  HoldingsTable
  ExposureBarChart
  PortfolioSummaryCard
  PeerComparisonTable
  ValuationSummary
  SensitivityTable
```

## 7.3 Required intelligence components

```text
components/intelligence/
  IntelligenceSummary
  SignalBadge
  ConfidenceBadge
  SourcePill
  EvidenceDrawer
  RiskPanel
  NarrativeCard
  InsightTimeline
  ScoreBreakdown
  SuggestedNextActions
```

## 7.4 Required data components

```text
components/data/
  DataFreshnessIndicator
  IngestionStatusCard
  ProcessingRunTable
  ApiConnectionStatus
  RetryIngestionButton
```

## 7.5 Required chart components

```text
components/charts/
  LineTrendChart
  RankedBarChart
  ExposureChart
  SentimentTrendChart
  NarrativeVelocityChart
  PeerScatterChart
  PortfolioValueChart
```

## 7.6 Component rules

Antigravity must follow these rules:

1. Reuse components before creating new ones.
2. Do not create duplicate metric card styles.
3. Do not hardcode mock data unless clearly labeled.
4. Keep chart wrappers consistent.
5. Create loading, empty, error, and stale states.
6. Keep components small and readable.
7. Do not create 800-line pages.
8. Keep business logic out of visual components where possible.

---

# 8. Chart selection rules

Charts should be chosen based on the question being answered.

| User question | Chart type |
|---|---|
| How has price changed? | Line chart |
| How has sentiment changed? | Line chart |
| What changed most? | Ranked bar chart |
| What is portfolio exposure? | Bar chart or treemap |
| How do peers compare? | Scatterplot or grouped bar |
| What is DCF sensitivity? | Heatmap-style table |
| What is narrative source velocity? | Line chart or stacked bar |
| What is risk contribution? | Ranked bar chart |
| What is sector concentration? | Bar chart |
| What are filings over time? | Timeline |

## 8.1 Avoid by default

Avoid:

- Pie charts for complex portfolio exposure
- 3D charts
- Decorative charts
- Charts without axis labels
- Charts without timestamps
- Charts using too many colors
- Charts that hide missing data

## 8.2 Required chart UX

Every chart should have:

- Title
- Short explanation
- Time range control where useful
- Loading state
- Empty state
- Error state
- Last updated timestamp
- Source label
- Tooltip
- Clear units

---

# 9. AI output and trust rules

## 9.1 Every AI insight must include structure

Each AI-generated insight should have:

1. Claim
2. Reasoning
3. Evidence
4. Confidence
5. Timestamp
6. Source references
7. Contradictory evidence if available

## 9.2 Confidence labels

Use:

- Low
- Medium
- High

Do not use fake precision like:

```text
Confidence: 87.4%
```

unless there is a real scoring methodology behind it.

## 9.3 Source-backed claims

Good pattern:

```text
Claim:
Narrative momentum around margin pressure is rising.

Reasoning:
Recent news and discussion increasingly focus on gross margin normalization after a prior period of unusually strong margins.

Evidence:
3 news articles, 1 earnings transcript, 246 forum mentions over 7 days.

Confidence:
Medium

Caution:
The stock price may already reflect some of this concern.
```

Bad pattern:

```text
The company is poised for growth due to strong fundamentals.
```

## 9.4 Separate facts from interpretations

The UI should label:

| Label | Meaning |
|---|---|
| Fact | Direct source or market data |
| Calculation | Derived number |
| AI Summary | Condensed interpretation |
| AI View | Model-generated judgment |
| User Assumption | User-entered input |
| Estimate | Approximation or incomplete data |

---

# 10. Data honesty and state handling

The frontend must expose data quality.

## 10.1 Required data states

Every major data area must support:

- Loading
- Empty
- Error
- Stale
- Partial
- Not configured
- Permission/API issue
- Success

## 10.2 Example stale state

```text
Sentiment score may be stale.
Last successful Reddit ingestion: May 28, 2026, 7:42 PM.
Retry ingestion or check API configuration.
```

## 10.3 Example not configured state

```text
SEC ingestion is not configured.
Add a valid SEC User-Agent in the backend environment configuration.
```

## 10.4 Example partial state

```text
Company summary is partially available.
Financial metrics loaded successfully, but latest filings failed to ingest.
```

## 10.5 Backend implication

Backend responses should include metadata:

```json
{
  "data": {},
  "meta": {
    "last_updated": "2026-05-30T10:00:00Z",
    "source": "SEC",
    "status": "success",
    "is_stale": false,
    "confidence": "medium",
    "warnings": []
  }
}
```

---

# 11. Scoring design

## 11.1 Scoring should be explainable

The score is not useful unless users can inspect why it exists.

Each score should include:

- Score name
- Numeric value if applicable
- Label
- Inputs
- Weighting
- Direction
- Confidence
- Last updated
- Evidence

## 11.2 Proposed score categories

| Score | Meaning |
|---|---|
| Fundamental score | Business and financial trend strength |
| Valuation score | Relative or intrinsic attractiveness |
| Narrative score | Strength and direction of market story |
| Sentiment score | Tone and direction of news/social discussion |
| Risk score | Business, market, filing, and data risks |
| Momentum score | Price and information-flow momentum |
| Confidence score | Reliability of available data and model view |
| Overall signal | Combined view, not a buy/sell recommendation |

## 11.3 Score breakdown UI

Use a `ScoreBreakdown` component.

It should show:

```text
Overall Signal: Neutral-positive

Inputs:
- Fundamental score: 72/100
- Valuation score: 44/100
- Narrative score: 68/100
- Sentiment score: 61/100
- Risk score: 39/100

Confidence: Medium

Main reason:
Improving narrative and fundamentals are offset by valuation pressure.
```

## 11.4 Backend implication

Backend needs score breakdown endpoints.

Proposed API:

```http
GET /api/scores/company/{ticker}
GET /api/scores/portfolio
GET /api/scores/narrative/{narrative_id}
```

Recommended response shape:

```json
{
  "entity_type": "company",
  "entity_id": "AAPL",
  "overall_signal": "neutral_positive",
  "confidence": "medium",
  "scores": [
    {
      "name": "fundamental",
      "value": 72,
      "label": "strong",
      "direction": "improving",
      "weight": 0.25,
      "inputs": ["revenue_growth", "margin_trend", "cash_flow"]
    }
  ],
  "explanation": "Improving fundamentals are offset by valuation pressure.",
  "last_updated": "2026-05-30T10:00:00Z"
}
```

---

# 12. Backend architecture changes required by frontend

The frontend design requires the backend to become more structured and transparent.

## 12.1 Current backend problem to avoid

Do not make the frontend invent intelligence that the backend does not actually provide.

If the backend does not support something yet, the frontend should show:

- Mock data clearly labeled
- Empty state
- Not configured state
- Coming later state
- Data unavailable state

## 12.2 Required backend capability groups

The backend should support:

1. Company master data
2. Portfolio and holdings
3. Price snapshots
4. SEC filings and CIK lookup
5. News ingestion
6. Sentiment analysis
7. Narrative tracking
8. Scoring
9. Research sessions
10. Valuation cases
11. Alerts
12. Processing runs and data freshness

---

# 13. Proposed backend data models

This is not necessarily the final schema, but the existing schema should be amended toward these entities.

## 13.1 Companies

```text
companies
  id
  ticker
  name
  exchange
  cik
  sector
  industry
  country
  currency
  market_cap
  created_at
  updated_at
```

## 13.2 Portfolio holdings

```text
portfolio_holdings
  id
  ticker
  company_id
  quantity
  average_cost
  currency
  user_notes
  created_at
  updated_at
```

## 13.3 Price snapshots

```text
price_snapshots
  id
  company_id
  ticker
  price
  open
  high
  low
  close
  volume
  date
  source
  created_at
```

## 13.4 SEC filings

```text
sec_filings
  id
  company_id
  ticker
  cik
  accession_number
  filing_type
  filing_date
  report_date
  sec_url
  raw_text_path
  summary
  key_risks
  status
  created_at
  updated_at
```

## 13.5 News articles

```text
news_articles
  id
  title
  source
  url
  published_at
  tickers
  summary
  sentiment_label
  sentiment_score
  relevance_score
  created_at
```

## 13.6 Narratives

```text
narratives
  id
  name
  description
  status
  confidence
  first_seen_at
  last_seen_at
  created_at
  updated_at
```

## 13.7 Narrative sources

```text
narrative_sources
  id
  narrative_id
  source_type
  source_id
  relevance_score
  evidence_summary
  created_at
```

## 13.8 Narrative company links

```text
narrative_company_links
  id
  narrative_id
  company_id
  ticker
  relationship_type
  strength
  created_at
```

## 13.9 Scores

```text
scores
  id
  entity_type
  entity_id
  score_type
  value
  label
  direction
  confidence
  explanation
  inputs_json
  created_at
  updated_at
```

## 13.10 Research sessions

```text
research_sessions
  id
  title
  question
  status
  created_at
  updated_at
```

## 13.11 Research messages

```text
research_messages
  id
  session_id
  role
  content
  citations_json
  confidence
  created_at
```

## 13.12 Valuation cases

```text
valuation_cases
  id
  ticker
  company_id
  case_name
  scenario
  assumptions_json
  outputs_json
  notes
  created_at
  updated_at
```

## 13.13 Alerts

```text
alerts
  id
  entity_type
  entity_id
  alert_type
  severity
  title
  description
  source
  status
  created_at
  resolved_at
```

## 13.14 Processing runs

```text
processing_runs
  id
  run_type
  source
  status
  started_at
  completed_at
  records_processed
  records_failed
  error_message
  metadata_json
```

---

# 14. API response standards

## 14.1 Use consistent response envelopes

Every API response should follow a predictable shape.

Example:

```json
{
  "data": {},
  "meta": {
    "status": "success",
    "last_updated": "2026-05-30T10:00:00Z",
    "source": "internal",
    "is_stale": false,
    "warnings": []
  },
  "errors": []
}
```

## 14.2 Error response

```json
{
  "data": null,
  "meta": {
    "status": "error",
    "last_updated": null,
    "source": "SEC",
    "is_stale": true,
    "warnings": []
  },
  "errors": [
    {
      "code": "SEC_USER_AGENT_MISSING",
      "message": "SEC ingestion requires a valid SEC User-Agent."
    }
  ]
}
```

## 14.3 Why this matters

The frontend can only show honest states if the backend returns:

- Source
- Last updated
- Status
- Warnings
- Errors
- Confidence
- Staleness

---

# 15. API endpoint checklist

## 15.1 Dashboard

```http
GET /api/dashboard/brief
GET /api/dashboard/freshness
```

## 15.2 Portfolio

```http
GET /api/portfolio
POST /api/portfolio/holdings
PUT /api/portfolio/holdings/{holding_id}
DELETE /api/portfolio/holdings/{holding_id}
GET /api/portfolio/exposures
GET /api/portfolio/risk
GET /api/portfolio/narrative-exposure
```

## 15.3 Companies

```http
GET /api/companies/search?q=
GET /api/companies/{ticker}
GET /api/companies/{ticker}/summary
GET /api/companies/{ticker}/metrics
GET /api/companies/{ticker}/filings
GET /api/companies/{ticker}/news
GET /api/companies/{ticker}/narratives
GET /api/companies/{ticker}/sentiment
GET /api/companies/{ticker}/risks
GET /api/companies/{ticker}/peers
GET /api/companies/{ticker}/valuation
```

## 15.4 SEC

```http
GET /api/sec/company/{ticker}/cik
GET /api/sec/company/{ticker}/filings
POST /api/sec/ingest/{ticker}
```

## 15.5 News

```http
GET /api/news
GET /api/news/company/{ticker}
POST /api/news/ingest
```

## 15.6 Narratives

```http
GET /api/narratives
GET /api/narratives/{narrative_id}
GET /api/narratives/{narrative_id}/timeline
GET /api/narratives/{narrative_id}/sources
GET /api/narratives/{narrative_id}/related-companies
GET /api/narratives/{narrative_id}/price-reaction
POST /api/narratives/extract
```

## 15.7 Scores

```http
GET /api/scores/company/{ticker}
GET /api/scores/portfolio
GET /api/scores/narrative/{narrative_id}
```

## 15.8 Research

```http
POST /api/research/sessions
GET /api/research/sessions
GET /api/research/sessions/{session_id}
POST /api/research/sessions/{session_id}/messages
POST /api/research/sessions/{session_id}/sources
POST /api/research/sessions/{session_id}/notes
POST /api/research/sessions/{session_id}/memo
```

## 15.9 Valuation

```http
GET /api/valuation/{ticker}
POST /api/valuation/{ticker}/cases
GET /api/valuation/{ticker}/cases
PUT /api/valuation/cases/{case_id}
DELETE /api/valuation/cases/{case_id}
POST /api/valuation/calculate
```

## 15.10 Ingestion and data health

```http
GET /api/ingestion/status
GET /api/ingestion/runs
GET /api/ingestion/runs/{run_id}
POST /api/ingestion/sec/run
POST /api/ingestion/news/run
POST /api/ingestion/prices/run
POST /api/ingestion/retry/{run_id}
```

---

# 16. Frontend architecture

The frontend should be simplified and organized around product areas.

Recommended structure:

```text
frontend/
  src/
    app/
      dashboard/
      portfolio/
      companies/
        [ticker]/
      narratives/
      research/
      valuation/
      data/
      settings/

    components/
      layout/
      finance/
      intelligence/
      charts/
      data/
      tables/
      forms/
      ui/

    lib/
      api/
      formatting/
      constants/
      scoring/
      validation/

    hooks/
      useCompany.ts
      usePortfolio.ts
      useNarratives.ts
      useIngestionStatus.ts

    types/
      company.ts
      portfolio.ts
      narrative.ts
      score.ts
      filing.ts
      news.ts
      valuation.ts
      api.ts
```

## 16.1 Rules

1. Pages should orchestrate data and layout.
2. Components should render reusable UI.
3. API functions should live under `lib/api`.
4. Types should live under `types`.
5. Formatting helpers should be centralized.
6. Do not scatter fetch logic across components.
7. Do not hardcode backend URLs in components.
8. Do not duplicate table/chart logic.

---

# 17. Backend architecture

Recommended backend organization:

```text
backend/
  app/
    api/
      routes/
        dashboard.py
        portfolio.py
        companies.py
        sec.py
        news.py
        narratives.py
        scores.py
        research.py
        valuation.py
        ingestion.py

    services/
      sec_service.py
      cik_service.py
      news_service.py
      price_service.py
      sentiment_service.py
      narrative_service.py
      scoring_service.py
      research_service.py
      valuation_service.py
      ingestion_service.py

    models/
      company.py
      portfolio.py
      filing.py
      news.py
      narrative.py
      score.py
      research.py
      valuation.py
      processing_run.py

    schemas/
      company.py
      portfolio.py
      filing.py
      news.py
      narrative.py
      score.py
      research.py
      valuation.py
      api_response.py

    db/
      session.py
      migrations/
```

## 17.1 Backend rules

1. Routes should be thin.
2. Business logic should live in services.
3. Database models should not leak directly into frontend responses.
4. Use schemas for clean API responses.
5. Track processing runs for all ingestion.
6. Return data freshness metadata.
7. Return clear error codes.
8. Do not silently fail ingestion jobs.
9. Do not pretend missing data exists.
10. Keep scoring explainable.

---

# 18. Security and safety requirements

## 18.1 Environment variables

Sensitive values should stay in `.env` and should never be committed.

Examples:

```text
DATABASE_URL=
SEC_USER_AGENT=
NEWS_API_KEY=
OPENAI_API_KEY=
GEMINI_API_KEY=
ALPHA_VANTAGE_API_KEY=
```

## 18.2 Frontend security

Do not expose backend secrets in frontend code.

Frontend may use:

```text
NEXT_PUBLIC_API_BASE_URL=
```

Frontend must not contain:

```text
SEC_USER_AGENT=
DATABASE_URL=
OPENAI_API_KEY=
```

## 18.3 Backend security

Backend should:

- Validate inputs
- Sanitize ticker inputs
- Rate limit ingestion endpoints where practical
- Avoid logging secrets
- Use environment variables
- Avoid exposing stack traces in production
- Use CORS carefully
- Validate URL ingestion sources if any
- Store API keys only server-side

## 18.4 AI safety within app

AI-generated market interpretation must not be presented as investment advice.

Use language like:

```text
This is a research signal, not a buy/sell recommendation.
```

The product can analyze. It should not claim certainty.

---

# 19. SEC ingestion requirements

## 19.1 SEC User-Agent

SEC requires respectful access. The backend should use a clear User-Agent string.

Example format:

```text
MarketIntelligenceApp/0.1 contact: your-email@example.com
```

This should be stored as:

```text
SEC_USER_AGENT=
```

## 19.2 CIK lookup

The backend should support ticker-to-CIK lookup.

Frontend needs:

```http
GET /api/sec/company/{ticker}/cik
```

The UI should display:

- Ticker
- CIK
- Company name
- Lookup status
- Last updated

## 19.3 Filing ingestion

Filing ingestion should support:

- 10-K
- 10-Q
- 8-K

The UI should show if no filings have been ingested yet.

## 19.4 Processing run tracking

Every ingestion job should create a processing run.

Track:

- Run type
- Source
- Status
- Started at
- Completed at
- Records processed
- Records failed
- Error message

---

# 20. Known technical issues to address

The existing docs should retain and update the known issues.

## 20.1 Alembic migration issue

Known error:

```text
Can't locate revision identified by 'a2afaa43a162'
```

Docs should explain:

- What caused it
- Whether the migration chain is broken
- How to inspect migration history
- Whether to stamp head, recreate migrations, or restore missing revision
- Which option is safest for local dev

Do not tell the user to run destructive migration commands without explanation.

## 20.2 Docker socket permission issue

Known error:

```text
permission denied while trying to connect to the docker API at unix:///var/run/docker.sock
```

Docs should explain:

- Docker Desktop must be running
- User may need Docker permissions
- On macOS, restarting Docker Desktop often helps
- Do not use random `sudo chmod 666 /var/run/docker.sock` as a default fix

## 20.3 Frontend cannot reach backend

Docs should include a checklist:

- Is backend running?
- Is frontend running?
- Is backend port correct?
- Is CORS configured?
- Is `NEXT_PUBLIC_API_BASE_URL` set?
- Is Docker exposing backend port?
- Is API path correct?
- Are containers on the same Docker network?

## 20.4 Missing SEC configuration

Docs should state:

- SEC ingestion will not work until `SEC_USER_AGENT` is configured
- This is not an API key
- It is an identifying string
- It should include app name and contact email

---

# 21. Documentation amendment instructions

The existing docs should be amended based on this document.

## 21.1 Amend `product-brief.md`

Add:

- Revised product north star
- Core workflows
- Target user
- What the app is not
- Source-backed AI principle
- Intelligence hierarchy
- Initial MVP scope

## 21.2 Amend `architecture.md`

Add:

- Revised frontend architecture
- Revised backend architecture
- API response envelope
- Service layer expectations
- Data freshness strategy
- Processing run strategy
- Scoring architecture
- Narrative tracking architecture

## 21.3 Amend `database-schema.md`

Add or update tables for:

- companies
- portfolio_holdings
- price_snapshots
- sec_filings
- news_articles
- narratives
- narrative_sources
- narrative_company_links
- scores
- research_sessions
- research_messages
- valuation_cases
- alerts
- processing_runs

## 21.4 Amend `data-sources.md`

Add:

- SEC source requirements
- SEC User-Agent explanation
- CIK lookup
- News source strategy
- Price data source strategy
- Social/forum source strategy
- Data freshness definitions
- Stale data rules
- Mock vs real data labeling

## 21.5 Amend `scoring-framework.md`

Add:

- Fundamental score
- Valuation score
- Narrative score
- Sentiment score
- Risk score
- Momentum score
- Confidence score
- Overall signal
- Score explainability requirement
- Score input and weighting transparency

## 21.6 Amend `implementation-checklist.md`

Add phases:

1. Stabilize local dev
2. Fix migrations
3. Confirm backend health
4. Add API response envelope
5. Add processing runs
6. Add SEC User-Agent and CIK lookup
7. Build company master data
8. Build portfolio endpoints
9. Build frontend shell
10. Build dashboard
11. Build portfolio page
12. Build company intelligence page
13. Build filings view
14. Build narrative tracking
15. Build scoring breakdown
16. Build valuation tool
17. Build data health page
18. Add error, empty, stale, and loading states
19. Add security checks
20. Add final documentation

## 21.7 Amend `known-issues.md`

Add or update:

- Alembic missing revision
- Docker socket permission
- Frontend/backend connectivity
- SEC not configured
- Mock data risk
- API error handling gaps
- Missing stale data state
- Missing score explainability
- Missing source evidence trails

## 21.8 Amend `local-development-plan.md`

Add:

- Required environment variables
- How to run backend
- How to run frontend
- How to run Docker
- How to run migrations
- How to verify API health
- How to verify frontend/backend connection
- How to seed sample data
- How to test SEC ingestion
- How to inspect logs

## 21.9 Amend `beginner-glossary.md`

Add beginner explanations for:

- Frontend
- Backend
- API
- Endpoint
- Database
- Migration
- Alembic
- Docker
- Docker Compose
- Container
- Environment variable
- CORS
- SEC User-Agent
- CIK
- Ingestion
- Processing run
- Mock data
- Stale data
- Source-backed AI
- Scoring model
- Narrative tracking
- DCF
- Sensitivity table

## 21.10 Amend `execution-runbook.md`

Add:

- Safe order of implementation
- Checkpoint commands
- Git commit points
- How to avoid giant unsafe diffs
- How to validate each phase
- Rollback instructions
- Testing checklist

## 21.11 Amend `current-state.md`

Add:

- What currently works
- What is mocked
- What is missing
- Which backend endpoints exist
- Which frontend pages exist
- Which data pipelines exist
- Which docs are outdated
- Which issues block progress

---

# 22. Implementation phases

## Phase 0: Audit only

Do not modify files yet.

Antigravity should inspect:

- Frontend file structure
- Backend file structure
- Existing docs
- Existing API routes
- Existing database models
- Existing migrations
- Existing Docker setup
- Existing environment variables
- Existing mock data
- Existing known issues

Output:

- Current-state assessment
- Gap list
- Safe implementation plan
- Files likely to change

## Phase 1: Stabilize local development

Fix:

- Docker startup
- Backend health
- Frontend/backend connection
- Environment variables
- Alembic migration chain
- Basic API health endpoint

Add:

```http
GET /api/health
```

Expected response:

```json
{
  "status": "ok",
  "timestamp": "2026-05-30T10:00:00Z"
}
```

## Phase 2: API response envelope and data states

Add standard response envelope.

Frontend should start using:

- Loading states
- Empty states
- Error states
- Stale states
- Not configured states

## Phase 3: Processing runs and ingestion status

Add backend support for:

- processing_runs table
- ingestion status endpoint
- SEC status
- News status
- Price status

Build Data page frontend.

## Phase 4: SEC User-Agent and CIK lookup

Add:

- SEC_USER_AGENT env variable
- CIK lookup service
- Company SEC metadata
- Filing list endpoint
- Filing ingestion status UI

## Phase 5: Frontend app shell

Build:

- Sidebar
- Top bar
- Global search shell
- Page header
- Shared layout
- Data freshness indicator
- Basic routing

Do not redesign every page at once.

## Phase 6: Portfolio page

Build portfolio UI and backend support.

Include:

- Holdings table
- Exposure charts
- Risk summary
- Empty state
- Add holding flow

## Phase 7: Company intelligence page

Build company page.

Include:

- Ticker header
- Summary
- Metrics
- Filings
- News
- Narratives
- Scores
- Risks
- Sources

## Phase 8: Narrative page

Build narrative tracking.

Include:

- Narrative list
- Narrative detail
- Timeline
- Related companies
- Evidence
- Confidence

## Phase 9: Scoring framework

Add score endpoints and score breakdown UI.

Do not hide the formula.

Expose inputs and confidence.

## Phase 10: Valuation tool

Build DCF UI.

Include:

- Assumptions
- Scenarios
- Sensitivity
- Saved cases
- Explanation

## Phase 11: Research workspace

Build research sessions and source-backed AI answers.

## Phase 12: Polish, security, and docs

Finalize:

- Accessibility
- Responsive behavior
- API errors
- Security checks
- Documentation updates
- Known issue cleanup

---

# 23. Antigravity instruction block

Use this instruction block with Antigravity.

```text
You are working on the Market Intelligence App.

Read this Markdown file fully before making changes.

Your job is to amend the existing app and documentation based on this design and backend alignment brief.

Do not blindly rewrite the project.

First perform an audit:
1. Inspect the frontend structure.
2. Inspect the backend structure.
3. Inspect existing docs.
4. Identify what already exists.
5. Identify what is missing.
6. Identify what is mocked.
7. Identify what is broken.
8. Identify what docs need amendment.

Then produce a plan.

After the plan, amend the existing docs first:
- product-brief.md
- architecture.md
- database-schema.md
- data-sources.md
- scoring-framework.md
- implementation-checklist.md
- known-issues.md
- local-development-plan.md
- beginner-glossary.md
- execution-runbook.md
- current-state.md

When amending docs:
- Preserve useful existing material.
- Remove outdated contradictions.
- Mark uncertain items as uncertain.
- Clearly separate real functionality from planned functionality.
- Add implementation checkboxes.
- Add beginner explanations where needed.
- Do not pretend missing features exist.

After docs are amended, implement in small phases:
1. Stabilize local dev.
2. Fix or explain migration issues.
3. Add standard API response envelope.
4. Add processing runs and ingestion status.
5. Add SEC User-Agent and CIK lookup.
6. Build frontend app shell.
7. Build dashboard.
8. Build portfolio page.
9. Build company intelligence page.
10. Build narrative page.
11. Build scoring breakdown.
12. Build valuation tool.
13. Build research workspace.
14. Finalize docs and security checks.

Rules:
- Do not change database schema without migration.
- Do not break working backend routes.
- Do not expose secrets in frontend code.
- Do not present mock data as real.
- Do not create fake intelligence.
- Do not use large decorative redesigns.
- Do not add visual complexity unless it improves decision clarity.
- Keep changes incremental and explain files touched after each phase.
```

---

# 24. Prompt to give Antigravity now

Use this prompt:

```text
Read the file `market-intelligence-frontend-backend-design-brief.md`.

First, do not code.

Audit the existing project against the brief.

Return:
1. What already matches the brief.
2. What conflicts with the brief.
3. What is missing.
4. Which docs need amendment.
5. Which backend changes are required.
6. Which frontend changes are required.
7. Which changes should happen first.
8. Any risks, especially migrations, Docker, frontend/backend connection, mock data, and secrets.

After that, amend the existing docs based on the brief. Preserve useful material, remove contradictions, and clearly distinguish current functionality from planned functionality.
```

---

# 25. Non-negotiables

These are the most important rules.

1. The UI must improve decision clarity, not just aesthetics.
2. AI claims must be source-backed.
3. Scores must be explainable.
4. Missing or stale data must be visible.
5. Mock data must be labeled.
6. Backend APIs must support frontend claims.
7. Ingestion status must be visible.
8. SEC setup must be documented.
9. The app must be implemented incrementally.
10. Existing docs must be amended before major implementation.
11. The app should feel like a serious financial intelligence cockpit.
12. Do not hide uncertainty.
13. Do not invent backend functionality from the frontend.
14. Do not expose secrets.
15. Do not create giant unreviewable diffs.

---

# 26. Final product direction

The app should become a financial intelligence system with the following pillars:

1. Portfolio cockpit
2. Company intelligence
3. Narrative tracking
4. Source-backed AI research
5. SEC filing intelligence
6. Explainable scoring
7. Valuation and DCF tooling
8. Data health transparency

The best version of this app is not the one with the most charts.

The best version is the one where a user can quickly understand:

- What changed
- Why it matters
- What evidence exists
- What is uncertain
- What to investigate next

That is the standard every frontend and backend decision should follow.
