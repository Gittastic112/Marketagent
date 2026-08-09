# Project Skill Library

This directory is the reusable knowledge layer for future coding agents working on the Market Intelligence Engine. These are project skills, not product features.

Use skills when a task repeats a known workflow, touches risky architecture, or requires project-specific judgment. Code and tests still beat docs.

Cross-skill invariants cover typed source locators, mandatory reporting units,
normalized coverage and reconciliation, valuation source age, traced workbook/PDF
uploads, authenticated binary streaming, processing-run lifecycles, escaped
filing diffs, same-origin multipart writes, and non-secret auth readiness.

## Skills Index

| Skill | Category | Purpose | Use When |
|---|---|---|---|
| [architecture-overview](architecture/architecture-overview.md) | Architecture | Map modules, boundaries, and trusted docs before work starts | Any task spans backend, frontend, database, ingestion, valuation, or docs |
| [documentation-workflow](documentation/documentation-workflow.md) | Documentation | Audit, classify, archive, consolidate, and relink docs safely | Cleaning docs, handoffs, roadmaps, or agent instructions |
| [backend-api-change](backend/backend-api-change.md) | Backend | Change routes/services/schemas/tests without API drift | Adding or modifying backend endpoints or response shapes |
| [frontend-data-state](frontend/frontend-data-state.md) | Frontend | Keep UI honest about loading, empty, stale, mock, partial, and not-configured states | Building or auditing frontend pages/components |
| [data-ingestion-workflow](data-ingestion/data-ingestion-workflow.md) | Data ingestion | Add or debug ingestion while preserving provenance and processing runs | SEC, RSS, provider, manual filing, market data, or macro ingestion work |
| [financial-statement-extraction](data-ingestion/financial-statement-extraction.md) | Data ingestion | Handle text/PDF/workbook/XBRL candidate extraction and review safely | Financial extraction, candidate review, normalized financials, or autofill inputs |
| [valuation-workflow](valuation/valuation-workflow.md) | Valuation | Build valuation features with deterministic formulas and source-labeled assumptions | DCF, WACC, scenarios, sensitivity, reverse DCF, FCFE/DDM, relative valuation |
| [market-intelligence-workflow](market-intelligence/market-intelligence-workflow.md) | Market intelligence | Build evidence, scoring, alert, thesis, narrative, and portfolio-impact flows | Event extraction, alerts, evidence, daily brief, research workspace, thesis impact |
| [security-review](security/security-review.md) | Security | Review secrets, external input, APIs, AI, and private financial data risks | Any task touches external data, files, AI, auth, broker, exports, or deployment |
| [local-operations](operations/local-operations.md) | Operations | Run Docker, migrations, tests, and troubleshooting safely | Local setup, test failures, Alembic issues, service health, handoff verification |
| [skill-maintenance](documentation/skill-maintenance.md) | Documentation | Create, update, archive, and validate project skills | Adding or changing reusable project workflows |

## Recommended Reading Order

1. [architecture-overview](architecture/architecture-overview.md)
2. [documentation-workflow](documentation/documentation-workflow.md) when changing docs or handoffs
3. [security-review](security/security-review.md) before external inputs, AI, imports, or credentials
4. Task-specific skill:
   - backend -> [backend-api-change](backend/backend-api-change.md)
   - frontend -> [frontend-data-state](frontend/frontend-data-state.md)
   - ingestion -> [data-ingestion-workflow](data-ingestion/data-ingestion-workflow.md)
   - financial extraction -> [financial-statement-extraction](data-ingestion/financial-statement-extraction.md)
   - valuation -> [valuation-workflow](valuation/valuation-workflow.md)
   - market intelligence -> [market-intelligence-workflow](market-intelligence/market-intelligence-workflow.md)
5. [local-operations](operations/local-operations.md) for verification and handoff
6. [skill-maintenance](documentation/skill-maintenance.md) when editing this skill library

## Skill Format

Every project skill uses:

- Purpose
- When to use
- When NOT to use
- Prerequisites
- Inputs
- Outputs
- Workflow
- Acceptance criteria
- Common mistakes
- Do not do
- Related skills
- References

## Maintenance Rules

- Keep skills concise. Put deep reference material in canonical docs, not in skills.
- Update skills when a repeated workflow changes.
- Archive stale skills rather than deleting them.
- Do not let skills claim a capability works unless code and tests support it.
- Prefer root `AGENTS.md` for hard rules and `docs/skills` for reusable workflows.

See [skill-system-audit.md](skill-system-audit.md) for the audit that produced this library.
