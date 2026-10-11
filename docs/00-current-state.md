# Current State

Source tests: 2026-10-10. Scope: local-first, single-user equity research.
M01 rollout/browser proof: [2026-10-10](archive/checkpoints/2026/m01-foundation-complete-2026-10-10.md); broader product claims retain their dates.

Latest foundation: [M01 rollout and browser repair](archive/checkpoints/2026/m01-foundation-complete-2026-10-10.md). Prior feature delivery: [security and analyst reviews](archive/checkpoints/2026/security-and-comparison-reviews-2026-09-30.md).
The preceding [private research inbox and AAPL proof](archive/checkpoints/2026/research-inbox-and-aapl-2026-09-22.md)
records the actual Apple scan, illustrative calculation and recovery verification.

## Product position

This is a broad research, valuation, evidence and portfolio platform, not a
finished daily-driver or trading system. Reviewed-source coverage, workflow
integrity, and public-deployment security remain uneven. The tracker accepts M01
at 10% of its gates, not engineering effort. The [feature register](roadmaps/feature-register.md) owns detailed
capability status; the [single limitation ledger](agent_capabilities_and_limitations.md)
owns remaining gaps and the confirmed personal-research US/India, USD-base scope.

## Current source validation

| Check | Evidence |
|---|---|
| Backend | 1,294 passed October 10 in the network-disabled source test container, including request/DNS/upload/rate boundaries and immutable/stale/owned analyst reviews; five upstream deprecation warnings |
| Frontend | 234 tests pass; TypeScript passes with final browser harness repairs. October 10 disposable functional workflows and normal desktop/mobile checks pass; the unchanged route-timing matrix passes on repeat after one slow local sample |
| API compatibility | 279 paths, 505 schemas and 381 inventoried application operations including hidden compatibility routes. Reviews add narrow write/history/detail contracts and migration s1. Financial contracts remain unchanged; OAuth writes are deliberately disabled |
| Schema boundaries | Compatibility identity, pure contract imports, engine dependency direction, unique class names and distinct metric fields covered |
| Frontend boundaries | Exact legacy runtime exports, domain/transport import rules, module limits, payload/error/404/binary behavior covered |
| Documentation / operations | October 10: 28 documentation/secret-scanner-fixture/Compose/backup-workflow tests pass in isolated tooling; scoped Git whitespace, explicit publication secret scan and knowledge-base audit pass. Protected environment paths are excluded; this is not a full-history secret audit |
| Production / browser | October 10 patched standalone frontend passes five normal routes, 1440px/390px dashboard inspection and missing/foreign-Origin 403. All functional browser workflows pass locally; timing scope is in the M01 checkpoint. Fresh frontend and resolved backend/test advisory audits pass; broader security certification is not implied |
| PostgreSQL concurrency | Five competing analyst-review pairs each returned 201/409, adding exactly five versions while the original receipt stayed unchanged. Visible stale forms did not write. Reviews remain User Assumption, not AI approval or financial edits |
| Runtime evidence | September 22: existing 11 drafts, 694 unreviewed SEC candidates and 196 FRED observations retained. Added public annual filings/business sections for AAPL/GOOGL and private Apple PDF source 1 with five real Gemini findings, pending review. Two models, four assumption sets, two holdings and three transactions have identical fingerprints to the pre-inbox backup. Non-saving AAPL illustration is USD106.01/share, not an approved current valuation |
| Migrations / recovery | Normal head s1s1s1s1s1s1 adds only an empty review table. Backup 20261001T015318Z restores all 108 r9 table fingerprints including private PDF/AI evidence. Rehearsed and normal s1 upgrades preserve all 107 prior data tables exactly; only migration metadata changes and an empty table is added (109 total). Dump mode 0600, directory 0700. Off-device recovery remains unproven |
| Performance | Same-data local authenticated checks: portfolio overview full server response 8,897 ms before vs 45/127 ms in two after samples; companies 890 vs 65/59 ms; Data Health 3,501 vs 193/152 ms. Valuation read queries 168 to 11; risk 204 to 12. Dashboard was already small and did not improve. These are not browser-interactivity or load-test guarantees; [measurement checkpoint](archive/checkpoints/2026/frontend-performance-2026-09-21.md) includes all results |
| Provider evidence | September 22 FRED DGS10/NFCI and SEC imports succeeded; six US securities have annual candidates. US/NSE personal-provider quotes have unknown timing. Real gemini-3.5-flash-lite scanned the public Apple PDF in the isolated browser and normal app with valid exact quotes, retained provenance and pending review. No stored portfolio/model values sent. This is workflow proof, not interpretation-quality certification |

October 10 accepts M01 after a 109-table restore/fingerprint comparison and normal
rollout. Current screens contain existing Mock Data; the backup has no document
assets, so September inventories above are historical. Initial browser access added
one deterministic brief; later normal quote activity is separately recorded in M01.

[Refactor checkpoint](archive/checkpoints/2026/repository-architecture-refactor-2026-09-09.md)
records the older production/browser scope. The
[saved-input/reverse checkpoint](archive/checkpoints/2026/saved-input-reverse-dcf-integrity-2026-09-10.md)
records current implementation, completed verification and cleanup evidence.
The [core zero/default checkpoint](archive/checkpoints/2026/core-dcf-zero-defaults-2026-09-14.md)
records the subsequent backend calculation correction and its verification scope.
The [Real Options checkpoint](archive/checkpoints/2026/real-options-integrity-2026-09-15.md)
records the subsequent saved-basis integration and isolated browser verification.
The [FCFE/DDM checkpoint](archive/checkpoints/2026/fcfe-ddm-integrity-2026-09-16.md)
records the subsequent explicit-equity-input correction and backend verification.
The [specialized-engine checkpoint](archive/checkpoints/2026/specialized-valuation-integrity-2026-09-21.md)
records the 30-item bank/distress integrity batch and its verification.
The [provider/portfolio checkpoint](archive/checkpoints/2026/provider-portfolio-architecture-2026-09-21.md)
records model connectivity, assumed portfolio setup, shared ingestion and contract extraction.
The [source-pipeline checkpoint](archive/checkpoints/2026/valuation-source-pipeline-2026-09-22.md)
records the latest SEC/FRED automation, source-scope repairs and verification.
Prior runtime evidence remains valid only for the environment and inputs tested.

## Architecture now

- FastAPI, SQLAlchemy, Pydantic and Alembic persist and serve source-backed data.
- Next.js App Router uses a server-only signed-identity client and an authenticated
  same-origin browser proxy. Transport failures are unavailable, not cached data.
- Valuation input/output contracts are independent of HTTP and ORM. Saved
  response assembly retains detached non-writing pricing reconciliation.
- Portfolio and common envelope contracts are pure, with compatibility re-exports.
  Error handling does not load domain services/models. Market ingestion shares
  one audited atomic service; private price-divergence alerts are owner-scoped.
- Internal portfolio calculations derive the persisted owner's DCF/thesis/alerts;
  explicit owner mismatches fail. Event-driven alerts validate relationships and
  link only the model owner's portfolios. Historical records are not rewritten.
- Common ORM reads avoid automatic graph cascades. SQL windows bound latest-price
  and provider-run object loading; tests protect query and row budgets.
- Queued public-source refreshes run in a separately locked local worker. SEC
  annual candidates, USD FRED proxies and dated quotes feed review-required drafts,
  not canonical financial facts or saved models. Explicit edits survive refresh.
- Private sources have bounded intake, explicit AI triage, paged search and owned
  versioned archiving, grouped comparison and append-only analyst receipts. No automatic resolution.
- Portfolio detail streams only its selected server view. Dashboard uses one
  consolidated read; company editing renders one selected form. Shared layout,
  table readability and keyboard navigation are improved. Risk price-age warnings
  withhold stale current DCF gaps without hiding historical risk calculations.
- Core FCFF defaults distinguish missing inputs from explicit zeros across
  forecasts, terminal values, sensitivity and diagnostics. Existing historical
  outputs remain unchanged; adjacent methods still require separate audits.
- Supplementary FCFE/DDM share a finite one-stage equity helper requiring explicit
  cost of equity, growth, shares and complete cash flows. Zero is preserved;
  unavailable estimates receive method-specific watch diagnostics. Payout messages
  use saved currency and do not assert causation. Historical outputs are unchanged.
- Financial-services excess returns require explicit finite equity inputs,
  preserve zeros, diagnose unavailable results and use equity-specific scenarios.
  Distressed calculations validate probability/recovery/shares, reconcile the full
  bridge and final price gap, and withhold unadjusted supplementary/sensitivity
  estimates. Forms now remove unreviewed special-case presets, require model-specific
  inputs, expose hidden invalid controls and use currency-aware payout/recovery labels.
  Saved projections use relative years and equity-specific bank labels.
- Version writes preserve omitted saved inputs with an owned basis, optimistic
  timestamp check, serialized writers and atomic calculation persistence.
- Reverse DCF uses a non-writing validation service, supported model dispatch,
  bracketed convergence and saved-result identity checks in an on-demand panel.
  Focused PostgreSQL/browser verification passed with disposable Mock Data.
- Real Options uses pure contracts and an owned saved-FCFF validation service.
  Backend total-equity integration precedes per-share conversion; saved currency,
  seven eligibility confirmations, explicit equity-basis review, fingerprints
  and independent-form request invalidation replace the old panel's custom base.
- Frontend domain contracts/endpoints are split under lib/api. The old api.ts is
  compatibility-only. HTTP and error-envelope code is centralized.
- Extraction evaluation has narrow contracts, a local non-writing extractor preview,
  an owner-scoped persisted report and a dedicated UI. Review assertions and exact
  hashes are required; scores do not certify PDF/XBRL/AI or company facts.
- Nested agent instructions describe real entry points. The handoff is bounded;
  task routing lives in the [code map](code-map.md), not cumulative history.
- Remaining legacy schemas, large action/UI/service files and split provider
  placement remain deliberate follow-up boundaries, not claimed solved problems.

## Capability summary

| Area | Current boundary |
|---|---|
| Companies and documents | Market identity, setup, dated annual-business cards in company/portfolio views, SEC/RSS ingestion, manual PDF/workbook/XBRL candidate review, raw assets and source locators |
| Financial facts | Review/promotion, normalization, reconciliation and statement identities for supported layouts; not universal extraction |
| Extraction evaluation | Executes the existing local text parser against a separately reviewed reference, retaining source/reference hashes and explicit unit/period/locator failures; no automatic truth or forecast calibration |
| Valuation | Multi-stage FCFF, specialized engines, scenarios, reverse DCF, options, sensitivity, versioned drafts and provenance; not all analysis panels have equal integrity |
| Saved outputs | Stale/invalid/critical, identity/currency and finite-value gates; saved prices are User Assumptions, quality scores are historical |
| Scenarios | Owned model dispatch, zero-preserving shocks, on-demand request isolation, saved currency and backend gaps; deterministic shocks are not probabilities |
| Relative pricing | Source-separated active industry benchmarks and owner-reviewed peers; exact input hashes, diagnostic receipts, normalized immutable revisions and bounded CSV workflows |
| Portfolio | Holdings/activity, FX, benchmarks, snapshots, TWR/MWR and marginal/component risk. Confirmed AAPL/GOOGL User Assumption case has sourced prices and checked calculations; broad genuine-input smoke is still pending |
| Evidence and briefing | Source-linked events/alerts/theses, deterministic briefs, private paste/PDF inbox, bounded comparison and exact-evidence analyst receipts. AAPL still shows five pending non-mock findings across five inputs; no normal review was invented. Direction flags are not verified contradictions or numerical edits |
| AI and research | Provenance, exact-span review, bounded local passage suggestions, human approval, owner-scoped stored search; no semantic truth guarantee |
| Provider health | Observable runs/configuration/freshness; FRED NFCI exact-record macro application; unsupported regime provider modules remain manual |
| Runtime | Production-built Compose services, liveness/readiness, local credential login, signed internal identity; not public-deployment security |

## Data evidence, not inferred runtime contents

September 22 benchmark audit: 24 active typed sources, 3,756 rows, all with
complete active provenance; 14 supported, 18 partial and 9 unsupported mirrors.
Repeated US intake created no duplicate versions or values and retained India rows.

The audited AAPL FY2022-FY2025 and APSEZ FY2023-FY2025 reference histories prove
covered real-source extraction paths. They do not prove those histories exist in
the normal user's database. September 22 leaves 694 unreviewed SEC candidates
and no normalized snapshots. Annual values populate drafts with source, unit,
period and review warnings; they are not approved financial statements. Missing
debt scope, share-class reconciliation and India statements remain explicit.
US industry priors are loaded but mappings require review. Workbook inspection
corrected global-input labels and a US country-tax alias without rewriting old rows.

Portfolio 1 models 200 AAPL and 200 GOOGL at January 2, 2024 unadjusted closes,
rounded to USD185.64/USD138.17. The confirmed USD64,762 deposit, zero fees,
no later trades and dividend exclusion are User Assumptions, not verified trades.
Two snapshots (January 2, 2024 and September 18, 2026), returns, attribution and
historical risk were checked; DCF coverage remains explicitly incomplete.

The separate knowledge base retains its own immutable corpus, source catalog,
hash ledger, rules and audit tool. September 22: 64 canonical files/catalog rows,
44 processing-ledger rows and no pending inbox files. Three new US originals were
added; three existing originals were reused. All pre-existing raw hashes remain intact.

## Prior verification scope

The preceding valuation task passed production builds and focused disposable
browser checks for saved output and scenario integrity. The latest September 21
28-route desktop/mobile matrix extends the older August 25 checks using isolated
fixtures. Neither replaces the pending genuine-input portfolio proof.

The normal runtime is s1s1s1s1s1s1 after fresh and populated restore/migration
preflights. Legacy evaluation ownership/report fields remain null.
Databases stamped with deliberately deleted 20260524_* or 20260530_* revisions
cannot be assumed upgradeable; stop and inspect before any reset/stamp.

## Next priorities

Follow the [completion tracker](roadmaps/completion-tracker.md) for percentage
requests, [Knull](../Knull%28readme%29.md) for detailed feature scopes/ownership,
and the [handoff](HANDOFF.md) for the next safe execution boundary.

[Previous detailed current state](archive/assessments/current-state-before-refactor-2026-09-09.md)
preserves source-specific milestone evidence. Do not resume its chronological
task numbers or treat older test counts as today's baseline.
