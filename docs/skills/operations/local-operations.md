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
8. For Compose auth, use the root `.env`; recreate both backend and frontend after shared-secret changes. Verify `/api/auth/readiness` without printing values. Host development has a separate process environment, as documented in local setup.
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
12. Browser workflows use the isolated `13000/18000` ports by default and must
    preflight collisions before startup. Do not reuse `3000/8000` while the
    normal stack is running.
13. Respect protected secret files. Agents may verify readiness state or consume
    already exported variables, but must not read `.env`; when that blocks a
    runtime check, give the exact user-run command and keep the gate pending.
14. The production backend does not bind-mount source code. Use the runbook's
    source-mounted, network-disabled test Compose for edited-source tests;
    production image tests can otherwise certify old code.
15. Before debugging an import-file mismatch, compare root `backend/test_*.py`
    basenames with `backend/tests/test_*.py`. Preserve untracked/prior work;
    establish ownership and obtain direction before removing a scratch collision.
    Do not clear broad caches or delete the real suite file.
16. Keep manual scripts out of pytest collection. A file under
    `backend/scripts/` must not expose a `test_*` function, and any database smoke
    utility must use isolated disposable storage. Move durable assertions into
    `backend/tests/`; `test_pytest_layout.py` enforces both collection boundaries.
17. For concurrent agents, follow the parallel-workstreams reference and runbook.
    Current browser/release/restore project names collide across worktrees;
    serialize those lanes. Different ports alone do not isolate cleanup or volumes.
    Keep test databases, build outputs and new fixtures separate from normal data.

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
- Docker or browser validation is not claimed when socket or credential access prevented execution.
- Container-relative validation commands resolve to real test files.

## Common mistakes

- Running `docker compose down -v` casually.
- Stamping Alembic without understanding history.
- Assuming frontend errors mean frontend bugs when backend is restarting.
- Reporting old test counts.
- Editing `frontend/.env.local` while expecting Docker Compose to load local-auth values.
- Running authenticated browser tests against the user's normal PostgreSQL volume.
- Treating npm's suggested framework downgrade as a safe audit fix.
- Running new tests in a stale production image or splitting a multiline pytest
  command by omitting shell continuation backslashes.
- Keeping a root scratch test with the same basename as a real suite module.
- Naming a manual database utility `test_*`, which lets a broad pytest run
  execute it against the configured database.

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
