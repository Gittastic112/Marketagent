# Project workflow routing

Read the root/nested agent rules, handoff and code map once. Then choose the
smallest relevant workflow below. Do not load this entire library for every task.
Hard rules live in AGENTS.md; commands live in the execution runbook; status and
limitations have their own canonical owners in the [documentation map](../README.md).

## What is implicit, explicit and actually available

- `docs/skills` contains project workflow references. Agents select them by task
  relevance or a direct request. They are not automatically installed Codex skills.
- The repository package [security-review](../../skills/security-review/SKILL.md)
  supplies skill metadata and a thin entrypoint to the canonical security workflow.
  Its policy allows implicit invocation when the package is installed and the task
  matches. A user can also invoke it explicitly in a session that exposes it.
- Repository presence, metadata and installation are different facts. Check the
  session's available-skills list. Do not claim installation, global availability
  or a permissions change from reading these files. No global skill was installed
  or changed by this documentation batch.

## Choose by the work, not by keywords

| Task | Primary workflow | Add only when needed |
|---|---|---|
| Find an owner or change runtime boundaries | [Architecture](architecture/architecture-overview.md) | Security for identity/data-flow changes |
| Change API behavior/contracts | [Backend](backend/backend-api-change.md) | Relevant domain workflow and security |
| Change presentation/forms/data states | [Frontend](frontend/frontend-data-state.md) | Domain behavior and security for input/auth changes |
| Ingest a source/provider | [Ingestion](data-ingestion/data-ingestion-workflow.md) | Security; extraction for financial statements |
| Extract/review/normalize financials | [Financial extraction](data-ingestion/financial-statement-extraction.md) | Ingestion only for new source transport |
| Change valuation math or assumptions | [Valuation](valuation/valuation-workflow.md) | Backend/frontend only for those layers |
| Change evidence, research or briefs | [Market intelligence](market-intelligence/market-intelligence-workflow.md) | Security for private sources, AI or owned evidence |
| Review auth, uploads, URLs, private data or external calls | [Security](security/security-review.md) | The affected domain workflow |
| Run services, tests, migration or recovery | [Operations](operations/local-operations.md) | Security if operational boundaries change |
| Assign/integrate concurrent agents | [Parallel workstreams](operations/parallel-workstreams.md) | Assigned domain workflow; allocations are in [workstream design](../workstreams/plan.md) |
| Restructure docs, handoffs or plans | [Documentation](documentation/documentation-workflow.md) | Skill maintenance only if workflow guidance changes |
| Maintain this library/package | [Skill maintenance](documentation/skill-maintenance.md) | Documentation for links and ownership |

A narrow task does not need architecture history, every financial manual and the
operations workflow just to find one command. Load more context when the actual
code reveals another boundary.

## Maintenance contract

Keep these standard sections so the existing validator can inspect every workflow:
Purpose; When to use; When NOT to use; Prerequisites; Inputs; Outputs; Workflow;
Acceptance criteria; Common mistakes; Do not do; Related skills; References.
Empty filler is not useful: one clear sentence is enough where appropriate.

Link deep domain guidance and commands instead of copying them. Update a workflow
when its reusable behavior changes; do not edit every file just to refresh dates.
Preserve source/review/privacy invariants and exact evidence distinctions in their
owning workflow. Archive superseded material, retain useful source references,
and run documentation, skill and ownership checks from the runbook.

[The audit](skill-system-audit.md) records reviewed families, changes, retained
references and validation limits. Parallel agents propose library changes in their
own evidence directories; only the coordinator updates shared workflow files.
