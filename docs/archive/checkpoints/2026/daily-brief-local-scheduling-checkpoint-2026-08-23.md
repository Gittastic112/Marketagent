# Daily Brief Local Scheduling Checkpoint

**Date:** 2026-08-23

## Delivered Boundary

- One owner-scoped Daily Brief schedule with an IANA timezone, local time,
  weekdays, persisted next run, lease, and last-run provenance.
- Deterministic timezone and weekday calculation, including daylight-saving
  behavior provided by the Python timezone database.
- Idempotent generation by owner and local brief date.
- A bounded lease and row-lock query for overlapping worker protection.
- Sanitized Processing Run audit records for successes and failures.
- GET and PUT schedule routes plus an owner-scoped run-due route.
- An opt-in Compose automation profile with a 256 MB worker limit and bounded
  polling interval.
- A responsive Daily Brief schedule form showing enabled, due, next-run,
  last-status, last-success, and Processing Run state.
- Backend service/API tests, frontend integrity coverage, and an authenticated
  browser workflow.

Scheduled generation deliberately uses the deterministic briefing path and does
not call external AI. The existing explicit refresh action remains the only
Daily Brief path that can run configured AI interpretation.

## Validation Performed

- `npm run typecheck`: passed.
- Focused frontend API and integrity tests: 54 passed.
- `python3 -m compileall -q app tests`: passed.
- `docker compose --env-file /dev/null config --quiet`: passed.

## Partial Runtime Evidence

The user supplied the following runtime evidence on 2026-08-24:

- The scheduler image built successfully and its container started.
- Backend health returned `ok`.
- Readiness returned `ready` at migration head `ee6ee6ee6ee6` with no missing
  tables or columns.
- The Daily Brief authenticated browser workflow passed.
- The complete backend suite passed all 584 tests with four upstream
  `openpyxl` warnings.

The supplied output did not contain scheduler startup/cycle logs and the browser
workflow configured a future schedule. It therefore did not prove that the
worker claimed a due schedule, created or reused a brief, wrote a sanitized
Processing Run, and advanced the schedule.

## Remaining Runtime Gate

From a normal terminal with Docker access, exercise one due schedule and inspect
the worker result:

```bash
docker compose exec postgres psql -U marketintel -d marketintel -c \
  "SELECT id, email FROM users ORDER BY created_at LIMIT 5;"
docker compose stop scheduler
docker compose exec postgres psql -U marketintel -d marketintel -c \
  "INSERT INTO daily_brief_schedules (user_id, enabled, timezone, local_time, days_of_week, next_run_at, last_status) SELECT id, true, 'UTC', '07:00:00', '[0,1,2,3,4,5,6]'::json, now() - interval '1 minute', 'scheduled' FROM users ORDER BY created_at LIMIT 1 ON CONFLICT (user_id) DO UPDATE SET enabled = true, timezone = 'UTC', days_of_week = '[0,1,2,3,4,5,6]'::json, next_run_at = now() - interval '1 minute', lease_expires_at = NULL, last_status = 'scheduled', updated_at = now();"
docker compose run --rm scheduler python -m app.workers.daily_brief_scheduler --once
docker compose exec postgres psql -U marketintel -d marketintel -c \
  "SELECT id, user_id, last_status, last_processing_run_id, last_brief_id, next_run_at, lease_expires_at FROM daily_brief_schedules ORDER BY updated_at DESC LIMIT 5;"
docker compose exec postgres psql -U marketintel -d marketintel -c \
  "SELECT id, status, created_count, error_count, error_details_json, metadata_json FROM processing_runs WHERE run_type = 'daily_brief_schedule' ORDER BY id DESC LIMIT 5;"
docker compose exec postgres psql -U marketintel -d marketintel -c \
  "SELECT id, user_id, brief_date, title, review_status, created_at FROM daily_briefs ORDER BY id DESC LIMIT 5;"
docker compose --profile automation up -d scheduler
docker compose logs scheduler --tail=100
```

Do not mark the automation runtime gate passed until a due worker cycle and its
Processing Run, generated brief, and advanced `next_run_at` are inspected.
