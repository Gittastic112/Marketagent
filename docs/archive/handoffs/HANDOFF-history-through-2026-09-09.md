Historical snapshot, not current instructions. Original relative links are preserved.

# Agent Handoff

**Updated:** 2026-09-09

**Purpose:** the shortest safe starting point for the next agent.

## Read Order

1. [`00-current-state.md`](00-current-state.md)
2. [`02-architecture.md`](02-architecture.md)
3. [`roadmaps/product-roadmap.md`](roadmaps/product-roadmap.md)
4. The task-specific core doc listed in [`README.md`](README.md)
5. Relevant code and tests

Do not read archived checkpoints unless the task needs historical evidence.

## Safe Starting State

- Current source migration head: `o6o6o6o6o6o6`.
- The migration history was intentionally replaced on 2026-08-09 after the
  user confirmed every database created from the prior chain was disposable.
  Recreate, rather than upgrade, any database still stamped with the deleted
  `20260524_*` or `20260530_*` revisions.
- Latest workbook-aware source-mounted container backend run: 845 tests passed
  with four upstream `openpyxl` deprecation warnings. All 191 frontend tests,
  TypeScript, and a Docker
  production build passed.
- The normal PostgreSQL runtime is upgraded to `o6o6o6o6o6o6`. The backend
  container has the current source and the valuation benchmark data is seeded.
  The production frontend bundle was rebuilt and deployed inside its existing
  configured container; frontend auth readiness and both container healthchecks
  are healthy. The
  scheduler image built and its container started. Daily
  Brief and unified-search browser workflows passed. A real due worker cycle
  now also passes: it created a sanitized successful Processing Run and one
  deterministic brief, then a repeated due cycle reused that brief with
  `created_count = 0`. The temporary opt-in schedule was disabled after the
  exercise; its two Processing Runs and generated brief remain as audit evidence.
- Damodaran coverage: 12 supported, 14 partial, 9 unsupported; 18 active typed
  sources and 2,625 rows, all with complete active provenance.
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
checker covers 62 active repository Markdown files and 319 local links; its four
unit tests and all 11 project-skill validations pass. See
[`archive/checkpoints/2026/documentation-architecture-checkpoint-2026-08-08.md`](archive/checkpoints/2026/documentation-architecture-checkpoint-2026-08-08.md).

The latest runtime/data boundary remains:

All current application-specific typed Damodaran importers now use preserved,
hash-versioned datasets with active-only reads. Country statistics retain the
exact 22-column contract and all 20 meaningful fields. The latest detailed proof
is archived at
[`archive/checkpoints/2026/next-5-damodaran-versioned-country-statistics-checkpoint-2026-08-08.md`](archive/checkpoints/2026/next-5-damodaran-versioned-country-statistics-checkpoint-2026-08-08.md).

Recent feature milestones completed include:
- **Saved Output and Scenario Integrity:** Shared output-card gates replace
  unguarded estimates, saved prices are User Assumptions, and stored scores are
  explicitly historical. Scenario dispatch retains model type, preserves zero,
  rejects stale/invalid inputs and uses saved currency with backend-calculated
  gaps. On-demand loading exposes diagnostics, unavailable values and retry.
  See [`archive/checkpoints/2026/output-scenario-integrity-checkpoint-2026-09-09.md`](archive/checkpoints/2026/output-scenario-integrity-checkpoint-2026-09-09.md).
- **DCF Implied-Pricing Reconciliation:** Explicit saved earnings/book/revenue
  inputs replace proxy ratios, final adjusted DCF values drive new runs, and
  historical reads reconcile responses without rewriting records. The sidebar
  exposes formulas, timestamps, source fields, unavailable EBITDA, zero values,
  and stale/critical gates. See
  [`archive/checkpoints/2026/dcf-implied-pricing-checkpoint-2026-09-08.md`](archive/checkpoints/2026/dcf-implied-pricing-checkpoint-2026-09-08.md).
- **Saved DCF Relative Input Basis:** Owned server-side mapping preserves zero
  bridge inputs and book equity, exposes derived EBIT without an EBITDA proxy,
  and reports input provenance and method coverage. Saved calculations require
  exact input-preview hashes and explicit basis confirmation, reread ownership
  and stale state, and return the consumed input basis. See
  [`archive/checkpoints/2026/saved-relative-input-basis-checkpoint-2026-09-08.md`](archive/checkpoints/2026/saved-relative-input-basis-checkpoint-2026-09-08.md).
- **Relative Valuation Request Isolation:** Latest-request resources prevent
  stale country/industry/peer responses from becoming selectable evidence.
  Refresh failures clear usable evidence and expose retry; company changes
  reset the editor; input changes invalidate in-flight results and errors.
  See [`archive/checkpoints/2026/relative-valuation-request-isolation-checkpoint-2026-09-06.md`](archive/checkpoints/2026/relative-valuation-request-isolation-checkpoint-2026-09-06.md).
- **Relative Valuation Input Contract:** Requests reject non-finite/boolean
  financial values, unknown fields, invalid bridge/share values, duplicate or
  empty methods, invalid identifiers, and ambiguous benchmark selection.
  Overflow is reported per method, finite averages use scaled summation, and
  validation error detail safely serializes non-finite rejected values. See
  [`archive/checkpoints/2026/relative-valuation-input-contract-checkpoint-2026-09-06.md`](archive/checkpoints/2026/relative-valuation-input-contract-checkpoint-2026-09-06.md).
- **Bounded Peer Eligibility and Review Navigation:** Shared peer eligibility
  includes lifecycle, receipt, storage consistency, and usable-method coverage.
  Data Health audits at most 100 sets per request (UI 50), identifies page-local
  counts and continuation, and links directly into a standalone company peer
  workspace. Results are hidden when valuation inputs change. See
  [`archive/checkpoints/2026/peer-eligibility-audit-navigation-checkpoint-2026-09-06.md`](archive/checkpoints/2026/peer-eligibility-audit-navigation-checkpoint-2026-09-06.md).
- **Peer Receipt Data Health:** The normal bounded Data Health page now audits
  every peer set owned by the current user, distinguishes current, missing,
  stale, Draft, and archived receipt states, and links only actionable active
  reviewed sets to their valuation workspaces. See
  [`archive/checkpoints/2026/peer-review-receipt-data-health-checkpoint-2026-09-05.md`](archive/checkpoints/2026/peer-review-receipt-data-health-checkpoint-2026-09-05.md).
- **Versioned Peer Diagnostic Acknowledgement:** Migration `o6o6o6o6o6o6`
  stores the exact deterministic diagnostic SHA-256, warning-code set, and
  diagnostic date on current peer sets and immutable revisions. Review rejects
  stale diagnostic snapshots and incomplete warning acknowledgement. Relative
  valuation rejects missing or stale receipts, while the UI makes warning review
  explicit, supports re-acknowledgement, and keeps ineligible sets out of the
  calculation selector. See
  [`archive/checkpoints/2026/peer-diagnostic-acknowledgement-receipts-checkpoint-2026-09-05.md`](archive/checkpoints/2026/peer-diagnostic-acknowledgement-receipts-checkpoint-2026-09-05.md).
- **Currency-Safe Peer Size Diagnostics:** Peer and target market-cap comparisons
  now operate only inside matching stated-currency groups. The response exposes
  per-currency membership, range and ratio data, plus target comparison and skip
  counts. Missing, invalid, and cross-currency amounts are disclosed rather than
  combined. The peer manager displays peer and target size coverage. See
  [`archive/checkpoints/2026/peer-market-cap-currency-diagnostics-checkpoint-2026-09-05.md`](archive/checkpoints/2026/peer-market-cap-currency-diagnostics-checkpoint-2026-09-05.md).
- **Idempotent Peer CSV Apply:** Migration `n5n5n5n5n5n5` records the exact
  UTF-8 request-content SHA-256 on imported peer sets and enforces one receipt
  per owner, target company, and hash. Exact retries return the existing active
  or archived set; concurrent collisions return the database winner. The API and
  UI distinguish created from reused results, and runtime readiness checks the
  critical unique constraint. Legacy pre-n5 rows remain intentionally unbackfilled.
  See [`archive/checkpoints/2026/peer-csv-idempotent-apply-checkpoint-2026-09-04.md`](archive/checkpoints/2026/peer-csv-idempotent-apply-checkpoint-2026-09-04.md).
- **Peer CSV Safety:** Bounded strict parsing, exact row-width checks, controlled
  parser errors, complete create validation during preview, sanitized numeric
  errors, conflicting-storage export gates, literal apostrophe preservation,
  strict browser UTF-8 file reads, and stale-preview invalidation are implemented.
  See [`archive/checkpoints/2026/peer-csv-safety-checkpoint-2026-09-03.md`](archive/checkpoints/2026/peer-csv-safety-checkpoint-2026-09-03.md).
- **Target-Profile CSV Portability:** Peer CSV format v2 includes the sourced
  target-company profile on every peer row. Preview requires identical target
  fields across rows, applies the same strict target model used by direct API
  writes, and preserves exact-file SHA-256 gating. Apply creates one Draft peer
  set with normalized/versioned target evidence; formula-safe export round-trips
  the target profile. Legacy member-only files remain accepted and visibly
  limited. See
  [`archive/checkpoints/2026/target-profile-csv-portability-checkpoint-2026-09-03.md`](archive/checkpoints/2026/target-profile-csv-portability-checkpoint-2026-09-03.md).
- **Sourced Target-Company Peer Comparability:** Migration `m4m4m4m4m4m4`
  adds one normalized current target profile and immutable target snapshots for
  peer-set revisions while preserving JSON as a consistency boundary. Profiles
  require source identity, URL, date, claim type, and at least one target fact.
  Relative valuation now surfaces target-versus-peer currency, country,
  accounting, fiscal-period, size, growth, and margin warnings. Missing target
  context remains visible, and storage mismatches block review and valuation.
  The UI supports add, edit, removal, audit state, and revision visibility. See
  [`archive/checkpoints/2026/target-relative-peer-comparability-checkpoint-2026-09-03.md`](archive/checkpoints/2026/target-relative-peer-comparability-checkpoint-2026-09-03.md).
- **Normalized Peer Evidence and Source-Preserving CSV:** Migration
  `l3l3l3l3l3l3` adds queryable current and immutable revision-member rows while
  preserving JSON snapshots for compatibility and consistency audits. Writes
  update both representations atomically. Strict CSV import uses a header-only
  template, non-writing row-level preview, exact SHA-256 apply, and Draft-only
  creation; formula-safe export retains source fields. Optional geography,
  currency, fiscal-period, accounting, size, growth, and margin context drives
  deterministic mismatch warnings without inventing a score. Fresh-chain,
  legacy-backfill, and real PostgreSQL create/update checks passed. See
  [`archive/checkpoints/2026/normalized-peer-evidence-csv-checkpoint-2026-09-02.md`](archive/checkpoints/2026/normalized-peer-evidence-csv-checkpoint-2026-09-02.md).
- **Versioned Peer Lifecycle and Comparability Diagnostics:** Migration
  `k2k2k2k2k2k2` adds immutable owner-scoped snapshots and optimistic mutation
  versions. Create, update, review, archive, restore, and legacy backfill actions
  retain exact evidence and changed fields. Restore always returns a set to
  Draft. The UI now edits, restores, and displays history. Deterministic warnings
  cover stale and unaligned dates, Source Summary members, sparse method
  coverage, and wide dispersion without silently excluding evidence. Reviewed
  peer reliability is capped at medium and falls to low when warnings apply.
- **Reviewed Peer Relative Valuation:** Owner-scoped peer sets now have strict
  create, update, review, list, detail, and archive boundaries. Each member
  carries identifier, optional company link, included state, positive multiples,
  source name, source URL, as-of date, claim type, and notes. Duplicate peers,
  self-comparison, future dates, non-positive multiples, and Mock Data labels are
  rejected. Only active reviewed sets may drive a valuation. Each method needs
  at least three eligible peers and uses a deterministic median while exposing
  counts, member IDs, exclusions, formula, and exact member provenance. Editing
  invalidates review. The valuation UI can create, review, select, inspect, and
  archive these sets. See
  [`archive/checkpoints/2026/reviewed-peer-relative-valuation-checkpoint-2026-08-26.md`](archive/checkpoints/2026/reviewed-peer-relative-valuation-checkpoint-2026-08-26.md).
- **Secret-free frontend build context:** `frontend/.dockerignore` now excludes
  `.env` and all `.env.*` files except `.env.example`. A clean no-cache Docker
  build passed without loading `.env.local`.
- **Owned Portfolio Evidence Bundles:** The portfolio workspace can now download
  a strict CSV template and server-preview genuine market-price and FX facts
  before any write. The backend constrains tickers and FX pairs to the owned
  portfolio plus active benchmark, requires actual provider labels, source URLs,
  timezone-aware source timestamps, and supported price types, rejects Mock Data
  markers, skips exact duplicates, blocks conflicts, and rechecks the preview
  SHA-256 during atomic apply. Successful and failed applies create sanitized
  Processing Runs; created facts retain the run ID, `Fact` claim type, and market
  price source URL. This removes the bulk-entry bottleneck but does not create
  holdings, benchmark configuration, snapshots, or DCF outputs. See
  [`archive/checkpoints/2026/portfolio-evidence-bundle-checkpoint-2026-08-24.md`](archive/checkpoints/2026/portfolio-evidence-bundle-checkpoint-2026-08-24.md).
- **Bounded local runtime:** Default Compose uses the standalone production
  frontend, one backend process, health-gated dependencies, capped logs, and an
  optional pgAdmin profile. `docker-compose.dev.yml` contains reloaders, bind
  mounts, named frontend caches, and a 1536 MB frontend heap cap. Narratives no
  longer has per-cluster request waterfalls, Macro setup requests are parallel,
  and expensive links opt out of automatic prefetch. The 20-route matrix now has
  a 15-second ready-state budget.
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
- **Real-Input Portfolio Readiness:** An owner-scoped, read-only audit now checks
  positive holdings, two complete snapshot boundaries, non-base-currency
  exposure, 20 aligned returns per holding, dated FX, an active benchmark and
  boundary comparison, one trust-gated Base DCF output, explicit source labels,
  and absence of Mock Data. The portfolio detail page exposes every check,
  blocker, next action, and source record ID. A CLI prints the same report without
  seeding, refreshing, capturing, or changing data. This prepares the manual
  smoke but does not replace it.
- **Deterministic Portfolio Runtime Gate:** The browser seed now creates a visibly
  labeled Mock Data portfolio with two complete snapshots, USD and EUR holdings,
  22 dated observations, EUR/USD FX, a benchmark, one opening cash flow, and two
  trusted Base DCF outputs. The focused browser workflow proves TWR/MWR,
  attribution, opportunity cost, risk reconciliation, DCF coverage, provenance
  IDs, and responsive UI disclosure. Mock state is propagated through the API
  body, response metadata, and visible panel badge. The implementation checkpoint
  is archived at
  [`archive/checkpoints/2026/portfolio-runtime-smoke-gate-2026-08-22.md`](archive/checkpoints/2026/portfolio-runtime-smoke-gate-2026-08-22.md).
- **Source-Linked Morning Briefing:** Held-company price moves now require two
  distinct dated prices and never default to zero. Important events expose source
  documents, claim type, status, affected portfolios, and provenance IDs.
  Contradiction and valuation AI states distinguish not-run, failed, partial,
  and complete; GET is deterministic and explicit refresh owns generation. The
  responsive page links to real evidence routes and the focused browser workflow
  covers source, move, portfolio, review, and document navigation. See
  [`archive/checkpoints/2026/daily-brief-evidence-loop-checkpoint-2026-08-23.md`](archive/checkpoints/2026/daily-brief-evidence-loop-checkpoint-2026-08-23.md).
- **Honest Availability and Brief Review State:** Transport, authentication,
  proxy, and parse failures are now unavailable/error states, not stale cached
  data. Stale is reserved for successful responses whose stored source records
  exceed their freshness threshold. Daily Brief review actions persist the real
  `reviewed_at` time and future briefs use that review waterline. Failed or
  partial processing runs since that waterline are visible without exposing raw
  provider error details. A deterministic inspection queue links contradictions,
  missing price evidence, unlinked material events, and failed runs to the exact
  event, document, price, alert, or processing-run records that caused the action.
- **Local Daily Brief Automation:** One owner-scoped schedule can now persist an
  IANA timezone, local run time, weekdays, next run, bounded lease, and last-run
  state. An opt-in Compose worker generates deterministic briefs without external
  AI, deduplicates each local brief date, records a sanitized Processing Run, and
  advances after success or failure. The Daily Brief page exposes configuration,
  due state, and last-run provenance. Its backend coverage passed inside the
  latest full container run. The scheduler image/container startup,
  schedule-specific browser workflow, actual due cycle, Processing Run audit,
  generated brief, lease release, next-run advancement, and repeated-cycle
  idempotency all passed. See
  [`archive/checkpoints/2026/daily-brief-local-scheduling-checkpoint-2026-08-23.md`](archive/checkpoints/2026/daily-brief-local-scheduling-checkpoint-2026-08-23.md).
  The final runtime proof is recorded at
  [`archive/checkpoints/2026/daily-brief-scheduler-runtime-checkpoint-2026-08-24.md`](archive/checkpoints/2026/daily-brief-scheduler-runtime-checkpoint-2026-08-24.md).
- **Runtime Readiness and Isolated Browser Gates:** `/api/health` remains a
  process liveness probe while public `/api/readiness` verifies database access,
  migration head `i0i0i0i0i0i0`, and the schema required by Daily Brief,
  FRED provenance, and linked Market Regime inputs
  automation. Compose now health-gates the frontend on readiness. Data Health
  displays migration and schema blockers with safe recovery commands. Browser
  workflows default to isolated ports `13000/18000`, reject occupied ports before
  starting, and no longer compete with the normal `3000/8000` stack. Daily Brief
  exposes the actual API error and an optional schedule failure cannot blank the
  briefing. The normal scheduler image was rebuilt from the `i0` source on
  2026-08-25 after its older image could not locate that migration; the recreated
  service now starts the deterministic worker at a 60-second interval. See
  [`archive/checkpoints/2026/runtime-readiness-checkpoint-2026-08-23.md`](archive/checkpoints/2026/runtime-readiness-checkpoint-2026-08-23.md).
- **Server-Rendered Authentication Repair:** The browser proxy could authenticate
  while React server components returned `Authentication error` under Next.js
  16. The shared server API helper no longer relies on `getServerSession` in that
  incompatible path. It reads the request cookie store asynchronously, assembles
  standard, secure, or chunked NextAuth tokens, verifies and decodes the token,
  then signs the internal backend identity without forwarding cookies. This one
  repair covers every server-rendered route. Runtime environment reads now occur
  only after Next.js `connection()`, preventing the production build from caching
  a false `Local authentication is not configured` page before runtime secrets
  exist. Cookie assembly has focused tests,
  the route matrix rejects authentication errors, and the Daily Brief smoke now
  asserts the same boundary. A fresh authenticated matrix passed all 20 primary
  routes at desktop and mobile widths on 2026-08-25.
- **Bounded Portfolio Overview and Accessibility:** The portfolio index no
  longer blocks on deep analytics or snapshot calculations. It retains holdings
  and trust-gated valuation status and links to owned detail workspaces for the
  expensive calculations. Market Regime controls now have programmatic labels
  and a responsive layout. The desktop/mobile smoke matrix covers 20 primary
  routes and includes typography minimums. All 20 routes now pass authenticated
  desktop and mobile renders, stream completion, the 15-second readiness budget,
  error rejection, overflow, semantic names, typography, focus, and screenshots.
  The separate mobile drawer test passes keyboard open, close, Escape, and focus
  restoration. See
  [`archive/checkpoints/2026/authenticated-20-route-matrix-checkpoint-2026-08-25.md`](archive/checkpoints/2026/authenticated-20-route-matrix-checkpoint-2026-08-25.md).
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
- **Valuation tab completion:** Company valuation lists use compact owner-scoped
  readiness summaries, while detail routes read one model directly and allow
  metadata edits. Save-and-calculate is one transaction and no longer leaves an
  assumption set behind after a calculation failure. The full workspace now
  preserves payout, cost-of-capital, story, equity-bridge, and currency inputs;
  currency choices and override rationale are durable. Missing dependencies and
  action failures are visible, and critical diagnostics suppress unreliable
  estimates in both full and quick workflows. Currency fields were introduced
  at `h9h9h9h9h9h9`; the current source head is `o6o6o6o6o6o6`.
- **Source-backed valuation inputs:** Migration `i0i0i0i0i0i0` links assumption
  methods to active dataset versions and expands growth and financing-flow
  storage. January 2026 India workbooks now seed risk-free rates, ERP, beta,
  cost of debt, capital weights, WACC, country and industry tax, 2Y/5Y growth,
  and financing-policy context with exact file/hash/date/row/column provenance.
  Autofill no longer uses hardcoded India rate fallbacks, is currency and
  industry aware, exposes every DCF input plus a readiness contract, and never
  treats aggregate industry financing flows as company facts. See
  [`archive/checkpoints/2026/valuation-input-seeding-checkpoint-2026-08-25.md`](archive/checkpoints/2026/valuation-input-seeding-checkpoint-2026-08-25.md).
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
- **Audited FRED Ingestion:** FRED imports now require authentication, normalize
  and validate the series ID, preserve the official series URL, update metadata,
  count created, duplicate, missing, and rejected observations, and record a
  sanitized Processing Run on success or failure. Provider Health recognizes
  the actual `partial_success` state instead of dropping it into unknown status.
- **Market Regime:** Inputs are bounded to the documented scale and require
  source name, date, type, and methodology. Provider inputs require a source
  URL. Scores distinguish Manual, Mixed, Live, Stale, and Incomplete modes and
  expose input provenance, formula, blockers, warnings, and confidence. FRED
  NFCI can now be previewed and applied from an exact stored observation using
  the disclosed `clamp(-NFCI × 50, -100, 100)` Calculation. It is idempotent,
  freshness-aware, and linked to the macro observation record. Declared provider
  entries without a stored record are Source Summaries, not Facts.
- **AI Evidence Review:** Approval requires source markers, declared-source
  consistency, exact stored-text validation for every cited source, successful
  execution, nonempty output, and no prohibited recommendation language.
  Reviewers can now request local deterministic passage candidates with exact
  offsets, numeric-aware lexical coverage, confidence, limitations, and source
  links. Selecting a candidate fills the draft only; validation and approval
  remain separate gates. The relevant backend tests passed within the latest
  584-pass container run; backend compile, 122 frontend tests, and TypeScript
  also pass.
- **Unified Stored-Research Search:** `/search/evidence` now covers shared
  documents, events, narratives and owner-scoped alerts, theses, decisions,
  valuations, research-session titles, user messages, and approved AI output.
  Pending, blocked, failed, unreviewed, and cross-user AI output is excluded.
  Results carry claim type, shared/private scope, review state, mock state,
  bounded excerpts, timestamps, and stable destination anchors. Its focused
  authenticated browser workflow passed, and its backend coverage passed inside
  the latest broad container run. TypeScript and all 122 frontend tests pass.
- **AI DCF Variable Mapping (Priority 3 Expansion):** Added a new AI service and `/ai/map-event-to-dcf` endpoint to map market events to DCF variables, accessible via the new `DcfImpactPredictor` component on the events page.

- **Morning Briefing Engine (Priority 3):** Completed the Morning Briefing dashboard overhaul. Connected ingestion, evidence, alerts, thesis changes, valuation relevance, and portfolio exposure. Implemented persisted `reviewed_at` waterline management, sanitized processing-failure facts, a source-backed inspection queue, and AI contradiction detection. Unreviewed contradictions are visible in Data Health.
- **India Provider & Identity Coverage (Priority 2):** Expanded standard methodology to parse minority interests, cross-holdings, operating leases, and diluted shares. Updated frontend company UI and DCF components to display these structural elements explicitly. Added RELIANCE on NSE to the certification manifest and integrated manual provider UI badges for non-US companies.

## Next Recommended Work

First fix conditional saved-input preservation: the browser recovery check found
that saving a standard FCFF model omits its saved book equity because that field
is rendered only for financial-services models. Audit all lifecycle-specific
fields and preserve values outside the active form; previous versions remain intact.

Then audit Reverse DCF and Real Options in
`advanced-workspace.tsx`. Reverse DCF still defaults an absent price to 100 and
labels it with a dollar sign. Check saved-input currency, stale/critical gates,
numeric validation, request isolation, and source labels in both panels and
their APIs. Output-card and scenario repairs do not certify these separate
workflows. Keep the remaining boundaries in the single limitations ledger.

Finish the manual portfolio smoke with real, source-labeled inputs containing
two complete snapshot dates,
one non-base-currency holding, one configured benchmark, at least 20 aligned
return observations per holding, and one trusted Base DCF output. Verify the
dashboard stays read-only and no longer renders a latency budget as partial data.
The normal database currently has no portfolio, holding, snapshot, price, FX,
benchmark, or usable DCF-output records, so this gate requires genuine user
inputs and must not be satisfied with the isolated Mock Data fixture. Use the
new source-labeled evidence bundle on the owned portfolio page to preview
and atomically load the required historical price and FX rows. It only accepts
linked positive holdings, the active benchmark, and portfolio-required currency
pairs, so holdings and benchmark configuration must exist first. Then capture
the two snapshot boundaries and complete the trusted Base DCF. Rerun
the new read-only readiness audit from the owned portfolio page or CLI; proceed
with the manual smoke only when it reports `ready`. The complete authenticated
20-route desktop/mobile matrix is now green using disposable local credentials
and isolated reference fixtures without reading protected project auth
configuration. That matrix validates route integrity, not genuine portfolio
facts. The scheduler runtime evidence is archived at
[`archive/checkpoints/2026/daily-brief-scheduler-runtime-checkpoint-2026-08-24.md`](archive/checkpoints/2026/daily-brief-scheduler-runtime-checkpoint-2026-08-24.md).

The preceding runtime increment passed backend compile, all 122 frontend tests,
TypeScript, the documentation checker, and authenticated browser checks for
Data Health, financial certification, industry allocation, and default-first DCF
creation. The user-run backend suite reached 584 passes with four upstream
`openpyxl` warnings. The scheduler image built, its container started, readiness
reported the expected migration and schema, and the Daily Brief browser workflow
passed. A real due scheduler cycle checked one schedule, completed it without
failure, created brief `2`, recorded sanitized Processing Run `1`, cleared the
lease, and advanced the next run. A repeated due cycle recorded Processing Run
`2`, reused brief `2`, and reported `created_count = 0`. Focused Daily Brief
tests passed 20/20; focused portfolio/dashboard tests passed 16/16; all 122
frontend tests and TypeScript passed. The subsequent real-input readiness
increment passes 11 focused backend tests, 123 frontend tests, and TypeScript.
The subsequent FRED/NFCI boundary passes all 604 backend tests, 30 focused
backend tests, all 124 frontend tests, TypeScript, and a single-head Alembic check
at `f7f7f7f7f7f7`. The portfolio evidence boundary then passes all 619 backend
tests, all 125 frontend tests, TypeScript, 15 focused importer tests, response
  contract inventory, and an empty-PostgreSQL full-chain migration to the single
  head `g8g8g8g8g8g8`. At that checkpoint the normal database remained at
  `ee6ee6ee6ee6`; it is now upgraded to `o6o6o6o6o6o6`.
The latest valuation increment passes all 774 backend tests with the repository
workbook data available, 127 focused input/pricing/peer/error-contract tests, all 138 frontend
tests, TypeScript, a production frontend build, and a fresh PostgreSQL
full-chain migration check at `o6o6o6o6o6o6`. A populated m4-to-n5 fixture
preserved two legacy sets with null receipts, rejected duplicate non-null
owner/company/hash receipts, and downgraded without row loss. A separate l3-to-m4 fixture
upgrade preserved existing peer sets and revisions with empty target defaults.
The earlier k2-to-l3 fixture proved normalized current and revision-member
backfill, including legacy strings and duplicate suppression. A real PostgreSQL service smoke proved
create and same-identifier update behavior. The normal backend, frontend,
PostgreSQL, and scheduler services are healthy at that head. Backend readiness
also reports no missing required tables, columns, or unique constraints.
The native host Next.js build still depends on a compatible macOS SWC binary;
the supported Docker production build is green. Do not weaken secret protections
to make host-only tooling pass.

## Commands

```bash
cd "/Users/mananmaheshwari/Documents/Codex/Market Intelligence App/market-intelligence-md-files copy"
cp -n .env.example .env
docker compose up --build -d
docker compose exec backend alembic upgrade head
docker compose --profile automation up --build -d scheduler
curl http://localhost:8000/api/health
curl http://localhost:8000/api/readiness
```

Validation:

```bash
docker compose exec -w /workspace/backend backend pytest -q tests/test_daily_brief.py tests/test_persisted_daily_brief.py tests/test_api_daily_brief.py tests/test_daily_brief_schedule.py tests/test_api_daily_brief_schedule.py
cd frontend && npm run test:e2e:brief && cd ..
docker compose exec -w /workspace/backend backend pytest -q tests/test_portfolio_risk_return.py tests/test_api_portfolio_performance.py
cd frontend && npm run test:e2e:portfolio && cd ..
docker compose exec -w /workspace/backend backend pytest -q tests/test_pytest_layout.py tests/test_assumption_diff_service.py tests/test_api_evidence_search.py tests/test_ai_citation_suggestions.py tests/test_ai_citations.py tests/test_api_daily_brief.py tests/test_api_dashboard_overview.py tests/test_daily_brief.py
docker compose exec -w /workspace/backend backend pytest -q
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
- Valuation assumptions need provenance and explicit review. Advanced-workspace
  edits are explicitly User Assumptions; draft-source provenance remains the
  stronger field-level record.
- Reviewed peer sets are user-reviewed evidence, not independently verified
  market facts. Editing, restore-as-draft, immutable lifecycle history, and
  stale-write rejection are built. Peer members and optional target profiles
  have normalized current/revision rows plus JSON consistency boundaries.
- Peer medians do not adjust for outliers, size, growth, margins, accounting,
  currency, fiscal-period alignment, or other comparability differences. These
  conditions produce warnings only. Target facts remain user-supplied. CSV v2
  carries the target profile, while legacy member-only CSV remains accepted with
  an explicit missing-target warning.
- The current normal database contains no reviewed company financial histories
  or matching company mappings for the supplied benchmark workbooks. Benchmark
  priors are seeded, but starting revenue, company margins, bridge items, shares,
  price, and company payout facts remain unavailable until the user loads and
  reviews company source files. Do not invent them.
- No broker credentials and no buy/sell recommendation language.
- Use the Damodaran knowledge base for valuation doctrine; use application docs
  for runtime behavior.

## Documentation Rule

Current docs describe present behavior. Archived docs preserve history. New
shipped work should update current state, feature register, affected core docs,
and this handoff. Do not append another chronological mini-handoff.

The previous 1,232-line cumulative handoff is preserved at
[`archive/handoffs/HANDOFF-history-through-2026-08-08.md`](archive/handoffs/HANDOFF-history-through-2026-08-08.md).
