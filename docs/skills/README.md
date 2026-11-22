# Project workflows

Choose the guide that matches the change. The [agent rules](../../AGENTS.md) govern the repository, the [code map](../code-map.md) identifies files and tests, and the [runbook](../execution-runbook.md) owns commands.

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

## Maintaining a workflow

Use the sections required by the [workflow validator](../../scripts/validate_project_skills.py) and link to the owner of each command or product rule. The [maintenance guide](documentation/skill-maintenance.md) covers adding or retiring a workflow. The [October 5 audit](../archive/assessments/project-workflows-2026-10-05.md) preserves earlier decisions.

These guides are repository documents. The [security review package](../../skills/security-review/SKILL.md) is also available for installation. Check the session’s available skills before relying on an installed package.
