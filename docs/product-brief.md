# Product Brief
# Market Intelligence Engine

## One-line description

A local-first, source-backed research system that helps detect meaningful changes across public companies, narratives, filings, news, macro data, and thesis assumptions.

---

## Core problem

Markets produce too much information:

- filings
- news
- macro releases
- price moves
- rumors
- commentary
- narratives
- analyst reactions

Most people either:

1. read manually and miss things, or
2. automate summaries and amplify noise.

The problem is not lack of information.

The problem is knowing:

- what changed
- what matters
- what is credible
- what is new
- who may react
- whether it affects the thesis

---

## Target user

Initial user:

- individual investor
- finance student
- research analyst
- founder/researcher building a personal research OS
- someone tracking a concentrated watchlist of 10 to 25 companies

---

## MVP user story

As a user, I want to track a small set of public companies so that I can see important filings, news, thesis changes, and source-backed alerts in one place.

---

## MVP scope

The MVP should include:

1. Company watchlist
2. Manual thesis notes
3. Raw document storage
4. SEC filing ingestion
5. RSS/news ingestion
6. Basic event classification
7. Credibility scoring
8. Change detection
9. Daily intelligence brief
10. Source-backed dashboard

---

## Explicit non-goals

Do not build:

- automated trading
- buy/sell recommendations
- portfolio execution
- social scraping
- options flow engine
- high-frequency alerts
- institutional terminal clone
- public SaaS product
- multi-user product

---

## What good looks like

The system should produce outputs like:

> Apple filed a new 10-Q. Risk factor language around China supply chain exposure changed materially versus the prior filing. Credibility is high because the source is primary. This may affect the supply-chain risk thesis. Review required.

Every output should include:

- source
- timestamp
- company
- what changed
- why it matters
- credibility score
- novelty score
- link to raw document
- human review status

---

## Success criteria

The MVP is successful if it can:

- track 10 to 25 companies
- ingest and store source-backed documents
- classify events into slow, medium, and fast information
- generate a daily brief
- reduce manual research time
- avoid unsupported AI claims
- preserve source provenance
