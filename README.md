# Market Intelligence Engine

Local-first equity research, valuation and portfolio tracking. The app connects
source documents, reviewed financials, events, thesis notes, assumptions and
portfolio exposure. It is not a trading bot or a source of buy/sell advice.

## Start here

- [Current status](docs/00-current-state.md): what is implemented and verified.
- [Code map](docs/code-map.md): where changes belong.
- [Agent rules](AGENTS.md) and [handoff](docs/HANDOFF.md): safe development entry.
- [Documentation index](docs/README.md): task-specific references.
- [Completion tracker](docs/roadmaps/completion-tracker.md): ten cumulative 10%
  milestones, exact task IDs, dependencies and acceptance gates.
- [Next five workstreams](Knull%28readme%29.md): independent assignments, file
  ownership, acceptance gates and integration procedure.
- [Limitations](docs/agent_capabilities_and_limitations.md): one current ledger.

## Run locally

Configure the root environment using [.env.example](.env.example), including
local credentials, a session secret and SEC contact identity. Never overwrite
an existing .env or commit secrets. See [local setup](docs/07-local-development.md).

From the repository root:

~~~bash
docker compose up --build -d
docker compose ps
curl --fail http://localhost:8000/api/readiness
~~~

The frontend is at http://localhost:3000. Backend liveness is /api/health;
readiness also checks the database and migrations. pgAdmin uses the opt-in admin
profile; Daily Brief and valuation-source workers use the automation profile.

This is not public-deployment-ready. Checked-in Compose ports bind 127.0.0.1;
inspect running container bindings because older containers can retain previous
settings. Localhost bindings do not establish production security.

## Develop and verify

The supported runtime uses production-built Next.js and FastAPI images.
docker-compose.dev.yml enables source mounts and reloaders. Do not assume tests
inside an old production container exercise edited source.

[The runbook](docs/08-execution-runbook.md) owns source-mounted backend tests,
frontend tests/type checking, production builds, browser checks, migrations,
and safe operational commands. [CI](.github/workflows/ci.yml) runs documentation,
secret, workflow, release and browser gates.

No source datasets, user database, credentials, or investment assumptions should
be changed merely to make a test pass. Synthetic fixtures must say Mock Data.

## Repository boundaries

| Area | Owns |
|---|---|
| [backend](backend/) | FastAPI routes, contracts, deterministic services, persistence, providers and tests |
| [frontend](frontend/) | App Router pages, UI, server-only auth client and domain browser APIs |
| [scripts](scripts/) | Maintained verification and operations; inspect side effects before running |
| [data](data/) | Runtime source assets and mirrored versioned datasets |
| [knowledge base](damodaran_knowledge_base_v1/) | Separate audited valuation doctrine and immutable raw sources |
| [docs](docs/) | Current architecture, setup, workflows and categorized historical evidence |
| [workstream coordination](docs/workstreams/) | Exclusive edit ownership and per-agent evidence; shared docs have one coordinator |

The dependency manifests and exact entry points are linked in the code map.
Old root debug scripts, generated repo_map.txt and archived plans are not the
current development workflow. Do not delete untracked material without checking
its ownership and purpose.

Company actuals, user assumptions, benchmark priors, calculations and AI
interpretations must remain distinguishable. Stored sources and review gates
come before generated conclusions.
