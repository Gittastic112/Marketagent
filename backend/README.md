# Backend

FastAPI application for source-backed research, deterministic valuation, and
portfolio workflows. Start at [app/main.py](app/main.py); route groups are
registered in [app/api/routes.py](app/api/routes.py).

| Directory | Owns |
|---|---|
| [app/api](app/api/) | Routes, authentication dependencies, errors, and serialization |
| [app/schemas](app/schemas/) | Domain contracts and calculation inputs/outputs |
| [app/services](app/services/) | Calculations, ingestion, review, and application workflows |
| [app/models](app/models/), [app/db](app/db/) | Persistence and database sessions |
| [app/providers](app/providers/) | External adapters and bounded transport |
| [app/core](app/core/) | Settings, identity, logging, and request limits |
| [app/workers](app/workers/) | Optional schedules and isolated parsing/provider jobs |
| [alembic](alembic/) | Ordered database migrations |
| [tests](tests/) | Behavior tests and isolated fixtures |
| [scripts](scripts/README.md) | Inventoried operational/source-review commands and their side effects |

The [API map](../docs/reference/api-map.md) lists every HTTP router module.
The [code map](../docs/code-map.md) links domain owners and tests.
[Backend rules](AGENTS.md) explain import, ownership, and valuation invariants.

Use the [runbook](../docs/execution-runbook.md#focused-and-full-source-verification)
for source-mounted tests. Production containers do not mount edited source;
running tests in an old image does not validate a new checkout.
Runtime and test dependencies have separate hash-locked requirements.

[Local setup](../docs/local-development.md) owns configuration.
[Operations](../docs/operations.md) owns provider runs and recovery.
Scripts that stage, promote, seed, or restore data are not setup prerequisites.
