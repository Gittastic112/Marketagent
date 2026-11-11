# Research workflow guide

Sign in to the local application after following [setup](local-development.md).
A fresh database can be empty. Add only the company and source scope you intend
to research; setup is not permission to restore historical examples.

Start at the dashboard, inspect the Daily Brief, open a company and its evidence,
then review valuation inputs and portfolio context. The
[route inventory](route-inventory.md) maps screens to their source pages.

## Dashboard and brief navigation

The dashboard defaults to the first owned portfolio with nonzero holdings or cash.
Use Portfolio and Show portfolio to select another account; the choice is in the
URL. Values come from the latest stored snapshot, with its date and missing-input
state. Open the portfolio to inspect current stored quotes or capture a snapshot.
The sample portfolio is hypothetical even when its price inputs are sourced.

Daily Brief starts with the stored briefing. Open Add or browse private research
sources for intake and search, or Local Brief Schedule for optional scheduling.
Empty queues and snapshot details are collapsible. Mock Data provenance, missing
inputs and source coverage remain separate. Refresh stored evidence creates a
new deterministic brief without AI or a human review receipt.

## Review financial evidence and macro inputs

For an existing company, open Fundamentals and use Financial review plan. Choose
Operating company, Bank / financial-services equity, or Equity cash flow and
dividends. The optional latest year creates a read-only three-year checklist; it
does not create financial periods. Follow each source/candidate link, resolve
units and conflicting scopes, then use the existing explicit promotion workflow.
Bank review deliberately excludes deposits-as-FCFF-debt assumptions. Source-linked
counts are traceability, not independent completeness certification.

The authenticated GET /api/companies/{company_id}/financial-statements/review-plan
accepts track and optional latest_year. Unknown companies return 404, invalid
tracks/future years return 422. Its reads are bounded and never call providers.

Macro Workbench calculations do not save history or models. Enter explicit zero
only when intended, use chronological consistent period labels and align currency,
scale and macro directions. Update period count expands history to 24 UI periods
(120 through the API). Missing factors stay unavailable. Covered segment/scenario
contributions are partial sums; they are not complete company estimates.

AI output review shows exact citations separately from claim-review cues. Resolve
numeric, period or instruction/inference flags and record your rationale before
approval. Changing the citation evidence resets approval and retains its prior
review receipt. No new external AI call occurs in these deterministic checks.

## Interpret the result

Check source date, currency, units, scope, and review status before relying on a
number. Missing input is different from zero. Sample portfolios are hypothetical;
sourced prices do not turn them into real transactions. AI suggestions require
review and do not silently update financial facts or saved assumptions.

Use Data Health to inspect unavailable providers, failures, freshness, and review
receipts. [Known limitations](limitations.md) explains
which results remain partial, experimental, or unavailable.
