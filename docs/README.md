# Documentation Map

One current owner per concern. Archived material is historical evidence,
not instructions. Routine work should not require reading the archive.

## Smallest useful starting context

Read [HANDOFF.md](HANDOFF.md) and the nearest AGENTS.md. Search
[code-map.md](code-map.md) for the affected domain and read its matching row,
then open that owner and the specific reference needed below.
For a major architecture change, also read current state and architecture.
Use the roadmap when selecting work, not as evidence that a feature is finished.

| Document | Owns |
|---|---|
| [HANDOFF.md](HANDOFF.md) | Latest boundary and next concrete work; at most 120 lines |
| [00-current-state.md](00-current-state.md) | Product truth and dated validation; at most 180 lines |
| [code-map.md](code-map.md) | Actual source entry points, dependencies and change routing |
| [02-architecture.md](02-architecture.md) | Runtime flows, ownership and compatibility boundaries |
| [roadmaps/product-roadmap.md](roadmaps/product-roadmap.md) | Priorities and acceptance gates |
| [roadmaps/completion-tracker.md](roadmaps/completion-tracker.md) | Percentage requests, ten cumulative milestones, task IDs and evidence gates |
| [Knull: five workstreams](../Knull%28readme%29.md) | Feature-workstream designs, exclusive scopes, detailed phases and completion gates mapped by the tracker |
| [workstreams](workstreams/README.md) | Machine-checked file ownership and per-agent evidence locations |
| [roadmaps/feature-register.md](roadmaps/feature-register.md) | Built/partial/prototype/not-built capability status |
| [agent_capabilities_and_limitations.md](agent_capabilities_and_limitations.md) | Single product and architecture limitation ledger |

## Task-specific references

| Document | Use for |
|---|---|
| [01-product-brief.md](01-product-brief.md) | Product purpose, user and non-goals |
| [03-database-schema.md](03-database-schema.md) | Persistence domains, relationships and migration policy |
| [04-data-sources-and-ingestion.md](04-data-sources-and-ingestion.md) | Providers, freshness, ingestion and provenance |
| [05-scoring-framework.md](05-scoring-framework.md) | Deterministic event scoring |
| [06-security-threat-model.md](06-security-threat-model.md) | Security/privacy boundaries and public-release blockers |
| [07-local-development.md](07-local-development.md) | First-time setup, environment, login and troubleshooting |
| [08-execution-runbook.md](08-execution-runbook.md) | Development, verification and operational commands |
| [09-beginner-glossary.md](09-beginner-glossary.md) | Finance and technical terminology |
| [09-route-inventory.md](09-route-inventory.md) | Source-backed page index, not blanket browser certification |
| [12-assumption-methodology-engine.md](12-assumption-methodology-engine.md) | Assumption-method selection |
| [valuation-agent/README.md](valuation-agent/README.md) | Application valuation and doctrine routing |
| [skills/README.md](skills/README.md) | Task-specific reusable project workflow references |
| [knowledge base](../damodaran_knowledge_base_v1/) | Canonical valuation doctrine and audited source corpus |

## Maintenance

- Code and tests beat docs. Update only the concern whose reality changed.
- Replace current status; archive dated evidence under archive/checkpoints/YYYY.
- Preserve old handoffs under archive/handoffs and superseded plans under
  archive/plans. Archive wording and links may be obsolete.
- Keep one roadmap, completion tracker, feature register, command owner and limitation ledger.
- Keep execution assignments in Knull; do not copy its task lists into status docs.
  Parallel agents propose shared-doc changes in their own evidence; the coordinator
  updates current references after integration.
- Use real relative links. Do not add speculative folder trees or duplicate
  complete instructions into several manuals.
- Run python3 -m unittest scripts.test_check_docs and python3 scripts/check_docs.py.
  CI enforces active links, root Markdown, archive README navigation, nested
  agent guidance, onboarding size budgets, page-inventory completeness and the
  documented source migration head. Historical archive bodies remain
  excluded so their dated wording is not silently rewritten.

Latest foundation verification: [October 10 M01 rollout and browser proof](archive/checkpoints/2026/m01-foundation-complete-2026-10-10.md).
Broader product verification remains separately dated in Current State.
Latest documentation reconciliation: [November 4 supplied delivery report](archive/checkpoints/2026/delivery-report-reconciliation-2026-11-04.md), with reported package checks separated from source inspection and current GitHub evidence.
Latest independent implementation: [November 4 briefing, permissions and release tooling](archive/checkpoints/2026/independent-completion-2026-11-04.md).

[Archive](archive/) contains older instructions, checkpoints, research and plans.
