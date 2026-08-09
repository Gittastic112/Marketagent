# Documentation Map

**Architecture:** current documents stay small and describe present reality.
Detailed dated evidence and superseded plans live in `archive/`.

## Start Here

| Order | Document | Purpose |
|---:|---|---|
| 1 | [`HANDOFF.md`](HANDOFF.md) | Safe start, latest boundary, commands, and next task |
| 2 | [`00-current-state.md`](00-current-state.md) | Current product truth, baseline, and limitations |
| 3 | [`02-architecture.md`](02-architecture.md) | Runtime boundaries, flows, ownership, and debt |
| 4 | [`roadmaps/product-roadmap.md`](roadmaps/product-roadmap.md) | Ordered priorities and acceptance gates |
| 5 | [`roadmaps/feature-register.md`](roadmaps/feature-register.md) | Built/partial/prototype/not-built status |

Agents should not need archived documents for routine work.

## Core Product Docs

| Document | Owns |
|---|---|
| [`01-product-brief.md`](01-product-brief.md) | Product purpose, user, principles, and non-goals |
| [`03-database-schema.md`](03-database-schema.md) | Persistence domains, relationships, and migration rules |
| [`04-data-sources-and-ingestion.md`](04-data-sources-and-ingestion.md) | Provider, source, freshness, ingestion, and provenance rules |
| [`05-scoring-framework.md`](05-scoring-framework.md) | Deterministic event scoring |
| [`06-security-threat-model.md`](06-security-threat-model.md) | Threat boundaries and public-release blockers |
| [`07-local-development.md`](07-local-development.md) | Environment, login, Docker, testing, backup, and troubleshooting |
| [`08-execution-runbook.md`](08-execution-runbook.md) | Task workflow and validation commands |
| [`09-beginner-glossary.md`](09-beginner-glossary.md) | Finance and technical terminology |
| [`12-assumption-methodology-engine.md`](12-assumption-methodology-engine.md) | Assumption-method selection contract |
| [`agent_capabilities_and_limitations.md`](agent_capabilities_and_limitations.md) | Product trust boundary |

## Specialized References

| Folder | Purpose |
|---|---|
| [`valuation-agent/`](valuation-agent/) | Current application-to-knowledge-base valuation map |
| [`skills/`](skills/) | Reusable project workflows for agents |
| [`../damodaran_knowledge_base_v1/`](../damodaran_knowledge_base_v1/) | Canonical valuation doctrine and audited raw corpus |

## Archive

[`archive/`](archive/) contains dated checkpoints, cumulative handoffs, old
assessments, superseded execution plans, research, and prior agent instructions.
Archived files preserve historical wording and may contain obsolete paths or
status claims. They do not override current docs or code.

## Maintenance Rules

1. Code and tests beat documentation.
2. Keep one current document per concern.
3. Replace current status; do not append chronological status sections.
4. Archive detailed shipped evidence under `archive/checkpoints/YYYY/`.
5. Archive superseded plans instead of keeping multiple active roadmaps.
6. Use relative links and run `python3 scripts/check_docs.py`.
7. Update `HANDOFF.md`, current state, and the feature register when reality changes.
