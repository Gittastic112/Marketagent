# Documentation

| Task | First document | Use it to find |
|---|---|---|
| Research a company | [User guide](user-guide.md) | Today, filings, chart pins, thesis decisions and valuation preview |
| Resume work | [Handoff](HANDOFF.md#next-work) | The installed release, deferred publication and next actions |
| Change a feature | [Code map by domain](code-map.md#route-a-domain-change) | The owning backend, screen, client and tests |
| Verify a release claim | [Current state](current-state.md#dated-validation) | Evidence from the installed app, isolated runs and earlier releases |
| Check financial gaps or acceptance | [Limitations](limitations.md#selected-company-review-follow-up) · [Milestone board](roadmaps/completion-tracker.md#milestone-board) | Required original disclosures and the evidence needed to close a milestone |
| Assign work to several chats | [Coordination guide](workstreams/README.md) | Public-source research, independent code review or local implementation |

## Product and research

- [Product brief](product-brief.md) gives the intended use. The [feature register](roadmaps/feature-register.md) describes available, partial and experimental capabilities. The [glossary](glossary.md) defines the terminology.
- [Data sources](data-sources.md) covers acquisition and provenance. The [adapter guide](adapters/README.md) covers configured inputs, operations and Research Lab.
- [Valuation and assumption methods](reference/valuation.md) covers calculations, benchmark priors and source selection. [Event scoring](reference/scoring.md) explains how the app ranks events for review.

## Setup, code and operations

| Need | Owner |
|---|---|
| Fresh install, sign-in or local configuration | [Local development](local-development.md) |
| Operate a running installation, run providers or recover data | [Operations](operations.md) |
| Choose a test environment, build or verify a release | [Execution runbook](execution-runbook.md) |
| Understand runtime boundaries, data flow or permissions | [Architecture](architecture.md) · [Workflow implementation](reference/workflows.md) · [Security](security.md) |
| Look up a screen, HTTP endpoint or database table | [Frontend routes](route-inventory.md) · [Backend API](reference/api-map.md) · [Database schema](database-schema.md) |
| Work on presentation, themes or navigation | [UI guide](geist-ui.md) · [Style ownership](../frontend/styles/README.md) |

## Planning and maintenance

The [planning index](roadmaps/README.md) routes delivery priorities, screen specifications, adapter work and recorded decisions. Start an agent task with the [repository rules](../AGENTS.md). Use the [workflow library](skills/README.md) for a particular kind of change. The [documentation rules](AGENTS.md) cover ownership, archiving and validation.

Historical handoffs, plans and checks live in the [archive](archive/README.md). Earlier workers’ original evidence has a separate [receipt index](workstreams/evidence/README.md).
