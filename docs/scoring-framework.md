# Scoring Framework

## Purpose

The scoring framework ranks information by usefulness.

The system should not alert on everything.

It should prioritize:

- credibility
- novelty
- potential impact
- information speed
- relevance to tracked thesis

---

## Core scores

### 1. Credibility score

Measures whether the claim is reliable.

Scale:

```text
0 = likely unreliable
100 = highly reliable
```

Suggested factors:

| Factor | Weight |
|---|---:|
| Primary source | 30 |
| Reputable source | 20 |
| Cross-source corroboration | 20 |
| Freshness | 10 |
| Historical reliability | 10 |
| Contradiction check | 10 |

Example:

- SEC filing: high credibility
- company press release: high but biased
- reputable news outlet: medium-high
- unsourced social post: low
- anonymous rumor: very low

---

### 2. Novelty score

Measures whether this is new versus repeated.

Scale:

```text
0 = old/recycled
100 = genuinely new
```

Inputs:

- seen before?
- duplicate headline?
- new language in filing?
- new source?
- new causal claim?
- new market reaction?

---

### 3. Impact score

Measures whether this might matter.

Scale:

```text
0 = irrelevant
100 = potentially thesis-changing
```

Factors:

| Factor | Question |
|---|---|
| Company relevance | Does this affect a tracked company? |
| Thesis relevance | Does this change an assumption? |
| Financial relevance | Could it affect revenue, margins, cash flow, valuation, risk? |
| Catalyst relevance | Is it tied to an upcoming event? |
| Market relevance | Could others care? |

---

### 4. Information speed

Classify as:

| Speed | Examples |
|---|---|
| Slow | 10-K, industry report, 13F |
| Medium | earnings, macro, guidance, product launch |
| Fast | breaking news, social post, rumor |

MVP should focus on slow and medium information.

---

### 5. Alert priority

Suggested formula:

```text
priority_score = credibility_score * 0.35
               + novelty_score * 0.25
               + impact_score * 0.35
               + speed_bonus * 0.05
```

Do not overtrust this formula.

It is a ranking aid, not truth.

---

## Confidence bucket

| Bucket | Score range |
|---|---|
| Low | 0 to 39 |
| Medium | 40 to 69 |
| High | 70 to 100 |

---

## Required alert fields

Every alert must include:

- title
- affected company
- source
- source URL
- timestamp
- what changed
- why it matters
- credibility score
- novelty score
- impact score
- confidence bucket
- what to verify next
- human review status

---

## Human feedback

Each alert should allow:

- useful
- not useful
- false positive
- needs follow-up
- notes

This is how the system improves.
