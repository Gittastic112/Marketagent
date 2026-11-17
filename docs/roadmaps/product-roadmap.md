# Product roadmap

Priorities for the local research/demo release. Reconciled November 15, 2026.
[Current State](../current-state.md) owns evidence, the
[feature register](feature-register.md) owns capability status, and the
[limitation ledger](../limitations.md) owns unresolved boundaries.

M01-M04 retain 40 accepted gate points. M05 is next in the
[completion tracker](completion-tracker.md). These are acceptance gates, not an
engineering-effort percentage. Existing implementation does not supply missing
financial facts, actual-use days, or final acceptance.

The immediate programme is the returned code-review repair sequence below.
The [research workspace plan](research-workspace-plan.md) still owns target layouts,
navigation and P0-P7 specifications. P0/P1 and bounded P2-P5 slices are delivered;
the returned review identifies gaps in those implemented workflows. Repair their
trust boundaries before expanding features. This changes priority, not architecture
or historical acceptance. [Current State](../current-state.md) links dated evidence.

## Planning rule

Finish the connected review workflow before adding isolated engines or schema.
Completion requires backend behavior, frontend states, source/ownership metadata,
tests, and documentation to agree.

The user also requested essential-only storage. Apply the
[retention policy](../operations.md#essential-retention-policy): no routine database
dumps for documentation/UI work, no permanent rollback stacks, and explicit roles
for the small amount of recovery material retained. Do not confuse deleting build
waste with permission to destroy unique source evidence or live records.

Preserve the November 9 four-company research scope. The removed historical
universe must not be restored automatically. Further issuer intake needs an
explicit company/source scope. The October 17 research/demo revision defers
host/off-device work and excludes genuine portfolio validation from v1.

The [workstream design](../workstreams/plan.md) retains detailed technical slices.
Its ownership rules apply to an explicitly assigned parallel batch; the plan
does not dispatch agents or replace current status.

## Immediate delivery order

### Review repair sequence

The [single limitation ledger](../limitations.md#returned-code-review) owns current
status. The [intake receipt](../../data/reviews/code-review-intake-20261115.json)
maps all 39 findings to exact source references, evidence qualifications and
regression requirements. D1 is a deliberate behavior change; D2 and A4-7 overlap
known WS07/P6 scope. Do not count them as additional undisclosed failures.

Use the existing domain modules and compatibility boundaries. No new architecture,
provider, agent framework or parallel edit batch is needed. Each row is a repair
package, split into small commits: regression, narrow repair, relevant UI/contract
integration, then evidence. A package is not authorization to rewrite historical data.

| Package and owner | Outcome and finding IDs | Exit evidence |
|---|---|---|
| R0 · Operations | A4-1/A4-2: preflight the complete ordered Compose target and stop unsafe populated legacy migration paths before any destructive step | Fake-command tests prove file order, spaces and target selection; legacy-revision fixtures prove rejection before migration. A separately authorized PostgreSQL preservation drill is required before claiming upgrade/restore support |
| R1 · Research and security | A3-1/A1-F1: protect dependent event/source evidence and version source corrections. A3-6/A3-7: scope holdings filters and private run metadata to the owner | Authenticated two-owner tests cover direct/indirect deletes, metadata visibility, unique nonzero owned holdings and safe unreferenced deletion; unrelated records and source history remain unchanged |
| R2 · Financial evidence | A1-F2 through A1-F7: retain override origin and original values, exact periods, workbook bytes, filed dates, units and percentage-point semantics | Override/undo/accept/promotion round trips retain provenance; quarter/YTD columns remain held; hash-verified workbook reattachment and unit/percent boundary fixtures pass; existing facts are not silently reclassified |
| R3 · Valuation engines | A2-1/A2-2/A2-3/A2-8: validate complete growth paths, finite outputs and nonnegative claims; wire financial-sector guards; reconcile duration signs and WACC units/horizons | Malformed/overflow inputs cannot be preview-ready or saved; all model entry points enforce classification; macro sign tests follow one declared coefficient convention; valid explicit zeros survive |
| R4 · Portfolio calculations | A3-2/A3-3/A3-4/A3-5/A3-9: replay corrections chronologically, preserve snapshot currency, enforce quote/FX freshness, withhold unknown weights, align return methods | Buy/split/bonus correction and metadata-only edit cases pass; mixed-currency and stale/unknown-price cases cannot look complete; equal economic wealth reconciles under external cash flows without rewriting old snapshots |
| R5 · Source acquisition | A1-F8 through A1-F12: retry missing filing text, deduplicate within batches, continue stored PDF pages, backfill section comparisons, route history to the correct asset | Repeated attempts are idempotent under autoflush=False and PostgreSQL concurrency; partial failures retain progress; new PDF ranges preserve bytes and candidates; browser links reach the exact source/page |
| R6 · Valuation workflow | A2-4 through A2-7: preserve edits during saves, synchronize visible growth with reviewed values, acknowledge exact stale versions, export raw saved history separately from current interpretation | Delayed-response browser tests keep edits paused while a submitted save is pending; refreshed growth matches submitted values; concurrent newer events cannot be cleared; exports match stored values/warnings while read reconciliation remains available |
| R7 · Research workflow | A3-8/A3-10/A3-11/A4-3 plus D1/D2: complete private-source approval, fix thesis links and memo contracts, retain AI origin, record exact brief/thesis review decisions | End-to-end owner-scoped approval/receipt flow, real event links and memo generation; new events between capture/click remain pending; no-change/blocked thesis decisions retain evidence and reject foreign owners |
| R8 · Auth and workers | A4-4 through A4-8: align research timeouts, recover sign-in states, record AI attempts before calls, reconcile expired leases and constrain callbacks to the same origin | Browser recovery and callback tests; delayed/interrupted provider doubles plus worker restart tests show pending/unknown/failed outcomes, no silent duplicate sends, and one terminal run outcome |

The first ten repairs are installed and merged in PR 18. PR 19 installs the next ten:
A1-F6/F7, all four R3 findings and A3-2 through A3-5. The
[release checkpoint](../archive/checkpoints/2026/review-financial-integrity-release-2026-11-15.md)
records final checks, the requested Today order and preservation. The
[evidence/workflow batch](../../data/reviews/review-evidence-workflows-ten-sets-20261116.json) installs A3-9 and R5/R6 locally;
its browser checks pass and GitHub publication is deferred by the user. The
[remaining nine](../../data/reviews/review-research-recovery-nine-sets-20261116.json) install R7/R8 and D1/D2 with scoped verification.
Publication remains deferred; the limitation ledger owns residual work. R0 still blocks
populated legacy conversion or restore; original evidence and historical snapshots remain preserved.
Work sequentially unless an explicit parallel batch assigns exclusive files.

Before each package, recheck its pinned claim against the current code, inspect
callers/contracts and preserve local edits. Write behavior regressions first where
practical. Use the [runbook](../execution-runbook.md) for the selected environment.
SQLite/helper checks do not prove HTTP authorization, PostgreSQL locking/migrations
or browser behavior; run those layers when the package changes them. Do not deploy
a schema change until its data-preservation and recovery prerequisites pass.

Closure requires an exact repair commit, failed-before/passed-after evidence,
representative UI states where affected, and a ledger update with remaining limits.
Keep the intake receipt immutable as the review baseline; store only essential new
proof. No routine backup, second full report copy, persistent test stack or automatic
pruning is part of these repairs. Policy defaults and conditional owner decisions
are in [review decisions](review-decisions.md#returned-review-design-decisions).

After these gates, resume the [workspace specifications](research-workspace-plan.md#delivery-sequence):
selected dated evidence into an explicit draft proposal and initial-model preview,
then wider period support, P6 reliability and P7 actual use. Source gaps can remain
honestly unavailable; they do not justify guessed inputs or financial acceptance.

## Boundaries to preserve while delivering

### Frontend and backend truth

Preserve explicit missing/zero, loading, empty, unavailable, stale, partial,
unconfigured, and Mock Data states. Verify representative desktop/mobile behavior,
authenticated server/browser access, and provenance through saved-input,
retry, and stale-write workflows. A build or source-string test alone is not
browser evidence. New methodology defaults must be reviewed/versioned or remain
explicit user assumptions.

### Financial and source coverage

Review the selected companies' financials and complete supported valuation
bridges before expanding coverage. Retained AAPL/APSEZ reference certification
and removed-universe receipts remain historical, not current database inventory.

The next issuer/layout requires official sources, hashes, periods, units,
security/share scope, reconciliation, and explicit promotion. Minority interests,
cross-holdings, leases, currency, and dilution must stay visible.
India automation additionally requires a permitted official endpoint, documented
response/freshness/rate limits, bounded transport, Processing Runs, fixtures,
and non-writing preview. Unsupported exchange automation remains manual.

### Daily evidence-to-decision loop

Connect dashboard changes to exact sources, thesis review, valuation relevance,
and portfolio exposure. Stored-public coverage counts, private research intake,
search, reversible archiving, comparison receipts, and deterministic scheduling
are implemented.

Next acceptance depends on repeatable use and interpretation quality. Coverage
must disclose its window, caps, exclusions, failures, and review state. Exact
quotes or differing directions do not prove economic contradiction. No claim of
comprehensive overnight news coverage or automatic numerical forecast edits.

### Portfolio attribution and research context

Preserve dated activity replay, FX, TWR/MWR, price/flow/position attribution,
benchmark comparison, risk alignment, and residual diagnostics.
Stale/missing prices and provisional histories must prevent false precision.
DCF gaps are Estimates, not annualized forecasts or trading instructions.

The existing example workflow can be checked against its stated inputs.
Genuine activity and multi-currency proof require a later scope with real
records. CSV preview/apply must retain exact hashes, ownership, source metadata,
duplicate handling, atomic writes, and Processing Runs.

### Provider health and market regime

Keep configuration, attempts, failures, freshness, source coverage, formula,
drivers, and confidence observable. Persisted FRED NFCI provides one
exact-record-linked macro calculation; unsupported options/liquidity/volume/
breadth feeds remain manual. A successful connection is not complete source coverage.

### Source-backed AI research

Retain exact citations, provenance, bounded output contracts, explicit disclosure,
and current owner/provider/action consent. Permission history and each output's
permitting decision are persisted. Revocation blocks future sends but cannot
recall data already transmitted.

Broaden evaluation using independently reviewed sources and known failure cases.
Numeric/period/instruction cues are review aids, not semantic truth.
Interpretation approval must not silently change financial facts or assumptions.
The [AI boundary](../limitations.md#ai-boundary) owns the exact limitations.

## Source and expansion prerequisites

| Work | Entry requirement |
|---|---|
| Financial/model review | Supported missing disclosures and explicit assumptions within the selected scope |
| Additional issuer/layout | Selected company, dated official reports, reproducible reference checks |
| Official India provider | Permitted endpoint and intended-use rights before adapter implementation |
| Peer comparison expansion | Permitted peer data with currency, accounting, and period definitions before normalization/scoring |
| Operating acceptance | Actual research use, failure/retry observations, and final acceptance |

The delivered financial review planner, explicit-input macro calculations, and
bounded AI claim-review cues support these steps. They do not close their evidence
requirements. Keep cumulative acceptance in the existing gate order while following
the implementation packages above. Do not expand scope to fill an empty screen.

## Deferred

Broker integration, public hosting, real-time trading feeds, unapproved social
scraping, and new workbook parsers without a consuming workflow require separate
scope and prerequisites. Keep their status explicit.
