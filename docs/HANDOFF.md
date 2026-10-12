# Agent Handoff

M02 accepted, M03-M06 in progress: 2026-10-11. Broader product proof stays
separately dated in [Current State](00-current-state.md). Latest work is recorded
in the [ownership](archive/checkpoints/2026/m02-ownership-2026-10-11.md) and
[recovery](archive/checkpoints/2026/m03-recovery-2026-10-11.md) and
[ingestion](archive/checkpoints/2026/m04-ingestion-2026-10-11.md) checkpoints.

## Next execution boundary

Use the [completion tracker](roadmaps/completion-tracker.md) for percentage work.
"Finish 10%" is satisfied; "finish the next 10%" means close M03, the earliest unfinished
milestone. The ten gates are acceptance points, not estimates of engineering hours.
M01 and M02 are accepted: 2/10 gates, or 20 acceptance points.
This is not an estimate of code completion or engineering hours.

Read the nearest AGENTS.md, [code map](code-map.md) and the milestone's actual
owners before editing. For architecture work, also read
[architecture](02-architecture.md). Preserve prior/untracked work.

The user authorized sequential M02 through M09 work and conservative continuation
when inputs are missing. Continue M07-M09 while preserving M04/M05 source-review
gaps. The [M05 checkpoint](archive/checkpoints/2026/m05-financial-evidence-2026-10-11.md) records 52 focused passing tests. Preserve human-review, actual-trade and
off-device recovery gates. M02 owns folder cleanup and module boundaries.
Portable tooling provides Git and recovery-script checks despite blocked host
runtimes. The private GitHub branch codex/m01-foundation preserves the tested
application/reference baseline and completion evidence in
[draft PR #1](https://github.com/Gittastic112/Marketagent/pull/1). Check its review/CI
state before integration. The shared local index/branch and unclassified prior files
remain preserved; do not infer a clean checkout or reset/stage everything.
Branch codex/m02-m09-completion is [PR #2](https://github.com/Gittastic112/Marketagent/pull/2).
M02 head 9881f4113a2649f27c4c2a91833676311ed7a0ce passes every GitHub check,
including 21 browser workflows. M03 recovery head b5c737bc8dd3af17aef401991cc7e39489a6314e
passes all eight GitHub checks. M03 security head de26630bb33aa0de41ada023a4acaf04a9d7a3b3
passes all ten push/PR checks. M04 head 44b93869 passes all ten checks;
see the [security checkpoint](archive/checkpoints/2026/m03-security-2026-10-11.md).
M04 phase two is published at 678068b5. Smaller tree writes resolved the stalled
publication. GitHub remains Allow all actions; other permission settings are unchanged.
The [M06 checkpoint](archive/checkpoints/2026/m06-sensitivity-2026-10-11.md) records 1,427 backend, three PostgreSQL,
263 frontend and 22 production browser tests passing, including mobile sensitivity.

## Runtime and source changes

- M04 source passes 1,402 backend tests. Runs 5-18 record successful SEC/FRED/Gemini
  connectivity and quotes/history for all 11 scoped securities. Probe success is
  not financial/price coverage. Run 19 adds nine absent catalog identities and fills
  missing AAPL/NVDA fields, preserving PLTR, share classes and existing records.
  No normal financial review or trade data was invented; source worker stays stopped.
- M04 follow-up passes manual mobile/PDF browser flows, 260 frontend tests, a
  production build, 69 focused backend tests and three PostgreSQL concurrency checks.
  Runs 20-40 add 667 unreviewed SEC candidates, 196 FRED observations and 2,739
  quote/history rows across all 11 securities. GOOGL's failed fetch remains audited.
- Docker's initial high CPU settled during idle samples. Old build cache and the
  local frontend generated cache were cleaned; temporary test images were removed.
  Volumes, rollback images, databases, backups and the immutable corpus were preserved.
- pgAdmin was stopped and its existing restart policy changed to no. Frontend,
  backend, PostgreSQL and the Daily Brief worker remain running. The source worker
  was already stopped; it was not started because it can perform external ingestion.
- Source now separates backend runtime/test targets and requirements, allowlists
  the backend build context and narrows development watching. Only backend startup
  runs migrations; both workers wait for healthy backend readiness. pgAdmin is
  bounded/opt-in; the development frontend's memory limit matches its heap budget.
- Normal frontend, backend and worker containers now use validated rebuilt images.
  Application/migration source matches the preserved rollout baseline. The only
  later backend-image source difference is a CI-only release script. Workers run
  direct commands; only the backend runs migrations. The source worker stays
  stopped with restart=no; pgAdmin is stopped and its 512 MiB limit is applied.
- A separate tools target runs repository/fake-Docker recovery tests without
  network, normal credentials or a Docker socket. Current database restore and
  all 109 table fingerprints pass. M03 now passes a concurrent-write disposable
  restore with both PDF stores and linked private/portfolio evidence. Off-device
  recovery remains open; the normal runtime still runs M01 source/images.
- Normal/source head remains s1s1s1s1s1s1. All 109 table fingerprints matched across
  rollout. Initial browser access generated one deterministic Daily Brief. A later
  normal quote ingestion changed three tables before the frontend security patch;
  the final browser check left all 109 unchanged. See the checkpoint for exact scope.
- Approved browser repairs cover navigation, review status, stored snapshots and
  fixture authentication without changing application guards. Functional workflows
  pass; the unchanged route-timing gate passed on repeat after one slow sample.
  The patched normal frontend passes five routes and inspected desktop/mobile views.
  Existing Mock Data screens do not certify the September genuine-input inventory.

## Remaining workstream designs

[Knull](../Knull%28readme%29.md) retains the detailed designs for recovery (M03),
financial coverage (M05), sensitivity (M06), portfolio replay (M07), and reviewed
brief context (M08). No parallel agents have been launched by this task. If the
user requests delegation, establish a preserved common baseline and follow the
[exclusive ownership manifest](workstreams/ownership.tsv). Unlisted/shared paths
stay frozen during parallel edits; the coordinator reconciles central docs once.

Browser/release runners use fixed Compose project names; serialize their use.
Recovery now allocates a unique portless tmpfs project. Commands and
validation belong in the [runbook](08-execution-runbook.md).

## Preserve product boundaries

The confirmed scope remains personal US/India research, USD reporting, five large
companies per market and dated prices. Earlier AAPL/GOOGL portfolio proof used
User Assumptions. The [single ledger](agent_capabilities_and_limitations.md) owns exact
input/review/provider/security gaps; the tracker does not invent missing evidence.

Source refreshes create review-required drafts, preserve edits, and never approve
facts or rewrite saved assumptions. Analyst receipts remain User Assumptions;
exact citations do not certify interpretation. Keep legacy imports compatible,
calculations backend-owned, auth/provenance intact and data states truthful.

Local authentication is not public-deployment security. Preserve localhost ports,
private evidence and database volumes. No broker credentials, buy/sell advice,
fabricated facts or automatic external AI. Protected environment files were not
read. The [prior handoff](archive/handoffs/handoff-before-resource-audit-2026-10-10.md)
is historical evidence, not the execution queue.
