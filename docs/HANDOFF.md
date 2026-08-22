# Agent Handoff

**Updated:** 2026-08-22

**Purpose:** the shortest safe starting point for the next agent.

## Read Order

1. [`00-current-state.md`](00-current-state.md)
2. [`02-architecture.md`](02-architecture.md)
3. [`roadmaps/product-roadmap.md`](roadmaps/product-roadmap.md)
4. The task-specific core doc listed in [`README.md`](README.md)
5. Relevant code and tests

Do not read archived checkpoints unless the task needs historical evidence.

## Safe Starting State

- Current database head: `cc4cc4cc4cc4`.
- The migration history was intentionally replaced on 2026-08-09 after the
  user confirmed every database created from the prior chain was disposable.
  Recreate, rather than upgrade, any database still stamped with the deleted
  `20260524_*` or `20260530_*` revisions.
- Fresh 2026-08-09 worktree baseline: 538 backend tests and 98 frontend tests
  pass; TypeScript and the Next.js production build pass. Local API health and
  authentication readiness also pass. Four upstream `openpyxl` deprecation
  warnings remain.
- Damodaran coverage: 9 supported, 13 partial, 13 unsupported; 14 typed sources
  and 3,290 rows.
- Knowledge-base inbox: empty; audit status `ok`.
- The worktree contains substantial user and prior-agent changes. Do not revert,
  reset, or reformat unrelated files.

## Latest Delivered Boundary

The source-truth worktree was extended through 40 dependency-ordered,
commit-sized phases on 2026-08-09. The latest boundary adds complete
point-in-time portfolio performance infrastructure, explicit benchmark and
historical-FX ownership, generated snapshot provenance, TWR/MWR, price/FX/flow
attribution, opportunity cost, provider run/freshness diagnostics, source-aware
market-regime scoring, and AI citation coverage gates. Agent scratch remains
intentionally uncommitted.

The documentation architecture has been consolidated. Active current-state,
architecture, schema, runbook, capability, handoff, roadmap, feature-register,
frontend, and valuation docs now replace cumulative histories. Detailed evidence
and old plans are preserved under categorized archive folders. The automated
checker covers 62 active repository Markdown files and 270 local links; its four
unit tests and all 11 project-skill validations pass. See
[`archive/checkpoints/2026/documentation-architecture-checkpoint-2026-08-08.md`](archive/checkpoints/2026/documentation-architecture-checkpoint-2026-08-08.md).

The latest runtime/data boundary remains:

All current application-specific typed Damodaran importers now use preserved,
hash-versioned datasets with active-only reads. Country statistics retain the
exact 22-column contract and all 20 meaningful fields. The latest detailed proof
is archived at
[`archive/checkpoints/2026/next-5-damodaran-versioned-country-statistics-checkpoint-2026-08-08.md`](archive/checkpoints/2026/next-5-damodaran-versioned-country-statistics-checkpoint-2026-08-08.md).

Recent feature milestones completed include:
- **Bounded Data Health:** The normal health page no longer launches three
  expensive diagnostics. Deep evidence, Damodaran coverage, and historical
  backfill checks are explicit, carry longer diagnostic timeouts, and distinguish
  not-run from zero. Provider health separates core requirements, optional
  integrations, and manual-only coverage. The page now groups operations,
  provider readiness, and diagnostic status with calmer type and status
  semantics; optional setup and not-run diagnostics are not styled as failures or
  successes.
- **Portfolio Marginal Risk and DCF Gap:** The owned portfolio endpoint and
  responsive detail panel now use dated base-currency returns, minimum coverage,
  sample covariance, annualized volatility, marginal risk for a one-percentage-
  point weight change, reconciling component risk, and trust-gated Base DCF
  valuation gaps. Missing inputs remain unavailable and all source record IDs,
  formulas, warnings, blockers, coverage, and claim types are exposed.
- **Bounded Portfolio Overview and Accessibility:** The portfolio index no
  longer blocks on deep analytics or snapshot calculations. It retains holdings
  and trust-gated valuation status and links to owned detail workspaces for the
  expensive calculations. Market Regime controls now have programmatic labels
  and a responsive layout. The desktop/mobile smoke matrix covers 20 primary
  routes and includes typography minimums. Seventeen routes reached a complete
  authenticated render in the latest sweep. Narratives, Macro, and Documents
  still need a live recheck after the local frontend reset; source-level integrity
  tests cover all 20.
- **Primary-route UI hardening:** Daily Brief request batches are parallel;
  Research, Narratives, Data Management, Search, and Market Regime layouts now
  collapse without fixed-width page overflow. CSV and workbook inputs have
  programmatic labels, Data Management no longer nests buttons inside links,
  and Settings loads independent configuration requests concurrently.
- **Dashboard Read Safety and Latency:** Dashboard GET requests no longer run AI
  contradiction/valuation generation or create divergence alerts. Price writes
  trigger divergence checks, explicit brief generation retains AI behavior,
  oversized raw source payloads and per-event price lookups are excluded from the
  dashboard path, headline portfolio value comes from the latest explicit
  snapshot, portfolio valuation inputs are batch-loaded, and internal latency
  breaches are logged rather than labeled as partial data.
- **Valuation workflow repair:** The frontend proxy now forwards industry-mix
  `PUT` requests. DCF drafts offer one explicit bulk acknowledgement for valid
  defaults, collapse warning and assumption detail, and derive positive
  invested-capital fallbacks from revenue when reported capital is zero. New
  writes reject invalid percentage-point rates and capital weights. Historical
  invalid models remain readable but show blocked output, disabled reruns,
  diagnostic-derived quality, and no sensitivity tables until corrected.
- **Portfolio Performance and Attribution:** Portfolios can persist one explicit
  benchmark, historical FX observations, and idempotent dated snapshots. Complete
  periods calculate TWR, MWR, price movement, FX impact, position change,
  external flows, cash change, dimension attribution, reconciliation residual,
  and benchmark opportunity cost. Missing prices, FX, snapshots, or benchmark
  history block false precision and expose source IDs, warnings, and formulas.
- **Local Authentication Boundary:** Local credentials, NextAuth sessions,
  signed internal identity, request/error contracts, route security inventory,
  and readiness checks are implemented and validated for localhost use.
- **Frontend/Backend Truth Parity (Priority 1):** Audited `events`, `portfolio`, and key routes. Standardized `serverFetchApi` to return direct `T` instead of nested wrapper to align with service layers.
- **Portfolio Pricing Reality (Phase 3):** Removed mock FX Impact and Opportunity Cost logic; configured `market_data/factory.py` to raise explicit `NOT_CONFIGURED` errors when providers are missing, and updated `PortfolioAnalyticsDashboard` to display "Not Configured" instead of fake values.
- **Advanced Portfolio Analytics (Priority 4):** Integrated sector, asset, and
  currency exposure breakdowns and HHI concentration. The legacy activity view
  remains conservative, while the dated performance view calculates FX impact
  and opportunity cost only when its required source series exist.
- **Provider Health:** Data Health distinguishes never-run, running, partial,
  successful, stale, and failing provider states. It reports latest attempts,
  run counts, consecutive failures, provider-specific freshness thresholds, and
  owned RSS source coverage.
- **Market Regime:** Inputs are bounded to the documented scale and require
  source name, date, type, and methodology. Provider inputs require a source
  URL. Scores distinguish Manual, Mixed, Live, Stale, and Incomplete modes and
  expose input provenance, formula, blockers, warnings, and confidence.
- **AI Evidence Review:** Approval requires source markers, declared-source
  consistency, exact stored-text validation for every cited source, successful
  execution, nonempty output, and no prohibited recommendation language.
- **AI DCF Variable Mapping (Priority 3 Expansion):** Added a new AI service and `/ai/map-event-to-dcf` endpoint to map market events to DCF variables, accessible via the new `DcfImpactPredictor` component on the events page.

- **Morning Briefing Engine (Priority 3):** Completed the Morning Briefing dashboard overhaul. Connected ingestion, evidence, alerts, thesis changes, valuation relevance, and portfolio exposure. Implemented `last_review_date` state management and AI contradiction detection. Unreviewed contradictions are now visible in Data Health.
- **India Provider & Identity Coverage (Priority 2):** Expanded standard methodology to parse minority interests, cross-holdings, operating leases, and diluted shares. Updated frontend company UI and DCF components to display these structural elements explicitly. Added RELIANCE on NSE to the certification manifest and integrated manual provider UI badges for non-US companies.

## Next Recommended Work

Run the focused and full backend suites from a terminal with Docker socket
access, then finish the portfolio smoke with real, source-labeled inputs containing
two complete snapshot dates,
one non-base-currency holding, one configured benchmark, at least 20 aligned
return observations per holding, and one trusted Base DCF output. Verify the
dashboard stays read-only and no longer renders a latency budget as partial data.

The 2026-08-22 increment passed backend compile, all 108 frontend tests,
TypeScript, the documentation checker, and authenticated browser checks for
Data Health, financial certification, industry allocation, and default-first DCF
creation. Backend pytest is unverified because this agent cannot access the
Docker socket and the bundled host Python runtime has no pytest. The host Next.js
build is blocked by the protected `.env.local` path and Docker-owned `.next`
artifacts; do not weaken secret protections to make that command pass.

## Commands

```bash
cd "/Users/mananmaheshwari/Documents/Codex/Market Intelligence App/market-intelligence-md-files copy"
cp .env.example .env
docker compose up --build -d
docker compose exec backend alembic upgrade head
curl http://localhost:8000/api/health
```

Validation:

```bash
docker compose exec backend pytest -q
cd frontend
npm test
npm run typecheck
npm run build
cd ..
python3 damodaran_knowledge_base_v1/tools/audit_kb.py
python3 scripts/check_docs.py
git diff --check
```

Local sign-in requires `NEXTAUTH_SECRET`, `LOCAL_AUTH_USERNAME`, and
`LOCAL_AUTH_PASSWORD` in `.env`. See [`07-local-development.md`](07-local-development.md).

## Important Boundaries

- Localhost only. Public deployment security is not complete.
- Do not expose secrets in frontend code or commit `.env`.
- Do not present mock, planned, stale, or unsupported data as real.
- AI output is interpretation until reviewed and source-validated.
- Valuation assumptions need provenance and explicit review.
- No broker credentials and no buy/sell recommendation language.
- Use the Damodaran knowledge base for valuation doctrine; use application docs
  for runtime behavior.

## Documentation Rule

Current docs describe present behavior. Archived docs preserve history. New
shipped work should update current state, feature register, affected core docs,
and this handoff. Do not append another chronological mini-handoff.

The previous 1,232-line cumulative handoff is preserved at
[`archive/handoffs/HANDOFF-history-through-2026-08-08.md`](archive/handoffs/HANDOFF-history-through-2026-08-08.md).
