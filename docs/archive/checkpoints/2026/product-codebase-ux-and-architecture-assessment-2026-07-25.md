# Product, Codebase, UX, and Architecture Assessment

**Audit date:** 2026-07-25  
**Status:** Active baseline for prioritization  
**Confidence:** Medium-high for code structure and automated behavior; medium for
daily usability because a full authenticated visual pass of every route was not
repeated during this audit.

## 1. Direct Answer

The honest quality-adjusted completion estimate is:

- **About 58% complete against the defined local-first product brief**
- **About 47% complete against a genuinely world-class daily research tool**
- **About 70% complete if completion is measured only by feature surface**

The 70% number is misleading on its own. There are many pages, models, routes,
and calculations. Several are real and substantial. But a world-class tool is
not measured by how many screens exist. It is measured by whether a user can
reliably move from source to decision, understand every limitation, trust every
boundary, and repeat the workflow daily without fighting the system.

The product is past the prototype stage. It is not close to production
readiness. The strongest area is deterministic valuation. The weakest areas are:

1. backend authorization consistency
2. frontend styling and responsive coherence
3. research/AI ownership and provenance
4. data transfer correctness
5. real-source data certification
6. point-in-time data governance
7. workflow integration across research, valuation, and portfolio decisions
8. operational discipline around CI, repository state, backups, and monitoring

The correct direction is not to add more top-level modules. It is to make the
existing product coherent, trustworthy, and fast enough to use every day.

### Post-audit implementation checkpoint

The first 30 R1 execution steps were implemented after this baseline was
measured:

- the aggregate FastAPI router is now authenticated by default
- only `GET /api/health` and `GET /health` are public application routes
- an automated dependency-aware route inventory protects that classification
- research create/list/read/message/delete operations resolve the current user
- CSV exports are real files and portfolio transfer is owner scoped
- imports enforce byte, row, schema, decimal, date, currency, enum, reference,
  duplicate, and ownership validation
- preview is read-only and portfolio transaction apply is atomic

Focused tests pass, the complete backend suite now reports 334 passed, frontend
tests/typecheck/build pass, and live unsigned direct-port checks return `401`.
Sections 6.1 through 6.3 below are retained as the evidence that selected the
work; their defects are superseded by this checkpoint.

The 58% and 47% scores remain the dated baseline rather than being moved after
one batch. The R1 error/request-ID/AI control batch is now implemented; a formal
re-score should follow the remaining R1 edges and the R2 styling acceptance
gate. CSV is now tested interchange, not a backup, until a restore drill
succeeds.

## 2. Audit Method

This assessment used the current code rather than roadmap completion claims.
The audit included:

- backend route, model, service, provider, migration, and test inventory
- frontend page, component, client, server action, style, and test inventory
- static inspection of authentication, ownership, response envelopes, errors,
  AI behavior, imports/exports, data states, CSS, and responsive layout
- live local health and representative access checks
- full backend tests
- full frontend tests
- TypeScript type checking
- production frontend build
- review of the current handoff, architecture, runbook, capability audit, and
  active ideation register

The audit did not claim that every endpoint or page was manually exercised.
That would require a separate authenticated browser matrix and representative
real data.

## 3. Measured Repository Shape

### Backend

| Measure | Current result |
|---|---:|
| Application Python lines | 22,927 |
| Application Python files | 180 |
| Router modules | 43 |
| API operations | 271 |
| SQLAlchemy model classes | 84 |
| Model files | 35 |
| Service files | 68 |
| Provider files | 20 |
| Alembic migrations | 28 |
| Backend test files | 81 |
| Largest schema file | 1,863 lines |
| Largest service | 756 lines |
| Largest router | 507 lines |

### Frontend

| Measure | Current result |
|---|---:|
| TypeScript/TSX lines in app/components/lib | 20,212 |
| TypeScript/TSX files | 123 |
| App Router pages | 40 |
| Component files | 53 |
| Frontend test files | 11 |
| Playwright specs | 3 |
| Server action functions | 120 |
| Exported API client functions | 72 |
| Largest API client file | 2,235 lines |
| Largest server action file | 942 lines |
| Largest page | 495 lines |
| Largest component | 577 lines |
| Inline style objects | 913 |
| Explicit `any` uses | 61 |
| Route loading boundaries | 0 |
| Route error boundaries | 0 |
| Route not-found boundaries | 0 |

### Repository and operations

| Measure | Current result |
|---|---:|
| Dirty worktree entries | 422 |
| Modified files | 147 |
| Deleted files | 21 |
| Untracked entries | 254 |
| CI workflow files | 0 |
| Frontend lint script | 0 |
| Configured coverage threshold | None |

This is a large application, not a small MVP. The main engineering problem is
now consolidation and control, not lack of code.

## 4. Completion Methodology

The score is quality-adjusted. Each capability is scored for:

- real implementation
- end-to-end usability
- source and limitation honesty
- ownership/security
- automated verification
- operational repeatability

### Local-first product score

| Capability | Weight | Score | Weighted result |
|---|---:|---:|---:|
| Platform foundation and raw-data custody | 10% | 80% | 8.0 |
| Company setup and ingestion | 10% | 65% | 6.5 |
| Financial extraction and normalization | 15% | 60% | 9.0 |
| Valuation and scenario modeling | 15% | 80% | 12.0 |
| Events, evidence, alerts, thesis, and narratives | 15% | 50% | 7.5 |
| Portfolio lifecycle and analytics | 10% | 55% | 5.5 |
| Frontend workflow and usability | 10% | 35% | 3.5 |
| Provider coverage and automation | 5% | 35% | 1.75 |
| Reliability and operations | 5% | 55% | 2.75 |
| Security and data governance | 5% | 30% | 1.5 |
| **Total** | **100%** |  | **58%** |

### Why the world-class score is lower

The world-class bar gives more importance to:

- exact evidence navigation
- global search and change detection
- licensed provider breadth
- point-in-time and revision-aware facts
- portfolio attribution and reporting
- consistent visual and interaction design
- operational recovery
- security that cannot be bypassed through another local port

Against that bar, the current implementation is approximately **47%**.

This estimate should be updated only when an acceptance gate changes from
partial to verified. Adding a page without closing its data, security, and
workflow gaps should not move the percentage.

## 5. What Is Actually Strong

### 5.1 Valuation is the product's deepest capability

The valuation system has real domain depth:

- FCFF DCF
- reinvestment and ROIC logic
- WACC
- terminal-value guardrails
- bear/base/bull scenarios
- sensitivity tables
- reverse DCF
- FCFE and DDM
- relative valuation
- macro sensitivity
- real options
- Damodaran benchmark ingestion
- reviewed setup drafts and optimistic concurrency

This is substantially ahead of a typical dashboard prototype. The math is
separated into services and has meaningful backend coverage.

The remaining valuation problem is not another model. It is input truth:

- representative real-source histories
- exact evidence behind material assumptions
- explicit point-in-time inputs
- reliable currency conversion
- clearer visual review of assumptions and changes

### 5.2 Source custody is directionally correct

The product stores:

- raw documents
- source metadata
- content hashes
- processing runs
- extracted candidates
- original PDF assets
- structured evidence locators

The recent evidence work also prevents full filing bodies and provider payloads
from leaking through alert evidence responses. That is the right product
instinct.

### 5.3 The API envelope is widely adopted

Of 271 operations:

- 217 declare a response model
- 215 use the standard `ApiResponse` envelope

The remaining non-envelope routes include legitimate binary/download and
no-content cases, but also older endpoints that need cleanup.

### 5.4 Data-state honesty is better than average

The frontend has explicit stale, partial, mock, empty, and error concepts. The
market-regime page labels itself as simulated. Missing portfolio prices are not
silently treated as zero.

This is a meaningful strength. It should become a universal contract rather
than a set of components used unevenly.

### 5.5 The test baseline is substantial

Current verification:

```text
Backend: 334 passed, 4 third-party warnings
Frontend: 63 passed
TypeScript: clean
Production frontend build: successful
```

Two isolated authenticated Playwright workflows were verified previously. A
third alert-evidence spec exists but has not completed against a clean rebuilt
E2E image.

The number of tests is not the main problem. The missing test classes are.

## 6. Critical Findings

### 6.1 Backend authentication is not the default boundary

**Checkpoint status:** Superseded on 2026-07-25 by aggregate auth-by-default,
the two-route public health allowlist, automated route inventory, direct-port
negative tests, and live `401` verification.

The Next.js application protects pages and signs short-lived identity
assertions for protected backend calls. That design is reasonable for a local
single-user application.

The FastAPI router does not require authentication globally.

Static route inspection found:

- 100 operations with direct `current_user` or `_user` dependencies
- 4 more operations protected by the admin router dependency
- approximately 167 operations without that direct authentication boundary
- 61 unauthenticated POST operations
- 16 unauthenticated PATCH operations
- 17 unauthenticated DELETE operations

Some reference-data reads may intentionally be public. Many company, source,
document, event, narrative, social, market-price, AI, and transfer operations
are not suitable for a public allowlist.

The live local check confirmed the inconsistency:

```text
GET /companies -> 200 without identity headers
GET /portfolios -> 401
GET /alerts -> 401
GET /export/portfolio-holdings -> 500
```

Because FastAPI is published on port 8000, the frontend proxy is not a security
boundary. A caller can bypass it.

**Required direction:** require authentication for the root API router and
create a small explicit public allowlist for health/readiness endpoints. Add an
automated route-inventory test so a new endpoint cannot accidentally become
public.

### 6.2 Research sessions have production ownership defects

**Checkpoint status:** Superseded on 2026-07-25. Session creation persists the
current user; list/read/message/delete operations resolve an owned parent;
caller-created assistant messages are rejected; cross-user tests pass. The
research UI and AI provenance behavior remain incomplete.

`POST /research/sessions` constructs `ResearchSession(title=...)` without
setting the required `user_id`. The shared backend test fixture automatically
fills missing `user_id` fields, which hides this production defect.

`POST /research/sessions/{id}/messages` resolves the session by numeric ID
without current-user ownership filtering. It can therefore append to another
user's session if the backend is used in a multi-user context.

The frontend research pages also rely heavily on `any`, browser alerts, and a
synchronous AI call. They are closer to a prototype than a trusted workspace.

### 6.3 CSV data transfer is broken and unsafe

**Checkpoint status:** Superseded on 2026-07-25 for manual interchange. Exports
are real files, model/relationship fields are correct, portfolio data is owner
scoped, imports are bounded and validated, preview is read-only, and
transaction apply rolls back atomically. Browser transfer coverage and a
restore drill remain open, so this is not yet a backup system.

The transfer router has several independent problems:

- export routes are not authenticated or user-scoped
- portfolio exports query every user's rows
- routes wrap a FastAPI `Response` inside `ApiResponse.data`
- raw-document export references `source_name` and `source_type` attributes
  that do not exist on `RawDocument`
- file-size and row-count limits are not enforced consistently
- database exception strings are returned to callers
- import ownership is not verified
- portfolio IDs from CSV are trusted without resolving an owned parent
- there are no focused transfer-route tests

The live export returned HTTP 500. Documentation that says CSV import/export is
working is currently wrong.

### 6.4 AI provenance and privacy are incomplete

There are multiple AI paths with different behavior:

- document summaries
- research chat
- narrative-to-numbers
- valuation memos
- event impact classification
- valuation staleness simulation

Gaps identified in the original audit included the following. The 2026-07-26 R1
control checkpoint supersedes these items; citation verification and complete
human-review UX remain open:

- silent fallback from provider failure to mock output
- no first-class `is_mock` field on persisted AI output
- no consistent provider field
- no source-ID set for research chat
- no privacy disclosure before sending text to an external model
- MD5 input hashes in several services
- one service using Python's process-randomized `hash()`
- AI endpoints that do not enforce valuation ownership
- prompt language asking for a final recommendation
- mock staleness logic stored with a real-looking default model name

AI cannot be called source-backed merely because an output row has a model
name and prompt version.

### 6.5 Frontend styling infrastructure is internally inconsistent

The project explicitly documents "no Tailwind" and the package does not include
Tailwind. The frontend nevertheless contains approximately 1,273
Tailwind-like utility-class token occurrences.

Examples include:

```text
flex
grid-cols-4
bg-slate-900
text-sm
p-4
rounded-md
dark:text-slate-300
```

The global stylesheet defines only a small custom class set. A static scan found
hundreds of utility-like class names with no corresponding CSS definition.

This means many components compile but do not render as designed. TypeScript
and production builds cannot detect this class-level visual failure.

There are also:

- 913 inline style objects
- 28 referenced CSS custom properties not defined in `globals.css`
- only one global media query
- many fixed two- and three-column inline grids
- a 400px minimum width on topbar search
- no responsive behavior for several valuation and company workspaces

The frontend is therefore visually inconsistent by construction.

### 6.6 Global search is a non-functional promise

The topbar exposes a global search field and a `/` keyboard hint, but it has no
submission, navigation, shortcut, result model, or backend search endpoint.

This makes the application look more complete than it is. Until source-backed
search exists, replace it with a real command palette limited to navigation or
remove the field.

### 6.7 Repository state is an operational risk

The current worktree has 422 dirty entries, including:

- deleted historical migrations
- untracked replacement migrations
- many untracked core source files
- untracked tests and docs
- ad hoc root diagnostic scripts
- an untracked `frontend/.env.local`

The application may work locally, but the repository does not currently provide
a reviewable release unit. A clean clone cannot be assumed to reproduce the
same state until the intended changes are organized and committed.

`.env*.local` and log files are now ignored, but existing local files still
need to remain uncommitted and any actual secret must be rotated if it was ever
shared.

### 6.8 Error handling leaks internals and lacks one contract

The backend has at least 37 paths that expose `str(exception)` through API
responses or persisted run errors. Some are validation messages; others can
include database or provider implementation details.

The global response-validation handler writes to a hardcoded
`/workspace/backend/error.log` and returns raw validation errors. Error codes
exist, but they are not the universal behavior.

### 6.9 Point-in-time truth is mostly absent

Across 84 model classes, only a small number of fields explicitly represent
`as_of`, effective, observed, or revision time.

For an investment system, `created_at` is not enough. The product needs to
distinguish:

- when a fact was economically effective
- when the source published it
- when the application observed it
- whether it was later revised
- which value was visible when a decision was recorded

Without this, backtests, decision reviews, estimate revisions, and historical
valuation reconstruction can contain hindsight.

## 7. Backend Architecture Assessment

### What is working

- FastAPI, SQLAlchemy, Pydantic, PostgreSQL, and Alembic are appropriate.
- There is a real service layer.
- Provider abstractions exist for multiple source types.
- Processing-run records are a good operational primitive.
- Router registration is centralized.
- The HMAC identity assertion avoids recursive auth calls.
- Database indexes and foreign-key cascades are broadly present.

### What needs improvement

#### Split the schema monolith

`backend/app/api/schemas.py` is 1,863 lines. It should be split by domain:

```text
schemas/
  common.py
  companies.py
  documents.py
  intelligence.py
  portfolio.py
  valuation.py
  research.py
  providers.py
```

Do this incrementally by router group. Do not rewrite every import at once.

#### Keep routers thin

The largest routers contain validation, persistence orchestration, import
parsing, provider access, and response construction in one file. The transfer,
fundamentals, portfolios, companies, and valuation routers should call
domain services and ownership-aware repositories.

#### Consolidate provider placement

Provider logic is split between:

```text
backend/app/providers/
backend/app/services/market_data/
```

There are also old and new abstractions for related responsibilities. Provider
adapters should live under `providers/`; domain orchestration should live under
`services/`.

#### Add explicit transaction boundaries

Some multi-step workflows commit repeatedly. Examples include AI session
message creation and assistant generation. The system needs explicit states:

```text
accepted -> processing -> completed
                       -> failed
```

A provider failure should not produce an ambiguous half-completed workflow or
silently substitute mock intelligence.

#### Version and normalize route paths

Only 20 operations are currently `/api/...` prefixed while 251 are rooted
directly. This inconsistency causes frontend route mistakes and makes future API
versioning harder.

Do not mass-rename routes immediately. First introduce a compatibility map and
choose one canonical namespace for new work.

## 8. Data Architecture Assessment

### Strong

- raw-source custody
- content hashes
- processing-run tracking
- normalized financial snapshots
- review-gated candidates
- evidence locators
- explicit portfolio decimal storage
- source capability metadata

### Partial

- canonical financial coverage
- cross-currency truth
- source freshness
- provider conflict resolution
- real India source coverage
- adjustment and restatement history
- exact event-to-source spans

### Missing or inadequate

- first-class bitemporal fact model
- data revision identity
- corporate-action ledger
- source-backed FX history
- backup and restore policy
- retention policy for raw documents and PDFs
- corpus search index
- representative production-data certification suite

The next data-model work should establish point-in-time fields before adding
consensus estimates, transcripts, or backtesting.

## 9. Frontend and UX Assessment

### Current product experience

The application exposes a wide surface:

- dashboard
- portfolio
- market regime
- companies
- narratives
- research
- macro
- valuation
- alerts
- events
- ingestion
- data health
- admin
- settings

Additional pages for documents, sources, prices, thesis notes, social data, and
daily briefs are reached indirectly or are absent from the primary nav.

The result is breadth without a clear mental model.

### Recommended information architecture

Use five primary groups:

1. **Today**
   - Overview
   - Alerts
   - Daily Brief
2. **Research**
   - Companies
   - Search
   - Documents
   - Narratives
3. **Portfolio**
   - Holdings
   - Attribution
   - Exposures
   - Market Context
4. **Models**
   - Valuation
   - Macro
5. **Operations**
   - Ingestion
   - Sources
   - Data Health
   - Settings
   - Admin

This should be a grouped, collapsible sidebar on desktop and a drawer on narrow
screens.

### Company workspace

The company page currently presents many independent buttons and panels. Make
the company the stable workspace shell:

```text
Overview | Filings | Financials | Thesis | Evidence | Decisions | Valuation
```

Keep company identity, price freshness, setup status, active alerts, and latest
filing visible in a compact header across all tabs.

### Dashboard direction

The dashboard should answer four questions:

1. What changed since the last review?
2. What is unreviewed or broken?
3. Which thesis or valuation is affected?
4. What data needs attention?

It should not lead with generic counts. Recommended first viewport:

- unreviewed alerts ranked by portfolio/thesis impact
- changed thesis assumptions
- stale or blocked valuations
- failed/stale ingestion
- upcoming or missing review tasks

Portfolio value and tracked-company count are secondary context.

### Data state behavior

Use Next route boundaries:

```text
loading.tsx
error.tsx
not-found.tsx
```

Keep component-level partial states for panels. This prevents one failed
request from turning a whole page into a generic error.

### Visual system

The current glass-like surfaces, shadows, metric-card movement, and large page
headings are more decorative than a repeated-use research tool needs.

Recommended direction:

- opaque surfaces
- restrained shadows
- compact 24-28px page titles
- denser tables
- stable tabs
- consistent badges and data-state colors
- one documented spacing scale
- one real styling system
- charts only where trend or comparison cannot be read faster in a table

### Accessibility

Priority gaps:

- keyboard navigation through sidebar, tabs, drawers, and tables
- focus trapping and return focus for the evidence drawer
- responsive labels for wide data tables
- non-color status cues
- automated accessibility checks on core workflows
- reduced-motion handling for hover movement and transitions

## 10. Efficiency and Performance Assessment

### Current strengths

- server-rendered pages often load independent requests with `Promise.all`
- browser and server API calls have a 15-second timeout
- raw-document list views use bounded summaries
- large binary content is streamed separately
- current production build succeeds

### Current inefficiencies

- dashboard renders seven base requests plus optional analytics
- portfolio pages issue per-portfolio valuation, analytics, and snapshot calls
- pages fetch broad collections and filter them in application code
- client API and server action files are large central bottlenecks
- no request tracing links frontend calls to processing runs
- no cache/freshness policy beyond broad `no-store`
- no pagination contract is consistently visible
- ingestion and AI provider calls can block request threads
- no performance budgets or representative dataset benchmarks exist

### Recommended approach

1. Add purpose-built aggregate endpoints for the dashboard and portfolio
   overview.
2. Add pagination/filter/sort contracts to collection endpoints.
3. Measure first. Do not introduce Redis or a job queue based only on size.
4. Move only measured long-running ingestion/provider work to background jobs.
5. Add request IDs and structured timing metadata.
6. Define budgets for dashboard render, company overview, large tables, search,
   and ingestion status.

## 11. Test and Reliability Assessment

### What the suite proves

- a large amount of deterministic domain logic works
- many API success and validation paths work
- valuation mathematics has meaningful coverage
- key frontend helper contracts compile and behave
- selected authenticated workflows can pass in an isolated stack

### What the suite does not prove

- every backend operation requires authentication
- every child resource enforces parent ownership
- real PostgreSQL behavior for ordinary tests
- data-transfer correctness
- visual styling correctness
- responsive behavior
- accessibility
- real-source India/US normalization
- provider outage and retry behavior across the product
- backup and restore
- performance with representative data volume

### Test-fixture risk

The shared backend fixture:

- automatically authenticates requests
- automatically fills missing `user_id` on new models
- uses SQLite in memory

This is convenient but can hide production defects. The research-session
creation bug is an example.

Add separate test layers:

```text
unit: pure services and formulas
api-auth: no automatic auth or user-id injection
api-domain: authenticated SQLite tests where suitable
postgres-integration: migrations, constraints, indexes, and representative queries
browser: isolated authenticated critical workflows
```

## 12. Planning and Documentation Assessment

### What improved

- current docs now distinguish shipped, partial, proposed, and mocked behavior
- historical world-class plans are archived
- acceptance gates exist for many proposed capabilities
- validation commands are recorded
- the active ideation register is a better control point than dozens of phase
  documents

### What still needs correction

- the execution runbook marks broad phases complete even when important
  subfeatures are broken
- the capability audit says CSV transfer works, but live export returns 500
- auth documentation overstates the backend boundary
- AI provenance descriptions do not capture silent mock fallback and missing
  ownership
- frontend build success is treated too closely to UI correctness
- accumulated "completed phases" create a false sense of product completion

Planning should use acceptance gates, not phase labels. A feature is shipped
only when its data, security, UX, and verification gates pass together.

## 13. What I Would Use Today

I would use the application today for:

- local company tracking
- controlled SEC/RSS ingestion
- raw document custody
- manually reviewed financial extraction
- Damodaran benchmark exploration
- DCF, sensitivity, reverse DCF, and related valuation work
- basic portfolio entry and valuation context
- alert review where document-level evidence is sufficient

I would not rely on it today for:

- private research chat
- multi-user separation
- CSV backup/export
- market regime decisions
- automated India filing/fundamental coverage
- exact claim citations
- historical decision attribution
- public deployment
- unattended monitoring
- source-backed AI conclusions
- complete portfolio accounting

## 14. Feasible Build Plan

The sequence below replaces feature-first expansion with risk-first
consolidation.

### Phase A: Correctness and security closure

#### A1. Protect the backend by default

**Effort:** Medium  
**Value:** Critical

- require `get_current_user` on the root API router
- explicitly allow only health/readiness/reference endpoints that are truly
  public
- add a route-inventory test
- preserve service-to-service and browser-proxy behavior
- verify every mutation without identity returns 401

#### A2. Repair research-session ownership

**Effort:** Small  
**Value:** Critical

- set `ResearchSession.user_id`
- resolve message parent through current-user ownership
- add cross-user tests
- return typed response models
- stop using shared fixture injection as proof of production behavior

#### A3. Repair and constrain data transfer

**Effort:** Medium  
**Value:** Critical

- return real CSV responses, not enveloped `Response` objects
- resolve source metadata through relationships
- scope portfolio exports/imports to current user
- enforce file size, row count, numeric, enum, currency, and ownership rules
- use transaction rollback for any invalid apply
- add preview/apply and formula-escaping tests

#### A4. Make AI output honest

**Effort:** Medium  
**Value:** Critical
**Status:** Foundation implemented 2026-07-26; citation verification and full
approve/reject UX remain.

- add provider, `is_mock`, source IDs, and disclosure fields
- replace MD5 and process `hash()` with SHA-256
- make provider failure explicit instead of silently producing mock output
- enforce valuation/research ownership
- remove recommendation language
- require review before AI changes assumptions or thesis state

#### A5. Standardize API errors

**Effort:** Medium  
**Value:** High

- replace raw exception strings with typed public errors
- add request IDs
- log structured internal details without fixed local log files
- keep provider secrets and response bodies out of logs

### Phase B: Frontend integrity and workflow coherence

#### B1. Restore one real styling system

**Effort:** Medium  
**Value:** Critical

The most feasible path is to formalize the utility system already used across
the codebase, then reconcile it with the product tokens. Removing more than a
thousand utility-token uses by hand is lower leverage.

Acceptance:

- utility classes render in production
- all referenced design tokens exist
- no component depends on undefined CSS custom properties
- dark utility classes do not create isolated dark panels in a light product
- representative screenshots pass at desktop, tablet, and mobile widths

#### B2. Rebuild the shell information architecture

**Effort:** Medium  
**Value:** High

- group primary navigation
- add a responsive sidebar drawer
- replace company action buttons with tabs
- make data health a real status indicator
- remove the fake global-search promise until navigation search is real

#### B3. Add route boundaries and resilient forms

**Effort:** Medium  
**Value:** High

- add `loading.tsx`, `error.tsx`, and `not-found.tsx`
- replace browser `alert()` with inline error states
- add timeout/retry to auth readiness
- preserve user input after failed writes
- add explicit success feedback

#### B4. Decompose frontend boundary files

**Effort:** Medium, incremental  
**Value:** High

Split:

```text
lib/api.ts -> lib/api/{domain}.ts
app/actions.ts -> app/actions/{domain}.ts
large pages -> route-local view components
```

Generate or validate TypeScript contracts from OpenAPI after the backend
response shapes stabilize.

### Phase C: Reliability and delivery discipline

#### C1. Establish a clean release baseline

**Effort:** Medium  
**Value:** Critical

- classify the 422 dirty entries
- preserve intended migration replacement history
- remove or archive ad hoc root diagnostics
- commit in reviewable phases
- prove a clean clone can build, migrate, test, and start

#### C2. Add CI and quality gates

**Effort:** Medium  
**Value:** High

Minimum gates:

```text
backend tests
PostgreSQL migration smoke
frontend tests
typecheck
production build
lint
auth route inventory
secret scan
selected browser workflows
```

Add coverage reporting for visibility. Do not impose a high global threshold
until the baseline is measured.

#### C3. Add backup and restore

**Effort:** Medium  
**Value:** High

- database backup
- document/PDF backup
- encrypted storage option
- restore drill
- database/document consistency check
- retention notes

### Phase D: Product differentiation

Resume world-class research work only after Phases A and the styling part of B
are complete.

1. exact event page/section/span evidence
2. filing/PDF evidence highlighting
3. representative real US and India financial certification
4. point-in-time and revision-aware fact model
5. PostgreSQL full-text corpus search
6. period-over-period filing language diff
7. contradiction and falsification inbox
8. valuation assumption evidence graph
9. source-indexed research memo export
10. saved monitors and reviewed change queues

### Phase E: Portfolio depth

1. source-backed FX history and multi-currency accounting
2. benchmark-aware performance attribution
3. sector/country/currency/thesis-driver exposure
4. corporate-action ledger
5. point-in-time decision attribution
6. reusable portfolio review report

### Provider-dependent work

Do not build these without a source, license, cost, and point-in-time contract:

- India filing automation
- earnings-call transcripts
- consensus estimates
- options/gamma data
- institutional flow data
- external notification delivery

## 15. Immediate Next Ten Tasks

These are the next practical tasks, in order:

1. Completed 2026-07-25: automated backend route-auth inventory and explicit public allowlist.
2. Completed 2026-07-25: authentication by default at the backend router.
3. Completed 2026-07-25: research session/message ownership repair.
4. Completed 2026-07-25: real CSV exports and focused transfer-route tests.
5. Completed 2026-07-25: owned bounded CSV preview/apply and rollback.
6. Completed 2026-07-26: owned AI provider/mock/source/privacy/review/failure
   schema, SHA-256 provenance, explicit disclosure, and no silent fallback.
7. Formalize the frontend utility styling pipeline and define missing tokens.
8. Add responsive shell navigation and company workspace tabs.
9. Add route loading/error/not-found boundaries for dashboard, companies,
   portfolio, and valuation.
10. Add CI for tests, typecheck, build, migrations, auth inventory, and secret
    scanning.

After those ten tasks, return to exact evidence locators and source-backed
search.

### Post-Audit Control Update: 2026-07-26

The follow-on R1 batch also completed the distributed owned-domain negative
matrix, request IDs, stable safe public errors, JSON stdout logging, raw
exception cleanup, and weak-hash removal. Narrative extraction is no longer an
automatic ingestion side effect, and thesis-impact AI now produces proposals
rather than direct writes. Full verification is 334 backend tests, 63 frontend
tests, TypeScript, production build, and migration head `b8b8b8b8b8b8`.

The original 58% local-first and 47% world-class scores are intentionally not
raised. The audit's largest remaining weights are still frontend integrity,
reproducible delivery/recovery, exact evidence, representative real-source
certification, point-in-time data, and integrated daily workflows.

### Post-Audit Product-Integrity Update: 2026-07-26

The next five controls now supersede several findings in this dated audit:

- request IDs persist on processing runs and appear in lifecycle logs/status
- the route inventory reports zero legacy JSON responses and preserves
  explicitly classified binary/no-content responses
- Tailwind/PostCSS now compiles the existing utility vocabulary against owned
  design tokens; production build proof passes
- grouped responsive navigation, company workspace tabs, and root route
  boundaries are implemented; the fake global search field is removed
- research/AI failure and CSV recovery states pass isolated browser coverage
- CI and `scripts/verify_release_baseline.sh` pass a fresh migration plus all
  336 backend tests, 65 frontend tests, and TypeScript

The browser run also found and fixed an application-capacity defect: dense
Next.js link prefetch plus overlapping dashboard renders could exceed the old
database pool ceiling. Dense navigation no longer prefetches all route trees,
and the local pool has explicit bounded settings.

This is a superseding implementation note, not a re-score. The 58%/47%
figures remain the assessment baseline until the weighted audit is repeated.
Restore, exact locator, real-source, accessibility, performance, and integrated
workflow gates remain open.

## 16. Features to Remove, Hide, or De-emphasize

- Hide CSV export buttons until exports pass tests.
- Keep Market Regime clearly mocked; do not position it as a decision signal.
- Rename or hide source-backed AI claims until exact source links exist.
- Remove the global search field until it performs real navigation or search.
- De-emphasize Social as a top-level product area. Treat manually entered posts
  as another document source.
- Keep Admin and provider configuration under Operations.
- Do not add more valuation methods until input evidence improves.

## 17. Success Metrics

### Trust

- 100% of non-public backend operations require identity
- 100% of user-owned child writes resolve an owned parent
- 100% of AI outputs state provider, mock state, review state, and source scope
- 100% of material intelligence claims have an exact locator or explicit
  no-locator state

### Reliability

- clean-clone setup succeeds without manual code edits
- main branch CI is green
- restore drill succeeds
- no untested user-visible export/import route
- no provider failure silently becomes mock success

### UX

- zero undefined CSS variables
- zero unprocessed utility-class dependencies
- all core routes have loading and error boundaries
- desktop/tablet/mobile screenshot checks pass
- the top five daily workflows complete without navigating through Settings or
  Admin

### Data

- one reviewed real-source US history is trust-ready
- one reviewed real-source India history is trust-ready
- source-backed FX supports the portfolio's active currencies
- effective, observed, and revision timestamps exist for material facts

### Workflow

- alert -> exact evidence -> thesis impact -> valuation impact -> portfolio
  impact is navigable without manual source searching
- every review disposition is durable and auditable
- daily dashboard prioritizes unresolved work rather than generic counts

## 18. Final Judgment

The codebase demonstrates strong domain ambition and a serious valuation
foundation. It also shows the cost of many rapid feature batches: duplicated
boundaries, uneven ownership, styling drift, oversized files, and documentation
that sometimes treats compiled or modeled behavior as shipped user value.

The architecture does not need a rewrite. It needs disciplined consolidation:

1. secure the boundary
2. fix the broken current workflows
3. restore one frontend system
4. establish clean delivery and recovery
5. deepen evidence and real-source data
6. add provider breadth only when the data contract is defensible

If that sequence is followed, the existing valuation and evidence work can
become a differentiated research tool. If the product keeps adding modules
before closing these gaps, the completion percentage will rise on paper while
actual usability and trust decline.
