# Daily Brief Scheduler Runtime Checkpoint

**Date:** 2026-08-24

## Scope

This checkpoint closes the remaining runtime gate for the opt-in local Daily
Brief scheduler. It records an actual due cycle against the normal local
PostgreSQL database and a repeated cycle proving owner/date idempotency. It does
not claim that the separate real-input portfolio smoke or complete 20-route
browser matrix passed.

## Starting State

- Backend, frontend, PostgreSQL, and scheduler containers were running.
- Backend, frontend, and PostgreSQL healthchecks were healthy.
- `/api/health` returned success.
- `/api/readiness` returned `ready` with no missing tables or columns.
- Alembic source and database heads were both `ee6ee6ee6ee6`.
- The scheduler log contained startup only and no prior schedule Processing Run.
- The existing application owner was `local-user`; no schedule existed.

## Runtime Exercise

1. The authenticated schedule API created schedule `1` for `local-user` at
   07:00 `Asia/Kolkata`, every day, using
   `deterministic_no_external_ai` generation.
2. Only that schedule's `next_run_at` was moved into the past to avoid waiting
   until the next calendar run.
3. Restarting only the scheduler container caused the real worker to lease and
   process the due schedule.
4. The first cycle reported one schedule checked, one completed, one brief
   created, and zero failures.
5. Processing Run `1` completed successfully with `source_type = internal`,
   `created_count = 1`, `error_count = 0`, no error details, and metadata limited
   to schedule ID, scheduled time, generation mode, and brief ID.
6. Brief `2` was persisted for `local-user` and local date `2026-08-24` with
   review state `new`.
7. The schedule cleared its lease, linked Processing Run `1` and brief `2`, and
   advanced to `2026-08-25T01:30:00Z`.
8. A repeated controlled due cycle created Processing Run `2`, reused brief `2`,
   reported `created_count = 0`, left exactly one brief for the date, cleared the
   lease, and advanced to the same next scheduled time.
9. The temporary opt-in schedule was disabled through the authenticated API
   after validation. It now has no next run, while its links to Processing Run
   `2` and brief `2` remain intact.

## Validation

- Daily Brief focused backend gate: 20 passed.
- Portfolio risk/return, performance, and dashboard focused gate: 16 passed.
- Live authenticated dashboard GET: success in 45 ms with no warnings; counts
  remained 2 Processing Runs, 2 briefs, and 0 alerts before and after the read.
- Frontend tests: 122 passed.
- TypeScript: passed.

The frontend checks ran in the existing validation image with current source
and required non-secret repository files mounted read-only. Protected
environment files were not mounted or read.

## Remaining Gates

- The normal database contains no portfolios, holdings, snapshots, price
  observations, FX observations, benchmark configuration, or usable DCF output.
  The manual real-input portfolio smoke therefore remains open and must not be
  replaced by the isolated Mock Data fixture.
- The complete authenticated 20-route browser matrix was not rerun because the
  host runner cannot read the protected local-auth environment and the running
  frontend image does not include Playwright. Existing prior browser evidence is
  unchanged.
- The host production build remains blocked by protected environment/build
  artifacts. Secret protection was not weakened.
