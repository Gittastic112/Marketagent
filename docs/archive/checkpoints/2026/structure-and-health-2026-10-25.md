# Structure and Data Health cleanup, October 25, 2026

Source-only work requested to improve organization, remove redundancy and correct
inefficient or misleading behavior. Current validation constraints live in the
[limitation ledger](../../../agent_capabilities_and_limitations.md); installed
runtime evidence retains its earlier date.

## Audit and preservation

The bounded inventory covered 639 maintained source/test files under frontend/app,
frontend/components, frontend/lib, backend/app and scripts. It found no identical
nontrivial files. Existing routes and domain API modules were below their size
budgets. Moving every directory would not establish a runtime speed improvement.

System Git could not run; the bundled Git executable was restricted. A read-only
comparison against the version-2 index found 222 changed and 224 untracked files
within that inventory. This is not a complete Git status or staged/HEAD comparison.
Exact pre-edit copies and SHA-256 hashes of changed existing files are retained
under /private/tmp/mi-structure-20261025/before and before-sha256.json.

No source, database, review evidence, backups or generated artifacts were deleted.
Removed paths: none. Actual reclaimed disk bytes: zero. Git/index and lockfiles
were not changed. No backend calculations, routes, schema or persisted data changed.

## Ownership and behavior

| Owner | Responsibility |
|---|---|
| frontend/lib/server/data-health.ts | Authenticated request orchestration; six regular reads and at most one explicitly selected audit |
| frontend/lib/data-health-summary.ts | One-pass recent-run counters, per-type summaries and latest-by-source index |
| frontend/components/data-health/health-overview.tsx | Page composition, navigation and contradiction review; reduced from 672 to 99 lines |
| frontend/components/data-health/health-diagnostics.tsx | Evidence, certification, coverage and exact-span backfill presentation |
| frontend/components/data-health/provider-health.tsx | Provider summary and status table |
| frontend/components/data-health/processing-health.tsx | Recent-run totals, freshness, configured sources and bounded history table |

The selected audit no longer waits for the regular reads to finish before it
starts. Unselected audits remain unrequested and diagnostic links still disable
prefetch. Requests have no shared response cache. Per-source lookups no longer
filter the entire run array; type groups retain summaries rather than arrays.
Latest attempts compare actual timestamps rather than assuming creation order.

Failures retain metadata and errors, suppress stale payloads and show unavailable
states. Successful empty responses retain their empty states. Failed audits differ
from audits that were never requested. Counts disclose the latest 100 returned
runs instead of implying whole-database totals. The recent history table still
renders at most 25 rows. Evidence links, review actions and panel order remain.

The root Docker context now explicitly includes maintained backend trees and
dependency/build inputs instead of every backend file. Existing nested secret/cache
exclusions remain last. Temporary source-review images are excluded from routine
searches by .rgignore and retained in place. These are input-boundary changes;
no image-size or build-time improvement was measured.

## Verification

The baseline frontend suite passed. Four new rendered regressions failed before
the implementation and passed afterward. Final source count is in
[Current State](../../../00-current-state.md). New checks cover one-pass indexing,
timezone/order handling, audit concurrency/selection, request isolation, error
metadata, empty/populated rendering and the 25-row table limit. Existing source
guards follow the extracted owners without removing evidence/review assertions.

All local logs and the bounded inventory are under /private/tmp/mi-structure-20261025.
The initial full-suite attempt from the repository root used the wrong working
directory; the corrected baseline and final runs use frontend as required.
An intermediate source-guard failure was resolved by following extracted owners.
The populated-page test caught the old misuse of a stale-data message for failed
requests; that message wiring was corrected before the final passing run.

A Mock Data microbenchmark used 100 runs and 1,000 source lookups. The old path
examined source IDs 100,000 times; the new path reads them 100 times and performs
1,000 map lookups. Five batches of 200 iterations gave median 0.171ms versus
0.085ms per pass on this host. This tests only that local operation, not page
latency, production data or concurrent-user capacity.

Full type checking repeats the baseline missing-package diagnostics. The approved
package restoration made no changes because the network allowlist blocked npm.
An additional diagnostic run type-checked all application and unit-test sources
with no errors, excluding only e2e files for that run. The checked-in TypeScript
configuration was not changed and the full gate remains blocked. A bounded link
check passed 317 relative targets in changed documentation, skipping the protected
environment-template target; handoff/current-state line budgets pass. This is not
a substitute for the full Python documentation checker.
The Compose allowlist guard was updated, but its Python execution and Docker
build validation remain pending under the ledger's toolchain constraints.
