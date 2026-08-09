# Valuation Application Map

The application valuation layer and the Damodaran knowledge base have different
jobs:

- Application behavior: `backend/app/services`, `backend/app/models/dcf.py`,
  valuation API routers, frontend valuation routes, and tests.
- Valuation doctrine and source corpus: `damodaran_knowledge_base_v1/`.
- Current product status: `../00-current-state.md` and
  `../roadmaps/feature-register.md`.

## Current Engines

- FCFF DCF with explicit revenue, margins, reinvestment, WACC, terminal value,
  equity bridge, sensitivity, and diagnostics.
- Reverse DCF.
- FCFE and dividend discount workflows.
- Relative valuation using active source-separated benchmarks.
- WACC with source-backed synthetic ratings.
- Macro sensitivity and real-options workflows.
- Durable setup drafts, assumption provenance, change logs, and review states.

## Trust Rules

- Reviewed company financials beat benchmark priors.
- Industry averages are priors, not company facts.
- Every assumption needs method, source, date/freshness, and review state.
- Keep intrinsic valuation, relative pricing, and market-event interpretation separate.
- Do not generate buy/sell recommendations.

## Historical Specs

The previous master plans, autofill plan, lecture absorption notes, data-batch
index, and six source-batch specs are preserved under
[`../archive/plans/valuation-agent/`](../archive/plans/valuation-agent/). Use them
only when a task needs source-specific historical detail; they are not the active
execution queue.
