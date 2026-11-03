# Agent Handoff

Updated: 2026-09-30. This is the current starting boundary, not phase history.

## Start

Read the nearest AGENTS.md, [code map](code-map.md), then the relevant reference
from [the docs index](README.md). For major changes also read
[current state](00-current-state.md), [architecture](02-architecture.md), and
[roadmap](roadmaps/product-roadmap.md). Code and tests beat documentation.

## Current worktree

- Substantial user and prior-agent changes are uncommitted. Preserve them.
  Untracked root scripts and source files are not automatically disposable.
- Source/runtime head is s1s1s1s1s1s1 (analyst comparison receipts). Fresh and
  restored-backup upgrades pass. Normal runtime was upgraded after recovery
  verification. Never reset/stamp to hide a migration problem.
- Backend valuation inputs, calculation outputs, and saved response assembly are
  separated under backend/app/schemas. Legacy app.api.schemas imports still work.
- Shared envelopes live in schemas/common.py; error handling and envelope-only
  routes no longer import the legacy domain graph. Full API fingerprint preserved.
- Market quote/history routes share one audited, atomic ingestion service.
  Same-date writes are duplicate-safe; price alerts use the caller's ownership.
- Source refresh queues SEC annual facts, FRED and prices outside page requests.
  The approved weekday 07:00 New York worker populates drafts, preserving edits
  and requiring review before saving. Latest completed fiscal year, not TTM.
  No source approval, saved-model overwrite or external AI is automated.
- Six dated US benchmark contracts now supply country-separated priors through
  the audited, duplicate-safe `--market US` intake. Company mappings need review.
- StoredFinancialMetricRead is distinct from the legacy FinancialMetricRead chart
  contract. JSON response fields are unchanged; OpenAPI names are disambiguated.
- Frontend lib/api.ts is now a compatibility facade. Domain modules own contracts
  and endpoints; transport owns HTTP; contract owns the shared envelope/error.
- Valuation services import narrow contracts rather than the HTTP facade.
  Server API code imports only the shared contract, not the browser API graph.
- Common reads no longer cascade through entire ORM graphs. Latest-price and
  provider-run reads use SQL windows with query/row-budget regression coverage.
- Portfolio detail streams only the selected Overview, Performance, Activity or
  Setup view. Company editing renders only the selected record. Dashboard, shared
  navigation, cards, tables and mobile focus were refined without financial math
  moving to the browser. Data Health presentation helpers have a separate owner.
- Advanced valuation saves preserve the confirmation/selected section across
  refresh while resetting versioned fields. Stale risk prices are dated, flagged
  partial, and excluded from current DCF price-gap comparisons.
- Saved-input resaves now merge omitted fields from an owned, timestamp-checked
  basis. Common book equity, explicit clears/zeros and saved horizons are covered.
- Reverse DCF now validates the saved basis, honors supported model types,
  requires convergence and exposes actual residuals through an isolated panel.
- Core FCFF calculations, sensitivity inputs/centers and related diagnostics now
  preserve explicit zeros; only missing inputs receive legacy presets. Invalid
  zero horizons are rejected. Source datasets and normal credentials are unchanged.
- Real Options uses owned saved FCFF inputs, explicit eligibility and a reviewed
  incremental-equity basis. FCFE/DDM and specialized models require finite,
  model-specific inputs and preserve zeros. Historical outputs are not rewritten.
  Saved projections use relative years; the legacy calendar field remains.
  Remaining limitations live in the [single ledger](agent_capabilities_and_limitations.md).
- `/evaluations` executes local text extraction against reviewed reference rows,
  storing owner-scoped reports and source/reference hashes. Missing units fail;
  no source/candidate changes, provider calls or broad quality certification occur.
- Daily Brief accepts private pasted text and text-based PDFs. Explicit Gemini
  scans link 14 core draft fields without editing values. Search/archive and
  scan races are guarded. A bounded read-only comparison groups exact passages,
  flags opposing suggestions and exposes exclusions. Separate append-only analyst
  receipts preserve exact evidence and reject stale evidence/review versions.
- Company/portfolio cards show sourced annual business excerpts; AAPL/GOOGL are
  populated. Comps exposes the existing reviewed-peer workspace, not a new feed.
- User scope: personal research, US/India, USD base, five large companies per market;
  daily closes and a 20-minute Sheets delay are acceptable. Demo mode is off.
- Portfolio 1 is explicitly User Assumption: 200 AAPL at USD185.64 and 200 GOOGL
  at USD138.17, January 2, 2024 closes; USD64,762 deposit, zero fees, no later
  trades, dividends excluded. Sourced history and two snapshots support checked
  returns/attribution/risk. No broker verification or invented DCF/benchmark.

## Validation

Use [Current State](00-current-state.md) for scope and [the runbook](08-execution-runbook.md) for commands.

September 30 full suites, TypeScript, production builds and review browser checks pass.
Both dependency scans report no known advisories; this is not security certification.
Normal AAPL retains five pending non-mock findings. All 107 prior data tables are
unchanged; s1 adds one empty review table. Backup 20261001T015318Z and restored
fingerprints prove recovery. Local ports, non-root/capability/resource controls pass.

## Next work

1. Eleven securities have drafts; six US securities have annual SEC suggestions.
   September 22 data had 694 unreviewed candidates and 196 FRED observations. Review
   units, borrowing scope and share classes. US priors are loaded; industry mappings,
   India statements and forecasts need review, not fabricated facts.
2. Preserve the verified local backup and localhost-only runtime. Use the updated
   restore workflow; quiesce any additional writers/admin clients before replacement.
3. Next research workstream: scheduled-brief integration of reviewed private-source
   context, preserving owner scope, dated evidence and stale receipt semantics.
   Then period/scope reconciliation; never treat direction flags as verified conflicts.
4. Keep the assumed portfolio distinct from actual broker history. The broad
   genuine-input gate still requires FX/benchmark/trusted DCF evidence; do not
   invent any to make the USD-only example pass. Audit historical holding replay.
5. Continue issuer/security separation beyond the explicit-CIK fallback. Preserve
   draft concurrency, review and query budgets. Unresolved debt remains unavailable;
   all limitations stay in the single ledger, not chat lists.

## Non-negotiable boundaries

Security residuals and operator actions are in the single ledger. Login is not
public-deployment security. Generic OAuth storage is disabled. Compose binds
127.0.0.1, verified on the normal runtime after recreation. No broker
credentials, buy/sell recommendations, fake source values, or silent AI promotion.
Benchmark workbooks are priors, not company financial statements.

The intentionally replaced pre-2026-08-09 migration history does not support
upgrading databases stamped with deleted 20260524_* or 20260530_* revisions.
Stop and inspect rather than guessing a migration/stamp/reset command.

## Historical evidence

- [Security and analyst review receipts](archive/checkpoints/2026/security-and-comparison-reviews-2026-09-30.md)
- [Private research inbox and AAPL proof](archive/checkpoints/2026/research-inbox-and-aapl-2026-09-22.md)
- [Earlier checkpoints](archive/checkpoints/2026/README.md)
