# Local Operations Skill

## Purpose

Run local services, migrations, tests, and troubleshooting without damaging user data or hiding failures.

## When to use

- Docker setup, service health, migrations, test runs, logs, handoff verification, backend restart loops, frontend/backend connectivity.

## When NOT to use

- Pure doc edits that do not need verification.

## Prerequisites

- Read `docs/07-local-development.md`.
- Check `git status --short`.

## Inputs

- Current task.
- Service status.
- Test scope.
- Error logs.

## Outputs

- Verified commands and results.
- Known limitations.
- Safe next action.

## Workflow

1. Check service state with Docker.
2. Inspect logs before guessing.
3. Check Alembic heads before migration fixes.
4. Run narrow tests first.
5. Run broader tests when risk warrants.
6. Avoid destructive resets unless explicitly approved.
7. Update handoff or docs when verification state changes.
8. For local auth, use only the root `.env`, recreate the frontend container after changes, and verify `/api/auth/readiness` without printing credential values.
9. For workflow regressions, run an authenticated browser lifecycle that creates
   temporary records, verifies derived state, and removes every temporary
   record. Confirm cleanup with the API or database without exposing secrets.
10. Prefer `npm run test:e2e` from `frontend/` for valuation/PDF workflows. It
    owns only the `market-intel-e2e` Compose project, uses a tmpfs database and
    non-default ports, migrates a fresh schema, and cleans containers/volumes on
    exit. Never substitute the normal local database.
11. Treat a fresh migration failure as a release blocker. Repair schema
    ownership in Alembic; do not restore runtime DDL endpoints or stamp past the
    failure.

## Acceptance criteria

- Test/verification claims include command and result.
- Alembic state is known before database advice.
- No user data is deleted without explicit approval.
- Unrelated dirty worktree changes are not reverted.
- Local-auth checks report configured/missing state only; they never print the username, password, or session secret.
- Browser lifecycle checks record routes, assertions, and cleanup; they do not
  leave test portfolios, transactions, prices, or snapshots behind.
- The isolated E2E Compose project is absent after the runner exits.
- Dependency overrides are accepted only after audit, typecheck, production
  build, and relevant browser workflows pass.

## Common mistakes

- Running `docker compose down -v` casually.
- Stamping Alembic without understanding history.
- Assuming frontend errors mean frontend bugs when backend is restarting.
- Reporting old test counts.
- Editing `frontend/.env.local` while expecting Docker Compose to load local-auth values.
- Running authenticated browser tests against the user's normal PostgreSQL volume.
- Treating npm's suggested framework downgrade as a safe audit fix.

## Do not do

- Do not use destructive git or Docker commands without explicit approval.
- Do not leave long-running sessions needed for the task.
- Do not claim tests pass unless they were run.

## Related skills

- `architecture-overview`
- `backend-api-change`
- `documentation-workflow`
- `security-review`

## References

- `docs/07-local-development.md`
- `docs/HANDOFF.md`
- `AGENTS.md`
