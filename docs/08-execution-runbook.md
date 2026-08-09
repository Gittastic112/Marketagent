# Execution Runbook

**Updated:** 2026-08-08

This is an operating checklist, not phase history. Completed phase records live
under `archive/checkpoints/` and `archive/plans/`.

## Start a Task

1. Read `HANDOFF.md`, `00-current-state.md`, and the relevant core doc.
2. Inspect the actual route, service, model, migration, frontend component, and tests.
3. State a small plan and likely files.
4. Add a failing test first where practical.
5. Implement the smallest safe change.
6. Run focused tests, then the appropriate broader baseline.
7. Update only current docs whose reality changed.

Split work that touches more than 10 files unless the task is explicitly a
cross-cutting audit, migration, or documentation reorganization.

## Start the Stack

```bash
cd "/Users/mananmaheshwari/Documents/Codex/Market Intelligence App/market-intelligence-md-files copy"
docker compose up --build -d
docker compose ps
docker compose exec backend alembic upgrade head
curl http://localhost:8000/api/health
```

Frontend: `http://localhost:3000`

Backend: `http://localhost:8000`

pgAdmin: `http://localhost:5050`

For first-time environment and sign-in setup, use `07-local-development.md`.

## Focused Validation

Backend change:

```bash
docker compose exec backend pytest -q backend/tests/test_target.py
python3 -m py_compile backend/app/path/to/changed.py
```

Frontend change:

```bash
cd frontend
npm test
npm run typecheck
npm run build
```

Migration change:

```bash
docker compose exec backend alembic heads
docker compose exec backend alembic current
docker compose exec backend pytest -q backend/tests/test_alembic.py
```

Damodaran knowledge change:

```bash
python3 -m unittest -q damodaran_knowledge_base_v1/tools/test_audit_kb.py
python3 damodaran_knowledge_base_v1/tools/audit_kb.py
```

Documentation change:

```bash
python3 scripts/check_docs.py
git diff --check
```

## Full Baseline

```bash
docker compose exec backend pytest -q
cd frontend
npm test
npm run typecheck
npm run build
cd ..
python3 damodaran_knowledge_base_v1/tools/audit_kb.py
python3 scripts/check_docs.py
git diff --check
```

The last verified product baseline is recorded in `00-current-state.md`. Do not
overwrite that count with a focused-test count.

## Common Operations

Logs:

```bash
docker compose logs backend --tail=100
docker compose logs frontend --tail=100
```

Damodaran scoped import:

```bash
docker compose exec backend python /workspace/scripts/ingest_damodaran.py --only country_stats
```

Local auth preflight:

```bash
python3 scripts/check_local_auth.py
```

Backup and restore scripts:

```bash
./scripts/backup_local.sh
./scripts/restore_local.sh PATH_TO_BACKUP
```

Review script arguments before running restore or reset operations. Never delete
the database volume unless the user explicitly accepts data loss.

## Debugging Order

1. Read the visible error and exact browser/network response.
2. Check `docker compose ps`.
3. Check backend and frontend logs.
4. Call the backend health route directly.
5. Verify migration head.
6. Verify required environment variables without printing secrets.
7. Reproduce with the smallest focused test.
8. Fix the owning layer rather than masking the error in UI code.

For a missing Lightning CSS native module, recreate the frontend container and
its anonymous `node_modules` volume. Do not bind-mount host modules into Linux.

## Data and Trust Checklist

- Is every claim typed as Fact, Source Summary, Calculation, User Assumption,
  AI Interpretation, Estimate, or Mock Data?
- Is source, freshness, confidence, and review state available?
- Are missing providers shown as not configured?
- Does imported content remain untrusted?
- Does a processing run expose external-action failures?
- Are user-owned resources owner-scoped?
- Are valuation assumptions reviewed and traceable?

## Documentation Maintenance

When behavior changes:

1. Update the relevant core doc.
2. Update `00-current-state.md` only if product status or baseline changes.
3. Update `roadmaps/feature-register.md` for feature status changes.
4. Update `roadmaps/product-roadmap.md` if priorities or gates change.
5. Replace the short `HANDOFF.md` status; do not append history.
6. Move detailed shipped evidence to `archive/checkpoints/YYYY/`.
7. Run `python3 scripts/check_docs.py`.

## Completion Report

Report files changed, tests run, manual checks, known limitations, and the next
recommended task. Do not claim a browser workflow was validated if only unit
tests or a build ran.

The previous 39-phase cumulative history is preserved at
[`archive/assessments/08-execution-runbook.md`](archive/assessments/08-execution-runbook.md).
