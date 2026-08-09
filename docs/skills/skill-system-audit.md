# Skill System Audit

Last updated: 2026-07-22

This audit records existing explicit skills and implicit reusable workflows found in the project docs. It is a planning artifact for the project skill library in `docs/skills/`.

## Explicit Skills

| Name | Location | Purpose | Status | Used by | Redundant? | Needs update? | Should merge with another? |
|---|---|---|---|---|---|---|---|
| security-review | `skills/security-review/SKILL.md` | Checklist for secrets, SSRF, untrusted rendering, CSV injection, and external API test isolation | Existing, upgraded this pass | Coding agents doing security-sensitive changes | No | Yes, original frontmatter used a space/capitalized name and lacked inputs/outputs/acceptance criteria | Link to `docs/skills/security/security-review.md` as canonical project workflow |

## Implicit Skills Extracted

| Name | Source docs | Purpose | Status |
|---|---|---|---|
| architecture-overview | `AGENTS.md`, `docs/02-architecture.md`, `docs/HANDOFF.md` | Understand module boundaries before changing backend/frontend/data flow | Extracted |
| documentation-workflow | `docs/README.md`, `docs/HANDOFF.md`, recent cleanup workflow | Audit, classify, archive, and relink docs safely | Extracted |
| backend-api-change | `AGENTS.md`, `docs/02-architecture.md`, `docs/08-execution-runbook.md` | Make backend API changes without schema/route/service drift | Extracted |
| frontend-data-state | `AGENTS.md`, `docs/00-current-state.md`, frontend data-state helpers | Keep UI honest about loading, error, stale, partial, mock, and not-configured states | Extracted |
| data-ingestion-workflow | `docs/04-data-sources-and-ingestion.md`, `docs/06-security-threat-model.md` | Add or debug ingestion while preserving provenance and processing runs | Extracted |
| financial-statement-extraction | `docs/HANDOFF.md`, `docs/00-current-state.md`, `docs/04-data-sources-and-ingestion.md` | Handle filing text/XBRL candidates, review, promotion, and normalized financials safely | Extracted |
| valuation-workflow | `docs/valuation-agent/README.md`, `docs/12-assumption-methodology-engine.md`, `damodaran_knowledge_base_v1/AGENTS.md` | Build valuation features with deterministic formulas and source-labeled assumptions | Extracted |
| market-intelligence-workflow | `docs/01-product-brief.md`, `docs/05-scoring-framework.md`, `docs/roadmaps/product-roadmap.md` | Build event, evidence, scoring, alert, thesis, and portfolio-impact features | Extracted |
| local-operations | `docs/07-local-development.md`, `AGENTS.md`, `docs/HANDOFF.md` | Run Docker, migrations, tests, and local troubleshooting safely | Extracted |
| skill-maintenance | Skill authoring instructions, this audit, `docs/skills/README.md` | Maintain and validate the project skill library itself | Extracted |

## Duplicate or Stale Skill Material

| Material | Issue | Resolution |
|---|---|---|
| Archived prompts in `docs/archive/agent-instructions/codex-prompts.md` | Old path names and old phase assumptions | Keep archived; do not use as active skills |
| `docs/archive/needs-review/design-brief.md` | Large and partially stale frontend/API plan | Keep as historical context only |
| `docs/archive/needs-review/world-class-expansion-supplement-master-plan.md` | Overlaps active roadmap and capability audit | Keep needs-review; do not drive implementation directly |
| Long valuation plans | Valuable but too large for routine task execution | Keep as references; skills point to specific docs only when needed |

## Missing Skills Added

- `docs/skills/architecture/architecture-overview.md`
- `docs/skills/documentation/documentation-workflow.md`
- `docs/skills/backend/backend-api-change.md`
- `docs/skills/frontend/frontend-data-state.md`
- `docs/skills/data-ingestion/data-ingestion-workflow.md`
- `docs/skills/data-ingestion/financial-statement-extraction.md`
- `docs/skills/valuation/valuation-workflow.md`
- `docs/skills/market-intelligence/market-intelligence-workflow.md`
- `docs/skills/security/security-review.md`
- `docs/skills/operations/local-operations.md`
- `docs/skills/documentation/skill-maintenance.md`

## Open Follow-Up

- The financial extraction, frontend data-state, valuation, and security skills were updated on 2026-07-22 for evidence locations, reporting-unit review, normalized coverage, source-age review, traced workbook uploads, same-origin multipart writes, and non-secret auth readiness.
- These are project documentation skills, not installed Codex global skills. If desired later, promote the most reusable ones into actual `skills/<name>/SKILL.md` folders.
- The root `AGENTS.md` should remain the enforcement layer. `docs/skills` should remain the reusable workflow library.
