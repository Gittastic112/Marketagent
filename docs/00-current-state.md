# Current State

**Audited:** 2026-08-09

**Scope:** local-first, single-user investment research

**Code wins:** verify routes, models, migrations, and tests before relying on this summary.

## Product Position

The repository is a broad, functional research, valuation, and portfolio
performance platform, not a finished daily-driver product. No new completion
percentage was calculated for this release. Valuation, evidence, portfolio
performance, provider diagnostics, and local authentication are stronger than
official India coverage, autonomous daily workflows, and public-deployment
security.

## Last Recorded Full Baseline

| Check | Current result |
|---|---|
| Backend tests | 538 passed; four upstream `openpyxl` deprecation warnings |
| Frontend tests | 98 passed |
| TypeScript | Passes |
| Production build | Next.js 16.2.11 passes |
| Database migration | `cc4cc4cc4cc4` (market-regime score evidence) |
| Knowledge-base tests | 4 passed |
| Knowledge-base audit | 61 canonical files, 61 catalog rows, 38 ledger rows, 0 pending |
| Damodaran application coverage | 9 supported, 13 partial, 13 unsupported |
| Damodaran typed data | 14 sources, 3,290 rows, 12 complete active provenance records |

This table reflects the reconciled 2026-08-09 source-truth worktree. Local API
health, authentication readiness, documentation links, and secret scanning also
pass. Uncommitted paths that remain after reconciliation are duplicate input
data or agent scratch, not application dependencies.

The migration history was deliberately replaced after the user confirmed all
databases created from the previous chain were disposable. Databases stamped
with the deleted `20260524_*` or `20260530_*` revisions must be recreated.

## Documentation State

The active documentation checker covers 62 Markdown files and 270 local links,
including the project skill library. One roadmap and one feature register drive future work.
Dated checkpoints, prior handoffs, old assessments, and superseded plans are
categorized under `archive/`. `scripts/check_docs.py` validates active Markdown
links and rejects retired active-plan paths.

Docker runtime checks, the full backend suite, frontend tests, TypeScript, and
the production build were all available and green during reconciliation.

The valuation UI now persists industry mixes through the authenticated proxy,
supports one explicit acknowledgement for all valid autofill defaults, and
collapses detailed warnings and assumption groups. Invalid percentage-point
DCF assumptions are rejected on new writes; historical invalid models remain
readable but their output, rerun action, and sensitivity tables are blocked as
unreliable until corrected.

## Capability Map

See [`roadmaps/feature-register.md`](roadmaps/feature-register.md) for the canonical list of capabilities and their current implementation statuses.

## Certified Data State

- AAPL FY2022-FY2025 core facts are reviewed, promoted, and reconciled.
- AAPL FY2021 is intentionally not promoted.
- Adani Ports FY2023-FY2025 is promoted, normalized, reconciled, and certified.
  The representative US/India two-market certification gate passes.
- `countrystats.xls` active version `#50` is dated `2026-01-05`, contains 127
  rows, and has SHA-256
  `900b6594f808461f9ce5194abf1a50e66f22854bc998473ad8282037d464829b`.

## Do Not Trust Without Review

- Stale, incomplete, or manual market-regime values without reviewing their
  normalization methodology and source.
- AI memos, narrative-to-numbers suggestions, or generated conclusions.
- Industry mapping or industry averages as company-specific facts.
- Autofilled valuation assumptions without checking source, age, method, and warnings.
- Financial metrics from unreviewed extraction candidates.
- Prices without provider, timestamp, freshness, and currency context.
- India automated filing/provider coverage.
- Any output phrased as a buy or sell recommendation.

## Current Priorities

1. Complete route-by-route frontend/backend truth and data-state parity. (DONE - Phase 16)
2. Expand beyond the certified APSEZ India case and strengthen official India providers.
3. Build a coherent daily research loop from ingestion to evidence, alerts,
   thesis impact, portfolio impact, and next action.
4. Browser-test portfolio performance with real dated prices, FX, flows, and a
   benchmark, then add marginal-risk and expected-return comparisons.
5. Add automated, compliant inputs for regime modules where a provider is
   available; keep manual/provider provenance visible.

Acceptance criteria and sequencing live in
[`roadmaps/product-roadmap.md`](roadmaps/product-roadmap.md). Feature status
lives in [`roadmaps/feature-register.md`](roadmaps/feature-register.md).

## Historical Evidence

Dated checkpoints, previous audits, accumulated handoffs, and superseded plans
are preserved under [`archive/`](archive/). They are evidence of prior work, not
current instructions.
