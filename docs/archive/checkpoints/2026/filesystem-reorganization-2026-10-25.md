# Mac project-folder reorganization, October 25, 2026

The later [cleanup/rollout continuation](cleanup-rollout-continuation-2026-10-25.md)
records restored axe packages, working Docker/container tools and the remaining
build, dependency-tree and empty-directory restrictions.

The user explicitly requested full validation, local rollout and actual Mac folder
cleanup, then directed completion of available non-Docker work with a prompt for
the remaining work. This checkpoint follows the
[Data Health source cleanup](structure-and-health-2026-10-25.md).

## Physical file moves

The [manifest](../../../../scripts/retired/inventory-2026-10-25.json) records 41
files, 295,277 preserved bytes, original/destination paths, Git-index membership
and SHA-256 checksums. No file contents were deleted and no disk savings are
claimed. Source, review receipts, databases containing records, backups and the
immutable knowledge corpus were not removed.

- Seven backend-root one-off scripts moved to scripts/retired/local/2026-10-25/backend
  with inactive .txt extensions. Searches found no current callers. Configured
  pytest discovery uses backend/tests, not those ad-hoc scripts.
- The zero-byte backend/test.db moved into the same local archive as test.db.empty.
- The old backend/error.log moved to output/legacy-backend/2026-10-25/error.log.
- All 32 files in the root spreadsheets and excel-live-control packages moved
  under skills, preserving their internal directory structure. Session-installed
  plugin locations were not changed.
- Two local documentation references in the spreadsheet quick-start were then
  corrected to sibling Markdown links. The manifest records the intentional
  post-move hash change; its original copy is retained in the task's before folder.

The first move attempt rolled all files back after empty-directory removal failed.
The second attempt moved and verified every file without attempting to remove
directories. The 16 empty original directory shells are listed in the manifest.
Both ordinary and explicitly escalated directory-removal requests were denied.
All 16 trees contain zero remaining files; the two parent directories still hold
their empty children. Remove only those exact directories, children first, after
confirming they are empty in a session that permits cleanup. No recursive
deletion is needed.

The root README, code map, local helper index and retired-tooling guide now describe
the actual layout. Runtime entry points, Compose locations, migration paths and
protected environment files retain their established locations.

## Access and validation boundary

The checked-in execution profile currently permits only localhost and 127.0.0.1
network destinations. Requests to restore the exact locked npm packages still
fail because registry.npmjs.org is absent from the network allowlist. Git is denied
and the existing Python executable cannot load its restricted framework library.
The expected Docker socket is inaccessible to this chat. The user reports Docker
is running; this session cannot determine its actual state from these failures.
Launching Docker from this execution context also failed. These results do not
justify reinstalling Docker, deleting volumes or changing system permissions broadly.

No permission profile, credential file, dependency version or installed service
was changed. The prior source-test results remain separately scoped. The latest
non-Docker verification is recorded in Current State and the limitation ledger;
full Python checks, production builds and live-browser verification are pending.

Final non-Docker checks after relocation:

- All 319 frontend tests pass with zero failures or skips, including the ten
  Data Health regressions from the source cleanup.
- All 41 destinations match their recorded original or documented post-edit
  SHA-256 hashes; every original file path is absent. The one edited Markdown
  file also has a preserved original matching its original hash.
- A bounded Node fallback checks 42 Markdown files and 465 local link targets
  with no failures. Two protected environment-template targets are excluded.
  All five instruction/current-context line budgets pass. This does not replace
  the canonical documentation checker or its route/schema consistency checks.
- Both python3 scripts/check_docs.py and the documentation/Compose unittest
  command fail before execution because the host developer-tool Python is
  unavailable. The previously documented full type-check blocker is unchanged;
  no TypeScript files changed during this physical reorganization.

Task-local before copies and logs are retained under
/private/tmp/mi-structure-rollout-20261025. The earlier source-change inventory and
tests remain under /private/tmp/mi-structure-20261025. These folders are evidence,
not application runtime inputs.

## Continue in a working local execution environment

1. Read the handoff, limitation ledger, both October 25 checkpoints and relocation
   manifest. Preserve the dirty checkout/index and every untracked file.
2. Verify scoped access to npm, an approved Git/Python toolchain and the existing
   Docker Desktop socket. Keep protected environment-file denies in force. Do not
   infer new permissions from prior chat approval alone.
3. Restore @axe-core/playwright and axe-core at locked version 4.13.0, verify their
   integrity and leave manifests/locks unchanged. Finish the full runbook checks
   using edited source. Keep normal data separate from isolated test fixtures.
4. Verify the empty-directory list before removing only empty shells. Recheck
   relocated-file hashes and full Git status, including the three indexed scripts
   now preserved in the local archive. Do not stage the whole checkout.
5. Before local rollout, inspect current services, image IDs, localhost bindings,
   persistent volumes and worker states. Preserve rollback images and a verified
   backup. Rebuild and replace only the affected services using existing settings
   without opening protected environment files or printing secrets.
6. Check readiness and the Data Health failure, empty, populated and explicit-audit
   workflows on desktop/mobile. Preserve database and source-asset fingerprints.
   Keep source refresh and pgAdmin stopped if that is their observed prior state.
   Do not seed normal data, reset volumes, publish publicly or broaden ports.
7. Update current evidence only after each gate actually passes. If access remains
   blocked, report the exact failure and required narrow permission change.
