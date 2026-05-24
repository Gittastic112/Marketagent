# Roadmap

## Phase 0: Project setup

Goal:

- create repo
- add docs
- initialize Git
- start Docker/PostgreSQL
- prepare Codex instructions

Deliverables:

- README.md
- AGENTS.md
- docker-compose.yml
- .env.example
- docs folder
- Git initialized

---

## Phase 1: Documentation/spec pass

Goal:

Convert strategy into implementation specs.

Deliverables:

- product-brief.md
- architecture.md
- local-development-plan.md
- scoring-framework.md
- database-schema.md
- data-sources.md
- codex-prompts.md

No application code yet.

---

## Phase 2: Backend foundation

Goal:

Create minimal backend.

Deliverables:

- FastAPI app
- PostgreSQL connection
- database models
- migrations
- tests

Core models:

- Company
- Source
- RawDocument
- Event
- Alert
- ThesisNote

---

## Phase 3: Manual research tracker

Goal:

Make the app useful before external APIs.

Features:

- add company
- add thesis note
- add raw document manually
- create event manually
- create alert manually
- view records through API

---

## Phase 4: Simple dashboard

Goal:

Create usable local UI.

Pages:

- Home
- Companies
- Company detail
- Raw documents
- Thesis notes
- Alerts
- Daily brief

---

## Phase 5: Daily brief generator

Goal:

Generate simple source-backed daily brief.

Inputs:

- raw documents
- events
- alerts
- thesis notes

Output:

- what happened
- why it matters
- source evidence
- credibility
- novelty
- follow-up questions

---

## Phase 6: SEC filing ingestion

Goal:

Pull public company filing metadata and documents.

Features:

- CIK mapping
- fetch filings
- store accession number
- store form type
- store filing date
- store source URL
- store raw text if available

---

## Phase 7: News/RSS ingestion

Goal:

Pull news from RSS feeds or basic news sources.

Features:

- RSS feed list
- headline ingestion
- URL storage
- source classification
- duplicate detection

---

## Phase 8: Scoring system

Goal:

Make outputs ranked and useful.

Scores:

- credibility score
- novelty score
- impact score
- information speed
- confidence bucket

---

## Phase 9: AI assistance

Goal:

Use AI only after source storage works.

AI tasks:

- summarize documents
- extract key claims
- label events
- draft daily brief
- identify contradictions
- suggest follow-up questions

Rules:

- every AI output must link to source IDs
- no source, no conclusion

---

## Phase 10: Narrative clustering

Goal:

Track repeated causal claims across sources.

Features:

- semantic grouping
- narrative labels
- cluster velocity
- supporting sources
- opposing sources

---

## Phase 11: Positioning and flows later

Goal:

Add market reaction context.

Possible sources:

- price and volume
- short interest
- options data
- COT data
- ETF ownership

Do not build this until the base engine works.
