# Backend Rules

Read the [root rules](../AGENTS.md). This file adds backend-specific guidance.

## Entry points and dependency direction

- app/main.py assembles FastAPI, middleware, errors, liveness, and readiness.
- app/api/routes.py registers authenticated route groups.
- app/api/dependencies.py resolves signed identity and owned resources.
- app/api/routers owns HTTP orchestration. Services own multi-step workflows.
- app/models and app/db own SQLAlchemy persistence; Alembic owns schema evolution.
- app/schemas/valuation_inputs.py owns DCF input validation.
- app/schemas/valuation_outputs.py owns pure calculation output contracts.
- app/schemas/valuation.py assembles saved valuation responses.
- app/schemas/portfolio.py owns pure portfolio request/response contracts.
- app/schemas/common.py owns ApiResponse, ApiMeta and ApiErrorDetail. Import it
  directly when only the shared envelope is needed; do not load the legacy facade.
- app/api/schemas.py is a compatibility facade over the pure domain contracts.
  Add fields in the owning app/schemas module, not the facade.
- Pure calculation contracts must not load HTTP, services, or ORM. Services
  import their narrow contracts directly.
- Providers mostly live in app/providers. The existing market-data factory,
  provider contracts and persistence live in app/services/market_data. Do not
  create a competing factory under the proposed-but-absent provider path.
- app/services/market_data/ingestion.py owns audited quote/history transactions.
  Both market routes delegate here; private price alerts require the caller's owner.

[Code map](../docs/code-map.md) links domain routes, services, and test entry points.
Move one domain group at a time; do not rename routes or migrations cosmetically.

## API contracts

New routes use ApiResponse with data, meta, and errors. Preserve status, source,
last_updated, is_stale, is_mock, warnings, confidence, and request context.
Use stable public error codes with safe messages. Never expose tracebacks,
credentials, environment values, or raw rejected private inputs.

Resolve owned parent resources before child evidence. Do not use a global list
and filter ownership in the browser. Preserve existing public health/readiness
exceptions and the route-security inventory.

Read-time reconciliation must be detached and non-writing. Keep deterministic
reads separate from provider fetches, AI generation, and review mutations.
Schema names must be unique: StoredFinancialMetricRead includes record metadata;
FinancialMetricRead is the legacy chart response contract.

## Persistence and ingestion

- Inspect models, migration history, current schema docs, and tests before writes.
- Append migrations. Never edit historical migrations to repair a live database.
- Updates that span evidence and revisions must be atomic and owner-scoped.
- Version checks, preview hashes, receipts, and reviewed-state invalidation are
  trust boundaries, not optional UI conveniences.
- Record external actions in Processing Runs with source/company scope, start
  and finish, status, fetched/created/duplicate/error counts, sanitized failures,
  and metadata. Never hide an ingestion failure.
- Keep provider configuration, last attempts/success/failure, rate limits,
  freshness, and coverage explicit. Missing configuration is not mock success.
- Do not add social scraping, broker sync, real-time feeds, or new workbook
  parsers without an approved consuming workflow and source-access basis.

## Valuation invariants

Read the [valuation application map](../docs/valuation-agent/README.md) and
task-specific [valuation workflow](../docs/skills/valuation/valuation-workflow.md)
before altering finance behavior. The separate knowledge base owns doctrine.

Preserve the established pipeline:
Story -> revenue -> margins -> reinvestment -> ROIC -> WACC -> terminal value
-> equity bridge -> sensitivity -> reverse DCF.

- FCFF = EBIT × (1 - tax rate) - reinvestment.
- Default reinvestment = change in revenue / sales-to-capital.
- ROIC = NOPAT / invested capital, using the engine's documented timing.
- Enterprise value plus cash/non-operating assets less debt, minority interests,
  preferred stock and employee options yields equity value; diluted shares yield
  per-share value. Do not double count bridge items.
- FCFF uses WACC; FCFE uses cost of equity. Keep intrinsic value and pricing apart.
- Keep all existing input fields, currency/scale, assumptions and provenance.
  Missing and explicit zero values are distinct.
- Preserve warnings for inconsistent terminal growth, high terminal dependence,
  unsupported WACC, growth without reinvestment, weak ROIC, missing/diluted shares,
  and incomplete scenario/reverse analysis. Never silence warnings for neat output.
- Test calculations, validation, diagnostics, serialization, ownership,
  historical reads, atomic failure, and scenario model selection when affected.
- Formula changes are not part of routine file extraction or import cleanup.

## Market regime and decision workflows

Regime values describe market structure/support, not buy/sell signals. Preserve
score, drivers, blockers, warnings, sources, formula, timestamps, and confidence.
Do not hardcode planning weights into HTTP/UI code; inspect the existing engine.
Unsupported options/liquidity/volume/breadth provider coverage stays manual.

## Validation

Use the source-mounted commands in the [runbook](../docs/08-execution-runbook.md).
The normal production container does not mount backend code, so running pytest
there without rebuilding can test old source. Test fixtures use isolated SQLite;
migration-specific tests cover PostgreSQL behavior where required.

Run test_schema_boundaries.py after moving contracts. Run route-security,
response-envelope and affected API tests after router changes. Compare OpenAPI
when moving public schemas. No live provider calls in deterministic tests.
