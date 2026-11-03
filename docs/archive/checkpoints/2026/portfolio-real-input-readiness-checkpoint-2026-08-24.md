# Portfolio Real-Input Readiness Checkpoint

**Date:** 2026-08-24

## Scope

This checkpoint records four commit-sized increments that prepare, but do not
replace, the pending manual portfolio smoke with genuine source-labeled inputs.
No migration, seed, provider refresh, snapshot capture, or normal-database write
is part of this work.

## Delivered

1. A deterministic service audits positive holdings, two distinct complete
   snapshot boundaries, non-base-currency exposure, 20 aligned returns per
   holding, dated FX coverage, an active benchmark and complete boundary
   comparison, at least one trust-gated Base DCF output, source labels and record
   IDs, and absence of Mock Data markers.
2. `GET /portfolios/{portfolio_id}/real-input-readiness` exposes the audit only
   to the owning user. A blocked audit is a successful current-state response,
   not a stale or partial transport state. Cross-owner access returns 404.
3. The portfolio detail page shows Ready, Blocked, or Unavailable, preserves API
   metadata, displays every requirement and next action, visibly rejects Mock
   Data, and exposes snapshot, market-price, FX, and DCF output IDs.
4. `backend/scripts/check_portfolio_real_input_readiness.py` prints the same
   report without mutation and returns a machine-usable exit code.

## Validation

- Readiness service tests: complete real inputs pass, Mock Data blocks, and an
  empty portfolio returns actionable blockers.
- Focused readiness plus existing portfolio-performance API gate: 11 passed.
- Frontend tests: 123 passed.
- TypeScript: passed.
- CLI `--help`: passed in an ephemeral backend container.

## Remaining Gate

The normal local database still has no genuine portfolio dataset meeting the
contract. The manual browser smoke remains open until a real owned portfolio
reports `ready`. The isolated Mock Data fixture remains valid only as
implementation proof and cannot satisfy this gate.
