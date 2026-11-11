# Assumption Methodology Engine

**Source reviewed:** 2026-11-11. Runtime validation is recorded in [Current State](current-state.md).

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
| Draft review UI | [Autofill review](../frontend/components/valuation/autofill-draft-review.tsx) | Inspect and review source-to-draft inputs |
| Saved valuation UI | [Advanced workspace](../frontend/components/advanced-workspace.tsx) | Edit and save assumptions with their current basis |

The standalone method selector had no route callers and was retired. The
[limitation ledger](limitations.md#valuation-boundary) distinguishes the available
backend contracts from the mounted review workflows.

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
See [source boundaries](data-sources.md) and
[intake commands](operations.md#us-benchmark-intake).

## Revenue-weighted prior calculations

Aggregation version 2 records the method for every blended field. Margins,
net-capex/sales and working-capital/sales use revenue weights. Sales-to-capital
uses `1 / sum(revenue_weight / component_sales_to_capital)`: combine the implied
capital before dividing revenue. Every component must be present and finite;
capital ratios must be positive. An absent component withholds the field rather
than redistributing its weight. Accepted percentage-rounding differences are
normalized to the actual total.

Revenue weights do not establish equity/capital weights or matched growth periods.
Multi-industry ROE, ROC, capital-structure ratios and multi-year growth therefore
remain unavailable. Absolute industry financing totals are not blended. Multiple
segments mapped to one taxonomy retain that single industry's own prior/context.
The aggregation version participates in the draft's source signature so old
autofilled values refresh, while explicit manual edits remain protected.

The October 22 review installed seven provisional mixes and four single-industry
comparisons across its historical scope; this does not describe the current database. Reliance's net external-revenue split
is withheld; bank comparisons do not claim that all group revenue is banking.
The [decision log](roadmaps/review-decisions.md) owns exact source scopes and proxy
choices. None approves a company forecast, current share count or valuation.

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
