# Architecture

## System overview

The Market Intelligence Engine is a source-backed event system.

It should not be designed as a chatbot.

Correct architecture:

```text
Raw source
↓
Stored with provenance
↓
Normalized event
↓
Classified by speed/type
↓
Scored for credibility/novelty/impact
↓
Linked to company/thesis/narrative
↓
Brief or alert
```

---

## Core components

### 1. Frontend

Purpose:

- display dashboard
- show companies
- show documents
- show alerts
- show daily briefs
- allow human review

Recommended tool:

- Next.js

---

### 2. Backend

Purpose:

- API endpoints
- business logic
- scoring
- processing
- brief generation

Recommended tool:

- FastAPI

---

### 3. Database

Purpose:

- store companies
- store raw sources
- store events
- store alerts
- store thesis notes
- preserve provenance

Recommended tool:

- PostgreSQL through Docker

---

### 4. Ingestion layer

Purpose:

- pull data from external sources
- normalize raw inputs
- save source-backed records

Initial sources:

- SEC EDGAR
- RSS/news
- FRED later
- Alpha Vantage/Finnhub later

---

### 5. Processing layer

Purpose:

- classify information speed
- detect changes
- score credibility
- score novelty
- score potential impact
- cluster narratives later

---

### 6. Output layer

Purpose:

- daily intelligence brief
- company brief
- filing delta brief
- narrative shift alert later
- thesis update memo

---

## Information speed classes

### Slow information

Examples:

- 10-K
- 10-Q
- annual report
- industry report
- 13F
- regulatory trend

Edge:

- interpretation and synthesis

### Medium information

Examples:

- earnings
- guidance
- macro release
- product launch
- rating change

Edge:

- framing and contextualization

### Fast information

Examples:

- breaking headline
- tweet
- rumor
- sudden price move

Edge:

- filtering and credibility discipline

MVP should focus on slow and medium information first.

---

## First technical milestone

The first technical milestone is not AI.

It is:

```text
Can the system store a source-backed document, link it to a company, classify it, and show it in a daily brief?
```

If yes, the system foundation is correct.
