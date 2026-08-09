# Product Roadmap

**Prioritized:** 2026-08-08

**Current estimate:** not recalculated for this release; rely on capability
status and acceptance gates instead of the prior subjective percentages.

## Planning Rule

Finish workflow integrity before adding more schema or isolated engines. A task
is complete only when backend behavior, frontend states, provenance, ownership,
tests, and documentation agree.

## Priority 1: Frontend and Backend Truth Parity (COMPLETED)

Audit every active frontend route against real API behavior.

Acceptance gates:

- Every panel identifies live, manual, partial, stale, mock, or not-configured data.
- Loading, empty, error, stale, partial, and permission states are intentional.
- Server and browser API access preserve auth and response metadata.
- No route invents values to compensate for a missing endpoint.
- Hardcoded methodology fallback values are replaced by approved versioned data
  or explicit user-custom/not-configured states.
- Representative desktop and mobile browser workflows pass.

## Priority 2: Broader Real-Issuer and India Provider Coverage (COMPLETED)

Preserve the certified AAPL/APSEZ reference gate, add broader issuer/layout
coverage, and improve official India source routing.

Acceptance gates:

- Existing AAPL/APSEZ certification remains green.
- At least one additional issuer/layout is reviewed, reconciled, promoted, and source-linked.
- Minority interests, cross-holdings, leases, currency, and diluted shares are explicit.
- India company identity, filing source, price source, and freshness are visible.
- The two-market certification harness remains portable and deterministic.
- Unsupported NSE/BSE automation remains visibly manual until implemented.

## Priority 3: Daily Evidence-to-Decision Loop (The Morning Briefing)

Connect ingestion, evidence, alerts, thesis changes, valuation relevance,
portfolio exposure, and next actions into one repeatable workflow (The Morning Briefing).

Acceptance gates:

- A user can see what changed since the last review in an aggregated dashboard.
- Each important claim opens its source evidence.
- Contradicting or thesis-breaking evidence is visible. If a new filing contradicts a user's logged thesis assumption, it flags a "Contradiction Alert."
- Portfolio holdings affected by an event are identified.
- News tracking feature cross-references overnight ingestion (SEC, RSS, News) with the active portfolio. If relevant news is found, it suggests which specific variable might be affected in the DCF model.
- The daily brief distinguishes new, unresolved, stale, and reviewed items.
- Processing failures are visible in Data Health.

## Priority 4: Portfolio Attribution and Opportunity Cost (CORE PERFORMANCE SLICE COMPLETED)

Move beyond current value and exposure totals to advanced portfolio tracking.

Acceptance gates:

- Performance separates price movement, cash flows, FX impact, and position changes.
- Attribution is available by holding, sector, geography, and user tags, providing detailed risk exposure breakdowns.
- The user can compare opportunity cost, marginal risk, and expected return across holdings.
- Stale or missing prices block false precision.
- No feature emits a buy/sell instruction.

Delivered: dated generated snapshots, historical FX, explicit benchmark
configuration, TWR/MWR, price/FX/position/flow attribution, dimension
attribution, residual diagnostics, and benchmark opportunity cost. Still open:
marginal-risk and expected-return comparisons across holdings.

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
formula, blockers, warnings, and input evidence. Automated provider coverage for
every regime module is not implied.

## Priority 6: Source-Backed AI Research (REVIEW GATE COMPLETED)

Raise AI trust only after deterministic evidence and review paths are complete.

Acceptance gates:

- Generated claims cite stored source IDs and exact evidence where available.
- Citation validation and evaluation run before approval.
- Unsupported claims are blocked or visibly flagged.
- Prompt/model/version/privacy metadata is stored.
- Output remains analysis, not investment advice.

Delivered: source-marker coverage, exact stored-text validation, persistent
blocked/evaluation state, owner-scoped review, and approval gating. Automatic
selection of exact supporting passages remains partial.

## Deferred

- Broker sync until an approved OAuth/token security design exists.
- Public deployment until the security threat model's release gates are met.
- Real-time trading feeds and expensive microstructure data.
- Social scraping without an official API and provenance model.
- Additional Damodaran workbook parsers without a consuming application workflow.

## Selection Rule

Choose the highest priority with an unmet acceptance gate. Do not use old
checkpoint numbering as a task queue. Historical plans are available in
`../archive/plans/` only when implementation context is needed.
