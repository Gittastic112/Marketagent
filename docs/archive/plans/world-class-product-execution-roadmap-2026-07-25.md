# World-Class Product Execution Roadmap

> **Progress note, 2026-08-08:** Country statistics now preserve the exact
> source version, all meaningful workbook fields, active-only reads, and API
> provenance. Live Damodaran coverage is 9 supported, 13 partial, 13 unsupported,
> 14 typed sources, and 3,290 rows, with 12 complete active provenance records.
> Current source-specific typed replacement paths are closed; unsupported mirror
> breadth and historical macro provenance remain. The rounded product estimate
> remains 75% local-first and 64% world-class. See
> `roadmaps/next-5-damodaran-versioned-country-statistics-checkpoint-2026-08-08.md`.

> **Progress note, 2026-08-08:** The four Damodaran pricing workbooks now have
> independent preserved versions, complete source controls, and active-only
> relative-valuation assembly with method-specific provenance. Live coverage is
> 9 supported, 13 partial, 13 unsupported, 13 typed sources, and 3,163 typed
> rows; 11 active source versions have complete provenance with no mismatch.
> Country statistics remain the next replacement-path conversion. The rounded
> product estimate remains 75% local-first and 64% world-class because daily
> research integration, provider breadth, and portfolio depth remain unchanged.
> See `roadmaps/next-20-damodaran-versioned-pricing-and-relative-valuation-checkpoint-2026-08-08.md`.

> **Progress note, 2026-08-08:** Synthetic ratings now use all 45 exact rows
> from approved `ratings.xls` instead of approximate hardcoded bands. The WACC
> API supports three firm types, keeps legacy callers compatible, and exposes
> selected-band/source provenance while retaining unknown-date and
> user-assumed-recency warnings. Damodaran coverage is now 4 supported, 18
> partial, and 13 unsupported. The overall estimate remains 75% local-first and
> 64% world-class because this is a correctness improvement, not broad workflow
> completion. Backend validation is 434 tests. See
> `roadmaps/next-15-source-backed-synthetic-ratings-checkpoint-2026-08-08.md`.

> **Progress note, 2026-08-08:** Data Health now exposes the actual
> source-to-application coverage of all 35 Damodaran runtime workbooks. All
> mirrors are present, but only 8 have typed rows; the live database contains
> 2,693 typed records. The strict implementation assessment is 4 supported, 18
> partial, and 13 unsupported. This closes the coverage-inventory and honest
> visibility gate, not the ingestion-breadth gate. Validation is 422 backend
> tests, 90 frontend tests, TypeScript, production build, four knowledge-base
> tests, and a clean corpus audit. See
> `roadmaps/next-15-damodaran-coverage-checkpoint-2026-08-08.md`.

> **Progress note, 2026-08-07:** A new quality-adjusted review estimates the
> product at approximately **75% of the declared local-first scope** and **64%
> of the world-class daily-driver target**. This re-score reflects verified
> security, recovery, evidence, two-market certification, search, valuation,
> and workflow foundations delivered since the 2026-07-25 baseline. Feature
> surface is approximately 85%, but remains the wrong primary measure. Broad
> source coverage, point-in-time replay, integrated daily workflow, portfolio
> depth, and frontend consistency remain the main gap. See
> `roadmaps/product-agent-status-brief-2026-08-07.md`.

> **Progress note, 2026-08-02:** Representative real-source certification now
> passes through a portable AAPL/APSEZ manifest with markets `US` and `IN`.
> Data Health verifies promoted locators, fiscal period ends, and annual
> statement identities and derives live certification coverage. APSEZ passes
> 6/6 profit and attribution checks; AAPL explicitly records unavailable
> identity coverage under its approved core fact set. Financial PDF candidates
> with trusted point geometry now render bounded authenticated source-page
> overlays with direct-PDF fallback. Revenue-weighted industry assumptions expose source
> provenance and missing benchmark coverage, and draft refresh tracks normalized
> history changes. Current proof is 397 backend tests, 80 frontend tests, clean
> TypeScript, webpack production build, and Alembic head `j6j6j6j6j6j6`. This
> closes the representative two-market gate, not broad parser coverage or the
> full R4 point-in-time/reproducibility acceptance gate.

**Project:** Market Intelligence Engine  
**Baseline date:** 2026-07-25  
**Status:** Canonical forward execution plan  
**Primary truth source:** `product-codebase-ux-and-architecture-assessment-2026-07-25.md`  
**Repository location:** `docs/world-class-product-execution-roadmap-2026-07-25.md`

## 0. Executive Judgment

The product is already a substantial application, not an early MVP. The latest
audit measures it at:

- approximately **58% complete** against the defined local-first product brief
- approximately **47% complete** against a world-class daily research tool
- approximately **70% complete** if completion is measured only by feature
  surface, which is the wrong measure

Its strongest capability is deterministic valuation. Its strongest product
instinct is source custody and explicit data-state honesty. Its biggest problem
is that breadth has outrun control.

The path to world class is not another set of top-level modules. It is:

1. close security and correctness defects
2. make the frontend visually and behaviorally coherent
3. produce a reproducible release with recovery controls
4. certify evidence and real-source financial data
5. connect research, valuation, and portfolio work into one daily loop
6. add differentiated search, change detection, contradiction, and attribution
7. expand providers only behind legal, temporal, and provenance contracts

The product should be considered world class only when a user can move from:

```text
source
-> exact change
-> credibility
-> thesis impact
-> valuation impact
-> portfolio exposure
-> reviewed decision
```

without losing provenance, point-in-time truth, privacy, or workflow state.

This is a consolidation and product-integration program measured in sustained
delivery, not a short feature sprint.

## 1. Authority, Scope, and Precedence

### 1.1 Primary authority

The current-state baseline, prioritization, measured repository shape, quality
score, UX findings, architecture findings, security findings, and immediate
sequence in this roadmap come from:

- `product-codebase-ux-and-architecture-assessment-2026-07-25.md`

Treat that assessment as the closest available truth as of 2026-07-25.

The assessment is especially authoritative for:

- what is genuinely strong
- what is broken
- what is insecure
- what is visually unreliable
- what is operationally unreproducible
- what should be fixed before feature expansion
- the difference between implemented surface and daily-driver quality

This roadmap elaborates the assessment. It does not weaken or reorder its
Phase A-C priorities.

### 1.2 Secondary context only

The following documents provide product intent, terminology, implementation
history, or possible later work:

- `world-class-product-ideation-register.md`
- `HANDOFF.md`
- `agent_capabilities_and_limitations.md`
- `00-current-state.md`
- `01-product-brief.md`
- `02-architecture.md`
- `03-database-schema.md`
- `04-data-sources-and-ingestion.md`
- `05-scoring-framework.md`
- `06-security-threat-model.md`
- `07-local-development.md`
- `08-execution-runbook.md`
- `12-assumption-methodology-engine.md`

These are not treated as equally current. A feature claim from a secondary
document is not proof of current behavior.

### 1.3 Conflict and uncertainty rule

For this roadmap's baseline:

1. the 2026-07-25 product/codebase/UX assessment
2. current code and tests inspected during a new implementation task
3. this roadmap
4. secondary documents
5. archived plans

Apply these rules:

- If a secondary document conflicts with the assessment, the assessment wins.
- If a secondary document says “complete” and the assessment says partial,
  broken, unsafe, or unverified, use the assessment.
- If the assessment is silent on an older claim, treat the claim as
  **unknown/needs verification**, not shipped.
- A future code change can supersede the assessment only after its acceptance
  gate passes and current-state documentation is updated.
- Do not resurrect older feature-first priorities until the assessment's
  correctness, UX, and release-control work is closed.

### 1.4 Roadmap focus

The emphasis of this roadmap is deliberately:

1. product truth and current-workflow correctness
2. frontend UX integrity and coherent information architecture
3. backend/domain architecture and ownership boundaries
4. reproducible delivery, testing, performance, and recovery
5. evidence and point-in-time data architecture
6. integrated daily workflows
7. later differentiation and provider expansion

The later roadmap exists to describe the route to world class. It must not
distract from the immediate UX and architecture closure identified in the
assessment.

### 1.5 Product scope

The world-class target is a:

- local-first
- single-user
- source-backed
- public-equity research
- valuation
- portfolio-intelligence

system for a concentrated watchlist and portfolio, initially centered on
approximately 10 to 25 US and India companies.

It is not required to become a public SaaS product to satisfy this roadmap.

### 1.6 Explicitly outside the current target

- public internet deployment
- team tenancy and role-based collaboration
- broker credential storage or trade execution
- real-time trading infrastructure
- prohibited social scraping
- unlicensed transcripts or estimates
- a generic AI chatbot
- buy, sell, or guaranteed-return recommendations
- a Bloomberg imitation built through superficial feature breadth

Public deployment, multi-user tenancy, or broker connectivity would constitute
a separate product program with a separate security architecture.

## 2. Product North Star

Every core screen and workflow must help answer:

> What changed, why does it matter, how reliable is it, what does it challenge,
> what does it change in the valuation, and where is the portfolio exposed?

The product should optimize for five repeated jobs:

1. **Triage today:** identify what changed, what failed, and what needs review.
2. **Investigate a company:** move from a source to facts, thesis, assumptions,
   evidence, and valuation without changing mental context.
3. **Review a valuation:** understand every material input, source, calculation,
   override, warning, and invalidating event.
4. **Review the portfolio:** understand performance, concentration, shared
   drivers, stale inputs, and decision history.
5. **Produce durable work:** save a reviewed memo, decision, watchlist review,
   or portfolio report that remains reproducible as of a stated date.

Live prices are not the current product center. Until a proper provider-backed
track exists, the product should prioritize the intelligence it actually owns:
documents, events, alerts, evidence, processing state, financial review,
theses, valuation, and decisions.

When live or delayed prices are added, they must be:

- ingested through the backend
- cached in the database
- source and timestamp labeled
- separate from financial-statement trends
- separate from valuation assumptions and outputs
- explicitly stale or unavailable when the provider fails

## 3. What “100% World Class” Means

World class means complete within the declared product boundary, not universal
coverage of every asset class, provider, or valuation method.

| Dimension | World-class pass condition |
|---|---|
| Truth | Every material output identifies whether it is reported fact, calculation, assumption, estimate, AI interpretation, user judgment, or mock/test data. |
| Provenance | Every material claim links to a source, timestamp, and exact locator, or explicitly states that an exact locator is unavailable. |
| Point-in-time integrity | The system can reconstruct what data and assumptions were visible when a review or decision occurred. |
| Security | Every non-public backend operation requires identity, every user-owned child resolves through an owned parent, and direct port access cannot bypass the boundary. |
| Privacy | Private portfolio, thesis, and valuation data never leave the local system without a disclosed, explicit provider action and audit record. |
| Financial correctness | Deterministic calculations are tested, inputs are source labeled, currency consistent, reviewed, and supported by certified real-source histories. |
| Workflow | The user can complete the five core jobs without detours through Settings or Admin and without manually searching source files. |
| UX | The interface is visually coherent, responsive, keyboard accessible, dense, calm, and honest about every loading, empty, stale, partial, failed, and unconfigured state. |
| Reliability | A clean clone can build, migrate, test, start, back up, restore, and recover without undocumented manual code edits. |
| Performance | Core pages, search, tables, and review workflows meet measured budgets on a representative dataset. |
| AI discipline | AI never silently becomes mock output, never invents sources, never mutates thesis or valuation state without review, and passes a defined evaluation suite. |
| Data coverage | Supported US and India workflows are backed by declared, tested source profiles; unsupported layouts or providers are blocked or labeled rather than guessed. |
| Portfolio depth | Performance, currency, corporate actions, exposures, attribution, and decision links are reproducible and point-in-time aware. |
| Operations | Failures are observable, retryable where appropriate, auditable, and recoverable through tested backup and restore procedures. |

## 4. The Shipping Contract

A feature is **Shipped** only when all seven gates pass:

1. **Implementation:** real backend behavior exists and no required surface is a
   mock or stub.
2. **Data:** provenance, freshness, point-in-time behavior, missing data, and
   conflict behavior are defined.
3. **Security:** authentication, ownership, validation, privacy, and untrusted
   input handling pass.
4. **UX:** the complete user workflow includes loading, empty, partial, stale,
   failed, success, and recovery behavior.
5. **Verification:** unit, integration, contract, and browser tests cover the
   material success and failure paths.
6. **Operations:** logs, request/run IDs, recovery, and representative
   performance are understood.
7. **Documentation:** current-state, capability status, limitations, and the
   relevant acceptance gate are updated.

A database table, route, page, passing TypeScript build, or isolated formula
does not by itself make a feature shipped.

Completion percentages must move only when a quality-adjusted capability gate
changes from partial to verified.

## 5. Non-Negotiable Product and Engineering Decisions

### 5.1 Source and calculation discipline

- Backend services perform financial calculations.
- AI explains, challenges, classifies, or drafts. It does not freehand core
  finance math.
- Growth assumptions must carry reinvestment implications.
- Industry benchmarks are priors, not company facts.
- Every material assumption has a source category and review status.
- No missing portfolio price or financial metric is silently treated as zero.
- No provider failure is silently converted into success.

### 5.2 Human control

- Extracted financial facts remain candidates until reviewed or overridden.
- AI suggestions remain suggestions until reviewed.
- Thesis and valuation state changes require explicit user action.
- Material overrides require an actor, time, prior value, new value, and reason.

### 5.3 Architecture

- Do not rewrite the application.
- Split monoliths one domain at a time behind compatibility imports.
- PostgreSQL remains the primary data platform.
- Use PostgreSQL full-text search before introducing a vector database.
- Measure synchronous duration before introducing a job queue.
- Add background infrastructure only for demonstrated long-running work.
- Preserve the current Next.js, FastAPI, PostgreSQL, SQLAlchemy, and Alembic
  architecture unless a measured problem justifies change.

### 5.4 Frontend

- Use one styling system.
- The recommended path is to install and formalize the utility compiler the
  existing code already assumes, then map it to a documented token system.
- Do not maintain unprocessed utility classes, a parallel custom-class system,
  and widespread inline styles at the same time.
- Use charts only when trend, distribution, or comparison is materially faster
  to understand than a table.
- Prefer opaque surfaces, restrained shadows, compact headings, dense tables,
  stable tabs, and consistent status colors.

### 5.5 Provider and legal discipline

- Do not build a provider integration until source, license, cost, rate limits,
  temporal behavior, and retention rights are approved.
- Do not scrape prohibited HTML.
- Do not backfill historical estimates or market data in a way that creates
  hindsight.
- Provider metadata is not evidence that a provider is working.

## 6. Reconciled Baseline

### 6.1 Strong and worth preserving

- deterministic FCFF DCF, WACC, scenarios, sensitivity, reverse DCF, FCFE/DDM,
  relative valuation, macro sensitivity, real options, and diagnostics
- durable reviewed valuation setup drafts with provenance and concurrency
- raw-document and original-PDF custody
- review-gated text, PDF, Screener, and XBRL financial candidates
- normalized financial coverage and reconciliation foundations
- SEC and RSS ingestion with processing-run records
- rule-based event scoring and alert generation
- portfolio lifecycle with honest missing-price behavior
- US/India market-aware identity and capability states
- explicit stale, partial, mock, empty, error, and not-configured concepts
- meaningful backend and selected browser test coverage

### 6.2 Current critical defects

- Auth-by-default was missing. This was closed in the first R1 checkpoint with
  a two-route public health allowlist and an automated route inventory.
- Research-session creation and message ownership were defective. This was
  closed in the first R1 checkpoint with owned-parent resolution and
  cross-user tests.
- CSV exports and transfer ownership were broken. This was closed for tested
  manual interchange in the first R1 checkpoint; backup status remains blocked
  on a restore drill.
- AI provider, mock, privacy, source, ownership, and failure behavior are
  inconsistent.
- raw exception strings leak through multiple paths.
- the frontend has a large unprocessed utility-class surface, missing tokens,
  extensive inline styles, and almost no responsive infrastructure.
- global search is a false affordance.
- route-level loading, error, and not-found boundaries are absent.
- the worktree is not a reproducible release unit.
- representative real-source US and India financial histories are not
  certified.
- exact event-to-source passage location is missing.
- point-in-time and revision-aware facts are largely absent.
- portfolio attribution, multi-currency accounting, corporate actions, and
  reusable reporting are incomplete.

### 6.3 Documentation contradictions that this roadmap resolves

| Older claim | Current truth |
|---|---|
| Broad frontend polish phase is complete | Build success does not prove styling, responsiveness, accessibility, or route-state behavior. |
| Research workspace is complete | Persistence exists, but creation and message ownership have production defects and source-grounding is incomplete. |
| CSV transfer works | Current exports can return HTTP 500 and are not a safe backup path. |
| Local authentication secures the app | The frontend boundary can be bypassed through many direct FastAPI routes. |
| Source-backed AI exists | Several AI paths lack a unified provider, source, mock, privacy, ownership, and failure contract. |
| Normalized financial mechanics prove readiness | Synthetic fixtures prove mechanics; representative reviewed US and India histories are still required. |

## 7. Critical-Path Release Sequence

Do not skip a release gate because later work looks more differentiated.

The first four releases are a direct expansion of the primary assessment:

| Primary assessment | This roadmap | Rule |
|---|---|---|
| Phase A: Correctness and security closure | R0-R1 | Mandatory before product expansion |
| Phase B: Frontend integrity and workflow coherence | R2 | Mandatory before calling the current UI reliable |
| Phase C: Reliability and delivery discipline | R3 | Mandatory before treating the repository as a release |
| Phase D: Product differentiation | R4-R6 | Starts only after the relevant A-C gates pass |
| Phase E: Portfolio depth | R7 | Starts after point-in-time and workflow foundations |
| Provider-dependent work | R8 | Starts only after a provider decision record |

R0-R3 are not optional “cleanup.” They are the current product roadmap.
R4-R9 describe what follows after the audited product becomes secure,
coherent, and reproducible.

| Release | Objective | Depends on | World-class value |
|---|---|---|---|
| R0 | Contain scope and preserve a safe baseline | None | Prevents further drift and loss |
| R1 | Close security, ownership, transfer, error, and AI-control defects | R0 | Makes current behavior trustworthy |
| R2 | Restore one frontend system and coherent information architecture | R1 | Makes the current product genuinely usable |
| R3 | Establish reproducible delivery, CI, observability, backup, and restore | R1, R2 | Makes progress durable |
| R4 | Complete exact evidence, real-source certification, and point-in-time truth | R1, R3 | Establishes the core trust moat |
| R5 | Integrate the five daily workflows | R2, R4 | Converts modules into a product |
| R6 | Add search, change detection, contradiction, evidence graphs, and work products | R4, R5 | Creates differentiated research value |
| R7 | Complete portfolio accounting, exposure, attribution, and reports | R4, R5 | Connects research to owned risk |
| R8 | Add provider-backed data and controlled automation | R3, R4 | Expands coverage without weakening trust |
| R9 | Pass world-class certification and a sustained daily-use trial | R1-R8 | Establishes the release as a daily driver |

## 8. R0: Scope Containment and Baseline Preservation

### Outcome

The existing application is preserved as a reviewable starting point, broken
promises are not presented as reliable functionality, and no new module is
started.

### Work

#### R0.1 Freeze feature breadth

- Pause new top-level pages, models, valuation methods, providers, and AI
  workflows.
- Allow only correctness, security, UX infrastructure, test, and release work
  until R1-R3 pass.

#### R0.2 Capture a release manifest

Record:

- current commit identifier
- Alembic head and complete migration graph
- Python, Node, framework, database, and package-lock versions
- backend route inventory
- frontend route inventory
- database model inventory
- current test results
- current Docker images and service health
- current known mocks and hidden limitations

#### R0.3 Protect local data

- Back up PostgreSQL and stored document/PDF assets before structural work.
- Verify the backup is readable.
- Do not use destructive migration or worktree reset commands.

#### R0.4 Classify the dirty worktree

Classify every dirty entry into:

- intended source change
- intended migration
- intended test
- intended documentation
- generated artifact
- local environment or secret
- obsolete diagnostic
- unclear and requires review

Do not bulk commit, delete, reset, or regenerate until the classification is
complete.

#### R0.5 Remove false affordances

Until repaired:

- hide or disable CSV export and import controls
- replace global search with a navigation-only command palette or remove it
- hide private research chat behind a clear unavailable state
- keep Market Regime explicitly marked as simulated and outside decision use
- remove “source-backed” claims from AI surfaces that cannot prove source scope

#### R0.6 Freeze the capability register

- Copy the current `WC-*` status matrix into the release manifest.
- Record which test or repeatable workflow supports each shipped status.
- Downgrade any capability whose proof is only a page, model, or stale document.

### Exit gate

- local data is backed up
- worktree entries are classified
- the baseline can be reproduced from recorded versions
- broken controls cannot be mistaken for working controls
- no new feature module has started

## 9. R1: Trust Boundary and Correctness Closure

### Outcome

Every current workflow has a defensible identity, ownership, transfer, error,
AI, and privacy boundary.

### R1.1 Build an automated route-security inventory

For every FastAPI operation, record:

- HTTP method
- canonical path
- router/domain
- public or authenticated
- ownership model
- parent ownership resolver
- mutation or read
- response type
- test coverage

The inventory must fail CI when a new route is not explicitly classified.

### R1.2 Require authentication by default

- Apply current-user authentication at the root application router.
- Maintain a small, reviewed public allowlist.
- Limit the allowlist to health, readiness, and any genuinely public reference
  data.
- Preserve the signed Next.js identity assertion flow.
- Preserve stripping of caller-supplied internal identity headers.
- Verify that direct calls to port 8000 cannot bypass identity.
- Verify that every unauthenticated mutation returns `401`.

### R1.3 Standardize ownership resolution

- Introduce reusable owned-parent resolver or repository helpers.
- Never resolve a user-owned child by numeric child ID alone.
- Return `404` for cross-user resource discovery where appropriate.
- Cover portfolio, thesis, valuation, alerts, research, decisions, evidence,
  daily briefs, AI output, and transfers.
- Add a negative cross-user test matrix.

### R1.4 Repair research sessions

- Set `ResearchSession.user_id` from the authenticated user.
- Resolve messages through a current-user-owned session.
- Add typed request and response models.
- Add cross-user create/read/write/delete tests.
- Remove shared-fixture behavior as evidence that production ownership works.
- Keep the UI unavailable until the ownership suite passes.

### R1.5 Rebuild data transfer as a real file workflow

- Return real streamed/file CSV responses, not a `Response` inside
  `ApiResponse.data`.
- Resolve source metadata through relationships.
- Scope every portfolio export to the current user.
- Resolve imported portfolio IDs through an owned parent.
- Enforce file-size, row-count, enum, currency, date, decimal, and reference
  limits.
- Provide preview and apply stages.
- Roll back the complete apply transaction if any blocking row fails.
- Escape cells beginning with `=`, `+`, `-`, or `@`.
- Add download, formula-injection, ownership, malformed-row, size-limit,
  duplicate, and rollback tests.
- Do not call CSV export a backup until a restore/import drill succeeds.

### R1.6 Introduce one public error contract

Every public failure should include:

- stable error code
- safe user message
- request ID
- retryability
- affected field when relevant
- provider or processing-run reference when relevant

Internal logs may include structured technical detail, but must exclude:

- secrets
- provider credentials
- private request bodies
- raw documents
- portfolio contents
- model prompts containing private data

Remove hardcoded log paths and raw `str(exception)` responses.

### R1.7 Introduce request and workflow IDs

- Generate a request ID at the HTTP boundary.
- Propagate it through services, provider calls, and structured logs.
- Link long operations to `ProcessingRun`.
- Show the run ID and safe failure state in Operations/Data Health.

### R1.8 Create one AI honesty and privacy contract

Every persisted AI output must include:

- provider
- model
- prompt version
- SHA-256 input hash
- explicit `is_mock`
- source IDs
- source scope
- generated time
- limitations
- confidence
- review status
- reviewer and review time where applicable
- privacy-disclosure version
- external data classes sent
- failure status and safe failure code

Behavioral rules:

- Provider failure returns failure. It never silently returns mock text.
- Mock output is allowed only in an explicit test or demo mode.
- The user sees what private data will leave the machine before the call.
- AI cannot update thesis or valuation state without a separate reviewed write.
- AI cannot invent a citation or cite a source outside the declared source set.
- Recommendation language is removed from prompts and UI labels.
- AI output remains untrusted display text.

### R1.9 Close current hidden defects

- Replace MD5 and process-randomized `hash()` usage with SHA-256 where
  determinism or integrity is required.
- Enforce ownership on valuation and research AI routes.
- Audit response envelopes for binary, no-content, and legacy paths.
- Verify imported text is escaped and never rendered through unsafe HTML.

### R1 acceptance gate

- 100% of non-public routes require identity
- 100% of user-owned child routes resolve an owned parent
- direct backend-port bypass tests fail with `401`
- research cross-user tests pass
- CSV export downloads valid files and import preview/apply is transactional
- no raw exception strings reach public responses
- every AI output uses the unified contract
- provider failure never becomes mock success

### R1 progress checkpoint: first 30 execution steps

Completed on 2026-07-25:

1. Reconciled this roadmap, the ideation register, and the product/codebase
   assessment into one R1 queue.
2. Preserved the pre-existing dirty worktree and replacement migration chain.
3. Defined the explicit public application-route allowlist.
4. Limited the allowlist to `GET /api/health` and `GET /health`.
5. Added a typed route-security inventory record.
6. Added recursive FastAPI dependency inspection.
7. Added deterministic route inventory generation.
8. Applied `get_current_user` at the aggregate API router.
9. Added an inventory test that rejects unclassified or accidentally public
   application operations.
10. Added direct backend-port tests for unauthenticated reads.
11. Added direct backend-port tests for unauthenticated POST, PATCH, and DELETE
    operations.
12. Persisted the authenticated user on research-session creation.
13. Added a reusable current-user-owned research-session resolver.
14. Scoped research-session lists to the current user.
15. Scoped research-session detail reads to the current user.
16. Resolved research-message writes through the owned parent.
17. Added owner-only research-session deletion.
18. Restricted caller-created research messages to the `user` role.
19. Added title and message length validation.
20. Added create, list, read, write, role, cross-user, delete, and cascade tests
    for research sessions.
21. Replaced enveloped `Response` objects with real CSV responses.
22. Added attachment filenames and `no-store` response headers.
23. Scoped holding exports through user-owned portfolios.
24. Scoped transaction exports through user-owned portfolios.
25. Reconciled market-price export/import with the actual model fields.
26. Resolved raw-document source metadata through the `Source` relationship.
27. Reconciled event export with the actual event model.
28. Applied formula-injection escaping to exported text fields.
29. Added UTF-8, file-size, row-count, required-column, decimal, date,
    currency, transaction-type, company-reference, duplicate, and portfolio
    ownership validation.
30. Added preview/apply behavior, atomic transaction application, rollback
    coverage, relationship-field coverage, owner-scope coverage, and focused
    transfer tests.

Verification:

- focused R1 tests: 13 passed
- complete backend suite: 320 passed
- frontend tests: 63 passed
- frontend typecheck and production build: passed
- Alembic current revision equals the single head `a7a7a7a7a7a7`
- live `GET /api/health`: 200
- live unauthenticated `GET /companies`: 401
- live unauthenticated `GET /export/portfolio-holdings`: 401

This checkpoint closes the audited route-auth default, research ownership, and
broken transfer defects. It does not complete R1. The remaining critical work
is the full owned-parent negative matrix, one public error/request-ID contract,
structured logging, deterministic hash cleanup, and the unified AI
provider/mock/privacy/source/review contract. CSV transfer is now a tested
manual interchange path, but it is not a backup until a restore drill passes.
CSV parsing, validation, duplicate detection, and ownership rules live in
`backend/app/services/data_transfer.py`; the router is limited to HTTP response,
query, preview/apply, and transaction orchestration.

### R1 progress checkpoint: next five major controls

Completed on 2026-07-26:

1. **Completed the owned-domain negative matrix and fixed found defects.**
   Alert creation now assigns the authenticated owner explicitly. Daily-brief
   generation filters alerts and thesis notes by owner, persisted briefs carry
   `user_id`, and cross-user inputs do not affect another user's brief. Existing
   and expanded negative suites cover portfolio trees, valuation models/drafts
   and children, thesis children, research, evidence, decisions, transfer, and
   AI outputs.
2. **Introduced one public error and request-ID contract.** Failed requests now
   use stable codes, safe messages, request IDs, retryability, fields, provider,
   and processing-run references where relevant. `X-Request-ID` is validated or
   generated at the HTTP boundary. The legacy `detail` field remains only as a
   compatibility bridge.
3. **Introduced structured safe logging.** Backend logs are JSON on stdout with
   request context and explicit safe fields. The fixed error-log file, provider
   response-body logging, exception interpolation, and raw public exception
   strings were removed.
4. **Replaced weak provenance hashes.** MD5 and Python's process-randomized
   `hash()` were replaced by canonical SHA-256 helpers with exact digest tests.
5. **Implemented the unified AI honesty/privacy contract.** Migration
   `b8b8b8b8b8b8` adds owned provider/model/mock/source/privacy/transmission/
   review/failure metadata. Provider failure never falls back to mock; mock is
   test/demo only; active UIs show transmitted data classes and require a
   versioned acknowledgement; valuation AI routes and outputs are owned;
   recommendation prompts were removed. Automatic ingestion no longer performs
   undisclosed narrative AI, and thesis-impact AI produces reviewable proposals
   instead of direct writes.

Verification:

- complete backend suite: 334 passed
- frontend tests: 63 passed
- frontend TypeScript: passed after regenerating a concurrently corrupted
  `.next` cache
- frontend production build: passed
- Alembic single head and current database: `b8b8b8b8b8b8`
- live `GET /api/health`: 200 with `X-Request-ID`
- static scans: no MD5/process `hash()` provenance, raw `detail=str(...)`, fixed
  error-log path, direct AI-provider bypass, or silent mock-fallback text

R1 is substantially closed but not declared fully complete. Remaining edges are
request-to-`ProcessingRun` correlation for every long operation, binary/
no-content/legacy envelope review, citation verification, an AI evaluation
corpus, and a complete approve/reject UI for stored AI output. The audit score
remains 58% local-first and 47% world-class because frontend integrity,
recovery/CI, exact evidence, real-source certification, and integrated daily
workflows still dominate the remaining product gap.

### R1-R3 progress checkpoint: product-integrity five-step batch

Completed and verified on 2026-07-26:

1. **Request/run observability:** migration `c9c9c9c9c9c9` adds indexed
   `processing_runs.request_id`. Run creation inherits the active request ID,
   lifecycle logs include the run ID and safe counters, and ingestion status
   exposes the correlation field.
2. **Response-contract closure:** `app/api/response_contracts.py` classifies
   every route as envelope, binary, no-content, or legacy JSON. Explicit
   binary endpoints remain file responses; the automated inventory reports
   zero legacy JSON routes. The conflicting company-industry route was also
   corrected and valuation assumption selection now resolves an owned model.
3. **Frontend compiler and token contract:** Tailwind 4 is wired through
   PostCSS, global utilities compile in production, Google font loading was
   removed, and project-owned typography, spacing, color, border, and radius
   tokens now have compatibility aliases. The assumption-method selector uses
   authenticated API helpers and the coherent light application surface.
4. **Information architecture:** primary navigation is grouped into Today,
   Portfolio, Research, Data, and System; it has a working mobile drawer.
   Company routes share stable workspace tabs and the app has root loading,
   error, and not-found boundaries. Automatic prefetch is disabled on dense
   navigation so an idle page does not render every destination.
5. **Recovery and delivery controls:** research provider failures render
   inline while preserving the saved user message; CSV preview keeps the file,
   shows row errors, and blocks apply. A clean release script and GitHub Actions
   workflow now build, migrate, and run the complete backend/frontend gates.

The browser pass exposed a normal sign-in/server-render burst exceeding the
old 15-connection SQLAlchemy ceiling. Database pool capacity is now explicit
and bounded by `DATABASE_POOL_SIZE`, `DATABASE_MAX_OVERFLOW`, and
`DATABASE_POOL_TIMEOUT_SECONDS` (defaults 10/20/10), while dense-link prefetch
remains disabled.

Verification:

- fresh Alembic migration: `c9c9c9c9c9c9 (head)`
- complete backend suite: 336 passed, 4 third-party openpyxl warnings
- frontend tests: 65 passed
- frontend TypeScript and production build: passed
- product-integrity Playwright suite: 3 passed
- clean isolated release baseline: passed

The 58% local-first and 47% world-class scores remain the dated audit baseline.
This batch materially closes control and frontend-foundation defects, but it
does not complete restore drills, exact evidence locators, representative
real-source certification, accessibility, performance budgets, or the five
integrated daily jobs.

## 10. R2: Frontend Integrity, UX System, and Information Architecture

### Outcome

The product becomes a coherent research instrument rather than a collection of
partially styled pages.

### R2.1 Adopt one styling pipeline

Recommended decision:

- formalize a utility compiler compatible with the utility tokens already
  present in the codebase
- map it to project-owned design tokens
- retain a small global stylesheet for resets and primitives
- migrate inline styles incrementally

Do not manually remove more than a thousand utility-token references before
testing the lower-cost path.

Run a bounded styling proof on:

- dashboard
- company workspace
- valuation workspace
- evidence drawer
- one large table

The proof must confirm production rendering, not only development rendering.

### R2.2 Define the design token contract

At minimum:

- typography scale
- font weight scale
- spacing scale
- surface colors
- text colors
- border colors
- semantic success, warning, error, stale, partial, mock, and unavailable colors
- radius scale
- shadow scale
- density modes
- responsive breakpoints
- focus ring
- chart palette
- reduced-motion behavior

Resolve all currently referenced but undefined CSS variables.

### R2.3 Build a minimal component system

Create or standardize:

- page header
- compact metric
- data-state notice
- badge
- tabs
- table
- form field
- inline validation
- button
- drawer
- modal
- tooltip
- command palette
- evidence citation
- freshness indicator
- skeleton
- empty state

Do not create decorative variants without a repeated product need.

### R2.4 Rebuild the primary information architecture

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

Desktop uses a grouped collapsible sidebar. Narrow screens use a drawer.

### R2.5 Make company identity the stable workspace

Use:

```text
Overview | Filings | Financials | Thesis | Evidence | Decisions | Valuation
```

Keep a compact company header visible across tabs with:

- company identity
- market and currency
- price plus source/freshness when available
- setup status
- active alert count
- latest filing
- latest valuation status

Replace disconnected action-button clusters with stable tabs and contextual
actions.

### R2.6 Rebuild the Today dashboard

The first viewport should prioritize:

1. unreviewed alerts ranked by thesis and portfolio relevance
2. changed or invalidated thesis assumptions
3. stale, blocked, or materially changed valuations
4. failed, stale, or partial ingestion
5. upcoming or overdue review tasks

Generic counts, tracked-company totals, and portfolio value are secondary.

### R2.7 Make search honest

Before corpus search exists:

- use a command palette for navigation, recent companies, and recent workflows
- support the `/` shortcut only if it actually opens the command palette
- remove language implying source or corpus search

After R6 search exists, extend the same interface to typed corpus results.

### R2.8 Add route and component resilience

For all core routes:

- `loading.tsx`
- `error.tsx`
- `not-found.tsx`

For all independent panels:

- loading
- empty
- stale
- partial
- not configured
- failed with retry
- permission denied
- conflict

One failed panel should not collapse the entire page.

### R2.9 Fix form behavior

- replace browser `alert()` calls with inline feedback
- preserve user input after failed writes
- show field-level errors
- distinguish validation, conflict, provider, and network failures
- disable duplicate submission
- show durable success confirmation
- require an explicit reason for material overrides
- use optimistic updates only where rollback behavior is safe

### R2.10 Make tables professional

- server-side pagination, filtering, and sorting for large collections
- sticky headers where useful
- consistent number, date, percentage, and currency formatting
- keyboard navigation
- compact density
- responsive column priority
- explicit unavailable values
- export only when the exported workflow is tested

### R2.11 Accessibility baseline

- keyboard access to sidebar, tabs, drawers, command palette, and tables
- focus trapping and return focus for modal/drawer workflows
- semantic landmarks and headings
- text alternatives and accessible names
- status cues that do not rely only on color
- contrast at WCAG AA
- reduced-motion support
- automated accessibility checks on critical workflows

### R2.12 Responsive and visual verification

Maintain representative screenshots for at least:

- wide desktop
- compact desktop/tablet
- narrow mobile

Cover:

- dashboard
- company workspace
- financial review
- valuation
- portfolio
- alert evidence
- operations/data health

Tests must detect missing styling infrastructure, undefined tokens, clipped
tables, inaccessible drawers, and isolated dark fragments.

### R2.13 Decompose frontend boundary files

Incrementally split:

```text
lib/api.ts -> lib/api/{domain}.ts
app/actions.ts -> app/actions/{domain}.ts
large pages -> route-local view components
large valuation components -> focused panels
```

Add stable compatibility exports during migration. Do not combine this with a
route rename or visual redesign in the same change.

### R2 acceptance gate

- one styling system works in production
- zero undefined design tokens
- zero unprocessed utility dependencies
- core pages pass desktop, tablet, and mobile screenshot checks
- core routes have loading, error, and not-found boundaries
- top-level navigation matches the five-group model
- company research uses the stable workspace tabs
- fake corpus search is gone
- core workflows are keyboard usable

## 11. R3: Reproducible Delivery, Reliability, and Recovery

### Outcome

A clean clone is a real release unit, failures are observable, and local data
can be recovered.

### R3.1 Establish a clean repository baseline

- organize intended dirty changes into reviewable commits
- preserve the intended migration chain
- remove generated artifacts from source control
- keep local environment files ignored
- archive or remove obsolete root diagnostics only after classification
- verify no secrets entered history; rotate any secret that did
- prove a clean clone reproduces the same build and migration state

### R3.2 Add continuous integration

Minimum gates:

```text
backend unit tests
backend API/auth tests
PostgreSQL migration smoke
PostgreSQL integration tests
frontend unit/contract tests
frontend lint
TypeScript typecheck
production frontend build
auth route inventory
secret scan
dependency audit
selected browser workflows
```

Add coverage reporting for visibility. Do not impose an arbitrary high global
threshold before measuring the baseline.

### R3.3 Separate test layers

Use:

```text
unit
api-auth
api-domain
postgres-integration
provider-contract
browser-critical
browser-failure
visual
accessibility
performance
```

The auth layer must not auto-inject identity or missing `user_id` values.

### R3.4 Expand browser coverage

Preserve the isolated disposable stack. Add:

- alert evidence complete and missing states
- company setup
- SEC not configured and provider failure
- research ownership
- transfer preview, download, apply, and rollback
- stale valuation write conflict
- review invalidation after source refresh
- responsive shell navigation
- partial dashboard data
- failed ingestion recovery

### R3.5 Add structured observability

- structured logs
- request IDs
- processing-run IDs
- provider timing
- database timing for measured slow queries
- safe error categories
- route and workflow latency
- no portfolio, thesis, document body, key, or credential logging

### R3.6 Define performance budgets

Measure on a representative dataset before finalizing exact budgets. Track:

- Today dashboard render
- company overview render
- financial review table
- valuation workspace
- portfolio overview
- search response
- large-table filtering
- ingestion request acceptance
- long-run completion

Add aggregate endpoints before adding cache infrastructure.

### R3.7 Add backup and restore

Back up:

- PostgreSQL
- original PDFs and document assets
- relevant local configuration templates, excluding secrets
- provider and migration metadata needed for restoration

Verify:

- encrypted-at-rest option
- documented retention
- restore into a clean environment
- database-to-document consistency
- hash verification
- restoration of user ownership

Run a restore drill and record duration and failures.

### R3.8 Establish release discipline

Every release candidate must include:

- migration review
- clean-clone proof
- test and browser evidence
- known limitations
- data backup
- restore compatibility
- capability-register changes
- rollback instructions

### R3 acceptance gate

- main branch CI is green
- a clean clone builds, migrates, tests, and starts
- critical browser workflows pass against isolated PostgreSQL
- a backup restores into a clean environment
- request and processing-run IDs connect UI failures to safe logs
- core route performance is measured against representative data

## 12. R4: Exact Evidence, Real-Source Certification, and Point-in-Time Truth

### Outcome

The product can prove material claims and reproduce historical research state.

### R4.1 Add a first-class evidence-reference model

Support multiple evidence references per event or claim. Each reference should
preserve:

- owning event or claim
- raw document
- source
- locator type
- typed locator payload
- bounded supporting text
- quote/content hash
- extraction method
- confidence
- created time
- observed time
- explicit no-locator reason when applicable

Do not overload one unstructured evidence string.

### R4.2 Propagate locators through the intelligence pipeline

Carry typed locators from:

- filing text
- PDF table cells
- spreadsheet cells
- XBRL facts
- document sections

into:

- events
- alerts
- thesis impacts
- valuation impacts
- decision evidence

Preserve document-level fallback when exact location is genuinely unavailable.

### R4.3 Build safe source highlighting

For plain text:

- render escaped text segments
- highlight only stored offsets or parser-owned tokens
- never render imported HTML as trusted content

For PDF:

- use stored page and coordinate systems
- display an overlay on the rendered page
- show page-only fallback when coordinates are unavailable or invalid
- allow the user to inspect the original source

### R4.4 Add evidence-integrity checks

Detect:

- missing source records
- missing document assets
- content-hash mismatch
- dead external source links
- locators outside current content
- missing timestamps
- cross-user reference leakage
- claim/source mismatch
- references to superseded facts

Expose results in Data Health.

### R4.5 Create a real-source certification corpus

Create a reviewed corpus for the exact supported profiles. At minimum:

- US SEC structured/XBRL history
- US text-based annual filing
- India text-based annual report/PDF history
- multiple fiscal periods
- common unit, currency, share-count, and equity-bridge cases

World-class certification should expand beyond one happy-path file. Maintain a
declared coverage matrix by:

- market
- filing type
- statement type
- extraction method
- text versus scanned
- layout profile
- supported metrics
- unsupported conditions

### R4.6 Add statement reconciliation

**Foundation shipped 2026-08-02:** company-level annual checks now validate
profit after tax and parent/NCI attribution with declared tolerances. Missing
facts remain unavailable; duplicate facts and arithmetic mismatches fail closed,
block certification, and downgrade valuation trust. APSEZ passes 6/6; AAPL's
narrow approved fact set records an explicit limitation. Balance sheet,
cash-flow movement, and broad total/subtotal checks remain open.

For supported statements:

- validate totals and subtotals
- validate sign conventions
- validate fiscal-period identity
- validate currency and scale
- compare extracted, reviewed, normalized, and source values
- identify missing and duplicate facts
- prevent promotion when blocking reconciliation fails

Do not raise extraction confidence because a parser returned a value. Raise it
only after source-level reconciliation.

### R4.7 Expand PDF handling by declared profile

**Bounding-box foundation expanded 2026-08-07:** trusted financial-candidate row
and component geometry plus validated event regions render on bounded,
authenticated source-page PNGs. New event regions must match the stored page's
physical dimensions. Unknown coordinate systems, invalid bounds, and legacy
page-only locators retain explicit source-PDF/page fallbacks. Merged-cell
reconstruction, additional layout profiles, and OCR remain open.

Sequence:

1. existing text-based line tables
2. bounding-box evidence overlay (financial and event-region foundation shipped)
3. multiline and merged-cell reconstruction
4. statement-layout profiles
5. totals and cross-statement validation
6. OCR for scanned documents
7. OCR confidence and human-review rules

Unsupported layouts must fail safely and remain reviewable.

**Historical event-span backfill foundation shipped 2026-08-07:** Data Health
now previews priority-ordered events without references and can apply only
bounded claims that occur exactly once in stored source text. Alert-derived
claims are current-user scoped; apply rechecks duplicates under an event lock
and records a processing run. Unmatched, ambiguous, conflicting, fuzzy, and
whitespace-normalized cases remain unapplied. The first live preview found one
unreferenced event and zero eligible exact matches, so no live rows were changed.

**Manual exact-span resolution shipped 2026-08-07:** Data Health now routes
unmatched, ambiguous, conflicting, and missing-candidate rows with stored source
text into a dedicated event resolver. Authenticated search is exact and
case-sensitive, returns at most 25 bounded snippets, and never returns a full
filing body. Save revalidates source hash, linked document/company, offsets,
quote, occurrence index, and duplicate state under an event lock, then records
the authenticated creator and explicit manual-resolution provenance. Fuzzy,
normalized, OCR-only, and arbitrary range selection remain open.

### R4.8 Retire legacy financial fallback carefully

Remove fallback only when:

- representative US and India histories pass
- old snapshots are backfilled
- coverage is complete for the declared metric set
- reconciliation has no blocking mismatch
- currency source/confidence is preserved
- valuation drafts use only certified reads

### R4.9 Introduce point-in-time and revision-aware facts

Material fact records need to distinguish:

- economic effective time
- source publication time
- application observed time
- valid-from and valid-to time
- provider/source revision identity
- superseded fact
- correction reason

Do not treat `created_at` as a substitute.

Migrate one domain at a time:

1. financial facts
2. market prices and FX
3. valuation assumptions and priors
4. event/alert facts
5. thesis and decision snapshots
6. provider estimates, if ever added

### R4.10 Add reproducible review snapshots

A decision, thesis review, or valuation review must reference:

- exact fact versions
- source versions
- assumption versions
- model version
- formula version
- user overrides
- review time

Later revisions must not rewrite historical decisions.

### R4 acceptance gate

- every material alert has exact evidence or an explicit no-locator state
- text and PDF highlighting are safe and usable
- evidence-integrity checks run and surface failures
- declared US and India real-source profiles reconcile
- legacy fallback is removed only for certified coverage
- material facts preserve effective, published, observed, and revision state
- a prior valuation or decision can be reproduced as of its review time

## 13. R5: Integrated Daily Research Workflows

### Outcome

The existing modules operate as one product.

### R5.1 Today triage workflow

From the dashboard, the user can:

1. see unresolved alerts and broken data
2. open the exact evidence
3. inspect the affected thesis assumption
4. inspect the affected valuation input
5. inspect portfolio exposure
6. record a disposition or follow-up

### R5.2 Company onboarding workflow

One guided flow:

```text
identity
-> source readiness
-> filing acquisition
-> financial extraction
-> review and reconciliation
-> industry confirmation
-> valuation draft
-> reviewed model
```

Do not make users understand backend modules or source IDs to complete setup.

### R5.3 Financial-review workflow

The review UI must show together:

- source value and unit
- exact evidence
- parsed value
- normalized value
- warnings
- reconciliation status
- review or override
- downstream valuation dependencies

### R5.4 Thesis and contradiction workflow

The user can:

- define explicit thesis assumptions
- define falsification conditions
- link supporting and contradicting evidence
- review drift over time
- record a disposition
- see downstream valuation and portfolio implications

### R5.5 Valuation-review workflow

The user can:

- distinguish actuals, priors, calculations, user inputs, AI suggestions, and
  placeholders
- open evidence for material inputs
- see formula dependencies
- review staleness and currency consistency
- compare bear, base, and bull cases
- inspect reverse DCF
- record why an assumption changed
- promote only after all required reviews

### R5.6 Portfolio-review workflow

The user can:

- see which data is fresh, stale, missing, or manual
- understand performance and exposure
- connect positions to active theses and invalidating events
- inspect valuation freshness
- create a reviewed portfolio report

### R5.7 Add aggregate read endpoints

Create purpose-built reads for:

- Today dashboard
- company overview
- portfolio overview
- review queues
- data-health summary

Avoid broad collection fetches followed by application-side filtering.

### R5.8 Add user-visible audit history

Show actor, time, old value, new value, reason, and source for:

- financial review and override
- thesis assumptions
- valuation assumptions
- evidence disposition
- decisions
- portfolio corrections
- provider/manual replacements

### R5.9 Calibrate alert usefulness

Record:

- useful
- not useful
- false positive
- needs follow-up
- user note

Measure false positives and review latency by event type and source. Do not tune
scores invisibly.

### R5 acceptance gate

- the five core jobs pass browser tests
- alert to evidence to thesis to valuation to portfolio is one navigable chain
- the dashboard prioritizes unresolved work, not generic counts
- company onboarding is a guided flow
- all material edits are auditable
- no core workflow requires Settings or Admin detours

## 14. R6: Differentiated Research Intelligence

### Outcome

The product becomes meaningfully better than a dashboard plus a DCF tool.

### R6.1 Build PostgreSQL full-text corpus search

Index:

- document sections
- filings
- events
- alerts
- thesis notes
- evidence
- decisions
- valuation notes

Return:

- typed result
- company
- source
- publication and observation time
- snippet
- exact locator
- relevance explanation
- filters

Search returns source material. It does not invent an answer.

### R6.2 Add period-over-period language change

Compare equivalent:

- filing sections
- risk factors
- management discussion sections
- selected document sections
- transcript speakers later, only if a licensed source exists

Every change links to both source periods and distinguishes:

- added
- removed
- materially reworded
- moved
- unavailable comparison

### R6.3 Build the contradiction and falsification inbox

- map new evidence to explicit thesis assumptions
- distinguish support, contradiction, ambiguity, and irrelevant evidence
- show deterministic reasons and AI classification separately
- require user disposition
- record false positives
- never auto-rewrite the thesis

### R6.4 Build the valuation evidence graph

Represent:

```text
source fact
-> normalized fact
-> calculation
-> assumption
-> scenario
-> valuation output
```

The graph must expose:

- provenance
- formula
- override
- review
- staleness
- invalidating event
- downstream impact

Use a graph visualization only where the dependency structure adds real value.

### R6.5 Produce durable research work products

Generate reviewed:

- company research memo
- earnings or filing review
- thesis change memo
- valuation review
- watchlist review
- portfolio review

Every export includes:

- as-of time
- source index
- exact links
- fact/assumption/AI labels
- reviewed/unreviewed state
- limitations
- model and formula versions

### R6.6 Add saved monitors

Allow the user to save:

- company filters
- source filters
- metric changes
- claim changes
- thesis assumptions
- filing sections
- data-health conditions

Each run records:

- run time
- source scope
- changes found
- failures
- next run
- user disposition

### R6.7 Add background run control only when justified

For measured long operations, support:

```text
queued -> running -> completed
                  -> partial
                  -> failed
                  -> cancelled
```

Require:

- idempotency
- ownership
- safe retry policy
- visible status
- cancellation semantics
- processing-run linkage

Do not add a queue merely because the codebase is large.

### R6.8 Rebuild source-backed AI research

Only after search, evidence, ownership, and AI contracts pass:

- restrict retrieval to declared sources
- expose source scope before generation
- require citations for material claims
- verify citations point to supporting text
- separate fact, interpretation, uncertainty, and missing evidence
- expose prompt/model/version
- require human review before durable use

### R6.9 Add an AI evaluation suite

Measure:

- citation precision
- citation coverage
- unsupported-claim rate
- source-scope violations
- fact versus interpretation labeling
- confidence calibration
- privacy-contract compliance
- prompt-injection resistance from imported documents
- refusal to produce recommendations
- deterministic fallback behavior

### R6 acceptance gate

- corpus search returns typed exact-linked results
- period changes link to both sources
- contradiction items require a durable disposition
- material valuation assumptions have navigable evidence dependencies
- reviewed work products are reproducible
- saved monitors are auditable
- AI passes the evaluation set and has zero silent mock fallback

## 15. R7: World-Class Portfolio Intelligence

### Outcome

Portfolio output explains owned risk, performance, and decision quality without
pretending to give trading advice.

### R7.1 Establish the accounting ledger

- define authoritative transaction, cash, holding, and snapshot semantics
- preserve corrections rather than rewriting history invisibly
- validate quantities, prices, fees, currencies, and dates
- reconcile holdings to transactions and cash

### R7.2 Add multi-currency accounting

Store:

- native security currency
- transaction currency
- portfolio base currency
- reporting currency
- source-backed FX rate
- FX as-of time
- conversion formula
- stale or missing status

Do not fabricate FX rates or reuse valuation currency as portfolio FX.

### R7.3 Add a corporate-action ledger

Support reviewed, idempotent:

- splits
- dividends
- mergers
- spin-offs
- symbol changes
- delistings
- cash distributions

Preserve source evidence, reversal, and cost-basis effects.

### R7.4 Add performance measurement

At minimum:

- time-weighted return
- cash-flow-aware money-weighted return where appropriate
- benchmark return
- security contribution
- sector/country/currency contribution
- fees
- realized and unrealized components
- unavailable-state handling

### R7.5 Add exposure and concentration

Cover:

- security
- sector
- industry
- country
- currency
- factor
- thesis driver
- narrative
- event
- liquidity where sourced

Every derived exposure must state source, formula, and coverage.

### R7.6 Add marginal and scenario impact

Show how an incremental or hypothetical position changes:

- concentration
- thesis overlap
- country/currency exposure
- scenario loss
- valuation dispersion
- liquidity constraints

This is analysis, not a recommendation.

### R7.7 Connect decisions to outcomes

Link:

- decision
- evidence available at the time
- thesis state
- valuation state
- portfolio exposure
- subsequent outcome

Avoid hindsight by using the point-in-time fact model.

### R7.8 Build reusable portfolio reports

Produce source-aware:

- performance report
- exposure report
- risk review
- thesis/valuation freshness report
- decision-attribution report

### R7 acceptance gate

- ledger reconciles
- active currencies use source-backed point-in-time FX
- corporate actions are idempotent and reversible
- benchmark-aware performance and contribution are tested
- exposure states disclose coverage
- historical decisions use facts available at the time
- portfolio reports reproduce from a clean restore

## 16. R8: Provider-Backed Data and Controlled Automation

### Outcome

Coverage expands without compromising licensing, point-in-time truth, or source
honesty.

### R8.1 Require a provider decision record

Before implementation, approve:

- source and legal right to use it
- supported markets and entities
- field coverage
- historical depth
- point-in-time and revision behavior
- rate limits
- uptime expectations
- cost
- caching and retention rights
- redistribution restrictions
- identifier mapping
- data-quality tests
- failure and fallback behavior

### R8.2 Recommended provider priority

1. official or licensed India filings and company identity
2. source-backed FX history
3. delayed/end-of-day US and India prices
4. structured US and India fundamentals
5. country rates and macro series
6. licensed earnings transcripts
7. point-in-time consensus and estimate revisions
8. optional approved news sources

This order can change only if an actual product workflow requires it.

### R8.3 Maintain separate data tracks

Keep distinct:

- market prices
- financial statements
- provider fundamentals
- valuation assumptions
- valuation outputs
- macro data
- estimates

Never use valuation data as a substitute for missing market or financial facts.

### R8.4 Provider ingestion contract

Every provider path must:

- preserve raw custody where permitted
- preserve source and provider identifiers
- record publication, observation, and revision time
- deduplicate deterministically
- expose freshness and coverage
- create processing runs
- handle partial success
- apply finite timeout and retry rules
- avoid silent fallback
- pass provider-contract tests without live calls

### R8.5 Scheduling and notifications

- in-app reviewed queues come first
- external notification delivery requires saved monitors and background-run
  control
- record delivery time, source scope, content hash, status, retry, and user
  disposition
- throttle repeated failures and duplicate events

### R8.6 Market Regime production gate

Do not productionize Market Regime until approved structured inputs support:

- deterministic formula
- coverage
- timestamp
- confidence
- drivers
- blockers
- missing-data behavior
- historical evaluation

If those conditions are not met, keep it hidden or explicitly simulated.

### R8.7 Specialized valuation scope

Do not add more valuation methods merely to increase feature count. Add
specialized models only after a real supported-company need and a separate
acceptance suite:

- banks and insurers
- young loss-making companies
- distressed companies
- sum-of-the-parts

Until then, explicitly mark unsupported company/model combinations.

### R8 acceptance gate

- every production provider has an approved contract
- provider data is temporal, source labeled, and revision aware
- India and US support is represented accurately
- live/delayed prices remain separate from financials and valuation
- scheduled work is visible, owned, retryable, and auditable
- no unlicensed or prohibited source path exists

## 17. R9: World-Class Certification

### Outcome

The product is proven as a reliable daily research system, not merely declared
complete.

### R9.1 Security certification

- route inventory shows no accidental public operation
- cross-user tests cover every owned domain
- secret scan is clean
- untrusted input tests cover documents, CSV, PDFs, provider text, and AI text
- private-data-to-AI disclosures are complete
- no public deployment claim is made

### R9.2 Data certification

- real-source US and India profile corpus passes
- material facts preserve full temporal state
- evidence integrity has no unresolved critical failure
- supported financial statements reconcile
- unsupported layouts are blocked or labeled
- provider revision behavior is tested

### R9.3 Financial certification

- valuation formulas and diagnostics pass regression suites
- every material assumption is source and review labeled
- currency consistency is explicit
- point-in-time valuation reproduction passes
- special-case companies are blocked unless a supported model exists

### R9.4 UX certification

- five core jobs pass without workaround
- responsive screenshots pass
- accessibility checks pass
- keyboard-only completion passes
- no fake affordance remains
- all data states and recovery actions are consistent

### R9.5 Reliability certification

- clean clone succeeds
- CI is green
- backup and restore pass
- failure-state browser suite passes
- representative performance budgets pass
- long operations are observable and recoverable

### R9.6 AI certification

- provider, model, source scope, mock state, privacy, and review are visible
- citation evaluation passes the approved thresholds
- source-scope violations are zero in the gold set
- silent mock fallback is zero
- recommendation generation is refused or reframed

### R9.7 Sustained daily-use trial

Run the product as the primary research cockpit for a defined trial, ideally 30
consecutive calendar days.

Record:

- daily active workflow completion
- alert usefulness
- false positives
- failed or partial ingestion
- unresolved evidence gaps
- valuation review time
- search success
- broken source links
- user workarounds
- performance regressions
- restore confidence

No critical trust, ownership, data-loss, or silent-failure defect may remain at
the end of the trial.

## 18. Target UX Specification

### 18.1 Product hierarchy

Every major view should follow:

1. executive summary
2. key metrics
3. evidence and source state
4. deep detail

Do not place deep configuration or raw tables above the user’s current job.

### 18.2 Data-state vocabulary

Use one universal set:

| State | Meaning | Required UI |
|---|---|---|
| Healthy | Current, complete, and usable | Source and last-updated context |
| Stale | Older than domain threshold | Warning, last success, refresh action |
| Partial | Some sources or fields failed | Coverage and exact missing scope |
| Not configured | Required key/source missing | Setup action without fake content |
| Unavailable | Provider or calculation cannot produce a result | Reason and safe next step |
| Conflict | Sources or writes disagree | Side-by-side conflict and resolution action |
| Mock/Test | Explicit non-production output | Persistent visible label |
| Processing | Accepted but incomplete | Run status and cancellation where supported |
| Failed | Operation failed | Safe error code, retryability, request/run ID |
| Empty | Valid result with no records | Meaningful explanation and relevant action |

### 18.3 Visual direction

- dense, calm, professional
- compact 24 to 28 pixel page titles
- restrained typography hierarchy
- opaque surfaces
- minimal elevation
- stable column alignment
- tabular numerals
- consistent financial formatting
- no decorative gradients
- no hover movement on metric cards
- no chart where a compact table communicates better

### 18.4 Dashboard rule

The dashboard is a work queue, not a collection of counters.

### 18.5 Company-workspace rule

Company context remains stable while the user moves through filings,
financials, thesis, evidence, decisions, and valuation.

### 18.6 Evidence rule

Every material claim has an immediately visible path to:

- source
- time
- exact location or limitation
- claim type
- confidence
- related thesis
- related valuation input

### 18.7 Form rule

Forms preserve work, explain failure, and never make the user guess whether a
write succeeded.

### 18.8 Responsive rule

Responsive design is not “stack every column.” Define:

- essential fields
- collapsible secondary context
- mobile actions
- drawer behavior
- table column priority
- evidence reading behavior
- keyboard and touch targets

## 19. Target Code and Architecture Changes

### 19.1 Backend target

| Current pressure | Target | Migration rule |
|---|---|---|
| Root API not auth protected | Authenticated root router plus explicit public allowlist | Add route inventory first |
| 1,863-line schema module | Domain schema packages | Move one router group at a time |
| Large routers | Thin HTTP layer plus services and owned repositories | Preserve route contracts during extraction |
| Provider logic in multiple locations | Adapters under `providers/`, orchestration under `services/` | Move only after contract tests |
| Mixed transaction behavior | Explicit workflow state and transaction boundary | No half-complete success |
| Mixed route prefixes | One canonical namespace plus compatibility map | No mass rename |
| Raw public errors | Typed errors plus request IDs | Keep internal detail in structured logs |
| Broad collection reads | Filtered, paginated, aggregate endpoints | Measure query behavior |

### 19.2 Frontend target

| Current pressure | Target | Migration rule |
|---|---|---|
| 2,235-line API client | Domain API clients | Compatibility exports during migration |
| 942-line action module | Domain server actions | Keep auth behavior centralized |
| Large route/components | Route-local views and focused components | No simultaneous domain rewrite |
| Utility tokens without compiler | One processed utility/token system | Production screenshot proof |
| 913 inline styles | Tokens and component variants | Migrate by touched workflow |
| No route boundaries | Core route loading/error/not-found | Add before workflow redesign |
| Client types drift from API | Generated or validated OpenAPI contracts | Stabilize response shapes first |

### 19.3 Data target

- immutable or revision-aware material facts
- bitemporal timestamps where decisions depend on history
- explicit source and revision identity
- typed evidence locators
- source-backed FX
- auditable overrides
- declared provider capabilities
- coverage and reconciliation as first-class outputs

### 19.4 Long-operation target

Synchronous operations remain synchronous until measured duration or failure
behavior justifies background work. When promoted, the workflow must use the
explicit run-state contract and remain visible in the UI.

## 20. Capability Closure Map

| Capability | Current state | Closing release | Proof required |
|---|---|---|---|
| WC-001 Authentication and ownership | Partial | R1 | Auth inventory, default auth, cross-user suite |
| WC-002 Company setup and identity | Partial | R5/R8 | Guided workflow plus real provider coverage |
| WC-003 SEC and RSS ingestion | Partial | R3/R8 | Failure tests, scheduling only if justified |
| WC-004 Raw document and PDF custody | Shipped foundation | R3/R4 | Backup, restore, integrity checks, search |
| WC-005 Financial extraction | Partial | R4 | Supported-profile corpus and reconciliation |
| WC-006 Normalized financials | Partial | R4 | Real US/India certification and fallback retirement |
| WC-007 Damodaran valuation | Strong shipped foundation | R4/R5 | Certified actuals and evidence graph |
| WC-008 Country and currency context | Partial | R4/R7 | Temporal FX and currency separation |
| WC-009 Macro sensitivity | Shipped foundation | R8 | Provider freshness and reviewed exports |
| WC-010 Event extraction and scoring | Partial | R4/R5 | Exact evidence and feedback calibration |
| WC-011 Alert review queue | Partial | R5/R6 | Integrated triage, monitors, queue analytics |
| WC-012 Alert-to-evidence | Partial | R4 | Exact locator and highlight |
| WC-013 Thesis and contradiction | Partial | R5/R6 | Falsification inbox and reviewed timeline |
| WC-014 Narrative tracking | Partial | R6/R8 | Temporal language change and licensed coverage |
| WC-015 Decisions and variant perception | Partial | R5/R7 | Guided loop and point-in-time attribution |
| WC-016 Portfolio lifecycle | Shipped foundation | R7 | Ledger, FX, and corporate actions |
| WC-017 Portfolio analytics | Partial | R7 | Attribution, exposure, benchmark, reports |
| WC-018 Provider and data health | Shipped foundation | R3/R8 | SLAs, trends, run control, provider contracts |
| WC-019 Browser workflows | Partial | R3/R9 | Critical, failure, responsive, accessibility suites |
| WC-020 Market Regime | Mock/partial | R8 or remain hidden | Source-backed deterministic contract |
| WC-021 AI research | Partial | R1/R6 | Unified contract, citations, privacy, evaluation |
| WC-022 Corpus search | Proposed | R6 | PostgreSQL search with typed exact links |
| WC-023 Transcripts and estimates | Provider decision | R8 | Licensed point-in-time source |
| WC-024 Operational reliability | Partial | R3/R9 | CI, observability, performance, recovery |
| WC-025 Data transfer | Broken/partial | R1 | Owned transactional import/export and restore drill |
| WC-026 Design system and responsiveness | Partial | R2 | One styling system, tokens, screenshots, accessibility |

## 21. First 40 Implementation Batches

Each batch should be one narrow, reviewable change with its own validation and
documentation update.

1. Freeze feature breadth and record the baseline.
2. Back up the current database and document assets.
3. Classify every dirty worktree entry without deleting or resetting anything.
4. Hide broken CSV, research, and fake-search affordances.
5. Generate the backend route-security inventory.
6. Add the route-inventory failure test.
7. Apply authentication to the root API router.
8. Add and review the public allowlist.
9. Add negative unauthenticated mutation tests.
10. Standardize owned-parent resolution helpers.
11. Repair research-session creation ownership.
12. Repair research-message ownership and add cross-user tests.
13. Rebuild one CSV export as a real owned file response.
14. Rebuild CSV preview/apply with limits and transaction rollback.
15. Add CSV download, injection, ownership, and malformed-file tests.
16. Introduce the public error catalog and request IDs.
17. Remove raw exception strings and hardcoded log paths.
18. Add the unified AI provenance/privacy schema and migration.
19. Remove silent AI mock fallback and add explicit provider-failure states.
20. Enforce AI route ownership and non-recommendation prompts.
21. Run the bounded styling-pipeline proof.
22. Formalize the utility compiler and design tokens.
23. Build the core component and data-state primitives.
24. Rebuild grouped responsive navigation.
25. Convert the company workspace to stable tabs.
26. Add core route loading, error, and not-found boundaries.
27. Replace browser alerts and preserve failed-form input.
28. Add responsive, visual, and accessibility checks for core routes.
29. Split one backend schema domain and one frontend API/action domain.
30. Organize the classified worktree into a clean release baseline.
31. Add CI, PostgreSQL migration smoke, secret scan, and lint.
32. Run the alert-evidence browser workflow against a clean E2E image.
33. Add structured request/run observability.
34. Implement and drill database/document backup and restore.
35. Add the first-class event/claim evidence-reference model.
36. Propagate text/PDF/XBRL locators into events and alerts.
37. Add safe text highlight and PDF coordinate overlay.
38. Build evidence-integrity checks.
39. Certify reviewed real-source US financial histories.
40. Certify reviewed real-source India financial histories.

After batch 40, proceed in this order:

```text
point-in-time facts
-> integrated Today/company/valuation workflows
-> PostgreSQL corpus search
-> language change
-> contradiction inbox
-> valuation evidence graph
-> reviewed work products
-> saved monitors and measured background work
-> portfolio FX/corporate actions/attribution/exposure
-> provider expansion
-> certification trial
```

## 22. Metrics and Acceptance Targets

### Trust and security

- 100% of non-public operations require identity.
- 100% of user-owned child writes resolve an owned parent.
- 100% of material claims have an exact locator or explicit no-locator state.
- 100% of material edits have durable audit history.
- 0 provider failures silently become mock success.
- 0 known cross-user data leaks in the ownership matrix.
- 0 public responses expose raw internal exception detail.

### Data

- At least one declared, representative real-source US and India profile passes
  before the first certification gate.
- The gold corpus expands to multiple filings and layouts per supported profile.
- 100% of promoted supported statement totals reconcile within declared
  tolerances.
- 100% of material facts preserve source and temporal identity.
- 0 unsupported parser conditions are silently promoted.

### UX

- zero undefined design tokens
- zero unprocessed utility-class dependencies
- all core routes have route boundaries
- desktop, tablet, and mobile visual checks pass
- keyboard-only completion passes for the five core jobs
- all status information has a non-color cue
- no fake search, fake live data, or fake source-backed claim remains

### Reliability

- clean clone setup passes
- main branch CI stays green
- restore drill passes
- failure-state browser suite passes
- no untested user-visible import/export path
- no critical operation lacks a request or processing-run identifier

### Workflow

- alert to evidence to thesis to valuation to portfolio is one navigable flow
- the top five jobs require no Settings/Admin detour
- every review disposition is durable
- dashboard first viewport contains unresolved work rather than generic counts
- reviewed work products reproduce from their as-of snapshot

### AI

- 100% of persisted outputs expose provider, model, prompt, source scope,
  `is_mock`, privacy disclosure, limitation, confidence, and review status
- 0 source-scope violations in the certification set
- 0 recommendation prompts in production
- citation precision, coverage, and unsupported-claim thresholds are defined
  and passed before source-backed AI is marketed as trusted

### Portfolio

- transaction/cash/holding ledger reconciles
- 100% of active currency conversions have source and as-of time
- corporate-action application is idempotent and reversible
- benchmark and contribution calculations pass fixed regression cases
- unavailable data never becomes zero exposure or zero value

## 23. Stop Rules and Deferrals

Stop the current feature batch and repair the issue if:

- ownership or authentication regresses
- migration history becomes ambiguous
- a provider or AI failure appears as success
- source evidence is lost during normalization
- a material fact is overwritten without revision history
- a clean-clone or restore test fails
- a page displays mock, stale, or partial data as trusted

Do not start:

- provider expansion before R1-R3
- vector search before PostgreSQL full-text search is measured
- background infrastructure before synchronous duration is measured
- public deployment before a separate security program
- broker sync before official OAuth, encryption, revocation, and audit design
- market-regime claims before deterministic source-backed inputs exist
- new valuation methods before input evidence and core workflow integration pass
- external notification channels before saved monitors and run control exist
- legacy fallback removal before real-source certification

## 24. Decisions That Can Wait

These decisions do not block R0-R6:

- exact India provider
- exact market-price provider
- transcript and estimate provider
- external notification channel
- public deployment strategy
- team roles
- broker integration
- vector database

When a provider decision becomes active, use the provider decision record in
R8.1. Do not let an API key determine product architecture.

## 25. Final Definition of Done

The product is 100% complete against this world-class local-first scope only
when all of the following are true:

- [ ] current security and ownership defects are closed
- [ ] transfer and recovery workflows work
- [ ] one frontend system renders coherently at all supported widths
- [ ] the repository is clean, reproducible, tested, and restorable
- [ ] material evidence is exact-linked or explicitly limited
- [ ] representative real-source US and India histories are certified
- [ ] point-in-time facts and decision snapshots are reproducible
- [ ] the five daily jobs work end to end
- [ ] search, language change, contradiction, and evidence dependencies work
- [ ] portfolio currency, corporate actions, attribution, and exposures work
- [ ] every production provider has an approved contract
- [ ] AI provenance, privacy, citation, review, and evaluation gates pass
- [ ] accessibility and performance budgets pass
- [ ] the sustained daily-use trial reveals no unresolved critical trust defect
- [ ] current-state, capabilities, security, architecture, and runbooks agree

The central test is simple:

> Can the user trust what the product says, prove where it came from, understand
> what changed, see what it affects, and reproduce the decision later?

If the answer is not consistently yes, the product is not yet world class,
regardless of how many routes, pages, models, or calculations it contains.
