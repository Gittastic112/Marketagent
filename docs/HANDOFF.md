# Agent Handoff

Infrastructure and completion-plan review: 2026-10-10. Broader product proof stays
separately dated in [Current State](00-current-state.md). Latest work is recorded
in the [architecture/resource audit](archive/checkpoints/2026/architecture-and-completion-2026-10-10.md).

## Next execution boundary

Use the [completion tracker](roadmaps/completion-tracker.md) for percentage work.
"Finish 10%" means close M01; "finish the next 10%" means the earliest unfinished
milestone. The ten gates are acceptance points, not estimates of engineering hours.
M01 is in progress, with no entire milestone accepted. Existing implementation
is substantial; this is not a claim that the app is 0% built.

Read the nearest AGENTS.md, [code map](code-map.md) and the milestone's actual
owners before editing. For architecture work, also read
[architecture](02-architecture.md). Preserve prior/untracked work.

M01 still needs controlled normal-runtime rollout and the remaining integrated
browser gates. Portable tooling now provides Git and recovery-script checks even
though host/bundled runtimes are blocked. Scoped Git inventory and a private
source-only safety archive are recorded in the checkpoint. Hundreds of existing
changes/untracked files remain; do not infer a clean checkout or stage them all.
Legacy source classification and safe relocation belong to M02.

## Runtime and source changes

- Docker's initial high CPU settled during idle samples. Old build cache and the
  local frontend generated cache were cleaned; volumes, images, databases,
  backups and the immutable corpus were preserved.
- pgAdmin was stopped and its existing restart policy changed to no. Frontend,
  backend, PostgreSQL and the Daily Brief worker remain running. The source worker
  was already stopped; it was not started because it can perform external ingestion.
- Source now separates backend runtime/test targets and requirements, allowlists
  the backend build context and narrows development watching. Only backend startup
  runs migrations; both workers wait for healthy backend readiness. pgAdmin is
  bounded/opt-in; the development frontend's memory limit matches its heap budget.
- New backend runtime/test images were built and checked separately. Existing
  normal app/worker containers were not replaced, so their commands/images still
  predate these source changes. Follow the runbook and verify source/image identity
  before claiming rollout. Keep source-worker state explicit.
- A separate tools target runs repository/fake-Docker recovery tests without
  network, normal credentials or a Docker socket. Populated/off-device recovery
  still needs M03; passing script fixtures is not that proof.
- Normal runtime and the rebuilt source report migration head s1s1s1s1s1s1. No
  migration or user record was changed. Never reset/stamp a migration problem.

## Remaining workstream designs

[Knull](../Knull%28readme%29.md) retains the detailed designs for recovery (M03),
financial coverage (M05), sensitivity (M06), portfolio replay (M07), and reviewed
brief context (M08). No parallel agents have been launched by this task. If the
user requests delegation, establish a preserved common baseline and follow the
[exclusive ownership manifest](workstreams/ownership.tsv). Unlisted/shared paths
stay frozen during parallel edits; the coordinator reconciles central docs once.

Browser/release/restore runners use fixed Compose project names. Serialize their
use and cleanup; different ports/worktrees alone are not isolation. Commands and
validation belong in the [runbook](08-execution-runbook.md).

## Preserve product boundaries

The confirmed scope remains personal US/India research, USD reporting, five large
companies per market and dated prices. Portfolio 1's AAPL/GOOGL activity is a User
Assumption. The [single ledger](agent_capabilities_and_limitations.md) owns exact
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
