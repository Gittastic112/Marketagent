# Market Intelligence Engine

A local workspace for equity research, valuation, and portfolio tracking.
Follow a claim from its source document to reviewed financial inputs, a valuation
assumption, and the holdings it affects.

The product is an implemented research/demo application. Source coverage and
review quality vary by workflow. It is not ready for public hosting or automated
trading. [Current status and dated validation](docs/current-state.md) ·
[Known limitations](docs/limitations.md)

## What you can do

| Workflow | What the application supports |
|---|---|
| Review the day | Inspect source-linked events, portfolio exposure, and a deterministic Daily Brief with visible coverage limits |
| Research a company | Store filings and private research, review extracted financial candidates, and maintain thesis notes with evidence |
| Build a valuation | Review inputs, save versioned DCF models, and inspect scenarios, sensitivities, reverse DCF, and reviewed peer comparisons |
| Track a portfolio | Record activity and inspect dated snapshots, returns, attribution, and risk with missing-input warnings |
| Inspect data quality | See provider configuration, processing failures, freshness, and review state in Data Health |

Calculations run in the backend. Optional AI can propose interpretations through
explicit consent and review gates. Facts, source summaries, calculations, user
assumptions, estimates, AI interpretations, and **Mock Data** remain distinct.

## Run locally

Prerequisite: Docker with Compose. Follow the
[setup guide](docs/local-development.md) to configure private local credentials,
a session secret, and any providers you intend to use. There is no default login.
For a **new installation**, from the repository root:

~~~bash
cp -n .env.example .env
# Fill in the required settings privately before starting.
docker compose up --build -d
docker compose ps
curl --fail http://localhost:8000/api/readiness
~~~

Open [localhost:3000](http://localhost:3000). A fresh installation does not include
the developer's research database. Provider features require their own
configuration and source review. Existing installations should use their verified
[runtime configuration](docs/operations.md#select-the-installed-local-stack).

## How it is built

Next.js 16 and React render the research workspace. FastAPI owns APIs and
deterministic calculations. PostgreSQL 16 stores research and review history;
SQLAlchemy and Alembic manage persistence and migrations. Docker Compose runs the
local services. [Architecture](docs/architecture.md)

| Directory | Purpose |
|---|---|
| [backend/](backend/README.md) | API, calculations, ingestion, persistence, migrations, and tests |
| [frontend/](frontend/README.md) | Pages, components, authenticated API clients, and browser tests |
| [scripts/](scripts/README.md) | Verification, data tooling, backup, and recovery commands |
| [data/](data/README.md) | Versioned runtime references, contract fixtures, and review receipts |
| [damodaran_knowledge_base_v1/](damodaran_knowledge_base_v1/INDEX.md) | Valuation doctrine and the immutable source corpus |
| [docs/](docs/README.md) | Product, architecture, setup, operations, and development references |

Use the [code map](docs/code-map.md) to locate a feature's owning files, or the
[route inventory](docs/route-inventory.md) to find a screen.

## Development and verification

Read [contribution guidance](.github/CONTRIBUTING.md) and the
[execution runbook](docs/execution-runbook.md). The
[CI workflow](.github/workflows/ci.yml) checks repository integrity, locked
dependencies, containers, backend/frontend behavior, browser workflows, and recovery.
Passing tests does not establish financial accuracy or live-provider coverage.

Local credentials, databases, backups, and generated reports belong outside Git.
The repository currently has no project license; included third-party material
retains its own source and rights. See the [security policy](.github/SECURITY.md)
and [data boundary](data/README.md) before sharing or redistributing material.
