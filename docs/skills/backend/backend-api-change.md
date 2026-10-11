# Backend API Change Skill

## Purpose

Make backend API changes without route, schema, service, model, migration, or test drift.

## When to use

- Adding or changing FastAPI endpoints.
- Changing response shapes or API envelope behavior.
- Adding service logic behind a route.
- Touching SQLAlchemy models or Alembic migrations.

## When NOT to use

- Pure frontend changes.
- Documentation-only changes that do not describe backend behavior.

## Prerequisites

- Read [backend rules](../../../backend/AGENTS.md) and use the code map to locate
  the owning domain.
- Inspect the relevant router, schema, service, model, migration, and tests.

## Inputs

- Endpoint behavior.
- Pydantic schema expectations.
- Persistence requirements.
- Existing test patterns.

## Outputs

- Thin route.
- Service-owned business logic.
- Stable `ApiResponse` envelope.
- Tests for success and important failure states.
- Updated docs when behavior changes.

## Workflow

1. Locate router in `backend/app/api/routers/`.
2. Locate the domain contract in `backend/app/schemas/`; the legacy
   `backend/app/api/schemas.py` is a compatibility facade/unextracted legacy owner.
   New valuation/portfolio fields belong in their narrow modules. Pure calculation
   contracts must not import HTTP, services or ORM.
3. Locate service in `backend/app/services/`.
4. Locate model and migration if persistence changes.
5. Add or update focused tests first where practical.
6. Implement the smallest service/route change.
7. Return envelope responses and specific errors.
8. Run targeted backend tests, then broader tests if risk warrants.
9. Resolve owned parent resources before reading child evidence or source IDs.
10. Keep deterministic suggestion/read endpoints separate from validation or
    mutation endpoints. Bound query limits, source scans, and returned excerpts.
11. For cross-model search, apply ownership filters inside each model query,
    exclude records without a truthful company relationship when company-filtered,
    preserve one global result limit, and carry scope/review/mock metadata.

## Acceptance criteria

- Route is thin.
- Business logic is in a service.
- Response shape matches frontend client expectations.
- No secrets leak in errors/logs.
- Tests cover the changed behavior.
- Evidence candidates are not described as validated claims, and read endpoints
  cannot silently mutate review state.
- Search tests cover cross-user isolation and pending/blocked AI exclusion.

## Common mistakes

- Returning ORM objects that schemas do not support.
- Nesting `ApiResponse` inside `data`.
- Changing a route path without updating frontend callers.
- Adding model fields without migrations.

## Do not do

- Do not make live external API calls in tests.
- Do not expose API keys to frontend code.
- Do not make destructive migrations without explicit approval.

## Related skills

- `architecture-overview`
- `data-ingestion-workflow`
- `security-review`
- `local-operations`

## References

- `docs/02-architecture.md`
- `docs/03-database-schema.md`
- `docs/08-execution-runbook.md`
- `backend/tests/helpers.py`
