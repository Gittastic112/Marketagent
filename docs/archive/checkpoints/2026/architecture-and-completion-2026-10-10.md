# Architecture, Docker and completion audit

Date: October 10, 2026, America/New_York. Scope: requested repository/runtime
cleanup, resource diagnosis, ten-step completion plan and a portable recovery-test
environment. This is not a completed product, finance-method change or normal app rollout.

## Findings and measurements

The screenshot shows 203.9% CPU out of eight cores' 800%, approximately 2.04 cores
or 25.5% of that CPU capacity. Its 645 MB memory reading is not excessive for
this stack. It does not show disk consumption or prove sustained idle load.
Live containers had just started around 14:49 EDT, with no repeated restarts.
Subsequent idle samples support a startup-transient explanation, not a proven
infinite loop: backend 0.31/0.53% and pgAdmin 0.05/0.06%. One frontend sample was
7.10%, so these are point measurements, not a load/performance guarantee.

| Resource | Before cleanup | After cleanup and verification builds |
|---|---|---|
| Images | 47, 18.93 GB | 50, 19.67 GB; three intentional validation/tooling images added |
| Build cache | 598 records, 30.75 GB; 21.24 GB reclaimable | 392 records, 19.8 GB; 10.29 GB reclaimable |
| Local volumes | 18, 3.108 GB | 18, 3.108 GB; none pruned |
| Normal containers | Six present, five running | Six present, four running; pgAdmin stopped |
| Frontend generated cache | About 1 GiB | Zero data by du; protected empty directories remain |

Docker reported **11.69 GB reclaimed** by removing unused build cache older than
seven days with 5 GB retention. New verification builds then used some cache.
This was a cache-only prune, not image/container/volume pruning. Docker layer
categories overlap, and freed Docker space is not a measured increase in the
Mac's physical free-space counter. It is not a permanent 5 GB storage cap.
See [Docker cache accounting](https://docs.docker.com/reference/cli/docker/buildx/du/)
and [pruning](https://docs.docker.com/reference/cli/docker/system/prune/).

Final idle sample: frontend 0.01% / 122.8 MiB, backend 0.31% / 185.4 MiB,
Daily Brief worker 0.01% / 85.18 MiB, PostgreSQL 0% / 49.27 MiB. About 443 MiB
of container memory in total; Docker Desktop VM overhead is additional.
pgAdmin previously used about 275 MiB and is now stopped with restart=no.
All published normal ports observed remain bound to 127.0.0.1. The source worker
was already stopped and was not enabled or used to fetch provider data.

## Implemented changes

- Backend Docker builds use maintained-source allowlisting; unrelated corpus,
  datasets, local environments, environment files and caches stay outside context.
  The tested context transferred 3.43 MB. Default runtime copies app/migrations/
  operational scripts; the test target adds pytest and backend fixtures. A separate
  requirements-test.txt includes runtime requirements plus the existing pytest pin.
- Only backend startup runs migrations. Both normal workers depend on healthy
  backend readiness and start their worker directly, avoiding competing startup DDL.
- Development watches backend/app, keeps runtime data read-only and gives the
  frontend 2 GiB for its configured 1.5 GiB heap. Normal frontend remains 1 GiB.
- pgAdmin remains an optional admin profile, gains a 512 MiB source limit, and
  no longer restarts automatically. Its running instance was stopped and its
  restart policy changed; its new memory limit awaits container recreation.
- The tools image adds Git and Perl/shasum, with a maintained tools Compose file.
  Checks run without network, with read-only source and an executable temporary
  fixture directory. No Docker socket, normal database or real credentials are
  provided. The user explicitly requested this environment after the first
  recovery-test attempt found missing tooling in the slim test image.
- CI dependency auditing now includes the test manifest and its runtime include.
  This does not hash-lock transitive dependencies or constitute a new advisory scan.
- The existing frontend build-exclusion guard now recognizes the stricter context
  allowlist. Five additional infrastructure regressions cover startup ownership,
  optional administration, development scope, dependency separation and exclusions.
- The completion tracker contains ten cumulative acceptance gates and 70 stable
  task IDs, mapped to the existing five Knull designs. Current docs route percentage
  requests there. No agents, background schedule or public deployment were launched.

## Verification

| Check | Result and scope |
|---|---|
| Baseline documentation/localhost checks | 14 passed before implementation |
| New infrastructure regression demonstration | Expected failures on old settings, then 19 documentation/Compose checks passed |
| Backend focused checks | 25 passed: schema boundaries, brief schedule, source refresh and readiness |
| Full backend | 1,294 passed, five upstream deprecation warnings; edited source, no network, disposable SQLite |
| Frontend | 234 passed; one existing exclusion assertion updated for the new allowlist. Initial incomplete mount failures were test setup, not product behavior |
| TypeScript | Passed with Node 24, read-only sources, incremental output disabled |
| Repository/recovery tests | 28 passed in tools Compose: docs, secret-scanner fixtures, Compose and seven fake-Docker recovery tests |
| Build targets | Runtime, test and tools built successfully using a staged copy of allowlisted source. Root-context build was blocked on environment-file metadata, so no protected file was copied or read |
| Runtime isolation | Application and both workers import; UID 10001; pytest and backend test fixtures absent; source head s1s1s1s1s1s1 |
| Fresh PostgreSQL startup | Disposable tmpfs database migrated to s1s1s1s1s1s1; backend ready; both direct workers running. Internal network, no published ports/provider work. Entire disposable stack removed afterward |
| Normal runtime | Read-only current/head both s1s1s1s1s1s1; existing web/backend/database healthy and localhost-only. No normal app/worker replacement or data migration |
| Git whitespace | Passed with protected environment paths excluded; one pre-existing corpus CSV line-ending warning, no corpus edit |
| Documentation/workflows | 78 active Markdown files and 643 local links pass; 12 project workflow skills validated; ownership guard passes 10 cases and 90 disjoint reservations |
| Tracker structure | 70 unique task IDs, exactly seven per milestone, ordered across ten milestones |

The first recovery test run could not execute temporary fake-Docker scripts and
lacked shasum. The dedicated tools target plus executable tmpfs resolved these
environment issues without changing backup/restore behavior or weakening tests.
Fake-Docker checks and fresh empty-database startup do not prove populated backup
consistency, private asset restoration or off-device recovery. W5/M03 still owns them.

No new browser run, frontend production build, genuine financial/portfolio source
certification or provider/AI request was performed. Normal app/worker containers
still use their preceding images/commands. Rebuild validation is not rollout proof.

## Preservation and change boundary

Host Git/Python/Perl and bundled Git/Python were unavailable or blocked. The tools
container enabled read-only Git inspection without installing host tools. Branch:
codex/worktree-recovery. HEAD: fba390bf4d22146229cfabd2d621b8ebd9975fe2.
One captured scoped status listed 268 modified and 320 untracked files, including
this work; this is not an attribution of all those changes to this task. Protected
environment paths were explicitly excluded. No reset, clean, broad staging, commit,
history rewrite or source deletion was performed.

A private source-only snapshot and Git inventory are retained under ignored
backups/source-baseline-20261010, with 0600 archive permissions. It captures the
current app/tooling source and planning state, not environment files, generated
dependencies, datasets, private database records or immutable corpus originals.
Archive SHA-256: f640aadf40c7c9837a17fe3a4213f7bcba33fd353b5ed8b2bd0f70113a66d3dc.
Archive member checks found no environment files or node_modules/.next content.
It predates the final audit/status edits and is not a database/off-device backup
or a committed common baseline for parallel worktrees.

Task-edited implementation paths: .dockerignore, .github/workflows/ci.yml,
backend/Dockerfile, backend/requirements.txt, new backend/requirements-test.txt,
docker-compose.yml, docker-compose.dev.yml, docker-compose.test.yml,
docker-compose.e2e.yml, new docker-compose.tools.yml, scripts/test_local_compose.py,
and frontend/lib/frontend-integrity.test.ts. Other application source changes in
Git were preserved. Documentation changes update the existing README, Knull,
handoff, architecture, code map, setup/runbook, ledger and roadmap owners, with
one new tracker, this checkpoint and an archived preceding handoff.

Large remaining owners include legacy schemas (2,425 lines), peer review (1,769),
benchmark ingestion (1,459), autofill (1,246), and server actions (1,188).
M02 sequences behavior-preserving extraction and root-script classification.
Renaming untracked legacy scripts without knowing their callers would not fix
these boundaries. The requested full architecture cleanup remains tracked, not
falsely declared complete by this initial runtime/build improvement.
