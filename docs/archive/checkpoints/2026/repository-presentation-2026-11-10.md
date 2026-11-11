# Repository presentation cleanup: November 10, 2026

## Scope and baseline

Prepared the repository for external review without changing application behavior,
migrations, financial inputs, or the running stack. GitHub's private default branch
was codex/worktree-recovery at 9f17dd6a; PR9 was already merged. The matching
pre-edit document blobs were compared with the published tree.

The local checkout began at fba390bf with 390 modified files, six prior deletions,
765 untracked files, and an empty staging area. Those earlier changes were
preserved. This cleanup is a separately enumerated patch against the published
baseline, not a broad commit of the local checkout.

## Organization

- README leads with product workflows, local setup, architecture, and navigation.
- Current docs use descriptive names instead of inconsistent numeric prefixes.
- Setup, development checks, operations, user guidance, and detailed workflow
  implementation have separate owners.
- Backend, scripts, and data have directory guides. The code map covers every
  published top-level area and the existing domain-owner map.
- The limitations ledger and product/status/roadmap pages no longer repeat long
  operational histories. Current scope and PR9's merged state are reconciled.
- Contribution and security policies provide GitHub-visible entry points.
  No project license was invented and repository visibility was not changed.

Eight entry/current guides decreased from 22,825 to 6,443 words at the initial
measurement, about 72%. Detailed workflow behavior and dated evidence remain in
references and archives. This is a reading-length reduction, not a claim of
equivalent total-repository byte savings.

## Path map

| Previous path | Current owner |
|---|---|
| docs/00-current-state.md | [Current state](../../../current-state.md) |
| docs/01-product-brief.md | [Product brief](../../../product-brief.md) |
| docs/02-architecture.md | [Architecture](../../../architecture.md) and [workflow reference](../../../reference/workflows.md) |
| docs/03-database-schema.md | [Database schema](../../../database-schema.md) |
| docs/04-data-sources-and-ingestion.md | [Data sources](../../../data-sources.md) |
| docs/05-scoring-framework.md | [Scoring](../../../scoring.md) |
| docs/06-security-threat-model.md | [Security](../../../security.md) |
| docs/07-local-development.md | [Local development](../../../local-development.md) |
| docs/08-execution-runbook.md | [Execution runbook](../../../execution-runbook.md) and [Operations](../../../operations.md) |
| docs/09-beginner-glossary.md | [Glossary](../../../glossary.md) |
| docs/09-route-inventory.md | [Route inventory](../../../route-inventory.md) |
| docs/12-assumption-methodology-engine.md | [Assumption methodology](../../../assumption-methodology.md) |
| docs/agent_capabilities_and_limitations.md | [Limitations](../../../limitations.md) |
| Knull(readme).md | [Workstream design](../../../workstreams/plan.md) |
| DELIVERY_VALIDATION.md | [Unchanged supplied report](../../assessments/delivery-validation-2026-11-04.md) |

The redundant root product-integrity redirect was removed; its full historical
plan remains in [the archive](../../plans/product-integrity-sequential-build-master-plan-2026-08-08.md).
Earlier current-state, limitation, and handoff snapshots retain their exact bytes.

## Cleanup and retention

The [retirement inventory](../../../../scripts/retired/inventory-2026-11-10.json)
records two unreferenced scratch scripts, their original paths, hashes, and 2,883
bytes. Originals remain as inactive local copies and in prior Git history.
The old route generator inferred Built status from source strings and would
overwrite reviewed documentation; the documentation checker now owns coverage.

Eleven generated .DS_Store files were removed: 102,444 logical bytes. Their exact
paths and sizes are in the local cleanup inventory. This is not a net disk-space
claim because before-images and evidence were retained.

Git ignore rules now keep 95 previously discoverable local files outside the
publication candidates: copied helper packages, source-review renders, privacy
notes, and workstream before-images/patches. Existing versioned review receipts,
benchmarks, immutable source originals, databases, backups, and installed
dependencies were preserved. No Git history rewrite or dependency removal occurred.

## Verification

- Ten ownership-guard regression cases pass; 150 reservations remain disjoint.
- Independent Node audit checks current document paths/headings, all 50 route
  pages, context budgets, and migration-head agreement. It is not execution of
  the Python checker. Environment-template targets are checked through published
  path metadata; their protected contents were not read.
- The Python checker now covers directory guides, GitHub policies, heading
  fragments, duplicate/explicit anchors, and local-only helper exclusions.
  Six additional regression cases cover these behaviors.
- Baseline file hashes show no application, test-fixture, migration, or runtime
  configuration changes. Staging remains untouched.
- Python and Docker are unavailable to this local session. Native Git and Node
  were located without installing system developer tools or changing permissions.
- [PR10](https://github.com/Gittastic112/Marketagent/pull/10) contains only this
  reviewed cleanup. Its first clean checkout passed all 18 documentation-checker
  regression tests and caught one stale inline archive-index path, corrected in
  the follow-up. The PR checks record the canonical documentation, application,
  browser, security, and recovery results for each commit.

Local before-images, hash comparisons, changed-path allowlist, path moves,
documentation audit, and cleanup inventory are retained under
output/repository-cleanup-20261110. No private output directory is published.

## Basis and limits

The structure follows [GitHub's README guidance](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/about-readmes)
and [repository practices](https://docs.github.com/en/repositories/creating-and-managing-repositories/best-practices-for-repositories):
clear purpose/setup/navigation, focused policies, and separation of source from
local/generated content. The current 1,475-file published tree was inventoried;
large retained files are source material, not generated application clutter.

This cleanup is not financial acceptance, a runtime rollout, a rights clearance,
or a full-history secret audit. Protected settings were not inspected. Application
validation and existing operating limits retain their original dates and scope.
