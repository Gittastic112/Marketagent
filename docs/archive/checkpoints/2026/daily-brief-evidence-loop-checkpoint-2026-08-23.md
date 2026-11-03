# Daily Brief Evidence Loop Checkpoint

**Date:** 2026-08-23

## Scope

Complete a source-linked, portfolio-aware Daily Brief slice without presenting
missing market data or failed AI generation as a real conclusion.

## Implemented

- Held-company moves require two distinct dated price records.
- Missing or invalid price history returns `not_available`; it never becomes a
  synthetic zero-percent move.
- Move calculations expose dates, provider, currency, exact price IDs, affected
  owned portfolios, warnings, and stale state.
- Filings and high-materiality events expose stored source document, provider,
  publication time, claim type, evidence state, and working internal links.
- High-priority filings remain visible in both the new-filing and materiality
  views instead of being dropped by mutually exclusive classification.
- Contradiction alerts are owner-scoped, deduplicated while unresolved, and
  visibly labeled AI Interpretation.
- Valuation mapping exposes AI output, model, prompt, confidence, review state,
  mock state, and explicit not-run/failed/partial/complete status.
- Ordinary Daily Brief GET remains deterministic. Only the explicit refresh
  action invokes configured external AI.
- The responsive workspace distinguishes new, unresolved, stale, reviewed,
  partial, unavailable, and mock states and links to Data Health.
- A focused authenticated browser workflow covers source creation, a material
  filing, a held company, exact price movement, review state, and navigation.

## Validation Completed In This Environment

```text
Frontend unit/integrity tests: 112 passed
TypeScript: passed
Changed Python module compilation: passed
Targeted diff whitespace check: passed
```

## Validation Still Open

This agent could not access the Docker socket. Run:

```bash
docker compose exec -w /workspace/backend backend pytest -q tests/test_daily_brief.py tests/test_persisted_daily_brief.py tests/test_api_daily_brief.py
cd frontend && npm run test:e2e:brief
```
