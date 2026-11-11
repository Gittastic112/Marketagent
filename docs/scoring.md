# Scoring Framework

## Purpose
The scoring framework ranks information by usefulness. It prevents the system from becoming a noise generator.
The core philosophy is: **Scoring should be explainable. The score is not useful unless users can inspect why it exists.**

## 1. Current Scoring Implementation (Event Level)
The current MVP has deterministic, rule-based scoring focused on individual **events** (like a filing or news article).

### 1.1 Credibility score
Uses the source's recorded reliability score as a credibility heuristic. It does
not independently verify a claim or turn source reputation into a probability.

### 1.2 Novelty score
Checks existing event counts for the same document, company and event type.
It is not a semantic recycled-language detector.

### 1.3 Impact score
Measures potential thesis-changing impact based on active thesis notes or high-importance event types.

### 1.4 Priority score
A bounded, rounded combination of credibility, novelty, impact and information
speed. Defaults in [scoring.py](../backend/app/services/scoring.py) are
0.35 × credibility + 0.25 × novelty + 0.35 × impact + 0.05 × speed bonus.
Speed bonuses are slow=60, medium=75 and fast=80. The first stored ScoringConfig
row by ID overrides these weights. These are deterministic heuristics, not
calibrated probabilities or proof that a claim is true.

---

## 2. Planned Score Expansion (Entity Level)

Private inbox AI high/medium/low importance is a separate model judgment, not this
deterministic event score or the planned entity-level scoring system below.

To support the dashboard and company intelligence pages, the scoring framework will expand from just scoring *events* to scoring *companies* and *narratives* across multiple dimensions.

### 2.1 The Explainability Requirement
All new score API endpoints must return the formula's inputs, weightings, direction, and a text explanation. **Do not hide the formula.**

```json
{
  "name": "fundamental",
  "value": 72,
  "label": "strong",
  "direction": "improving",
  "weight": 0.25,
  "inputs": ["revenue_growth", "margin_trend", "cash_flow"],
  "explanation": "Improving fundamentals due to recent 10-Q margin trend."
}
```

### 2.2 New Score Categories

| Score | Meaning |
|---|---|
| **Fundamental score** | Business and financial trend strength (derived from SEC filings and financials). |
| **Valuation score** | Relative or intrinsic attractiveness (derived from DCF and price data). |
| **Narrative score** | Strength and direction of the market story. |
| **Sentiment score** | Tone and direction of news/social discussion. |
| **Risk score** | Business, market, filing, and data risks. |
| **Momentum score** | Price and information-flow momentum. |
| **Confidence score** | Reliability of available data and model view (High/Medium/Low). |
| **Overall signal** | Combined view across all scores (Not a buy/sell recommendation). |

---

## 3. Future Portfolio-Aware Alert Priority
The formula below is an unimplemented proposal, not the existing portfolio
impact/exposure calculation. Holdings and manual prices already exist. Any new
ranking layer must preserve the event score and disclose its own inputs.

**Suggested Portfolio Priority Formula:**
```text
portfolio_priority_score =
    event_priority_score * 0.50
  + ownership_weight_score * 0.25
  + thesis_relevance_score * 0.15
  + valuation_gap_score * 0.05
  + narrative_velocity_score * 0.05
```

**Ownership Weight Rules:**
- not owned: 0
- watchlist: 25
- owned, < 2% portfolio: 50
- owned, 2% to 10% portfolio: 75
- owned, > 10% portfolio: 100

---

## 4. Human Feedback Loop
Each alert and score should allow the user to flag it as:
- useful
- not useful
- false positive
- needs follow-up
- (Allows adding notes)

This feedback loop is the primary mechanism for improving the deterministic rules over time.
