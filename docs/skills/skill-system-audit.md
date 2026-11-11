# Skill system audit

Reviewed October 5, 2026 for documentation efficiency and concurrent execution.
This records repository workflow/package state, not installed-session inventory
or a product capability certification.

## Explicit package

| Package | Actual state | Decision |
|---|---|---|
| [security-review](../../skills/security-review/SKILL.md) | One repository package; metadata retains allow_implicit_invocation: true. Installation is not established by this repository | Replace duplicated checklist with a narrow entrypoint to the canonical project security workflow. Keep explicit/implicit scope aligned |

No global skill files or installation settings were changed. The session's
installed skill-authoring guide was inaccessible even after an escalated read
attempt; the accessible repository maintenance workflow governed this edit.

## Workflow families

| Family | October 5 disposition | Reason |
|---|---|---|
| Workflow routing/index | Simplified | Select one primary workflow, add only relevant cross-cutting references; distinguish documentation selection from installed skill invocation |
| Architecture | Updated | Smallest-context routing instead of unconditional repeated status/history reads |
| Documentation | Updated | One current owner per concern, current batch separate from roadmap, per-agent proposals for shared docs, exact validation scope |
| Skill maintenance | Updated | Thin explicit package, canonical workflow, metadata alignment and coordinator ownership |
| Security | Updated | Same-origin/body/download boundaries and immutable/stale analyst receipts reflected in the reusable checklist; respect secret-file access restrictions |
| Market intelligence | Updated | Private-source comparisons, review receipts and deterministic snapshot boundaries |
| Operations | Updated | Fixed-project test collisions, isolated evidence and serialized operational lanes |
| Parallel workstreams | Added | Reusable exclusive-path, contract-freeze, baseline and shared-change procedure |
| Backend / frontend | Updated | Route new work to actual domain contracts/clients rather than compatibility facades; retain auth, envelopes and data-state rules |
| Ingestion / financial extraction | Updated | Start audit runs before work; distinguish explicitly unreviewed draft suggestions from trusted normalized facts; reduce repeated prerequisite reading |
| Valuation | Updated | Add sensitivity basis/validity and legacy-output distinctions while retaining deterministic finance, zero/missing and review boundaries |

There are 12 project workflow references and one explicit package. The package is
not another project workflow reference and is not counted by the existing
project-workflow validator.

## Efficiency and ownership decisions

- Root/nested AGENTS files enforce repository rules; workflows do not repeat a
  second universal reading stack. Commands, limits and status retain canonical owners.
- [workstream design](../workstreams/plan.md) retains batch scopes, while the roadmap owns product
  priorities. The manifest and shell guard make file allocation checkable.
- Shared workflow edits happen through the coordinator after integration. Agents
  keep proposed changes in their own evidence instead of racing to append here.
- Do not package all project references as global skills. Promote a workflow only
  after repeated use demonstrates a need and its repository references can resolve.
- Archived prompts, design briefs and superseded valuation plans remain historical
  context. They are not implicit skills, active task queues or auto-loaded instructions.

## Verification

The [audit receipt](../archive/checkpoints/2026/documentation-and-parallel-plan-2026-10-05.md)
records shell checks and the blocked Git/Python/Node runtimes. Do not carry forward
September test counts as new evidence. The standard Python documentation and skill
validators still need a working runtime; no validator was weakened to hide that.
