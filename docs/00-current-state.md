# Current State

**Audited:** 2026-08-09

**Scope:** local-first, single-user investment research

**Code wins:** verify routes, models, migrations, and tests before relying on this summary.

## Product Position

The repository is a broad, functional research and valuation platform, not a
finished daily-driver product. The quality-adjusted estimate remains about
**75% of the declared local-first scope** and **64% of the world-class target**.
The valuation and evidence foundations are stronger than provider coverage,
daily workflow integration, portfolio analytics, and frontend consistency.

## Last Recorded Full Baseline

| Check | Current result |
|---|---|
| Backend tests | 492 passed; four upstream `openpyxl` deprecation warnings |
| Frontend tests | 91 passed |
| TypeScript | Passes |
| Production build | Next.js 16.2.11 passes |
| Database migration | `z1z1z1z1z1z1` (cross-holdings and operating leases) |
| Knowledge-base tests | 4 passed |
| Knowledge-base audit | 61 canonical files, 61 catalog rows, 38 ledger rows, 0 pending |
| Damodaran application coverage | 9 supported, 13 partial, 13 unsupported |
| Damodaran typed data | 14 sources, 3,290 rows, 12 complete active provenance records |

This table reflects the current 2026-08-09 dirty worktree. Local API health,
authentication readiness, documentation links, and secret scanning also pass.
The worktree still contains substantial uncommitted prior-agent changes, so
future phases must continue to stage only their reviewed files.

## Documentation State

The active `/docs` layer is now 31 Markdown files and 3,489 lines, including the
project skill library. One roadmap and one feature register drive future work.
Dated checkpoints, prior handoffs, old assessments, and superseded plans are
categorized under `archive/`. `scripts/check_docs.py` validates active Markdown
links and rejects retired active-plan paths.

The Docker daemon was unavailable during the documentation cleanup. The table
above records the immediately preceding verified baseline; documentation checks
for this cleanup are reported separately in `HANDOFF.md`.

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

- Market-regime values or any panel labeled `Mock Data`.
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
4. Complete point-in-time portfolio attribution and opportunity cost. Recorded
   activity by currency and exposure drill-down are present, but historical FX
   and a benchmark series are not configured.
5. Replace or hide the market-regime prototype until source-backed inputs exist.

Acceptance criteria and sequencing live in
[`roadmaps/product-roadmap.md`](roadmaps/product-roadmap.md). Feature status
lives in [`roadmaps/feature-register.md`](roadmaps/feature-register.md).

## Historical Evidence

Dated checkpoints, previous audits, accumulated handoffs, and superseded plans
are preserved under [`archive/`](archive/). They are evidence of prior work, not
current instructions.
