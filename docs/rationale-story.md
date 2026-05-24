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

### 18. Made the app runnable through Docker Compose

Files added:

- `.dockerignore`
- `backend/Dockerfile`
- `frontend/Dockerfile`
- `frontend/.dockerignore`

Files changed:

- `docker-compose.yml`
- `.gitignore`
- `README.md`
- `frontend/README.md`

Why:

- The host shell did not expose `npm`, `pnpm`, `yarn`, or `corepack`.
- A later check showed `frontend/node_modules` did exist, so we could run the local TypeScript compiler directly.
- The local Next.js build still failed because macOS rejected the native SWC compiler binary signature.
- Next then tried to download a fallback compiler into `~/Library/Caches/next-swc`, but the sandbox blocked that write.

Root cause:

- The project code was not the source of that build failure.
- The failure came from local environment restrictions around the native Next.js compiler and sandboxed filesystem access.

Fix chosen:

- Added a backend Docker image.
- Added a frontend Docker image.
- Added backend and frontend services to Docker Compose.
- Set the backend container to use `postgres` as the database host.
- Set the frontend container to call `http://backend:8000`.
- Added generated frontend folders to `.gitignore`.

Why Docker is the right fix here:

- The project docs already describe a Docker-based local build.
- Docker gives the frontend a Linux Node environment instead of relying on the host shell.
- Docker avoids the missing host package manager problem.
- Docker avoids the broken macOS SWC binary path.

Verification:

- Docker Compose config parses successfully.
- Backend test suite passes: 26 passed.
- Frontend TypeScript check passes.

What could not be verified inside this sandbox:

- `docker compose build backend frontend`
- `docker compose up --build`

Reason:

- The sandbox blocks connecting to Docker Desktop's socket even after file permissions are granted.
- That means the Docker files can be checked for structure here, but the actual container build has to be run in a less restricted terminal.

### 19. Added manual create forms to the frontend

Files added:

- `frontend/app/actions.ts`
- `frontend/app/sources/page.tsx`
- `frontend/lib/form-payloads.ts`
- `frontend/lib/form-payloads.test.ts`

Files changed:

- frontend pages under `frontend/app/`
- `frontend/app/globals.css`
- `frontend/lib/api.ts`
- `frontend/package.json`
- `frontend/tsconfig.json`

Why:

- The backend already supports manual create endpoints.
- The frontend could read records, but it could not create records.
- A beginner-friendly market intelligence tool needs manual entry before ingestion.

What changed:

- Added create forms for companies.
- Added a sources page and create form.
- Added create forms for raw documents, events, alerts, and thesis notes.
- Added server actions so form submissions happen from the Next.js server.
- Added a small payload conversion helper to trim strings, convert blank fields to `null`, and convert IDs/scores to numbers.

Why server actions:

- The browser should not call Docker service names like `backend`.
- The Next.js server can call the backend through `NEXT_PUBLIC_API_BASE_URL`.
- This avoids CORS work for now.
- It keeps the first manual workflow simpler.

Why a form payload test:

- Form data arrives as strings.
- The backend expects numbers, booleans, and `null` for blank optional values.
- A small Node test proves the conversion layer does that consistently.

Verification:

- Frontend form payload tests pass: 5 passed.
- Frontend TypeScript check passes.
- Backend test suite passes: 26 passed.
- Docker Compose config still parses successfully.

### 20. Added frontend delete controls

Files changed:

- `frontend/app/actions.ts`
- `frontend/lib/api.ts`
- `frontend/lib/form-payloads.ts`
- `frontend/lib/form-payloads.test.ts`
- frontend table pages under `frontend/app/`
- `frontend/app/globals.css`

Why:

- The backend already had DELETE endpoints.
- The frontend could create records, but a beginner manually entering data needs a way to remove mistakes.
- Delete is simpler than edit because it only needs a record ID.

How it was done:

- Added a tested helper that reads a hidden `id` field from form data and converts it to a number.
- Added a `deleteApi` helper that sends `DELETE` requests to the backend.
- Added server actions for deleting companies, sources, raw documents, events, alerts, and thesis notes.
- Added delete buttons to each record table.
- Added small button styling so destructive actions are visually separate from create actions.

Verification:

- Frontend form payload tests pass: 6 passed.
- Frontend TypeScript check passes.
- Backend test suite passes: 26 passed.
- Docker Compose config still parses successfully.

### 21. Added debug console logs

Files added:

- `frontend/components/browser-debug-logger.tsx`

Files changed:

- `frontend/lib/api.ts`
- `frontend/app/actions.ts`
- `frontend/app/layout.tsx`
- `frontend/.env.local.example`
- `docker-compose.yml`
- `frontend/README.md`

Why:

- The frontend runtime still needs browser/Docker verification outside this sandbox.
- Console logs make that verification easier once the app is started in a normal terminal.

What logs were added:

- Browser mount log in DevTools.
- Frontend API request start, success, and failure logs.
- Create action logs.
- Delete action logs.

What is intentionally not logged:

- Full request payloads.
- Thesis text.
- Raw document text.
- API keys or secrets.

Reason:

- Logs should help trace flow without leaking research content.

How to disable logs:

- Set `NEXT_PUBLIC_DEBUG_LOGS=false`.

### 22. Added frontend edit controls

Files added:

- `frontend/lib/api.test.ts`

Files changed:

- `frontend/lib/api.ts`
- `frontend/app/actions.ts`
- frontend table pages under `frontend/app/`
- `frontend/app/globals.css`
- `frontend/README.md`

Why:

- Create and delete were working, but manual research entry still needed correction without deleting and re-creating records.
- The backend already had PATCH endpoints for every MVP model.
- Edit controls are the natural next layer before ingestion.

How it was done:

- Added a failing test for `patchApi`.
- Added `patchApi` after the test failed for the expected reason.
- Added update server actions for companies, sources, raw documents, events, alerts, and thesis notes.
- Added collapsible inline edit forms in each table row.

Why collapsible edit forms:

- Always-visible edit fields would make the dashboard noisy.
- A collapsible row keeps the table scannable while still making edits available.

Verification:

- Frontend tests pass: 7 passed.
- Frontend TypeScript check passes.
- Backend test suite passes: 26 passed.
- Docker Compose config still parses successfully.

### 23. Added persisted daily brief records

Files added:

- `backend/app/models/daily_brief.py`
- `backend/alembic/versions/20260524_0002_create_daily_briefs.py`
- `backend/tests/test_persisted_daily_brief.py`

Files changed:

- `backend/app/models/__init__.py`
- `backend/app/services/daily_brief.py`
- `backend/app/api/schemas.py`
- `backend/app/api/routes.py`
- `backend/tests/test_api_daily_brief.py`
- `frontend/app/actions.ts`
- `frontend/app/daily-brief/page.tsx`
- `frontend/lib/api.ts`

Why:

- The daily brief was only computed live.
- A useful research system needs a record of what the brief said on a given day.
- Persisting snapshots creates history without introducing AI or ingestion complexity.

What changed:

- Added a `daily_briefs` table.
- Added a `DailyBrief` SQLAlchemy model.
- Added a migration for the new table.
- Added `save_daily_brief`.
- Added `POST /daily-brief` to save the current generated brief.
- Added `GET /daily-brief-history` to list recent saved briefs.
- Added a frontend `Save brief` button.
- Added a saved briefs table on the Daily Brief page.

Why snapshot JSON:

- A saved brief should not change later just because events or alerts are edited.
- The system stores the generated payload exactly as it existed at save time.

Verification:

- Backend test suite passes: 29 passed.
- Frontend tests pass: 7 passed.
- Frontend TypeScript check passes.
- Docker Compose config still parses successfully.

Runtime note:

- This adds a new database table.
- The backend Docker command runs Alembic migrations at startup.
- If the app is already running, restart the backend or rerun `docker compose up --build` so the `daily_briefs` table is created.

### 24. Added pasted RSS XML ingestion

Files added:

- `backend/app/services/rss_ingestion.py`
- `backend/tests/test_rss_ingestion.py`
- `backend/tests/test_api_rss_ingestion.py`

Files changed:

- `backend/app/api/schemas.py`
- `backend/app/api/routes.py`
- `frontend/app/actions.ts`
- `frontend/app/documents/page.tsx`
- `frontend/lib/api.ts`
- `frontend/lib/form-payloads.ts`
- `frontend/lib/form-payloads.test.ts`

Why:

- The roadmap calls for RSS ingestion after the manual dashboard.
- We need source ingestion before scoring and AI.
- Live fetching external feeds adds network, uptime, feed format, and legal questions.
- A pasted XML import proves the ingestion path without those problems.

What changed:

- Added an RSS parser using Python standard library XML parsing.
- Added duplicate detection using a stable SHA-256 content hash.
- Stores each RSS item as a `RawDocument` with `document_type="rss_item"`.
- Stores title, source URL, published timestamp, raw description, raw payload JSON, and content hash.
- Added `POST /ingest/rss`.
- Added a frontend RSS XML import form on the Documents page.

What this does not do yet:

- It does not fetch live RSS feed URLs.
- It does not classify RSS items into events automatically.
- It does not call AI.

Reason:

- This keeps the first ingestion step deterministic, testable, and beginner-friendly.

Verification:

- Backend test suite passes: 32 passed.
- Frontend tests pass: 8 passed.
- Frontend TypeScript check passes.
- Docker Compose config still parses successfully.

### 25. Added pasted SEC filing metadata ingestion

Files added:

- `backend/app/services/sec_ingestion.py`
- `backend/tests/test_sec_ingestion.py`
- `backend/tests/test_api_sec_ingestion.py`

Files changed:

- `backend/app/api/schemas.py`
- `backend/app/api/routes.py`
- `frontend/app/actions.ts`
- `frontend/app/documents/page.tsx`
- `frontend/lib/api.ts`
- `frontend/lib/form-payloads.ts`
- `frontend/lib/form-payloads.test.ts`

Why:

- SEC EDGAR is a Tier 1 source in the docs.
- The roadmap calls for SEC filing metadata before full filing text ingestion.
- Metadata ingestion gives the system source-backed filing records without handling live SEC network calls yet.

What changed:

- Added a service that accepts supplied SEC filing metadata.
- Stores each filing as a `RawDocument` with `document_type="sec_filing_metadata"`.
- Stores accession number, form type, filing date, report date, primary document, filing URL, and content hash.
- Skips duplicate filings using a stable hash based on accession number, form type, and filing date.
- Added `POST /ingest/sec-filings`.
- Added a frontend SEC filing metadata import form on the Documents page.

What this does not do yet:

- It does not call SEC EDGAR live.
- It does not download filing text.
- It does not detect filing text changes.
- It does not auto-create events from filings.

Reason:

- This keeps ingestion deterministic and testable.
- It also keeps us inside the docs' principle: stable, legal, source-backed inputs first.

Verification:

- Backend test suite passes: 35 passed.
- Frontend tests pass: 9 passed.
- Frontend TypeScript check passes.
- Docker Compose config still parses successfully.

### 26. Added rule-based event extraction

Files added:

- `backend/app/services/event_extraction.py`
- `backend/tests/test_event_extraction.py`
- `backend/tests/test_api_event_extraction.py`

Files changed:

- `backend/app/api/schemas.py`
- `backend/app/api/routes.py`
- `frontend/app/actions.ts`
- `frontend/app/events/page.tsx`
- `frontend/lib/api.ts`
- `frontend/README.md`

Why:

- Ingestion creates raw documents, but the daily brief is driven by events.
- A market intelligence system needs a normalized layer between source material and alerts/briefs.
- Rule-based extraction gives us that layer before AI.

What changed:

- Added a service that creates one event per raw document that does not already have an event.
- SEC filing metadata becomes `event_type="sec_filing"` with slow information speed and high credibility.
- RSS items become `event_type="rss_news"` with fast information speed and source-based credibility.
- Manual/raw documents fall back to a generic `raw_document` event type.
- Added `POST /extract/events`.
- Added an Extract Events button on the Events page.

What this does not do yet:

- It does not use AI to summarize documents.
- It does not detect exact filing language changes.
- It does not create alerts automatically.
- The scoring is simple fixed-rule scoring, not a mature ranking model.

Reason:

- This is the correct bridge from source-backed storage to daily briefs.
- It keeps behavior auditable and testable.

Verification:

- Backend test suite passes: 37 passed.
- Frontend tests pass: 9 passed.
- Frontend TypeScript check passes.
- Docker Compose config still parses successfully.

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
- Docker Compose services for PostgreSQL, backend, frontend, and pgAdmin.
- Manual frontend create forms for companies, sources, documents, events, alerts, and thesis notes.
- Manual frontend edit controls for companies, sources, documents, events, alerts, and thesis notes.
- Manual frontend delete controls for companies, sources, documents, events, alerts, and thesis notes.
- Persisted daily brief snapshots and daily brief history.
- Pasted RSS XML ingestion with duplicate detection.
- Pasted SEC filing metadata ingestion with duplicate detection.
- Rule-based event extraction from raw documents.
- Tests for app health, settings, models, Alembic migration, and CRUD.

Not built yet:

- Docker build/run verification in this sandbox.
- Live SEC EDGAR fetching.
- Live RSS/news fetching.
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

### Dockerfiles

Used to make backend and frontend runnable without depending on host Python or host Node package managers.

Why:

- The local shell had missing or blocked frontend tooling.
- A Docker-based path is more consistent for beginners once Compose is set up.

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
11. Add Docker services for backend and frontend.
12. Add manual create forms in the frontend.
13. Add manual delete controls in the frontend.
14. Add debug console logs.
15. Add manual edit controls in the frontend.
16. Add persisted daily brief snapshots.
17. Add pasted RSS XML ingestion.
18. Add pasted SEC filing metadata ingestion.
19. Add rule-based event extraction from raw documents.

This order prevents a common failure:

```text
build AI/front-end first -> discover there is no reliable source-backed data model
```

We are building the foundation first because this product depends on trustworthy stored evidence.

## Next logical steps

Recommended next steps:

1. Restart Docker Compose so the new `daily_briefs` migration runs if it has not already run.
2. Test pasted RSS XML and SEC metadata import from the Documents page.
3. Test event extraction from the Events page.
4. Add automatic alert creation from high-priority events.

I would not start SEC ingestion yet. The manual workflow should be solid first.
