Historical snapshot, not current instructions. Original relative links are preserved.

# Current State

**Audited:** 2026-09-09

**Scope:** local-first, single-user investment research

**Code wins:** verify routes, models, migrations, and tests before relying on this summary.

## Product Position

The repository is a broad, functional research, valuation, and portfolio
performance platform, not a finished daily-driver product. No new completion
percentage was calculated for this release. Valuation, evidence, portfolio
performance, provider diagnostics, and local authentication are stronger than
official India coverage, autonomous daily workflows, and public-deployment
security.

## Latest Recorded Validation Baseline

| Check | Current result |
|---|---|
| Backend tests | 845 passed with four upstream `openpyxl` deprecation warnings |
| Frontend tests | All 191 passed |
| TypeScript | Passes |
| Production build | Next.js 16.2.11 Docker production build passed; the running frontend bundle was refreshed and frontend auth readiness and container health pass |
| Database migration | Source and normal runtime are at `o6o6o6o6o6o6` |
| Knowledge-base tests | 4 passed |
| Knowledge-base audit | 61 canonical files, 61 catalog rows, 38 ledger rows, 0 pending |
| Damodaran application coverage | 12 supported, 14 partial, 9 unsupported |
| Damodaran typed data | 18 active sources, 2,625 rows, 18 complete active provenance records |

The 538-backend/98-frontend fully green reconciliation baseline remains the last
recorded complete release baseline. The table above carries forward newer,
scope-specific evidence without claiming a new fully green release baseline.
Local API health, authentication readiness, documentation links, and secret
scanning also passed in their recorded gates. The worktree remains substantially
uncommitted; do not assume every untracked path is disposable.

The migration history was deliberately replaced after the user confirmed all
databases created from the previous chain were disposable. Databases stamped
with the deleted `20260524_*` or `20260530_*` revisions must be recreated.

## Documentation State

The active documentation checker covers 62 Markdown files and 319 local links,
including the project skill library. One roadmap and one feature register drive future work.
Dated checkpoints, prior handoffs, old assessments, and superseded plans are
categorized under `archive/`. `scripts/check_docs.py` validates active Markdown
links and rejects retired active-plan paths.

Docker runtime checks, the full backend suite, frontend tests, TypeScript, and
the production build were all available and green during reconciliation.

The valuation UI now persists industry mixes and DCF currency choices through
the authenticated proxy, supports one explicit acknowledgement for valid
autofill defaults, and exposes compact model readiness instead of loading every
projection into the model list. Model detail uses an owner-scoped direct read;
metadata edits, save-and-calculate, reverse DCF, memo loading, and real-option
actions expose failures. Assumption saves are atomic, preserve payout,
cost-of-capital, equity-bridge, story, and currency fields, and identify inputs
as User Assumptions and outputs as Calculations or Estimates. Invalid percentage
units, capital weights, currency codes, and unexplained currency mismatches are
rejected on new writes. Historical invalid, stale, or critically warned models
remain readable but their estimate and comparison outputs are blocked as
unreliable until corrected.

Valuation benchmark inputs are now seeded from the supplied January 2026
workbooks through hash-versioned contracts. Risk-free rates, ERP, beta, cost of
debt, debt/equity weights, WACC, country and industry tax, historical/expected
growth, and financing-flow context preserve exact source file, hash, date,
sheet, row, and column. Hardcoded India rate fallbacks were removed. Autofill
selects currency- and industry-matched active records, exposes all DCF inputs,
and returns a field-level readiness summary. Industry financing aggregates are
context only and are never copied into company cash-flow assumptions.

The normal database currently has the benchmark sources but no reviewed company
financial histories or confirmed valuation industry mappings. Company-specific
starting financials, equity-bridge items, shares, price, and payout inputs cannot
be seeded from the available benchmark files. They remain explicit review or
missing states until matching company source files are imported and reviewed.

Relative valuation now supports owner-scoped reviewed peer sets in addition to
the broader industry-aggregate benchmark. Every peer member requires a source
name, URL, as-of date, and claim type. Mock-labeled sources, duplicate peers,
self-comparison, future source dates, and non-positive multiples are rejected.
The app uses a deterministic median only when at least three included peers have
a usable value for that method, and it exposes the exact included member IDs,
exclusions, formula, counts, and member-level provenance. Draft peer sets cannot
drive a valuation. Editing a reviewed set invalidates its review before it can
be used again.

Peer review now records an immutable receipt for the exact deterministic
diagnostic snapshot presented to the reviewer. The review request carries the
current diagnostic SHA-256 and the complete warning-code set; stale hashes or
partial warning acknowledgements are rejected. Reviewed sets without a current
receipt cannot drive relative valuation. The current set and each revision expose
the receipt date, warning codes, hash, and whether it still matches current
diagnostics. The UI requires an explicit warning acknowledgement and supports
re-acknowledging legacy or time-stale reviews without editing the peer evidence.
The relative-valuation selector offers only active reviewed sets whose receipts
still match current diagnostics.

Data Health audits peer evidence in owner-scoped cursor pages of 50 sets (API
maximum 100). Its page-local counts separate current/missing/stale receipts,
conflicting member/target storage, insufficient method coverage, Draft, and
archived states. Calculation eligibility is shared with the relative-valuation
backend and selector. A dedicated company peer workspace works without a DCF
model, and audit links open and focus the affected peer set. Relative-valuation
results are shown only while their input context still matches current controls.
Country, industry, and peer loaders now discard superseded responses, clear old
data during refresh, expose separate failure/retry states, and gate calculation
on membership in the successfully loaded current options. Changing companies
remounts the peer editor and calculation scope. Late calculation successes and
errors are discarded after an input change; returning to an earlier choice does
not restore its old result.

Relative-valuation requests now require finite numeric financial inputs,
nonnegative supplied cash/debt, positive supplied shares, unique supported
methods, valid identifiers, and one benchmark basis. Unknown fields and
ambiguous requests return structured validation errors. Losses and missing
inputs retain their established unavailable-method behavior. Overflowing
calculations are excluded per method, and scaled averaging keeps finite price
ranges finite. Non-finite rejected values are safe to serialize in error detail.

The saved DCF workspace now loads relative-valuation inputs through an owned
backend adapter rather than reconstructing financials in the browser. It
preserves zero cash/debt and saved book equity, derives EBIT only from available
revenue and operating margin, and leaves EBITDA unavailable without complete
D&A evidence. The input view shows source fields, assumption/model IDs, saved
timestamps, currency, missing values, and method-specific company-input coverage.
Stale, invalid, currency-unconfigured, or wholly unavailable saved inputs block
the saved-input calculation route. Calculation rereads the owned input set and
requires its exact preview hash and explicit basis confirmation. Client financial
overrides are rejected. Results include the exact input basis used. Unsaved DCF
form edits are not calculation inputs and relative actions do not submit the DCF
form. Monetary/share scales and the simplified debt/cash bridge are disclosed
for user confirmation, not silently inferred or independently verified.

The separate DCF implied-pricing sidebar now uses explicit saved net income,
book equity, revenue, and margin instead of proxy earnings or EBIT-as-EBITDA.
New runs use final adjusted DCF values; historical API reads reconcile ratios
and structured pricing diagnostics without changing stored records. The UI
shows formulas, source fields, timestamps, and unavailable reasons, preserves
zero values, and blocks stale or untrusted ratios. Review thresholds are labeled
heuristics, not empirical industry benchmarks. Historical quality scores are
not recalculated by reads. Remaining output-card gaps stay in the single ledger.

The saved output cards now share stale/invalid/critical, identity, currency and
finite-value display gates. Saved price is labeled User Assumption, historical
quality scores are not synthesized or presented as current confidence, and
supplementary total-equity calculations are distinguished from per-share values.
Corrected historical input forms can reach backend validation instead of being
permanently disabled by their old values. Scenarios retain the owned model type,
preserve explicit zero shocks, use saved currency and backend-calculated gaps,
and expose diagnostics with loading, error/retry and empty states. Scenario
generation is on demand and blocks stale or invalid saved inputs.

Peer-set lifecycle writes now use optimistic version checks and immutable
snapshots. Create, edit, review, archive, restore, and migration-backfill actions
retain their exact member evidence, aggregates, review state, actor ownership,
changed fields, and version. Archived sets can be restored only as Draft. The UI
can edit, restore, and inspect history. Comparability diagnostics flag stale or
unaligned source dates, Source Summary members, sparse method coverage, and wide
multiple dispersion. These are warnings, not silent exclusions, and they reduce
displayed reliability rather than pretending peer selection is objective.

Peer members are now also stored in normalized current and immutable revision
tables while the existing JSON snapshots remain as a compatibility and storage-
consistency audit boundary. New writes update both representations atomically,
and reads expose any mismatch. A strict source-preserving CSV workflow supports
header-only template download, non-writing row-level preview, exact SHA-256 apply
as Draft, and formula-safe export. CSV format v2 repeats one sourced target-company
profile across peer rows, validates that the target fields are identical, and
round-trips the profile on export. Legacy member-only files remain accepted with
a visible missing-target warning. Optional country, currency, fiscal period,
accounting standard, size, growth, and margin fields drive deterministic mismatch
warnings. They remain user-supplied facts, not independently verified data, and
the product deliberately does not invent a comparability score.

Peer size diagnostics now group positive market-cap amounts by stated currency.
Only same-currency peers contribute to a size-dispersion ratio, and target-size
checks compare only peers whose currency matches the target. The API returns the
per-currency groups, included identifiers, ratios, and skipped counts. Missing,
invalid, or cross-currency values remain visible as warnings instead of being
silently combined into a raw amount comparison. The peer-set UI shows comparison
coverage and the number of target peers skipped.

Peer sets can now retain a separate source-labeled target-company comparability
profile in normalized current and immutable revision rows, with JSON retained as
an explicit consistency boundary. The optional target profile requires a real
source label, URL, as-of date, claim type, and at least one comparability fact.
Target-versus-peer currency, country, accounting, fiscal-period, size, growth,
and margin mismatches are exposed as deterministic warnings and lower result
reliability. Missing target context stays visible instead of being inferred from
industry priors or company metadata. Target storage mismatches block review and
valuation use.

The peer CSV path now rejects malformed quoting, wrong row widths, NUL bytes,
oversized UTF-8 content, non-finite numeric cells, and invalid create metadata
before apply. Parsing stops at the 50-peer limit, numeric errors are sanitized,
and conflicting storage blocks export. Browser file reads enforce size and UTF-8
checks and invalidate stale previews. Migration `n5n5n5n5n5n5` stores a nullable
source-content SHA-256 receipt on imported sets and enforces uniqueness per owner
and target company. Reapplying the exact previewed CSV returns the existing set,
including an archived set, and concurrent duplicate requests converge on the
database winner. Manual sets retain null receipts and can still be duplicated.

The portfolio detail implementation now includes a source-traced risk and DCF
valuation-gap comparison. It converts dated holding prices with dated FX,
aligns daily returns, calculates sample covariance, annualized volatility,
marginal volatility, and reconciling component risk, and shows coverage when a
holding lacks enough history. The expected-return label is deliberately limited
to a current DCF valuation gap Estimate. Stale, low-quality, warned, or missing
DCF outputs remain unavailable and are not treated as forecasts.

A deterministic portfolio runtime fixture now supplies explicitly labeled Mock
Data for two complete dates, USD and EUR holdings, 22 aligned observations,
dated FX, a benchmark, an opening cash flow, and two trusted Base DCF outputs.
Its focused browser workflow checks TWR/MWR, price and FX attribution,
opportunity cost, marginal/component risk reconciliation, DCF coverage, source
IDs, and the visible Mock Data disclosure. This is repeatable implementation
proof, not real investment evidence. The user reported the focused backend and
browser Docker gate passing on 2026-08-23. A separate manual real-input smoke
remains open.

The portfolio detail page now includes a read-only real-input readiness audit.
It checks the exact pending manual-smoke inputs: positive holdings, two complete
snapshot dates, a non-base-currency holding, at least 20 aligned returns per
holding, dated FX evidence, an active benchmark with boundary prices, at least
one trusted Base DCF output, explicit source labels and record IDs, and no Mock
Data markers. A blocked audit remains a successful current-state read rather
than being mislabeled stale or partial. The same deterministic service is
available through an owner-scoped endpoint and a non-mutating CLI. Readiness is
only a preflight; it does not make synthetic data real or replace the manual
browser smoke.

The portfolio page now also has an owner-scoped source-evidence bundle workflow
for bulk historical market prices and FX observations. A non-writing server
preview enforces the exact CSV contract, portfolio/benchmark symbol scope,
required currency-pair scope, finite positive values, non-future ISO dates,
attributable provider names, safe source URLs, timezone-aware source timestamps,
supported price types, and absence of Mock Data markers. It reports create,
exact-duplicate skip, conflict, and row-error states. Apply accepts only the
same SHA-256 file, revalidates it, writes atomically, and records a sanitized
Processing Run. Imported records retain `Fact`, their source metadata, and the
import run ID. The upstream source is still user-supplied and is not
independently verified by the application.

Portfolio valuation now batches prices, owned DCF outputs, thesis state, and
alert counts instead of issuing per-holding queries. Portfolio surfaces expose
trusted, stale, untrusted, and unavailable valuation states; an output that fails
quality, warning, currency, freshness, or positivity gates cannot be displayed
as a valid intrinsic value.

The dashboard overview no longer runs AI generation, creates alerts, or performs
a live full-portfolio recalculation during a GET request. It reads the latest
explicitly captured portfolio snapshot for the headline value; deeper live
analytics remain in the Portfolio workspace. Latency budget breaches are logged
for operators instead of being misreported as partial investment data.

Daily Brief now calculates held-company moves only from two distinct dated
prices and exposes an unavailable state instead of inventing a zero. Filings and
high-materiality events carry stored document, source, timestamp, claim-type,
and evidence-state context. Affected owned portfolios, price IDs, alert IDs, and
AI output provenance are visible. Contradiction and valuation generation expose
not-run, failed, partial, and complete states. Ordinary GET is deterministic;
the explicit refresh action is the only briefing path that runs external AI.
The frontend now links to the real event evidence-resolution and source-document
routes and has a focused authenticated browser workflow.

Daily Brief review state now records the actual review timestamp instead of
using the brief creation time as a proxy. Failed and partial processing runs
since that review are included as sanitized facts with a Data Health link. A
bounded inspection queue derives explicit human-review actions for unresolved
contradictions, failed processing, missing two-price move evidence, and material
events without linked documents. Each action exposes its originating record IDs.

Daily Brief also has an explicit local scheduling foundation. Its owner-scoped
record stores an IANA timezone, local time, weekdays, next run, lease, last
status, Processing Run, and generated brief. The optional worker creates the
same deterministic no-external-AI brief as an ordinary GET, deduplicates the
owner and local date, advances after both success and failure, and never stores
raw exception details. Configuration and run state are visible on the Daily
Brief page. The current source migration head is `o6o6o6o6o6o6`. Schedule tests
passed inside the latest full backend run. The scheduler image and container
started, and the schedule-specific browser workflow passed. A real due cycle on
2026-08-24 checked and completed one schedule, created one deterministic brief,
recorded a sanitized successful Processing Run, cleared the lease, and advanced
the next run. A repeated due cycle reused the same owner/date brief with
`created_count = 0`; exactly one brief remained for the date.

Runtime health now separates liveness from readiness. `/api/health` only proves
the backend process responds. `/api/readiness` also checks the database,
migration head, and Daily Brief schema and returns HTTP 503 with safe blockers
when they disagree. The frontend depends on readiness, and Data Health exposes
the current and expected migration plus missing tables or columns. The Daily
Brief page preserves its main briefing when only scheduling fails and exposes
the actual structured API error when the brief itself is unavailable. E2E
workflows use `13000/18000` by default and preflight port ownership instead of
colliding with the normal `3000/8000` stack.

Server-rendered authentication now uses the asynchronous Next.js cookie store
and verified NextAuth JWT decoding instead of the incompatible
`getServerSession` path that returned no session under the current Next.js 16
runtime. Standard, secure, and chunked session cookie names are supported. Only
the decoded local identity is converted into a signed internal backend header;
the browser cookie is not forwarded or logged. This shared path owns Dashboard,
Research, Daily Brief, Companies, Documents, and the other server-rendered
workspaces.
The shared API helper crosses the Next.js runtime `connection()` boundary before
reading `NEXTAUTH_SECRET` or `API_BASE_URL`. Production builds therefore mark
these authenticated pages dynamic instead of caching a build-time configuration
failure created before Compose supplies runtime environment variables.

AI evidence review now offers on-demand exact-passage candidates for each
declared raw-document source marker. Matching is local and deterministic: it
extracts the generated claim, scans bounded stored source text, ranks exact
spans with numeric-aware lexical coverage, and returns source offsets,
confidence, and limitations. Selecting a candidate only fills a review draft.
The existing exact-text validator and human approval gate still decide whether
the output can be approved; no external provider is called by suggestion
generation.

Stored-corpus search now covers documents, events, owned alerts, thesis notes,
decision logs, valuation models, shared narrative clusters and claims, owned
research-session titles and user messages, and owned approved AI outputs.
Private records are filtered by the authenticated owner. Pending, blocked,
failed, unreviewed, and cross-user AI outputs are excluded. Shared narratives
are labeled as `AI Interpretation` because their records do not yet preserve
enough per-record provenance to classify them as facts. Search excerpts are
bounded to 280 characters, mock AI results propagate mock state, and each new
result links to a stable record anchor.

Frontend data-state semantics now separate availability from freshness. Request,
authentication, proxy, and parse failures render as unavailable/error states and
never claim a cache fallback. Stale labels apply only to successful responses
whose stored source data is older than its freshness threshold.

The portfolio index is now a bounded overview. It loads owned portfolios,
holdings, companies, and trust-gated valuation status, then links to each
portfolio's detail workspace for performance, attribution, benchmark, snapshot,
and risk calculations. Those deep calculations no longer block the overview.
Market Regime inputs have programmatic labels and its two-column layout collapses
responsively. The authenticated responsive smoke matrix now covers 20 primary
routes at desktop and mobile widths and now rejects undersized body text, page
titles, panel headings, and meaningful controls. All 20 routes reached complete
authenticated desktop and mobile renders on 2026-08-25. The same run passed
server-stream completion, the 15-second per-route readiness budget, 5xx and
authentication rejection, horizontal-overflow checks, semantic names,
typography minimums, keyboard focus, and screenshot capture. The separate mobile
navigation test also passed open, close, Escape, and trigger-focus restoration.
This isolated reference-data run does not satisfy the pending genuine-input
portfolio performance smoke.

FRED macro ingestion now has an authenticated, auditable boundary. It validates
and normalizes series IDs, preserves the official series URL and provider name,
updates stored metadata, distinguishes new, duplicate, missing, and rejected
observations, and records sanitized success, partial-success, or failure evidence
through Processing Runs. Provider Health now recognizes the emitted
`partial_success` state.

The Market Regime workspace can preview the latest persisted NFCI observation
and apply one exact-record-linked macro input without fetching data inside the
calculation action. The normalization is a visible Calculation:
`clamp(-NFCI × 50, -100, 100)`. Missing provenance blocks application, stale
observations remain stale, repeated application is idempotent, and provider
claims entered without a stored source record remain Source Summaries rather
than Facts. Options, liquidity, volume, and breadth still have no equivalent
automated provider adapter.

Daily Brief now loads its current and saved briefs in parallel. Research and
Narratives use responsive layouts without fixed-width overflow. Data Management
loads companies, sources, and both market capability matrices concurrently, uses
valid link actions, and collapses its cards safely. CSV upload, Damodaran admin,
and search controls now have programmatic labels and bounded responsive layouts;
Settings loads scoring and integration status concurrently.

The default Docker stack now runs a multi-stage standalone Next.js image and a
single backend process instead of permanent development compilers and reloaders.
Development bind mounts are opt-in, named caches replace anonymous frontend
volumes, pgAdmin is opt-in, service startup is health-gated, logs are capped, and
the backend build context excludes data, documentation, and frontend files.
Narratives now loads four bounded datasets in parallel instead of issuing two
requests per cluster; Macro setup calls run concurrently. Expensive workspace and
deep-diagnostic links do not prefetch server work. The 20-route matrix enforces a
15-second ready-state budget in addition to its accessibility and layout gates.
Frontend Docker build context now excludes `.env` and every `.env.*` file except
`.env.example`. A clean no-cache production build confirmed that `.env.local`
is no longer loaded or copied during image construction.

Data Health now keeps its normal page load bounded by separating deep evidence,
Damodaran coverage, and evidence-backfill diagnostics into explicit user-run
checks. Provider cards separate required configuration from optional
integrations. Its summary now separates operations, provider readiness, and
diagnostic status; a diagnostic that has not run is muted instead of being shown
as a successful zero, and optional integrations no longer compete visually with
required failures. The deep evidence audit accepts retrieval time as the
freshness clock for SEC Company Facts snapshots, while publication documents
still require a source publication timestamp.

Current validation through 2026-09-06: the workbook-aware source-mounted backend
suite passes all 774 tests with four upstream `openpyxl` deprecation warnings.
The focused valuation-input/pricing/peer/error-contract suite passes 127 tests, all 138 frontend
tests pass, and TypeScript passes. A production frontend image
build passes. Source and the normal PostgreSQL runtime are at
`o6o6o6o6o6o6`, and the live valuation benchmark seed reports complete
provenance for all 18 active typed sources. The production frontend build and
deployment passed without reading protected host environment files. A fresh
temporary PostgreSQL database also upgraded through the full chain to the same
single head. A populated m4-to-n5 fixture preserved legacy peer sets with null
receipts, enforced owner/company/hash uniqueness, and downgraded without losing
the rows. A separate `l3` fixture upgrade preserved existing peer sets and
revisions with empty target defaults rather than fabricated facts. The prior
`k2` fixture upgrade proved current-member and revision-member normalization,
including safe handling of legacy strings and duplicate identifiers, and a real
PostgreSQL service smoke proved same-identifier updates remain atomic.
Previously recorded Daily Brief, stored-research search, FRED/NFCI, portfolio,
and authenticated browser gates remain valid for their stated source boundaries.

## Capability Map

See [`roadmaps/feature-register.md`](roadmaps/feature-register.md) for the canonical list of capabilities and their current implementation statuses.

## Certified Data State

- AAPL FY2022-FY2025 core facts are reviewed, promoted, and reconciled.
- AAPL FY2021 is intentionally not promoted.
- Adani Ports FY2023-FY2025 is promoted, normalized, reconciled, and certified.
  The representative US/India two-market certification gate passes.
- `countrystats.xls` active version `#50` is dated `2026-01-05`, contains 127
  rows, and has SHA-256
  `900b6594f808461f9ce5194abf1a50e66f22854bc998473ad8282037d464829b`.

## Do Not Trust Without Review

- Stale, incomplete, or manual market-regime values without reviewing their
  normalization methodology and source.
- AI memos, narrative-to-numbers suggestions, or generated conclusions.
- Industry mapping or industry averages as company-specific facts.
- Draft, stale, or weakly comparable peer sets, even when their source fields
  are complete.
- Autofilled valuation assumptions without checking source, age, method, and warnings.
- Financial metrics from unreviewed extraction candidates.
- Prices without provider, timestamp, freshness, and currency context.
- India automated filing/provider coverage.
- Any output phrased as a buy or sell recommendation.

## Current Priorities

1. Browser-test portfolio performance separately with real dated prices, FX,
   flows, a benchmark, and trusted DCFs after the readiness audit reports
   `ready`.
2. Add compliant provider adapters for remaining regime modules only where
   licensing and exact stored-record provenance are available; keep unsupported
   options, liquidity, volume, and breadth inputs explicitly manual.

Acceptance criteria and sequencing live in
[`roadmaps/product-roadmap.md`](roadmaps/product-roadmap.md). Feature status
lives in [`roadmaps/feature-register.md`](roadmaps/feature-register.md).

## Historical Evidence

Dated checkpoints, previous audits, accumulated handoffs, and superseded plans
are preserved under [`archive/`](archive/). They are evidence of prior work, not
current instructions.
