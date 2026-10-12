# Agent Handoff

October 11, 2026: M01-M02 accepted; M03-M09 have source work and open gates.
The [completion tracker](roadmaps/completion-tracker.md) owns percentage requests.
Two of ten gates means 20 acceptance points, not 20% of engineering hours.
"Next 10%" means M03, the earliest unfinished milestone. Do not report 90% complete.

## Current execution boundary

The user authorized sequential M02-M09, conservative continuation when inputs are
missing, refactors/worktrees, Git/GitHub publication and fixing browser/CI failures.
GitHub is Allow all actions; other app permissions remain unchanged. No parallel
agents were launched. Public deployment, broker integration and M10 acceptance
are outside this task. Follow the nearest AGENTS.md and actual owning code.

Private [draft PR #1](https://github.com/Gittastic112/Marketagent/pull/1) preserves
the M01 source baseline. [Draft PR #2](https://github.com/Gittastic112/Marketagent/pull/2)
on codex/m02-m09-completion holds subsequent work, based on the M01 branch.
Consult the PR for the latest published head and checks; the
[M09 checkpoint](archive/checkpoints/2026/m09-browser-validation-2026-10-11.md)
owns integrated source/browser evidence and its exact limits.
The shared local branch/index contains extensive prior changes. Publication uses
an explicit-path isolated Git snapshot; never reset, clean or stage everything.
Protected environment files are excluded and must not be read indirectly.

## Implemented source work

- [M02](archive/checkpoints/2026/m02-ownership-2026-10-11.md): domain-owned contracts,
  server actions, provider workflows and UI orchestration, compatibility facades,
  contract-drift guards and classified retired tooling.
- [M03 recovery](archive/checkpoints/2026/m03-recovery-2026-10-11.md) and
  [security](archive/checkpoints/2026/m03-security-2026-10-11.md): consistent format-2
  dump/asset fingerprints, disposable concurrent-write restore, bounded parsers
  and outbound clients, locked dependencies and container/security CI.
- [M04](archive/checkpoints/2026/m04-ingestion-2026-10-11.md): scoped identities,
  bounded/idempotent ingestion, dated price coverage and truthful Processing Runs.
  Runs 20-40 added 667 unreviewed SEC candidates, 196 FRED observations and 2,739
  price/history rows across eleven securities. Failed fetches remain audited.
- [M05](archive/checkpoints/2026/m05-financial-evidence-2026-10-11.md): per-company
  evidence inventory and review/certification guards. No normal facts were approved.
- [M06](archive/checkpoints/2026/m06-sensitivity-2026-10-11.md): canonical saved-FCFF
  sensitivity, explicit validity/basis and keyboard/mobile table access.
- [M07](archive/checkpoints/2026/m07-portfolio-replay-2026-10-11.md): dated recorded
  positions/cash, purchase-date FX, reconciliation and snapshot activity hashes.
  Legacy/manual snapshots and corrected activity remain provisional. No trades
  are inferred and historical risk remains a fixed-weight price-return calculation.
- [M08](archive/checkpoints/2026/m08-private-brief-context-2026-10-11.md): explicit
  quoted period/currency/scope comparison and bounded owner-scoped private context
  in manual/scheduled briefs. Reviewed and pending queues remain separate, saved
  as generated, with no automatic external AI or numeric assumption changes.
- [M09](archive/checkpoints/2026/m09-browser-validation-2026-10-11.md): production
  browser coverage for all 50 page routes at desktop/mobile sizes plus functional
  workflows. Semantic fixes retain standalone finding links and label research input.
  Mock Data, route layout checks and builds do not certify all controls or real inputs.

## Normal runtime and recovery

Normal frontend/backend/Daily Brief worker remain on the validated M01 images,
with PostgreSQL schema s1s1s1s1s1s1 and localhost ports. The source worker and
pgAdmin stay stopped with restart=no. Do not infer a rollout from a successful build.
Disposable browser databases use separate tmpfs projects and explicit test settings.
Do not remove normal volumes, backups, rollback images or the immutable corpus.

M03's current-backup preflight produced a verified 109-table dump/manifest but
macOS rejected final atomic directory rename, including an escalated retry.
The `.partial` backup remains explicitly incomplete; do not bypass that denial
or call it a finalized backup. The earlier verified M01 backup is preserved.
Normal rollout requires resolving that preflight and rechecking source/image/data
identity. The exact paths and failure are in the M03 recovery checkpoint.

The user has no off-device backup destination or genuine trade records yet.
Continue independent work, retain the explicit open gates, and never manufacture
records, review approvals, recovery credentials or user acceptance. Host security,
reviewed source/valuation coverage, actual multi-currency portfolio proof, AI quality,
full adverse-state/control coverage and recovery remain in the
[single limitation ledger](agent_capabilities_and_limitations.md).

## Next work

Close the remaining stable task IDs in the tracker using dated evidence, beginning
with M03. Reconcile source/CI evidence after every publication; preserve failed-run
artifacts. Browser/release projects and heavy PDF/build tests must run sequentially
on the small Docker VM. Commands belong in the [runbook](08-execution-runbook.md).
[Knull](../Knull%28readme%29.md) and the [ownership manifest](workstreams/ownership.tsv)
apply if the user explicitly requests a parallel batch; they do not launch one.
