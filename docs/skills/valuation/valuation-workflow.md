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
5. Run deterministic backend formulas.
6. Generate diagnostics before memo/explanation.
7. Present assumptions, outputs, warnings, source labels, and what would change the conclusion.
8. Add/update tests for formulas, warnings, and API shapes.

## Acceptance criteria

- LLM does not freehand valuation numbers.
- Cash flow and discount rate currencies are consistent or explicitly overridden.
- Terminal value, reinvestment, ROIC, and WACC guardrails are visible.
- User assumptions are not silently overwritten.
- Autofill drafts expose source metadata and warnings before they can become saved assumptions.
- Stale or unknown-freshness sources require explicit review; financial actuals currently use a 550-day threshold and market prices a 7-day threshold.
- Generic autofill placeholders are never presented as company actuals.

## Common mistakes

- Using EPS growth as FCFF operating growth.
- Mixing FCFF with cost of equity or FCFE with WACC.
- Treating industry averages as company facts.
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
- `docs/12-assumption-methodology-engine.md`
- `damodaran_knowledge_base_v1/AGENTS.md`
