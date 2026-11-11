# Repository maintenance follow-up: November 11, 2026

## Baseline and scope

This follow-up starts from PR10's merged commit 4020f6cf. The published repository
contained 1,485 published files. Local HEAD remains fba390bf with existing edits;
this pass preserves those edits and publishes only its reviewed paths. GitHub
reports the repository as public at the final November 11 metadata check; this
cleanup did not change its visibility.

The change concerns repository navigation, obsolete developer tools, unused UI
modules, and review checks. Application APIs, calculations, financial records, migrations, runtime
configuration, dependencies, and immutable source originals are preserved.

## Cuts and consolidation

| Previous active content | Treatment |
|---|---|
| 3,962-word October workstream narrative | [Archived design](../../plans/workstreams-2026-10-05.md); current scope index is 328 words with preserved incoming anchors |
| 2,471-word historical decision narrative | [Archived readable record](../../assessments/research-demo-decisions-2026-11-04.md); current index is 311 words and points to the unchanged decision register |
| Uncalled manual ledger smoke script | Removed from backend/scripts; maintained assumption-diff and version-integrity tests remain |
| Legacy Milestone A verifier | Incompatible unauthenticated request/response logic retired; command path now returns an explicit unavailable notice, including with old write flags |

The two current narratives are about 90% shorter. Archives retain their content
with a historical notice and rebased working links. Exact before-images are
retained locally and in the baseline Git revision. The
[retirement inventory](../../../../scripts/retired/inventory-2026-11-11.json)
records original paths, hashes, byte counts, retained copies, and replacement
behavior. Five helper tests for the retired verifier are replaced by three
black-box cases for its unavailable behavior. The unused UI audit below explains
the separate retirement of two helper-only frontend tests.

## Unused frontend paths

An import audit covered 334 frontend source/config/test modules and 61 framework
entry points. The six components below had no import callers. The form adapter
was reachable only from the retired form and its own two tests. Repository
reference searches checked documentation and source-inspection tests as well.

| Removed path | Original bytes | Reason / maintained owner |
|---|---:|---|
| frontend/components/dcf-form.tsx | 35,695 | No route callers; advanced-workspace owns saved valuations |
| frontend/components/intelligence/AssumptionMethodSelector.tsx | 8,439 | No callers; backend method contracts remain, UI claim corrected |
| frontend/components/page-header.tsx | 639 | No callers; components/page owns the shared PageHeader |
| frontend/components/portfolio-analytics.tsx | 11,062 | No route callers; portfolio sections and performance panel own the workflow |
| frontend/components/ui/methodology-fallback.tsx | 744 | No callers |
| frontend/components/ui/scroll-area.tsx | 341 | No callers; no dependency removed |
| frontend/lib/regression-priors.ts | 2,104 | Only production caller was the retired DCF form |
| frontend/lib/regression-priors.test.ts | 1,145 | Two tests exercised only the retired form adapter; backend regression tests remain |

The active source tree loses 60,169 bytes across eight files. Exact local
before-images remain under the ignored audit output, so this is source reduction,
not a claim of disk-space recovery. Git retains the original published blobs.
The portfolio integrity assertion now checks the mounted performance panel and
its unavailable states; its other assertions remain. The method guide and
limitation ledger now state the actual UI boundary. No mounted route, API export,
backend regression calculation, or dependency was removed.

## Mapping and review improvements

- [API map](../../../reference/api-map.md): all 58 HTTP router modules.
- [Root command guide](../../../../scripts/README.md) and
  [backend command guide](../../../../backend/scripts/README.md): all 33 maintained
  commands, including 26 root tools and seven backend commands, with effects.
- [Historical evidence index](../../../workstreams/evidence/README.md): 34 retained
  artifacts across three dated batches. Their bytes and original paths are unchanged.
- The documentation checker now rejects unmapped commands, missing command guides,
  and missing/stale API module listings. Five added regressions cover these rules
  and the separation of historical receipt bodies from checked indexes.
- The duplicate market-data/fundamentals summary is removed from the data-source
  guide; its provider and financial-review sections remain the owners.
- Pull-request formatting now runs against the checkout's merge comparison before
  merge, while existing push safeguards remain. A concise
  [PR template](../../../../.github/pull_request_template.md) asks for the problem,
  result, verification, data/compatibility effects, and documentation owner.

## Retention decisions

The 41 nontrivial duplicate blob groups are workbook source/runtime mirrors.
Their separate paths serve the immutable corpus and application import contracts;
removing a path would require a separate data/import migration. They are retained.
Fixtures, acceptance gates, security controls, source reports, review receipts,
backups, installed dependencies, and rollback assets are retained for their
existing roles. No arbitrary file-size threshold or unused-looking name was used
as deletion authority. No license, public-sharing permission, or repository
administration change was invented.

## Verification record

Local checks cover all changed-file formatting, documentation paths and anchors,
source-to-inventory coverage, original/retained file hashes, and preservation
outside the change set. Ownership regression cases and the 150 reservations are
checked separately. The local Python toolchain is unavailable; this is not a
claim that the Python suite ran on this Mac. The final local frontend suite passes
363 tests, and TypeScript checking passes with incremental output disabled.

Canonical documentation regressions, backend/frontend behavior, builds, browser
workflows, security scans, and recovery run in
[GitHub CI](https://github.com/Gittastic112/Marketagent/actions/workflows/ci.yml).
The PR and commit checks retain exact outcomes; this checkpoint does not turn
software validation into financial, provider, or daily-use acceptance.

Local inventories, exact before-images, retained-tool hashes, formatting checks,
coverage checks, and preservation evidence are under
output/repository-cleanup-followup-20261111. This output directory is not published.

The workflow changes follow GitHub's
[pull-request event semantics](https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows#pull_request)
and [PR-template convention](https://docs.github.com/en/communities/using-templates-to-encourage-useful-issues-and-pull-requests/creating-a-pull-request-template-for-your-repository).
