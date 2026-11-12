# Agent Handoff

## Latest source boundary

November 11, 2026: main is the primary branch for new work and pull requests.
CI runs on main pushes, pull requests, and tags. Older branch references in
archived evidence describe their original verification and remain unchanged.

Repository navigation and [Compose ownership](../docker/README.md) are documented.
Python editor paths live in pyproject.toml; personal editor/agent overrides stay
local. The [efficiency checkpoint](archive/checkpoints/2026/repository-efficiency-2026-11-11.md)
retains the scanner, style-ownership, and conservative CI-selection evidence.

## Start a change

Read the nearest AGENTS.md, then the matching domain in the
[code map](code-map.md). The [documentation index](README.md) assigns one
current owner per topic. [Execution runbook](execution-runbook.md) owns checks;
[Operations](operations.md) owns changes to an existing installation.
Inspect local status before editing and preserve uncommitted work.

## Product boundary

This is local equity-research, valuation, and portfolio software with source
traceability. Research/demo validation does not establish genuine transaction
accuracy, complete financial facts, daily-use acceptance, or readiness for
public hosting. Keep sourced facts, estimates, assumptions, and Mock Data distinct.

[Current State](current-state.md) owns dated validation and delivered behavior.
The [limitation ledger](limitations.md) owns unresolved product and operating gaps.
Historical checkpoints retain evidence; they are not a current execution queue.

## Preserve while maintaining

Keep original assets, reviewed evidence, backups, failed reports, and rollback
material. Confirm the actual target before any operational change. Do not reset,
clean, or broadly stage a checkout to conceal pre-existing work. Cleanup does not
authorize data ingestion, new AI disclosure, broker activity, or public deployment.

## Next work

Use the [roadmap](roadmaps/product-roadmap.md) for priority and the
[ordered handoff](limitations.md#ordered-operator-handoff) for prerequisites.
Structural cleanup does not advance product acceptance gates. Source completeness
and actual-use evidence cannot be supplied by automated tests.
