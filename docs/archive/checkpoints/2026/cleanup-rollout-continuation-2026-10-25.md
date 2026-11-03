# Cleanup and local rollout continuation, October 25, 2026

This continues the [filesystem reorganization](filesystem-reorganization-2026-10-25.md)
and [Data Health source cleanup](structure-and-health-2026-10-25.md). Local rollout
was authorized, but no normal service was replaced. October 24 remains the latest
installed UI and completed desktop/mobile application evidence.

## Access and preservation

System Git/Python require unavailable Apple developer tools. The bundled host
executables return Operation not permitted, including narrow escalated attempts.
The explicit Docker Desktop executable reaches the existing socket and reports
engine 29.7.2. A task-only Docker configuration avoids the inaccessible personal
Docker configuration. The retained offline tooling image provides Git 2.47.3 and
Python 3.14.6 without installing host tools or changing security settings.

Read-only Git status, with protected environment paths excluded and optional index
writes disabled, records 937 paths: 358 modified, six deleted and 573 untracked.
The three indexed relocated scripts remain deletions in the shared checkout and
are preserved at their manifest destinations. Nothing was staged or reset.

Both registry.npmjs.org and snapshot.debian.org are explicitly rejected because
they are absent from the active network allowlist, including narrow escalated
requests. The project permission configuration is unchanged. Protected environment
files were not read, including through Compose, application settings or browser
configuration. Package manifests, the lockfile and Git index retain their initial
SHA-256 hashes.

## Package restoration and dependency boundary

The retained local browser image contains the original npm cache archives for
@axe-core/playwright and axe-core 4.13.0. Both archives exactly match the lockfile's
SHA-512 integrity values. Their package names, versions and archive paths were
verified before installing only those two absent package directories. No network
download, version declaration change or lockfile rewrite was performed.

A subsequent required-package comparison found pre-existing installed-tree drift:

| Package | Locked | Installed |
|---|---|---|
| @next/env | 16.4.1 | 16.2.11 |
| @swc/helpers | 0.5.23 | 0.5.15 |
| baseline-browser-mapping | 2.11.26 | 2.10.32 |
| nanoid | 3.3.19 | 3.3.16 |
| next | 16.4.1 | 16.2.11 |
| source-map-js | 1.2.2 | 1.2.1 |

The comparison covers required packages; it does not certify optional native
packages. These additional packages were not altered. The frontend results below
apply to the existing installed tree with the two restored axe packages, not a
fresh installation of the full lockfile.

## Validation performed

- Edited-source backend: 1,766 passed, six opt-in PostgreSQL checks skipped and
  five dependency deprecation warnings. The retained test image's runtime/test
  lock hashes exactly match current source. Tests use network-disabled containers,
  read-only source/data mounts and isolated SQLite fixtures, without normal settings.
- Frontend: all 319 tests pass. The host runner first failed to spawn subprocesses;
  the standard npm test command then passed in the retained Node 24 image against
  the read-only edited source and installed dependencies. Full TypeScript exits zero.
- Repository tests: 57 pass, including documentation, secret fixtures, Compose,
  backup/recovery, dependency locks, container-scan fixtures and retired-evaluator checks.
- Canonical documentation check: 112 active Markdown files and 909 local links
  pass before this evidence update. Final documentation results are retained separately.
- Dependency lock consistency: 66 runtime and 70 test packages. Project skill
  checks, ten ownership test cases, ownership validation and Git diff formatting pass.
- All 22 maintained frontend/backend wire contracts match their reviewed manifest.
- Source secret scan passes with protected environment paths excluded before any
  content reads. It does not certify the excluded files.
- Public backend readiness reports ready, with schema/head s1s1s1s1s1s1 and no
  missing tables, columns or constraints. This checks the previously installed app.
  Sign-in readiness reports configured local-single-user mode and explicitly
  reports production_ready=false. All six service identities, images, states and
  localhost bindings match the initial inspection.

Both production builds were attempted from a 998-file, 6,069,518-byte staged
source manifest excluding protected files. Build steps had networking disabled to
respect the active download boundary. Both stop at the uncached, dated Debian
security-update stage because snapshot.debian.org cannot resolve in that offline
build. A separate access probe confirms that the active policy also denies that
domain. The first backend command lacked the Docker build plugin; the task-only
configuration was corrected and its subsequent build failure is retained separately.

No successful production build, fresh dependency-security audit, separate
PostgreSQL integration run or full release/browser gate is claimed. A new browser
tab reached the installed sign-in screen only. It is not Data Health verification.

## Relocations and normal services

All 41 destinations still match their original or explicitly documented post-edit
hashes. All original file paths are absent; the intentionally edited quick-start's
original copy also matches. The manifest preserves 295,277 original bytes.

All 16 original directory shells contain no files. Children were checked before
parents. Ordinary removal and the subsequent exact non-recursive escalated rmdir
request both return Operation not permitted. No directory was removed and no file
byte savings are claimed. No Docker or alternate filesystem route was used to
override that restriction.

The inspected normal services retain their existing images and storage:
PostgreSQL, backend, frontend and Daily Brief are running; source refresh and
pgAdmin are stopped. Published ports are bound to 127.0.0.1. No worker state,
persistent volume, normal setting or rollback image was changed.

The retained October 24 pre-review backup still has 128,252,312 bytes and its
recorded SHA-256. A fresh pg_restore --list succeeds without restoring or writing
database data. This verifies that retained archive, not a current-state backup or
a new recovery rehearsal. A fresh quiesced backup remains necessary before rollout.

## Evidence and remaining work

Logs, preservation hashes, package integrity receipts, dependency comparison,
relocation verification and runtime metadata are retained under
output/milestones/cleanup-rollout-continuation-20261025. The protected-file-free
build staging, recovered package archives and before copies also remain under
/private/tmp/mi-cleanup-rollout-20261025-continuation. Earlier failed evidence,
backups and source reports are preserved.

Completion requires scoped package/signed-OS download access and permission to
remove the manifest's exact empty directories. Reconcile the installed dependency
tree to the unchanged lockfile, then rerun frontend validation and complete the
production, integration and browser gates. Inspect services again, retain rollback
images and a current verified backup, replace only affected local services, preserve
worker states and localhost bindings, and verify Data Health on desktop/mobile.
Do not treat this partial continuation as a completed rollout.
