# Execution Runbook

Development and validation commands. Run from the repository root unless a
different directory is stated. [Local setup](local-development.md) owns first
installation; [Operations](operations.md) owns existing-stack, provider, credential,
and recovery commands. Historical results remain in [Current State](current-state.md).

## Start a change

Read [the handoff](HANDOFF.md), nearest AGENTS.md, the matching [code-map](code-map.md)
row and relevant current reference. Inspect status and actual owning code. State a
bounded plan, add tests where practical, preserve user changes, and report
verified scope. Use [local setup](local-development.md) for first-time login
and environment configuration. Never print secrets.

## Choose the right environment

The [Compose file guide](../docker/README.md) maps all six definitions. Only the
dev file extends the normal app; test, tools, E2E, and recovery run independently.

| Purpose | Environment |
|---|---|
| Normal application | docker-compose.yml, production images, persistent user database |
| Edited-source backend tests | docker-compose.test.yml, network disabled, disposable SQLite, read-only source/data mounts |
| Repository/recovery script tests | docker-compose.tools.yml, Git/shasum, network disabled, read-only source, executable temporary fixture scripts; no Docker socket |
| Hot-reload development | docker-compose.yml plus docker-compose.dev.yml |
| Browser/release verification | Separate disposable project using docker-compose.e2e.yml |
| Backup/restore rehearsal | Separate disposable database/backend using docker-compose.recovery.yml; follow [Operations](operations.md) |
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
The backend, frontend and PostgreSQL Dockerfiles freeze signed Debian security
packages to a dated snapshot. Advance all three snapshots together, retain signature
checking, fail incomplete updates, and rebuild all images before claiming fixes are
installed. PostgreSQL's build keeps its pinned version-16 binaries and excludes the
rolling PGDG repository from OS updates. Build it with the normal Compose project;
the browser and recovery projects use the same Dockerfile.
The backup verifier defaults to the immutable image ID of the selected running
database, so a moving local tag cannot silently choose a different build.
RECOVERY_POSTGRES_IMAGE remains an explicit override. Ambiguous database service
selection fails before a verifier starts.

Scan explicitly selected built runtime images, with Python 3 and Docker available:

~~~bash
bash scripts/scan_container_images.sh backend-image:tag frontend-image:tag postgres-image:tag
~~~

The pinned scanner receives only exported images, not the source directory or
Docker socket. Complete JSON package inventories stay in output/security/container-scan;
CI uploads them. Scanner databases and image exports share a temporary directory
that is removed on success or failure; JSON reports remain outside it. The gate
rejects missing OS inventories and available HIGH/CRITICAL
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
docker compose --env-file /dev/null -f docker-compose.test.yml build backend-tests
docker compose --env-file /dev/null -f docker-compose.test.yml run --rm backend-tests pytest -q -p no:cacheprovider backend/tests/test_schema_boundaries.py
docker compose --env-file /dev/null -f docker-compose.test.yml run --rm backend-tests
~~~

Replace the focused test path with the behavior being changed. Tests use their
isolated database fixtures, not normal portfolio rows. The default database is
also disposable SQLite inside the container; PostgreSQL-specific browser/migration
checks require the separate disposable runtime below. Inspect test setup before
running an unfamiliar manual script. Do not collect root debug scripts as tests.
The explicit empty environment file prevents Compose from reading the root .env
for these isolated definitions. It does not authorize reading protected files or
substituting empty settings into the normal runtime.

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

Production builds, from root. Replace the example tag with an unused release tag;
keep currently installed and rollback tags intact:

~~~bash
release_tag=review-YYYYMMDD-N
docker build -f backend/Dockerfile -t "market-intelligence-backend:$release_tag" .
docker build -t "market-intelligence-frontend:$release_tag" frontend
docker build -t "market-intelligence-postgres:$release_tag" docker/postgres
~~~

After validation, a new deployment selects these reviewed images in its runtime
override. Restarting the installed stack does not deploy changed source files.

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

The [workstream design](workstreams/plan.md) retains the batch design. Its
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

Browser, release and recovery runners allocate unique owned Compose projects.
Browser/release runners reject existing containers, networks or volumes before
startup and recheck after builds. Cleanup is enabled only when their own creation
begins; preflight failures never delete a pre-existing project. Release unit tests
also get a separate project. Failure and interrupt exit codes remain visible.
The coordinator still serializes shared image builds and reserves free default
ports, or supplies explicit overrides. Unique projects do not isolate shared image
tags or occupied host ports. Frontend build/test outputs need separate worktrees.
Before installing an image, give it a unique release tag and verify that tag resolves
to the recorded image ID. Never rebuild or retag a release name used by a running
or retained rollback container. With Docker's containerd image store, replacing the
last tag can make an intermediate image ID unresolvable even while its container
snapshot still starts. Preserve that intact container; do not delete it while
attempting to recover image metadata. Preflight the new tagged image before stopping
the old service, then verify settings, localhost ports and data after replacement.

## Browser and release gates

Dependency security gate (package metadata only, not project data): run
`npm audit --audit-level=moderate` inside frontend and `pip-audit -r
backend/requirements-test.txt --progress-spinner off` from a disposable Python 3.14
audit environment. Do not install audit tooling into normal runtime containers.
CI runs both on pushes/PRs. Rebuild and run behavioral tests after changes;
clean advisory results are not a penetration test or a container OS scan.

From root, with frontend test dependencies installed:

~~~bash
./scripts/run_browser_workflows.sh valuation-draft.spec.ts
./scripts/run_browser_workflows.sh daily-brief-runtime-smoke.spec.ts
./scripts/run_browser_workflows.sh portfolio-runtime-smoke.spec.ts
./scripts/run_browser_workflows.sh accessibility-responsive.spec.ts route-details.spec.ts
./scripts/verify_release_baseline.sh
~~~

These launch separate disposable projects. Read their cleanup targets before
running. Browser ports default to 13000/18000, not the normal 3000/8000 stack.
The browser runner supplies disposable authentication defaults; explicitly exported
test credentials override them. Compose uses `/dev/null` as its environment file,
and Playwright never loads the repository's private settings. Direct Playwright
invocations must receive their test credentials through the process environment;
their default target is also port 13000. The runner checks occupied ports before
cleanup and uses only the installed Playwright package, without downloading one.
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

## Completion and documentation

Report changed files, tests, manual checks, remaining risks and next work.
Distinguish source checks, image builds, isolated fixtures and genuine-input
evidence. Keep the full test count in [current state](current-state.md), precise
proof in archive/checkpoints/YYYY, and unresolved gaps in the
[single ledger](limitations.md).

Update the roadmap only when priorities change and the feature register only
when capability status changes. Replace the short handoff; do not append history.

CI starts on pull requests, pushes to the default branch codex/worktree-recovery,
and all tags. Feature branches run when a pull request opens, avoiding duplicate
branch-push builds. Keep the branch filter aligned if the default branch changes.

The repository-checks job always runs documentation, credential-pattern,
dependency-lock, ownership, and tooling checks. It compares the entire event
range, including every commit in a push and both paths of a rename. Recognized
Markdown-only changes skip the five expensive application, browser, dependency,
container, and recovery jobs. Unknown paths, unavailable comparisons, empty
comparisons, workflow/configuration changes, and tags require all five.

The final ci-result job must pass. It rejects failed/cancelled/missing checks and
unexpected skips. If configuring branch protection, require ci-result so an
intentional documentation-only skip is not confused with an incomplete build.
The selector and result gate are tested with:
`python3 -m unittest scripts.test_ci_scope`.
Scanner lifecycle fixtures use
`python3 -m unittest scripts.test_scan_container_workflow`.
These tests need Python and Git, but no Docker, credentials, or network.

Upstream package-download failures remain failures and may be retried without
changing pins.

Image-build APT commands use 30-second HTTP/HTTPS connection/data timeouts.
The frontend disables HTTP retries until APT 2.6.2 is installed; PostgreSQL checks
APT 3.0.4 before bootstrapping certificates. Signed-package checks remain enabled,
then sources switch to HTTPS. Patched APT and existing HTTPS paths retain three
per-file retries. This addresses [CVE-2026-109518](https://security-tracker.debian.org/tracker/CVE-2026-109518).
The November 7 snapshot also supplies the available trixie zlib fixes. These are
not whole-build deadlines; CI job limits remain. See [Debian's transport timeout definition](https://manpages.debian.org/trixie/apt/apt-transport-http.1.en.html).
