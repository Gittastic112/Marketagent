# AGENTS.md

## Project

This repo is for a local-first Market Intelligence Engine for public equity research.

The user is non-technical and learning from the beginning. Prefer clear, simple, incremental implementation over advanced engineering.

---

## Core product idea

The system ingests source material, stores it with provenance, detects changes, scores credibility, and generates useful research outputs.

Core question:

> What changed, why does it matter, how credible is it, and does it affect my thesis?

---

## MVP scope

Build a local app for tracking 10 to 25 public companies.

Initial features:

1. Company watchlist
2. Manual thesis notes
3. Raw document storage
4. SEC filing ingestion
5. RSS/news ingestion
6. Basic event classification
7. Credibility scoring
8. Change detection
9. Daily intelligence brief
10. Simple dashboard

---

## Do not build yet

Do not build:

- trading execution
- buy/sell recommendations
- Twitter/X scraping
- Reddit scraping
- options flow engine
- real-time market alerts
- multi-user authentication
- payment system
- production cloud deployment
- complex vector database setup
- LangChain-heavy architecture
- Kubernetes
- Kafka

---

## Technical stack

Use:

- Frontend: Next.js
- Backend: Python FastAPI
- Database: PostgreSQL through Docker
- ORM: SQLAlchemy or SQLModel
- Migrations: Alembic
- Tests: pytest
- Formatting/linting: ruff
- Environment variables: `.env`

---

## Engineering rules

1. Keep code simple and readable.
2. Preserve source provenance for every document, event, alert, and brief.
3. Never hardcode API keys.
4. Use `.env` for secrets.
5. Add tests for every module.
6. Do not call live APIs in tests.
7. Use mocked responses in tests.
8. Do not add unnecessary dependencies.
9. Update documentation when architecture changes.
10. Ask for clarification only if a decision would materially change the project.

---

## Data rules

Every ingested item must preserve:

- source name
- source type
- source URL if available
- published timestamp
- ingestion timestamp
- raw payload or raw text
- hash of raw content
- linked company if relevant

---

## AI rules

AI-generated outputs must:

- link back to source records
- include confidence or uncertainty
- avoid unsupported claims
- identify assumptions
- identify what would falsify the interpretation

Do not let LLMs invent sources.

---

## Product principle

This is not an AI summarizer.

It is a source-backed intelligence system.

The order is:

```text
source → storage → classification → scoring → brief/alert
```

Not:

```text
source → chatbot answer
```
