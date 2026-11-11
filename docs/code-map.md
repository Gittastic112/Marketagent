# Code Map

Use this to find the owner of a change. It is not a generated listing of every
file. Runtime flows live in [architecture](architecture.md), commands in the
[runbook](execution-runbook.md), status in [current state](current-state.md).
Start with the compact JSON map in [AGENTS.md](../AGENTS.md). For a narrow change:

~~~bash
rg -n '^\| Financial review ' docs/code-map.md
~~~

Inspect only the returned owner and tests. Do not read every domain by default.

For assigned parallel work, [workstream design](workstreams/plan.md) defines the batch and
[ownership.tsv](workstreams/ownership.tsv) defines exclusive writes. The entries
below locate code; they do not grant another agent permission to edit it.

## Repository layout

| Path | Purpose |
|---|---|
| [backend](../backend/README.md) | FastAPI application, domain logic, migrations, and backend tests |
| [frontend](../frontend/README.md) | Next.js pages, UI, clients, and browser tests |
| [scripts](../scripts/README.md) | Maintained checks, operational commands, and explicit data tools |
| [data](../data/README.md) | Runtime references, contract fixtures, certification inputs, review receipts |
| [damodaran_knowledge_base_v1](../damodaran_knowledge_base_v1/INDEX.md) | Independent doctrine, immutable sources, catalog, and audit tools |
| [docker/postgres](../docker/postgres/) | Narrow PostgreSQL image build context |
| [docs](README.md) | Current guides, planning, workflow references, and historical archive |
| [skills](../skills/README.md) | Maintained project security-review package; copied tool packages stay local |
| [.github](../.github/) | CI and contribution/security policies |
| .codex, .vscode | Agent/editor configuration, separate from application runtime; preserve local overrides |
| [docker-compose.yml](../docker-compose.yml) | Normal local services and persistent volumes |
| [dev](../docker-compose.dev.yml), [test](../docker-compose.test.yml), [tools](../docker-compose.tools.yml) overrides | Source reload, offline backend tests, isolated repository-tool checks |
| [E2E](../docker-compose.e2e.yml), [recovery](../docker-compose.recovery.yml) | Separate disposable verification environments |
| [alembic.ini](../alembic.ini), [pyproject.toml](../pyproject.toml) | Migration and Python test/type configuration |
| [.gitignore](../.gitignore), [.rgignore](../.rgignore), [.dockerignore](../.dockerignore), [.gitattributes](../.gitattributes) | Publication, search, build-context, and file-type boundaries |
| README.md, AGENTS.md | Product entry and development rules; detailed plans live under docs |

Local output, backups, scratch, tmp, installed dependencies, and private settings
are distinct from the published source tree. Git ignores control discovery, not
permission to delete evidence.

## Runtime and dependencies

| Concern | Entry point | Responsibility |
|---|---|---|
| FastAPI | [main.py](../backend/app/main.py), [routes.py](../backend/app/api/routes.py) | Middleware, errors, health/readiness, authenticated route registration |
| Backend identity | [dependencies.py](../backend/app/api/dependencies.py), [route inventory](../backend/app/api/route_security.py) | Signed identity, owner scoping, intentional public exceptions |
| Frontend entry | [layout.tsx](../frontend/app/layout.tsx), [page.tsx](../frontend/app/page.tsx), [proxy.ts](../frontend/proxy.ts) | App shell, dashboard, sign-in redirect; dashboard router returns owned portfolio choices, funded default and latest stored snapshot |
| Server requests | [server-api.ts](../frontend/lib/server-api.ts), [server-auth.ts](../frontend/lib/server-auth.ts) | Runtime connection boundary, verified cookies, signed backend identity |
| Server actions | [domain actions](../frontend/app/actions/), [compatibility exports](../frontend/app/actions.ts) | Eight workflow owners; shared validation/error/revalidation helpers remain server-only; server-actions.test.ts verifies payloads, failures, redirects and versioned draft promotion |
| Basic form recovery | [retained action form](../frontend/components/retained-action-form.tsx) | Serializes saves, retains entries on failure, invalidates unmounted requests and confirms only completed actions; manual-research-controls and decision-journal browser checks |
| Browser requests | [proxy route](../frontend/app/api/backend/[...path]/route.ts), [transport.ts](../frontend/lib/api/transport.ts) | Same-origin authentication; HTTP, multipart, binary and parsing behavior |
| Shared response | [contract.ts](../frontend/lib/api/contract.ts), [common.py](../backend/app/schemas/common.py), [backend facade](../backend/app/api/schemas.py) | Pure envelopes, shared error identity, legacy compatibility exports |
| Database | [session.py](../backend/app/db/session.py), [models](../backend/app/models/), [migrations](../backend/alembic/versions/) | SQLAlchemy unit of work, persistence, ordered schema changes |
| Workers | [daily_brief_scheduler.py](../backend/app/workers/daily_brief_scheduler.py), [valuation_source_scheduler.py](../backend/app/workers/valuation_source_scheduler.py) | Separate deterministic briefs and queued public-source/draft refreshes; no external AI |
| Configuration | [.env.example](../.env.example), [config.py](../backend/app/core/config.py) | Documented variable names and backend settings; never read secrets into docs |
| Runtime build | [Compose](../docker-compose.yml), [dev override](../docker-compose.dev.yml), [backend Dockerfile](../backend/Dockerfile), [frontend Dockerfile](../frontend/Dockerfile), [PostgreSQL Dockerfile](../docker/postgres/Dockerfile) | Python 3.14, Node 24, pinned PostgreSQL 16 binaries; signed dated OS updates in all three builds; source mounts opt-in |
| Dependency manifests | [requirements](../backend/requirements.txt), [package.json](../frontend/package.json), [lockfile](../frontend/package-lock.json) | Backend pinned dependencies; frontend declared ranges and exact resolved tree |

Backend [test requirements](../backend/requirements-test.txt) include the runtime
requirements plus pytest. The default Docker target excludes backend test fixtures;
unit/E2E builds select the test target. Do not prune another package solely because
a text search finds no import; extras, tooling and dynamic imports need checking too.

## Route a domain change

| Work | Start here | Contract/client and verification |
|---|---|---|
| Saved DCF and scenarios | [valuation router](../backend/app/api/routers/valuations.py), [DCF](../backend/app/services/dcf.py), [scenarios](../backend/app/services/scenario_engine.py) | [inputs](../backend/app/schemas/valuation_inputs.py), [outputs](../backend/app/schemas/valuation_outputs.py), [saved responses](../backend/app/schemas/valuation.py), [frontend API](../frontend/lib/api/valuation.ts); test_dcf, test_scenario_integrity, test_implied_pricing_integrity |
| Valuation AI explanations | [saved basis](../backend/app/services/valuation_ai_basis.py), [AI route](../backend/app/api/routers/ai.py), [contracts](../backend/app/schemas/valuation_ai.py) | Exact assumption ID/time and output hash, diagnostics before memo generation, provenance and historical-read status; test_valuation_ai_basis and valuation-explanation browser checks |
| Event AI interpretation | [mapper](../backend/app/services/dcf_variable_mapper.py), [research route](../backend/app/api/routers/ai_research.py), [panel](../frontend/components/dcf-impact-predictor.tsx) | Explicit disclosure, exact event basis, bounded structured output, policy checks and pending review; test_event_ai_workflow and event-ai-workflow browser checks |
| Core DCF zero/default handling | [DCF](../backend/app/services/dcf.py), [diagnostics](../backend/app/services/diagnostics_engine.py) | [zero/default regressions](../backend/tests/test_dcf_zero_defaults.py) cover forecasts, terminal math, sensitivity centers/funding inputs, invalid-zero diagnostics and persisted results; adjacent engine defaults are separate |
| Supplementary equity estimates | [FCFE/DDM and payout service](../backend/app/services/fcfe_ddm_engine.py) | [integrity regressions](../backend/tests/test_fcfe_ddm_integrity.py); complete finite cash flows, explicit equity rate/growth/shares, zero preservation, method-specific availability and currency-aware payout diagnostics |
| Specialized valuation | [excess-return engine](../backend/app/services/financial_services_engine.py), [distressed engine](../backend/app/services/distressed_engine.py) | [specialized integrity tests](../backend/tests/test_specialized_valuation_integrity.py); explicit equity inputs, finite results, consistent bridge/gaps, model-specific scenarios and persisted diagnostics |
| Input-preserving resaves | [version service](../backend/app/services/assumption_versions.py), [form adapter](../frontend/lib/form-payloads.ts) | DcfAssumptionVersionWrite adds the base ID/time; test_assumption_version_integrity covers omission, clears, conflicts and rollback |
| Reverse DCF | [saved-basis service](../backend/app/services/reverse_dcf_service.py), [solver](../backend/app/services/reverse_dcf_engine.py), [panel](../frontend/components/valuation/reverse-dcf-panel.tsx) | test_reverse_dcf_integrity and reverse-dcf-state tests; bounded, non-writing solves from saved inputs |
| Real Options | [owned route](../backend/app/api/routers/real_options.py), [saved-basis service](../backend/app/services/saved_real_options.py), [panel](../frontend/components/valuation/real-options-panel.tsx) | [pure contracts](../backend/app/schemas/real_options.py), [client](../frontend/lib/api/real-options.ts), test_saved_real_options and real-options-state tests; total common-equity units, saved shares/currency, no writes |
| Saved output UI | [workspace](../frontend/components/advanced-workspace.tsx), [cards](../frontend/components/valuation/saved-output-cards.tsx) | [trust/display helper](../frontend/lib/valuation-output-state.ts), scenario-display and implied-pricing helpers/tests |
| Saved projections and specialized forms | [projections](../frontend/components/valuation/saved-projections.tsx), [column mapping](../frontend/lib/valuation-projections.ts) | valuation-projections and scenario-display tests; bank equity labels, relative forecast years and model-specific validation |
| Valuation setup | [draft service](../backend/app/services/valuation_setup_draft.py), [autofill](../backend/app/services/assumption_autofill_engine.py), [unit policy](../backend/app/services/valuation_input_units.py) | [draft API](../frontend/lib/api/valuation-drafts.ts), [review UI](../frontend/components/valuation/autofill-draft-review.tsx); model-specific review, source-signature promotion gates, full-unit conversions and valuation-draft browser workflow |
| Industry allocation UI | [mapping card](../frontend/components/valuation/industry-mapping-card.tsx) | [Pending-request browser checks](../frontend/e2e/valuation-loading.spec.ts); desktop/mobile loading contrast and recovery after the request completes |
| Source-to-valuation automation | [source adapters](../backend/app/services/valuation_source_inputs.py), [refresh queue](../backend/app/services/valuation_source_refresh.py), [worker](../backend/app/workers/valuation_source_scheduler.py) | [owned router](../backend/app/api/routers/valuation_refresh.py), [contracts](../backend/app/schemas/valuation_refresh.py), [browser client](../frontend/lib/api/valuation-refresh.ts), [panel](../frontend/components/valuation/source-refresh-panel.tsx); owner-scoped queued cancellation uses the worker lock; test_valuation_source_inputs, test_valuation_source_refresh, test_sec_xbrl_extractor and valuation-refresh.test.ts |
| US benchmark intake | [audited intake](../backend/app/services/damodaran_us_ingestion.py), [existing parsers](../backend/app/services/damodaran_ingestion.py), [CLI](../scripts/ingest_damodaran.py) | [coverage registry](../backend/app/services/damodaran_coverage.py), [source record](../damodaran_knowledge_base_v1/reference/us_benchmark_intake_2026.md); test_damodaran_us_ingestion and test_damodaran_coverage |
| Peer/relative valuation | [router](../backend/app/api/routers/relative_valuation.py), [peer service](../backend/app/services/peer_valuation_sets.py), [relative engine](../backend/app/services/relative_valuation.py) | [API](../frontend/lib/api/relative-valuation.ts), [manager](../frontend/components/valuation/peer-set-manager.tsx); tests named peer, relative, saved_relative |
| Financial review planning | [service](../backend/app/services/financial_review_plan.py), [schemas](../backend/app/schemas/financials.py), [fundamentals route](../backend/app/api/routers/fundamentals.py) | [panel](../frontend/components/financial-review-plan.tsx), fundamentals page, test_financial_review_plan and financial-review-recovery browser workflow; read-only evidence planning |
| Macro analysis | [contracts](../backend/app/schemas/macro.py), [canonical routes](../backend/app/api/routers/macro_valuation.py), [compatibility adapter](../backend/app/services/macro_sensitivity_service.py) | top_down_macro_sensitivity, bottom_up_macro_sensitivity, macro_scenario_translation; frontend/components/macro and macro-review browser workflow |
| Financial review | [fundamentals router](../backend/app/api/routers/fundamentals.py), [extraction](../backend/app/services/financial_extraction.py), [normalization/provenance](../backend/app/services/accounting_normalization.py), [source revisions](../backend/app/services/source_fact_history.py), [pure calculations](../backend/app/services/financial_metric_derivations.py) | [API](../frontend/lib/api/financials.ts); test_financial_metric_derivations, test_normalization_provenance, test_source_fact_history, candidate-version/extraction tests and certification fixtures; PDF-promotion browser checks |
| SEC compatibility intake | [audited workflow](../backend/app/services/sec_xbrl_ingestion.py), [bounded extractor](../backend/app/services/sec_xbrl_extractor.py) | test_sec_ingestion_compatibility verifies both routes create review candidates, preserve existing metrics and audit safe failures; the old fetch import shares the same bounded transport |
| Scoped financial coverage | [read-only inventory](../backend/app/services/financial_coverage_inventory.py), [CLI](../backend/scripts/report_financial_coverage.py), [source checklist](../data/certification/scoped-source-checklist.json) | test_financial_coverage_inventory; six scalar queries, source/review gaps, no certification or writes |
| Filing intake | [manual storage](../backend/app/services/filing_manual.py), [audited discovery](../backend/app/services/filing_acquisition.py), [bounded input](../backend/app/providers/filings/base.py) | test_manual_filing_integrity, integration/test_ingestion_postgres and manual-filing.spec.ts verify retry/review preservation, shared issuer identity, audit and mobile intake |
| Official India manual guidance | [identity-bound source selection](../backend/app/services/manual_filing_sources.py), [dated checklist](../data/certification/scoped-source-checklist.json) | Read-only NSE symbol/ISIN matching; filing acquisition exposes source/date/document guidance, never approved financial values |
| PDF resource isolation | [parent job boundary](../backend/app/services/pdf_jobs.py), [single-use worker](../backend/app/workers/pdf_parse_worker.py) | Financial/private extraction and previews use bounded children; test_pdf_job_limits and PDF browser review cover rejection, cleanup and retained workflows |
| Extraction evaluation | [router](../backend/app/api/routers/evaluation.py), [executor](../backend/app/services/extraction_evaluation.py), [workspace](../frontend/components/evaluation-workspace.tsx) | [contracts](../backend/app/schemas/evaluation.py), [client](../frontend/lib/api/evaluation.ts), [execution tests](../backend/tests/test_evaluation_execution.py); owned reports, exact source hash, independent reviewed reference, no candidate promotion |
| Portfolio | [router](../backend/app/api/routers/portfolios.py), [valuation](../backend/app/services/portfolio_valuation.py) | [pure contracts](../backend/app/schemas/portfolio.py), [API](../frontend/lib/api/portfolio.ts), [detail page](../frontend/app/portfolio/[id]/page.tsx); schema-boundary, portfolio performance/risk tests and runtime smoke |
| Historical portfolio replay | [recorded activity](../backend/app/services/portfolio_replay.py), [snapshot capture](../backend/app/services/portfolio_analytics.py) | [replay regressions](../backend/tests/test_portfolio_replay.py), [snapshot labels](../frontend/lib/portfolio-replay.ts); dated positions/cash, purchase-date FX, current reconciliation, immutable legacy snapshots and corrected-activity hashes |
| Portfolio selected views | [overview](../frontend/components/portfolio/overview.tsx), [performance](../frontend/components/portfolio/performance-view.tsx), [activity](../frontend/components/portfolio/activity.tsx), [setup](../frontend/components/portfolio/setup.tsx) | Server-owned requests per URL tab; [period validation](../frontend/lib/portfolio-period.ts), portfolio-period and frontend-navigation tests |
| Portfolio list loading | [bounded server loader](../frontend/lib/server-portfolio.ts) | server-portfolio.test.ts checks concurrency, order and failure envelopes; both list pages share it and management omits unused analytics |
| Company coverage display | [stored quote](../frontend/components/company-market-header.tsx), [recorded financials](../frontend/components/financial-trends.tsx) | data-panels.test.ts and company-coverage.spec.ts protect currency, units, dates, zero/missing/error states and source-health links |
| Dated portfolio risk | [risk service](../backend/app/services/portfolio_risk_return.py), [valuation service](../backend/app/services/portfolio_valuation.py) | test_portfolio_risk_integrity checks independent covariance/marginal values, interval alignment, FX gaps, stale inputs, saved currencies and nonfinite outputs |
| Read-path performance | [query budgets](../backend/tests/test_read_query_budgets.py), [provider health](../backend/app/services/provider_health.py), [portfolio risk](../backend/app/services/portfolio_risk_return.py) | Explicit relationship loading, SQL latest-price/run windows, owner-scoped history and price-age gates; tests guard query count and ORM row materialization |
| Shared visual/navigation system | [tokens and layout](../frontend/app/globals.css), [page primitives](../frontend/components/page.tsx), [sidebar](../frontend/components/sidebar.tsx), [topbar](../frontend/components/topbar.tsx) | Bounded readable tables, responsive layout, mobile focus/inert cleanup; frontend-navigation tests and browser checks |
| Daily Brief | [router](../backend/app/api/routers/daily_brief.py), [engine](../backend/app/services/morning_briefing_engine.py), [public coverage](../backend/app/services/brief_public_coverage.py) | [contracts](../frontend/lib/api/daily-brief.ts), [coverage panel](../frontend/components/brief-public-coverage.tsx), [page](../frontend/app/daily-brief/page.tsx); public-coverage/dashboard/daily-brief tests cover bounded counts, historical unknowns, source parity and deterministic manual/scheduled assembly |
| Saved private brief context | [bounded snapshot](../backend/app/services/brief_private_context.py), [pure contract](../backend/app/schemas/brief_context.py), [panel](../frontend/components/brief-private-research.tsx) | test_brief_private_context; manual/scheduled owner-scoped as-generated evidence, exact IDs/hashes, separate reviewed and pending queues, no provider calls |
| Private research intake, retrieval and archiving | [router](../backend/app/api/routers/brief_sources.py), [workflow/search](../backend/app/services/brief_sources.py), [lifecycle](../backend/app/services/brief_source_lifecycle.py), [PDF extraction](../backend/app/services/brief_source_extraction.py) | [contracts](../backend/app/schemas/brief_sources.py), [intake](../frontend/components/brief-source-inbox.tsx), [library](../frontend/components/brief-source-library.tsx), [archive controls](../frontend/components/brief-source-lifecycle.tsx), [client](../frontend/lib/api/brief-sources.ts); test_brief_sources, test_brief_source_search, test_brief_source_lifecycle, brief-sources.test.ts and brief-source-search.spec.ts cover privacy, paging, lifecycle/scan conflicts, exact citations and review-only links |
| Company business context | [bounded read model](../backend/app/services/company_research.py), [cards](../frontend/components/company-research-cards.tsx) | [endpoint](../backend/app/api/routers/company_research.py); test_company_research checks one-query selection and excludes quarterly financial sections |
| Private-source comparison | [read-only service](../backend/app/services/brief_source_triage.py), [pure contracts](../backend/app/schemas/brief_triage.py), [workspace](../frontend/components/brief-source-triage.tsx) | [domain API](../frontend/lib/api/brief-triage.ts), test_brief_source_triage and brief-triage.test.ts; v2 quoted period/currency/scope labels, unknown/incompatible basis, exact-span receipts, bounded coverage, duplicate/Mock Data separation; no provider calls |
| Analyst comparison decisions | [review service](../backend/app/services/brief_comparison_reviews.py), [model](../backend/app/models/brief_review.py), [form/history](../frontend/components/brief-comparison-review.tsx) | test_brief_comparison_reviews; exact evidence hash, scoped version, immutable receipts and stale status, no approval or valuation writes |
| Request and ingestion security | [browser boundary](../frontend/lib/request-security.ts), [body cap](../backend/app/core/request_limits.py), [throttling](../backend/app/core/rate_limits.py), [public HTTP](../backend/app/providers/safe_http.py), [workbooks](../backend/app/services/workbook_safety.py) | test_security_boundaries, request-security.test.ts, route-security inventory; test included routers as well as direct health routes |
| Evidence and research | [search](../backend/app/services/evidence_search.py), [citation validation](../backend/app/services/ai_citations.py), [claim cues](../backend/app/services/ai_claim_review.py), [local candidates](../backend/app/services/ai_citation_suggestions.py) | [evidence API](../frontend/lib/api/evidence.ts), [AI API](../frontend/lib/api/ai.ts); source/ownership/review-gate tests |
| Scoped external AI permissions | [policy](../backend/app/services/ai_consent.py), [executor](../backend/app/services/ai_contract.py), [model](../backend/app/models/ai_consent.py), [router](../backend/app/api/routers/ai_consent.py), [schemas](../backend/app/schemas/ai_consent.py) | [client](../frontend/lib/api/ai-consent.ts), [Settings panel](../frontend/components/ai-consent-settings.tsx); test_ai_consent, test_ai_consent_routes, test_ai_consent_migration and ai-consent.spec cover default denial, owner/revision/scope checks, revocation, exact decision linkage and no automatic grants |
| Providers and ingestion | [providers](../backend/app/providers/), [ingestion](../backend/app/services/ingestion_pipeline.py), [market factory](../backend/app/services/market_data/factory.py) | [operations API](../frontend/lib/api/operations.ts), provider-health and source-specific tests |
| Bounded price fetch and connectivity | [SDK jobs](../backend/app/services/market_data/yfinance_jobs.py), [daily cutoffs](../backend/app/services/market_data/sessions.py), [fixed-host JSON](../backend/app/providers/fixed_json.py), [probes](../backend/app/services/provider_connectivity.py) | test_yfinance_job_limits, test_market_history_window, test_alpha_vantage_limits, test_provider_connectivity; no secret environment in SDK children, explicit audit without invented data coverage |
| Market quote/history writes | [workflow](../backend/app/services/market_data/ingestion.py), [canonical router](../backend/app/api/routers/market.py), [quote compatibility router](../backend/app/api/routers/market_prices.py) | [transaction tests](../backend/tests/test_market_ingestion_workflow.py), [price-alert ownership tests](../backend/tests/test_price_divergence_ownership.py); audited configuration, atomic persistence, duplicate handling and caller-owned downstream alerts |
| Private portfolio context | [portfolio valuation](../backend/app/services/portfolio_valuation.py), [valuation alerts](../backend/app/services/valuation_alert_service.py) | [ownership regressions](../backend/tests/test_private_portfolio_context.py); persisted-owner DCF/thesis/alerts, matching event/company/change-log relationships and owner-only portfolio impacts |
| Gemini connectivity | [adapter](../backend/app/providers/ai_provider.py), [audited probe](../backend/app/services/ai_provider_probe.py), [CLI](../backend/scripts/check_ai_provider.py) | [probe tests](../backend/tests/test_ai_provider_probe.py), provider and health tests; configurable model, header-only key, fixed non-private prompt and model-matched health evidence |
| Runtime/data health | [readiness](../backend/app/services/runtime_readiness.py), [health page](../frontend/app/data-health/page.tsx) | [health contracts](../frontend/lib/api/health.ts), route-security and readiness tests; batched column/constraint inspection retains missing-schema gates, with polling intervals owned by Compose |
| Data Health | [request loader](../frontend/lib/server/data-health.ts), [run summary](../frontend/lib/data-health-summary.ts), [overview](../frontend/components/data-health/health-overview.tsx) | One-pass recent-run indexes, concurrent explicitly selected audit, preserved failure envelopes; data-health and server-page-states tests |
| Data Health presentation | [diagnostics](../frontend/components/data-health/health-diagnostics.tsx), [providers](../frontend/components/data-health/provider-health.tsx), [processing](../frontend/components/data-health/processing-health.tsx), [health-ui](../frontend/components/data-health/health-ui.tsx) | Server-rendered domain panels; unavailable, empty and not-run states stay distinct; counts disclose the latest-100-run window |
| Peer review UI | [controller](../frontend/components/valuation/use-peer-set.ts), [view](../frontend/components/valuation/peer-set-view.tsx), [fields](../frontend/components/valuation/peer-set-fields.ts) | Company-keyed state, late-response isolation, source-preserving form/CSV review |
| Draft review UI | [controller](../frontend/components/valuation/use-autofill-draft.ts), [view](../frontend/components/valuation/autofill-draft-view.tsx), [fields](../frontend/components/valuation/autofill-draft-fields.ts) | Company/draft-keyed state, review/version checks and provenance display; test_valuation_setup_drafts covers partial/review-only save preservation |
| Peer calculation boundary | [contracts](../backend/app/schemas/peer_valuation.py), [diagnostics](../backend/app/services/peer_diagnostics.py), [persistence](../backend/app/services/peer_valuation_sets.py) | Pure inputs/calculation/receipt hashing separate from atomic owner-scoped mutations; legacy service imports stay compatible |
| Autofill responsibilities | [workflow](../backend/app/services/assumption_autofill_engine.py), [financial inputs](../backend/app/services/assumption_financial_inputs.py), [provenance](../backend/app/services/assumption_provenance.py) | Reviewed input lookup, deterministic provenance/readiness, draft orchestration |
| Workbook parsing | [pure parser](../backend/app/services/damodaran_workbook.py), [ingestion](../backend/app/services/damodaran_ingestion.py) | Workbook reading/header/value checks separate from dataset persistence |

Find remaining tests with `rg --files backend/tests frontend/lib frontend/e2e`.
Tests are indexed by behavior/domain, not by historical task number.

## API boundaries to preserve

- Backend: input validation and pure output contracts -> saved response assembly
  -> HTTP facade. Calculation services import narrow input/output contracts.
  The saved-response adapter still invokes non-writing pricing reconciliation.
  All legacy contracts now live in [domain schema modules](../backend/app/schemas/).
  The facade re-exports identical classes and literal aliases; pure contract
  imports cannot load HTTP, service or persistence layers.
- Shared backend envelopes live in schemas/common.py. Error handling and routes
  needing only envelope types import that module, not the legacy domain facade.
- Frontend: domain modules -> transport -> shared contract. Cross-domain types
  use type-only imports. lib/api.ts re-exports the old public surface so existing
  consumers need not all change at once. Never import that facade inside a domain.
- Server API code imports the shared contract, not browser endpoints. Keep its
  Next.js dynamic runtime boundary and signed authentication separate.
- Do not unify data-only and envelope-returning helpers by silently changing
  return shapes. Metadata-aware panels need the envelope; ordinary calls throw.
- Existing route aliases remain for compatibility. Use an observed registered
  path, not an inferred singular/plural or /api prefix.

## Source, tooling, and history boundaries

| Location | Treatment |
|---|---|
| [backend/tests](../backend/tests/), [frontend/lib tests](../frontend/lib/), [browser tests](../frontend/e2e/) | Maintained automated verification, isolated fixtures |
| [scripts](../scripts/), [backend/scripts](../backend/scripts/) | Operational tools; inspect arguments and side effects before running |
| [data](../data/) | Runtime datasets/assets, including mirrored versioned workbooks; not disposable code |
| [knowledge base](../damodaran_knowledge_base_v1/) | Separate doctrine/source corpus with its own AGENTS.md and immutable raw files |
| [docs/skills](skills/) | Task-specific project workflow references, not installed application features |
| [skills/security-review](../skills/security-review/) | Packaged repository skill; do not confuse with workflow-reference Markdown |
| .codex | Host/agent configuration; not application runtime code or a source for secrets |
| [retired tooling](../scripts/retired/README.md) | 27 old root/frontend/backend scripts preserved as inactive local records; excluded from Git and Docker builds; dated inventories record hashes, original paths and no current callers |
| [local helper packages](../skills/README.md) | Consolidated reference packages, including the former root spreadsheet folders; not application runtime code or proof of installed plugins |
| Backend build context | [.dockerignore](../.dockerignore) includes only maintained app, migration, operational-script and test trees plus build/dependency files; root scratch scripts and local databases stay on disk outside the context |
| tmp | Retained local source-review images and evidence; excluded from Git publication and routine searches |
| output, scratch, .playwright-cli | Ignored local reports or historical/manual evidence; not a current task queue. The obsolete generated repo_map.txt is removed and ignored |
| .pytest_cache, .pnpm-store, frontend/.next, frontend/tsconfig.tsbuildinfo | Reproducible generated caches; never confuse these with database volumes or source inputs |
| frontend/node_modules | Reproducible installed dependencies, retained while local Node processes may use them. Supported locked validation uses isolated Docker tooling |
| [archive](archive/) | Dated evidence and superseded instructions, excluded from routine onboarding |

## Safe verification entry points

- [Runbook](execution-runbook.md): source-mounted backend tests, frontend tests,
  production builds, isolated browser checks, migration/readiness diagnostics.
- [Test Compose](../docker-compose.test.yml): network-disabled backend tests,
  disposable SQLite default, read-only sources; no normal database or credentials.
- [Tooling Compose](../docker-compose.tools.yml): isolated Git/documentation and
  fake-Docker backup/restore checks, with shasum and executable temporary scripts;
  no Docker socket or normal database. Does not perform an actual restore drill.
- [CI](../.github/workflows/ci.yml): documentation/secret/workflow checks, release
  baseline, isolated browser quality gate.
- [Schema boundaries](../backend/tests/test_schema_boundaries.py) and
  [API boundaries](../frontend/lib/api-boundaries.test.ts): import/compatibility rules.
- [Contract manifest](../scripts/check_api_contracts.py), [backend check](../backend/tests/test_contract_manifest.py),
  [frontend drift check](../frontend/lib/contract-drift.test.ts): 15 critical wire
  contracts, including envelopes, aliases, nullable values and brief enums. New
  domains must extend this explicit coverage before a generated-client migration.
- [Documentation checker](../scripts/check_docs.py): links, nested instructions,
  retired plans, heading anchors, directory guides, page-inventory completeness and context-size limits. No second
  generated full-tree listing to maintain. .rgignore keeps archived bodies, raw
  corpus, locks and large receipts out of broad searches; use exact paths when needed.
- [Workstream guard](../scripts/check_workstream_ownership.sh): disjoint path
  reservations and changed-path ownership; [tests](../scripts/test_workstream_ownership.sh)
  reject overlap and frozen/shared-file edits. Behavioral compatibility still
  requires contract tests and coordinated integration.
