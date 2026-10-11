Historical snapshot, not current instructions. Original relative links are preserved.

# Execution Runbook

**Updated:** 2026-08-24

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
curl http://localhost:8000/api/readiness
```

Frontend: `http://localhost:3000`

Backend: `http://localhost:8000`

pgAdmin: `http://localhost:5050`

For first-time environment and sign-in setup, use `07-local-development.md`.

## Focused Validation

The default production backend image does not bind-mount source code. After
adding a test file or changing backend code, run `docker compose up -d --build
backend` before executing it. The commands below set `/workspace/backend`
explicitly so `tests/...` paths cannot depend on the image's default directory.
Keep root-level debug scripts uniquely named. A `backend/test_*.py` file with
the same basename as `backend/tests/test_*.py` causes a pytest import mismatch;
`tests/test_pytest_layout.py` guards that boundary. Manual utilities under
`backend/scripts/` must not define `test_*` functions because broad pytest
invocations can collect them and run side effects against the configured
database. Put real assertions in `backend/tests/` and give manual entry points
names such as `run_*_smoke`.

Backend change:

```bash
docker compose exec -w /workspace/backend backend pytest -q tests/test_target.py
python3 -m py_compile backend/app/path/to/changed.py
```

Frontend change:

```bash
cd frontend
npm test
npm run typecheck
npm run build
```

Portfolio performance and risk runtime gate:

```bash
docker compose exec -w /workspace/backend backend pytest -q tests/test_portfolio_risk_return.py tests/test_api_portfolio_performance.py
cd frontend
npm run test:e2e:portfolio
```

The browser seed is explicitly Mock Data. Passing this gate proves calculation,
provenance, and UI behavior, but does not replace a manual smoke with real,
source-labeled inputs.

Real-input portfolio preflight:

```bash
docker compose exec -w /workspace/backend backend python scripts/check_portfolio_real_input_readiness.py \
  --portfolio-id <owned-portfolio-id> \
  --user-id <local-user-id>
```

The command is read-only. It does not seed records, capture snapshots, refresh
providers, or change the portfolio. Exit code `0` means every persisted-input
requirement passed; exit code `1` means the JSON report contains actionable
blockers; exit code `2` means the owned portfolio or arguments are invalid. The
same report appears on the owned portfolio detail page. `ready` is permission to
perform the manual smoke, not proof that the calculations are investment advice
or that a browser workflow passed.

FRED NFCI to Market Regime:

```bash
docker compose exec backend alembic upgrade head
docker compose exec -w /workspace/backend backend pytest -q \
  tests/test_fred_ingestion.py \
  tests/test_market_regime_macro_provider.py \
  tests/test_api_market_regime.py \
  tests/test_provider_health.py
```

With FRED configured, open Macro, import series `NFCI`, and inspect the generated
Processing Run in Data Health. Then open Portfolio > Market Regime. Preview is
read-only. Apply uses the latest stored NFCI observation, creates at most one
linked macro input for that observation, and performs no external fetch. Confirm
the displayed raw value, normalized Calculation, observation ID, date, formula,
freshness, and official FRED link before applying. A stale input may be stored
but must keep the overall regime state stale.

Daily Brief evidence-to-decision runtime gate:

```bash
docker compose exec -w /workspace/backend backend pytest -q tests/test_daily_brief.py tests/test_persisted_daily_brief.py tests/test_api_daily_brief.py
cd frontend
npm run test:e2e:brief
```

The browser workflow creates isolated source, event, portfolio, holding, and
price records. It verifies nullable move behavior, exact price provenance,
source navigation, and review state. A material event returned by deterministic
GET must report valuation analysis as `not_run`; `not_required` means no material
event requires valuation analysis.

AI exact-passage review:

```bash
docker compose exec -w /workspace/backend backend pytest -q tests/test_ai_citation_suggestions.py tests/test_ai_citations.py
cd frontend
npm test
npm run typecheck
```

Suggestion tests must prove that returned quotes match stored text at the exact
offsets and still pass the existing validator. A lexical candidate is not proof
that the source entails the generated claim; approval remains a human-reviewed
step.

Unified stored-research search:

```bash
docker compose exec -w /workspace/backend backend pytest -q tests/test_api_evidence_search.py
cd frontend
npm test
npm run typecheck
npm run test:e2e -- search-workflows.spec.ts
```

The backend gate must prove owner isolation, bounded private excerpts, shared
narrative labeling, and exclusion of pending, blocked, failed, or cross-user AI
output. The browser gate verifies record-type filters and stable destinations.

Browser workflows publish the isolated frontend on `13000` and backend on
`18000` by default. They must not reuse the normal stack's `3000/8000` ports.
The launcher exits with an explicit collision message if either E2E port is
already allocated. Override only when necessary:

```bash
E2E_FRONTEND_PORT=13010 E2E_BACKEND_PORT=18010 ./scripts/run_browser_workflows.sh daily-brief-runtime-smoke.spec.ts
```

Local Daily Brief automation:

```bash
docker compose exec backend alembic upgrade head
docker compose exec -w /workspace/backend backend pytest -q tests/test_daily_brief_schedule.py tests/test_api_daily_brief_schedule.py
docker compose --profile automation up --build -d scheduler
docker compose logs scheduler --tail=100
```

The scheduler is opt-in, polls no faster than every 15 seconds, uses a bounded
lease, and records Processing Runs. Scheduled briefs are deterministic and do
not call external AI. Keep explicit AI refresh under user control. Stop only the
worker with `docker compose stop scheduler`.

Migration change:

```bash
docker compose exec backend alembic heads
docker compose exec backend alembic current
docker compose exec -w /workspace/backend backend pytest -q tests/test_alembic.py
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
docker compose exec -w /workspace/backend backend pytest -q
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

Runtime liveness and readiness:

```bash
curl --fail http://localhost:8000/api/health
curl --fail http://localhost:8000/api/readiness
```

If liveness passes but readiness returns 503, inspect the returned migration and
schema blockers, then run `docker compose exec backend alembic upgrade head`.
Do not mask schema failures as stale investment data.

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
