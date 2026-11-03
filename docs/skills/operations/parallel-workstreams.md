# Parallel workstreams workflow

## Purpose

Let independent agents edit concurrently without shared-file races or hidden
dependencies. The current batch is [Knull](../../../Knull%28readme%29.md).

## When to use

An explicitly requested parallel batch or an assigned stream in that batch.

## When NOT to use

A single bounded task. This workflow does not itself authorize spawning agents.

## Prerequisites

Read root rules, handoff, code map, assigned scope and ownership manifest. Preserve
dirty/untracked work and establish one reviewed baseline before dispatch.

## Inputs

Independent outcomes, frozen shared contracts, exact write allocations, available
agent/runtime capacity, tests and user/source/operator acceptance gates.

## Outputs

Disjoint patches, per-agent evidence and a coordinated integration result.

## Workflow

1. Split by complete domain outcome, including tests/UI, not by frontend/backend
   roles that must edit the same feature together.
2. Allocate exact files and non-overlapping new directories. Freeze unlisted
   paths, models/migrations, common contracts and shared docs. Use the path guard.
3. Prefer separate worktrees from the same preserved baseline. New worktrees do
   not automatically include current uncommitted source or private configuration.
4. Freeze existing call/response semantics, not just names. Each stream uses its
   own fixtures and must pass without another stream's unfinished commits.
5. Give one coordinator ownership of shared integration and runtime leases.
   Serialize fixed-project browser/release/recovery tools; isolated file edits
   do not isolate databases, ports, images, build outputs or cleanup.
6. Record out-of-scope needs in the requesting agent's evidence. Continue independent
   work. One owner integrates any shared prerequisite after affected agents stop;
   rebase and revalidate before resuming. Never quietly expand scope or clone code.
7. Handoff exact changes, tests/results, source provenance, remaining gates and doc
   proposals. Integrate one stream at a time, then run combined checks and update
   central docs once. Separate implementation, genuine-input and operator completion.

## Acceptance criteria

Path guard passes; no hidden cross-stream dependency; frozen contracts remain
compatible; tests use isolated inputs; evidence states what actually ran; shared
files and runtime changes have one owner. The guard is not a behavioral test.

## Common mistakes

Splitting one feature by technical layer; concurrent edits to central docs; creating
worktrees from an obsolete HEAD; assuming ports isolate fixed Compose projects;
calling a blocked real-input gate complete because Mock Data passed.

## Do not do

Do not reset user work, seed the normal database, race migrations, auto-resolve
semantic conflicts, or start more agents than the supported execution capacity.

## Related skills

Architecture, documentation, local operations and the assigned domain workflow.

## References

- [Workflow routing](../README.md)
- [Execution runbook](../../08-execution-runbook.md)
- [Current allocations](../../workstreams/ownership.tsv)
