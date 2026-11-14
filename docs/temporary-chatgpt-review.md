# Temporary four-part ChatGPT code review

This is a disposable review brief, requested November 14, 2026. It is not a new
architecture, implementation queue or set of parallel editing permissions. No
application, script or documentation index depends on this file. Delete it after
the findings have been consolidated into the existing project documents.

## How to use it

Open four separate ChatGPT Pro chats with access to this repository. Give each
chat this file and assign exactly one review number below. Use the same commit
in all four chats. Ask each reviewer to record that commit before starting.

PR #17 is merged into `main`, which is now the repository's default branch.
Choose the current `main` commit when starting the review and use that same full
commit SHA in all four chats. If ChatGPT cannot read the files at that commit,
it must say so and request the specific missing source files. A repository URL
alone does not prove code access.

These are four substantial areas divided by responsibility, not exactly equal
line counts. Each owns its domain's backend, screens and tests. Reviewer 4 owns
shared infrastructure and cross-cutting contracts, avoiding four incompatible
architecture proposals. Findings are suggestions only; integrate them centrally.

Do not upload runtime databases, backups, credentials, environment files, private
research notes, portfolio exports or the entire source corpus. Review tracked
source and existing test fixtures. A fixture is Mock Data, not evidence of real
financial accuracy or user acceptance.

## Instructions common to all four reviews

1. Read [AGENTS.md](../AGENTS.md), the nearest directory rules,
   [handoff](HANDOFF.md), [current state](current-state.md) and relevant rows in
   [code map](code-map.md). Consult [limitations](limitations.md) before calling
   a disclosed limitation a new bug. Plans describe intent, not proof of delivery.
2. Follow a small number of complete user journeys: screen or API input, identity
   and authorization, validation, service/calculation, database writes, response,
   display and tests. Check both callers and consumers of a changed contract.
3. Start with the files below, then follow imports and callers within your area.
   Use file listings and targeted searches. Do not read the repository or immutable
   knowledge corpus indiscriminately. Explain material files you could not inspect.
4. Distinguish a reproducible defect, a missing requirement, a deliberate tradeoff,
   a known limitation and an optional product idea. Never invent a failing test,
   executed command, browser observation, source fact or financial methodology.
5. Missing values, unknown source dates, user assumptions, calculations, estimates,
   stale outputs, provider failures and Mock Data must stay distinguishable.
   A successful calculation does not certify its evidence or model suitability.
6. Suggest the smallest coherent fix with a meaningful regression case. Do not
   propose a rewrite, new dependency or schema migration without a concrete need.
   Preserve user data, source history, old valuation versions and essential recovery.
7. Report crossing issues to the named reviewer instead of redesigning their
   module. No edits, Git pushes, live ingestion, provider/AI calls, broker activity,
   production transactions or deletion are authorized by this review brief.
8. Be critical and specific. If the code cannot establish a claim, say so. Where
   outside financial/security facts matter, cite original authoritative sources
   and separate those facts from your own implementation judgment.

## Review 1: Source ingestion and financial evidence

**Question:** Can a number be traced to the right original source, reporting
period, currency, scale and review decision without corrupting existing evidence?

Start with the code-map rows for financial review/planning, dated evidence, filing
intake, SEC compatibility intake, normalization/history and extraction evaluation.

| Layer | Main scope |
|---|---|
| Backend | `filing_acquisition`, `filing_manual`, `financial_extraction`, `financial_period_basis`, `dated_financial_inputs`, `source_fact_history`, `financial_review_plan`, `financial_metric_derivations`, normalization, SEC/XBRL and PDF extraction, ingestion/provider adapters |
| Routes/contracts/storage | Filing, fundamentals, raw documents, source facts, ingestion, evaluation, source capabilities and matching schemas/models/migrations |
| Frontend | Company Sources/Financials, document sections/evidence/library, filing discovery, financial candidate/review/history/date panels and corresponding API modules |
| Tests and references | Matching backend tests; PostgreSQL ingestion tests; financial-review/manual-filing/PDF browser specs; data-sources and financial traceability guidance |

Trace a filing through acquisition, duplicate handling, extraction, review,
promotion, revision history and selected-date display. Examine conflicting values,
annual versus quarter/YTD, restatements, accounting scope, share classes, units,
unknown publication dates, partial/failed runs and repeat submissions. Confirm that
future knowledge cannot silently become historical evidence. Check that importing
or opening a page cannot approve a fact or alter a saved valuation.

Financial source acquisition belongs here; model assumptions and calculations
belong to Reviewer 2. General SSRF/auth/security infrastructure belongs to Reviewer
4, but report concrete unsafe uses you encounter. Consult the knowledge-base index
and its own rules only when a particular formula/source needs verification.

Copyable prompt:

> Review area 1 of `docs/temporary-chatgpt-review.md` at the selected commit. Follow
> its common instructions and output format. Trace source-to-financial-evidence
> workflows and their failure cases. Identify concrete correctness and usability
> problems, including provenance, dates, units, review and preservation. Inspect
> actual implementation and tests before suggesting fixes. Stay within area 1;
> hand off crossing findings to the named reviewer. Do not change any files or data.

## Review 2: Valuation and assumption correctness

**Question:** Does every displayed estimate use a valid, explicit and reproducible
set of assumptions, with appropriate model boundaries and preserved versions?

Start with code-map rows for saved DCF/scenarios, preview/save, draft setup,
supplementary/specialized valuation, relative/reverse valuation, real options,
macro sensitivity, benchmark priors and valuation AI explanations.

| Layer | Main scope |
|---|---|
| Backend | DCF, diagnostics, scenarios/sensitivities, FCFE/DDM, financial-services/distressed engines, relative/reverse/real-options/macro calculations, assumption provenance/methodology/autofill/versioning, industry/benchmark inputs |
| Routes/contracts/storage | Valuations, assumptions, relative valuation, WACC, regression priors, macro valuation, real options, benchmark administration and matching models/schemas/migrations |
| Frontend | Valuation pages, advanced workspace, draft review, proposed changes, version history/export, saved outputs, peers, narrative-to-numbers and saved-model memo basis |
| Tests and references | Valuation integrity/zero/default/version/preview/scenario tests, concurrency save test, frontend display/payload tests and valuation browser specs; methodology documentation |

Trace missing versus explicit zero, currencies and scale, shares/equity claims,
discounting, reinvestment, terminal math, model-specific required inputs and
diagnostics. Independently check representative formulas where possible. Inspect
preview-to-save equality, unchanged old versions, race/retry behavior, unsaved
edits, stale outputs, historical selection and exact export/memo basis. Explain
where the research date is only a label and where sources actually determine it.

Upstream fact extraction belongs to Reviewer 1. AI-provider consent/transport and
shared authorization belong to Reviewer 4; private research/portfolio consumers
belong to Reviewer 3. Assess their interfaces without taking over their modules.

Copyable prompt:

> Review area 2 of `docs/temporary-chatgpt-review.md` at the selected commit. Follow
> its common instructions and output format. Check valuation math, required inputs,
> provenance, model suitability, diagnostics, preview/save/version consistency and
> truthful UI output. Do not treat an assumption or benchmark prior as a company
> fact. Give concrete failing cases and minimal fixes. Stay within area 2 and route
> crossing findings to their owner. Do not change files, data or saved assumptions.

## Review 3: Research, thesis and portfolio workflows

**Question:** Can the user move from evidence to a reviewed research decision and
understand holdings/performance without hidden state changes or false certainty?

Start with code-map rows for Today/holdings queues, Daily Brief, private research
intake/triage/decisions, thesis/evidence, portfolio replay/valuation/risk and private
portfolio context.

| Layer | Main scope |
|---|---|
| Backend | Review queue, briefs/schedules, private sources/retrieval/triage/reviews, research sessions, thesis evidence/impacts, events/alerts/narratives/scoring, decisions/learning, portfolio replay/analytics/performance/risk/exposure |
| Routes/contracts/storage | Dashboard, research, daily brief/private sources, thesis, events, alerts, evidence, decisions, search, portfolio and matching schemas/models/migrations |
| Frontend | Today, briefs, research/library sessions, thesis chooser/editor, evidence/decision views, events/alerts/narratives and portfolio overview/performance/activity/setup |
| Tests and references | Queue ownership/query-budget tests, private-research/evidence tests, replay/performance/risk tests, frontend recovery tests and corresponding browser specs |

Trace a queue item to its exact evidence, note, decision and model context.
Check partial/empty/error states, resolution versus stale failure records, note
selection, audit/review history and missing return context. Trace transactions,
prices, FX, cash/dividends/corporate actions, date ranges, benchmark comparisons and
overlapping exposures. Check user ownership, example labels, historical versus
current holdings, missing prices/FX and unavailable calculations. Separate AI
interpretations from approved facts and check what private material could be sent.

Shared consent/auth enforcement belongs to Reviewer 4. Saved valuation math
belongs to Reviewer 2; incoming source evidence belongs to Reviewer 1. This area
owns how those outputs are consumed in research and portfolio decisions.

Copyable prompt:

> Review area 3 of `docs/temporary-chatgpt-review.md` at the selected commit. Follow
> its common instructions and output format. Trace research, thesis, Today and
> portfolio journeys end to end. Find correctness, privacy, historical-basis and
> usability problems with exact code evidence. Check whether the UI makes the next
> action and uncertainty understandable. Separate known gaps from new defects. Do
> not perform trades, external AI calls, ingestion or modifications.

## Review 4: Shared application, security and operations

**Question:** Is the application coherent, secure and maintainable across domains,
and can it be built, updated, operated and recovered without waste or data loss?

Start with [architecture](architecture.md), [runbook](execution-runbook.md),
[operations](operations.md), [local setup](local-development.md), [route inventory](route-inventory.md)
and the code-map rows for request security, shared navigation, contracts and read
performance. This reviewer also coordinates issues crossing areas 1-3.

| Layer | Main scope |
|---|---|
| Backend foundation | App startup/router registration, dependencies, auth, configuration, session/DB ownership, response envelopes, request limits, safe HTTP/URL handling, AI consent/executor/provider boundary, worker lifecycle, health and processing observability |
| Frontend foundation | Layout/sidebar/topbar/company navigation, shared styles/accessibility, loading/error boundaries, server/browser API transport, same-origin proxy, session/CSRF/CORS handling, retained actions and request-race helpers; Advanced/Settings/shared setup |
| Operations/build | Docker/Compose roles and local ports, migrations as a chain, requirements/manifests/lockfiles, scripts, CI, backup/restore/retention, security checks, provider configuration and deployment documentation |
| Tests and references | Security/route/schema/API-boundary/query-budget tests, responsive/accessibility browser specs, script/docs/backup tests, runbook environment matrix and current receipts |

Check authorization on each route family, tenant/owner scoping, browser secret
boundaries, untrusted HTML/CSV/URLs/uploads, size/time limits, CSRF/CORS and safe
error handling. Inspect worker retry/cancel/restart semantics and audit records.
Review API contract drift, bounded reads, resource use, dependency compatibility,
startup/migration correctness and local-only exposure. Check shared navigation,
keyboard/focus, narrow screens and the balance between useful defaults and detail.

For recovery, evaluate semantic roles, verified usable copies, restore isolation,
pins and bounded cleanup. Do not recommend more backups or containers by default.
Review migration mechanics here; each domain reviewer owns its schema semantics.
Do not duplicate every domain's business-rule review. Record cross-domain risks
and designate one owner for each proposed change.

Copyable prompt:

> Review area 4 of `docs/temporary-chatgpt-review.md` at the selected commit. Follow
> its common instructions and output format. Review shared architecture, security,
> UI foundations, contracts, workers, deployment, CI and essential-only recovery.
> Trace actual boundaries and failure paths. Prioritize exploitable defects, data
> loss risks and concrete workflow failures over speculative rewrites. Coordinate
> crossing findings with areas 1-3. Do not modify files, credentials or runtime state.

## Required result from every reviewer

Start with the reviewed commit, scope actually inspected and checks actually run.
Then return findings ordered by impact. For every finding provide:

- A concrete title, severity and confidence. Critical: credible unauthorized
  access or irreversible data loss. High: materially wrong financial output or
  broken core workflow. Medium: bounded correctness/usability/recovery defect.
  Low: minor improvement. Severity must follow demonstrated impact.
- Exact file and line, relevant caller/consumer, trigger and minimal reproduction.
- Expected behavior versus observed or code-derived behavior. Label an unexecuted
  reproduction clearly. Include contrary evidence or conditions limiting impact.
- A minimal fix, compatibility/data effects and a meaningful regression check.
- The owning review area, any cross-area dependency, and whether it duplicates a
  documented limitation. Do not inflate a known open feature into a fresh incident.

After findings, give three short lists: unanswered questions requiring a person;
missing evidence you could not obtain; and at most five prioritized improvements.
Do not fabricate ten findings to fill a quota. If no defect is established, say so
and describe the coverage limits. Keep optional redesign ideas separate from bugs.

## Bringing the four reviews back together

Send all four reports back to the implementation chat. Deduplicate by root cause,
validate each reproduction against the same commit, and assign one owner per fix.
Resolve disagreements with code, tests and original sources. Turn verified work
into small changes with appropriate checks. Update the existing limitation ledger
and roadmap rather than creating four competing plans. Delete this temporary file
when it has served its purpose; retain only useful reviewed findings and decisions.
