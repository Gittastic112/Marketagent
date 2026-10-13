# Completion tracker: local research release v1

Created October 10, 2026. **Accepted milestones: 2/10 (20%). Next: M03.**
This is a new acceptance baseline, not a claim that the existing app is 0% built.
Much of the implementation exists; historical tests do not close today's gates.

## What 100% means

A dependable local, single-user research app for the confirmed US/India universe,
USD portfolio reporting, daily prices, reviewed financials, explainable valuation,
portfolio history and an evidence-linked daily review. The exact company/security
selection and user assumptions remain in the [single ledger](../agent_capabilities_and_limitations.md#confirmed-scope-and-input-checklist).
The September selection is a fixed scope, not a live market-cap ranking.

The release is complete when all ten gates below pass, the genuine-input daily
workflow works, recovery is rehearsed, and remaining optional features are visibly
bounded. An implemented manual India/report-review path can pass; pretending an
unimplemented automated feed works cannot. External data, financial review and
off-device recovery can require user input. They cannot be replaced by fixtures.

Public hosting, broker integration/trading, real-time feeds, prohibited scraping,
paid provider expansion, a Sheets alternative and unused workbook parsers are
outside this release. Experimental methods with no validated consuming workflow
must be clearly unavailable or explicitly experimental, not quietly counted as
complete. Scope additions require a new version of this plan and an explicit
decision; do not move the denominator to manufacture progress.

## How to execute a percentage request

- **"Finish 10%"** means finish M01 and its acceptance gate. **"Finish 40%"** means
  finish every unfinished milestone through M04 in order.
- **"Finish the next 10%"** means the earliest unfinished milestone. If M01 is
  partly done, finish it first. Never silently select ten arbitrary tasks.
- Each milestone contributes ten **acceptance points**, not ten percent of hours,
  code, complexity or remaining effort. No credible effort percentage is available
  without executing the remaining work. Do not claim a milestone fraction as an
  engineering-time estimate.
- Read the handoff, this tracker, its cited owners, and current code/tests. Work
  sequentially unless delegation is explicitly requested. This plan launches no agents.
- A checkbox needs dated evidence. A milestone closes only when every checkbox
  and its gate passes. Blocked checks stay open; record exact missing input in the
  ledger. Work that can proceed safely in later milestones earns no cumulative gate.
- Preserve stable IDs. On completion, mark checks, attach one dated evidence
  checkpoint, update the table and handoff, and reconcile affected current docs.
  Reopen the gate if a later change invalidates its evidence.

The [product roadmap](product-roadmap.md) owns product priorities; this document
owns percentage requests, ordering and execution checklists. The
[feature register](feature-register.md) owns capability status, and the ledger
owns limitations. [Knull](../../Knull%28readme%29.md) remains the detailed design
and exclusive ownership reference for its five workstreams, mapped below.
It is not a second progress counter or an instruction to dispatch agents.

## Milestone board

| Gate | Cumulative target | Deliverable | Depends on | State | Evidence |
|---|---:|---|---|---|---|
| M01 | 10% | Measured, lean, reproducible local foundation | None | Accepted October 10 | [Rollout and browser proof](../archive/checkpoints/2026/m01-foundation-complete-2026-10-10.md) |
| M02 | 20% | Clear code and folder ownership | M01 | Accepted October 11 | [Ownership and validation checkpoint](../archive/checkpoints/2026/m02-ownership-2026-10-11.md) |
| M03 | 30% | Reliable recovery and local security | M02 | In progress | [Recovery](../archive/checkpoints/2026/m03-recovery-2026-10-11.md), [security](../archive/checkpoints/2026/m03-security-2026-10-11.md) |
| M04 | 40% | Dependable identities, prices and ingestion | M03 | Checks verified; M03 prerequisite open | [Identity and ingestion](../archive/checkpoints/2026/m04-ingestion-2026-10-11.md), [consuming pages](../archive/checkpoints/2026/m04-m09-coverage-2026-10-12.md) |
| M05 | 50% | Reviewed financial coverage for the scoped universe | M04 | In progress | [Official reports and review batches](../archive/checkpoints/2026/m05-source-review-preparation-2026-10-13.md) |
| M06 | 60% | Consistent valuation and sensitivity | M05 | In progress | [Saved sensitivity and browser proof](../archive/checkpoints/2026/m06-sensitivity-2026-10-11.md) |
| M07 | 70% | Correct portfolio history and performance | M06 | In progress | [Recorded replay and provenance](../archive/checkpoints/2026/m07-portfolio-replay-2026-10-11.md) |
| M08 | 80% | Connected daily research and review | M07 | In progress | [Private brief context](../archive/checkpoints/2026/m08-private-brief-context-2026-10-11.md) |
| M09 | 90% | Complete browser workflows and measured responsiveness | M08 | Checks verified; M08 prerequisite open | [Connected workflow verification](../archive/checkpoints/2026/m05-m09-workflows-2026-10-13.md) |
| M10 | 100% | Proven local daily-driver release | M09 | Not started | None |

October 12 recovery and coverage evidence remains linked in the preceding
checkpoints. The [October 13 connected-workflow checkpoint](../archive/checkpoints/2026/m05-m09-workflows-2026-10-13.md)
closes M05-06, M06-05, M08-03/06/07 and verifies all M09 technical checks. Its recorded
official-source morning flow and separate due-cycle test preserve their distinct
source/fixture boundaries. Final return labels, affected browser flows, measured
process-cold/warm profiles and normal rollout are verified. Genuine-input, human
review and recovery/host gates remain open in the [single ledger](../agent_capabilities_and_limitations.md).
M04 and M09 have verified checks but open prerequisites. Cumulative acceptance
remains 20 points; the next milestone is M03.

The [ordered operator handoff](../agent_capabilities_and_limitations.md#ordered-operator-handoff)
maps every open M03-M09 check to the exact operator input and agent-owned work.
October 13 follow-up prepares a read-only financial/AI review packet and disables
the legacy self-scoring extraction command; neither preparation confers approval
or changes the acceptance total.

## M01: measured, lean, reproducible foundation

Owners: Compose files, backend Dockerfile/requirements, repository tooling.

- [x] M01-01 Measure repeated container CPU/RAM, restart state, actual ports and
  Docker image/cache/volume usage. Separate startup load from idle behavior.
- [x] M01-02 Identify disposable caches versus persistent volumes, backups and
  source material. Perform bounded cache cleanup and record before/after usage.
- [x] M01-03 Separate backend runtime/test dependencies and image targets; exclude
  unrelated folders and nested environment files from the backend build context.
- [x] M01-04 Make the backend the sole normal startup migration owner. Workers
  wait for its healthy schema; make pgAdmin opt-in without automatic restart,
  constrain development watching and align the dev heap with its memory limit.
- [x] M01-05 Obtain working Git, inventory tracked/untracked/prior changes, and
  preserve a source baseline with HEAD/status and a verified source-only safety
  archive. Protected environment paths are excluded; prior work is preserved.
  The checkpoint records the published source baseline for later integration.
- [x] M01-06 Rebuild and apply the validated configuration to the normal app in
  a controlled maintenance window after M03's current-backup preflight. Verify
  source/image identity, worker commands, readiness and idle resources; retain
  the existing source-worker stopped state unless its external-fetch operation
  is explicitly resumed. Do not read protected environment files through tools.
- [x] M01-07 Complete the existing full backend/frontend/type baseline, API/schema
  boundary checks and representative disposable browser smoke; record inherited
  failures separately. The October 10 infrastructure checks alone do not close this.

Gate: a preserved source baseline, passing gates and a normal runtime known to
match it. M03's backup preflight is reusable existing tooling, not a dependency
on finishing M03; fix/verify it first if current recovery cannot be trusted.
No database reset, volume removal or new provider call is needed for cleanup.

Accepted October 10: [dated evidence](../archive/checkpoints/2026/m01-foundation-complete-2026-10-10.md)
includes a 109-table backup/restore comparison, identical post-rollout fingerprints,
source/image checks, disposable functional workflows and authenticated normal
desktop/mobile checks after the dependency patch. The unchanged route-timing gate
passed on repeat after one slow local sample; the checkpoint and PR retain results.
Existing normal screens show **Mock Data**; this foundation
gate does not certify genuine-input portfolio coverage or complete M03 recovery.

## M02: clear code and folder ownership

Owners: [code map](../code-map.md), actual callers and contract tests.

- [x] M02-01 Classify every root script and generated directory using Git history,
  caller searches and the runbook. Relocate retained one-off scripts under an
  explicitly retired tooling directory; preserve necessary compatibility entry
  points. Remove only proven generated/unused artifacts and record exact paths.
- [x] M02-02 Extract server actions from the 1,188-line frontend action collection
  by company, evidence, portfolio and valuation workflow. Keep old named imports
  working; share only validation/error/revalidation helpers that have real callers.
  Test payloads, auth, redirects, errors and save behavior, not just source text.
- [x] M02-03 Extract remaining legacy backend contracts by domain, starting with
  brief contracts in W1 when needed. Keep identical legacy class exports and
  public OpenAPI compatibility. Pure contracts must not import HTTP or persistence.
- [x] M02-04 Split peer review, benchmark parsing and assumption autofill where
  responsibilities actually diverge. Inspect the 1,769/1,459/1,246-line owners;
  preserve atomic writes, receipt hashes and input provenance. File size alone
  does not justify a move. Keep one authoritative market-provider factory.
- [x] M02-05 Separate the largest UI orchestration from presentation, beginning
  with Data Health, peer review and draft review. Retain loading/error/partial/
  stale/not-configured/Mock Data states and request identity isolation.
- [x] M02-06 Establish contract-drift verification for frontend/backend types
  before any generated-client migration. Preserve aliases, envelopes and error
  identity. Retire an alias only after callers and compatibility tests allow it.
- [x] M02-07 Update the existing code map and add focused dependency/import guards.
  Verify public API equality, ownership, affected workflows and browser behavior.

Gate: each changed workflow has one clear owner and no broken callers or source
loss. Keep the current modular monolith and database. Do not add microservices,
a second provider factory or a catch-all utilities framework for folder tidiness.

## M03: reliable recovery and local security

Owners: backup/restore scripts; [Knull W5](../../Knull%28readme%29.md#9-w5-consistent-backup-and-recoverable-evidence);
[security reference](../06-security-threat-model.md).

- [x] M03-01 Make the backup manifest and dump describe the same database snapshot
  during concurrent writes. Version the format and explicitly handle old backups.
- [x] M03-02 Verify both document_assets and private brief-source PDF bytes, full
  table inventories and content fingerprints. A table-count match alone is insufficient.
- [x] M03-03 Restore a fresh backup into a separate disposable PostgreSQL instance,
  verify the intact migration chain and asset bytes, and test failure recovery,
  worker stop/resume and interruption. Never replace the normal database for a test.
- [ ] M03-04 Complete host/configuration checks with the operator where access is
  required: least-privilege local administration, DB/admin credential rotation
  with persisted roles, disk encryption and encrypted off-device key/backup recovery.
- [x] M03-05 Bound expensive PDF parsing and review remaining fixed-host outbound
  clients, uploads, CSV exports and owner access. Test malicious/oversized input,
  cross-owner resources, request forgery and sanitized failure messages.
- [x] M03-06 Lock/reproduce the supported dependency environment, scan runtime and
  test dependencies plus container OS packages, and document update/rollback steps.
  Evaluate image/action pins without silently upgrading dependencies.
- [ ] M03-07 Demonstrate off-device recovery and document backup retention and
  maintenance cadence. Scheduling a job requires an explicit scheduling request.

Gate: repeatable restore evidence and closed local-release security blockers.
Public deployment remains outside scope even after this gate passes.

## M04: dependable identities, prices and ingestion

Owners: providers, market-data ingestion, source worker, Processing Runs and Data Health.

- [x] M04-01 Verify all ten scoped companies plus the separately selected GOOGL
  holding identity, exchange, currency, share class and issuer mapping. Do not
  silently replace an NSE security with an ADR or GOOG with GOOGL.
- [x] M04-02 Verify configured SEC, personal-use price, FRED and AI connectivity
  using explicit audited probes. Separate configured, last success, stale,
  failed, rate-limited and unavailable; no implicit provider fallback.
- [x] M04-03 Make daily-close cutoffs/timezones explicit for US/India markets,
  distinguish final history from quotes, and verify bounded/idempotent history
  updates. Document provider timestamps/delay when unknown.
- [x] M04-04 Exercise queue restart, failure/retry, weekday/DST scheduling, overlap
  prevention and source-worker stopped/disabled states. Every external attempt
  needs a truthful Processing Run. Preserve manual draft edits.
- [x] M04-05 Finish a reliable official India source selection/manual intake path
  with identity, dates and evidence locators. Add automation only if access is
  compliant and tested; otherwise label the manual step clearly.
- [x] M04-06 Surface missing price/FX/financial coverage and provider health at the
  consuming page. Keep unsupported FMP/market-regime/Sheets paths visibly unavailable
  or out of normal navigation rather than suggesting they are live services.
- [x] M04-07 Run recorded genuine-source checks plus deterministic failure/duplicate/
  freshness tests. External source failure blocks that coverage claim, not all development.

Gate: daily source inputs and their gaps are reproducible and visible across the
scoped universe, without silent fabrication, source promotion or external AI reads.

## M05: reviewed financial coverage

Owners: extraction, normalization, source certification; [Knull W2](../../Knull%28readme%29.md#6-w2-reviewed-usindia-financial-source-coverage).

October 13 [source preparation](../archive/checkpoints/2026/m05-source-review-preparation-2026-10-13.md)
retains official annual reports for all ten issuers and three target years, with
per-company review batches and source/candidate reconciliations. The real PDF
previews expose layout, unit and accounting-scope defects; this is not parser
certification. Human reference/model approval and remaining note work stay open.
No financial promotion or new acceptance points. Mac settings/backups are deferred
by the user and do not block this independent work.

- [x] M05-01 Build an issuer/period/source checklist for the scoped US/India
  companies using the existing AAPL/APSEZ certified paths as references. Record
  required source documents and human-review dependencies before execution.
- [ ] M05-02 Verify parser coverage against independent reviewed references,
  including a new US issuer/layout and India non-bank/bank layouts. Cover units,
  currency, dates, fiscal periods, duplicate/revised facts and exact source hashes.
- [ ] M05-03 Reconcile statements and review debt scope, leases, minority interests,
  cross-holdings, cash, diluted/class-specific shares and financial-service equity.
  Persist unresolved fields as gaps; never substitute benchmark/company values.
- [ ] M05-04 Review/promote only approved candidates and normalize histories for
  each scoped issuer. Keep issuer and security/share-class evidence distinct and
  preserve the provenance of previous reviewed values.
- [ ] M05-05 Confirm weighted industry mappings and country/currency conventions.
  Inspect the loaded benchmark versions/unsupported columns; each prior remains
  a reviewed prior, and each forecast remains an assumption.
- [x] M05-06 Complete the source -> candidate -> review -> normalized financial ->
  draft browser path, including corrections, stale evidence and rejected promotion.
- [x] M05-07 Produce a per-company evidence matrix with supported statements,
  dates, missing fields and model suitability. No unaudited row earns certification.

Gate: every scoped company has a usable reviewed input basis for its supported
model, or an explicit user-approved scope change. Lack of evidence is a blocker,
not permission to invent it. Human source/assumption review remains required.

## M06: consistent valuation and sensitivity

Owners: deterministic engines, saved-input contracts and valuation panels;
[Knull W4](../../Knull%28readme%29.md#8-w4-trustworthy-sensitivity-calculations).

- [x] M06-01 Repair sensitivity to reuse the canonical forecast/bridge behavior,
  preserve saved funding/terminal assumptions, and expose per-cell validity and
  method/version basis. Invalid convergence must not become zero terminal value.
- [x] M06-02 Verify sensitivity center equals the saved base with independent
  expected calculations. Cover missing versus zero, negative values, currency,
  funding overrides, terminal ROIC, shares and critical diagnostics.
- [x] M06-03 Audit supported FCFF, bank, distress, FCFE/DDM, scenario and reverse
  paths as separate method boundaries. Preserve finite-value/convergence gates,
  currency, input identity, optimistic versions and unchanged historical outputs.
- [ ] M06-04 Complete supported accounting/equity bridges and exact peer input
  provenance. Lease, D&A, options, dilution and cross-currency peer gaps require
  reviewed explicit inputs or an unavailable result, never proxy company facts.
- [x] M06-05 Verify narrative -> assumption -> saved calculation -> sensitivity ->
  reverse -> memo/export traceability. Expose formulas, dates, claim type and
  uncertainty. Keep unsaved edits and stored calculations distinct.
- [x] M06-06 Restrict experimental/legacy custom-options and unsupported specialized
  analyses in the normal product; verify compatibility routes separately if retained.
  No unvalidated method may appear as a certified number or trade instruction.
- [ ] M06-07 Run deterministic reference calculations, contract/ownership tests,
  PostgreSQL stale/concurrent-save checks and genuine-input browser walkthroughs.

Gate: supported valuation methods agree across services and panels for the same
saved basis; unsupported inputs/methods withhold results with useful diagnostics.

## M07: correct portfolio history and performance

Owners: portfolio valuation, transaction replay, snapshots, readiness and risk;
[Knull W3](../../Knull%28readme%29.md#7-w3-historical-positions-cash-and-portfolio-proof).

- [x] M07-01 Replay dated transactions/cash into historical positions instead of
  applying today's holdings to older dates. Cover purchases, sales, deposits,
  withdrawals, fees, partial history and zero holdings without retroactive guessing.
- [x] M07-02 Define corporate-action/dividend/adjusted-price handling for supported
  return modes. Keep the confirmed price-only AAPL/GOOGL assumptions explicit;
  do not silently relabel them as broker history or total return.
- [x] M07-03 Version replay provenance/coverage in new snapshots, keep legacy
  snapshots visibly unverified for replay, and enforce owner/as-of price and FX scope.
- [x] M07-04 Reconcile cash, position, price and FX contributions; TWR/MWR,
  dimensions, benchmark opportunity cost and residuals must agree with independent
  reference cases. Missing aligned history must reduce availability/confidence.
- [ ] M07-05 Verify marginal/component risk and current valuation gaps with complete
  dated series, freshness and reviewed model coverage. Never substitute an annualized
  return forecast for a valuation gap or emit portfolio trading instructions.
- [ ] M07-06 Finish the genuine-input readiness checklist and a real multi-currency
  manual smoke using sourced history and reviewed user activity. The existing assumed
  AAPL/GOOGL case is useful separate evidence, not a replacement for that proof.
- [x] M07-07 Exercise import preview/hash/atomic apply, duplicate/conflict handling,
  historical-date selection, corrections and browser states on disposable fixtures.

Gate: present and historical portfolio views reconcile to their dated inputs and
the genuine-input smoke passes without fixture data in the normal database.

## M08: connected daily research and review

Owners: Daily Brief, private-source comparison, analyst receipts, evidence/AI;
[Knull W1](../../Knull%28readme%29.md#5-w1-reviewed-private-evidence-in-daily-brief).

- [x] M08-01 Distinguish same/unknown/incompatible period, currency and economic
  scope in comparisons. Copied content and opposing arrows cannot certify a
  contradiction. Version semantics without rewriting historical analyst receipts.
- [x] M08-02 Include bounded owner-scoped private evidence and current analyst
  dispositions in manual and scheduled deterministic brief snapshots. Retain exact
  source/hash/receipt IDs, exclusions and freshness; isolate pending findings.
- [x] M08-03 Connect event -> evidence -> held company -> thesis review -> relevant
  valuation field -> next review action. Preserve source access and stale-review
  guards. A suggested field link never approves or changes its numeric assumption.
- [ ] M08-04 Build a reviewed AI evaluation set with unsupported claims, numeric
  errors, contradictory periods and source-text prompt injection. Report citation
  validity and interpretation quality separately; exact quotes do not prove meaning.
- [x] M08-05 Verify explicit consent, model/prompt/input/source provenance, owner
  access and review approval for AI. Failed/pending/rejected output stays outside
  trusted search/brief evidence. No provider call during an ordinary read.
- [x] M08-06 Exercise scan timeouts, late responses, edits/archive/restore, duplicate
  sources, stale review receipts, source comparison and complete review history.
- [x] M08-07 Run the complete morning-review browser workflow with public genuine
  source evidence, and a due scheduler cycle with safe scoped test inputs.

Gate: a user can explain what changed, which evidence supports it and what needs
review from one repeatable workflow, without implying universal news/AI coverage.

## M09: complete browser workflows and responsiveness

Owners: every active route in [route inventory](../09-route-inventory.md), domain UI,
transport/state helpers and query-budget tests.

- [x] M09-01 Audit every active route/control against actual endpoints and source
  status. Complete the intended path or visibly retire an unsupported surface.
  Do not create fake demo results to make a route appear complete.
- [x] M09-02 Verify loading, empty, unavailable, stale, partial, not-configured,
  Mock Data and success states where applicable, including expired/foreign sessions.
- [x] M09-03 Test save/retry/navigation/delayed-response races with behavior-based
  browser/component checks for the extracted forms. Preserve edits and saved confirmations.
- [x] M09-04 Inspect desktop/mobile, keyboard focus, labels, contrast, table overflow
  and charts with source/date/units. Cover adverse states as well as the populated page.
- [x] M09-05 Measure warm/cold route, query/row, browser-interaction and idle resource
  budgets on a recorded dataset/hardware profile. Set thresholds from the measured
  baseline, then repair the measured slowest paths without a cross-user data cache.
- [x] M09-06 Verify read-only previews, bounded exports/imports, source links and
  useful recovery paths. A build is not browser proof and a fast response is not
  a guarantee that the rendered workflow is responsive.
- [x] M09-07 Run the complete isolated production browser matrix and full source/
  type/contract suites after integration; record screenshot/trace and source identity.

Gate: all scoped workflows are usable and truthful across supported viewports,
with measured performance and no unresolved release-blocking regression.

## M10: proven local daily-driver release

Owners: coordinated release lane, current-state/handoff/ledger and operations runbook.

- [ ] M10-01 Freeze reviewed source/dependency identity and rerun clean builds,
  full source/type/contract suites, migrations, dependency scans and browser gates.
  Resolve blockers; do not delete failing tests or relabel failures as deferred.
- [ ] M10-02 Rehearse fresh install plus an existing populated backup upgrade in
  disposable runtimes; verify all pre-existing user-data and asset fingerprints.
- [ ] M10-03 Deploy the reviewed local release with a verified backup, confirm
  localhost-only bindings/auth, provider settings, explicit worker states and
  source/image identity. Keep a documented rollback path without destructive reset.
- [ ] M10-04 Record five business days of actual daily use: startup, source refresh,
  review, valuation, portfolio and briefing, including one restart and one provider
  outage/retry. Record missed runs truthfully. Do not invent future soak evidence.
- [ ] M10-05 Repeat encrypted off-device recovery, confirm retention/maintenance
  instructions and inspect disk growth, idle load and sanitized failure audit trails.
- [ ] M10-06 Reconcile the feature register and limitation ledger. Every v1 acceptance
  item is evidenced; every optional/deferred capability is clearly labeled. Replace
  the handoff with maintenance priorities, not an endless historical task list.
- [ ] M10-07 Obtain final user acceptance of the genuine daily workflow and the
  disclosed local/manual/provider boundaries. Close M10 only after this acceptance.

Gate: all earlier milestones remain valid, the user accepts the working local
release, and release/soak/recovery evidence is recorded. This is the end of v1;
future enhancements and public deployment belong to a separately scoped release.
