# AGENTS.md

## Project

This repo is for a local-first Market Intelligence Engine and portfolio tracker for public equity research.

The user is non-technical and learning from the beginning. Prefer clear, simple, incremental implementation over advanced engineering.

---

## Core product idea

The system ingests source material, stores it with provenance, detects changes,
scores credibility, tracks portfolio exposure, and generates useful research
outputs.

Core question:

> What changed, why does it matter, how credible is it, does it affect my thesis, and how exposed am I through my portfolio?

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
11. Portfolio holdings and transactions
12. Manual market prices and portfolio valuation
13. Exposure and concentration analytics

---

## Do not build yet

Do not build:

- trading execution
- buy/sell recommendations
- Twitter/X scraping
- Reddit scraping
- broker credential storage
- broker account syncing until OAuth/token security is designed
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
- Formatting/linting: ruff planned, not configured yet
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

## Security rules

1. Treat RSS, SEC filing text, CSV imports, markdown, social posts, and AI output as untrusted input.
2. Do not hardcode secrets, API keys, bearer tokens, broker tokens, or model keys.
3. Never commit `.env`.
4. Keep `.env.example` placeholder-only.
5. Do not store broker passwords directly. Future broker integrations must use official OAuth or token flows.
6. Do not scrape sources that prohibit scraping or unauthorized automated access.
7. Use official APIs, licensed data, approved exports, or manual imports.
8. Do not call live external APIs in tests.
9. Do not render imported text, markdown, RSS content, social posts, or AI output as trusted HTML.
10. Do not expose this app beyond localhost until authentication, authorization, CSRF/CORS, rate limiting, HTTPS, and secret handling are deliberately designed.
11. For CSV import/export, guard against malformed rows and CSV formula injection.
12. Read `docs/security-threat-model.md` before adding broker, AI, social, file import, or external API features.

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
