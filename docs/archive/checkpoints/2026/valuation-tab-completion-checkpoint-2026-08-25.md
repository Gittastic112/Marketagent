# Valuation Tab Completion Checkpoint

**Date:** 2026-08-25

## Scope completed

- Added owner-scoped direct model reads, metadata updates, and compact company
  model readiness summaries.
- Made assumption creation, deterministic calculation, projections,
  sensitivities, and change logs one transaction.
- Preserved all rendered payout, cost-of-capital, story, equity-bridge, and
  currency inputs on every saved assumption version.
- Persisted cash-flow currency, discount-rate currency, and mismatch rationale
  under migration `h9h9h9h9h9h9`.
- Rejected malformed currency codes and unexplained currency mismatches at the
  API boundary.
- Added visible load, save, reverse-DCF, memo, and real-option failure states;
  actionable first-run states; metadata editing; and model readiness.
- Blocked critically warned quick/full estimates and labeled assumptions,
  calculations, estimates, market facts, mock data, freshness, and missing data.

## Validation evidence

- Frontend unit/integrity tests: 127 passed.
- TypeScript: passed.
- Alembic source graph: one head at `h9h9h9h9h9h9`, one connected chain of 60 revisions.
- Backend valuation test additions cover direct reads/updates, model type,
  compact summaries, transaction rollback, currency persistence, and the
  currency mismatch gate.

## Unresolved limitations

- Docker Desktop was not reachable during the final validation pass. The focused
  backend suite, Alembic head/full-chain upgrade, authenticated browser workflow,
  and production build still require rerun. The last backend baseline before
  these changes was 619 passing tests.
- The authenticated valuation browser workflow now covers metadata editing,
  save-and-calculate, payout persistence, and readiness, but that expanded gate
  has not run while Docker is unavailable.
- The normal local database is still at `ee6ee6ee6ee6`; do not use the new
  currency fields until it is upgraded through `h9h9h9h9h9h9`.
- Field-level source provenance is strongest in the reviewed draft workflow.
  Later advanced-workspace edits are explicitly User Assumptions and versioned,
  but do not invent external source evidence.
- Relative valuation uses industry aggregates, not a reviewed company peer set.
- Narrative-to-numbers and valuation memos require configured AI providers,
  disclosure acknowledgement, source review, and human approval.
- The Assumption Methodology Engine still has documented hardcoded India
  risk-free-rate and equity-risk-premium fallbacks when approved benchmark rows
  are not seeded. No new fallback was added here.
- This completion covers the local valuation product workflow. It does not make
  outputs investment recommendations or make the app safe for public deployment.
