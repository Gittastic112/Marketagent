# Portfolio Runtime Smoke Gate Checkpoint

**Date:** 2026-08-22

## Scope

Add deterministic end-to-end proof for the implemented portfolio performance,
attribution, opportunity-cost, marginal-risk, and DCF-gap workflow.

## Implemented

- The E2E seed creates one visibly labeled Mock Data portfolio.
- The fixture has USD and EUR holdings, 22 dated prices per holding, 22 dated FX
  observations, two complete snapshots, a configured benchmark, and one opening
  cash flow.
- Both holdings have trust-gated Base DCF outputs in their local currencies.
- Backend coverage verifies 21 aligned return observations, full price/FX/DCF
  provenance, complete risk and expected-return coverage, and component-risk
  reconciliation.
- The browser workflow verifies TWR/MWR, attribution, opportunity cost, risk,
  DCF coverage, source IDs, claim labels, and visible Mock Data disclosure.
- Mock state propagates through the calculation body, API metadata, and UI badge.

## Validation Completed In This Environment

```text
Frontend unit/integrity tests: 111 passed
TypeScript: passed
Changed Python module compilation: passed
```

## Runtime Validation

The implementing agent could not access the Docker socket. The user reported
both commands passing on 2026-08-23:

```bash
docker compose exec -w /workspace/backend backend pytest -q tests/test_portfolio_risk_return.py tests/test_api_portfolio_performance.py
cd frontend && npm run test:e2e:portfolio
```

## Still Open

A separate manual smoke with real source-labeled inputs remains required.
Synthetic fixture success must not be presented as real investment-data proof.
