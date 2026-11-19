# Documentation

| If you want to… | Start here |
|---|---|
| Use the app | [Today, source review and valuation](user-guide.md) or [inspect a price move and pin a thesis note](user-guide.md#inspect-a-price-move-and-pin-a-thesis-note) |
| Find what shipped, what was tested and what comes next | [Current state](current-state.md#dated-validation), [handoff](HANDOFF.md) and [open gates](roadmaps/completion-tracker.md#milestone-board) |
| Assign public-source research or work on the code | [Knull review rounds and local implementation](workstreams/README.md) and [code map](code-map.md) |

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
| [Geist UI notes](geist-ui.md) | Presentation changes and signed-in browser acceptance |
| [Route inventory](route-inventory.md) | Every frontend source page |
| [API map](reference/api-map.md) | Every backend HTTP router module and its owner |
| [Database schema](database-schema.md) | Persistence domains and migration policy |
| [Data sources](data-sources.md) | Providers, ingestion, freshness, and provenance |
| [Research adapters](adapters/README.md) | Research Lab, concrete adapters, optional profiles, API contracts and remaining integration limits |
| [Security threat model](security.md) | Threats, mitigations, and public-release blockers |
| [Workflow implementation](reference/workflows.md) | Detailed research, valuation, and source-processing flows |
| [Scoring](scoring.md) | Deterministic event scoring |
| [Assumption methodology](assumption-methodology.md) | Selection and review of valuation assumptions |
| [Valuation map](valuation-agent/README.md) | Calculation owners and doctrine references |

## Maintain the project

The [product roadmap](roadmaps/product-roadmap.md) owns delivery order. The [workspace plan](roadmaps/research-workspace-plan.md) owns screen and workflow specifications. The [UI and adapter worklist](roadmaps/ui-adapter-worklist.md) maps the 16 integration packages to their next evidence or implementation requirement. [Review decisions](roadmaps/review-decisions.md) records delegated choices.

The [completion tracker](roadmaps/completion-tracker.md) owns milestone acceptance. The [limitation ledger](limitations.md) names missing company disclosures, provider prerequisites and remaining review boundaries. [Operations](operations.md#essential-retention-policy) owns the single verified recovery set.

The [release-completion round](workstreams/README.md#release-completion-round) gives Pro chats the issuer research, workflow design and independent checks. Local implementers start with the root [AGENTS.md](../AGENTS.md), the [handoff](HANDOFF.md) and the nearest directory instructions. [Task-specific workflows](skills/README.md) cover development and verification.

Put dated proof and superseded documents in the [archive](archive/README.md).
Keep current docs concise, replace stale status, and retain important evidence.
Keep private reports, uploads and local configuration outside publication. Run
`python3 -m unittest scripts.test_check_docs` and `python3 scripts/check_docs.py`
after edits. The checker covers current links, anchors, directory guides, route
coverage, command inventories, migration-head consistency, and onboarding size limits.
