# Product brief

## Problem and intended user

An equity researcher has to connect filings, financial statements, news, thesis
notes, valuation assumptions, and portfolio exposure across separate tools.
The application puts that review loop in one local workspace.

The current scope is personal research in US and Indian equities, with USD
portfolio reporting. Professional data licensing and public hosting are outside
the verified scope. [Current state](current-state.md) and the
[feature register](roadmaps/feature-register.md) distinguish implementation from
coverage and acceptance.

## Core workflow

1. Inspect what changed in the dashboard and Daily Brief.
2. Open the underlying source and review its identity, date, scope, and quality.
3. Review financial candidates and record a thesis or interpretation.
4. Make explicit valuation assumptions, calculate, and save a version.
5. Inspect affected holdings and the basis of displayed portfolio results.

Every important screen should answer: what changed, why might it matter, how
reliable is the evidence, and what needs review next?

## Product principles

- Lead with the conclusion and material gaps, then offer metrics, sources, and detail.
- Keep facts, source summaries, calculations, assumptions, AI interpretations,
  estimates, and Mock Data visibly separate.
- Retain source links, as-of dates, freshness, uncertainty, and review state.
- Preserve missing, zero, stale, failed, partial, and unconfigured states.
- Treat AI as optional interpretation support. Exact quotes and generated
  confidence do not replace source review.
- Keep calculations deterministic in the backend. Review and versioning precede
  changes to trusted evidence or saved assumptions.

## Non-goals

Automated trading, buy/sell recommendations, broker credential storage,
unapproved scraping, and implied trading-grade real-time data are excluded.
Public deployment requires a separate security and operating design.
The interface must not invent values or claim unavailable provider coverage.

The [roadmap](roadmaps/product-roadmap.md) owns priorities and the
[limitation ledger](limitations.md) owns unresolved gaps.
