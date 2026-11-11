# Documentation

Start with the product and current evidence. Use the detailed references only for
the task at hand. Each subject below has one current owner.

## Understand the product

| Read | Purpose |
|---|---|
| [Product brief](product-brief.md) | Problem, intended user, workflow, and non-goals |
| [Current state](current-state.md) | Delivered behavior and dated validation |
| [Feature register](roadmaps/feature-register.md) | Built, partial, experimental, and unavailable capabilities |
| [Limitations](limitations.md) | Current trust boundaries and unresolved work |
| [User guide](user-guide.md) | Navigate the core research and review workflows |
| [Glossary](glossary.md) | Finance and technical terminology |

## Run and develop

| Read | Purpose |
|---|---|
| [Local setup](local-development.md) | First installation, credentials, providers, and troubleshooting |
| [Execution runbook](execution-runbook.md) | Development, tests, builds, and release checks |
| [Operations](operations.md) | Existing installations, provider runs, credentials, backups, and recovery |
| [Architecture](architecture.md) | Runtime, ownership, authentication, and data flow |
| [Code map](code-map.md) | Repository layout and feature-to-source navigation |
| [Route inventory](route-inventory.md) | Every source page, without implying blanket browser certification |
| [Database schema](database-schema.md) | Persistence domains and migration policy |
| [Data sources](data-sources.md) | Providers, ingestion, freshness, and provenance |
| [Security threat model](security.md) | Threats, mitigations, and public-release blockers |
| [Workflow implementation](reference/workflows.md) | Detailed research, valuation, and source-processing flows |
| [Scoring](scoring.md) | Deterministic event scoring |
| [Assumption methodology](assumption-methodology.md) | Selection and review of valuation assumptions |
| [Valuation map](valuation-agent/README.md) | Calculation owners and doctrine references |

## Maintain the project

The [roadmap](roadmaps/product-roadmap.md) owns priorities. The
[completion tracker](roadmaps/completion-tracker.md) owns acceptance gates, not an
estimate of engineering effort. [Review decisions](roadmaps/review-decisions.md)
retain the basis of delegated choices.

Agents start with [AGENTS.md](../AGENTS.md), [the handoff](HANDOFF.md), the nearest
nested instructions, and the relevant code-map row. Optional
[workflow references](skills/README.md) support specific tasks.
[Workstream coordination](workstreams/README.md) applies only to an explicitly
assigned parallel batch; the historical plan does not launch agents.

Put dated proof and superseded documents in the [archive](archive/README.md).
Keep current docs concise, replace stale status, and retain important evidence.
Local reports and copied helper packages are not publication inputs. Run
`python3 -m unittest scripts.test_check_docs` and `python3 scripts/check_docs.py`
after edits. The checker covers current links, anchors, directory guides, route
coverage, migration-head consistency, and onboarding size limits.
