# Workstream coordination

The [five-workstream design](plan.md), originally prepared October 5, retains
technical scopes and integration rules. It is a design reference, not a current
launch instruction or a list of unimplemented features. The
[completion tracker](../roadmaps/completion-tracker.md) owns acceptance status.

- [ownership.tsv](ownership.tsv) is the exclusive allowlist for an explicitly
  assigned batch. A file reservation is exact; a tree reservation ends in /.
  Unlisted paths are frozen during that batch.
- W1 covers briefing, W2 financial sources, W3 portfolio history, W4 sensitivities,
  and W5 recovery. Allocation never grants unrelated feature scope.
- [evidence/](evidence/) retains dated review and execution receipts. Some files
  are published; local snapshots and patches are not application code.
- The coordinator reconciles shared documents after integration. Agents propose
  cross-boundary changes in their allocated receipt instead of duplicating work.

Use the [runbook](../execution-runbook.md#parallel-workstream-checks) for path
guards. A passing ownership check does not prove behavior, test isolation, or
that a supplied changed-file list is complete.
