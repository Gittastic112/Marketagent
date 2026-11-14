# Research workspace implementation plan

Design baseline and first implementation: November 13, 2026. This is the detailed
design and delivery specification for simplifying the existing local app. After
the user authorised implementation, P0 was verified and P1 was installed with
[recorded evidence](../../data/reviews/research-workspace-p1-20261113.json).
November 14 adds [ten bounded P2-P5 slices](../../data/reviews/research-workspace-ten-sets-20261114.json).
Remaining package acceptance and P6/P7 work are open. This does not establish complete
financial inputs, personal acceptance or research-use days. Essential-only storage applies.

## Read this plan

- [Scope and decisions](#scope-and-decisions): what this release is for.
- [Navigation and feature placement](#navigation-and-feature-placement): where everything belongs.
- [Screen specifications](#screen-specifications): content, layout, actions and states.
- [Connected workflows](#connected-workflows): how research becomes a reviewed model update.
- [Data and backend design](#data-and-backend-design): identity, dates, contracts and safe writes.
- [Interface rules](#interface-rules): presentation, accessibility and recovery.
- [Delivery sequence](#delivery-sequence): ordered, bounded implementation packages.
- [Acceptance matrix](#acceptance-matrix): evidence required to call the work done.
- [Storage and operating discipline](#storage-and-operating-discipline): essential retention.
- [Managing the work](#managing-the-work): status, decisions, handoffs and change control.
- [Next implementation session](#next-implementation-session): the first concrete actions.

The [roadmap](product-roadmap.md) owns priority. This plan owns target behavior and
implementation packages. [Limitations](../limitations.md#workspace-follow-up)
owns current gaps, [Current State](../current-state.md) owns verified behavior,
and the [completion tracker](completion-tracker.md) owns release acceptance.
The existing [code map](../code-map.md) remains the implementation index.
Do not maintain a second completion percentage in this plan.

## Scope and decisions

### Product outcome

The researcher should be able to open the app, understand what requires attention,
inspect the source, update a thesis or financial input, review the valuation effect,
save a version, and see relevant portfolio exposure without reconstructing the
relationships across unrelated pages.

The existing four companies are the working scope: Apple, NVIDIA, Meta and
Alphabet. Existing hypothetical portfolios and Sample research remain examples.
The sourced Apple model remains a separate Estimate. Nothing in this plan restores
the removed company universe, invents transactions, or grants external AI access.
Existing US/India manual research capabilities stay available; new issuer intake
and provider expansion are separate scope decisions.

The November 12, 2026 valuation date belongs to the current selected-company
review. It is not a global default for all future research. Opening an old model
must preserve its original basis. New research chooses its own explicit date.

### Design decisions for implementation

These are working design decisions made for this plan. They can be revised from
observed use; they are not recorded as personal user approval of financial inputs.

| ID | Decision | Reason and boundary |
|---|---|---|
| D01 | Four primary areas: Today, Companies, Valuations, Portfolio | Organise around tasks. Library, Advanced and Settings remain secondary entry points |
| D02 | Five company sections: Overview, Financials, Thesis, Valuation, Sources | Consolidate related work; preserve all existing deep links and records |
| D03 | Lead with summaries and next actions; reveal evidence on demand | Keep important dates, missing-input blockers and claim types visible without printing entire notes |
| D04 | One financial input view per selected basis | Show sourced values, calculations, assumptions, conflicts and missing values together; do not flatten their differences |
| D05 | Reads do not create or refresh research objects | Draft creation, refresh, review, calculation and save become explicit actions |
| D06 | Existing domain objects remain authoritative | Assemble a review queue from existing records before adding a general task system |
| D07 | Every saved model version retains its basis | New evidence creates a proposed update; it does not silently rewrite past outputs |
| D08 | Example context is filterable and visibly labeled | Preserve existing examples and original facts; never infer real/mock status solely from a title |
| D09 | Storage follows the bounded policy in Operations | No per-task database dumps, permanent rollback stacks or copied evidence bundles by default |
| D10 | Deliver small usable slices on the existing installation | Use the current Compose project, additive compatible changes and scoped checks |

### Non-goals for this pass

No broker integration, execution, buy/sell recommendations, public hosting,
licensed-feed purchase, comprehensive live news promise, broad OCR project,
semantic search platform, new valuation engine, generic workflow platform, or
infrastructure rewrite. Existing specialist calculations remain available under
their actual limitations. Their visibility depends on relevance and support.

Do not remove a supported capability merely to make navigation shorter. Move it
to the right context and preserve a discoverable path. Do not fill blank panels
with generated business claims or placeholder finance values.

## Navigation and feature placement

### Global shell

| Destination | Main question | Initial route strategy |
|---|---|---|
| Today | What needs my attention, and what changed? | Use the existing home route; Daily Brief and Alerts become views reached from it |
| Companies | What am I researching, and where did I leave off? | Keep the existing company list and company URLs |
| Valuations | Which models exist, what basis do they use, and what needs review? | Keep the cross-company valuation list; a model opens its company context |
| Portfolio | What do I hold or model, and where is the exposure? | Keep portfolio routes and their explicit activity basis |
| Library, secondary | Where are my sources, notes and past sessions? | Reuse research, documents, thesis-note and search routes |
| Advanced, secondary | Which specialist tools are available? | Group macro, regime, evaluation and specialist valuation entry points |
| Settings, secondary | Are sources and local services configured? | Group settings, source administration, ingestion and data health |

The top bar contains search and a concise status link. Show an attention marker
when a relevant failure exists, with a text explanation available. A green global
badge must never imply that every company fact or model is verified.

Keep the sidebar stable across screens. On mobile, use the existing accessible
drawer with the same destinations. Keep focus trapping, Escape, active location
and focus return. Do not add a second independent mobile navigation model.

### Company workspace

| Section | Contains | Existing destinations retained |
|---|---|---|
| Overview | Business context, key trends, thesis summary, model status, next reviews | Company overview |
| Financials | Reviewed history, source candidates, gaps, period/basis selection | Fundamentals and document financial-evidence views |
| Thesis | Selected thesis, supporting/opposing evidence, questions and decision history | Thesis, thesis-note detail and decisions |
| Valuation | Saved models, drafts, assumptions, scenarios and relevant peers | Model list/detail, draft and peers |
| Sources | Filings, uploads, passages and source history | Filings, evidence, document sections and source-specific detail |

Company setup moves into a company menu labeled "Company details". Peer comparison
is a valuation subview. Decisions are a thesis subview. Opening a section preserves
company identity, selected basis and a clear return path.

### Existing capability disposition

| Existing area | Treatment in the new structure |
|---|---|
| Dashboard, Daily Brief, Alerts | Today owns prioritisation; saved briefs and alert details remain linked views |
| Events, Narratives, Contradictions | Research evidence and review views under Today, Thesis or Library; wording states whether a contradiction is only proposed |
| Research and research sessions | Library retains cross-company work; company pages link relevant sessions |
| Thesis notebook and Decisions | Thesis owns narrative and decisions; cross-company note search remains in Library |
| Documents, Filings, Evidence | Sources within a company, plus global Library; the document has one authoritative identity |
| Ingestion, Sources, Data Health | Source management in Settings; relevant failures also surface beside affected work |
| Evaluations and benchmark administration | Advanced/Settings, with purpose and current scope explained |
| Macro and Market Regime | Advanced and relevant portfolio/model links; unsupported factors remain unavailable |
| Quick valuation | Optional valuation shortcut with the same required-input and provenance gates |
| FCFE/DDM, bank, distressed, options | Show only for an applicable model and supported input set; preserve experimental labels |
| Social route and unavailable providers | Preserve compatibility entry points with truthful unavailable states; do not promote them as daily features |
| Price history | Reach from company quote or Portfolio; keep provider, currency and date visible |
| Authentication and private-source detail | Keep existing identity, ownership and consent boundaries |

Use label and placement changes first. Avoid route renames in the first slice.
If later consolidation needs redirects, inventory current links, query parameters,
anchors, exports and browser tests before changing them. A hidden navigation item
must still have a contextual or secondary entry point. Update the
[route inventory](../route-inventory.md) only when routes actually change.

## Screen specifications

These are structural wireframes, not screenshots or invented financial results.
Reuse the existing restrained visual system and components. Layout changes are
subordinate to readable evidence, useful actions and truthful states.

### Today

~~~text
Today                         Research scope / date window     Search
Source status: last success, relevant failure or incomplete coverage

Needs review                                  Continue research
Company | reason | affected work | action      Most recent unfinished work
Blocking issues first, then changed evidence   Resume / inspect

What changed
Grouped source changes with publication date, retrieval date and exact links
Each item: what changed / why it might matter / current review state

Portfolio context, when selected
Exposure linked to these companies; snapshot basis and example label

Saved briefs / completed reviews / coverage details
~~~

The primary action is "Review next item" when actionable work exists; otherwise
"Continue research" or "Open companies". It must lead to a concrete record.
Show a bounded initial list with total counts and "View all". Group related events
by company/source identity; do not silently merge differing claims or review states.
Ordering starts with explicit blockers, failed refreshes affecting current work,
new material sources, then ordinary unread material. Existing scores can explain
ordering but must not be relabeled as objective investment importance.

Coverage is one compact line with expandable window, caps, exclusions and failures.
No new events means "No new stored events in this window", not "Nothing happened".
Unknown coverage remains unknown. A sample portfolio must not dominate the page
when the user is doing company research. Portfolio context is optional and scoped.

### Companies

Use a compact list/table rather than large repeated information cards. Each row:
company/security, selected annual basis, financial review status, latest model
date/status, source freshness and one next action. Sorting and filters should
answer "needs review", "has a model", "missing sources" and "recently worked on".
These are separate statuses, not a fabricated completeness percentage.

Keep existing company intake as an explicit action. Do not add companies merely
to fill the screen. Empty state explains how to add an authorised company/source.
Search remains useful with four companies without requiring a new search engine.

### Company overview

~~~text
Company / security / currency       Stored quote + quote date     Company menu
Overview | Financials | Thesis | Valuation | Sources

Research status and the next unresolved action

Business in brief                   Current valuation
Reviewed summary or bounded         Saved estimate / basis / status
filing excerpt with source          Open model / review missing inputs

Financial trends
Comparable periods, sensible units, readable table and limited useful charts

Current thesis                      Needs review
Main view / counter-case             Named source or input gaps
What would change the view           Resume exact review step

Recent sources and decisions         Links to full notes and history
~~~

The first desktop viewport should identify the business, research status and next
action. Do not put a full filing section, complete research memo or hash table in
that space. Initially use an attributed excerpt where a reviewed business summary
does not exist; do not present a parser excerpt as curated analysis.

Select trend metrics from actually supported compatible inputs: revenue, operating
profit/margin, cash generation, reinvestment and financing where available. Do not
keep permanently empty columns solely because a generic company template has them.
Required missing inputs still appear in a visible gaps list with a resolution link.
Changing display units never changes stored units. Comparability and source basis
must be inspectable for each period; do not connect incompatible periods in a chart.

Show a short thesis summary and links to complete notes. Multiple active notes need
an explicit selected primary thesis or a visible chooser. Do not assume the first
returned active note is the user's intended thesis. Keep supplemental research and
the dated financial review accessible alongside the main thesis.

### Financials and input review

~~~text
Financials    Annual / interim basis    Period    Currency    Valuation date
Readiness for selected method: ready / review required / blocked

Input                    Selected value   Basis/date    Review state    Action
Revenue / operating ...  original units   source        reviewed        Inspect
Financing components     scoped subtotal  source        incomplete      Resolve
Missing required input   unavailable      reason        blocked         Find source

Selected row detail
Exact passage/table | original amount | conversion/calculation | source history
Use sourced value / record an assumption / keep unresolved / reject candidate

Review proposed model changes                 Save draft / return to model
~~~

Separate annual, quarter-only, year-to-date and point-in-time facts. Do not turn
partial-year figures into annual facts. A date selector changes the selected basis,
not source values or past model versions. Show fiscal period end separately from
filing publication, retrieval, quote date and valuation date.

Each applicable input must say whether it is a Fact, Calculation, Source Summary,
User Assumption or Estimate, with a source/reason. A candidate remains unreviewed
until the existing review action passes. Required unresolved rows are visible even
when no value exists. Optional method inputs may be collapsed and labeled optional.

Offer a reviewed sourced value and a manual assumption as different actions. A
manual assumption must not overwrite the original fact. Show the economic scope
of debt, leases, cash, minority/preferred claims, employee awards and shares. An
incomplete financing subtotal is not a complete total-debt input. Show the exact
missing component or reconciliation, not a generic "data incomplete" banner.

The [selected-company ledger](../limitations.md#selected-company-review-follow-up)
owns company-specific unresolved facts. Reuse the existing dated review notes and
receipts as evidence; do not ingest duplicates or parse prose into approved values.
Working capital, reinvestment and award treatment remain method-specific. Avoid
counting the same economic claim in both the equity bridge and share dilution.

### Thesis and decisions

Lead with a selected thesis, its date/status and three readable blocks: main view,
counter-case, and what would change the view. Structured assumptions retain
importance, confidence and falsification criteria in an expandable table.
Supporting and opposing evidence link to exact sources and their review state.
"No linked evidence" must not imply that evidence does not exist.

Provide an explicit note selector and a list of supplemental notes. Editing a
thesis retains version/context and does not silently select a different active note.
Decision history records what changed, why, which evidence was used and the next
review trigger. An AI-proposed contradiction stays a proposal until reviewed.
Optional AI retains its existing disclosure and permission check at execution.

### Valuations list and saved model

The global list shows company, model type, valuation date, source basis, last saved
version, estimate state and unresolved blockers. Separate a saved result from a
draft and from a successful calculation awaiting review. A saved number alone is
not evidence of source completeness or an approved investment conclusion.

The company valuation page starts with existing models and resumable drafts.
Industry allocation, benchmark administration and peer setup move below the main
workflow or into relevant advanced sections. They must not hide the saved model.

~~~text
Model / company / valuation date / saved version       Edit assumptions
Basis summary and any blocking diagnostic

Estimate and comparison price, each with its own date and classification
Scenario range and the assumptions producing it

What drives the result               What needs attention
Growth / margins / reinvestment       Missing basis / old sources / model warnings
Discounting / terminal dependence    Explicit review actions

Inputs | Scenarios | Sources and history | Advanced
Export a memo from this exact saved version
~~~

Explain uncertainty through assumptions, sensitivities and source gaps. A scenario
range is not a probability interval. Keep intrinsic value separate from the market
comparison price. Show terminal dependence, currency, equity-bridge basis and share
scope without forcing the user to inspect every technical diagnostic first.
Blocking problems stay visible beside the affected result and withhold it where
required. Keep historical results labeled historical rather than recalculating on read.

### Creating or updating a valuation

Use one resumable sequence with a visible step list, no forced long wizard for
routine edits, and links directly to unresolved fields:

1. **Choose basis:** company/security, method, valuation date, reporting currency,
   financial periods and comparison quote. Explain applicable methods briefly.
2. **Review facts:** sourced actuals, financing and equity claims; inspect conflicts.
3. **Set assumptions:** growth, margins, reinvestment, discounting and terminal basis.
   Defaults carry their original classification and rationale; they are not facts.
4. **Compare changes:** old/new inputs, affected sources, diagnostics and a calculation
   preview. State whether each result uses saved or unsaved values.
5. **Save a version:** explicit action with current-version validation and a reason.
   Return to the saved model with its evidence and the next review item.

Existing review controls should be grouped by meaningful sections. Bulk acceptance
must list exactly what will be accepted and exclude missing, conflicting or invalid
required values. A collapsed section must not hide a blocking field.
Draft edits can be saved while incomplete; calculation/publication eligibility is
checked separately. Error recovery preserves entered values and explains retry.

Source refresh, draft creation, source review, model calculation and save are
different actions. A double click or retry must not create duplicate models/versions.
Navigating to the draft URL must not create or refresh a persisted draft. Use an
explicit create/resume action and a read-only retrieval path.

### Portfolio

Keep a clear portfolio selector and a persistent Example/Mock Data label where
applicable. Show value, cash, holdings, concentration, performance basis and date.
Performance and fixed-weight price risk have different labels and explanations.
Missing prices, FX or activity history remain visible and prevent false precision.

Add research context through existing company/security links: which holdings have
new sources, unresolved thesis reviews or old model assumptions. A company update
does not imply a portfolio return or trade instruction. Exposure values are computed
from the selected holdings snapshot, not from research importance scores.
Never create trades, dividends or cash movements to demonstrate the redesigned UI.

### Library, source detail and settings

Library provides company/type/date/review-state filters, bounded pagination and
search over stored material. Preserve private/public ownership and source kind.
One document detail contains original-source access, exact passages, financial
candidates, related research and processing status. The original source remains
accessible when parsing has not completed or failed. Hashes and parser metadata
belong in technical details.

Settings separates source configuration, processing history, local service status
and AI permissions. Show configured, reachable, latest success, current coverage and
last failure as distinct facts. Enabling a provider does not certify its data.
Explain external AI disclosure immediately before the relevant action; no hidden
AI calls for summaries, sorting or navigation. System controls are secondary to
research but remain accessible when an error points there.

## Connected workflows

### Normal research loop

```mermaid
flowchart LR
    T[Today review item] --> S[Exact source]
    S --> R[Review fact or interpretation]
    R --> H[Thesis or financial basis]
    H --> D[Proposed valuation changes]
    D --> V[Save reviewed version]
    V --> P[Related portfolio exposure]
    P --> N[Record next review trigger]
```

Every transition preserves company/security identity, relevant date, source IDs and
the return location. Research items may legitimately end with "No model change",
"Source needed" or "Not applicable", with a reason. A completed interpretation
review does not automatically complete financial review or model approval.

### Workflow contracts

| Trigger | Required path | Completion condition |
|---|---|---|
| New filing | Source intake/run -> exact document -> candidates or research task | Source retained once; changes reviewed or explicitly left unresolved |
| Changed financial figure | Candidate/revision -> original evidence -> selected basis -> draft diff | Review receipt and a distinct model update decision |
| New thesis evidence | Passage -> support/opposition/uncertain classification -> thesis review | Rationale saved; model relevance recorded without automatic forecast edits |
| Continue a model | Existing draft/version -> unresolved section -> preview -> save | One new version or an unchanged draft with a clear blocker |
| Refresh failure | Failure reason -> retry/configuration action -> run status | Success with coverage metadata, or a retained actionable failure |
| Research completed | Changed/no-change decision -> next review trigger | Item leaves actionable queue only when its underlying state permits it |
| Revisit old analysis | Historical version -> original facts/assumptions -> optional new draft | Old version unchanged; new basis explicit |

### Review queue design

First implement a bounded, owner-aware projection over existing alerts, financial
gaps/candidates, private review states, source failures and valuation drafts. Keep
the original object as the source of truth. Use a stable composite identity such
as domain + record + relevant revision for deduplication and links.

A queue row needs: company/security, reason, origin reference, relevant date,
affected work, severity basis, current state, next action and permission scope.
Counts and ordering come from the backend. Frontend labels do not manufacture
workflow state. Do not create a second copy of each source payload for the queue.

Suggested display states are Needs review, Waiting for source, In progress and
Resolved. Map them from the authoritative domain state. If dismissal/snoozing is
needed later, add only owner-scoped metadata with an explicit reason and revision;
it must not approve or delete the underlying fact. A newly revised source can reopen
an item. A source still unavailable is not completed work.

## Data and backend design

### Reuse and ownership

Keep Next.js/FastAPI/PostgreSQL and the current domain structure. HTTP routes
validate and authorise; services own workflows/calculations; models own persistence;
frontend components present data and collect explicit decisions. Use existing
response envelopes, source revisions, Processing Runs and optimistic version checks.
The [architecture](../architecture.md) owns present runtime boundaries.

| Work | Existing owners to inspect and extend |
|---|---|
| Shell and company views | [Sidebar](../../frontend/components/sidebar.tsx), [company tabs](../../frontend/components/company-tabs.tsx), [overview](../../frontend/app/companies/[id]/page.tsx), [research read service](../../backend/app/services/company_research.py) |
| Financial identity/review | [Models](../../backend/app/models/financial.py), [promotion](../../backend/app/services/financial_extraction.py), [review planner](../../backend/app/services/financial_review_plan.py), [source history](../../backend/app/services/source_fact_history.py) |
| Dated model inputs | [Actuals selection](../../backend/app/services/assumption_financial_inputs.py), [draft service](../../backend/app/services/valuation_setup_draft.py), [unit policy](../../backend/app/services/valuation_input_units.py), [draft UI](../../frontend/components/valuation/autofill-draft-review.tsx) |
| Explicit draft lifecycle | [Draft page](../../frontend/app/companies/[id]/valuation/draft/page.tsx), [draft client](../../frontend/lib/api/valuation-drafts.ts), [draft service](../../backend/app/services/valuation_setup_draft.py) |
| Today and review flow | [Home page](../../frontend/app/page.tsx), [brief engine](../../backend/app/services/morning_briefing_engine.py), [brief coverage](../../backend/app/services/brief_public_coverage.py), [research models](../../backend/app/models/research.py) |
| Provider operation | [Refresh service](../../backend/app/services/valuation_source_refresh.py), [worker](../../backend/app/workers/valuation_source_scheduler.py), [provider health](../../backend/app/services/provider_health.py) |
| Portfolio linkage | [Portfolio router](../../backend/app/api/routers/portfolios.py), [valuation](../../backend/app/services/portfolio_valuation.py), [risk](../../backend/app/services/portfolio_risk_return.py), [overview UI](../../frontend/components/portfolio/overview.tsx) |
| Contract stability | [Schemas](../../backend/app/schemas/), [domain clients](../../frontend/lib/api/), [contract checks](../../scripts/check_api_contracts.py) |

Inspect each affected route, schema, caller, model, migration and existing test
before implementation. These are entry points, not an instruction to edit every
listed file. Do not move large modules merely because this plan mentions them.

### Financial period identity

Treat fiscal label, period start/end, duration type and instant date as distinct
information. Annual, quarter-only and year-to-date facts must not share a storage
identity merely because fiscal year and period_type match. Source locator/context
must support the identity; missing dates remain unresolved.

Start with a regression that shows two different quarterly periods cannot collide,
replace one another or be treated as conflicting versions of the same fact. Until
the complete path supports precise periods, reject ambiguous promotion explicitly.
Do not infer a quarter from a filing month or invent a December year end.

Then design an additive migration only if needed: inspect current rows, classify
known/unknown identity, preserve old IDs/source revisions, backfill only directly
supported fields, and introduce constraints after ambiguity is resolved. Retain
read compatibility for historical annual records. Do not merge old periods or
rewrite saved model bases automatically. Database-specific constraints require
the authorised validation environment; a normal database is never a test fixture.

### Issuer and security identity

Separate issuer-level reports from security-level quotes, share classes, holdings
and valuation outputs. First enforce consistent issuer/security references and
reject an incompatible quote/share basis using current models. A complete issuer
table migration is a later bounded package if current identity cannot support the
selected securities safely; it is not a prerequisite for the first UI slice.

Any migration must preserve company IDs/URLs, source links, model ownership and
holdings. Specify the compatibility mapping and unresolved class-share cases before
adding uniqueness constraints. Do not create extra companies to work around a
constraint or reinterpret preferred depositary interests as common shares.

### Dated financial basis

A valuation basis must distinguish: valuation date, financial period start/end,
source publication date, retrieval date, quote date/session and review timestamp.
For historical research, distinguish "information publicly available by that date"
from "later restated knowledge about that period". Retrieval after the valuation
date is acceptable only when publication availability supports the selected basis.
Do not claim full point-in-time reconstruction without source vintages.

Extend the existing provenance contract only where fields are absent. The minimum
reviewable input shape is conceptually:

~~~json
{
  "metric": "existing metric identifier",
  "value": null,
  "currency": "explicit or unavailable",
  "unit_and_scale": "original and normalized basis",
  "period": "start/end or instant, with annual/quarter/YTD scope",
  "valuation_date": "selected research date",
  "claim_type": "Fact / Calculation / User Assumption / Estimate",
  "source_refs": ["document, locator, revision and publication date"],
  "review": "state, actor, time, reason and reviewed revision",
  "limitations": ["named missing scope or unresolved conflict"]
}
~~~

This is a design checklist, not an implemented API payload or proposed replacement
for every existing schema. Reuse current field names and model-specific contracts.
Preserve raw values and explicit conversions. Store references to original sources,
not repeated full documents in each model or queue row.

### Read, draft and save boundaries

1. Read endpoints/pages only retrieve data. They do not create drafts, approve
   evidence, refresh providers, calculate-and-save, or alter historical results.
2. Explicit draft creation selects a basis and returns a stable owned draft.
   Resume retrieves it. Refresh is a separate auditable action preserving edits.
3. Input changes invalidate only affected review acknowledgements and downstream
   diagnostics. Maintain exact source/method/version signatures.
4. Preview returns proposed changes and diagnostics without changing saved models.
   Distinguish unsaved previews visibly and discard them when their basis changes.
5. Save checks ownership, current version, required inputs and source signatures;
   writes atomically; records the new version; preserves the previous one.
6. Duplicate submissions reuse the same successful outcome or report the existing
   version. A stale write returns a conflict and preserves the user's pending edits.

Missing required shares or claims cannot be replaced by a hidden default just to
display a result. Explicit zero remains valid where evidence or a declared
assumption supports it. Check every output surface, scenario and export against
the same backend eligibility result.

### Refresh reliability

Extend the existing queue/worker, not a new scheduler stack. Add bounded retries
only for classified transient failures, with attempt count, next retry time and
provider limits. Configuration, permission and invalid-data failures need an
explicit remedy; do not hammer providers or silently retry external AI.

Expose worker last-seen status and job state separately from source freshness.
On restart, mark interrupted work truthfully, avoid duplicate imports and offer a
bounded catch-up plan. Do not invent missed historical observations or start an
unbounded date backfill. Keep cancellation and retry history. Workers remain
opt-in; this plan does not enable a disabled worker or create a scheduled task.

### Contracts and performance

Add backend-owned read projections only when existing endpoints cannot return
the page's required data efficiently. Avoid one request per table row, loading
entire note bodies on summary pages, or repeatedly fetching binary documents.
Use bounded lists, server-side filters, explicit totals/limits and lazy advanced
panels. Preserve request isolation when switching company, portfolio or date.

Pilot schema-derived frontend types in one touched financial domain after its
contract stabilises. Preserve envelope aliases and historical response assembly.
Do not perform a repository-wide client rewrite. Keep existing query-budget and
ownership tests. Measure representative local page/API timings before setting
performance claims; targets are acceptance criteria, not current achievements.

## Interface rules

### Hierarchy and language

Use the existing typography, spacing, neutral surfaces and restrained green accent.
Prefer compact tables for comparisons and charts for trends. One primary action
per work area; secondary actions remain visible but quieter. Avoid full-page card
grids, repeated company headers, decorative scores and paragraphs of repeated warnings.

| Current wording or pattern | Target presentation |
|---|---|
| Thesis Assumption Engine | Thesis, with structured assumptions in details |
| Promoted | Reviewed financial input, with the underlying status in details |
| Processing Runs | Source activity in normal flows; technical name in settings |
| Raw Documents / hashes | Sources, with hash and parser details expandable |
| Generic data incomplete warning | Named missing input, its consequence and a direct action |
| Large unexplained number | Readable scale/currency, exact value on inspection, source/date nearby |
| Repeated disclaimers on every card | One shared basis summary plus local material blockers |

Do not soften a real blocker into a harmless-looking tooltip. Claim type, date,
example status and material uncertainty remain visible where they affect meaning.
Use the existing formatting helpers; no finance calculations in UI formatting.

### State and recovery matrix

| State | Required behavior |
|---|---|
| Loading | Stable page structure, scoped progress, no zero-value placeholders |
| Empty | Explain what is absent and offer a relevant authorised action |
| Not configured | Name the missing provider/configuration and link to its settings |
| Unavailable/error | Explain the failed operation and retry; do not relabel a transport failure as stale data |
| Partial | Show usable values and exactly which inputs/periods are missing |
| Stale | Show age/basis and the refresh/review action; preserve old saved versions |
| Conflict | Show competing values or version changes; retain edits and require explicit resolution |
| Mock Data/example | Persistent context label and per-item provenance where content is mixed |
| Saving | Prevent duplicate submission, retain inputs and show progress |
| Saved | Confirm the actual saved object/version; do not claim unsaved preview success |
| Permission denied | Safe explanation and no leaked private payload or stale prior-owner view |
| Source blocked | Keep a visible unresolved item with a named dependency and next step |

### Accessibility and responsive behavior

Check desktop, narrow mobile, keyboard-only navigation and 200% zoom. Use meaningful
headings, programmatic labels, visible focus, table captions and text equivalents
for chart information. No status relies on colour alone. Error summaries link to
fields; dialogs return focus to their trigger. Tables may scroll within a labeled
region; the whole page must not overflow. Mobile prioritises identity, status and
next action before advanced tables. Reuse existing accessible navigation/form
patterns rather than introducing a second component system.

## Delivery sequence

Statuses below describe this programme, not earlier app implementation.
**P0 is Verified; P1 and P2.1/P2.2 are Verified and Installed** on November 13.
The November 14 receipt records ten further bounded P2-P5 slices. Package completion
is not inferred from those slices; the [limitation ledger](../limitations.md#workspace-follow-up)
owns remaining scope, and P6/P7 remain open.

| November 14 set | Delivered boundary |
|---|---|
| 1 / P2.3 | New annual promotions retain available period/scope/accounting basis in existing locator JSON; conflicting scopes are held. No migration or historical rewrite |
| 2 / P2.4 | Selected-date evidence rows show original amounts, unit conversions, publication/retrieval/recorded times, revisions, conflicts and missing inputs. Read-only |
| 3 / P3.1 | Required/missing/optional draft guidance, direct field links and exact bulk-accept values. Missing diluted shares cannot produce a one-share estimate |
| 4 / P3.2 | Existing saved-model edits show a non-writing input diff and deterministic calculation preview tied to the selected base |
| 5 / P3.3 | Atomic reviewed save with preview hash, reason/date and UUID retry receipt; stale conflicts, selectable history and selected-version JSON export |
| 6 / P4.1 | Bounded owner-aware projection of candidates, alerts, drafts, thesis interpretations, selected public-source failures and recent sources |
| 7 / P4.2 | Today state filters, capped counts and source-to-financial/model return links |
| 8 / P4.3 | Explicit thesis chooser, supplemental notes, linked event/review state and recorded note changes |
| 9 / P5.1 | Review queue scoped to the selected portfolio's current declared holdings, retaining missing price/FX and example context |
| 10 / P5.2 | Source library filtering/pagination, Advanced landing and Settings/source entry points; existing feature links retained |

The selected financial date does not feed a draft automatically. Preview/save covers
existing saved-model edits; initial model creation still uses its existing review gate.
Research dates are labels until historical source/market selection is implemented.
Normal data preservation, image identity and cleanup evidence belong in the receipt.
A package becomes Verified only after evidence exists; Installed is recorded separately.
Work is sequential by default. This plan does not dispatch agents.

| Package | Deliverable and bounded scope | Dependency | Acceptance mapping |
|---|---|---|---|
| P0 | Establish current source/runtime/retention baseline and exact first slice | None | Preserve accepted M01-M04 evidence; do not award new points |
| P1 | Four-area shell, company sections, readable company overview and saved-model-first list | P0 | M09 interface behavior |
| P2 | Explicit draft/source-discovery actions; precise financial period guard; dated input presentation | P0; needed before new period/draft automation | M05/M06 correctness, M09 recovery |
| P3 | Complete reviewed-input -> assumptions -> preview -> saved-version journey | P2; consume P1 layout | M05/M06, source gaps stay explicit |
| P4 | Today review queue and thesis/source/model handoffs | P1/P3 contracts | M08/M09 workflow and interpretation boundaries |
| P5 | Portfolio research linkage and secondary feature placement | P1/P4 | M07 existing example basis, M09 navigation |
| P6 | Bounded refresh reliability, targeted contract generation and measured performance | Stable P2-P4 contracts | M04 follow-up plus M09/M10 operating evidence |
| P7 | Installed end-to-end verification, actual research-use record and acceptance | Applicable prior packages | Existing M09/M10 gates |

P1 can improve usability without waiting for an unavailable company disclosure.
P2 correctness guards should precede any expansion of quarterly ingestion. Open
facts remain visible; they do not justify marking M05/M06 complete. Package order
does not change the milestone denominator or waive cumulative prerequisites.

### Commit-sized work within packages

| Task | Work and expected owner | Proof required |
|---|---|---|
| P0.1 | Inspect git changes, current containers/images/mounts and source/runtime difference | Small baseline receipt; no new dump for read-only planning or UI work |
| P0.2 | Classify storage using Operations; link retained recovery basis | Exact retained roles and disposable targets; no bulk deletion by age alone |
| P1.1 | Sidebar, company tabs and secondary destinations | Every old feature reachable; deep links, active state, keyboard/mobile checks |
| P1.2 | Company overview summaries and existing financial display | All four companies inspected; correct units, zero/missing/error, note links and dates |
| P1.3 | Valuation landing list before advanced industry setup | Existing Apple model and drafts accessible; no writes on list navigation |
| P2.1 | Explicit draft create/resume/refresh and filing-discovery actions | Browser/read API tests prove opening a page does not create/refresh drafts or start provider discovery; retry is safe and explicit discovery retains Processing Runs |
| P2.2 | Financial period regression and fail-closed identity guard | Annual, two distinct quarters, YTD and missing-identity cases; no cross-period replacement |
| P2.3 | Annual period/basis snapshot now uses existing metadata; broader period design remains | Compatibility reads and scope conflicts verified; any later migration must be additive and separately verified |
| P2.4 | Unified dated input rows and source detail | Source locator/revision, original scale, selected date, claim type and conflict states round-trip |
| P3.1 | Required input/assumption sections and readiness | Model-specific rules; no hidden missing-share fallback or bulk approval of invalid values |
| P3.2 | Proposed input diff and deterministic preview | Changed values and affected results linked to exact versions; preview has no saved-model writes |
| P3.3 | Save version, compare history and memo basis | Atomic save, stale-write rejection, duplicate retry, unchanged previous version and matching export |
| P4.1 | Backend review projection with bounded counts | Owner scope, stable identity, grouping, limits, date ordering and no duplicate source storage |
| P4.2 | Today views and source-to-review return paths | New-source, no-new-source, failure, partial coverage and no-model-change journeys |
| P4.3 | Thesis selection, evidence and decision history | Multiple active notes selectable; interpretation review cannot approve financial facts |
| P5.1 | Portfolio research context | Uses selected holdings basis; missing prices/FX and example status remain visible |
| P5.2 | Library, Advanced and Settings entry points | No orphaned route/capability; unavailable features stay truthful; private access unchanged |
| P6.1 | Worker status and bounded transient retry | Retry classifications, limits, interruption/restart, cancellation and duplicate-import tests |
| P6.2 | One-domain contract pilot and read-path optimisation | Contract compatibility, source/type checks, query budgets and measured before/after timings |
| P7.1 | Scoped installation and integrated browser checks | Correct image identity, local ports, readiness, old records/versions preserved and resource check |
| P7.2 | Actual research-use and final acceptance | User-reported dated sessions/failures; automated tests never count as use days |

Do not bundle all P1-P7 work into a single change. A task may split when it affects
multiple trust boundaries. Before a package touches more than ten files, explain
the cross-cutting dependency and list its owners. Do not use cosmetic file moves
or a general framework to disguise an oversized change.

## Acceptance matrix

Tests should verify behavior and regressions, not merely search for UI strings.
Reuse existing fixtures and approved test environments. No new normal-app demo
records or unauthorised disposable databases are introduced to close a gate.

| Area | Minimum cases | Existing starting points |
|---|---|---|
| Navigation | Four main areas; five company sections; old links; mobile/keyboard/focus; secondary reachability | [Navigation tests](../../frontend/lib/frontend-navigation.test.ts), [responsive browser tests](../../frontend/e2e/accessibility-responsive.spec.ts) |
| Company summary | Four scoped companies; mixed source states; large/zero/missing values; long notes | [Company coverage](../../frontend/e2e/company-coverage.spec.ts), [financial display tests](../../frontend/lib/data-panels.test.ts) |
| Financial identity | Different quarters/YTD/annual; conflicting duplicates; units; precise date; unchanged old revisions | [Extraction workflow](../../backend/tests/test_financial_extraction_workflow.py), [candidate versions](../../backend/tests/test_financial_candidate_versions.py), [source history](../../backend/tests/test_source_fact_history.py) |
| Draft lifecycle | Read-only open; explicit creation; resume; refresh preserving edits; stale version; failed save | [Draft service tests](../../backend/tests/test_valuation_setup_drafts.py), [draft browser flow](../../frontend/e2e/valuation-draft.spec.ts) |
| Input review | Required/missing/optional distinction; exact evidence; explicit assumptions; no false completeness | [Review planner tests](../../backend/tests/test_financial_review_plan.py), [review recovery](../../frontend/e2e/financial-review-recovery.spec.ts) |
| Valuation | Valid/invalid inputs; zero vs missing; scenario basis; saved/unsaved distinction; old version unchanged | [DCF tests](../../backend/tests/test_dcf.py), [zero defaults](../../backend/tests/test_dcf_zero_defaults.py), [reverse DCF](../../backend/tests/test_reverse_dcf_integrity.py) |
| Today and private review | Owner boundaries; empty/partial/error; capped counts; source-to-action; no AI on read | [Dashboard API](../../backend/tests/test_api_dashboard_overview.py), [brief recovery](../../frontend/e2e/brief-recovery.spec.ts) |
| Refresh | Disabled worker; transient/permanent failure; bounded retry; interruption; cancellation | [Source refresh tests](../../backend/tests/test_valuation_source_refresh.py) |
| Contracts/performance | Response envelopes; private identity; no per-row requests; bounded histories; race handling | [Schema boundaries](../../backend/tests/test_schema_boundaries.py), [query budgets](../../backend/tests/test_read_query_budgets.py) |
| Retention | No snapshot on read/UI edit; explicit roles; failed backup cannot displace good copy; pin handling | [Backup tests](../../scripts/test_backup_workflow.py), [recovery metadata tests](../../scripts/test_recovery_metadata.py) |

### Product acceptance checks

- From Today, the user can reach an item's exact source and return to the same
  review context without searching for the company again.
- A company overview communicates business context, financial basis, thesis/model
  state and the next unresolved action before full technical details.
- Every required unavailable input has a named reason and an actionable destination;
  no empty field silently becomes zero or an undisclosed assumption.
- A new source can be reviewed and proposed as a model change, or explicitly left
  unresolved, without altering the old model.
- Saved versions and exported memos agree on date, inputs, assumptions and source
  basis. No result is displayed as current solely because it was fetched today.
- All retained features have a contextual or secondary route. Unsupported methods
  are explicit and do not lead to an unexplained empty panel.
- Existing data, original documents, private research and prior versions survive
  the change. Verification matches the actual mutation scope.
- The installed app passes the affected browser flows and the applicable runbook
  checks. Compilation is not browser proof; fixture proof is not real-data acceptance.
- Actual research-use evidence is recorded by the user under the existing
  five-business-day gate. No dates or observations are invented by the agent.

Useful measurable UX targets for implementation: one source-detail action from a
financial row; one resume action from a model list; no primary task hidden below
an advanced setup form; no page-level horizontal overflow at 320 px; no loss of
entered values on recoverable request failure. Measure these, do not report them
as achieved from this planning document.

## Storage and operating discipline

[Operations retention policy](../operations.md#essential-retention-policy) is the
only numerical retention owner. It distinguishes live data, original evidence,
verified recovery material and reproducible generated artifacts. Read it before
creating a backup, retaining a rollback image or deleting material.

For this programme:

- Documentation and normal frontend changes create no database backup. Reuse the
  verified recovery basis and preserve the exact current application image only
  while the changed service is being validated.
- A schema or substantial persisted-data change needs the appropriate verified
  pre-change recovery point, matched to its assets and database compatibility.
- Keep one active Compose installation. Tests use existing authorised lanes and
  remove their identified temporary artifacts on completion. No renamed stopped
  production containers or new full stacks for each UI revision.
- Keep original sources once with stable references; financial receipts and model
  versions refer to them. Do not copy a full source bundle into each test/report.
- Evidence is a compact receipt plus representative screenshots or a minimal
  failure reproducer. Preserve enough to explain unresolved failures; large
  caches, repeated videos and exported images are not permanent evidence.
- No automatic pruning is enabled by this plan. Existing script retention is
  count-based and cannot protect semantic roles or an active pre-change pin.
  Do not turn it on until the selected backup root is safe for that behavior.
- No new encrypted off-device destination, scheduled task or restore rehearsal is
  assumed. Existing scope deferrals remain in the limitation ledger.

## Managing the work

### Status and evidence

Use Planned -> In progress -> Verified -> Installed for software packages. Use
Blocked only with a specific unresolved dependency and a next action. Accepted
belongs to the milestone tracker and the user's actual-use/final gates. A source
gap can remain open while a UI package is correctly installed.

At package completion, record its task IDs, changed owners, verified source/image
identity, checks actually run, significant failures, installed/not-installed state,
retention actions and remaining dependencies. Add a small dated receipt at the
repository's existing evidence location; reference existing artifacts by path/hash.
Do not create a new full handoff, duplicate plan and database dump for every task.

### Documentation responsibilities

| Owner | Update when |
|---|---|
| This plan | Target design, task sequence or design decisions change |
| [Roadmap](product-roadmap.md) | Product priorities change |
| [Limitations](../limitations.md) | A gap is discovered, resolved or changes scope |
| [Current State](../current-state.md) | Behavior is verified or installed, with dated evidence |
| [Feature register](feature-register.md) | A capability changes between built/partial/experimental/unavailable |
| [Completion tracker](completion-tracker.md) | An existing acceptance check gains valid evidence |
| [Handoff](../HANDOFF.md) | Immediate next task, blocker or installed boundary changes |
| [Operations](../operations.md) | Runtime, retention, recovery or provider procedure changes |

Replace stale current status. Keep prior evidence linked without turning archive
files into the active queue. Existing parallel-workstream ownership applies only
to an explicitly launched batch; it does not assign this programme to agents.

### Decisions that do not need another user interruption

Within the authorised scope, choose labels, layout, component reuse, focused tests,
safe incremental implementation and source-backed delegated research methods.
Record the rationale. Do not ask the user to select every tab name or approve
routine reversible work. Missing company facts still require evidence.

User input is genuinely needed for actual research-use observations and final
acceptance, changed company/provider scope, paid services, external AI permission,
real portfolio records, public/broker work, or deletion of unique information whose
disposition is unclear. An unavailable source is a source blocker, not automatically
a question for the user. Identify the exact missing source or decision first.

### Risks and controls

| Risk during implementation | Control |
|---|---|
| A cleaner page hides material uncertainty | Keep local blockers and dates visible; move only explanatory detail |
| A page merge loses a review or source capability | Feature disposition and route regression inventory before removal |
| Existing manual inputs are overwritten | Source/version-aware diff; preview; atomic save; preserve old versions |
| Different periods/classes are combined | Precise identity guard before broader ingestion and dated selection |
| A UI query creates data | Explicit command/read separation and no-write navigation tests |
| A pending request updates the wrong company | Existing request gates plus identity-switch browser tests |
| A long task leaves more stacks or backups | End-of-package inventory and bounded retention cleanup |
| Samples appear to be real research or holdings | Structured provenance and persistent context labels |
| Completion is overstated | Separate built, verified, installed and accepted; no fabricated use days |

## Next implementation session

1. Read the [ten-set receipt](../../data/reviews/research-workspace-ten-sets-20261114.json),
   handoff and affected owners. Recheck the dirty checkout and running project; preserve earlier edits.
2. Reuse the existing recovery basis. No new dump is needed for inspection or UI-only work.
3. Preserve the installed P2.1/P2.2 safeguards. Annual date confirmations use existing
   locator metadata with source notes, reviewer/time and history; no migration was needed.
4. Design complete quarterly/YTD/transition-period and basis persistence before
   enabling interim promotion. Any necessary migration must be additive.
5. Connect selected dated evidence to a reviewable draft proposal and initial-model
   preview. Retain exact source revision/date/knowledge in the save receipt; never
   equate a research-date label with historical market-data reconstruction.
6. Install verified slices into the existing project, remove their generated material,
   and replace the handoff status with evidence and the next bounded task.

The installed safeguards retain explicit commands, annual period review and previous
versions. The November 14 tests and isolated Mock Data flows verify the bounded
behaviors above. They do not prove complete financial inputs, all package acceptance
cases or actual use. Continue worker reliability and measured read performance after
the dated proposal contract is settled; keep normal data and recovery material intact.
