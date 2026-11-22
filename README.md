# Market Intelligence Engine

Marketagent is a local equity research workspace. Follow a filing to a reviewed financial input, a valuation assumption and the holdings it affects. The personal research release covers four selected companies. A new installation starts with its own database.

| What you came to do | Start here |
|---|---|
| Use the installed app | [Open Today](http://127.0.0.1:3000) · [Research guide](docs/user-guide.md) |
| Set up a new installation | [Local configuration and sign-in](docs/local-development.md#first-time-configuration) |
| Maintain an existing installation | [Select the installed stack](docs/operations.md#select-the-installed-local-stack) |
| Continue development or review | [Agent instructions](AGENTS.md) · [Current handoff](docs/HANDOFF.md) |
| Check the release or find a guide | [Dated verification](docs/current-state.md#dated-validation) · [Documentation index](docs/README.md) |

## Research workflows

- Start on Today with the portfolio snapshot, Daily Brief and active alerts. Inspect a source's publication date, coverage and review state before using it.
- Select a marked stock move to see the close, the previous comparable close and nearby filings. You can pin an observation to a private thesis and record a decision about an assumption. [Chart walkthrough](docs/user-guide.md#inspect-a-price-move-and-pin-a-thesis-note)
- Apply a dated financial revision to a valuation draft. Review the remaining inputs, preview the calculation, then confirm the version with its sources and your reason. [Valuation walkthrough](docs/user-guide.md#review-a-filing-and-valuation)
- Review holdings, activity, dated returns, attribution and risk. Research Lab can run allocations, simulations and reports on supplied returns. Sample holdings are hypothetical. [Portfolio guide](docs/user-guide.md#review-portfolio-and-macro-results) · [Research Lab](docs/adapters/README.md)

Coverage varies by company and provider. Estimates, user assumptions, AI interpretations and Mock Data carry explicit labels. Financial review and private AI consent are separate actions. [Capabilities](docs/roadmaps/feature-register.md) · [Known limits](docs/limitations.md)

## Development

The Next.js frontend calls a FastAPI backend. Calculations run in the backend and PostgreSQL stores research and review history. Docker Compose runs the local services. [Architecture](docs/architecture.md) · [Compose file guide](docker/README.md)

Find a feature's implementation and tests in the [code map](docs/code-map.md#route-a-domain-change). For a contribution, use the [contributor guide](.github/CONTRIBUTING.md) and [test environments](docs/execution-runbook.md#choose-the-right-environment). Remote checks are recorded in [GitHub Actions](https://github.com/Gittastic112/Marketagent/actions/workflows/ci.yml).

Keep credentials, private research databases and backups local. The repository has no project license. Third-party sources retain their own rights. [Security policy](.github/SECURITY.md) · [Data guide](data/README.md) · [Third-party notices](THIRD_PARTY_NOTICES.md)
