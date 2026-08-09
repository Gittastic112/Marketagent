# World-Class Market Intelligence App Expansion Supplement

**Purpose:** This document supplements the existing expansion plan. It consolidates the UI critique, DCF redesign, market regime scoring concept, investment decision features, cybersecurity constraints, API/provider needs, and a phased implementation roadmap.

**Product direction:** Build a serious local-first investment intelligence cockpit. The goal is not to create a prettier dashboard. The goal is to help a user make better research and timing decisions by showing evidence, uncertainty, valuation logic, market regime, portfolio exposure, and what to investigate next.

**Core rule:** The app can help answer whether conditions are attractive, risky, crowded, stale, or uncertain. It should not present itself as a guaranteed buy/sell machine.

---

# 1. Executive Summary

## 1.1 What should happen next

The next step is:

```text
stabilize app
→ audit reality vs docs
→ standardize API responses and data states
→ improve dashboard UI foundations
→ rebuild DCF as a serious valuation engine
→ add market regime scoring
→ connect regime, valuation, thesis, and portfolio exposure into decision readiness
```

Do not jump straight into advanced features before the foundation is trustworthy.

## 1.2 The app should become

A **source-backed investment cockpit** with these pillars:

1. **Portfolio intelligence**
   - What do I own?
   - Where am I concentrated?
   - Which holdings are affected by new information?
   - What is my marginal risk if I buy more?

2. **Company intelligence**
   - What changed recently?
   - What does the latest filing say?
   - What narratives are forming?
   - What risks are rising?

3. **Valuation intelligence**
   - What is the company worth under my assumptions?
   - What assumptions does the market price imply?
   - Is my story internally consistent?

4. **Market regime intelligence**
   - Is the broader market supportive or hostile?
   - Are institutions buying or selling?
   - Are options dealers stabilizing or amplifying volatility?
   - Is the rally broad or narrow?
   - Are credit and volatility markets confirming or warning?

5. **Decision readiness**
   - Is this a good research setup?
   - Is this a good entry setup?
   - Is the thesis supported, contradicted, or still uncertain?
   - What would falsify the decision?

## 1.3 The app should not become

Do not let it become:

- a generic AI chatbot with charts
- a pretty frontend full of mock data
- a fake Bloomberg clone
- a trading signal toy
- a DCF calculator that gives precise outputs from lazy assumptions
- a dashboard that hides stale, missing, or unreliable data
- a system that says “buy” without explaining evidence, uncertainty, and risk

## 1.4 The core product promise

Every important screen should answer:

```text
What changed?
Why does it matter?
What evidence supports it?
How reliable is it?
How exposed am I?
What should I investigate next?
```

---

# 2. Immediate Next Steps

## 2.1 Step 1: Stabilize local environment

Before feature work:

- confirm Docker Desktop is running
- confirm backend is reachable
- fix Alembic migration chain
- confirm frontend can reach backend
- run database migrations
- verify health endpoint
- run a basic browser workflow

Commands to run from the project root:

```bash
docker compose ps
docker compose logs backend --tail=100
docker compose logs frontend --tail=100
curl http://localhost:8000/api/health
```

If backend is down, fix backend before frontend. The frontend cannot be judged while the backend is failing.

## 2.2 Step 2: Reality audit

The docs have shifted several times. Some documents may claim features are complete while others say they are missing. Codex should inspect actual code, not rely on optimistic docs.

Codex prompt:

```text
Read the current docs and inspect the actual codebase.

Do not build anything yet.

Audit:
1. Which backend models exist.
2. Which Alembic migrations exist.
3. Which routes exist.
4. Which frontend pages exist.
5. Which pages use real backend data.
6. Which pages use mock or hardcoded data.
7. Which docs contradict actual code.
8. Which tests exist and pass.
9. Which features are broken because of migration or API issues.
10. Which feature should be built next.

Return a table:
- feature
- claimed status in docs
- actual status in code
- risk
- next action
```

## 2.3 Step 3: Standard API response envelope

This should happen before more frontend complexity.

Every API response should follow:

```json
{
  "data": {},
  "meta": {
    "status": "success",
    "last_updated": "2026-05-30T10:00:00Z",
    "source": "internal",
    "is_stale": false,
    "warnings": [],
    "confidence": "medium"
  },
  "errors": []
}
```

Why this matters:

- frontend can show stale data
- frontend can show partial data
- frontend can distinguish mock from real
- frontend can avoid white screens
- user can know when not to trust data

## 2.4 Step 4: Data state components

Add global UI states:

- Loading
- Empty
- Error
- Stale
- Partial
- Not Configured
- Mock Data
- Permission/API issue
- Success

Every data panel needs one of these states.

## 2.5 Step 5: Rebuild valuation properly

The current DCF is useful as a prototype, but not sufficient. It must become a Damodaran-style valuation engine.

Minimum rebuild:

- story-first valuation
- revenue-driven forecast
- operating margin path
- tax rate
- reinvestment
- sales-to-capital ratio
- ROIC
- WACC builder
- terminal value guardrails
- EV to equity bridge
- sensitivity tables
- reverse DCF
- scenario comparison
- assumption quality score

## 2.6 Step 6: Add Market Regime Dashboard

This becomes a subtab under Portfolio or Dashboard:

```text
Portfolio → Market Regime
```

Purpose:

```text
Is the current market structure supportive for adding risk?
```

It should not say “buy now” blindly. It should show an **Entry Timing Readiness Score** and explain the drivers.

---

# 3. UI Improvement Plan

## 3.1 Current UI problem

The UI has a clean foundation, but it can feel like a ghost town when:

- data is empty
- cards show zeros
- there are no clear actions
- low-contrast text makes the interface feel unfinished
- the active sidebar state is weak
- the app looks polished but not decisive
- too much whitespace pushes important content down
- empty panels say nothing useful

## 3.2 Internal workflow principle

Because this is currently an internal tool, the priorities are:

1. speed
2. density
3. clarity
4. shortcuts
5. immediate next actions
6. no marketing fluff

This is not a consumer SaaS homepage. It is a research cockpit.

## 3.3 Dashboard UI improvements

### Sidebar

Current issue:
- inactive sidebar text is too muted
- active page is not visually anchored enough

Fix:
- give active page a strong background pill or left accent bar
- increase text contrast
- group navigation by workflow

Recommended sidebar:

```text
Dashboard
Portfolio
  Holdings
  Exposure
  Market Regime
Companies
Narratives
Research
Valuation
Alerts
Events
Data / Ingestion
Data Health
Settings
```

### Top bar

Current issue:
- search placeholder can truncate
- data status is isolated
- top bar does not feel like a command center

Fix:
- search placeholder should be short: `Search... (/)` or `Search... (⌘K)`
- make shortcut actually focus search
- show data status with click-through to Data Health
- add `Sync Now` only if backend supports it
- date can sit under page title or in top bar, but avoid floating labels

### KPI cards

Current issue:
- zeros and dashes feel dead
- cards do not tell user what to do

Fix:
- replace passive empty states with action states

Examples:

```text
Portfolio Value
No portfolio yet
[Add Holding] [Import CSV]
```

```text
Tracked Companies
0
[Add Company] [Import Watchlist]
```

```text
Active Alerts
No active alerts
[Configure Sources] [Run Ingestion]
```

### Daily Intelligence Brief

Current issue:
- suggested questions look like plain text
- not actionable enough

Fix:
- turn suggested questions into clickable prompt chips

Examples:

```text
[Is this new information or repeated noise?]
[Which holdings have new risks?]
[What changed in filings?]
[Which narrative is accelerating?]
```

Clicking should:
- open Research Workspace
- prefill the question
- attach relevant sources
- show evidence-backed answer

## 3.4 Valuation UI improvements

The current valuation page feels too much like a simple calculator. It should feel like a structured valuation workstation.

Recommended tabs inside valuation:

```text
Story | Assumptions | Forecast | Valuation | Sensitivity | Reverse DCF | Notes
```

### Story tab

Purpose:
- connect narrative to numbers

Fields:
- company story
- growth story
- margin story
- reinvestment story
- risk story
- terminal story
- thesis link
- what would falsify this valuation?

### Assumptions tab

Sections:
- revenue
- margins
- taxes
- reinvestment
- cost of capital
- terminal value
- equity bridge

Each assumption should show:
- label
- explanation
- current value
- normal range
- source or user-entered tag
- warning if abnormal

### Forecast tab

Show yearly operating model:

| Year | Revenue | Growth | EBIT Margin | EBIT | Tax | NOPAT | Reinvestment | FCFF | ROIC |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|

### Valuation tab

Show:
- intrinsic value per share
- current market price
- upside/downside
- enterprise value
- equity value
- PV of explicit FCFF
- PV of terminal value
- terminal value as % of EV
- implied exit multiple
- margin of safety
- model quality score

### Sensitivity tab

Show:
- WACC vs terminal growth
- revenue growth vs margin
- sales-to-capital vs WACC
- terminal ROIC vs terminal growth

### Reverse DCF tab

Show:
- what growth is implied by current price
- what margin is implied by current price
- what terminal assumptions are implied
- whether implied assumptions are realistic
- what execution level the market is pricing in

## 3.5 General visual design rules

Use:

- dark-first dashboard
- muted surfaces
- strong borders
- high-contrast text
- tabular numerals
- compact spacing
- clear badges
- consistent chart wrappers
- consistent cards

Avoid:

- decorative gradients
- fake neon finance terminal styling
- too many colors
- huge empty cards
- unlabelled charts
- mock intelligence shown as real
- charts without source/timestamp

---

# 4. DCF Maker: Damodaran-Style Redesign

## 4.1 Core problem with current DCF

Current DCF asks for:

- current FCF
- FCF growth
- WACC
- terminal growth
- shares
- net debt

This is acceptable for a quick calculator, but it is too shallow for investment work.

A serious DCF should not just grow FCF mechanically. It should answer:

```text
What is the business story?
What growth is possible?
What reinvestment is needed?
Does growth create value?
What risk does the discount rate imply?
What terminal assumptions are economically plausible?
What does the market price already assume?
```

## 4.2 Core DCF formula

```text
Firm Value = Sum of discounted FCFF during explicit forecast period
           + Present value of terminal value
```

Where:

```text
FCFF = NOPAT - Reinvestment
NOPAT = EBIT × (1 - Tax Rate)
Reinvestment = Change in Revenue / Sales-to-Capital Ratio
ROIC = NOPAT / Invested Capital
```

## 4.3 Required assumptions

### Operating assumptions

| Input | Description |
|---|---|
| Starting revenue | Base year revenue |
| Revenue growth path | Year-by-year or staged growth |
| Current EBIT margin | Current operating profitability |
| Target EBIT margin | Mature-state margin |
| Margin fade period | Years to reach target margin |
| Tax rate | Effective or marginal tax rate |
| Sales-to-capital ratio | How much revenue is generated per dollar of capital |
| Current invested capital | Needed for ROIC |
| Reinvestment lag | Optional advanced feature |

### Risk assumptions

| Input | Description |
|---|---|
| Risk-free rate | Base rate |
| Equity risk premium | Market risk premium |
| Beta | Equity risk |
| Cost of equity | Calculated |
| Pre-tax cost of debt | Debt cost |
| Tax rate | For after-tax debt cost |
| Debt weight | Capital structure |
| Equity weight | Capital structure |
| WACC | Calculated or manual override |
| WACC fade | Optional path from current WACC to mature WACC |

### Terminal assumptions

| Input | Description |
|---|---|
| Terminal growth | Long-term perpetual growth |
| Terminal WACC | Mature discount rate |
| Terminal ROIC | Mature return on invested capital |
| Terminal reinvestment rate | Terminal growth / terminal ROIC |
| Terminal value method | Perpetuity or exit multiple |
| Exit multiple | Optional cross-check |

### Equity bridge

| Item | Description |
|---|---|
| Enterprise value | Value of operating assets |
| Cash | Add |
| Marketable securities | Add |
| Non-operating assets | Add |
| Debt | Subtract |
| Minority interests | Subtract |
| Preferred stock | Subtract |
| Pension deficit | Subtract |
| Employee options | Subtract or adjust |
| Diluted shares outstanding | Divide equity value |

## 4.4 Story to numbers mapping

A Damodaran-style valuation should force the user to connect story and assumptions.

Example mapping:

| Story claim | Required assumption |
|---|---|
| Company has high growth runway | Revenue growth above industry median |
| Margins should expand | EBIT margin path increases |
| Growth needs heavy capital | Lower sales-to-capital ratio |
| Company is maturing | WACC declines or stabilizes |
| Company has strong moat | ROIC stays above WACC |
| Market is overpricing growth | Reverse DCF implied growth exceeds plausible range |

## 4.5 Required guardrails

The app should flag bad assumptions.

### Terminal growth guardrails

Flag if:

- terminal growth > risk-free rate
- terminal growth > long-term nominal GDP estimate
- terminal growth is too high for mature company
- terminal growth is positive but terminal reinvestment is zero

Warning example:

```text
Terminal growth exceeds the risk-free rate. This may overstate terminal value.
```

### Terminal value concentration

Flag if:

- terminal value > 75% of enterprise value
- terminal value > 85% of enterprise value as high warning

Warning example:

```text
82% of enterprise value comes from terminal value. The valuation is highly dependent on terminal assumptions.
```

### ROIC vs WACC

Flag if:

- ROIC < WACC while growth is high
- high growth destroys value
- terminal ROIC is below WACC but model assumes value creation

Warning example:

```text
Projected ROIC is below WACC. Growth may destroy value under these assumptions.
```

### WACC sanity

Flag if:

- WACC < risk-free rate
- beta is unrealistic
- cost of debt is below risk-free without explanation
- equity risk premium missing
- user entered WACC without support

### Reinvestment sanity

Flag if:

- positive growth with no reinvestment
- negative reinvestment without explanation
- sales-to-capital ratio unrealistic
- reinvestment rate inconsistent with ROIC

### Share count sanity

Flag if:

- shares outstanding missing
- basic shares used instead of diluted shares
- buybacks assumed without cash impact
- options not considered for high-growth companies

## 4.6 DCF outputs

Minimum outputs:

- revenue by year
- EBIT by year
- NOPAT by year
- reinvestment by year
- FCFF by year
- discount factor by year
- PV of FCFF by year
- terminal value
- PV of terminal value
- enterprise value
- equity value
- value per share
- current market price
- upside/downside
- margin of safety
- terminal value % of EV
- implied exit multiple
- model quality score
- assumption warnings

## 4.7 DCF charts

Required charts:

1. Revenue forecast line chart
2. EBIT margin line chart
3. FCFF bar chart
4. ROIC vs WACC line chart
5. PV contribution bar chart
6. Terminal value vs explicit value split
7. Scenario comparison chart
8. Sensitivity heatmap
9. Current price vs intrinsic value chart

## 4.8 Sensitivity tables

### WACC vs terminal growth

| WACC / g | 1.5% | 2.0% | 2.5% | 3.0% | 3.5% |
|---|---:|---:|---:|---:|---:|
| 8.0% | | | | | |
| 9.0% | | | | | |
| 10.0% | | | | | |
| 11.0% | | | | | |
| 12.0% | | | | | |

### Revenue growth vs target margin

| Growth / Margin | 20% | 22% | 24% | 26% | 28% |
|---|---:|---:|---:|---:|---:|
| 2% | | | | | |
| 4% | | | | | |
| 6% | | | | | |
| 8% | | | | | |
| 10% | | | | | |

### Sales-to-capital vs WACC

Useful because reinvestment is often ignored.

| Sales-to-Capital / WACC | 8% | 9% | 10% | 11% | 12% |
|---|---:|---:|---:|---:|---:|
| 1.0x | | | | | |
| 1.5x | | | | | |
| 2.0x | | | | | |
| 2.5x | | | | | |
| 3.0x | | | | | |

## 4.9 Reverse DCF

Reverse DCF answers:

```text
What assumptions are embedded in the current market price?
```

Inputs:
- current market price
- shares outstanding
- net debt
- current revenue
- current EBIT margin
- tax rate
- WACC
- terminal growth
- sales-to-capital ratio

Outputs:
- implied revenue growth
- implied target margin
- implied ROIC
- implied terminal value
- implied reinvestment
- plausibility rating
- market story summary

Example output:

```text
At the current price, the market appears to require 8.5% annual revenue growth for 5 years, EBIT margin expansion from 24% to 30%, and ROIC above WACC throughout the forecast period. This is plausible only if the company sustains pricing power and avoids margin compression.
```

## 4.10 DCF model quality score

The model should have a quality score, not because the valuation is “right”, but because the assumptions may be more or less internally consistent.

Example:

```text
Model Quality: 74/100

Strengths:
- Revenue and margin assumptions are explicit.
- Reinvestment is modeled.
- ROIC exceeds WACC in most years.

Warnings:
- Terminal value is 81% of enterprise value.
- WACC was manually entered without component build-up.
- Terminal growth is close to risk-free rate.
```

Scoring categories:

| Category | Weight |
|---|---:|
| Assumption completeness | 20% |
| Story consistency | 20% |
| Reinvestment logic | 20% |
| Terminal value discipline | 20% |
| Sensitivity coverage | 10% |
| Source support | 10% |

---

# 5. Market Regime Dashboard

## 5.1 Purpose

The Market Regime Dashboard tells the user:

```text
Is the broader market structure supportive for adding risk right now?
```

It should combine options data, institutional flows, volume, market breadth, volatility, credit spreads, and microstructure into a single explainable regime view.

## 5.2 Important wording

Do not label the output as:

```text
Buy / Sell Signal
```

Better labels:

```text
Entry Timing Readiness
Market Structure Score
Risk-On / Risk-Off Regime
Liquidity Regime
Market Support Score
```

The system can say:

```text
Market structure is supportive for cautious buying.
```

It should not say:

```text
You should buy now.
```

## 5.3 Top-level score

### Master Regime Score

Range:

| Score | Label | Meaning |
|---:|---|---|
| 0 to 30 | Structural Bear / Liquidation | Avoid adding broad equity risk unless special setup |
| 31 to 49 | Volatile / Transitioning | Wait, hedge, or use smaller sizing |
| 50 to 69 | Accumulation / Improving | Cautious buying may be reasonable |
| 70 to 100 | Structural Bull / Risk-On | Market structure supportive for adding risk |

## 5.4 Top-level UI

The subtab should show:

```text
Market Regime
Score: 72 / 100
Label: Risk-On, but crowded
Confidence: Medium
Main driver: Positive gamma and improving breadth
Main risk: Credit spreads starting to widen
Last updated: timestamp
```

Components:
- large score gauge
- price chart overlaid with regime score
- sub-score radar chart
- module breakdown cards
- warning panel
- historical regime timeline
- what changed today
- what would improve/worsen the score

## 5.5 Main chart

Dual-axis chart:

- line 1: index or asset price
- line 2: master regime score

Tooltip on hover:

```text
Date: 2026-05-30
Regime Score: 68
Price: 5,240
Options: 74
Flows: 61
Volume: 70
Breadth: 59
Macro/Credit: 52
Interpretation: Improving but not broad enough yet
```

## 5.6 Score modules and weights

Initial module weights:

| Module | Weight |
|---|---:|
| Options and derivatives | 30% |
| Institutional flow and liquidity | 25% |
| Volume and participation | 15% |
| Market breadth and momentum | 15% |
| Macro, credit, and volatility regime | 15% |

Alternative advanced weights:

| Module | Weight |
|---|---:|
| Options and derivatives | 25% |
| Institutional flow | 20% |
| Volume and delivery | 15% |
| Breadth and trend | 15% |
| Volatility and credit | 15% |
| Microstructure | 10% |

Use the first version unless you have reliable microstructure data.

---

# 6. Market Regime Module Details

## 6.1 Module 1: Options and derivatives

Purpose:
- understand options positioning
- detect dealer hedging regime
- identify volatility amplification or suppression
- identify crowding and squeeze risk

Weight: 30%

### Metrics

#### Put-Call Ratio

Formula:

```text
Put-Call Ratio = Total Put Open Interest / Total Call Open Interest
```

Interpretation:

| Condition | Interpretation |
|---|---|
| PCR falling with price rising | Bullish risk appetite |
| PCR rising with price falling | Bearish hedging pressure |
| PCR extremely high | Fear extreme, possible contrarian rebound |
| PCR extremely low | Complacency, possible downside vulnerability |

Score example:

| PCR State | Score |
|---|---:|
| 0.6 to 0.9 and stable | 75 |
| 0.9 to 1.2 | 55 |
| 1.2 to 1.4 and rising | 35 |
| > 1.4 but price stabilizing | 65 contrarian |
| < 0.5 | 40 complacency warning |

#### Gamma Exposure and Gamma Flip

Definitions:

- **Positive gamma:** dealers tend to buy dips and sell rallies, dampening volatility
- **Negative gamma:** dealers may sell into falling markets and buy into rising markets, amplifying moves
- **Gamma flip:** approximate level where dealer gamma changes sign

Interpretation:

| State | Meaning |
|---|---|
| Price above gamma flip | more stable, bullish/neutral |
| Price below gamma flip | volatile, bearish risk |
| approaching gamma flip from above | risk zone |
| reclaiming gamma flip | improving structure |

Score:

| Gamma State | Score |
|---|---:|
| Strong positive gamma | 85 |
| Mild positive gamma | 70 |
| Near flip | 50 |
| Mild negative gamma | 35 |
| Deep negative gamma | 20 |

#### Open Interest Change

Interpretation:

| Price | OI | Meaning |
|---|---|---|
| Up | Up | Long buildup |
| Up | Down | Short covering |
| Down | Up | Short buildup |
| Down | Down | Long unwinding |

Scoring:
- long buildup: bullish
- short covering: bullish but less durable
- short buildup: bearish
- long unwinding: bearish or risk-off

#### Implied Volatility Rank

Interpretation:

| IV Rank | Meaning |
|---|---|
| Low IV, price stable | calm regime |
| Low IV, complacency extreme | hidden risk |
| High IV, price falling | panic |
| High IV, price stabilizing | possible capitulation |

#### Volatility Skew

Track:
- put skew
- call skew
- risk reversal
- OTM put IV vs OTM call IV

Bullish:
- skew flattening
- upside calls bid
- panic puts stop rising

Bearish:
- downside puts bid aggressively
- skew steepening
- IV rising with price falling

## 6.2 Module 2: Institutional flow and liquidity

Purpose:
- identify whether structural capital is entering or leaving

Weight: 25%

### Metrics

#### FII/DII flows

For Indian markets:
- FII net buy/sell
- DII net buy/sell
- 5-day moving average
- 10-day moving average
- cumulative monthly flow

Interpretation:

| Flow Pattern | Signal |
|---|---|
| FII buying + DII buying | strongest bullish |
| FII selling but DII absorbing | neutral to bottoming |
| FII selling + DII weak | bearish |
| FII buying but DII selling | mixed |
| FII selling slows while market stabilizes | improving |

#### Mutual fund and ETF flows

For US or global markets:
- ETF inflows/outflows
- sector ETF flows
- active fund flows
- money market fund balances

#### Liquidity proxy

Examples:
- dollar volume
- bid-ask spreads
- market depth if available
- realized volatility
- turnover

## 6.3 Module 3: Volume and delivery

Purpose:
- verify whether price moves have institutional participation

Weight: 15%

### Metrics

#### Volume multiplier

Formula:

```text
Volume Multiplier = Current Volume / 20-Day Average Volume
```

Interpretation:

| Condition | Signal |
|---|---|
| breakout with >1.5x volume | bullish validation |
| breakout with low volume | fakeout risk |
| breakdown with high volume | bearish validation |
| high volume with flat price | absorption |

#### Delivery percentage

Useful in markets where deliverable volume data exists.

Interpretation:

| Condition | Signal |
|---|---|
| high volume + high delivery + rising price | accumulation |
| high volume + low delivery | trading churn |
| falling price + high delivery | distribution or forced selling |
| flat price + high delivery | possible accumulation or block transfer |

#### Volume at price

Future feature:
- volume profile
- high volume nodes
- support/resistance zones

## 6.4 Module 4: Market breadth and momentum

Purpose:
- test whether the rally is broad or narrow

Weight: 15%

### Metrics

#### Percentage above moving averages

Track:
- % of index above 20-day SMA
- % above 50-day SMA
- % above 100-day SMA
- % above 200-day SMA

Interpretation:

| Breadth State | Signal |
|---|---|
| > 65% above 200-day | broad bullish regime |
| 50% to 65% | neutral/improving |
| < 50% while index rising | hollow rally |
| < 35% | weak regime |
| improving from oversold | early recovery |

#### Advance/decline line

Bullish:
- index rising with A/D line rising

Bearish:
- index rising while A/D line falling

#### New highs vs new lows

Bullish:
- expanding new highs
- shrinking new lows

Bearish:
- new lows expanding under surface

#### Hurst exponent

Purpose:
- measure whether price is trending, random, or mean-reverting

Interpretation:

| Hurst | Meaning |
|---:|---|
| < 0.5 | mean-reverting |
| around 0.5 | random walk |
| > 0.5 | trending/persistent |

Use carefully. It should be a supporting indicator, not a primary signal.

## 6.5 Module 5: Macro, credit, and volatility regime

Purpose:
- identify systemic risk-on or risk-off conditions

Weight: 15%

### Metrics

#### VIX level and trend

Interpretation:

| State | Meaning |
|---|---|
| VIX low and stable | calm risk-on |
| VIX rising sharply | risk-off |
| VIX high but falling | recovery possible |
| VIX low and complacent | hidden downside risk |

#### VIX term structure

Definitions:
- contango: longer-term volatility > short-term volatility, usually normal/risk-on
- backwardation: short-term volatility > longer-term volatility, stress/risk-off

Interpretation:

| State | Signal |
|---|---|
| contango | healthy market |
| steep contango | calm, possibly complacent |
| flat curve | transition |
| backwardation | stress/panic |

#### Credit spreads

Examples:
- high-yield spread
- investment-grade spread
- emerging market spreads
- credit default swap indices if available

Interpretation:

| State | Signal |
|---|---|
| spreads narrowing | risk appetite improving |
| spreads stable | neutral |
| spreads widening | risk-off warning |
| spreads widening while equities rise | bearish divergence |

#### Rates and liquidity

Track:
- 10-year yield
- real yields
- Fed funds
- yield curve
- dollar index
- financial conditions index
- money supply/liquidity proxy

---

# 7. Market Regime Interactive Sandbox

## 7.1 Purpose

The sandbox allows the user to stress-test market conditions.

It answers:

```text
If these inputs change, how does the market regime score change?
```

## 7.2 UI layout

### Left column: controls

Inputs:

- PCR slider: 0.4 to 1.8
- Gamma toggle: Positive / Near Flip / Negative
- Institutional flow slider: heavy selling to heavy buying
- Volume multiplier dropdown: 0.5x, 1.0x, 1.5x, 2.0x+
- Breadth slider: 20% to 90% above 200-day
- VIX slider: 10 to 50
- Credit spread slider: tightening to widening
- Hurst slider: 0.3 to 0.8
- Delivery percentage slider: 20% to 80%
- Risk mode toggle: Conservative / Balanced / Aggressive

### Right column: live outputs

- Live Regime Score
- Regime label
- sub-score radar chart
- dynamic explanation
- top positive drivers
- top negative drivers
- what would change the conclusion
- suggested action style

Suggested action styles:
- Avoid adding risk
- Wait for confirmation
- Small starter position only
- Cautious accumulation
- Market structure supportive
- Strong risk-on, watch crowding

## 7.3 Dynamic explanation logic

Example:

```text
Regime Score: 34 / 100
Label: Bearish Cascade Risk

Why:
- Price is below gamma flip, meaning dealer hedging may amplify downside.
- VIX is elevated and rising.
- Breadth is below 40%, so participation is weak.
- FII flows are negative over the last 5 sessions.

What would improve the setup:
- Reclaim gamma flip level.
- Breadth above 50%.
- FII selling slows or turns positive.
- Credit spreads stop widening.
```

## 7.4 Radar chart dimensions

Use:

- Derivatives
- Institutional Flow
- Volume Confirmation
- Breadth
- Macro/Credit
- Microstructure if available

## 7.5 Score transparency

Clicking the score should show:

```text
Master Regime Score = 
Options Score × 30%
+ Flow Score × 25%
+ Volume Score × 15%
+ Breadth Score × 15%
+ Macro/Credit Score × 15%
```

Each sub-score expands into its inputs.

---

# 8. Entry Timing Readiness Score

## 8.1 Purpose

This is more useful than a generic market regime score because it connects:

- company-specific valuation
- thesis strength
- portfolio exposure
- market regime
- sentiment/narrative
- liquidity
- risk

It answers:

```text
Is this a good setup to initiate or add to a position?
```

Again, this is not a buy/sell recommendation. It is a structured research score.

## 8.2 Suggested formula

```text
Entry Timing Readiness =
    Valuation Attractiveness × 25%
  + Thesis Confidence × 20%
  + Market Regime Support × 20%
  + Technical/Liquidity Confirmation × 15%
  + Narrative/Sentiment Confirmation × 10%
  + Portfolio Fit × 10%
```

## 8.3 Score labels

| Score | Label | Interpretation |
|---:|---|---|
| 0 to 30 | Avoid / high risk | Setup is structurally poor |
| 31 to 49 | Wait | Too much uncertainty or poor regime |
| 50 to 64 | Watchlist / starter only | Some support but not enough |
| 65 to 79 | Accumulate cautiously | Setup is attractive but monitor risks |
| 80 to 100 | Strong setup | Multiple independent factors align |

## 8.4 Required breakdown

The UI must show:

- overall score
- drivers
- blockers
- confidence
- data freshness
- evidence
- assumptions
- what would change the score
- position sizing caution

Example:

```text
Entry Timing Readiness: 68 / 100
Label: Cautious accumulation

Positive:
- Reverse DCF implies reasonable expectations.
- Market regime is supportive.
- Breadth is improving.
- Portfolio weight is below target.

Negative:
- Terminal value sensitivity is high.
- Recent sentiment is mixed.
- FII flows are not yet positive.

What would improve the score:
- FII 5-day average turns positive.
- Price holds above gamma flip.
- Latest 10-Q confirms margin stability.
```

## 8.5 Feature uniqueness

Most apps show:
- price charts
- portfolio holdings
- generic news
- maybe simple valuation

This app can be different by combining:

```text
valuation attractiveness
+ price-implied expectations
+ thesis falsification
+ source-backed new information
+ portfolio exposure
+ market regime
+ data quality
```

That creates a decision support system, not another dashboard.

---

# 9. Investment Decision Features To Add

## 9.1 Thesis Assumption Engine

Instead of a free-form thesis note, break the thesis into assumptions.

Example:

```text
Thesis: Apple can compound earnings through services growth and buybacks.

Assumptions:
1. Services revenue grows faster than hardware.
2. Gross margins remain above 43%.
3. China risk does not materially worsen.
4. Buybacks continue at meaningful scale.
5. AI capex does not destroy free cash flow.
```

Each assumption should have:
- metric or evidence link
- status
- confidence
- last checked
- supporting evidence
- contradicting evidence
- falsification trigger

Statuses:
- supported
- weakening
- contradicted
- unknown
- stale
- needs review

## 9.2 Falsification Trigger System

For every thesis, define what would prove you wrong.

Examples:

```text
If services growth falls below 5% for 2 quarters, flag thesis weakening.
If gross margin falls below 40%, flag margin thesis contradicted.
If debt rises while FCF falls, flag capital allocation risk.
```

This is a high-value feature because most investors do not define exit criteria or falsification criteria clearly.

## 9.3 Evidence Ledger

Every important conclusion should link to evidence.

Structure:

```text
Claim
Evidence supporting
Evidence contradicting
Source type
Date
Confidence
User notes
```

Example:

```text
Claim: Margin pressure is rising.
Supporting evidence:
- 10-Q margin decline
- management commentary on input costs
- 3 news articles on discounting
Contradicting evidence:
- gross margin still above 5-year average
- competitor margins also falling
```

## 9.4 Contradiction Engine

The app should not only summarize. It should look for contradictions.

Examples:

- thesis says margins improving, filings show margin compression
- sentiment bullish, insiders selling
- stock breaking out, breadth weakening
- DCF says undervalued, reverse DCF says market assumptions are already modest
- management says demand strong, inventory days rising

## 9.5 Variant Perception Map

This feature captures the difference between:

```text
What the market believes
What I believe
What the evidence says
What price implies
```

UI:

| Dimension | Market View | My View | Evidence | Price Implied |
|---|---|---|---|---|
| Growth | slowing | stable | mixed | 4% growth |
| Margins | pressured | resilient | weakening | 24% EBIT |
| Risk | high | manageable | moderate | high discount |
| Narrative | negative | overdone | improving | pessimistic |

This is extremely useful for investment decisions because alpha often comes from variant perception.

## 9.6 Price-Implied Expectations

This connects reverse DCF to market narrative.

The app should show:

```text
Current price implies:
- 6.2% revenue growth for 5 years
- 28% target EBIT margin
- 18% ROIC
- 2.5% terminal growth
```

Then compare:

```text
Your model assumes:
- 5.0% revenue growth
- 26% target EBIT margin
- 16% ROIC
- 2.0% terminal growth
```

This tells the user whether they are actually disagreeing with the market.

## 9.7 Decision Journal

Every investment decision should be logged.

Fields:
- date
- ticker
- action considered
- action taken
- price
- position size
- thesis
- valuation
- market regime
- risks
- expected catalyst
- what would prove me wrong
- confidence
- 30/90/180 day review notes

This creates feedback and improves investor behavior.

## 9.8 Pre-Mortem Generator

Before buying, the app should ask:

```text
Imagine this investment loses 30%. Why did that happen?
```

Possible categories:
- valuation multiple compression
- margin decline
- revenue miss
- macro regime shift
- liquidity event
- regulatory risk
- thesis was already priced in
- position size too large
- narrative reversed

The app can generate a pre-mortem checklist based on company risks, filings, and portfolio exposure.

## 9.9 Position Sizing Assistant

Not a recommendation engine. A risk tool.

Inputs:
- current portfolio weight
- target max weight
- volatility
- drawdown tolerance
- conviction
- market regime
- liquidity
- correlation to existing holdings

Outputs:
- current exposure
- proposed exposure
- marginal concentration impact
- sector/theme impact
- worst-case loss contribution
- whether position breaches rules

Example:

```text
Adding $5,000 to AAPL increases portfolio weight from 8.2% to 11.4%.
This breaches your 10% single-name concentration rule.
```

## 9.10 Portfolio Marginal Impact Simulator

Before adding a position, show:

```text
If you buy this:
- sector exposure changes from 22% tech to 29% tech
- AI capex exposure rises from 35% to 42%
- USD exposure rises from 70% to 76%
- top 5 holdings concentration rises from 52% to 58%
- portfolio beta rises from 1.05 to 1.12
```

This is more useful than simply showing a buy score.

## 9.11 Catalyst Calendar

Track upcoming catalysts:
- earnings
- investor day
- product launch
- court/regulatory date
- macro event
- Fed meeting
- CPI
- options expiry
- index rebalance
- lockup expiry
- dividend date

Tie catalysts to:
- holdings
- thesis assumptions
- DCF assumptions
- market regime
- alerts

## 9.12 Data Quality and Confidence Layer

Every score should show confidence.

Confidence depends on:
- data freshness
- source coverage
- number of sources
- source credibility
- contradiction level
- model completeness
- missing assumptions
- API health

A weak data environment should lower confidence even if the signal looks strong.

---

# 10. Market Regime Data Pipeline

## 10.1 Data requirements by module

| Module | Data Needed | Difficulty |
|---|---|---:|
| Options | options chain, OI, IV, strikes, expiries | High |
| Gamma | options chain and assumptions | High |
| Flows | FII/DII, ETF/fund flows | Medium |
| Volume | OHLCV | Low |
| Delivery | exchange-specific delivery data | Medium |
| Breadth | index constituent prices | Medium |
| VIX | volatility index data | Low/Medium |
| Credit | spreads from FRED or similar | Low |
| Microstructure | tick/order book | Very High |

## 10.2 Practical build order

Do not start with gamma and order book if data access is poor.

Build in this order:

### Phase MR-1: Manual regime inputs

Allow user to enter:
- PCR
- FII/DII flow
- volume multiplier
- breadth
- VIX
- credit spread direction
- gamma regime manually

This lets the UI and scoring work before APIs.

### Phase MR-2: Free or easy data

Add:
- OHLCV
- volume multiplier
- VIX
- credit spreads
- moving average breadth if data available
- manual FII/DII import

### Phase MR-3: Options chain

Add:
- PCR
- IV rank
- skew
- OI buildup

### Phase MR-4: Gamma model

Add:
- estimated gamma exposure
- gamma flip
- dealer regime
- caution labels

### Phase MR-5: Microstructure

Only later:
- CVD
- order book imbalance
- tick data
- depth

This may be expensive and unreliable for a personal app.

## 10.3 Provider strategy

Start with provider interfaces, not hardcoded providers.

Example backend structure:

```text
services/
  market_data/
    base.py
    manual_provider.py
    alpha_vantage_provider.py
    fmp_provider.py
    polygon_provider.py
    fred_provider.py
    nse_provider.py
```

Each provider returns normalized internal objects.

## 10.4 Provider health

Track:
- configured or not
- last successful run
- rate limit hit
- error count
- stale status
- coverage gaps

---

# 11. API and Data Source Needs

## 11.1 Required now

| Need | Source |
|---|---|
| SEC filings | SEC EDGAR |
| RSS/news | RSS feeds |
| manual prices | user input |
| portfolio | user input |
| DCF assumptions | user input |

## 11.2 Useful next

| Need | Source Type |
|---|---|
| end-of-day prices | Alpha Vantage, FMP, Polygon, Tiingo, Yahoo-like provider if acceptable |
| fundamentals | SEC Company Facts, FMP, Alpha Vantage, Financial Modeling Prep |
| macro | FRED |
| news | RSS, NewsAPI, GDELT |
| market breadth | calculated from constituent prices |
| options chain | Polygon, Tradier, ORATS, CBOE data, broker APIs |
| Indian flows | NSE/BSE/NSDL style public data or manual import |
| delivery data | exchange data or manual import |
| broker sync | only later through official OAuth/token flows |

## 11.3 Data source rules

- use official APIs where possible
- do not scrape forbidden sites
- store provenance
- store timestamps
- store raw payload or normalized raw text
- store provider and data version
- mark stale data
- mark mocked data
- never put API keys in frontend

---

# 12. Cybersecurity Requirements

## 12.1 Non-negotiable rules

- never commit `.env`
- keep `.env.example` placeholder-only
- never expose API keys in frontend code
- do not store broker passwords
- do not deploy publicly without auth
- do not allow arbitrary backend URL fetching
- treat RSS, CSV, markdown, social posts, AI output as untrusted
- escape CSV exports that begin with `=`, `+`, `-`, `@`
- do not render imported HTML as trusted
- add timeouts for network calls
- log errors without secrets
- track ingestion failures
- use mocked external calls in tests

## 12.2 Security before risky features

Before adding CSV import:
- row validation
- file size limits
- formula injection protection
- error reporting
- no script execution

Before adding broker sync:
- OAuth/token design
- encryption strategy
- token rotation
- permission boundaries
- no password storage

Before adding AI:
- AI output provenance
- prompt versioning
- input hash
- source links
- no autonomous thesis edits
- no buy/sell recommendations

Before public deployment:
- auth
- HTTPS
- CSRF review
- CORS policy
- rate limits
- secrets manager
- audit logging
- backups
- role-based access if multi-user

---

# 13. Backend Architecture Additions

## 13.1 Data models to add or verify

### MarketRegimeSnapshot

```text
id
market
asset_symbol
snapshot_date
master_score
regime_label
confidence
options_score
flow_score
volume_score
breadth_score
macro_credit_score
microstructure_score nullable
inputs_json
warnings_json
created_at
```

### MarketRegimeInput

```text
id
snapshot_id
metric_name
metric_value
metric_unit
metric_score
direction
weight
source
last_updated
is_stale
explanation
created_at
```

### ValuationCase

```text
id
company_id
ticker
case_name
scenario
story_text
created_at
updated_at
```

### DcfAssumptionSet

```text
id
valuation_case_id
starting_revenue
revenue_growth_json
current_ebit_margin
target_ebit_margin
tax_rate
sales_to_capital_ratio
invested_capital
risk_free_rate
equity_risk_premium
beta
pre_tax_cost_of_debt
debt_weight
equity_weight
wacc
terminal_growth
terminal_wacc
terminal_roic
cash
debt
minority_interest
preferred_stock
options_adjustment
diluted_shares
current_market_price
units
created_at
```

### DcfProjectionYear

```text
id
valuation_case_id
year_number
revenue
revenue_growth
ebit_margin
ebit
tax
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

### DcfOutput

```text
id
valuation_case_id
pv_explicit_fcff
terminal_value
pv_terminal_value
enterprise_value
equity_value
value_per_share
upside_downside_percent
terminal_value_percent_ev
implied_exit_multiple
model_quality_score
warnings_json
created_at
```

### DcfSensitivityTable

```text
id
valuation_case_id
table_type
row_variable
column_variable
values_json
created_at
```

### DecisionJournalEntry

```text
id
portfolio_id
company_id
ticker
decision_type
decision_date
price_at_decision
position_size_before
position_size_after
thesis_summary
valuation_summary
market_regime_summary
risks_json
falsification_criteria_json
confidence_label
review_date
review_notes
created_at
updated_at
```

### ThesisAssumption

```text
id
thesis_note_id
company_id
assumption_text
metric_name
target_condition
current_status
confidence_label
supporting_evidence_json
contradicting_evidence_json
falsification_trigger
last_checked_at
created_at
updated_at
```

### EvidenceLedgerItem

```text
id
entity_type
entity_id
claim
evidence_type
source_id
raw_document_id
url
evidence_text
direction
confidence_label
created_at
```

### PortfolioMarginalImpact

```text
id
portfolio_id
company_id
ticker
proposed_trade_json
before_snapshot_json
after_snapshot_json
impact_summary
warnings_json
created_at
```

## 13.2 Service modules

Add or verify:

```text
services/
  valuation_engine.py
  reverse_dcf_engine.py
  dcf_quality_service.py
  market_regime_scoring.py
  market_regime_explanation.py
  thesis_assumption_service.py
  evidence_ledger_service.py
  decision_journal_service.py
  portfolio_impact_service.py
```

## 13.3 API endpoints

### Valuation

```http
GET /api/valuation/{ticker}
POST /api/valuation/{ticker}/cases
GET /api/valuation/{ticker}/cases
GET /api/valuation/cases/{case_id}
PUT /api/valuation/cases/{case_id}
DELETE /api/valuation/cases/{case_id}
POST /api/valuation/calculate
POST /api/valuation/reverse-dcf
GET /api/valuation/cases/{case_id}/sensitivity
```

### Market regime

```http
GET /api/market-regime
POST /api/market-regime/manual-inputs
GET /api/market-regime/history
GET /api/market-regime/breakdown
POST /api/market-regime/sandbox
```

### Decision readiness

```http
GET /api/decision-readiness/{ticker}
POST /api/decision-readiness/calculate
GET /api/decision-readiness/{ticker}/breakdown
```

### Thesis assumptions

```http
POST /api/thesis-notes/{id}/assumptions
GET /api/thesis-notes/{id}/assumptions
PATCH /api/thesis-assumptions/{id}
DELETE /api/thesis-assumptions/{id}
POST /api/thesis-assumptions/{id}/check
```

### Evidence ledger

```http
GET /api/evidence
POST /api/evidence
GET /api/evidence/entity/{entity_type}/{entity_id}
```

### Decision journal

```http
POST /api/decision-journal
GET /api/decision-journal
GET /api/decision-journal/{id}
PATCH /api/decision-journal/{id}
DELETE /api/decision-journal/{id}
```

### Portfolio impact

```http
POST /api/portfolio/{id}/simulate-trade
GET /api/portfolio/{id}/marginal-impact/{ticker}
```

---

# 14. Frontend Architecture Additions

## 14.1 Recommended page structure

```text
app/
  dashboard/
  portfolio/
    page.tsx
    market-regime/
    impact-simulator/
  companies/
    [ticker]/
  narratives/
  research/
  valuation/
    [ticker]/
    [ticker]/cases/[caseId]/
  thesis/
  decision-journal/
  data/
  settings/
```

## 14.2 Required components

### Valuation components

```text
components/valuation/
  ValuationShell
  ValuationStoryPanel
  DcfAssumptionsForm
  RevenueForecastTable
  DcfProjectionTable
  WaccBuilder
  TerminalValueGuardrails
  EquityBridge
  DcfOutputCards
  SensitivityHeatmap
  ReverseDcfPanel
  ScenarioComparisonChart
  ModelQualityPanel
```

### Market regime components

```text
components/market-regime/
  MarketRegimeGauge
  RegimeScoreTimeline
  RegimeBreakdownCards
  RegimeRadarChart
  OptionsRegimePanel
  InstitutionalFlowPanel
  VolumeConfirmationPanel
  BreadthPanel
  MacroCreditPanel
  RegimeSandbox
  RegimeExplanationBox
```

### Decision components

```text
components/decision/
  EntryReadinessScore
  DecisionBreakdown
  ThesisAssumptionChecklist
  FalsificationTriggerPanel
  EvidenceLedger
  VariantPerceptionMap
  DecisionJournalForm
  PremortemPanel
  PortfolioImpactSimulator
```

## 14.3 UI rule for scores

Every score component must show:

- numeric score
- label
- confidence
- last updated
- driver list
- blocker list
- data freshness
- source or calculation basis
- expandable formula

---

# 15. Implementation Roadmap

## Phase 0: Stop and audit

Do:
- inspect code
- inspect docs
- inspect migrations
- inspect real pages
- mark features as real, partial, mocked, missing

Do not:
- add new features

## Phase 1: Stabilize local dev

Do:
- fix Alembic issue
- fix backend health
- fix frontend/backend connection
- validate Docker
- document exact recovery path

Acceptance:
- `curl http://localhost:8000/api/health` works
- frontend loads without backend error
- `alembic upgrade head` works

## Phase 2: API envelope and data states

Do:
- add response envelope
- update frontend fetcher
- add ErrorState, EmptyState, StaleState, MockDataBadge
- add metadata handling

Acceptance:
- frontend no longer white-screens on backend errors
- panels show honest data state

## Phase 3: DCF engine backend

Do:
- add/verify DCF models
- implement valuation engine
- implement WACC builder
- implement reinvestment and ROIC
- implement terminal value
- implement equity bridge
- add tests

Acceptance:
- DCF math tested
- invalid assumptions generate warnings
- output includes full projection schedule

## Phase 4: DCF frontend redesign

Do:
- create valuation tabs
- build assumptions form
- build projection table
- build output cards
- build guardrail warnings
- build sensitivity tables
- build reverse DCF panel

Acceptance:
- user can build bear/base/bull case
- user can see value drivers and warnings
- UI does not feel like a toy calculator

## Phase 5: Manual market regime inputs

Do:
- add market regime snapshot model
- add manual input form
- add scoring service
- add master score
- add breakdown UI

Acceptance:
- user can manually input regime metrics
- app calculates regime score
- score explanation is visible

## Phase 6: Market regime dashboard

Do:
- add timeline chart
- add radar chart
- add module tabs
- add sandbox sliders
- add dynamic explanation

Acceptance:
- user can understand why regime is bullish/bearish
- user can stress-test inputs

## Phase 7: Entry Timing Readiness

Do:
- combine valuation, thesis, market regime, technical/liquidity, sentiment/narrative, portfolio fit
- build breakdown UI
- build confidence and warnings

Acceptance:
- score explains whether setup is attractive, risky, or uncertain
- no buy/sell recommendation language

## Phase 8: Thesis assumptions and falsification

Do:
- convert thesis notes into assumptions
- add falsification triggers
- connect alerts/events to assumptions

Acceptance:
- user can see which assumptions are supported or weakening

## Phase 9: Evidence ledger and contradiction engine

Do:
- add evidence ledger
- add contradiction detection rules
- surface contradictions on company and thesis pages

Acceptance:
- app shows both supporting and opposing evidence

## Phase 10: Decision journal and pre-mortem

Do:
- add journal entries
- add pre-mortem generator
- add decision review dates

Acceptance:
- user can review past decisions and compare thesis vs outcome

## Phase 11: Portfolio marginal impact simulator

Do:
- simulate adding to position
- show concentration changes
- show factor/theme changes
- show risk warnings

Acceptance:
- user knows how a trade changes portfolio risk before acting

## Phase 12: API integrations

Only after manual versions work:
- market prices
- FRED
- options data
- institutional flows
- news APIs
- fundamentals

Acceptance:
- provider health visible
- no secrets leaked
- no unlabeled stale data

---

# 16. Codex Skills Needed

## 16.1 Test-first feature builder

Rules:
- inspect code first
- add failing tests
- implement smallest change
- run tests
- report files changed

## 16.2 Database migration skill

Rules:
- inspect models
- add migration
- check migration chain
- avoid destructive schema changes
- explain local migration steps

## 16.3 API envelope skill

Rules:
- enforce `{data, meta, errors}`
- add tests
- update frontend fetcher
- preserve error details without leaking secrets

## 16.4 Financial math skill

Rules:
- implement DCF formulas
- test WACC, FCFF, terminal value, sensitivity
- avoid hardcoded finance shortcuts
- document formulas

## 16.5 Market regime scoring skill

Rules:
- implement scoring modules
- store input values
- store weights
- return explanations
- distinguish observed data from manual input

## 16.6 Cybersecurity skill

Rules:
- inspect secrets
- prevent frontend key exposure
- validate imports
- protect against SSRF
- avoid unsafe Docker/socket advice
- no broker passwords

## 16.7 UI simplification skill

Rules:
- reduce clutter
- improve active states
- turn empty states into actions
- no mock data as real
- reuse components
- no giant page files

## 16.8 Investment decision workflow skill

Rules:
- build thesis assumptions
- build falsification triggers
- build evidence ledger
- build decision journal
- never produce direct buy/sell advice

---

# 17. Exact Next Codex Prompt

Use this next:

```text
Read:
- docs/00-current-state.md
- docs/08-execution-runbook.md
- docs/10-design-brief.md
- docs/06-security-threat-model.md
- docs/world_class_expansion_supplement_master_plan.md

Do not build new features yet.

First perform a reality audit against the actual codebase:
1. Verify backend health endpoint.
2. Verify Alembic migration chain.
3. List existing backend models.
4. List existing backend routes.
5. List existing frontend pages.
6. Identify pages using mock/hardcoded data.
7. Identify docs that contradict the code.
8. Identify whether API response envelope is implemented.
9. Identify whether DCF is toy-level or full revenue-driven FCFF.
10. Identify whether market regime features exist.

Return:
- current real state
- broken or risky areas
- exact first 5 implementation tasks
- files likely to change
- tests to add
- commands to run

Do not modify files until after this audit.
```

After audit, use:

```text
Implement Phase 2 only: API response envelope and frontend data states.

Constraints:
- Do not add new product features.
- Do not redesign all pages.
- Add tests.
- Preserve existing route behavior where possible.
- Frontend must show ErrorState, EmptyState, StaleState, and MockDataBadge where applicable.
- Return files changed and tests run.
```

---

# 18. What Makes This App Potentially World-Class

The app becomes differentiated if it does the following better than existing tools:

## 18.1 It connects thesis, valuation, and evidence

Most tools show data. Few tools ask:

```text
Does this new evidence support or weaken my actual thesis?
```

## 18.2 It exposes uncertainty

Most dashboards hide missing data. This app should show:

```text
Data stale
Confidence low
Evidence mixed
Assumption unsupported
Source unavailable
```

## 18.3 It makes valuation falsifiable

DCF tools often output a number. This app should show:

```text
Your valuation only works if margins reach 30% and reinvestment stays low.
```

## 18.4 It shows market structure

Buying a good company at the wrong regime can still hurt. The market regime tab adds timing context.

## 18.5 It simulates portfolio impact before action

The app should show:

```text
This trade improves valuation exposure but worsens concentration risk.
```

## 18.6 It builds investor memory

Decision journal, thesis assumptions, and pre-mortems make the app improve the user over time.

## 18.7 It separates signal from noise

The product should constantly distinguish:

- fact
- source summary
- calculation
- user assumption
- AI interpretation
- market narrative
- price-implied belief

That is the core of trust.

---

# 19. Final Build Principle

The best version of this app is not the one with the most features.

The best version is the one where a user can open it and quickly understand:

```text
What changed?
What matters?
What is the evidence?
What is uncertain?
What does the market imply?
What does my thesis require?
How exposed am I?
What should I inspect next?
```

Everything else is secondary.
