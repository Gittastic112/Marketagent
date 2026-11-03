# Market Intelligence Engine
# Product Integrity, Sequential Build, and Agent Execution Master Plan

**Status:** Historical proposal, superseded by the current handoff and roadmap. Archived 2026-09-19; implementation claims below are not current certification.  
**Prepared:** 2026-08-08  
**Primary purpose:** Convert the existing Market Intelligence Engine from a broad and technically capable repository into a reliable, coherent, demonstrable, and eventually decision-grade investment research system.

---

# 0. Why This Document Exists

The repository has reached an important transition point.

The problem is no longer that too little has been built.

The problem is that the product now contains many technically serious components, but several of them are more mature in isolation than they are as a connected user workflow. The next stage must therefore prioritize **integrity, completion, calibration, and sequencing** rather than uncontrolled feature expansion.

This document is the execution specification for that next stage.

It is intended to guide Codex, Claude Code, Cursor, Antigravity, or any other coding agent working in the repository.

This file does **not** replace the following current sources of truth:

- `docs/HANDOFF.md`
- `docs/00-current-state.md`
- `docs/02-architecture.md`
- `docs/03-database-schema.md`
- `docs/04-data-sources-and-ingestion.md`
- `docs/05-scoring-framework.md`
- `docs/06-security-threat-model.md`
- `docs/07-local-development.md`
- `docs/08-execution-runbook.md`
- `docs/12-assumption-methodology-engine.md`
- `docs/agent_capabilities_and_limitations.md`
- `docs/roadmaps/product-roadmap.md`
- `docs/roadmaps/feature-register.md`
- `docs/valuation-agent/README.md`
- root `AGENTS.md`

Instead, it defines **how the existing product should now be completed and matured in sequence**.

If this document conflicts with actual code, tests, or the current architecture, agents must inspect and reconcile the conflict before changing behavior.

---

# 1. Executive Judgment

## 1.1 Current position

The Market Intelligence Engine is no longer a basic MVP.

Its strongest areas are:

- deterministic valuation
- evidence and provenance foundations
- source-backed financial review
- local ownership and authentication controls
- database versioning
- explicit trust states
- Damodaran dataset handling
- broad backend capability
- investment-domain modeling

Its weaker areas are:

- end-to-end user workflow
- frontend/backend truth parity
- real-world provider breadth
- broad issuer certification
- portfolio attribution
- AI citation quality
- calibrated intelligence evaluation
- decision-readiness visibility
- consistency across documentation
- live market-regime inputs
- autonomous daily operation

The core strategic conclusion is:

> **The next stage should make existing components complete, connected, testable, and trustworthy before adding substantial new backend breadth.**

---

# 2. Product North Star

The product should become a **source-backed investment research operating system**.

It should not merely collect data.

It should help the user answer:

1. What do I know?
2. What is the source?
3. How current is it?
4. What changed?
5. How important is the change?
6. What part of my thesis does it affect?
7. What valuation assumption could it affect?
8. What part of my portfolio is exposed?
9. What remains uncertain?
10. What requires review?
11. What evidence contradicts my current belief?
12. What did I previously expect?
13. Was that expectation correct?
14. What should I investigate next?

The long-term ideal is not simply:

```text
AI + dashboard + DCF
```

It is:

```text
Evidence
→ reviewed facts
→ explicit assumptions
→ thesis
→ valuation
→ portfolio context
→ new evidence
→ contradiction or confirmation
→ assumption change
→ valuation change
→ decision record
→ later outcome
→ forecast calibration
→ improved judgment
```

That is the product.

---

# 3. Hard Product Rules

These rules are non-negotiable.

## 3.1 No fake reality

The product may contain concept demonstrations, simulations, mock data, hypothetical providers, or prototype outputs.

That is acceptable.

What is unacceptable is presenting them as real.

Every visible state must identify whether it is:

- Live
- Source-backed
- Manual
- Calculated
- Reviewed
- Unreviewed
- Partial
- Stale
- Not Configured
- Unsupported
- Simulated
- Prototype
- Mock Data

A user should never need to guess.

---

## 3.2 Concept features are allowed

Some features require data that is expensive, rate-limited, difficult to license, or unavailable through a free API.

Do **not** automatically remove such features.

A useful product can contain three maturity modes:

### Mode A: Operational

Real, source-backed, current enough for intended use.

Example:

```text
AAPL latest filing from SEC
```

### Mode B: Manual or user-supplied

The feature works correctly if the user provides the input manually or through an imported file.

Example:

```text
VIX term structure entered manually from a trusted source
```

### Mode C: Concept / demonstrator

The interface, formulas, workflow, state logic, and explainability are built, but live data is unavailable.

Example:

```text
Market Regime Prototype
Source mode: Demonstration
Data: Simulated
Not for investment decisions
```

A concept mode is valuable when it demonstrates:

- what the feature would do
- what data it needs
- how the score is calculated
- how the output affects the research process
- what a funded or licensed version would unlock

This is especially useful for demonstrating the product to potential employers, investors, collaborators, or funding sources.

However, concept mode must be visibly separated from live mode.

---

## 3.3 No buy/sell recommendations

The application should structure investment judgment.

It should not issue direct instructions such as:

```text
Buy
Sell
Strong Buy
Guaranteed upside
You should purchase
```

The system may instead produce:

```text
Valuation gap appears positive under the reviewed base-case assumptions.

Decision readiness is incomplete because two material thesis assumptions have unresolved evidence.

Market structure is currently supportive, but the market-regime module is using simulated options-flow inputs.

The current evidence set weakens the margin-expansion thesis.
```

---

## 3.4 No precision without support

The system should avoid fake exactness.

Bad:

```text
Company quality score = 83.42
```

unless that precision is genuinely justified.

Better:

```text
Fundamental score: 83 / 100
Confidence: Medium
Primary drivers:
- improving margins
- positive ROIC spread
- strong cash conversion
Main limitation:
- latest quarter remains unreviewed
```

Likewise:

```text
Decision readiness: 72%
```

is acceptable only if the underlying completeness rules are explicit.

---

# 4. Source and Trust Taxonomy

Every meaningful data point or conclusion should carry one or more of the following claim types.

## 4.1 Fact

Directly supported by a reviewed source.

Example:

```text
FY2025 revenue = ₹31,000 crore
```

## 4.2 Source Summary

A bounded summary of a source.

Example:

```text
Management stated that port capacity expansion remains on schedule.
```

## 4.3 Calculation

Derived deterministically from explicit inputs.

Example:

```text
ROIC = 17.8%
```

## 4.4 User Assumption

Chosen or manually entered by the user.

Example:

```text
FY2027 revenue growth = 13%
```

## 4.5 AI Interpretation

Generated reasoning based on source-backed inputs.

Example:

```text
The filing may weaken the assumption that margin expansion will continue at the prior pace.
```

## 4.6 Estimate

A non-reviewed or estimated value.

Example:

```text
Estimated lease-adjusted debt
```

## 4.7 Mock / Simulated

Artificial value used for demonstration, testing, or prototyping.

Example:

```text
Simulated gamma exposure regime = positive
```

---

# 5. Current Strategic Problem

The system contains many capable modules:

- filings
- PDFs
- financial candidates
- normalization
- reconciliation
- evidence
- events
- alerts
- thesis notes
- thesis assumptions
- contradictions
- portfolios
- market prices
- macro data
- DCFs
- FCFE/DDM
- reverse DCF
- relative valuation
- real options
- macro sensitivity
- Damodaran priors
- scoring
- narratives
- research sessions
- AI
- market-regime concepts

The product risk is that each module becomes increasingly sophisticated while the overall user journey remains fragmented.

Therefore:

> **For the next major stage, the default action is to deepen or connect an existing capability, not create a new domain.**

---

# 6. Sequential Build Doctrine

The system should mature in explicit stages.

Do not skip ahead merely because a later feature is more exciting.

Every stage has:

1. objective
2. required functionality
3. acceptance gates
4. evaluation requirements
5. allowed prototype behavior
6. prohibited shortcuts

The Morning Briefing remains a later-stage feature.

That is intentional.

The system should first make each underlying component reliable enough that the Morning Briefing can summarize real product intelligence rather than assembling partially trusted modules.

---

# 7. Stage 0: Repository Truth and Documentation Integrity

## Objective

Ensure the repository has one coherent understanding of what exists.

This stage must happen before significant new product development.

## Required work

### 7.1 Reconcile migration-head documentation

Current documents appear to disagree about the Alembic migration head.

The agent must:

1. inspect:
   - `backend/alembic/versions/`
   - `alembic heads`
   - `alembic current`
2. identify the actual current migration head
3. update every current document that states a migration head
4. avoid duplicating that value unnecessarily
5. make one document the canonical owner of the migration-head state

Suggested owner:

```text
docs/00-current-state.md
```

Other docs should say:

```text
See 00-current-state.md for the current migration head.
```

rather than hardcoding it.

---

### 7.2 Reconcile backend URL configuration

Inspect whether current code uses:

- `API_BASE_URL`
- `NEXT_PUBLIC_API_BASE_URL`
- same-origin `/api/backend`
- another pattern

Then update current documentation.

There must be one clear explanation for:

- server-rendered API requests
- browser API requests
- container-to-container requests
- host-to-backend requests

---

### 7.3 Reconcile health-route wording

Determine whether canonical health is:

```text
/api/health
```

and whether:

```text
/health
```

is legacy compatibility.

Document that consistently.

---

### 7.4 Standardize feature statuses

Use exactly:

- Built
- Partial
- Prototype
- Not Built

Optional additional runtime states may include:

- Not Configured
- Stale
- Manual
- Unsupported

But do not call the same feature:

```text
Built but not autonomous
```

in one file and:

```text
Partial
```

in another unless the difference is explicitly defined.

---

### 7.5 Reduce mutable-fact duplication

A current mutable fact should have one owner.

Examples:

| Fact | Canonical owner |
|---|---|
| Current migration head | `00-current-state.md` |
| Current test baseline | `00-current-state.md` |
| Current feature statuses | `feature-register.md` |
| Execution priority | `product-roadmap.md` |
| Local commands | `07-local-development.md` |
| Architecture | `02-architecture.md` |
| Security requirements | `06-security-threat-model.md` |
| Scoring formula | `05-scoring-framework.md` |
| Assumption methodology | `12-assumption-methodology-engine.md` |

Other documents should link rather than restate.

---

## Stage 0 acceptance gates

- `scripts/check_docs.py` passes
- no conflicting migration-head claims
- no conflicting canonical API URL claims
- no conflicting feature-state claims across active docs
- root `AGENTS.md` distinguishes instruction precedence from factual truth precedence
- archived docs are clearly non-current

---

# 8. Stage 1: Agent Instruction Architecture

## Objective

Make agent behavior safer, more focused, and less prone to giant speculative changes.

## 8.1 Root AGENTS.md

Root `AGENTS.md` should remain concise enough to function as a real operating manual.

It should contain:

- project purpose
- trust rules
- inspect-before-editing rule
- small-diff rule
- source/provenance rules
- security invariants
- destructive-operation stop conditions
- testing expectations
- documentation ownership rules
- completion-report format

It should not become the permanent home of detailed specifications for every future feature.

---

## 8.2 Nested agent instructions

Add narrower instructions where needed.

Suggested:

```text
backend/AGENTS.md
frontend/AGENTS.md
docs/AGENTS.md
damodaran_knowledge_base_v1/AGENTS.md
```

Potential later:

```text
backend/app/services/valuation/AGENTS.md
backend/app/providers/AGENTS.md
```

Nested instructions should be narrower than root instructions.

---

## 8.3 Explicit hierarchy

Separate:

### Instruction precedence

```text
1. User request
2. Nearest applicable nested AGENTS.md
3. Parent/root AGENTS.md
4. Task-specific current docs
5. Framework conventions
```

from:

### Factual truth precedence

```text
1. Running code and database reality
2. Tests
3. Current state documentation
4. Archived historical documentation
5. Planning documents
```

These are different concepts.

Do not mix them.

---

# 9. Stage 2: Frontend and Backend Truth Parity

## Objective

Ensure every visible interface accurately reflects actual backend capability.

This is more important than redesigning the UI.

## 9.1 Route inventory

Build an automated or manually maintained route audit table.

For every active page:

```text
Route
Purpose
Backend endpoint(s)
Ownership
Source
Freshness
Loading
Empty
Error
Stale
Partial
Not Configured
Mock
Mobile
Desktop
Browser validation
```

Example:

| Route | Live? | Loading | Empty | Error | Stale | Partial | Mock |
|---|---:|---:|---:|---:|---:|---:|---:|
| `/companies/[id]/fundamentals` | Yes | Yes | Yes | Yes | Yes | Yes | No |
| `/market-regime` | Prototype | Yes | N/A | N/A | N/A | N/A | Clearly labeled |

---

## 9.2 Standard data-state components

Every important module should use consistent components:

```text
LoadingState
EmptyState
ErrorState
StaleDataNotice
PartialDataNotice
NotConfiguredState
UnsupportedState
ManualDataBadge
MockDataBadge
PrototypeBadge
SourceBadge
FreshnessIndicator
ConfidenceIndicator
ReviewStateBadge
```

---

## 9.3 No frontend invention

If the backend does not supply a value, the frontend must not create one merely to make the screen look complete.

Allowed:

```text
Not available
Provider not configured
Manual input required
Prototype only
```

Not allowed:

```text
Hardcoded placeholder value displayed as ordinary data
```

---

## Stage 2 acceptance gates

- all core routes have intentional data states
- all mock/prototype panels are visibly labeled
- no uncaught loading failures
- browser workflows pass on representative mobile and desktop sizes
- ownership and auth remain intact
- response metadata is not discarded by the frontend
- source/freshness context remains visible

---

# 10. Stage 3: Provider and Data Scarcity Architecture

## Objective

Make the product useful even when the user cannot afford or access premium APIs.

The solution is **not** to remove ambitious features.

The solution is to architect each feature around multiple data modes.

---

# 11. Provider Capability Modes

Every external-data dependency should support one or more of the following modes.

## 11.1 Mode 1: Free official API

Examples may include:

- SEC EDGAR
- FRED
- official exchange publications where legally and technically accessible
- official government datasets

These are preferred.

---

## 11.2 Mode 2: Free-tier third-party API

Examples may include market-data providers with strict request limits.

Rules:

- rate limits must be known
- calls should be cached
- no silent overuse
- provider status visible
- prioritize high-value calls

---

## 11.3 Mode 3: Personal-use unofficial provider

Example:

```text
yfinance_personal
```

This can be acceptable for local personal usage when clearly labeled.

It must never silently masquerade as licensed production-grade data.

---

## 11.4 Mode 4: Manual input

Manual input is a first-class data source.

Examples:

- price
- risk-free rate
- ERP
- implied volatility
- put-call ratio
- institutional flow
- sector weights
- company segment mix

Manual does not mean inferior if:

- source is recorded
- date is recorded
- unit is recorded
- user explicitly confirms it
- freshness is visible

---

## 11.5 Mode 5: File import

Allow user-supplied:

- CSV
- Excel
- PDF
- exported market-data files
- broker exports
- exchange reports
- company reports

where legally appropriate.

File import may be the best low-cost solution for several features.

---

## 11.6 Mode 6: Derived calculation

Some expensive data can be replaced with calculations from cheaper/rawer data.

Examples:

```text
Volume multiplier
moving averages
breadth calculations
historical volatility
basic momentum
simple yield spreads
valuation multiples
portfolio attribution
rolling beta
drawdowns
```

Do not pay for a derived metric if it can be computed reliably from available inputs.

---

## 11.7 Mode 7: Prototype / simulated

Use when real data is unavailable but the feature is strategically important to demonstrate.

Prototype data must:

- use a deterministic fixture where possible
- be clearly labeled
- show expected source requirements
- show formula and logic
- expose what would change with live data
- never contaminate trusted datasets
- never be used in decision-grade aggregate scores without an explicit prototype warning

---

# 12. Provider Fallback Ladder

Each data domain should define an explicit provider ladder.

Example:

```text
Preferred official source
→ configured free-tier provider
→ personal-use provider
→ imported file
→ manual input
→ unavailable
```

Do **not** automatically fall back to mock data in normal use.

Mock is a separate explicit mode.

---

# 13. Free-Tier Call Budgeting

Where providers have limited free calls, implement quota-aware prioritization.

Example logic:

```text
Tier 1 calls:
- current prices for owned portfolio holdings
- current prices for active valuation companies
- latest filing metadata
- essential macro variables

Tier 2 calls:
- active watchlist prices
- historical refresh for recently reviewed companies
- company fundamentals refresh

Tier 3 calls:
- inactive watchlist
- exploratory companies
- low-priority historical refresh
```

The system should store:

```text
provider
quota window
estimated quota
calls used
calls remaining
last successful call
next safe refresh
priority class
```

If exact provider quota cannot be queried, track local estimated calls.

---

# 14. Caching and Data Reuse

Do not repeatedly call APIs for unchanged information.

Examples:

- company identity
- historical annual statements
- older market prices
- old filings
- static industry classification
- prior macro observations

The system should prefer:

```text
read local
→ evaluate freshness
→ call provider only if refresh required
```

---

# 15. Stage 4: Financial Evidence and Extraction Reliability

## Objective

Move from "works on selected examples" to "measured reliability across heterogeneous sources."

The system already has meaningful financial extraction infrastructure.

The next requirement is evaluation breadth.

---

## 15.1 Golden issuer corpus

Create a test/certification corpus covering multiple statement layouts.

Target progression:

```text
2 certified issuers
→ 5
→ 10
→ 20
```

Do not chase sheer company count.

Choose issuers that intentionally stress different cases:

- US industrial
- US technology
- US financial institution
- India infrastructure
- India manufacturing
- conglomerate
- company with meaningful minority interest
- company with leases
- company with unusual fiscal year
- company with multiple currencies or ADR complexity

---

## 15.2 Financial extraction evaluation metrics

Track:

```text
metric coverage
precision
wrong-year rate
wrong-unit rate
wrong-currency rate
duplicate rate
sign error rate
period alignment rate
source-locator accuracy
reconciliation mismatch rate
manual override rate
manual review time
unsupported-layout rate
```

---

## 15.3 Trust gates

No fact becomes valuation-ready unless required review conditions are satisfied.

At minimum:

- source known
- reporting period known
- unit known
- currency known
- source locator known where supported
- review state known
- conflicting duplicates handled
- reconciliation state visible

---

## 15.4 Reconciliation

Reconciliation should move toward structured accounting integrity checks.

Examples:

```text
Assets = Liabilities + Equity
Revenue → EBIT bridge consistency
Debt component sums
Cash flow statement reconciliation where practical
Share-count consistency
Minority-interest treatment
Cash / restricted cash treatment
```

Not every filing can be perfectly reconciled.

Failures should be explicit.

---

# 16. Stage 5: Valuation Integrity and Reproducibility

## Objective

Make valuation not merely mathematically correct, but reproducible, source-aware, and economically inspectable.

---

## 16.1 Fix assumption fallback technical debt

Hardcoded India ERP and risk-free fallbacks should not operate as ordinary trusted defaults.

Replace with:

```text
approved versioned source
OR
explicit user custom input
OR
not configured
```

Legacy fallback values may remain only as migration/history metadata if required.

---

## 16.2 Valuation snapshot reproducibility

Every completed valuation should preserve enough information to recreate it.

Store or reference:

```text
valuation model version
company financial snapshot version
market price and timestamp
reporting currency
risk-free method
risk-free source
ERP method
ERP source
beta method
cost-of-debt method
capital structure
industry mapping version
Damodaran dataset version
all assumption values
all manual overrides
scenario
share count
debt
cash
minority interest
cross holdings
option value
terminal method
calculation version
created_at
reviewed_at
```

A valuation should be replayable.

---

## 16.3 Peer-set relative valuation

Relative valuation should eventually support a reviewed peer set.

Required workflow:

```text
candidate peers
→ user review
→ include/exclude
→ comparable metric definitions
→ normalized operating metrics
→ valuation multiple distribution
→ company relative position
→ warnings
```

Avoid treating broad industry averages as equivalent to reviewed comparable companies.

Industry aggregates remain useful priors.

---

## 16.4 Accounting adjustments

High-value adjustments include:

- R&D capitalization
- operating leases
- minority interests
- cross holdings
- employee options
- non-operating assets
- unusual one-time items
- financial-company model suitability
- cyclical normalization

Each adjustment needs provenance and explanation.

---

## 16.5 Forecast calibration

Add an explicit forecast history.

For each key assumption:

```text
what was expected
when it was expected
what source supported it
what actually happened
forecast error
explanation
thesis implication
model implication
```

Example:

| Metric | Forecast | Actual | Error | Interpretation |
|---|---:|---:|---:|---|
| Revenue growth | 14% | 10% | -4 pp | Project ramp slower than expected |
| EBIT margin | 21% | 22% | +1 pp | Cost discipline better than expected |

This turns the system into a learning tool.

---

# 17. Stage 6: Scoring Framework

## Objective

Retain the scoring architecture while preventing it from becoming opaque pseudo-precision.

Scoring is useful for:

- triage
- prioritization
- comparability
- information filtering
- surfacing changes

Scoring is not a substitute for investment judgment.

---

# 18. Event-Level Scoring

Retain the existing deterministic event model.

## 18.1 Credibility

How trustworthy is the source/evidence?

Possible drivers:

- regulator filing
- company filing
- official government source
- company press release
- reputable media
- specialist publication
- anonymous source
- forum/social source

---

## 18.2 Novelty

How new is the information?

Consider:

- duplicate article
- duplicate filing language
- first-seen fact
- repeated narrative
- incremental change
- major new disclosure

---

## 18.3 Impact

How material could the information be?

Drivers:

- active thesis assumption affected
- cash-flow implication
- balance-sheet implication
- management change
- regulatory impact
- major capital allocation
- litigation
- operational disruption
- strategic shift
- portfolio exposure

---

## 18.4 Event Priority

Retain an explainable weighted calculation.

Every event score must expose:

```text
score
formula
weights
inputs
reasoning
source
confidence
limitations
```

---

# 19. Entity-Level Scoring

The existing proposed categories may remain:

- Fundamental
- Valuation
- Narrative
- Sentiment
- Risk
- Momentum
- Confidence
- Overall Signal

However, each score must answer a specific operational question.

---

## 19.1 Fundamental Score

Question:

> Are company fundamentals improving, stable, or deteriorating?

Potential inputs:

- revenue growth
- margin trend
- ROIC
- ROIC minus WACC
- cash conversion
- leverage
- interest coverage
- working capital
- capital intensity
- earnings quality

---

## 19.2 Valuation Score

Question:

> How attractive or stretched does valuation appear under reviewed methods?

Potential inputs:

- DCF implied gap
- reverse DCF difficulty
- peer-relative multiples
- historical multiples
- sensitivity
- terminal-value dependence

This must never be interpreted as a buy score.

---

## 19.3 Narrative Score

Question:

> How strong, persistent, and evidence-backed is the current market narrative?

Inputs may include:

- claim frequency
- source diversity
- novelty
- evidence strength
- narrative velocity
- contradiction rate
- company relevance

---

## 19.4 Sentiment Score

Question:

> What is the direction and intensity of observable source sentiment?

This is only useful if source coverage is adequate.

If social/news APIs are unavailable:

```text
Sentiment Score: Not Configured
```

or:

```text
Prototype
```

Do not fabricate real sentiment.

---

## 19.5 Risk Score

Question:

> What material risks are currently visible?

Potential components:

- leverage
- liquidity
- operating deterioration
- regulatory issues
- governance
- customer concentration
- valuation dependence
- unresolved data quality
- thesis contradictions

---

## 19.6 Momentum Score

Question:

> What is the current direction of price and information flow?

Can often be calculated cheaply from OHLCV and stored events.

---

## 19.7 Confidence Score

Question:

> How trustworthy is the system's current understanding?

Possible inputs:

- source completeness
- data freshness
- review completeness
- model agreement
- citation quality
- unresolved contradiction count
- provider state
- extraction confidence

---

## 19.8 Overall Signal

If retained, this must be explicitly non-prescriptive.

Better names include:

```text
Research Composite
Investment Context Composite
Company Context Score
```

Avoid:

```text
Buy Score
Investment Score
```

---

# 20. Decision Readiness Framework

Scoring and Decision Readiness serve different purposes.

## Scoring asks:

> What does the evidence appear to indicate?

## Decision Readiness asks:

> Do I have enough reliable and current information to responsibly form or revisit a judgment?

Both should coexist.

Decision Readiness should become one of the core system frameworks.

---

# 21. Decision Readiness Components

Possible categories:

## 21.1 Financial Readiness

Questions:

- latest annual financials reviewed?
- latest interim period reviewed?
- normalized statements available?
- reconciliation passed?
- debt reviewed?
- diluted shares reviewed?
- cash and minority interests reviewed?

---

## 21.2 Valuation Readiness

Questions:

- valuation exists?
- valuation recently reviewed?
- key assumptions source-backed?
- price fresh?
- bear/base/bull available?
- reverse DCF completed?
- terminal-value dependence acceptable?
- valuation warnings unresolved?

---

## 21.3 Thesis Readiness

Questions:

- active thesis exists?
- explicit assumptions logged?
- falsification criteria exist?
- major risks documented?
- variant perception documented?
- latest evidence reviewed?

---

## 21.4 Evidence Readiness

Questions:

- current filings ingested?
- exact evidence available?
- major unresolved alerts?
- stale sources?
- missing source classes?
- pending financial candidates?

---

## 21.5 Portfolio Readiness

Questions:

- current holding?
- position size known?
- current price known?
- cost basis known?
- portfolio concentration visible?
- relevant portfolio exposures known?

---

## 21.6 Catalyst Readiness

Questions:

- next earnings date?
- major known regulatory event?
- debt maturity?
- project milestone?
- investor day?
- court ruling?
- capital-allocation event?

If current event-calendar APIs are not available, this category can be manual.

---

# 22. Decision Readiness Output

Example:

```text
Decision Readiness: Medium

Financials: Ready
Valuation: Ready with warning
Thesis: Incomplete
Evidence: Partial
Portfolio Context: Ready

Blocking issues:
1. Latest quarterly filing not reviewed.
2. Terminal value = 82% of enterprise value.
3. Two thesis assumptions do not have falsification criteria.
4. Current market price is 3 days old.

Recommended next research actions:
- Review latest quarter.
- Revisit terminal assumptions.
- Define falsification criteria.
- Refresh price.
```

This is more useful than a single investment score.

---

# 23. Decision Readiness Levels

Suggested:

### Ready

No material unresolved blockers.

### Ready With Warnings

Core information complete, but meaningful warnings remain.

### Incomplete

Important research components are missing.

### Blocked

Critical inputs are missing or unreliable.

### Prototype

Readiness is being demonstrated using mock or simulated components.

---

# 24. Relationship Between Scores and Readiness

The system must not confuse them.

Example:

```text
Fundamental Score: 84
Valuation Score: 73
Narrative Score: 66
Confidence: Medium

Decision Readiness: Incomplete
Reason:
Latest quarterly financials remain unreviewed.
```

This is correct.

A high score does not imply the user has enough evidence.

---

# 25. Stage 7: Thesis and Evidence Operating System

## Objective

Turn thesis notes into a structured, falsifiable research model.

---

## 25.1 Thesis structure

A thesis should support:

```text
Investment thesis
Key drivers
Key assumptions
Catalysts
Risks
Falsification conditions
Variant perception
Evidence for
Evidence against
Unknowns
```

---

## 25.2 Thesis assumptions

Each important thesis assumption should contain:

```text
statement
category
importance
current belief
source support
confidence
last reviewed
expected timeframe
falsification trigger
linked valuation assumption if applicable
```

---

## 25.3 Contradiction engine

A contradiction is not necessarily a negative event.

It is evidence inconsistent with an existing assumption.

Example:

```text
Assumption:
Container volume growth will remain above 10%.

New evidence:
Management guides to 5% to 7%.

System:
Potential contradiction detected.
Confidence: High.
Source: Q2 earnings call.
Action required: Review assumption.
```

---

## 25.4 Confirmation engine

Likewise detect evidence that supports a thesis.

Avoid only searching for negative evidence.

---

## 25.5 Evidence ledger

Every thesis-changing item should be recordable as:

```text
supports
contradicts
neutral
unclear
```

with:

```text
source
date
claim
importance
confidence
review status
```

---

# 26. Stage 8: Portfolio Intelligence

## Objective

Move from tracking holdings to understanding investment outcomes and risk.

---

# 27. Core Portfolio Metrics

Ensure correct support for:

```text
market value
cost basis
realized P&L
unrealized P&L
cash
portfolio weight
sector exposure
country exposure
user-tag exposure
currency exposure
```

---

# 28. Performance Measurement

Add:

## 28.1 Time-weighted return

Useful for evaluating portfolio investment performance independent of cash flows.

## 28.2 Money-weighted return / XIRR

Useful for user-specific capital deployment experience.

## 28.3 Benchmark-relative performance

Support user-selected benchmark.

Examples:

```text
S&P 500
Nasdaq
Nifty 50
custom benchmark
```

Benchmark data may be:

- provider-backed
- imported
- manually updated

---

# 29. Attribution

Decompose performance into:

- price movement
- dividends
- FX
- position changes
- fees
- cash drag

And group by:

- company
- sector
- geography
- user tag
- thesis theme

---

# 30. Opportunity Cost

Do not pretend expected return is objective.

Opportunity-cost analysis should present comparisons rather than instructions.

Example:

```text
Holding A:
Reviewed DCF gap: +22%
Confidence: Medium
Decision readiness: Ready With Warnings

Holding B:
Reviewed DCF gap: +11%
Confidence: High
Decision readiness: Ready

Trade-off:
A offers larger modeled upside but has lower evidence confidence and greater terminal-value sensitivity.
```

---

# 31. Stage 9: Research Evaluation Infrastructure

## Objective

Measure whether the product is actually good.

Tests verify software behavior.

Evaluation verifies research quality.

This distinction is critical.

---

# 32. Financial Evaluation

Maintain golden truths for selected filings.

Measure:

- extraction precision
- recall
- unit accuracy
- period accuracy
- source-locator accuracy
- reconciliation
- manual intervention

---

# 33. Event Extraction Evaluation

Create a labeled event corpus.

For representative documents:

```text
expected material events
expected non-material events
expected event categories
expected thesis links
```

Measure:

- precision
- recall
- duplicate suppression
- false positives
- missed material events

---

# 34. Alert Evaluation

For each alert:

ask the user to classify:

- useful
- not useful
- false positive
- already known
- needs follow-up

Then track:

```text
useful-alert rate
false-positive rate
missed-event rate
average priority by feedback class
```

Use this to tune deterministic scoring.

---

# 35. AI Evaluation

Evaluate:

- source citation validity
- citation relevance
- unsupported claim rate
- source coverage
- contradiction handling
- privacy boundary compliance
- hallucinated numbers
- hallucinated sources
- faithful distinction between fact and interpretation

No AI trust label should improve solely because the output "looks good."

---

# 36. Valuation Evaluation

Test:

- deterministic calculation accuracy
- reproducibility
- guardrail behavior
- accounting bridge
- scenario behavior
- reverse DCF solver
- sensitivity
- historical forecast calibration

---

# 37. Stage 10: AI Research Layer

## Objective

Use AI as an analyst assistant operating over trusted local evidence.

Do not make AI the system of record.

---

## 37.1 AI permitted roles

AI may:

- summarize evidence
- compare documents
- identify potential contradictions
- classify thesis impact
- propose DCF assumption changes
- draft research memos
- explain valuation changes
- propose questions
- identify unknowns
- generate variant-perception hypotheses

---

## 37.2 AI prohibited roles

AI must not silently:

- promote financial facts
- alter reviewed assumptions
- create trusted citations
- rewrite thesis beliefs as approved
- fabricate sources
- issue buy/sell recommendations
- send private data externally without disclosed permission

---

## 37.3 Prompt-injection defense

External content is data, never instruction.

AI execution should follow:

```text
system policy
→ application instruction
→ user task
→ retrieved evidence as quoted/untrusted context
```

Never allow source text to override application behavior.

Generated AI text must not directly authorize:

- file writes
- external calls
- credential access
- assumption promotion
- portfolio transactions
- privileged actions

---

# 38. Stage 11: Narrative Intelligence

## Objective

Track market stories without pretending that narrative mentions automatically equal truth.

---

## 38.1 Narrative object

A narrative may contain:

```text
title
claims
companies
source mentions
first seen
last seen
velocity
source diversity
supporting evidence
contradicting evidence
confidence
status
```

---

## 38.2 Narrative states

Examples:

```text
Emerging
Strengthening
Stable
Weakening
Contradicted
Dormant
```

---

## 38.3 Data scarcity

If full news/social coverage is unavailable, narrative intelligence can still function using:

- SEC
- RSS
- manually imported articles
- user links
- filings
- selected news feeds

Coverage must be disclosed.

Do not imply market-wide narrative detection when the source universe is small.

---

# 39. Stage 12: Market Regime

## Objective

Preserve the concept because it is strategically useful and demonstrable, while being rigorous about the difference between prototype and source-backed behavior.

Market Regime should remain a context layer, not an investment instruction.

---

# 40. Market Regime Question

The module should answer:

> Is the broader market structure currently supportive, neutral, or hostile to taking additional risk?

It should not answer:

> Should I buy this stock?

---

# 41. Market Regime Modules

Retain the current conceptual structure:

| Module | Weight |
|---|---:|
| Options and derivatives | 30% |
| Institutional flow and liquidity | 25% |
| Volume and participation | 15% |
| Breadth and momentum | 15% |
| Macro, credit, volatility | 15% |

Weights must be configurable and inspectable.

---

# 42. Market Regime Input Strategy

Each metric should define:

```text
Preferred source
Free source
Derived alternative
Manual input
Prototype fixture
Required freshness
```

Example:

| Metric | Preferred | Low-cost alternative | Manual | Prototype |
|---|---|---|---|---|
| VIX | market API | free public source | Yes | Yes |
| Put-call ratio | options provider | exchange publication if available | Yes | Yes |
| Gamma exposure | specialist provider / chain | derive from imported chain | Yes | Yes |
| Breadth | market breadth feed | calculate from universe prices | file import | Yes |
| Credit spread | FRED | FRED | Yes | Yes |
| FII/DII | official/public India data | manual import | Yes | Yes |

---

# 43. Prototype Market Regime

A fully functional prototype is acceptable.

It should allow:

- manual input
- simulated fixture
- formula transparency
- module scores
- confidence
- warnings
- source-mode labeling
- clear conversion path to real providers

Example:

```text
Market Structure Score: 63 / 100
Mode: Prototype
Live modules: Macro
Manual modules: Breadth
Simulated modules: Options, Flows
Decision use: Not permitted
```

This demonstrates the architecture without pretending to possess data that the user cannot currently afford.

---

# 44. Stage 13: Morning Briefing

## Objective

Only after underlying modules are reliable, combine them into a coherent daily workflow.

The Morning Briefing is intentionally later-stage.

The system should not summarize unreliable components merely to appear integrated.

---

# 45. Morning Briefing Structure

Suggested sections:

## 45.1 New Since Last Review

- filings
- material news
- portfolio price moves
- macro changes
- newly generated alerts

## 45.2 High-Materiality Events

Sorted using event priority.

## 45.3 Thesis Contradictions

Evidence that may invalidate existing assumptions.

## 45.4 Thesis Confirmations

Evidence supporting existing assumptions.

## 45.5 Valuation Relevance

Possible affected model variables.

Example:

```text
Potentially affected:
- revenue growth
- operating margin
- capex
- cost of debt
```

AI may propose links, but user review is required.

## 45.6 Portfolio Impact

Identify holdings exposed to the event.

## 45.7 Decision Readiness Changes

Example:

```text
APSEZ:
Ready → Ready With Warnings

Reason:
New quarterly filing has not been reviewed.
```

## 45.8 Data Health

Show failed providers and stale sources.

## 45.9 Pending Reviews

- financial candidates
- thesis contradiction reviews
- AI outputs
- valuation warnings

## 45.10 Upcoming Known Catalysts

Manual or provider-backed.

---

# 46. Morning Briefing Acceptance Gate

The Morning Briefing should not be considered complete until:

- source links work
- event scoring works
- thesis relationships work
- valuation-variable relationships work
- portfolio relationships work
- decision readiness works
- data health works
- stale/missing states are preserved
- user can mark items reviewed
- reviewed state changes subsequent brief behavior

---

# 47. Stage 14: Research Memory and Forecast Learning

## Objective

Make the system improve the user's judgment over time.

This is a major long-term differentiator.

---

# 48. Decision Journal

For material research decisions, store:

```text
date
company
decision type
current thesis
valuation
market price
decision readiness
key supporting evidence
key contradictory evidence
uncertainties
expected catalysts
what would change the view
portfolio context
```

---

# 49. Outcome Review

Later compare:

```text
What did I think?
What happened?
Which assumption was wrong?
Was the information unavailable or misinterpreted?
Was the valuation wrong?
Was the thesis wrong?
Was the timing wrong?
Was the position sizing wrong?
```

This should become a structured calibration dataset.

---

# 50. Product Maturity Model

Every major feature should be assigned one maturity level.

## Level 0: Not Built

No usable workflow.

## Level 1: Concept

UI/spec exists, but data may be simulated.

## Level 2: Functional Manual

Works correctly with manual/user-supplied input.

## Level 3: Provider-Backed

Works with source-backed external data.

## Level 4: Integrated

Connects to related evidence, thesis, valuation, portfolio, and readiness workflows.

## Level 5: Evaluated

Quality is measured against explicit evaluation datasets or user feedback.

## Level 6: Decision-Grade

Reliable enough for the product's intended personal research use, with known limitations.

This maturity model is more defensible than saying the whole product is "64% world-class."

---

# 51. Replace Arbitrary Overall Completion Percentages

Avoid statements such as:

```text
75% complete
64% world-class
```

unless a weighted rubric exists.

Instead maintain a maturity matrix.

Example:

| Capability | Maturity |
|---|---|
| FCFF DCF | 5 |
| Financial extraction | 4 |
| Market regime | 1 |
| Portfolio attribution | 2 |
| AI citations | 3 |
| Morning Briefing | 2 |

If a summary percentage is desired later, calculate it explicitly from weighted maturity scores.

---

# 52. Suggested Product Dashboard of System Maturity

Add an internal developer/admin view showing:

```text
Feature
Maturity
Source mode
Coverage
Last validated
Evaluation score
Current blocker
```

This can be useful both for development and product demonstration.

---

# 53. Data Health Expansion

Data Health should become a core trust surface.

For each provider/source:

```text
configured
source type
last success
last attempt
last failure
rate-limit state
estimated quota
coverage
freshness
error
manual fallback
prototype fallback
```

For each company:

```text
filings status
financials status
price status
valuation status
thesis status
evidence status
AI status
```

---

# 54. Provider Independence

Do not bind the product to one data provider.

Interfaces should remain.

Examples:

```text
MarketDataProvider
FundamentalsProvider
FilingsProvider
MacroProvider
NewsProvider
OptionsProvider
AiProvider
CompanyIdentityProvider
```

The user should be able to add higher-quality providers later without rewriting the product.

---

# 55. Build Versus Buy Framework

Before adding a paid dependency, ask:

1. Can this be calculated locally?
2. Is there an official free source?
3. Is there a free tier?
4. Can the user import the information?
5. Can it be manually entered?
6. Is the live version necessary now?
7. Would a prototype demonstrate the value?
8. What specifically would the paid provider improve?

Only then consider paid data.

---

# 56. Example Low-Cost Data Strategies

## Market prices

Possible architecture:

```text
free-tier provider
→ personal-use provider
→ manual/import
```

Cache aggressively.

---

## Macro

Use official/public macro sources where possible.

Historical macro data generally does not need frequent repeated API calls.

---

## Financial statements

Prefer:

```text
SEC / official filing
→ manual PDF
→ XBRL
→ reviewed extraction
```

rather than paying for pre-normalized fundamentals too early.

---

## News

Use:

```text
RSS
→ official investor-relations feeds
→ manually imported links
→ selected free provider later
```

---

## Options

If chain APIs are unavailable:

```text
manual chain import
→ CSV
→ prototype fixture
```

The formulas and interface can still be built.

---

## Institutional flow

Use public official releases where available, manual entry otherwise.

---

# 57. Demonstration / Funding Mode

The project may benefit from an explicit demo mode.

This is different from hiding mock data.

Demo mode should be intentionally transparent.

Example banner:

```text
DEMONSTRATION MODE

Live:
- SEC filings
- reviewed financials
- DCF

Manual:
- market prices

Simulated:
- options regime
- institutional flows

All simulated components are excluded from decision-grade outputs.
```

This allows showcasing the full product vision responsibly.

---

# 58. Demo Data Isolation

Mock/simulated data must not pollute trusted application data.

Use:

- explicit `is_mock`
- explicit source type
- separate fixtures
- optional demo database
- filtering from trusted views
- visible badges

A demo should be resettable.

---

# 59. What Not to Build Yet

Until the above sequence progresses, avoid:

- broker execution
- broker password storage
- real-time trading
- expensive microstructure
- large social scraping
- public deployment
- large autonomous agent systems
- opaque machine-learning scores
- unnecessary vector-database complexity
- unbounded web crawling
- more exotic valuation methods without a clear workflow
- large schema expansions without consumption
- paid APIs simply because they are convenient

---

# 60. What Can Still Be Designed in Advance

It is acceptable to build the architecture/UI/contracts for future features when:

- data requirements are known
- the feature has strategic importance
- simulated/manual modes are safe
- labels are explicit
- it demonstrates the eventual product
- implementation does not distort current trusted workflows

Good candidates:

- market regime
- options analytics
- provider routing
- opportunity cost
- benchmark attribution
- advanced narrative views

---

# 61. UI Philosophy

The app should feel like research software.

Prefer:

- dense but readable information
- source access
- visible uncertainty
- compact cards
- tables where useful
- clear hierarchy
- drill-down
- evidence panels
- consistent badges
- keyboard-accessible workflows

Avoid:

- marketing-page styling
- decorative gradients
- giant empty cards
- unexplained gauges
- fake terminal aesthetics
- too many score dials
- excessive color
- unexplained AI output

---

# 62. Company Page Ideal Architecture

A mature company page should eventually organize around:

```text
Overview
Evidence
Financials
Thesis
Valuation
Narratives
Events
Catalysts
Decision Readiness
Research History
```

The Overview should summarize, not duplicate everything.

---

# 63. Company Overview

Potential content:

```text
Company identity
Latest price
Data freshness
Decision readiness
Key thesis
Top 3 active assumptions
Recent material events
Valuation summary
Top unresolved contradiction
Latest financial period
Portfolio ownership
```

---

# 64. Evidence-First Interaction

Any important claim should open:

```text
source
document
location
quote/context
date
claim type
review state
```

This evidence drawer is one of the most important product components.

---

# 65. Valuation UI

Retain:

```text
Story
Assumptions
Forecast
Valuation
Sensitivity
Reverse DCF
Notes
```

Potential additions later:

```text
Forecast Accuracy
Peer Set
Accounting Adjustments
History
```

---

# 66. Score Explainability UI

Every score should show:

```text
value
label
direction
confidence
formula
inputs
weights
warnings
source coverage
last updated
```

Do not hide the formula.

---

# 67. Decision Readiness UI

Prefer a checklist/gate interface over a decorative gauge.

Example:

```text
Decision Readiness: Ready With Warnings

✓ Financials reviewed
✓ Valuation reviewed
✓ Thesis exists
! Two unresolved contradictions
! Price 2 days old
✕ Latest quarter not reviewed
```

---

# 68. User Feedback Loop

The user should be able to classify:

### Alerts

- useful
- not useful
- false positive
- needs follow-up

### AI output

- useful
- unsupported
- misleading
- incomplete

### Extracted facts

- approve
- override
- reject

### Thesis contradiction

- valid contradiction
- not material
- wrong linkage
- needs follow-up

This feedback should drive later calibration.

---

# 69. Security Additions

Retain the existing threat model.

Add explicit controls for indirect AI prompt injection.

Rules:

- external document text is never instruction
- user files cannot override system policy
- model-generated text cannot authorize privileged actions
- provider/API secrets are never included in model context
- portfolio/private data transmission requires explicit disclosure
- retrieved evidence is bounded
- AI output is untrusted display text
- AI cannot silently approve its own result

---

# 70. Background Jobs

Do not rush into a complex distributed job queue.

Current synchronous processing is acceptable while local use and workload remain manageable.

Only introduce workers when there is a concrete need for:

- long-running ingestion
- retries
- scheduled work
- cancellation
- concurrency
- provider quota management

A simple local scheduler may precede Celery/Redis or other infrastructure.

---

# 71. Scheduling Strategy

Eventually classify jobs by cadence.

Example:

```text
On demand:
- company lookup
- DCF
- manual extraction

Daily:
- owned-company filings
- watchlist news
- macro refresh

Weekly:
- slow-moving industry benchmarks
- provider health audit

Monthly/quarterly:
- financial refresh
- peer review
- thesis calibration
```

This minimizes API calls.

---

# 72. API Cost Governance

Add a lightweight cost/quota monitor.

For each provider:

```text
free quota
calls used
estimated monetary cost
last reset
priority
```

Even if current cost is zero, this architecture prevents future surprise.

---

# 73. Source Coverage Declaration

Each feature should explicitly state what universe it sees.

Example:

```text
Narrative coverage:
- SEC filings: Yes
- configured RSS: 7 feeds
- X/Twitter: No
- Reddit: No
- institutional research: No
```

This prevents false confidence.

---

# 74. Research Quality Versus Source Quantity

Do not optimize for collecting maximum data.

A smaller set of high-quality sources can be more useful than thousands of low-quality articles.

Priority:

```text
official primary source
→ high-quality specialist secondary source
→ broader media
→ social
```

depending on use case.

---

# 75. Company Identity and Market Context

Continue improving market-aware identity.

Important fields:

```text
ticker
exchange
country
currency
CIK or equivalent
legal name
sector
industry
fiscal year-end
reporting currency
```

Ambiguous tickers should fail closed.

---

# 76. India Strategy

India is structurally more difficult than SEC-based US coverage.

Do not pretend otherwise.

Near-term approach:

```text
official/manual filing PDF
→ reviewed extraction
→ manual or free market data
→ Damodaran country/industry context
→ user-reviewed valuation
```

Automated NSE/BSE routing can come later.

APSEZ should remain a reference case, not proof that every India issuer is automated.

---

# 77. Damodaran Data Strategy

Continue distinguishing:

```text
canonical knowledge base
vs
runtime application data
```

Never assume a workbook existing in the mirror means the feature supports it.

Prioritize additional parsers only when a product workflow consumes the data.

---

# 78. Industry Priors

Industry benchmarks are priors.

They are not company facts.

The UI must distinguish:

```text
Company Actual
Industry Prior
Formula-Derived
User Assumption
```

at all times.

---

# 79. Research Readiness Versus Decision Readiness

These may eventually be separated.

### Research Readiness

Is the research dataset complete enough to analyze?

### Decision Readiness

Is the user sufficiently informed to revisit an investment judgment?

For now, one Decision Readiness framework is sufficient.

Avoid creating unnecessary conceptual duplication.

---

# 80. Catalysts

Catalyst tracking should eventually support:

```text
earnings
investor days
regulatory decisions
debt maturities
project milestones
capital allocation
court cases
product launches
macro events
```

If automated calendars are unavailable, manual catalysts are entirely acceptable.

---

# 81. Variant Perception

The system already has a variant-perception domain.

Make it useful.

A variant perception should state:

```text
Consensus belief
User belief
Why different
Evidence
What market may be missing
What would prove the user wrong
Time horizon
```

Do not turn it into generic notes.

---

# 82. Pre-Mortem

For major positions, allow:

```text
Imagine this investment loses 40%.
What probably happened?
```

Store structured risks.

Later compare realized outcomes.

---

# 83. Falsification

Every high-importance thesis should eventually have falsification criteria.

Example:

```text
Thesis:
Margin expansion will drive value.

Falsification:
EBIT margin remains below 18% for two consecutive reported periods despite volume growth.
```

This makes contradiction detection far more useful.

---

# 84. Evidence Aging

Not all evidence remains equally relevant.

Consider evidence states:

```text
Current
Aging
Superseded
Contradicted
Historical
```

New filings should be able to supersede old operating facts without deleting history.

---

# 85. Data Versioning

Preserve versions for:

- financial facts
- Damodaran datasets
- valuation assumptions
- model outputs
- thesis assumptions
- provider observations

Do not silently overwrite the past.

---

# 86. Historical Research Replay

Long-term:

Allow a user to inspect:

```text
What did the app know on this date?
What was my thesis?
What was my valuation?
What evidence existed?
What price existed?
```

This is extremely useful for calibration.

---

# 87. Quality Gates Before a Feature Is "Built"

A feature should not be labeled Built merely because:

- a database model exists
- a route exists
- UI is visible
- one test passes

Built should mean:

- real persisted behavior
- ownership correct
- trust state correct
- data states correct
- meaningful tests
- user workflow usable

---

# 88. Quality Gates Before "Decision-Grade"

A feature should not be called decision-grade until:

- source reliability known
- freshness known
- failure states visible
- evaluation exists
- broad enough real-world validation exists
- no hidden mock paths
- user review rules clear

---

# 89. Coding Agent Standard Workflow

For every task:

## Step 1

Read:

```text
HANDOFF
current state
architecture
relevant core doc
```

## Step 2

Inspect actual code and tests.

## Step 3

State:

```text
Task
Plan
Files likely to change
Risks
```

## Step 4

Add or update tests first where practical.

## Step 5

Implement smallest safe change.

## Step 6

Run focused tests.

## Step 7

Run broader baseline when warranted.

## Step 8

Update only the current documentation whose truth changed.

## Step 9

Report:

```text
Files changed
Tests run
Manual checks
Known limitations
Feature maturity change
Next recommended task
```

---

# 90. Agent Stop Conditions

Stop and report if:

- migration chain is broken
- destructive migration required
- provider licensing unclear
- secret would be exposed
- mock data would appear real
- ownership boundary is unclear
- source cannot be verified
- data needs to be silently fabricated
- requested feature requires public deployment security
- unrelated tests fail
- code/docs strongly contradict
- implementation would exceed intended scope without clear reason

---

# 91. Do Not Overbuild

If a requested feature can be implemented with:

```text
one table
one service
one route
one UI
```

do not create:

```text
eight abstractions
four queues
a plugin framework
two new databases
```

Complexity must be earned.

---

# 92. Database Discipline

Before adding a model ask:

> What live workflow consumes this model now?

If the answer is:

> maybe later

do not add it yet unless it is an intentionally approved schema foundation.

---

# 93. Test Strategy

Maintain layers:

## Unit

Deterministic formulas and utilities.

## Service

Business workflow behavior.

## API

Auth, ownership, response contracts.

## Migration

Head and upgrade behavior.

## Browser

Representative user workflows.

## Evaluation

Research quality.

Do not confuse them.

---

# 94. Documentation Strategy

Keep current docs compact.

Move:

- historical evidence
- old plans
- implementation narratives
- dated audits

to archive.

A current document should answer:

> What is true now?

not:

> What happened over the last 39 phases?

---

# 95. Documentation Checker Expansion

Consider adding automated checks for:

- duplicate canonical facts
- stale migration-head references
- retired environment variables
- old route names
- invalid current-doc links
- prohibited archived references in current instructions

---

# 96. Recommended Immediate Task Order

The next practical sequence should be:

## Task 1: Repository truth reconciliation

Fix known documentation/config inconsistencies.

## Task 2: Assumption methodology integrity

Remove trusted hardcoded market assumption fallbacks.

## Task 3: Core frontend truth audit

Prioritize:

```text
Dashboard
Companies
Company Overview
Filings
Financials
Valuation
Portfolio
Data Health
```

## Task 4: Decision Readiness foundation

Implement deterministic readiness model and UI.

## Task 5: Scoring audit

Keep scoring framework, verify formulas, explainability, and score/readiness separation.

## Task 6: Financial extraction evaluation harness

Build golden issuer evaluation.

## Task 7: Add another heterogeneous real issuer

Do not simply choose another easy US tech company.

## Task 8: Valuation reproducibility

Ensure complete snapshot replay.

## Task 9: Reviewed peer-set relative valuation

## Task 10: Thesis assumption and falsification workflow

## Task 11: Contradiction and confirmation quality

## Task 12: Portfolio performance and attribution

## Task 13: Research evaluation dashboard

## Task 14: AI citation and claim evaluation

## Task 15: Narrative maturity

## Task 16: Market Regime prototype completion

Make manual/simulated/source modes explicit.

## Task 17: Provider expansion as justified

Do not buy data prematurely.

## Task 18: Morning Briefing

Only now combine the modules.

## Task 19: Forecast calibration and decision-history review

This may also be advanced earlier if convenient because its data model is highly valuable.

---

# 97. What Success Looks Like Before Morning Briefing

Before Morning Briefing becomes the priority, the system should be able to do the following for a representative company:

1. identify the company correctly
2. ingest or upload official evidence
3. extract financial candidates
4. allow exact evidence review
5. normalize reviewed facts
6. reconcile the history
7. create a valuation
8. trace assumptions
9. run sensitivity and reverse DCF
10. record thesis assumptions
11. define falsification criteria
12. ingest new evidence
13. score the event
14. connect it to the thesis
15. identify contradiction/confirmation
16. show Decision Readiness
17. show portfolio exposure
18. preserve the decision/history
19. measure whether the system got the facts right

If that works, Morning Briefing becomes aggregation rather than invention.

---

# 98. Product Showcase Strategy

The system can already become an unusually strong portfolio project.

A strong demonstration should show three classes of capability.

## Live / operational

Examples:

- source-backed financial extraction
- evidence viewer
- reviewed DCF
- portfolio
- thesis tracking

## Manual but functional

Examples:

- certain macro inputs
- catalyst calendar
- some market-regime inputs

## Concept / prototype

Examples:

- advanced options regime
- institutional flow
- premium-provider narrative coverage

The demo should state this openly.

That makes the architecture more credible, not less.

---

# 99. Funding / Resource Unlock Narrative

If showing the product to someone who may fund data access, demonstrate:

```text
This is what works today.
This is what uses free/public data.
This is what requires manual input.
This is what is simulated.
This is the provider interface already prepared.
This is the exact additional capability that paid data would unlock.
```

That is more convincing than silently faking completeness.

---

# 100. Example Data Upgrade Map

```text
Market Regime

Today:
Manual + simulated options inputs

With free provider:
Real VIX + OHLCV + credit spreads

With options-chain access:
Real put-call, skew, open interest, IV

With premium institutional flow:
Flow/liquidity module becomes source-backed
```

This makes funding requirements concrete.

---

# 101. Avoid Vendor Lock-In

Paid providers should be adapters.

The system should own:

- normalization
- provenance
- scoring
- valuation logic
- user data
- history

The provider supplies observations.

Do not make core logic depend on vendor-specific response shapes.

---

# 102. Data Licensing Awareness

Before integrating any provider:

Record:

```text
provider
terms URL or reference
personal/commercial status
storage rights
redistribution rights
rate limits
attribution requirements
last reviewed
```

A personal local app has different constraints than a funded public product.

Keep this visible.

---

# 103. API Errors Are Product States

If a provider fails:

Bad:

```text
0.00
```

Good:

```text
Provider unavailable.
Last good value: 2026-08-07.
Status: Stale.
```

---

# 104. Missing Data Should Reduce Confidence

Missing data should affect:

- Confidence Score
- Decision Readiness
- Data Health

It should not necessarily force the entire product to fail.

Example:

```text
Market Regime unavailable
```

does not make the DCF unusable.

Keep domain boundaries.

---

# 105. Prototype Data Must Not Affect Trusted Composites

If:

```text
Options module = simulated
```

then:

```text
Market Regime Composite = Prototype
```

Do not combine four real modules and one fake module and label the result Live.

---

# 106. Score Confidence

Every composite score should have confidence separate from value.

Example:

```text
Narrative Score: 72
Confidence: Low
Reason:
Coverage only includes 5 RSS feeds and filings.
```

This is essential.

---

# 107. Readiness Is Not Confidence

Confidence asks:

> How reliable is the signal?

Readiness asks:

> Is enough of the research process complete?

Example:

```text
High confidence in current financial facts
but
Decision Readiness incomplete because no current valuation exists.
```

---

# 108. Portfolio and Thesis Privacy

Keep private data local by default.

If future external AI calls use:

- portfolio holdings
- thesis notes
- valuation assumptions

require explicit disclosure and audit metadata.

---

# 109. Public Deployment

Remain localhost-first.

Do not spend development time on production deployment until there is a real reason.

Before public deployment:

- production identity
- authorization audit
- HTTPS
- secure secret management
- CSRF review
- CORS hardening
- rate limiting
- audit logs
- backup strategy
- privacy policy
- data licensing review
- AI transmission controls

---

# 110. Final Build Philosophy

The project should evolve according to five principles.

## Principle 1: Truth before polish

A rough screen with honest data is better than a beautiful screen with uncertain data.

## Principle 2: Completion before expansion

Finish workflows before creating more modules.

## Principle 3: Manual is acceptable

If high-quality live data is unavailable, use explicit manual input rather than fake automation.

## Principle 4: Prototype honestly

If a strategically important feature requires unaffordable data, build the product logic and demonstrate it with clearly isolated simulated inputs.

## Principle 5: Measure quality

Software tests are necessary but not sufficient.

Build research evaluations.

---

# 111. The Product End State

The mature system should allow a user to answer:

```text
What happened?
What source proves it?
How important is it?
What does it contradict?
What does it confirm?
What assumption might change?
What happens to valuation?
What is my portfolio exposure?
How ready am I to form a judgment?
What do I still not know?
What did I previously believe?
Was I right?
```

If the system reliably does that, it will be substantially more valuable than a generic AI investment dashboard.

---

# 112. Agent Final Directive

For future work, agents must optimize for:

```text
trust
reproducibility
source quality
workflow completion
explainability
evaluation
cost awareness
user review
modularity
honest product demonstration
```

Agents must not optimize for:

```text
number of features
number of models
number of database tables
visual impressiveness
fake real-time behavior
unsupported automation
opaque intelligence scores
```

The default question before building anything should be:

> Does this make one existing investment-research workflow materially more complete, trustworthy, or useful?

If yes, proceed.

If not, defer it unless the user explicitly wants a concept/prototype demonstration.

---

# 113. Required Agent Completion Report

At the end of every meaningful task, report:

```text
Objective
What changed
Why it changed
Files changed
Tests run
Browser/manual checks
Data/source modes affected
Trust-state changes
Feature maturity before
Feature maturity after
Known limitations
New technical debt
Documentation updated
Next recommended task
```

Never write:

```text
Fully complete
Production ready
Decision-grade
Source-backed
```

unless the evidence actually supports the claim.

---

# 114. Immediate First Instruction to the Next Agent

Start with repository truth reconciliation.

Specifically:

1. Verify the actual Alembic head from code/runtime.
2. Reconcile all current docs that state the migration head.
3. Verify current backend/frontend API URL configuration.
4. Verify canonical health endpoints.
5. Reconcile feature status terminology.
6. Inspect root `AGENTS.md` precedence wording.
7. Identify other mutable facts duplicated across current docs.
8. Reduce duplication by assigning each mutable fact one canonical owner.
9. Run documentation checks.
10. Do not change product behavior unless required to correct an actual implementation inconsistency.

Then proceed to the assumption-methodology fallback cleanup.

Do not start a new major feature until those two integrity tasks are complete.
