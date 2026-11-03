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
- Read `docs/HANDOFF.md` and `docs/code-map.md`; use Current State for status
  questions and architecture for major changes, not as a repeated universal read.

## Inputs

- User request.
- Relevant source files.
- Current docs and tests.

## Outputs

- Clear placement decision.
- Files to inspect or change.
- Risks, unknowns, and verification commands.

## Workflow

1. Use the handoff/code map to locate the owner and read only the relevant current
   reference. In a parallel batch check the assigned allowlist before editing.
2. Identify the affected layer: frontend, backend, database, ingestion, valuation, security, docs, or operations.
3. Inspect the actual code before trusting docs.
4. Classify the capability as implemented, partial, planned, mocked, obsolete, or unknown.
5. Pick the smallest safe change.
6. Update docs if behavior or architecture reality changes.
7. Verify with focused tests or docs sanity checks.
8. Separate source-level proof, isolated runtime proof, and user-reported manual
   proof. Do not carry one category forward as another.
9. For authenticated server-rendered routes, preserve the dynamic request
   boundary and signed internal identity flow. For service startup, distinguish
   process liveness from database/migration/schema readiness.
10. For cross-model search, map every result type to its ownership, claim type,
    review gate, company relationship, and stable destination before adding it.

## Acceptance criteria

- No feature is described as working unless code or tests support it.
- The change belongs in the right layer.
- Frontend, backend, schema, and docs do not contradict each other.
- Remaining uncertainty is labeled.
- Runtime claims name the environment and validation that produced them.
- Aggregation does not erase access control or make derived interpretation factual.

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
