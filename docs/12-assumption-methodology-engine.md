# Assumption Methodology Engine

**Source reviewed:** 2026-09-22. Runtime validation is recorded in Current State.

**Status:** source-backed benchmark methods are built; review required

## Purpose

The engine stores selectable methods and provenance for valuation assumptions
such as risk-free rate, equity risk premium, beta, cost of debt, tax rate,
margin, sales-to-capital, terminal growth, and terminal return on capital.

It does not make an assumption correct. It makes the selected method and applied
value inspectable.

## Implementation

| Layer | Location | Responsibility |
|---|---|---|
| Models | `backend/app/models/assumption_methodology.py` | Method values and valuation-specific provenance |
| Service | `backend/app/services/assumption_methodology.py` | Method lookup, defaults, and country packs |
| API | `backend/app/api/routers/assumptions.py` | List methods and persist reviewed selections |
| UI | `frontend/components/intelligence/AssumptionMethodSelector.tsx` | Method choice, source/confidence display, and user override |

API routes are mounted under `/api/assumptions`:

- `GET /methods/{assumption_key}?country=...&industry=...&currency=...`
- `GET /country/{country}?industry=...&currency=...`
- `POST /valuations/{valuation_id}/select-method`

The write route owner-scopes the valuation and records selected method, applied
value, source label, confidence, review status, and notes.

## Current Source Contract

The service has no hardcoded country-rate fallback table. An unseeded database
returns only `user_custom` and no default. Active January 2026 workbook versions
supply country-separated India/US priors for beta, ERP/cost of capital, borrowing
cost, financing weights and related assumptions. Methods retain dataset ID,
SHA-256, source date, canonical path, sheet, row and column when source-backed.
Labels preserve workbook scope: the India WACC workbook's D10/D11 inputs are
Global weighted averages, not independently verified India-specific rates.

`betaIndia.xls`, `waccIndia.xls`, `taxrateIndia.xls`, and
`countrytaxrates.xls` are seeded by the same versioned importer used by the full
Damodaran ingestion command. Missing workbook cells remain missing rather than
being filled with guessed numbers.

The explicit `--market US` intake also loads six dated US contracts through the
existing parsers. Margin, reinvestment, ROE and working-capital datasets supplement
the beta/WACC priors; they are not company facts or automatically approved industry
mappings. The stored FRED DGS10 observation supplies a dated USD risk-free proxy
through the separate source-to-draft workflow, not a universal currency fallback.
See [source boundaries](04-data-sources-and-ingestion.md) and
[intake commands](08-execution-runbook.md#us-benchmark-intake).

## Important Limitations

- Benchmark methods are estimates and require review before promotion.
- Industry beta, capital structure, cost of debt, and WACC are not company facts.
- The single DCF tax field defaults to reviewed company effective tax when
  available, otherwise the country marginal rate. Industry effective tax remains
  an inspectable alternative/reality check.
- Revenue-weighted multi-industry companies do not yet receive a synthetic
  blended beta or WACC. Those fields remain review-required until an explicit
  blending method is implemented.
- Company financial, bridge, share, price, payout, and special-case inputs still
  require reviewed company evidence or user input.

## Usage Rules

1. Prefer reviewed company facts and approved current datasets.
2. Store source name, source file, dataset date, confidence, and notes.
3. Keep a custom-user-input option.
4. Require review before applying a default to a valuation.
5. Never hide stale, unknown-date, fallback, or unavailable states.
6. Keep methodology selection separate from deterministic valuation formulas.
7. Never use aggregate industry financing flows as company cash-flow inputs.
