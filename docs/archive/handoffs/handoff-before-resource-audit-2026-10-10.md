# Agent Handoff

Documentation/plan review: 2026-10-05. Product verification remains dated
2026-09-30 in [Current State](00-current-state.md); it was not rerun for this edit.

## Start with the assigned task

Read the nearest AGENTS.md and [code map](code-map.md), then only the relevant
reference from [the index](README.md). Major architecture changes also need
[current state](00-current-state.md) and [architecture](02-architecture.md).
Code and tests beat plans. Archive bodies are historical evidence.

## Next execution boundary

[Knull](../Knull%28readme%29.md) contains the next five independent workstreams:
reviewed brief context, financial-source coverage, portfolio history, sensitivity
integrity and backup/recovery consistency. It owns the detailed phases and gates.
The [write allowlist](workstreams/ownership.tsv) assigns every permitted path to
one agent. Unlisted paths and shared contracts are frozen during parallel work.
Each agent keeps its own evidence; the coordinator reconciles central docs once.

Before dispatch, establish a preserved common Git baseline containing the actual
current uncommitted source, verify the migration chain and run baseline checks.
Do not create worktrees from an older HEAD and silently lose prior improvements.
No development agents were started by the documentation task.

Browser/release/restore checks need a coordinator-controlled lane: existing
runners use fixed Compose project names. Separate worktrees and ports alone do
not isolate cleanup. Commands and guard usage live in the [runbook](08-execution-runbook.md).

## Preserve these source boundaries

- Source migration head remains s1s1s1s1s1s1. September 30 recovery/runtime proof is
  historical evidence until checked again. Never reset/stamp a migration problem.
- Valuation/portfolio/common contracts have narrow owners; legacy imports remain
  compatibility facades. Frontend domain API modules own new client work.
- Source refreshes create review-required drafts and preserve edits. They do not
  approve candidates, rewrite saved assumptions or automate external AI.
- Private source comparison and append-only analyst receipts retain exact evidence,
  owner scope and stale-version guards. Review is User Assumption, not AI approval.
- Existing saved-input, reverse DCF, options and specialized-engine repairs have
  dated tests. Historical outputs are not silently recalculated.
- Actuals, benchmark priors, calculations, estimates, AI interpretations and user
  assumptions must remain distinct. Missing inputs never become synthetic facts.

## User/data boundary

The confirmed scope is personal research, US/India, USD base and five large
companies per market. Daily closes and a 20-minute Sheets delay are acceptable.
Portfolio 1's AAPL/GOOGL activity is explicitly User Assumption, not broker history.
The [single ledger](agent_capabilities_and_limitations.md) owns exact assumptions,
review/input gaps, provider scope, security residuals and operational limitations.
Do not duplicate or silently broaden that scope in an implementation plan.

## Validation and launch constraints

[October 5 audit](archive/checkpoints/2026/documentation-and-parallel-plan-2026-10-05.md)
records the documentation/ownership checks and blocked runtime tools. A successful
ownership check proves disjoint path reservations, not behavioral compatibility.
Git status, full Python doc/skill validation and product/runtime checks remain
pending for this session. Preserve all existing/untracked work. The prior handoff
is [archived](archive/handoffs/handoff-before-parallel-plan-2026-10-05.md).

## Non-negotiable boundaries

Local authentication is not public-deployment security. Keep published ports on
127.0.0.1; inspect actual containers before operational changes. No broker
credentials, buy/sell recommendations, fabricated facts or silent AI promotion.
Normal database replacement requires exact-target/data-loss authorization.
The intentionally replaced pre-August-9 migration history cannot upgrade deleted
20260524_* or 20260530_* revisions by assumption. Stop and inspect.
