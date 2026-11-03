Historical snapshot, not current instructions. Original relative links are preserved.

# Backend Operating Manual

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

## 13.1 The robust DCF pipeline is active

We have already built a rigorous, multi-stage Damodaran-style valuation pipeline. Do not revert to simple math:

```text
Current FCF × growth rate → discounted value
```

Maintain and use the established architecture which properly connects:

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
- portfolio marginal
