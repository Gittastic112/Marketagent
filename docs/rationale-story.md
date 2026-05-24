# Rationale Story

This file tracks what we did, why we did it, and how the outputs were produced.

The goal is not to sound impressive. The goal is to make the build process understandable.

## Project direction

We are building a local-first Market Intelligence Engine.

The important product decision is this:

```text
source -> storage -> classification -> scoring -> brief/alert
```

Not this:

```text
source -> chatbot answer
```

That choice matters because a market intelligence system needs evidence, provenance, and repeatable records. If we start with AI summaries first, the system becomes hard to audit and easy to fool.

## Chronology

### 1. Read the setup docs

Files reviewed:

- `README.md`
- `AGENTS.md`
- `docker-compose.yml`
- `.env.example`
- every file in `docs/`

What happened:

- The docs described a local build using Next.js, FastAPI, Docker, PostgreSQL, Alembic, and pytest.
- `docker-compose.yml` defined PostgreSQL and pgAdmin correctly for local use.
- `.env.example` was referenced in the docs, but it did not exist yet.
- `.env` existed and already had the local database URL.

Why this mattered:

- The project was still documentation-only.
- Before writing backend code, we needed to check whether the docs and local setup agreed with each other.
- The missing `.env.example` was a real beginner-hostile gap because new users should not have to infer environment variables from `.env`.

Output:

- Created `docs/implementation-checklist.md`.

### 2. Created the implementation checklist

File created:

- `docs/implementation-checklist.md`

Why:

- The docs needed a short, practical next-step list.
- The checklist turned broad product docs into an implementation order.
- It also recorded setup issues before code was written.

Main decisions:

- Backend first.
- PostgreSQL through Docker.
- Manual CRUD before external ingestion.
- Rule-based briefs before AI.
- AI only after source-backed storage works.

### 3. Built the minimal backend skeleton

Files added:

- `backend/app/main.py`
- `backend/app/core/config.py`
- `backend/app/db/base.py`
- `backend/app/db/session.py`
- model files under `backend/app/models/`
- `backend/requirements.txt`
- `pyproject.toml`
- `.env.example`
- `.gitignore`

Why:

- FastAPI gives the local API.
- SQLAlchemy gives explicit database models and relationships.
- PostgreSQL remains the real local database.
- `.env` keeps secrets and settings out of code.
- `.env.example` gives a safe template for setup.

Important choice:

- We used SQLAlchemy instead of SQLModel.

Reason:

- SQLAlchemy is explicit and widely used.
- For a beginner-friendly backend, explicit table models are easier to inspect than mixing validation and persistence too early.

### 4. Added the six MVP models

Models implemented:

- `Company`
- `Source`
- `RawDocument`
- `Event`
- `Alert`
- `ThesisNote`

Why these six:

- They are the minimum useful source-backed research loop.
- A company has sources and documents.
- Documents become events.
- Events can become alerts.
- Thesis notes give the system something to compare new information against.

What we did not add yet:

- `ThesisChange`
- `ProcessingRun`
- SEC ingestion
- RSS ingestion
- AI summaries
- frontend

Reason:

- Those are useful later, but not needed to prove the base storage/API system works.

### 5. Added Alembic migrations

Files added:

- `alembic.ini`
- `backend/alembic/env.py`
- `backend/alembic/script.py.mako`
- `backend/alembic/versions/20260524_0001_create_mvp_tables.py`

Why:

- Alembic records database structure changes.
- This avoids manually creating tables and forgetting what changed.
- It lets the database evolve in a controlled way.

Tool used:

- Alembic migration files.

Result:

- The migration created these PostgreSQL tables:
  - `companies`
  - `sources`
  - `raw_documents`
  - `events`
  - `alerts`
  - `thesis_notes`
  - `alembic_version`

### 6. Added tests before implementation

Test files added:

- `backend/tests/test_app.py`
- `backend/tests/test_settings.py`
- `backend/tests/test_models.py`
- `backend/tests/test_alembic.py`

Why:

- Tests define expected behavior before relying on the code.
- The first backend test run failed because pytest and the backend package did not exist yet.
- That failure was useful because it proved the tests were checking real missing behavior.

Tools used:

- `pytest`
- FastAPI `TestClient`
- in-memory SQLite for model tests

Why SQLite in tests:

- Tests should be fast and not require Docker.
- The real app still uses PostgreSQL from `.env`.
- SQLite is only used for isolated model/API tests.

### 7. Installed local Python dependencies

File added:

- `backend/requirements.txt`

Why:

- The environment did not have FastAPI, SQLAlchemy, Alembic, pytest, or related packages installed.
- A local `.venv` was created so dependencies stay inside the project folder.

Packages included:

- FastAPI
- Uvicorn
- SQLAlchemy
- psycopg
- Alembic
- pydantic-settings
- python-dotenv
- pytest
- httpx

### 8. Verified PostgreSQL migration once Docker was running

What happened:

- Docker initially had no running services.
- `docker compose up -d` pulled PostgreSQL and pgAdmin images.
- The pull was slow, but it eventually completed.
- PostgreSQL and pgAdmin started.
- `alembic upgrade head` applied the migration successfully.

Why:

- Unit tests are useful, but they do not prove the real PostgreSQL path works.
- Running Alembic against the Docker database proved that `.env`, SQLAlchemy, psycopg, Alembic, Docker, and PostgreSQL all lined up.

Verified state:

- PostgreSQL had the six MVP tables plus `alembic_version`.

### 9. Added manual CRUD API endpoints

Files added:

- `backend/app/api/schemas.py`
- `backend/app/api/routes.py`
- `backend/tests/test_api_crud.py`

File changed:

- `backend/app/main.py`

Endpoints added:

- `POST /companies`
- `GET /companies`
- `GET /companies/{company_id}`
- `POST /sources`
- `GET /sources`
- `GET /sources/{source_id}`
- `POST /raw-documents`
- `GET /raw-documents`
- `GET /raw-documents/{raw_document_id}`
- `POST /events`
- `GET /events`
- `GET /events/{event_id}`
- `POST /alerts`
- `GET /alerts`
- `GET /alerts/{alert_id}`
- `POST /thesis-notes`
- `GET /thesis-notes`
- `GET /thesis-notes/{thesis_note_id}`

Why:

- Manual CRUD is the first usable backend layer.
- It lets us create companies, sources, documents, events, alerts, and thesis notes before external ingestion exists.
- This keeps the product useful before SEC/RSS/API work.

Tool choices:

- Pydantic schemas for request and response validation.
- FastAPI routers to keep API routes separate from `main.py`.
- SQLAlchemy sessions through FastAPI dependency injection.

### 10. Verified manual CRUD

Test added:

- `backend/tests/test_api_crud.py`

What it verifies:

- Create/list/get company.
- Create/list/get source.
- Create/list/get raw document.
- Create/list/get event.
- Create/list/get alert.
- Create/list/get thesis note.

Result:

- Focused CRUD tests passed: 6 passed.
- Full backend test suite passed: 10 passed.

### 11. Local server attempt

What happened:

- Tried to start Uvicorn on `127.0.0.1:8000`.
- The app started successfully.
- The environment blocked binding to the local port with `operation not permitted`.

What this means:

- The FastAPI app imports and starts.
- The sandbox blocked opening the local network listener.
- The API behavior is still verified through FastAPI `TestClient`.

This is not an application bug based on the current evidence. It is an environment permission issue.

### 12. Added update and delete API endpoints

Files added:

- `backend/tests/test_api_update_delete.py`

Files changed:

- `backend/app/api/schemas.py`
- `backend/app/api/routes.py`

Endpoints added:

- `PATCH /companies/{company_id}`
- `DELETE /companies/{company_id}`
- `PATCH /sources/{source_id}`
- `DELETE /sources/{source_id}`
- `PATCH /raw-documents/{raw_document_id}`
- `DELETE /raw-documents/{raw_document_id}`
- `PATCH /events/{event_id}`
- `DELETE /events/{event_id}`
- `PATCH /alerts/{alert_id}`
- `DELETE /alerts/{alert_id}`
- `PATCH /thesis-notes/{thesis_note_id}`
- `DELETE /thesis-notes/{thesis_note_id}`

Why:

- Create/list/get is enough to prove the data model, but not enough for a usable manual workflow.
- A beginner using the app will make mistakes while entering companies, documents, events, alerts, and thesis notes.
- Update and delete make the manual workflow practical before external ingestion exists.

How it was done:

- Added tests first for update and delete behavior.
- The first test run failed with `405 Method Not Allowed`, which proved the tests were reaching existing resources and the missing behavior was specifically PATCH/DELETE support.
- Added update schemas where every field is optional.
- Added shared route helpers for update and delete to avoid repeating the same database logic six times.
- Added PATCH and DELETE routes for all six MVP resources.

Verification:

- Focused update/delete tests passed: 6 passed.
- Full backend test suite passed: 16 passed.

### 13. Added clearer API error handling

Files added:

- `backend/tests/test_api_errors.py`

Files changed:

- `backend/app/api/routes.py`

Why:

- The manual API could create, read, update, and delete records, but bad inputs still behaved badly.
- Duplicate records could leak raw database errors.
- Missing relationships could be accepted in the test database because SQLite does not enforce foreign keys by default.
- A beginner-friendly local API should return plain, predictable errors.

What changed:

- Duplicate unique records now return `409 Conflict`.
- Missing referenced records now return `404 Not Found`.
- Raw documents must reference an existing source.
- Raw documents, events, alerts, and thesis notes validate optional company/document/event references when provided.
- Shared commit handling now rolls back failed writes before returning an API error.

Tool behavior:

- Tests were written first.
- The first run failed for the right reasons:
  - duplicate inserts raised raw SQLAlchemy integrity errors
  - missing references were accepted
- Then route helpers were updated to make the API behavior explicit.

Verification:

- Focused error tests passed: 7 passed.
- Full backend test suite passed: 23 passed.

### 14. Added sample seed data

Files added:

- `backend/app/services/seed_data.py`
- `backend/tests/test_seed_data.py`
- `scripts/seed_sample_data.py`

Why:

- A beginner-friendly local app should not start with an empty database forever.
- Sample data makes it easier to test the API manually and understand what records look like.
- The seed logic needed to be idempotent, meaning you can run it repeatedly without creating duplicates.

What it seeds:

- Companies:
  - `AAPL`
  - `MSFT`
  - `NVDA`
- Sources:
  - `Manual Research`
  - `RSS Feed`
  - `SEC EDGAR`

How it was done:

- Added a service function that accepts a database session.
- The function checks for existing records before inserting.
- Added a small runner script that can be used later against the local PostgreSQL database.

Verification:

- Seed data test passed.
- The test confirms the first run creates records and the second run creates zero new records.

### 15. Added a rule-based daily brief service

Files added:

- `backend/app/services/daily_brief.py`
- `backend/tests/test_daily_brief.py`

Why:

- The product docs say the daily brief should come before AI.
- A rule-based brief proves the stored data model is useful without relying on LLMs.
- This keeps the system source-backed and auditable.

What it does:

- Pulls recent events.
- Ranks events by `priority_score`.
- Includes linked company, source name, and source URL where available.
- Includes recent alerts.
- Counts active thesis notes.
- Adds basic follow-up questions.

What it does not do yet:

- It does not call AI.
- It does not filter by exact date yet.
- It does not save briefs to the database yet.
- It does not expose a public API endpoint yet.

Verification:

- Daily brief test passed.
- Full backend test suite passed: 25 passed.

### 16. Exposed the daily brief through the API

Files added:

- `backend/tests/test_api_daily_brief.py`

Files changed:

- `backend/app/api/routes.py`

Endpoint added:

- `GET /daily-brief`

Why:

- The daily brief service was useful internally, but not reachable through the API.
- The frontend will need a simple endpoint to show the daily brief.
- Keeping the route thin makes the service easy to test separately from the web layer.

How it was done:

- Added an API test first.
- The first run failed with `404 Not Found`, proving the route was missing.
- Added a route that calls `generate_daily_brief(db)`.

Verification:

- Focused daily brief API test passed.
- Full backend test suite passed: 26 passed.

### 17. Added a read-only local dashboard scaffold

Files added:

- `frontend/package.json`
- `frontend/next.config.js`
- `frontend/tsconfig.json`
- `frontend/next-env.d.ts`
- `frontend/.env.local.example`
- `frontend/README.md`
- `frontend/app/layout.tsx`
- `frontend/app/globals.css`
- `frontend/lib/api.ts`
- `frontend/components/page.tsx`
- pages under `frontend/app/`

Why:

- The backend now has enough manual API surface to display useful records.
- A beginner-friendly app should have a local dashboard before ingestion gets complicated.
- The first dashboard should show stored data, not create new product complexity.

What it shows:

- overview metrics
- companies
- raw documents
- events
- alerts
- thesis notes
- daily brief

How it works:

- Next.js server pages call the FastAPI backend through `NEXT_PUBLIC_API_BASE_URL`.
- The default backend URL is `http://127.0.0.1:8000`.
- Shared TypeScript types live in `frontend/lib/api.ts`.
- Reusable page components live in `frontend/components/page.tsx`.

What we intentionally did not add:

- create/edit forms
- delete controls
- charts
- authentication
- production deployment
- external ingestion UI

Reason:

- The frontend should first prove that the backend data is readable and understandable.
- Forms are the next layer, but adding them before running the frontend would make debugging harder.

Environment issue found:

- `node` exists.
- `npm`, `pnpm`, `yarn`, and `corepack` are not available in the current shell.
- Because of that, frontend dependencies could not be installed and the Next.js app could not be run here yet.

This is a machine setup issue, not proof that the frontend code is wrong.

## Current project state

Working:

- Documentation baseline.
- Implementation checklist.
- `.env.example`.
- FastAPI backend skeleton.
- SQLAlchemy models.
- Alembic migration.
- PostgreSQL Docker schema, verified once.
- Manual create/list/get API endpoints.
- Manual update/delete API endpoints.
- Plain API errors for duplicate records and missing references.
- Idempotent sample seed data service.
- Rule-based daily brief generation service.
- `GET /daily-brief` endpoint.
- Read-only Next.js frontend scaffold.
- Frontend pages for overview, companies, documents, events, alerts, thesis notes, and daily brief.
- Tests for app health, settings, models, Alembic migration, and CRUD.

Not built yet:

- Frontend create/edit/delete forms.
- Frontend package installation and browser verification in this shell.
- Persisted daily brief records.
- SEC ingestion.
- RSS/news ingestion.
- Scoring logic implementation.
- AI usage.

## Tool map

### File search and inspection

Used to understand the repo before changing it.

Examples:

- list files
- read docs
- inspect current backend structure

Why:

- You do not want to write code before knowing the project shape.

### `apply_patch`

Used to create and edit files.

Why:

- It makes edits explicit.
- It avoids accidental broad rewrites.

### `pytest`

Used to verify backend behavior.

Why:

- It gives repeatable proof that code works.
- It catches regressions when new endpoints are added.

### FastAPI `TestClient`

Used to test API endpoints without starting a real server.

Why:

- The sandbox blocked opening port `8000`.
- TestClient still exercises the FastAPI app directly.

### Docker Compose

Used to start PostgreSQL and pgAdmin locally.

Why:

- The docs require a local PostgreSQL build through Docker.

### Alembic

Used to apply database migrations.

Why:

- Database schema changes need to be versioned.

### SQLAlchemy

Used for database models and sessions.

Why:

- It is explicit, mature, and fits FastAPI well.

### Next.js

Used for the frontend scaffold.

Why:

- It matches the project docs.
- It can render simple pages from the FastAPI API without adding frontend state management yet.

### Official framework docs

Used to confirm the current Next.js version before updating `frontend/package.json`.

Why:

- Frontend package versions change over time.
- Guessing framework versions is a bad habit.

## Why the order matters

The build order so far has been:

1. Confirm the docs and local setup.
2. Create a practical checklist.
3. Add database models.
4. Add migrations.
5. Add tests.
6. Verify PostgreSQL.
7. Add manual API endpoints.
8. Verify CRUD.
9. Add the daily brief.
10. Add a read-only frontend scaffold.

This order prevents a common failure:

```text
build AI/front-end first -> discover there is no reliable source-backed data model
```

We are building the foundation first because this product depends on trustworthy stored evidence.

## Next logical steps

Recommended next steps:

1. Make a JavaScript package manager available, then install and run the frontend.
2. Add basic frontend forms for manual companies, documents, events, alerts, and thesis notes.
3. Add persisted daily brief records if the frontend needs brief history.
4. Add SEC/RSS ingestion only after the manual dashboard works.

I would not start SEC ingestion yet. The manual workflow should be solid first.
