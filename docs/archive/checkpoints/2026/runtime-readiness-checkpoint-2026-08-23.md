# Runtime Readiness Checkpoint

**Date:** 2026-08-23

## Problem

The backend liveness route could pass even when the database schema was not
usable by current Daily Brief code. Browser workflows also defaulted to the
normal application's `3000/8000` ports, causing Docker bind failures whenever
the application was already running.

## Delivered Boundary

- Kept `/api/health` as a lightweight process liveness probe.
- Added public `/api/readiness` with a database probe, expected/current Alembic
  head comparison, required table checks, and required column checks.
- Readiness failures return HTTP 503 with structured, sanitized blockers and
  recovery commands. No connection strings or exception text are returned.
- Normal and E2E Docker backend health checks now use readiness.
- The E2E frontend waits for a healthy E2E backend.
- Browser workflow and E2E Compose defaults moved to `13000/18000`.
- Browser workflow startup rejects occupied ports with an actionable message.
- Daily Brief shows the actual structured backend failure, links to Data Health,
  and treats local scheduling as an independently available panel.
- Data Health shows database, schema, current migration, expected migration,
  missing tables, missing columns, and safe recovery steps.
- Server-rendered requests now verify and decode standard, secure, and chunked
  NextAuth session cookies directly from the asynchronous request cookie store.
  This fixes the application-wide authentication failure without forwarding or
  logging the cookie and without caching identity headers across requests.
- The server API helper waits for the Next.js runtime `connection()` boundary
  before reading authentication and backend URL environment variables. This
  prevents standalone builds from caching a false not-configured response.

## Validation

- 120 frontend tests passed.
- TypeScript passed.
- Python source and tests compiled.
- Normal and E2E Compose configuration passed.
- Browser and release shell scripts passed syntax validation.

Backend pytest and live Docker/browser execution remain pending because this
agent cannot access the user's Docker socket. The runtime gate is:

```bash
docker compose -p market-intel-e2e -f docker-compose.e2e.yml down --remove-orphans
docker compose down
docker compose up --build -d
docker compose exec backend alembic upgrade head
curl --fail http://localhost:8000/api/readiness
docker compose exec -w /workspace/backend backend pytest -q tests/test_runtime_readiness.py tests/test_daily_brief_schedule.py tests/test_api_daily_brief_schedule.py
cd frontend && npm run test:e2e:brief
```
