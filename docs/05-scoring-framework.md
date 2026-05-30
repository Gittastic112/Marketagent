# Scoring Framework

## Purpose
The scoring framework ranks information by usefulness. It prevents the system from becoming a noise generator.
The core philosophy is: **Scoring should be explainable. The score is not useful unless users can inspect why it exists.**

## 1. Current Scoring Implementation (Event Level)
The current MVP has deterministic, rule-based scoring focused on individual **events** (like a filing or news article).

### 1.1 Credibility score
Measures whether the claim is reliable based on the source (e.g., SEC vs unknown blog).

### 1.2 Novelty score
Checks for duplicate documents, recycled language, or first-seen events.

### 1.3 Impact score
Measures potential thesis-changing impact based on active thesis notes or high-importance event types.

### 1.4 Priority score
A weighted combination of the above, used to decide if an alert should be generated.

---

## 2. Planned Score Expansion (Entity Level)

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
After portfolio holdings and manual prices exist, add a second ranking layer without changing the existing objective event score.

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
