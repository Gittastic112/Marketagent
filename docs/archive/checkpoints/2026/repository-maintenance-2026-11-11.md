# Repository maintenance follow-up: November 11, 2026

## Baseline and scope

This follow-up starts from PR10's merged commit 4020f6cf. The private repository
contained 1,485 published files. Local HEAD remains fba390bf with existing edits;
this pass preserves those edits and publishes only its reviewed paths.

The change concerns repository navigation, obsolete developer tools, and review
checks. Application APIs, calculations, financial records, migrations, runtime
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
black-box cases for its unavailable behavior; application tests are retained.

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
claim that the Python suite ran on this Mac.

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
