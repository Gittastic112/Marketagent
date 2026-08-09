# Architecture Overview Skill

## Purpose

Help agents understand where a change belongs before editing code or docs.

## When to use

- A task touches more than one layer.
- A feature spans backend, frontend, database, ingestion, valuation, or security.
- Docs and code may disagree.
- You need to decide whether something is implemented, partial, planned, mocked, or obsolete.

## When NOT to use

- Single-line copy edits with no architecture impact.
- Pure formatting changes.

## Prerequisites

- Read `AGENTS.md`.
- Read `docs/HANDOFF.md` and `docs/00-current-state.md`.

## Inputs

- User request.
- Relevant source files.
- Current docs and tests.

## Outputs

- Clear placement decision.
- Files to inspect or change.
- Risks, unknowns, and verification commands.

## Workflow

1. Read the current handoff and current-state doc.
2. Identify the affected layer: frontend, backend, database, ingestion, valuation, security, docs, or operations.
3. Inspect the actual code before trusting docs.
4. Classify the capability as implemented, partial, planned, mocked, obsolete, or unknown.
5. Pick the smallest safe change.
6. Update docs if behavior or architecture reality changes.
7. Verify with focused tests or docs sanity checks.

## Acceptance criteria

- No feature is described as working unless code or tests support it.
- The change belongs in the right layer.
- Frontend, backend, schema, and docs do not contradict each other.
- Remaining uncertainty is labeled.

## Common mistakes

- Treating roadmap text as implementation proof.
- Building from archived docs.
- Adding UI affordances for backend features that do not exist.
- Reorganizing large modules during a narrow task.

## Do not do

- Do not rely only on `README.md`.
- Do not present mock data as live data.
- Do not skip migrations/schema inspection for persisted behavior.

## Related skills

- `documentation-workflow`
- `backend-api-change`
- `frontend-data-state`
- `security-review`

## References

- `AGENTS.md`
- `docs/HANDOFF.md`
- `docs/00-current-state.md`
- `docs/02-architecture.md`
- `docs/agent_capabilities_and_limitations.md`
