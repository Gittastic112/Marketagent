# Product Roadmap

**Prioritized:** 2026-08-24. Product evidence: see Current State.
Completion sequencing reconciled: 2026-11-07 against the supplied delivery report, current source and independent completion work.

**Completion requests:** use the [ten-milestone tracker](completion-tracker.md).
It defines ten acceptance gates for the remaining local release, not an estimate
of engineering hours or the amount of code already built. M01-M04 are accepted
at 40 acceptance points under the research/demo scope; M05 is the next unfinished gate. See the tracker for dated evidence.

October 17 explicitly scopes the first release to local research/demo on the
existing data. The [scope revision](completion-tracker.md#scope-revision-approved-october-17-2026)
defers Mac/off-device setup and excludes genuine portfolio validation from v1.
Remaining financial, model and AI review choices are delegated to Codex and
recorded in the [decision log](review-decisions.md). Each applied choice still
requires supporting evidence and current-record checks. No new local disposable
fixture datasets are authorized.

November 3 completes the approved historical research scenarios; November 4 adds
dated disclosure notes without changing their assumptions. [PR4](https://github.com/Gittastic112/Marketagent/pull/4)
is merged with five successful post-merge checks. The [delivery-report reconciliation](../archive/checkpoints/2026/delivery-report-reconciliation-2026-11-04.md)
maps its two named priorities below; it does not import the absent 45-ticket backlog.
Missing issuer claims and actual-use/final acceptance remain distinct from finished engineering checks.

## Planning Rule

Finish workflow integrity before adding more schema or isolated engines. A task
is complete only when backend behavior, frontend states, provenance, ownership,
tests, and documentation agree.

The detailed feature batch is [Knull](../../Knull%28readme%29.md): reviewed
brief context, financial-source coverage, portfolio history, sensitivity integrity
and recovery consistency. It defines five disjoint write scopes, phased tests,
external-input gates and shared-file escalation. The completion tracker sequences
these slices with foundation, architecture, security and release prerequisites.
Use its next incomplete milestone for percentage requests. Respect Knull ownership
if a parallel batch is explicitly launched; this plan does not launch one.

## Priority 1: Frontend and Backend Truth Parity (FOUNDATION DELIVERED, FOLLOW-UPS OPEN)

The earlier route and data-state gates passed, but this is not a blanket
completion claim. Saved-input preservation and focused Reverse DCF/Real
Options integrity repairs now have isolated regression evidence. Use [the handoff](../HANDOFF.md) for the next
concrete task and [the single ledger](../agent_capabilities_and_limitations.md)
for the current boundaries. The architecture refactor makes owners easier to
find; it does not certify every route or genuine-input workflow.

Audit every active frontend route against real API behavior.

Acceptance gates:

- Every panel identifies live, manual, partial, stale, mock, or not-configured data.
- Loading, empty, error, stale, partial, and permission states are intentional.
- Server and browser API access preserve auth and response metadata.
- No route invents values to compensate for a missing endpoint.
- Hardcoded methodology fallback values are replaced by approved versioned data
  or explicit user-custom/not-configured states.
- Representative desktop and mobile browser workflows pass.

## Priority 2: Broader Real-Issuer and India Provider Coverage (REFERENCE GATE PASSED, EXPANSION OPEN)

Preserve the dated AAPL/APSEZ certification and the historical receipts for the
11 removed securities. Do not restore them automatically. The current company
universe is empty. Broader issuer/layout validation needs an authorized company
and source scope; complete claim values cannot be inferred from source counts.

Acceptance gates:

- Existing AAPL/APSEZ certification remains green.
- At least one additional issuer/layout is reviewed, reconciled, promoted, and source-linked.
- Minority interests, cross-holdings, leases, currency, and diluted shares are explicit.
- India company identity, filing source, price source, and freshness are visible.
- The two-market certification harness remains portable and deterministic.
- Unsupported NSE/BSE automation remains visibly manual until implemented.

## Priority 3: Daily Evidence-to-Decision Loop (WORKFLOW VERIFIED, REVIEW OPEN)

Connect ingestion, evidence, alerts, thesis changes, valuation relevance,
portfolio exposure, and next actions into one repeatable workflow (The Morning Briefing).

Acceptance gates:

- A user can see what changed since the last review in an aggregated dashboard.
- Each important claim opens its source evidence.
- Potential thesis conflicts are visible with source, period and scope. Direction
  differences or an exact quote alone must not be labeled verified contradictions.
- Portfolio holdings affected by an event are identified.
- News tracking feature cross-references overnight ingestion (SEC, RSS, News) with the active portfolio. If relevant news is found, it suggests which specific variable might be affected in the DCF model.
- The daily brief distinguishes new, unresolved, stale, and reviewed items.
- Processing failures are visible in Data Health and summarized in the Daily Brief without raw provider error leakage.

Delivered: bounded source-linked event/alert aggregation, held-company impact,
review timestamps, exact-price market moves, inspection queues and opt-in
deterministic scheduling. A separate private paste/PDF inbox now offers explicit
AI triage, exact quotes and links to valuation fields. Source refresh has its own
SEC/FRED/price worker and draft-only review gate. October 13 verifies the connected
recorded-public morning workflow; interpretation review still gates the research/
demo workflow. Genuine portfolio validation belongs to a later scoped release.

Private-source search, reversible archiving and a bounded multi-source comparison
now support the inbox lifecycle. The comparison groups exact-passage-backed
suggestions by input and flags opposing directions without claiming a verified
contradiction. Persisted analyst dispositions now retain exact evidence receipts,
immutable history and stale-review guards. Quoted period/currency/scope checks
and bounded manual/scheduled private-brief snapshots are integrated. Semantic
interpretation quality remains a separate human-review gate.
Do not imply comprehensive overnight news coverage or automatic numerical forecast
edits. Reads stay deterministic; external AI requires an explicit disclosed action.
Use [Current State](../00-current-state.md) for dated browser/provider evidence,
not historical test counts embedded in planning text.

November 4 implementation closes the report's bounded briefing engineering items in the
[public coverage and provenance limits](../agent_capabilities_and_limitations.md#what-is-not-product-ready).
Delivered behavior, with dated validation in Current State:

- Counts eligible, included and excluded public events, failed runs and inspection
  actions for an explicit time window; exposes caps and exclusion reasons in the
  contract and UI. A warning-free calculation does not imply complete ingestion.
- Preserves linked-document provenance in dashboard and saved-brief callers.
  Fresh-session regressions and browser assertions cover source links and claim
  labels; manual events remain User Assumptions. Historical counts stay unknown.
- Keeps source linkage, source freshness and analyst verification distinct. Broader
  interpretation checks must retain exact evidence and review state; no automatic
  numerical forecast changes or claim of complete provider coverage. Manual refresh
  is deterministic; external AI stays behind separate explicit per-item actions.

## Priority 4: Portfolio Attribution and Opportunity Cost (AUTOMATED RUNTIME PASSED, REAL-INPUT SMOKE PENDING)

Move beyond current value and exposure totals to advanced portfolio tracking.

Acceptance gates:

- Performance separates price movement, cash flows, FX impact, and position changes.
- Attribution is available by holding, sector, geography, and user tags, providing detailed risk exposure breakdowns.
- The user can compare opportunity cost, marginal risk, and expected return across holdings.
- Stale or missing prices block false precision.
- No feature emits a buy/sell instruction.

Delivered: dated generated snapshots, historical FX, explicit benchmark
configuration, TWR/MWR, price/FX/position/flow attribution, dimension
attribution, residual diagnostics, benchmark opportunity cost, annualized
aligned-return covariance, marginal and component risk, and trust-gated DCF
valuation-gap comparisons. The DCF gap is labeled Estimate and is not presented
as an annualized forecast. A deterministic Mock Data fixture and browser workflow
now exercise two complete snapshots, a USD and EUR holding, 22 aligned prices,
dated FX, a configured benchmark, TWR/MWR, attribution, opportunity cost, risk
reconciliation, and two trust-gated Base DCF outputs. The user reported the
focused backend and browser Docker gate passing on 2026-08-23. An owner-scoped,
read-only readiness audit now checks the complete persisted input contract,
rejects Mock Data, displays actionable blockers and source IDs in the portfolio
detail page, and has a non-mutating CLI. Still open: populate genuine
source-labeled inputs, reach `ready`, and complete the manual smoke. The owned
portfolio page now removes the bulk-entry bottleneck with a strict price/FX CSV
template, non-writing server preview, portfolio/benchmark scope checks, explicit
provider/source/timestamp requirements, Mock Data rejection, exact-duplicate
skips, conflict blocking, preview-file SHA-256 enforcement, atomic apply, and
Processing Run audit links. It does not invent or independently verify facts and
does not create holdings, benchmark configuration, snapshots, or DCF outputs.

## Priority 5: Provider Health and Market Regime (COMPLETED FOUNDATION)

Keep provider state observable and regime calculations source-backed.

Acceptance gates:

- SEC, RSS, market data, FRED, filings, and AI show configured, last success,
  last failure, rate-limit, freshness, and coverage state.
- Market-regime inputs are source-backed and timestamped.
- The score exposes formula, drivers, blockers, warnings, and confidence.
- Mock regime values are removed or remain unmistakably labeled.

Delivered: persisted run classifications and freshness/coverage diagnostics;
bounded regime inputs with manual/provider provenance; source-aware confidence,
formula, blockers, warnings, and input evidence. FRED imports now produce real,
sanitized Processing Runs and preserve official series provenance. The stored
NFCI observation can be previewed and idempotently applied to the macro module
through a disclosed bounded Calculation with an exact observation-record link.
Stale evidence stays stale, and a provider declaration without a stored record
is a Source Summary rather than a Fact. Automated provider coverage for options,
liquidity, volume, and breadth is not implemented or implied.

## Priority 6: Source-Backed AI Research (REVIEW FOUNDATION DELIVERED, QUALITY OPEN)

Raise AI trust only after deterministic evidence and review paths are complete.

Acceptance gates:

- Generated claims cite stored source IDs and exact evidence where available.
- Citation validation and evaluation run before approval.
- Unsupported claims are blocked or visibly flagged.
- Prompt/model/version/privacy metadata is stored.
- Output remains analysis, not investment advice.

Delivered: source-marker coverage, exact stored-text validation, persistent
blocked/evaluation state, owner-scoped review, and approval gating. Reviewers can
now request bounded, deterministic exact-passage candidates from the declared
stored raw documents. Candidates include exact character offsets, numeric-aware
lexical coverage, confidence, source links, and limitations; choosing one only
fills the review draft and never validates or approves it. Evaluation v4 adds per-marker numeric-literal, multiple-period and instruction/inference cues.
Flagged claims require review notes before approval; changed citation evidence
resets approval while retaining its prior review receipt. Provider-generated
citation completeness and claim-level semantic entailment remain partial.
Stored-research search now unifies the primary evidence and research objects,
keeps shared narratives visibly interpretive, scopes private notes/sessions to
their owner, and indexes AI output only after successful execution, human
approval, and an unblocked review state. Search does not make an approved AI
interpretation a fact or prove semantic entailment.

The private research inbox now validates exact source quotes and constrains
suggestions to known valuation fields. It remains review-only; importance,
direction and interpretation are not certified by a matching quote. Public Apple
PDF workflow proof does not certify arbitrary reports or a complete AI research
evaluation corpus.

Current external AI actions already require feature-specific acknowledgement of
the shared disclosure version and retain per-output ownership/transmission audit.
The report's centralized-consent item is implemented as a persisted policy and
Settings interface, scoped in the [AI boundary](../agent_capabilities_and_limitations.md#ai-boundary).
Delivered behavior, retaining the existing per-action gates:

- Stores authenticated user, provider/action/data scopes and grant/refusal/revocation
  history; exposes current scopes and controls to that user, with stale-tab rejection.
- Checks current permissions immediately before each provider call. Denied,
  outdated or revoked permission sends no request. Revocation cannot recall a
  previous transmission or cancel an already dispatched request.
- Preserves disclosure, ownership, review gates and historical output audit.
  The additive migration grants nothing. New external outputs retain the exact
  permitting decision. Current policy covers ten Gemini actions; unsupported
  internal actions remain unavailable and actual Mock Data generation stays local.

## November 7 development sequence

The first three increments are implemented in the [current checkpoint](../archive/checkpoints/2026/product-development-2026-11-07.md).
They improve the existing workflows without creating companies or research activity.

| Increment | Delivered behavior or prerequisite |
|---|---|
| Financial evidence planning | Read-only three-year review tracks for operating companies, bank equity and equity cash flow. Missing disclosures, unit conflicts, duplicate scopes and source linkage lead to existing review actions. No completeness certificate or new financial values |
| Macro workbench | Real canonical calculations replace fixed compatibility coefficients; constant regressors stay unavailable, missing segment coefficients withhold full-company totals, and forms preserve explicit zeros and errors. Signed top-down duration remains distinct from source-convention coefficients |
| AI claim review | Bounded deterministic cues and required review rationale strengthen exact-citation review without provider calls or automatic approval |
| Next issuer/layout | Select a new company and dated official filings after the deliberate company reset; run source hashes, units, periods, scope and identity reconciliation before promotion. The existing harness remains available, but no new company is implied by this pass |
| India provider integration | Establish a documented official endpoint, intended-use rights, response examples, freshness and rate limits before an adapter. Require bounded transport, Processing Runs, fixtures and read-only preview before apply. Manual official-source intake remains supported |
| Peer comparison expansion | Obtain permitted peer data with currency/accounting/period definitions before FX normalization or calibrated scoring. Do not treat missing comparisons as zero or invent a score |
| Operating acceptance | Record actual use and failures. Agent tests do not create business-day usage, genuine transactions or off-device recovery evidence |

## Deferred

- Broker sync until an approved OAuth/token security design exists.
- Public deployment until the security threat model's release gates are met.
- Real-time trading feeds and expensive microstructure data.
- Social scraping without an official API and provenance model.
- Additional Damodaran workbook parsers without a consuming application workflow.

## Selection Rule

Choose the highest priority with an unmet acceptance gate. Do not use old
checkpoint numbering as a task queue. During an assigned batch, respect its
exclusive scopes before selecting additional work. Historical plans are available in
`../archive/plans/` only when implementation context is needed.
