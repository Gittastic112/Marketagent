> Historical design, prepared October 5, 2026; archived November 11. Source
> observations and assignments below describe that date. Use the current
> [workstream index](../../workstreams/plan.md) and [acceptance tracker](../../roadmaps/completion-tracker.md).

# Five-workstream design and ownership plan

Prepared October 5, 2026. Historical design reference; implementation and acceptance
status live in the [completion tracker](../../roadmaps/completion-tracker.md).
The source observations below describe the planning date, not current defects.

October 10 routing: user requests such as "finish 10%" use the
[completion tracker](../../roadmaps/completion-tracker.md). It maps W5/W2/W4/W3/W1
to M03/M05/M06/M07/M08 and adds the other local-release gates. This document
retains the detailed workstream designs and ownership rules; it launches no agents.

This is the detailed design for the October five-workstream batch. The
[product roadmap](../../roadmaps/product-roadmap.md) owns long-term priorities;
this file owns assignment, sequencing and completion for this batch. The
[limitation ledger](../../limitations.md) remains the only
product-gap inventory. Finishing these five streams does not finish every
roadmap item or authorize a public release.

## 1. What the batch should deliver

| Agent | Workstream | User-visible outcome | Independent completion boundary |
|---|---|---|---|
| W1 | Reviewed evidence in Daily Brief | A scheduled brief includes dated private research, exact evidence and current analyst dispositions; incompatible periods/scopes are not counted as corroboration | Existing brief/source interfaces and stored receipts; no valuation or portfolio writes |
| W2 | Reviewed financial-source coverage | More US/India financial histories survive extraction, review, reconciliation and normalization, with explicit security/share/unit scope | Financial-source pipeline and separate certification data; no valuation engine or live portfolio dependence |
| W3 | Historical portfolio accuracy | An as-of snapshot uses positions and cash valid on that date, and incomplete history cannot look complete | Transaction replay, snapshot/performance consumers and readiness; existing persisted valuation outputs only |
| W4 | Sensitivity calculation integrity | A sensitivity cell preserves the intended saved assumptions, explains its basis and withholds invalid values | FCFF sensitivity generation and its own panel; no source ingestion or portfolio changes |
| W5 | Consistent backup and recovery | A backup and its manifest describe the same database snapshot, cover both document stores, and pass an isolated restore drill | Backup/restore tools and fixtures; no application-schema or provider changes |

Why these five: they close identified workflow/integrity gaps using existing
interfaces. Dividing the work into generic backend/frontend/testing agents would
force daily coordination on the same features. Each agent here owns a complete
slice, including its tests and UI where needed.

## 2. Evidence and limits of this plan

Source inspection on October 5 found:

- `MorningBriefingEngine` aggregates events, alerts, holdings and prices. Private
  comparison/review services exist separately. The brief response contract still
  resides in the legacy schema facade, which W1 alone may edit for brief extraction.
- Financial certification resolves company selectors and source hashes and checks
  reviewed/promoted evidence. Draft SEC inputs explicitly warn that annual issuer
  shares do not establish current class-specific shares.
- `calculate_portfolio_valuation` filters prices by target date but reads current
  positive holding quantities. `record_daily_snapshot` calls that path. Historical
  replay needs regression proof before existing snapshots can be trusted broadly.
- `_calc_value_for_overrides` duplicates forecast math, recomputes funding rates,
  resets terminal ROIC for some shocks and substitutes zero terminal value when
  growth is not below the discount rate. The panel does not explain cell validity.
- `backup_local.sh` dumps the database before separately querying counts and asset
  totals. Concurrent writes can separate those observations. Its manifest summarizes
  `document_assets`, while private PDFs also live in `brief_sources.pdf_bytes`.
- Browser and restore runners have fixed Compose project names. Changing only
  ports does not prevent one runner from removing another runner's containers.

These are code observations and planning decisions, not newly executed product
tests. September 30 product evidence stays dated in
[Current State](../../current-state.md). The
[documentation audit](../checkpoints/2026/documentation-and-parallel-plan-2026-10-05.md)
records this session's validation and environment restrictions.

## 3. Before the five agents start

The coordinator completes this preparation once. It is a launch/integration duty,
not a sixth feature workstream.

1. Obtain a working Git/Python/Node/Docker toolchain. Inspect the real Git status,
   active agents, port bindings and source migration chain. This documentation
   session could not verify Git status or the running database. Do not interpret
   missing checks as a clean baseline.
2. Preserve the dirty checkout and untracked work. Establish one reviewed baseline
   containing the intended current source plus this plan. Record its commit ID.
   A worktree from an old HEAD does not include current uncommitted improvements.
   Use an intentional snapshot/commit or reviewed patch transfer; never reset,
   clean, broadly stage unknown files, copy secrets or assume an old branch is current.
3. Prefer five separate worktrees on `codex/knull-w1-brief`,
   `codex/knull-w2-financials`, `codex/knull-w3-portfolio`,
   `codex/knull-w4-sensitivity`, and `codex/knull-w5-recovery`, all from that baseline.
   Inspect/reuse suitable managed worktrees before creating more. Do not launch
   development agents as an incidental effect of reading this plan.
4. Run the ownership guard, the existing baseline suites and schema/API compatibility
   checks. Record pre-existing failures and stop affected work for direction.
   Agree on the existing request/response snapshots each agent must preserve.
5. Give every agent its own disposable database, test fixtures, output directory
   and new-test namespace from the manifest. No agent may populate the normal
   database to prove completion. W2 evidence and W3 inputs must be independent.
6. Reserve the shared browser/release/restore test lanes with one coordinator.
   Current fixed-project runners run one at a time, including across worktrees.
   Focused tests and code edits may run concurrently. Never let cleanup target a
   second agent's stack. Build common test images once before parallel testing;
   do not concurrently replace shared image tags.

Five editing agents can run simultaneously on a host that supports five workers.
This session exposes only three child-agent slots, so launching all five here
would require a different supported capacity or two waves. The plan does not
claim agents have been started.

## 4. Exclusive ownership and frozen contracts

The [ownership manifest](../../workstreams/ownership.tsv) is the write allowlist.
It contains exact files and reserved new directories, not broad backend/frontend
ownership. A file has exactly one owner. Read access to another domain does not
grant edit ownership. New paths in the manifest are reservations, not claims that
the files already exist.

The [ownership checker](../../../scripts/check_workstream_ownership.sh) rejects duplicate
or nested reservations, another owner's changed files, unsafe relative paths and
unassigned files. Its [regression checks](../../../scripts/test_workstream_ownership.sh)
exercise those failures. Run it before coding, on every proposed commit and at
handoff. The [runbook](../../execution-runbook.md#parallel-workstream-checks)
owns commands, including how to collect changed/untracked paths.

**Frozen for all five:** ORM models, migrations, route registration/security
inventory, shared response/transport/auth helpers, global styles, navigation,
server-action collection, shared fixtures/conftest, package manifests/lockfiles,
Compose/CI configuration, normal data, knowledge-base originals, this plan, the
manifest, and central documentation. Any file not allocated is frozen too.

| Boundary | Permitted change | Required compatibility |
|---|---|---|
| W1 brief payload | Add optional versioned private-research context; extract brief-only classes to a narrow schema module | Existing HTTP paths, envelope and old payload reads remain valid; legacy imports re-export identical classes. No other facade domain changes |
| W2 financial pipeline | Repair extraction, normalization and scope diagnostics using existing models/contracts | Preserve candidate review/promotion rules, historical evidence and source adapters' public call shapes. No identity-model migration |
| W3 portfolio payload | Add optional replay provenance/coverage to snapshot/readiness outputs | Current positions and old snapshot reads still work. Legacy snapshots remain visibly unverified for replay. No dependency on a new DCF calculation |
| W4 sensitivity JSON | Add versioned method/validity metadata within existing JSON columns; finite numbers or unavailable cells | Existing numeric grids remain readable with a legacy-basis warning. Existing calculation entry points, output identity and saved-version behavior remain intact |
| W5 backup format | Version the manifest and strengthen verification | Read v1 backups explicitly with their evidence limits; never silently bless them as v2. No schema, credential or deployment change |

Avoid changing a public behavior simply because its type signature is unchanged.
Each stream tests its boundary against the common baseline and does not import
another stream's new helper, fixtures, source data, branch or output artifact.
Broader full-suite tests may read shared modules; editing those tests remains
restricted to their owner or the coordinator after parallel work ends.

### When a boundary is insufficient

1. The requesting agent records the exact path, needed behavior, smallest proposed
   contract change, caller list and failing test in its own evidence directory.
2. Continue independent work. Do not edit the shared file, add a duplicate adapter
   elsewhere, cherry-pick another agent's work or quietly broaden the manifest.
3. The coordinator either rejects/defer the dependency, or stops affected owners,
   assigns the shared change to one owner, and integrates a compatibility-preserving
   prerequisite separately. Rebase affected worktrees to the same new baseline,
   rerun boundary tests and update ownership before resuming.
4. If the change needs a migration or a new route, serialize that design and
   integration. Check migration head, recovery and route-auth contracts once.
   Never give five agents permission to edit migration head/readiness independently.

This is also the mechanism for semantic overlap without a file conflict. No
automatic merge resolution can establish financial or evidence compatibility.

## 5. W1: reviewed private evidence in Daily Brief

**Read first:** briefing/comparison rows in the [code map](../../code-map.md),
[market-intelligence workflow](../../skills/market-intelligence/market-intelligence-workflow.md),
[security workflow](../../skills/security/security-review.md), brief schemas,
`morning_briefing_engine.py`, `brief_source_triage.py`, `brief_comparison_reviews.py`,
`daily_brief_schedule.py`, existing brief endpoints and their tests.

**Owns:** W1 entries in the manifest. The legacy schema facade is allocated only
to this agent; the permitted edit is extraction/re-export of brief contracts.
Review models, source intake and worker entrypoints remain read-only.

**Commit-sized phases:**

1. **Characterize and freeze.** Add regressions for current payload/history reads,
   source/receipt owner scope, duplicate content and stale receipt hashes. Specify
   optional context fields and an old-payload reader before changing generation.
2. **Make comparisons honest.** Distinguish unknown, same and incompatible
   reporting periods, currencies and economic scope using explicit stored evidence.
   Missing attributes stay unknown. Distinguish source findings, exact-quote
   identity and analyst judgment. Do not infer semantic contradictions from arrows.
   Version new comparison semantics so previous receipts cannot appear current
   under a different evidence grouping. Preserve immutable receipt/history reads.
3. **Integrate deterministic snapshots.** Add bounded owned research context to
   both scheduled and existing manual deterministic generation. Retain source IDs,
   exact evidence/hash, receipt ID/version, generation/as-of time, claim type,
   exclusions and freshness. Reviewed dispositions remain User Assumptions.
   Pending findings may appear only in a clearly separate review queue; rejected,
   archived, copied, mock or stale material must not become fresh corroboration.
4. **Render and navigate.** Extend the existing brief panel with counts, source and
   receipt links, reviewed/unresolved/stale/unavailable states and an explicit
   as-generated label. A later source/archive/receipt change must not rewrite the
   saved brief or make historical context look current. Opening the source shows
   its current state separately. Empty research context leaves normal briefs usable.
5. **Verify and hand off.** Exercise owner isolation, old JSON, stale reviews,
   copied sources, missing scope, incompatible periods and partial coverage. Test
   the due scheduler cycle, owner/date reuse and no external AI on scheduled paths.
   Run desktop/mobile brief-to-source-to-receipt navigation in the reserved lane.

**Done when:** both generation paths retain traceable context; old briefs still
open; another owner's text never appears; stale or incompatible evidence never
counts as current corroboration; no source approval or saved valuation value
changes; the bounded query behavior is measured and tested.

**Verification:** owned brief/triage/review tests; existing schedule/API tests as
read-only regressions; new W1 tests; frontend tests/typecheck; isolated brief
browser workflow. External AI is unnecessary for this gate.

**Not part of W1:** new ingestion providers, full semantic-entailment certification,
automatic thesis resolution, numerical DCF updates, portfolio replay or source
approval. If the existing JSON cannot represent a required receipt safely, use
the shared-change protocol before introducing persistence.

## 6. W2: reviewed US/India financial-source coverage

**Read first:** [ingestion reference](../../data-sources.md),
[financial extraction workflow](../../skills/data-ingestion/financial-statement-extraction.md),
`financial_history_certification.py`, `accounting_normalization.py`,
`valuation_source_inputs.py`, candidate review UI and
[existing reference manifest](../../../data/certification/aapl-apsez-reference-manifest.json).

**Owns:** W2 entries. The existing AAPL/APSEZ manifest and shared originals are
read-only. New source manifests/excerpts belong under the reserved W2 data tree;
deterministic synthetic tests stay labeled Mock Data in W2 fixtures.

**Commit-sized phases:**

1. **Coverage contract.** Preserve the dated ten-company selection in the ledger;
   do not recalculate market-cap rankings as a side effect. Inventory each selected
   issuer/security, reporting currency, period, share class, source locator,
   debt scope, normalized state and unresolved evidence. Choose at least one
   additional US issuer and one additional Indian issuer/layout for full proof.
   Identify bank-specific gaps rather than forcing banks through industrial ratios.
2. **Reproduce evidence failures.** Add failing unit/period/scale/share/debt tests
   before fixes. Cover annual versus TTM, standalone versus consolidated, restated
   versus original periods, issuer versus listed share class, missing versus zero,
   duplicated tags and currency mismatch. A locator without explicit units fails.
3. **Repair only supported extraction/normalization paths.** Preserve original
   bytes, append candidates, maintain hashes and use existing review/promotion
   transactions. Reconcile statements and retain debt-component scope. Rejected
   candidates cannot return through autofill; refreshed candidates cannot overwrite
   reviewed values. Do not synthesize complete debt from an incomplete component.
4. **Complete review usability.** Show source excerpt/locator, units, currency,
   period, scale and share-scope warnings at the existing review surface. Verify
   stale edits, empty/error/partial states, rejection and normalization conflict
   recovery. Preserve the boundary between a reviewed financial fact and a draft
   valuation suggestion; forecast assumptions remain separate.
5. **Prove broader histories.** Re-run AAPL/APSEZ certification unchanged, then
   certify the two additional histories with independent reference values and
   reviewed official evidence. Record source/hash, expected versus extracted
   values, normalized outputs and reconciliations. Produce a coverage matrix for
   all ten selected companies; uncovered histories remain pending with named inputs.

**Done when:** the original two-market gate and two additional real-source
histories pass; units/periods/share and debt scope are explicit; repeat intake is
duplicate-safe; reviewed records are preserved; review and normalized provenance
can be followed end to end; all ten companies have an honest coverage entry.

**Verification:** financial extraction/PDF/XBRL/identity/certification/source-input
tests, the existing extraction-evaluation gate as a read-only regression,
frontend evidence tests and an isolated review/promotion browser workflow.

**External input gate:** source access and actual human review cannot be fabricated.
Use existing lawful sources and the manual official-report route where needed.
If a chosen issuer's evidence is unavailable, finish parser/review work but keep
the real-source acceptance gate open and identify the exact missing report or
review. Do not claim that automated tests have approved the normal review queue.

**Not part of W2:** automated NSE/BSE discovery, identity-model migrations,
benchmark mapping approval, forecasts, normal-database bulk promotion, or W3's
genuine portfolio inputs. Further issuer/security schema separation is a later
coordinated design, not a hidden prerequisite for this stream.

## 7. W3: historical positions, cash and portfolio proof

**Read first:** portfolio rows in the [code map](../../code-map.md), transaction and
holding models, `portfolio_valuation.py`, `portfolio_holdings.py`,
`portfolio_analytics.py`, `portfolio_cash_flows.py`,
`portfolio_real_input_readiness.py`, snapshot/performance tests and the read-only
readiness CLI. Read W4's frozen boundary, not its future implementation.

**Owns:** W3 entries. Models, FX/provider services, risk service, DCF engines and
shared seeding scripts remain read-only. Use already persisted DCF output fixtures
when testing valuation coverage so W4 is not a dependency.

**Commit-sized phases:**

1. **Expose look-ahead.** Add fixtures with buys, partial/full sales, a later buy,
   deposits, withdrawals, dividends and fees on both sides of the requested date.
   Prove that a position sold today still existed earlier, and that future trades,
   current cash balances and future prices cannot leak into a historical snapshot.
2. **Define replay completeness.** Establish deterministic transaction ordering
   and existing cash-flow conventions. Resolve starting positions/cash explicitly.
   A manually entered current holding or unexplained opening balance is not proof
   of historical ownership. Missing history, unsupported corporate actions,
   oversells and ambiguous security identity produce blockers/partial results.
   Do not invent splits, dividends, opening trades or FX.
3. **Implement bounded as-of replay.** Use transaction dates and existing sourced
   price/FX lookups; preserve Decimal money/quantity handling and owner scoping.
   Keep current-position reads compatible. Add replay date, method and input
   record IDs/coverage to new snapshots using existing JSON, and mark old snapshots
   as legacy where the basis cannot be proven. No bulk historical rewrite.
4. **Propagate trust.** Make performance/attribution/readiness and the selected
   portfolio view expose incomplete replay. Preserve the strict multi-currency
   readiness contract. The known USD-only AAPL/GOOGL assumed case may pass its
   narrow regression while the broader FX/benchmark/trusted-DCF gate stays blocked.
5. **Prove calculations and workflow.** Reconcile positions, cash, external flows,
   snapshot totals, return intervals and attribution residuals against independent
   small calculations. Test duplicate/reordered/edited transactions, foreign owners,
   future prices, unavailable FX and unsupported actions. Run isolated snapshot and
   performance UI checks, then the read-only genuine-input preflight if authorized.

**Done when:** historical calculations use dated positions/cash; known incomplete
history cannot be labeled complete; current behavior and old snapshot reads are
compatible; no normal records are rewritten; independent calculation and browser
evidence passes. **Genuine-input completion is a separate gate** requiring actual
reviewed price, activity, FX, benchmark and trusted DCF evidence.

**Verification:** owned portfolio tests plus existing cash/FX, TWR/MWR,
performance/API and private-context tests as read-only regressions; new W3 replay
tests; frontend tests/typecheck; isolated portfolio runtime workflow. Record exact
input IDs and blocker codes for the genuine-input audit, never copied credentials.

**Not part of W3:** broker integration, arbitrary corporate-action automation,
new valuation assumptions, benchmark/provider intake or inventing foreign holdings
to pass a multi-currency check. Missing genuine inputs leave that gate open without
blocking W1/W2/W4/W5.

## 8. W4: trustworthy sensitivity calculations

**Read first:** [valuation workflow](../../skills/valuation/valuation-workflow.md),
the sensitivity limitation in the ledger, forecast/terminal/bridge functions in
`dcf.py`, `diagnostics_engine.py`, pure output contracts and
`sensitivity-tables-panel.tsx`. Inspect all callers before changing helper behavior.

**Owns:** W4 entries. No saved-input schema, model, scenario/reverse/options engine,
advanced workspace, normal saved output or source data edits.

**Commit-sized phases:**

1. **Define the method and reproduce errors.** Specify which variables each axis
   changes and which saved assumptions stay fixed. Test explicit zeros, missing
   values, nonfinite inputs, near-singular terminal growth, invalid shares and
   sales-to-capital, and a saved cost of equity that differs from a CAPM estimate.
   The unshocked case must match an independent reference for the documented method.
2. **Unify only the sensitivity calculation path.** Reuse existing deterministic
   forecast/terminal/bridge logic where safe. Preserve public call shapes and core
   output behavior. Do not silently reset saved terminal ROIC or unrelated rates
   when an axis changes financing. If a financing table intentionally recalculates
   rates, label that method and show why its center differs from the saved value.
3. **Represent unavailable cells.** Never substitute an economically valid zero
   for invalid/nonconvergent math. Store bounded per-cell reasons and methodology
   version in existing JSON. Preserve true zero and negative values when valid.
   Restrict this to supported FCFF sensitivity; bank/distressed unsupported grids
   remain unavailable. Historical saved tables are read, not recalculated in place.
4. **Fix the panel.** Render zero, negative, unavailable and malformed legacy cells
   correctly. Show units, saved-input/as-of basis and method limits. Describe colors
   as a comparison against the saved assumed price; remove unconditional claims
   that color establishes undervaluation/overvaluation. Keep finance math backend-owned.
5. **Verify compatibility.** Add independent numeric expectations and cell-validity
   tests; protect main DCF, zero/default, scenario, reverse, specialized and saved
   output tests as read-only regressions. Verify old/new grids, currency, stale
   basis and mobile table behavior in the reserved browser lane.

**Done when:** documented shocks preserve every unshocked input; valid center
behavior is explained and tested; invalid cells cannot look like precise prices;
versioned results and legacy warnings are visible; main engine behavior and saved
history remain compatible.

**Verification:** owned DCF tests and new W4 tests, schema/import boundaries,
read-only adjacent valuation suites, frontend sensitivity tests/typecheck, isolated
sensitivity UI proof with Mock Data. Financial quality claims require reviewed
inputs; a green test never certifies a company valuation.

**Not part of W4:** recalculating stored portfolios/models, new forecasts, new
industry priors, probabilistic interpretations, trading recommendations or broader
scenario/reverse refactoring. Request a shared prerequisite if a schema redesign
becomes necessary rather than changing models during parallel work.

## 9. W5: consistent backup and recoverable evidence

**Read first:** [operations workflow](../../skills/operations/local-operations.md),
backup/restore sections of the [runbook](../../execution-runbook.md),
`backup_local.sh`, `restore_local.sh`, `drill_backup_restore.sh`,
`restore_drill_fixture.py` and `test_backup_workflow.py`.

**Owns:** W5 entries only. The normal runtime, secrets, database roles, container
configuration and other agents' test runners are outside scope.

**Commit-sized phases:**

1. **Characterize failure cases.** Extend fake-Docker tests for writes during
   manifest collection, interrupted dumps, invalid checksums, count mismatch,
   equal-count/different-content corruption, incomplete asset inventories and
   failed restore verification. Preserve existing worker stop/resume regressions.
2. **Choose one consistent observation method.** Prefer deriving verification
   data from the completed dump restored to an isolated scratch database, or use
   one proven PostgreSQL snapshot for both dump and manifest. Document the chosen
   guarantee. Do not compare a consistent dump to later mutable live counts and
   call that consistency. Normal writer shutdown needs an explicit maintenance
   window and is not required for independent code/test completion.
3. **Version the recovery evidence.** Include table inventory and deterministic
   content verification where supportable; cover `document_assets.content` and
   `brief_sources.pdf_bytes` with counts, bytes and hashes. Validate manifest
   paths, format and checksums before any replacement. Retain restrictive local
   permissions and explicit handling of older manifests.
4. **Make the drill safe and complete.** Use disposable Mock Data with private PDF,
   findings, analyst receipts, portfolio and source records. Verify original bytes
   and relationships after restore/migration. Reject non-disposable targets in
   drill code; make cleanup target only its allocated project. Demonstrate failure
   leaves writers stopped when verification fails and does not enable disabled workers.
5. **Record operational recovery requirements.** Produce a tested operator procedure
   and exact verification receipt. Specify encrypted off-device copy/key-recovery
   requirements without choosing an account, moving private data or inventing a
   completed off-device drill. Measure local restore duration and scope, not an
   unsupported recovery-time guarantee.

**Done when:** dump and manifest share a provable basis; both document stores and
their relationships survive a disposable restore; corruption and incomplete
manifests fail safely; prior worker states and v1 evidence limits remain explicit;
the real database and backups are untouched by tests.

**Verification:** expanded backup unit tests, shell syntax checks and one serialized
disposable PostgreSQL drill. Do not use another agent's database as the scratch
target or run destructive normal restore as a test.

**External operator gate:** encrypted off-device recovery is incomplete until the
user supplies the destination/key custody and authorizes private-data transfer.
Complete the tools and a concrete procedure first. Production replacement needs
exact-target and data-loss authorization. These gates do not block the other streams.

## 10. Common delivery and integration checklist

Each agent creates its receipt under `docs/workstreams/evidence/<owner>/receipt.md`
and keeps pending shared-change requests there. Central docs remain frozen during
parallel editing. The receipt must contain:

- Baseline commit, final commits, owned changed paths and ownership-check result.
- Before/after behavior and compatibility decisions, including new JSON versions.
- Commands/results, dates, environment and fixture provenance; passing, failing,
  blocked and not-run checks listed separately.
- Actual browser routes/assertions and cleanup evidence where applicable.
- Remaining input/operator gates, exact next action and proposed central-doc changes.
- Links to evidence or log locations without private document text or secrets.

The coordinator then:

1. Checks each diff against the manifest, including new/deleted/renamed files.
   Rejects shared-file edits or hidden dependence on another branch. Verifies the
   baseline and adds only that stream's reviewed files.
2. Integrates one completed stream at a time in any order. No stream is allowed to
   require another stream's unfinished commit. Re-run focused boundary checks after
   each merge. A conflict triggers review; do not resolve it by discarding behavior.
3. Runs full backend/frontend/type/schema/API checks on the combined source, then
   production builds and serialized browser/recovery gates. Baseline tests are
   separate from genuine-source, genuine-portfolio and operator recovery evidence.
4. Updates only the affected current references: Current State, feature register,
   ledger, code map, architecture/schema/source docs if their boundaries changed,
   roadmap, skills and handoff. Archives detailed receipts and runs doc/skill/secret
   checks. Do not copy the same completion narrative into every document.
5. Marks each stream **implementation verified**, **evidence/operator gate pending**,
   or **complete** with its remaining gate. The batch is complete only when all
   required acceptance gates pass; missing inputs are never counted as completion.
   A normal-runtime rollout is a separate coordinated action within user authority.

## 11. What remains after this batch

Use the roadmap and ledger for selection. This batch deliberately does not close
official India discovery, full issuer/security schema separation, licensed peers,
all provider coverage, AI semantic-quality certification, historical model
recalculation, broker integration or public deployment. It also does not promise
that all ten companies or a genuine multi-currency portfolio have reviewed inputs.
Those require further evidence or designs, not larger completion claims here.

Do not begin another batch until the five receipts and remaining gates have been
reconciled. No calendar estimate is asserted before executable baselines and the
source/operator inputs are available.
