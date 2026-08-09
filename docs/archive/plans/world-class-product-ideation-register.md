# World-Class Product Ideation Register

> **2026-08-08 country-statistics update:** `countrystats.xls` now preserves an
> exact active source version and all 20 meaningful fields. API and mapping reads
> exclude inactive history and expose source provenance. The live mirror has 14
> typed sources, 3,290 rows, and 12 complete active provenance records with no
> mismatch. All current application source-specific typed Damodaran importers
> now use preserved versions; 21 mirrors remain partial or unsupported. See
> `next-5-damodaran-versioned-country-statistics-checkpoint-2026-08-08.md`.

> **2026-08-08 pricing update:** PE, PBV, PS, and EV/EBITDA now preserve
> independent source versions and complete workbook controls. Relative valuation
> assembles active rows by source and returns per-method provenance rather than
> selecting an arbitrary sparse row. All 35 mirrors are present; 13 have typed
> rows, 9 are supported, 13 partial, and 13 unsupported, for 3,163 typed rows.
> Active provenance is 11 complete / 0 partial / 0 missing / 0 mismatched.
> Country statistics remain the next version conversion. See
> `next-20-damodaran-versioned-pricing-and-relative-valuation-checkpoint-2026-08-08.md`.

> **2026-08-08 status:** The Damodaran runtime mirror has active source-version
> provenance for Capex, ROE, Margin, Working Capital, Dividend, FCFE, and
> Volatility. All 35 files are present; 9 have typed rows, 5 are fully supported,
> 17 are partial, and 13 are unsupported, for 2,787 typed rows. Active typed
> provenance is 7 complete / 0 partial / 0 missing / 0 mismatched. Pricing and
> country-stat paths still need version conversion. See
> `next-20-damodaran-versioned-volatility-and-real-options-api-checkpoint-2026-08-08.md`.

> **2026-08-07 status:** The current quality-adjusted estimate is 75% against
> the declared local-first scope and 64% against the world-class daily-driver
> target. The current shape, scorecard, limitations, and next sequence are in
> `product-agent-status-brief-2026-08-07.md`.

**Status:** Active living register  
**Started:** 2026-07-25  
**Update rule:** Change a status only when code, tests, and current-state docs support it.

## 1. Why This File Exists

The repository already contains two older world-class planning documents:

- [Archived market-intelligence app plan](../archive/world_class_market_intelligence_app_plan.md)
- [Archived expansion supplement](../archive/needs-review/world-class-expansion-supplement-master-plan.md)

They are historical inputs, not current execution truth. They contain useful ideas, but their
completion claims predate the current code audit and should not be revived wholesale.

This register keeps one current list of:

- capabilities that are actually shipped
- capabilities that are partial or mocked
- proposed features and their dependencies
- features that remain blocked on a provider or security decision
- explicit deferrals and rejections

## 2. Status Vocabulary

| Status | Meaning |
|---|---|
| Shipped | Implemented, user-visible where applicable, and verified by tests or a repeatable manual workflow |
| Partial | A real foundation exists, but the end-to-end workflow or trust standard is incomplete |
| Proposed | Not implemented; acceptance criteria are recorded |
| Provider decision | Implementation should not start until a source, license, cost, and data contract are approved |
| Deferred | Valuable later, but deliberately outside the current product boundary |
| Rejected | Conflicts with product, trust, security, or investment-language rules |

## 3. Blunt Assessment

This is already a broad and technically serious local investment research system. It is not yet
a world-class product.

The main reasons are:

1. Representative AAPL and APSEZ normalized histories now pass; breadth across additional issuers, filing layouts, and accounting policies remains unproven.
2. India filings, fundamentals, rates, and market data remain mostly manual or provider-dependent.
3. Exact evidence works for new supported records and has on-demand integrity checks, but historical coverage, external-link health, and scheduled auditing remain incomplete.
4. Point-in-time history covers reviewed financial facts only; prior decisions and valuations are not fully reproducible.
5. Search covers six stored domains, but lacks section, research-message, AI-output, saved-query, and representative relevance coverage.
6. Contradiction and language-change review lacks durable disposition and thesis-falsification mapping.
7. Portfolio attribution, multi-currency accounting, and corporate actions remain incomplete.
8. Provider scheduling, retry control, and saved monitoring are not built.
9. Dashboard and stored-corpus search have first query/latency budgets, but large-table, browser-render, provider, and concurrent-load performance remain unmeasured.
10. Local authentication and recovery are real foundations, but the app is not safe for public deployment.

The next advantage should come from trust and workflow depth, not from adding more dashboard panels.

The measured product/code/UX audit and quality-adjusted completion score are in
[product-codebase-ux-and-architecture-assessment-2026-07-25.md](product-codebase-ux-and-architecture-assessment-2026-07-25.md).

## 4. What “World Class” Means Here

A world-class version of this product should:

- connect every important claim to a source, timestamp, claim type, confidence, and exact locator
- distinguish reported facts, calculations, assumptions, estimates, AI interpretation, and mock data
- show what changed over time, not only the latest state
- connect source changes to thesis assumptions, valuation inputs, and portfolio exposure
- preserve point-in-time truth so later revisions do not rewrite prior decisions
- make missing, stale, partial, conflicting, and unconfigured data impossible to overlook
- produce reusable research work products without hiding source limitations
- remain fast and reliable enough for repeated daily use
- keep private portfolio and thesis data local unless an explicit provider action requires disclosure
- never convert research evidence into buy/sell instructions

## 5. Current Capability Register

| ID | Capability | Status | Current evidence | Remaining gap |
|---|---|---|---|---|
| WC-001 | Local authentication and user ownership | Partial | Signed identity assertions; auth-by-default; two-route public allowlist; route inventory; negative ownership coverage for portfolio, alert/evidence, thesis, valuation/drafts/AI, research, decisions, briefs, and transfer | Remains local-only; public deployment requires a separate identity, authorization, CSRF, HTTPS, audit, and recovery program |
| WC-002 | Company setup and US/India identity | Partial | Market, exchange, local symbol, regulatory identity, setup checklist, taxonomy fallback, persisted Damodaran mapping, and authenticated create workflow | India provider-backed identity and filings are missing |
| WC-003 | SEC and RSS ingestion | Partial | Real ingestion, deduplication, safe URL validation, processing runs, SEC readiness UI, and deterministic failed-RSS browser proof | Scheduling, retries, live-provider failure matrix, and broader source coverage |
| WC-004 | Raw document and PDF custody | Shipped | Bounded list responses, authenticated PDF bytes, bounded authenticated page PNGs, hashes, source metadata, and restore-tested document-byte custody | Off-device scheduling/encryption and broader corpus search |
| WC-005 | Financial extraction candidates | Partial | Text, PDF, Screener, and XBRL candidates with review gates and typed locators; trusted PDF rows/components render exact overlays; AAPL/APSEZ preserve 75 exact promoted facts/calculations; APSEZ source facts pass 6/6 profit/attribution identities | OCR, complex tables, balance-sheet/cash-flow totals and subtotals, and broader real-source profiles |
| WC-006 | Canonical normalized financials | Partial | Normalization, coverage, reconciliation, trust-ready states, annual identity evaluation, and portable AAPL/APSEZ `US`/`IN` certification proof | Broader issuer/layout/accounting-policy coverage and cautious legacy fallback retirement |
| WC-007 | Damodaran-style valuation | Shipped | FCFF, WACC, scenarios, sensitivity, reverse DCF, diagnostics, durable reviewed drafts, and identity-driven trust downgrade for source actuals | Better real-source actuals, evidence graph, and reporting automation |
| WC-008 | Country and currency valuation context | Partial | Market/country context and currency consistency checks | Native/reporting/portfolio/valuation currencies plus source-backed FX |
| WC-009 | Macro sensitivity | Shipped | Series, sector, scenario, top-down, and bottom-up workbench | Provider freshness automation and scenario audit exports |
| WC-010 | Event extraction and scoring | Partial | Rule-based events, deterministic scores, explanations, corroboration links, and conservative exact-span backfill for uniquely matching historical claims | Broader pipeline span propagation, calibration, temporal comparisons, and false-positive measurement |
| WC-011 | Alert review queue | Partial | User-owned alerts, review states, portfolio priority, alert detail route | Saved monitors, delivery channels, queue analytics, review-quality feedback loop |
| WC-012 | Alert-to-evidence trail | Expanded partial 2026-08-07 | Typed authenticated responses, validated text/page/section/PDF-region references, safe exact highlighting, explicit fallback states, owned impacts, bounded integrity checks, and a dry-run-first exact historical text-span queue | Manual resolution of unmatched/ambiguous history, broader pipeline propagation, dead-link checks, and scheduled monitoring |
| WC-013 | Thesis and contradiction workflow | Partial | Thesis notes, assumptions, drift, evidence ledger, event impact foundation | Reliable contradiction queue, falsification review, and source-backed drift timeline |
| WC-014 | Narrative tracking | Partial | Narrative models and pages exist | Management-language shifts, cross-period comparison, transcript coverage |
| WC-015 | Decision journal and variant perception | Partial | Decision, evidence-ledger, and variant-perception models/routes/pages exist | Guided review loop, outcome attribution, and point-in-time snapshots |
| WC-016 | Portfolio lifecycle | Shipped | Holdings, transactions, cash, snapshots, pricing honesty, ownership checks | Corporate-action automation, tax lots, multi-currency accounting |
| WC-017 | Portfolio analytics and reporting | Partial | Valuation and basic analytics exist | Performance attribution, factor/sector/country exposure, benchmark comparison, reusable reports |
| WC-018 | Provider and data health | Shipped | Capability matrix, provider readiness, processing-run status, evidence hash/locator checks, promoted-financial fiscal checks, per-history normalization/reconciliation/identity gates, derived certification coverage, and active Damodaran source-version/hash visibility for twelve current typed sources | Typed coverage breadth, historical macro provenance, freshness SLAs, coverage trends, dead-link checks, alerting, and retry controls |
| WC-019 | Authenticated browser workflows | Partial | Fourteen isolated workflows pass; a fifteenth weighted-industry/source-provenance workflow compiles and is registered | Execute the new workflow, then cover live-provider behavior, every portfolio mutation, long-running jobs, and the remaining dynamic matrix |
| WC-020 | Market regime | Partial | Clearly labeled mock UI foundation | Deterministic sourced inputs and formulas; do not present as real until then |
| WC-021 | AI research assistance | Partial | Unified owned output schema; exact declared-source citation validation; deterministic evaluation fixtures; approve/reject/revision UI; provider/model/mock/privacy/transmission/review/failure fields; no silent fallback | Provider-generated complete citations, larger evaluation corpus, source-grounded retrieval, and asynchronous execution |
| WC-022 | Unified corpus search | Partial | PostgreSQL full-text search and GIN indexes cover documents, events, owned alerts, theses, decisions, and valuations; typed results include claim/source labels, timestamps, excerpts, filters, exact links, ownership proof, and a 14-query/750-ms budget | Section/research-message/AI-output coverage, saved searches, relevance evaluation, highlighting for mutable records, and large-corpus proof |
| WC-023 | Earnings calls and estimate revisions | Provider decision | No verified transcript or consensus provider | Licensed source, timestamps, revision history, speaker attribution, source links |
| WC-024 | Operational reliability | Partial | Docker, migrations, health, rate limits, request/run correlation, safe public errors, JSON stdout logs, CI, backup/restore, secret/static gates, broad tests, dashboard/search budgets, and container-isolated Linux frontend native modules | Broader route/large-table/concurrent budgets, off-device backup automation, and background job controls |
| WC-025 | Data transfer and backup exports | Partial | Real CSV downloads; formula escaping; relationship-backed fields; owner-scoped portfolio exports/imports; bounded preview/apply; atomic rollback; valid browser apply/download proof; separate checksum-verified database/document restore drill | Off-device encrypted backup scheduling and broader transfer browser coverage |
| WC-026 | Frontend design system and responsiveness | Partial | Tailwind/PostCSS, project-owned tokens, reusable page/data-state components, responsive shell, semantic/overflow gates, and 12 route screenshots | Inline styles and legacy page-specific patterns remain; dynamic workflow visual coverage is incomplete |
| WC-027 | Market-price routing and provenance | Shipped | Configured typed provider boundary; no route-level yfinance bypass; explicit unofficial-source state; stable errors; processing runs; stored provider/timing/adjustment/warnings; manual and legacy labels in API and UI; deterministic backend/unit/browser verification | This is routing integrity, not certified market coverage; provider policy/quota controls, Tiingo, Upstox, and live drift tests remain |

## 6. Prioritized Feature Backlog

### P0A: Correctness and Control-Plane Closure

These items precede the existing trust backlog.

| ID | Feature | Status or why it matters | Acceptance gate |
|---|---|---|---|
| IDEA-027 | Backend auth-by-default | Shipped 2026-07-25 | Root API router requires signed identity; only an explicit reviewed allowlist is public; automated inventory rejects accidental public operations |
| IDEA-028 | Research ownership repair | Shipped 2026-07-25 | Session create persists current user; all session/message reads and writes resolve an owned parent; cross-user tests pass |
| IDEA-029 | Data-transfer repair | Shipped as interchange 2026-07-25; backup claim blocked | True CSV responses, relationship-backed fields, size/row limits, owned parents, preview/apply transactions, formula escaping, and focused tests pass |
| IDEA-030 | AI honesty and privacy contract | Shipped foundation 2026-07-26 | Owned provenance/failure schema, SHA-256, source scope, explicit mock/provider/transmission state, versioned disclosure, no silent fallback, owned routes, and non-recommendation prompts pass; citation/evaluation and full review UI remain under WC-021 |
| IDEA-031 | Frontend styling pipeline | Shipped foundation 2026-07-26 | Tailwind/PostCSS processes utilities, project tokens resolve, production build passes, and responsive screenshots cover core routes; legacy inline layout remains |
| IDEA-032 | Shell and route-state rebuild | Shipped foundation 2026-07-26 | Grouped responsive nav, company tabs, real evidence search, and loading/error/not-found boundaries cover core routes |
| IDEA-033 | Clean release and CI baseline | Partial | Isolated fresh migration/tests/build, browser CI, deterministic secret scanning, scanner tests, and project-skill/static integrity gates exist; a reviewable clean repository history remains |
| IDEA-034 | API/domain decomposition | Monolithic schema/client/action files increase regression cost | Split one domain at a time with stable compatibility imports and no broad route rewrite |
| IDEA-035 | Market-provider routing correction | Shipped 2026-08-01 | Every price fetch uses the selected provider contract; yfinance is explicit personal-use opt-in; provider, source time, currency, timing/adjustment limits, warnings, duplicate behavior, and failure are tested and visible |
| IDEA-036 | Provider contract and quota ledger | More keys without use-scope, rate-limit, freshness, and failure metadata will make data trust worse | Each provider records allowed use, terms-review date, capability/market coverage, quota state, freshness SLA, last success/failure, and stable errors in Provider Health |
| IDEA-037 | OpenAI-compatible evaluation providers | NVIDIA NIM and Groq can reduce development inference cost, but free access is not a production contract | Explicit provider selection, server-only keys, capability checks, no silent fallback, transmission disclosure, stable errors, provenance, mocked failure tests, and evaluation-corpus thresholds pass |
| IDEA-038 | Public identity/macro/news expansion | OpenFIGI, World Bank, BLS, and GDELT add high-value coverage without pretending to be exchange market data | Implement one capability at a time with source links, time/provenance, bounded payloads, rate limits, processing runs, provider health, and honest discovery-versus-fact labels |

### P0: Trust Before Breadth

| ID | Feature | Why it matters | Acceptance gate |
|---|---|---|---|
| IDEA-001 | Exact event evidence locators | Expanded foundation 2026-08-07 | New events validate exact text/section locators and reproducible PDF regions; a bounded processing-run-backed workflow backfills unique exact historical matches; unmatched/ambiguous/conflicting rows now have bounded exact search and reviewed occurrence selection with locked revalidation and provenance; fuzzy/normalized/OCR-only evidence remains open |
| IDEA-002 | Real-source normalization certification | Expanded representative foundation 2026-08-02 | Portable AAPL/APSEZ manifest passes with 75 exact promoted facts/calculations, seven trust-ready periods, markets `US`/`IN`, and APSEZ 6/6 statement identities; AAPL identity coverage is explicitly unavailable under its approved core set; expand before broad fallback retirement |
| IDEA-003 | Point-in-time data contract | Research decisions must not silently change after provider revisions | Every material fact has effective date, observed-at time, revision identity, source, and reproducible prior view |
| IDEA-004 | Evidence integrity checks | Expanded foundation 2026-08-02 | On-demand checks include missing timestamps/documents, hash/size and locator failures, PDF metadata, promoted-financial exactness, fiscal-period/end mismatches, statement identities, and inspectable per-history certification coverage; dead-link, scheduled, and full ownership audits remain |
| IDEA-039 | Cross-statement accounting identities | Partial foundation 2026-08-02 | Profit-after-tax and parent/NCI attribution checks expose formula, actual, expected, delta, tolerance, missing and duplicate facts; applicable failure blocks certification and valuation trust; add balance sheet, cash-flow movement, and declared total/subtotal identities |
| IDEA-040 | Exact rendered PDF evidence | Expanded foundation 2026-08-07 | Stored authenticated pages render under scale/pixel limits; trusted financial row/component and event-region geometry overlays proportionally; invalid geometry retains source-PDF/page fallback; broader layout profiles remain |
| IDEA-041 | Reproducible benchmark dataset versions | Expanded foundation 2026-08-08 | Capex, ROE, Margin, Working Capital, Dividend, FCFE, Volatility, PE, PBV, PS, EV/EBITDA, and Country Statistics preserve source hash, source date/confidence, active/superseded state, and typed row count; same hashes are idempotent and historical hashes can be reactivated; all current app source-specific typed paths are converted, while historical macro provenance and unimplemented mirrors still prevent complete point-in-time benchmark replay |
| IDEA-005 | Failure-state browser suite | Expanded baseline 2026-08-01 | Repeatable isolated tests cover setup, auth readiness, deterministic provider failure, stale write, alert evidence, CSV recovery/apply/export, review invalidation, and partial data states |

### P1: Research Workflow Differentiation

| ID | Feature | Why it matters | Acceptance gate |
|---|---|---|---|
| IDEA-006 | Unified source-backed search | Expanded foundation 2026-08-01 | Documents, events, owned alerts, theses, decisions, and valuations return typed stored records, snippets, timestamps, company/type filters, and exact links; section/research-message/AI-output coverage and measured relevance remain |
| IDEA-007 | Period-over-period language diff | Narrative change is often more valuable than a static summary | Compare equivalent filing sections or transcript speakers, preserve changed text, and link every change to both periods |
| IDEA-008 | Contradiction and falsification inbox | The product should challenge the thesis, not confirm it | Queue evidence against explicit assumptions and falsification triggers; require user disposition |
| IDEA-009 | Valuation evidence graph | Assumptions should be inspectable back to facts and user choices | Every material assumption links to reported inputs, formulas, overrides, reviews, and invalidating events |
| IDEA-010 | Research work products | Analysts need durable outputs, not only screens | Generate source-indexed memo/watchlist/earnings review exports with as-of time, limitations, and reviewed/unreviewed status |
| IDEA-011 | Saved monitors | Daily usefulness requires repeatable questions | Save company/source/metric/claim filters and record each run, changes, errors, and next run |

### P2: Portfolio Intelligence

| ID | Feature | Why it matters | Acceptance gate |
|---|---|---|---|
| IDEA-012 | Performance and decision attribution | Users need to learn whether decisions and theses worked | Time-weighted return, cash-flow handling, benchmark, security contribution, and point-in-time decision links are tested |
| IDEA-013 | Exposure and concentration engine | Ticker weights do not capture shared drivers | Sector, country, currency, factor, thesis-driver, and event exposure with source/formula metadata |
| IDEA-014 | Portfolio marginal | The next action depends on what the portfolio already owns | Show marginal concentration, scenario loss, thesis overlap, liquidity constraints, and unavailable inputs without recommendations |
| IDEA-015 | Multi-currency accounting | India/US portfolios need reproducible conversions | Store native/base/reporting currencies, source-backed FX, as-of times, formulas, and stale/missing blocks |
| IDEA-016 | Corporate-action ledger | Splits, dividends, mergers, and spin-offs affect history | Idempotent events update holdings/cost basis with reviewed source records and reversal support |

### P3: Data Coverage and Automation

| ID | Feature | Status dependency | Acceptance gate |
|---|---|---|---|
| IDEA-017 | Official India filing/fundamentals provider | Provider decision | Approved license/source, capability metadata, raw custody, timestamps, rate limits, duplicates, and partial states |
| IDEA-018 | Earnings-call transcripts | Provider decision | Speaker/time metadata, exact text links, terms compliance, and no unlicensed scraping |
| IDEA-019 | Consensus and estimate revisions | Provider decision | Point-in-time estimate vintages, contributor/provider terms, revision timestamps, and no backfilled hindsight |
| IDEA-020 | Background run control | Measured synchronous duration | Idempotent queued/running/partial/failed/cancelled states, retry policy, ownership, and UI visibility |
| IDEA-021 | Notification delivery | Saved monitors and background runs | In-app first; external channels require explicit configuration, throttling, provenance, and delivery audit |
| IDEA-022 | Market-regime productionization | Approved structured providers | Deterministic modules, formula, coverage, timestamp, confidence, drivers, blockers, and no buy/sell language |

### P4: Product Quality

| ID | Feature | Acceptance gate |
|---|---|---|
| IDEA-023 | Accessibility baseline | Shipped baseline 2026-07-31: semantic, keyboard, focus, overflow, responsive, and 12 screenshot checks pass; this is not a complete WCAG audit |
| IDEA-024 | Performance budgets | Partial foundation 2026-08-01: dashboard overview is bounded to 20 SQL/1,000 ms and corpus search to 14 SQL/750 ms locally; other routes, browser-render, concurrency, and large-table budgets remain |
| IDEA-025 | Backup and restore drill | Shipped local foundation 2026-07-31: versioned archive, manifest, retention option, table/checksum/document-byte verification, and destructive isolated restore; off-device encryption/scheduling remains |
| IDEA-026 | User-visible audit history | Material edits to thesis, evidence, financial review, valuation, and decisions show actor, time, old/new value, and reason |

## 7. Competitive Pattern Scan

The dated provider research and proposed delivery sequence for `IDEA-035`
through `IDEA-038` are in
[Free API Provider Landscape](free-api-provider-landscape-2026-08-01.md).

This is a pattern scan, not a clone list.

- Quartr emphasizes global search across investor-relations material, transcript search, source-linked summaries, and transcript highlighting. The relevant product lesson is exact source navigation and temporal management-language review. See [Quartr Features](https://quartr.com/features), [Transcript Search](https://quartr.com/features/transcript-search), [Summaries](https://quartr.com/features/summaries), and [Transcript Highlighting](https://quartr.com/features/transcript-highlighting).
- AlphaSense emphasizes generative search, deep research, monitoring, reusable work products, and structured financial data. The relevant lesson is turning search into a repeatable reviewed workflow rather than a one-off answer. See [AlphaSense Platform](https://www.alpha-sense.com/platform/).
- TIKR combines global financials, estimates, transcripts, screening, and valuation tooling. The lesson is that company research loses value when fundamentals, estimates, and valuation are disconnected. See [TIKR feature guidance](https://support.tikr.com/hc/en-us/sections/5636384240027-How-to-best-use-TIKR-features-and-tools).
- Koyfin emphasizes configurable portfolio reports covering performance, risk, exposure, and holdings. The lesson is that portfolio output should be reusable and comparable, not just a current-value panel. See [Koyfin Reports](https://www.koyfin.com/features/reports/).

The product should not compete by copying breadth. Its defensible position is local-first privacy plus unusually strong evidence, thesis, valuation, and portfolio traceability.

## 8. Completed 20-Step Batch: Alert Evidence Foundation

Completed on 2026-07-25:

1. Audited both archived world-class plans and kept them historical.
2. Selected alert-to-evidence traceability as the highest active trust gap.
3. Audited the existing event evidence endpoint and all three drawer entry points.
4. Replaced untyped ORM serialization with an explicit response schema.
5. Added the missing `is_mock` field to the backend response metadata contract.
6. Added required claim-type labels.
7. Added explicit complete, partial, and missing evidence states.
8. Added confidence and source timestamp fields.
9. Added bounded alert/event claim context with its origin.
10. Added a safe raw-document summary that never returns filing bodies or provider payloads.
11. Added document, original-source, and stored-PDF links.
12. Added explicit document-level locator precision and exact-locator warnings.
13. Added authentication to event evidence reads.
14. Added a user-owned alert evidence endpoint.
15. Filtered thesis impacts to the current user's thesis records.
16. Filtered valuation impacts to the current user's valuation models.
17. Rebuilt the drawer around typed data, loading, error, partial, and limitation states.
18. Routed alert surfaces through alert ownership and added the missing alert detail page.
19. Replaced non-actionable alert/event empty states and corrected event navigation.
20. Added backend ownership/leakage tests plus frontend contract/source tests.

The same audit exposed direct child-ID ownership gaps outside the evidence
endpoint. They were also closed in this batch: thesis assumption/impact and
valuation assumption/output/change-log/reverse-DCF routes now resolve through a
current-user parent, and manual valuation creation sets `user_id` explicitly.

## 9. Completed 30-Step Batch: Auth, Research, and Transfer

Completed on 2026-07-25:

- `IDEA-027` now has auth-by-default at the aggregate FastAPI router, a
  two-route public health allowlist, a generated inventory, and direct-port
  negative tests.
- `IDEA-028` now persists the current user, resolves all session/message work
  through an owned parent, rejects caller-created assistant messages, supports
  owner-only deletion, and has cross-user tests.
- `IDEA-029` now returns real CSV files, uses actual relationship/model fields,
  scopes portfolio rows to the current user, enforces bounded validation,
  supports preview/apply, and rolls transaction batches back atomically.

The exact numbered record and verification evidence are in
`../world-class-product-execution-roadmap-2026-07-25.md`, under the R1 progress
checkpoint. Transfer remains an interchange feature, not a backup, until a
restore drill succeeds.

### 9.1 Completed Five-Control R1 Batch

Completed on 2026-07-26:

- owned alert creation and daily-brief aggregation/persistence defects fixed;
  expanded cross-user AI and owned-domain coverage passes
- stable safe public errors plus request IDs implemented; raw exception strings
  and the fixed error-log path removed
- request-aware JSON stdout logging implemented without provider bodies,
  prompts, credentials, or private payloads
- MD5 and process-randomized provenance hashes replaced with SHA-256
- `IDEA-030` contract and migration shipped across summaries, research,
  valuation memo, narrative-to-numbers, narrative extraction, deterministic
  staleness triage, and thesis-impact proposals

Verification is 334 backend tests, 63 frontend tests, clean TypeScript and
production build, and Alembic head `b8b8b8b8b8b8`. Baseline completion remains
58% local-first and 47% world-class; this is control-plane closure, not evidence
or daily-driver completion.

## 10. Next Recommended Sequence

**Execution update 2026-07-31:** all ten items received implementation work.
Items 1, 2, 3, 5, 6, and the HTTP portion of 7 have passing foundations. Item
4 has a fail-closed harness but zero real certified histories. Items 8-10 are
bounded first-domain foundations and do not satisfy their full roadmap gates.
Exact status and validation are recorded in
`next-10-execution-checkpoint-2026-07-31.md`.
The final regression baseline is 352 backend tests, 67 frontend tests,
TypeScript, and 8 isolated Playwright workflows. The PDF workflow also verifies
that promoted audit records leave the active extraction-review queue.

**Execution update 2026-08-01:** the follow-on ten-item reliability batch is
recorded in `next-10-execution-checkpoint-2026-08-01.md`. The verified baseline
is 355 backend tests, 68 frontend tests, TypeScript, production build, static
repository gates, and 13 isolated Playwright workflows. This adds a first
dashboard performance budget and an on-demand integrity audit; it does not
change the zero real-history certification result or the dated completion score.

**Search execution update 2026-08-01:** the next ten search tasks are recorded
in `next-10-search-execution-checkpoint-2026-08-01.md`. Search now covers six
stored domains with owner filters, typed provenance, deterministic source-first
ranking, PostgreSQL GIN indexes, and production-stack browser proof. The current
baseline is 358 backend tests, 70 frontend tests, TypeScript, production build,
and 14 isolated Playwright workflows. This expands `WC-022`; it does not satisfy
large-corpus relevance evaluation or real-source history certification.

Completed 2026-07-26: the former items 1-5 now have code, automated contracts,
browser evidence, and a clean isolated release gate. This did not change the
dated product score.

1. [Complete] Add database/document backup and complete a restore drill.
2. [Complete foundation] Propagate exact page/section/span locators into alert evidence.
3. [Complete foundation] Add AI citation verification, evaluation corpus, and approve/reject workflow.
4. [Blocked: 0 certified] Certify representative real-source US and India histories.
5. [Complete baseline] Add accessibility and responsive screenshot gates for the core jobs.
6. [Complete for known calls] Replace the remaining production `alert()`/`confirm()` interactions with
   inline or modal states that preserve user input.
7. [Partial] Split dashboard fan-out behind a bounded overview contract and measure its
   server-render/database budget.
8. [Partial, financial domain only] Add point-in-time facts after real-source certification.
9. [Partial, documents/events] Add PostgreSQL full-text corpus search with exact evidence links.
10. [Partial review queue] Build contradiction and language-change workflows on the certified corpus.

## 11. Do Not Build Yet

- Public deployment, team accounts, or cloud tenancy without a separate security design.
- Broker credential storage or trading execution.
- Twitter, Reddit, or prohibited HTML scraping.
- Unlicensed transcript or estimate ingestion.
- A vector database before PostgreSQL full-text search is measured and found insufficient.
- Market-regime output presented as real before source-backed formulas are implemented.
- AI-generated claims without source IDs, limitations, confidence, prompt/model provenance, and review state.
- Buy/sell recommendations or guaranteed-return language.

## 12. Maintenance Rule

For every substantial feature task:

1. Update the relevant `WC-*` capability row.
2. Update or add one `IDEA-*` row with an acceptance gate.
3. Link code/tests or the current-state document that proves a shipped status.
4. Record new limitations instead of hiding them.
5. Move rejected or obsolete ideas to an archive only after explaining why.
