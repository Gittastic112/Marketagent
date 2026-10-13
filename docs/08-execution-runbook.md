# Execution Runbook

Updated: 2026-10-12. This document owns commands, not historical phase records.
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
Compose explicitly select the test target. Supported Linux/Python 3.14 environments
install backend/requirements-test.lock with `--require-hashes`; requirements.lock
is runtime-only. The `.txt` files declare direct dependencies; Docker installs locks.

## Dependency and container updates

Edit direct requirements intentionally, then regenerate locks with Python 3.14,
pip 25.3 and pip-tools 7.5.2 in a disposable environment. Existing locks preserve
versions unless the requested change requires one; review every version/hash diff.
From backend:

~~~bash
pip-compile --generate-hashes --strip-extras --no-emit-index-url --no-emit-trusted-host --no-header --no-annotate -o requirements.lock requirements.txt
pip-compile --generate-hashes --strip-extras --no-emit-index-url --no-emit-trusted-host --no-header --no-annotate -c requirements.lock -o requirements-test.lock requirements-test.txt
~~~

From the root, run `python3 scripts/check_dependency_locks.py`, the backend suite,
dependency audits and affected browser workflows. Frontend uses `npm ci` with its
existing lockfile. CI action SHAs and Python/Node/PostgreSQL image digests are pinned;
review updated official references rather than replacing them with floating tags.
The Dockerfiles also freeze signed Debian security packages to a dated snapshot.
Advance both snapshots together, retain signature checking, fail incomplete updates,
and rebuild both images before claiming the fixes are installed.

Scan explicitly selected built runtime images, with Python 3 and Docker available:

~~~bash
bash scripts/scan_container_images.sh backend-image:tag frontend-image:tag postgres-image:tag
~~~

The pinned scanner receives only exported images, not the source directory or
Docker socket. Complete JSON package inventories stay in output/security/container-scan;
CI uploads them. The gate rejects missing OS inventories and available HIGH/CRITICAL
fixes. Unfixed findings remain visible and require review, including vendor severity
differences. The optional stopped admin image and host Docker are separate checks.

Before normal rollout, keep the current application/PostgreSQL image IDs as rollback
tags and obtain a verified database backup. Rehearse migration/restore on a disposable
database with the selected PostgreSQL major version. Recreate only intended services,
preserving the stopped source worker and persistent volumes; verify readiness, browser
behavior and idle use. Also verify `docker compose ps --all` and ordinary backup
commands select the actual current containers. Compose discovery requires its
configuration label; a healthy manually created container alone is insufficient.
Keep rollback containers outside active Compose registration to avoid ambiguous
service selection. Preserve rollback images and persistent volumes.
Application rollback selects the retained image. Database
rollback must respect migration and PostgreSQL compatibility; never attach a data
directory to an older incompatible major or overwrite normal data for a test.

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

The browser runner also executes `backend/tests/integration/test_ingestion_postgres.py`
against its disposable PostgreSQL database. It proves row/advisory locking that
SQLite cannot exercise. The test requires `INGESTION_TEST_DATABASE_URL`, rejects
database names without the `_e2e` suffix, and allocates/removes only its own random
schema. Four checks cover ingestion locks, review writers and competing saved
valuation versions. The default offline backend suite skips them; a skip is not
concurrency proof. Never point this variable at the normal database.

Critical frontend/backend contracts are checked in both suites. For an intentional
wire change, regenerate the manifest using the backend dependencies, review its
diff, then run both suites. The normal check never rewrites the manifest:

~~~bash
PYTHONPATH=backend python3 scripts/check_api_contracts.py
PYTHONPATH=backend python3 scripts/check_api_contracts.py --write
~~~

The maintained coverage list lives in that script. Retired one-off recipes and
their local preservation inventory live under scripts/retired; they are excluded
from Git/Docker runtime inputs and must not be used as operational commands.

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
python3 -m unittest scripts.test_check_docs scripts.test_check_secrets scripts.test_local_compose scripts.test_backup_workflow scripts.test_recovery_metadata scripts.test_dependency_locks scripts.test_container_scan
python3 scripts/check_dependency_locks.py
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

Browser and release runners use fixed Compose project names; recovery allocates a unique project.
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
./scripts/run_browser_workflows.sh accessibility-responsive.spec.ts route-details.spec.ts
./scripts/verify_release_baseline.sh
~~~

These launch separate disposable projects. Read their cleanup targets before
running. Browser ports default to 13000/18000, not the normal 3000/8000 stack.
Fixture mutations send the signed-in page's Origin. A container browser base URL
must match the disposable frontend's NEXTAUTH_URL host and port. Keep the app's
host/Origin guards intact. If shared filesystem trace folders fail, write artifacts
inside the test container and copy completed results to output/playwright. Use
explicit disposable credentials and staged source; do not read protected env files.
On macOS, source bindings and artifact writes can also add validation overhead.
Use a backend image built from the verified source, copy the browser tests into
the runner, and export artifacts after execution. Record the image/source identity
and retain earlier failures; this does not justify increasing route time budgets.
The browser helper signs in once per worker and reuses cookies in fresh contexts;
it does not disable or raise the normal sign-in throttle. Seed a fresh disposable
database before each full run, because some workflow fixtures use fixed identities.
Use E2E_FRONTEND_PORT and E2E_BACKEND_PORT only when those ports are occupied.
Do not run two invocations against the same disposable project concurrently.
The browser script runs a production Next.js build with `npm run start` from
the builder image. Separately build the normal standalone production image.
Both Compose definitions bind published ports to 127.0.0.1. Check the actual
runtime bindings; previously created containers retain their old configuration.

The page matrix covers 50 routes at 1440px and 390px. It saves screenshots and
route-measurements.json under each test's output directory, including failures.
CI retains passing and failing browser evidence for seven days. This is rendered
page/selected-workflow proof, not every control/state or cold-start/load certification.
On small Docker VMs, finish image builds before backend PDF tests or browser runs;
resource-limit failures remain failures, and must pass a serial rerun without
raising the parser or route budgets.

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
  Format 3 verifies the completed dump in a network-disabled, bounded scratch
  PostgreSQL 16 container; normal writes can continue. Its manifest contains all
  public table counts/content fingerprints and both PDF stores' byte hashes.
  Scratch readiness requires a successful TCP query to its `proof` database,
  with bounded connection/retry waits; socket readiness during initialization
  alone does not authorize restore. Startup failure retains an incomplete folder.
  Paths, complete checksums, format and inventory are checked before replacement.
  A format-3 backup becomes complete only when its atomic `COMPLETE` file matches
  the manifest hash. Payload/checksum files are flushed before publishing that
  marker; finalization does not rename the containing directory. This works with
  the observed macOS managed-workspace directory-rename restriction. No broad
  filesystem permission change is needed. This is not a power-loss guarantee.
  Restore rejects missing, changed or linked markers before touching the database.
  Existing verified format-2 folders remain readable. Restore refuses `.partial`
  or linked folders; format 1 needs explicit
  `RESTORE_ALLOW_LEGACY=true` and provides only count-based verification.
  It stops running/restarting `scheduler` and `source_scheduler` writers before database
  replacement and resumes only those that were running after verification.
  Custom worker names use `DAILY_BRIEF_SERVICE` and `SOURCE_REFRESH_SERVICE`;
  set them to empty for a stack without those workers. Quiesce any other writers
  manually. Worker lifecycle regressions use fake Docker, not the normal database.
  Verify a backup by restoring to a separate disposable database and comparing
  every table plus original asset bytes before normal-runtime maintenance.
  Run `bash scripts/drill_backup_restore.sh` for the isolated concurrent-write
  and original-byte drill. It builds `docker-compose.recovery.yml`, publishes no
  ports, checks the actual tmpfs data directory and never adopts an existing project.
  Fake-Docker and metadata tests cover corruption, failures, interruptions and
  worker state. PostgreSQL 16 is the supported fingerprint basis.
  `BACKUP_ROOT` selects a local folder. Directories/files use 0700/0600. Failed
  backups retain a folder without a valid `COMPLETE` marker for inspection. Old
  `.partial` backups remain incomplete. Retention
  defaults off; `BACKUP_PRUNE=true BACKUP_RETENTION_COUNT=7` deletes only older
  verified format-2/3 folders owned by this script. It preserves invalid, unrelated,
  legacy and linked folders. Never remove the only verified recovery copy.
  The metadata helper uses host Python when available; set
  `RECOVERY_PYTHON_IMAGE=market-intelligence-tools:local` after building the tools
  target to use bounded, network-disabled Docker instead. `DOCKER_BIN` accepts
  the Docker executable path; `COMPOSE_ENV_FILE=/dev/null` is mandatory for agent
  drills. Operator restores must supply the same reviewed Compose environment
  as the normal app, without printing or sharing its values.
  Off-device procedure: choose an encrypted removable/off-device destination,
  copy one complete verified folder, keep recovery keys/environment separately,
  then restore the retrieved copy into the disposable environment and compare
  every table/PDF hash. A same-disk folder or cloud sync alone is not that proof.
  No transfer, credential rotation, pruning or scheduled job is performed by default.
- Root legacy scripts are not maintained entry points unless explicitly verified.

## Completion and documentation

Report changed files, tests, manual checks, remaining risks and next work.
Distinguish source checks, image builds, isolated fixtures and genuine-input
evidence. Keep the full test count in [current state](00-current-state.md), precise
proof in archive/checkpoints/YYYY, and unresolved gaps in the
[single ledger](agent_capabilities_and_limitations.md).

Update the roadmap only when priorities change and the feature register only
when capability status changes. Replace the short handoff; do not append history.
