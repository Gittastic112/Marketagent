# Implementation Checklist

## Setup fixes before coding

- [x] Create `.env.example`; the docs reference it, but only `.env` exists right now.
- [x] Keep Docker as the local PostgreSQL path using `docker-compose.yml`.
- [x] Keep the app database URL aligned with Docker credentials:
  `postgresql+psycopg://marketintel:marketintel_password@localhost:5432/marketintel`
- [x] Document that `localhost` works for a backend running directly on the laptop, while `postgres` is the host name only from inside another Docker container.
- [ ] Initialize Git in the actual project folder if this has not already been done.

## Phase 1: Backend foundation

- [x] Create a minimal FastAPI backend.
- [x] Load configuration from `.env`.
- [x] Connect to PostgreSQL with SQLAlchemy or SQLModel.
- [x] Add Alembic migrations.
- [x] Implement the MVP tables: Company, Source, RawDocument, Event, Alert, and ThesisNote.
- [x] Add pytest tests that do not call live external APIs.

## Phase 2: Manual research workflow

- [x] Add API endpoints for companies.
- [x] Add API endpoints for thesis notes.
- [x] Add API endpoints for raw documents.
- [x] Add API endpoints for events.
- [x] Add API endpoints for alerts.
- [x] Preserve source provenance on every stored document and event.

## Phase 3: Local dashboard

- [x] Create a simple Next.js frontend.
- [x] Show companies, thesis notes, raw documents, events, alerts, and daily brief.
- [x] Connect the frontend to the local FastAPI backend.
- [x] Do not add authentication or production deployment yet.

Note: frontend package installation and browser verification are still blocked in this shell because no JavaScript package manager is available.

## Phase 4: Source ingestion

- [ ] Add RSS/news ingestion with mocked tests.
- [ ] Add SEC EDGAR filing metadata ingestion with mocked tests.
- [ ] Store raw payloads, source URLs, timestamps, and content hashes.
- [ ] Add duplicate detection before generating events.

## Phase 5: Briefs and scoring

- [ ] Implement credibility, novelty, impact, and priority scoring.
- [x] Generate a rule-based daily brief before adding AI.
- [x] Link every brief item back to source records.
- [ ] Add human review status and notes for alerts.

## Phase 6: AI later

- [ ] Add AI only after source storage, events, alerts, and briefs work.
- [ ] Require AI outputs to cite stored source records.
- [ ] Include uncertainty, assumptions, and follow-up questions.
- [ ] Do not allow unsupported conclusions.
