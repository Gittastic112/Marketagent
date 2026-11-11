# Valuation Workflow Skill

## Purpose

Build valuation features that keep deterministic formulas, source-labeled assumptions, and user judgment separate.

## When to use

- DCF, WACC, FCFF, FCFE, DDM, reverse DCF, sensitivity, scenarios, relative valuation, real options, macro sensitivity, industry priors, or valuation memo work.
- Any task changes valuation assumptions or outputs.

## When NOT to use

- General event/news scoring unrelated to valuation.
- Financial extraction before reviewed inputs exist. Use `financial-statement-extraction` first.

## Prerequisites

- Read `docs/valuation-agent/README.md`.
- Inspect relevant valuation service, model, schema, router, frontend page, and tests.

## Inputs

- Company and market/currency context.
- Reviewed financials or explicit user assumptions.
- Industry benchmark mapping.
- Valuation model type.

## Outputs

- Deterministic valuation results.
- Assumption source labels.
- Diagnostics and warnings.
- Sensitivity/scenario/reverse DCF outputs where relevant.

## Workflow

1. Confirm company, country, currency, and benchmark context.
2. Confirm industry mapping; do not assume first match is correct.
3. Use reviewed company actuals where available.
   Check normalized coverage, reporting-currency confidence, and source age before treating them as ready.
4. Use Damodaran priors as priors, not company facts.
5. For peer-relative valuation, require an active reviewed peer set. Preserve a
   source name, source URL, as-of date, and claim type for every member. Use a
   median only when at least three included peers have a positive usable value
   for the method. Expose the member IDs, exclusions, counts, and formula. Any
   edit must invalidate review. Require the caller's current version for every
   mutation, retain an immutable snapshot, and restore archived sets as Draft.
   Show source-age, date-alignment, claim-type, coverage, and dispersion warnings
   without silently excluding observations. For bulk input, use the strict
   template, non-writing preview, and exact SHA-256 apply workflow. Apply must
   create a Draft and export must preserve source fields and escape spreadsheet
   formulas. CSV v2 must repeat one identical target profile across all peer rows,
   validate it through the direct target-profile contract, and preserve it on
   export. Legacy member-only CSV may remain readable only with a visible missing-
   target warning. Treat optional country, currency, fiscal-period, accounting, size,
   growth, and margin values as user-supplied facts used for warnings, not as an
   objective comparability score. When target-relative diagnostics matter, store
   a separately sourced target-company profile with at least one comparability
   fact. Preserve it in current and immutable revision records, expose missing or
   inconsistent storage, and compare it to peers without fabricating values from
   company metadata or industry priors.
6. Require a current diagnostic acknowledgement receipt for reviewed-peer
   calculation. Review status alone is insufficient; edits and time-sensitive
   diagnostic changes can invalidate the receipt.
   Run deterministic backend formulas. Preserve explicit zeros and distinguish
   missing inputs. Saved-basis panels must reject stale versions and isolate
   forms/requests; do not silently include unsaved DCF edits.
7. Generate diagnostics before memo/explanation.
8. Present assumptions, outputs, warnings, source labels, and what would change the conclusion.
9. Add/update tests for formulas, warnings, and API shapes.
10. If AI commentary cites valuation evidence, treat passage suggestions as
   review candidates only. Exact-text validation does not make an assumption,
   forecast, or valuation conclusion correct.
11. For sensitivity work, define which axes change which inputs and preserve the
    remaining saved assumptions. Diagnose unavailable cells separately from true
    zeros, label the calculation basis and keep legacy saved results distinguishable.
    A scenario/sensitivity grid is not a probability distribution or live price.

## Acceptance criteria

- LLM does not freehand valuation numbers.
- Cash flow and discount rate currencies are consistent or explicitly overridden.
- Terminal value, reinvestment, ROIC, and WACC guardrails are visible.
- User assumptions are not silently overwritten.
- Autofill drafts expose source metadata and warnings before they can become saved assumptions.
- Stale or unknown-freshness sources require explicit review; financial actuals currently use a 550-day threshold and market prices a 7-day threshold.
- Generic autofill placeholders are never presented as company actuals.
- Draft peer sets, self-comparisons, duplicate peers, Mock Data sources, and
  methods with fewer than three eligible peers cannot drive relative valuation.
- Target profiles with missing source identity, future dates, Mock Data labels,
  no comparability fact, or inconsistent normalized/JSON storage cannot pass the
  relevant review and valuation gates.
- AI evidence review cannot overwrite assumptions or relax valuation trust gates.

## Common mistakes

- Using EPS growth as FCFF operating growth.
- Mixing FCFF with cost of equity or FCFE with WACC.
- Treating industry averages as company facts.
- Treating a reviewed peer set as proof that its members are economically
  comparable or that its source facts are independently verified.
- Adding real option value by default.
- Hiding terminal value dependence.
- Treating source age as proof that a value is wrong, or omitting it from review metadata.

## Do not do

- Do not create buy/sell recommendations.
- Do not use AI as source-of-truth calculator.
- Do not build a generic DCF calculator detached from evidence and assumptions.
- Do not create a valuation model directly from an unreviewed autofill draft.

## Related skills

- `financial-statement-extraction`
- `frontend-data-state`
- `backend-api-change`
- `security-review`

## References

- `docs/valuation-agent/README.md`
- `docs/assumption-methodology.md`
- `damodaran_knowledge_base_v1/AGENTS.md`
