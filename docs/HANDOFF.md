# Agent Handoff

**Updated:** 2026-08-09

**Purpose:** the shortest safe starting point for the next agent.

## Read Order

1. [`00-current-state.md`](00-current-state.md)
2. [`02-architecture.md`](02-architecture.md)
3. [`roadmaps/product-roadmap.md`](roadmaps/product-roadmap.md)
4. The task-specific core doc listed in [`README.md`](README.md)
5. Relevant code and tests

Do not read archived checkpoints unless the task needs historical evidence.

## Safe Starting State

- Current database head: `z1z1z1z1z1z1`.
- The migration history was intentionally replaced on 2026-08-09 after the
  user confirmed every database created from the prior chain was disposable.
  Recreate, rather than upgrade, any database still stamped with the deleted
  `20260524_*` or `20260530_*` revisions.
- Fresh 2026-08-09 worktree baseline: 492 backend tests and 91 frontend tests
  pass; TypeScript and the Next.js production build pass. Local API health and
  authentication readiness also pass. Four upstream `openpyxl` deprecation
  warnings remain.
- Damodaran coverage: 9 supported, 13 partial, 13 unsupported; 14 typed sources
  and 3,290 rows.
- Knowledge-base inbox: empty; audit status `ok`.
- The worktree contains substantial user and prior-agent changes. Do not revert,
  reset, or reformat unrelated files.

## Latest Delivered Boundary

The source-truth worktree was reconciled into 20 dependency-ordered phases on
2026-08-09. The committed boundary now includes the replacement migration
chain, expanded persistence and API contracts, provider and evidence workflows,
valuation engines, authenticated frontend workflows, operational checks, and
the audited valuation knowledge base. Agent scratch and the duplicate
`Data for Model/` input folder remain intentionally uncommitted.

The documentation architecture has been consolidated. Active current-state,
architecture, schema, runbook, capability, handoff, roadmap, feature-register,
frontend, and valuation docs now replace cumulative histories. Detailed evidence
and old plans are preserved under categorized archive folders. The automated
checker covers 60 active repository Markdown files and 271 local links; its four
unit tests and all 11 project-skill validations pass. See
[`archive/checkpoints/2026/documentation-architecture-checkpoint-2026-08-08.md`](archive/checkpoints/2026/documentation-architecture-checkpoint-2026-08-08.md).

The latest runtime/data boundary remains:

All current application-specific typed Damodaran importers now use preserved,
hash-versioned datasets with active-only reads. Country statistics retain the
exact 22-column contract and all 20 meaningful fields. The latest detailed proof
is archived at
[`archive/checkpoints/2026/next-5-damodaran-versioned-country-statistics-checkpoint-2026-08-08.md`](archive/checkpoints/2026/next-5-damodaran-versioned-country-statistics-checkpoint-2026-08-08.md).

Recent feature milestones completed include:
- **Portfolio Attribution Truth Boundary:** Removed hardcoded 5% opportunity
  cost and fake zero FX impact. The backend now reports recorded transaction
  activity by currency, blocks aggregate cross-currency price movement, and
  exposes explicit partial/not-configured warnings. The frontend uses the same
  contract and does not present missing benchmark or historical-FX data as real.
- **Local Authentication Boundary:** Local credentials, NextAuth sessions,
  signed internal identity, request/error contracts, route security inventory,
  and readiness checks are implemented and validated for localhost use.
- **Frontend/Backend Truth Parity (Priority 1):** Audited `events`, `portfolio`, and key routes. Standardized `serverFetchApi` to return direct `T` instead of nested wrapper to align with service layers.
- **Portfolio Pricing Reality (Phase 3):** Removed mock FX Impact and Opportunity Cost logic; configured `market_data/factory.py` to raise explicit `NOT_CONFIGURED` errors when providers are missing, and updated `PortfolioAnalyticsDashboard` to display "Not Configured" instead of fake values.
- **Advanced Portfolio Analytics (Priority 4):** Integrated sector, asset, and
  currency exposure breakdowns and HHI concentration. Recorded activity is
  separated by currency; opportunity cost and historical FX impact remain
  visibly unavailable until real benchmark and FX series exist.
- **Provider Health Mock-Status (Priority 5):** Added explicit `mock` and `prototype` statuses to `provider_health.py` and the data-health dashboard to prevent deceptive presentation of AI outputs.
- **AI DCF Variable Mapping (Priority 3 Expansion):** Added a new AI service and `/ai/map-event-to-dcf` endpoint to map market events to DCF variables, accessible via the new `DcfImpactPredictor` component on the events page.

- **Morning Briefing Engine (Priority 3):** Completed the Morning Briefing dashboard overhaul. Connected ingestion, evidence, alerts, thesis changes, valuation relevance, and portfolio exposure. Implemented `last_review_date` state management and AI contradiction detection. Unreviewed contradictions are now visible in Data Health.
- **India Provider & Identity Coverage (Priority 2):** Expanded standard methodology to parse minority interests, cross-holdings, operating leases, and diluted shares. Updated frontend company UI and DCF components to display these structural elements explicitly. Added RELIANCE on NSE to the certification manifest and integrated manual provider UI badges for non-US companies.

## Next Recommended Work

Continue with Priority 4 (Portfolio Attribution and Opportunity Cost) in [`roadmaps/product-roadmap.md`](roadmaps/product-roadmap.md). The next complete slice needs point-in-time prices or snapshots, historical FX rates, and an explicit benchmark selection so period return can separate price, FX, external cash flow, and position changes without estimates.

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
