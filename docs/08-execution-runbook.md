# Execution Runbook

Updated: 2026-10-10. This document owns commands, not historical phase records.
Run commands from the repository root unless a different directory is stated.

## Start a change

Read [the handoff](HANDOFF.md), nearest AGENTS.md, [code map](code-map.md), and
the relevant current reference. Inspect status and actual owning code. State a
bounded plan, add tests where practical, preserve user changes, and report
verified scope. Use [local setup](07-local-development.md) for first-time login
and environment configuration. Never print secrets.

## Choose the right environment

| Purpose | Environment |
|---|---|
| Normal application | docker-compose.yml, production images, persistent user database |
| Edited-source backend tests | docker-compose.test.yml, network disabled, disposable SQLite, read-only source/data mounts |
| Repository/recovery script tests | docker-compose.tools.yml, Git/shasum, network disabled, read-only source, executable temporary fixture scripts; no Docker socket |
| Hot-reload development | docker-compose.yml plus docker-compose.dev.yml |
| Browser/release verification | Separate disposable project using docker-compose.e2e.yml |
| Genuine-input portfolio proof | User's real, reviewed data; never replace with Mock Data |

The normal backend image does not mount source. Running pytest in an existing
container can test old code. The frontend production image has no compiler or
test runner. Building images alone does not replace running containers.
The backend runtime target now also excludes pytest and backend/tests. Unit/E2E
Compose explicitly select the test target. For host test environments install
backend/requirements-test.txt; requirements.txt is runtime-only.

## Focused and full source verification

Backend, using edited source and repository workbook fixtures without normal
database settings or network access:

~~~bash
docker compose -f docker-compose.test.yml build backend-tests
docker compose -f docker-compose.test.yml run --rm backend-tests pytest -q -p no:cacheprovider backend/tests/test_schema_boundaries.py
docker compose -f docker-compose.test.yml run --rm backend-tests
~~~

Replace the focused test path with the behavior being changed. Tests use their
isolated database fixtures, not normal portfolio rows. The default database is
also disposable SQLite inside the container; PostgreSQL-specific browser/migration
checks require the separate disposable runtime below. Inspect test setup before
running an unfamiliar manual script. Do not collect root debug scripts as tests.

Frontend, from frontend:

~~~bash
npm test
npm run typecheck
~~~

Production build, from root:

~~~bash
docker compose --profile automation build backend frontend scheduler source_scheduler
~~~

Host frontend builds may lack the macOS SWC native package. The Docker production
build is the supported build gate. Do not weaken .env exclusions to make a build
pass. Use Node 24 and the checked-in package-lock.json; do not upgrade dependencies
as a side effect of refactoring.

Documentation and repository static checks, from root:

~~~bash
python3 -m unittest scripts.test_check_docs scripts.test_check_secrets scripts.test_local_compose scripts.test_backup_workflow
python3 scripts/check_docs.py
python3 scripts/check_secrets.py
python3 scripts/validate_project_skills.py
bash scripts/test_workstream_ownership.sh
bash scripts/check_workstream_ownership.sh
git diff --check
~~~

If the system runtime is missing or sandbox-blocked, use an available approved
runtime or record the exact gate as not run. Never infer a clean Git status,
weaken checks, install developer tools or alter security settings merely to make
a documentation task pass. Read denied secret files through no alternate tool.

The maintained tooling image supports repository and fake-Docker recovery checks
without installing Git/Perl/Python on the host. Use an empty environment file to
prevent Compose from loading normal credentials:

~~~bash
docker compose --env-file /dev/null -f docker-compose.tools.yml build repo-checks
docker compose --env-file /dev/null -f docker-compose.tools.yml run --rm repo-checks
docker compose --env-file /dev/null -f docker-compose.tools.yml run --rm repo-checks python scripts/check_docs.py
~~~

The image build needs package-download access. Checks run network-disabled and
read-only; only /tmp is writable/executable because recovery fixtures generate a
fake Docker command there. No real Docker socket or database is mounted. Passing
these script tests does not prove a populated database restore or off-device recovery.

Knowledge-base changes additionally require its AGENTS.md workflow and:

~~~bash
python3 damodaran_knowledge_base_v1/tools/audit_kb.py
python3 -m unittest discover -s damodaran_knowledge_base_v1/tools -p 'test_audit_kb.py' -q
~~~

## Parallel workstream checks

[Knull](../Knull%28readme%29.md) owns the current batch. Its
[manifest](workstreams/ownership.tsv) reserves exact files/new trees; unlisted
paths are frozen. Validate the allocation without needing Git/Python/Docker:

~~~bash
bash scripts/test_workstream_ownership.sh
bash scripts/check_workstream_ownership.sh
~~~

Before handoff, use a separate worktree based on the coordinator's recorded
baseline. Replace the placeholder and owner below. Both tracked differences
(including deletions and both sides of renames) and untracked paths are checked:

~~~bash
(
  set -e
  KN_WORKSTREAM_BASE='<recorded-baseline-commit>'
  KN_WORKSTREAM_PATHS=$(mktemp)
  trap 'rm -f "$KN_WORKSTREAM_PATHS"' EXIT
  git -c core.quotePath=false diff --name-only --no-renames "$KN_WORKSTREAM_BASE" -- > "$KN_WORKSTREAM_PATHS"
  git -c core.quotePath=false ls-files --others --exclude-standard >> "$KN_WORKSTREAM_PATHS"
  bash scripts/check_workstream_ownership.sh --owner W1 --paths "$KN_WORKSTREAM_PATHS"
)
~~~

Any failed collection or ownership command stops that block. Do not omit
unassigned paths to obtain a pass. The guard consumes
literal relative paths, one per line; unusual quoted/newline names fail closed.
Ignored/generated files are not a permission loophole: use only isolated test
outputs, never normal data or another agent's build directories. In a shared dirty
checkout, have the coordinator attribute prior changes first; a full baseline diff
cannot distinguish authors. Prefer separate worktrees for this batch.

Each agent owns only its manifest paths and evidence tree. Contract changes,
central docs, test infrastructure and migrations use the plan's coordinator
procedure. A boundary failure does not authorize editing a neighbor's test.

Browser, release and restore-drill runners use fixed Compose project names.
Only the coordinator dispatches one such gate at a time; record the owner until
cleanup is confirmed. Different ports or worktrees do not prevent destructive
cross-run cleanup. Build shared images before parallel tests and avoid concurrent
replacement of image tags. Frontend build/test outputs need separate worktrees.

## Browser and release gates

Dependency security gate (package metadata only, not project data): run
`npm audit --audit-level=moderate` inside frontend and `pip-audit -r
backend/requirements-test.txt --progress-spinner off` from a disposable Python 3.14
audit environment. Do not install audit tooling into normal runtime containers.
CI runs both on pushes/PRs. Rebuild and run behavioral tests after changes;
clean advisory results are not a penetration test or a container OS scan.

From root, with local test credentials configured:

~~~bash
./scripts/run_browser_workflows.sh valuation-draft.spec.ts
./scripts/run_browser_workflows.sh daily-brief-runtime-smoke.spec.ts
./scripts/run_browser_workflows.sh portfolio-runtime-smoke.spec.ts
./scripts/verify_release_baseline.sh
~~~

These launch separate disposable projects. Read their cleanup targets before
running. Browser ports default to 13000/18000, not the normal 3000/8000 stack.
Fixture mutations send the signed-in page's Origin. A container browser base URL
must match the disposable frontend's NEXTAUTH_URL host and port. Keep the app's
host/Origin guards intact. If shared filesystem trace folders fail, write artifacts
inside the test container and copy completed results to output/playwright. Use
explicit disposable credentials and staged source; do not read protected env files.
The browser helper signs in once per worker and reuses cookies in fresh contexts;
it does not disable or raise the normal sign-in throttle. Seed a fresh disposable
database before each full run, because some workflow fixtures use fixed identities.
Use E2E_FRONTEND_PORT and E2E_BACKEND_PORT only when those ports are occupied.
Do not run two invocations against the same disposable project concurrently.
The browser script runs a production Next.js build with `npm run start` from
the builder image. Separately build the normal standalone production image.
Both Compose definitions bind published ports to 127.0.0.1. Check the actual
runtime bindings; previously created containers retain their old configuration.

The release script builds, migrates a fresh PostgreSQL database, checks readiness,
and runs backend/frontend/type/static checks. Backend unit tests use the separate
network-disabled test service with read-only reference files. Frontend source
guards receive a read-only repository through REPOSITORY_ROOT; these files stay
out of the normal frontend image. It is not the genuine-input
portfolio smoke. Screenshots and traces belong in output/playwright.

## Normal runtime operations

### Valuation source refresh

With user approval, set `VALUATION_REFRESH_ENABLED=true` and
`VALUATION_REFRESH_OWNER_ID` to the existing local user ID in ignored `.env`.
Never print credential values. The fixed schedule is weekdays 07:00
America/New_York; DST is handled automatically. The scope is active companies
with exchange/local-symbol identities, not arbitrary test catalog rows.

~~~bash
docker compose --profile automation up --build -d backend source_scheduler
docker compose --profile automation ps
docker compose logs --tail=50 source_scheduler
~~~

Manual refresh: open a company's valuation draft and choose **Fetch latest source
inputs**. It saves current edits, queues the job and polls progress. The worker
checks every 30 seconds. **Refresh Stored Inputs** performs no provider fetch.
Both paths preserve explicit edits and require review before model creation.
Source refreshes do not approve financial candidates or recalculate saved models.

The worker must stay running for manual queued jobs even if weekday automation
is disabled. A weekday startup after 07:00 runs that day's single due job; it does
not backfill older dates. A stopped/interrupted job is marked failed on the next
worker cycle and requires explicit retry. Provider failures and manual India
coverage appear in Data Health, not as fake success. Existing brief scheduling
remains separate.

### General runtime commands

These commands change the normal local runtime; use only within the requested
workflow. A code review or diagnosis alone does not authorize deploying changes.

~~~bash
docker compose up --build -d
docker compose ps
docker compose logs backend --tail=100
docker compose logs frontend --tail=100
curl --fail http://localhost:8000/api/health
curl --fail http://localhost:8000/api/readiness
~~~

Readiness checks DB/schema/migrations; liveness only proves a responding process.
If readiness fails, inspect returned blockers before changing the database.

~~~bash
docker compose exec backend alembic heads
docker compose exec backend alembic current
docker compose exec backend alembic upgrade head
~~~

Upgrade only an intact compatible migration chain. Never stamp/drop/reset data
to hide a missing revision. Never chmod a Docker socket to 666; inspect Desktop,
context and permissions instead.

Optional deterministic worker:

~~~bash
docker compose --profile automation up --build -d scheduler
docker compose logs scheduler --tail=100
docker compose stop scheduler
~~~

Scheduled briefs do not call external AI. Explicit AI refresh remains user-driven.
pgAdmin is optional via the admin profile. Normal Compose ports now specify
127.0.0.1. Existing containers need recreation to apply this, not just restart.
Do not recreate PostgreSQL without checking the persistent volume and backup;
never remove a database volume to change its port binding.

### Resource inspection and bounded cleanup

Measure after startup and again while idle. CPU can exceed 100% when a process
uses more than one core. Docker's memory limit is a ceiling, not memory consumed;
Desktop's VM can use additional memory outside these container measurements.

~~~bash
docker stats --no-stream
docker system df
docker compose ps --all
~~~

For occasional database administration, start pgAdmin explicitly and stop it
when finished. It has no automatic restart policy in the current configuration:

~~~bash
docker compose --profile admin up -d pgadmin
docker compose stop pgadmin
~~~

Inspect disk usage before a requested cleanup. A bounded build-cache cleanup,
which does not remove images, containers, volumes or database records, is:

~~~bash
docker builder prune --filter until=168h --keep-storage 5GB
docker system df
~~~

The command asks for confirmation. It targets old unused build cache and can
slow the next rebuild. It is not a persistent 5 GB quota: newer, shared or active
records can remain above that amount. Shared layers also mean Docker's categories
are not an exact sum of extra host disk use. See Docker's
[cache accounting](https://docs.docker.com/reference/cli/docker/buildx/du/) and
[garbage collection](https://docs.docker.com/build/cache/garbage-collection/) docs.
Do not treat an unattached volume or stopped image/container as disposable; it
can still hold data or a rollback image. Inventory those separately and obtain
exact-target authorization before deleting user data. No automatic pruning is set up.

## Data and operational tools

### US benchmark intake

The user-approved US-specific January 2026 sources have separate dated filenames.
This explicit, audited import does not fetch new versions or approve mappings:

~~~bash
docker compose exec -T backend python scripts/ingest_damodaran.py --market US
~~~

It supports beta_methods, wacc_methods, margin, capex, roe and working_capital.
Use `--only` to select these contracts. Repeating the same bytes is idempotent;
changed dates/populations require a separately registered source version. The
default `--market IN` retains the existing India workflow. Inspect coverage in
Data Health, then use **Refresh Stored Inputs** on an existing draft. New priors
remain review-required and do not alter saved models.

### Other tools

- backend/scripts/check_ai_provider.py is an explicit external Gemini check, not
  a deterministic test. It sends only the fixed prompt `Reply exactly OK.`, uses
  GEMINI_API_KEY/GEMINI_MODEL from the backend environment and persists a sanitized
  Processing Run with model, prompt version and input hash. No company, portfolio
  or research records are sent. After a deliberate local configuration change:

  ~~~bash
  docker compose up -d --no-deps backend
  docker compose exec -T backend python backend/scripts/check_ai_provider.py
  ~~~

  Rebuild the backend first if source changed. An optional `--model` probes an
  override without changing configuration; health only uses runs for the current
  configured model. Success proves connectivity, not AI output quality or quota.
- scripts/ingest_damodaran.py imports supported source contracts and writes data.
  Inspect its --only options; generic inventory is not typed application support.
- scripts/verify_milestone_a.py defaults to connectivity checks; --write creates
  records and can access providers. It is not a unit-test command.
- backend/scripts/check_portfolio_real_input_readiness.py is a read-only,
  owner-scoped preflight. It does not seed, refresh, capture snapshots or satisfy
  the manual browser gate.
- scripts/backup_local.sh and restore_local.sh own backup/restore. Inspect exact
  targets and get data-loss authorization before restore/reset/volume deletion.
  Table-count commands must not consume the surrounding manifest loop's input;
  the backup workflow tests reproduce this Docker behavior without accessing Docker.
  Restore checks the actual restored table inventory, not only tables listed in
  the manifest, and does not restart the app if legacy/incomplete counts differ.
  It stops running/restarting `scheduler` and `source_scheduler` writers before database
  replacement and resumes only those that were running after verification.
  Custom worker names use `DAILY_BRIEF_SERVICE` and `SOURCE_REFRESH_SERVICE`;
  set them to empty for a stack without those workers. Quiesce any other writers
  manually. Worker lifecycle regressions use fake Docker, not the normal database.
  Verify a backup by restoring to a separate disposable database and comparing
  every table plus original asset bytes before normal-runtime maintenance.
  Both `document_assets.content` and `brief_sources.pdf_bytes` are in the dump;
  the legacy manifest's asset summary counts only the former.
- Root legacy scripts are not maintained entry points unless explicitly verified.

## Completion and documentation

Report changed files, tests, manual checks, remaining risks and next work.
Distinguish source checks, image builds, isolated fixtures and genuine-input
evidence. Keep the full test count in [current state](00-current-state.md), precise
proof in archive/checkpoints/YYYY, and unresolved gaps in the
[single ledger](agent_capabilities_and_limitations.md).

Update the roadmap only when priorities change and the feature register only
when capability status changes. Replace the short handoff; do not append history.
