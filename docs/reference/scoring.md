# Event scoring

The backend ranks individual events for review. Each scored event stores its four scores, speed classification and explanation. Priority runs from 0 to 100. Its meaning is the order in which to inspect events. The score has no calibrated probability interpretation. [Scoring service](../../backend/app/services/scoring.py) · [Behavior tests](../../backend/tests/test_scoring.py)

| Input | What affects it |
|---|---|
| Credibility | Primary-source classification, recorded source type or reliability, a linked document and URL, and explicit corroboration or contradiction fields when supplied. |
| Novelty | Earlier events sharing the same document, company or event type. Repeated document IDs receive the lowest score. |
| Impact | Company association, an active thesis, material event types, alert-worthy terms, recency and source credibility. |
| Speed | Filing, news and other terms classify information as slow, medium or fast. The numeric bonuses are 60, 75 and 80. |

The default priority is `0.35 × credibility + 0.25 × novelty + 0.35 × impact + 0.05 × speed bonus`, rounded and bounded to 0–100. The first stored scoring configuration by ID overrides the weights. Use the stored explanation when checking an individual event.

Private inbox AI importance has its own model and review process. The earlier proposed company scores, portfolio-weighted formula and feedback workflow are retained in the [planning archive](../archive/plans/entity-and-portfolio-scoring.md).
