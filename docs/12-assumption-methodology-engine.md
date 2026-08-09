# Assumption Methodology Engine

**Audited:** 2026-08-08

**Status:** partial; review required

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

- `GET /methods/{assumption_key}?country=...&industry=...`
- `GET /country/{country}?industry=...`
- `POST /valuations/{valuation_id}/select-method`

The write route owner-scopes the valuation and records selected method, applied
value, source label, confidence, review status, and notes.

## Important Limitation

The service still contains hardcoded India ERP and risk-free fallback values for
an unseeded database. They are visibly named fallback methods and require review,
but they are not acceptable as current source-backed defaults. Treat this as
technical debt. A future change should seed/version approved source records and
return only `user_custom` or not-configured when no approved record exists.

Do not add more hardcoded market assumptions to `FALLBACK_METHODS`.

## Usage Rules

1. Prefer reviewed company facts and approved current datasets.
2. Store source name, source file, dataset date, confidence, and notes.
3. Keep a custom-user-input option.
4. Require review before applying a default to a valuation.
5. Never hide stale, unknown-date, fallback, or unavailable states.
6. Keep methodology selection separate from deterministic valuation formulas.
