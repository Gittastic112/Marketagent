# Current State

Source tests and normal rollout: 2026-10-13. Scope: local-first, single-user equity research.
M01 rollout/browser proof: [2026-10-10](archive/checkpoints/2026/m01-foundation-complete-2026-10-10.md); broader product claims retain their dates.

Latest source and normal runtime: [October 13 workflow verification](archive/checkpoints/2026/m05-m09-workflows-2026-10-13.md). Source/candidate/price intake remains separately audited and review-required.
The preceding [private research inbox and AAPL proof](archive/checkpoints/2026/research-inbox-and-aapl-2026-09-22.md)
records the actual Apple scan, illustrative calculation and recovery verification.

## Product position

This is a broad research, valuation, evidence and portfolio platform, not a
finished daily-driver or trading system. Reviewed-source coverage, workflow
integrity, and public-deployment security remain uneven. The tracker accepts M01-M02
at 20% of its gates, not engineering effort. The [feature register](roadmaps/feature-register.md) owns detailed
capability status; the [single limitation ledger](agent_capabilities_and_limitations.md)
owns remaining gaps and the confirmed personal-research US/India, USD-base scope.

## Current source validation

| Check | Evidence |
|---|---|
| Backend | 1,594 tests pass; six opt-in PostgreSQL checks pass separately. Five upstream deprecation warnings. Strict narrative output/provider schema, saved AI basis, candidate versions and SQL-bounded price pages are covered; no migration change |
| Frontend | 302 tests, TypeScript and production build pass. Final v10: 64 isolated browser workflows, 110 desktop/mobile route/state views covering all 50 pages plus populated price-history paging and keyboard scrolling. Screenshots, failures and automatic accessibility results remain retained |
| API compatibility | 279 public paths, 513 schemas and 373 public operations. Audit covers 380 static HTTP callers, ten reviewed dynamic entries and 227 controls with no unwired-button candidates. Pure contracts, facade identity and wire guards pass; counts alone are not behavioral proof |
| Operations | 56 documentation/secret-fixture/Compose/recovery/lock/scan tests pass. Format-3 completion, bounded proof-database readiness, timeout cleanup, retention and format-2 compatibility are covered. Protected environment files remain excluded |
| PostgreSQL | Six real integration checks pass, including candidate/valuation competing versions, queue recovery, source/price idempotency and one audited due brief. Fresh schema reaches s1s1s1s1s1s1 |
| Normal runtime | October 13 backend/frontend/worker images installed after a verified format-3 backup. Original database volume/schema and all 109 fingerprints preserved through rollout and browser reads; settings remain in memory and ports stay localhost-only |
| Normal browser | 25 routes, 50 desktop/mobile views pass: 48 rollout-gated plus two empty valuation-setup views. Zero browser errors, overflow or automatic accessibility violations; four forbidden-Origin checks. Maximum readiness 468.0 ms. No saved normal AAPL model, fixture seeding or provider/AI call |
| Recovery | Complete format-3 normal backups and an isolated concurrent-write restore pass. Both original public/private PDF bytes and all 109 table inventories are verified in the drill. Restore verification took 10 seconds, complete drill 35 seconds. Same-disk copies do not prove encrypted off-device recovery |
| Performance | Final profile: six process-cold and 30 warm samples over 774 rows/109 tables, nine query-budget regressions and eight section interactions pass. Market Prices fetches 51 rows and renders 50 forms, retaining filtering/history/export access. Database fingerprints remain unchanged; database/OS caches remain warm. Dataset and hardware are recorded without a concurrent-user/load claim |
| Provider evidence | October 11 authentic SEC/FRED/Gemini and 11-security price probes pass. October 13 [M05 preparation](archive/checkpoints/2026/m05-source-review-preparation-2026-10-13.md) retains official annual reports and ten review batches. Financial records stay unapproved; acquisition runs are audited. Real PDF previews expose layout/unit/scope failures. Provider access and arithmetic checks do not certify interpretation or reviewed coverage |

Normal screens still contain labeled Mock Data. The final rollout has no stored
PDF assets, so September's private-PDF/source inventories below remain historical.
Earlier browser reads add one FRED capability, two SEC discovery runs and one blocked
new-day regime score. The checkpoint separates these from the final rollout and
browser pass, each of which preserves all 109 table fingerprints.

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
- Private sources have bounded intake, explicit AI triage and append-only receipts. Comparison v2 discloses quoted period/currency/scope compatibility.
  Manual/scheduled briefs snapshot bounded private evidence with separate reviewed and pending queues.
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
- Experimental Real Options uses pure contracts and an owned saved-FCFF validation service.
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
- Legacy schemas/actions are compatibility facades over domain owners. Recorded portfolio replay checks cash/positions and purchase-date FX.
  Corrected activity makes old snapshots provisional without rewriting them. No trades are inferred.

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
| Portfolio | Recorded dated replay, purchase-date FX, benchmarks, snapshots, selected-period TWR, annualized MWR since first cash flow and fixed-weight price risk. Legacy/manual or corrected-activity snapshots remain provisional. Genuine multi-currency records and reviewed-input smoke are still required |
| Evidence and briefing | Source-linked events/alerts/theses, deterministic briefs and bounded private source/receipt snapshots with separate review queues. Saved evidence remains as generated; quoted labels and exact citations do not certify interpretation or numeric edits. Normal reviews were not invented |
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

The September 22 reference portfolio modeled 200 AAPL and 200 GOOGL at January 2, 2024 unadjusted closes,
rounded to USD185.64/USD138.17. The confirmed USD64,762 deposit, zero fees,
no later trades and dividend exclusion are User Assumptions, not verified trades.
Two snapshots (January 2, 2024 and September 18, 2026), returns, attribution and
historical risk were checked; DCF coverage remains explicitly incomplete.

The separate knowledge base retains its own immutable corpus, source catalog,
hash ledger, rules and audit tool. September 22: 64 canonical files/catalog rows,
44 processing-ledger rows and no pending inbox files. Three new US originals were
added; three existing originals were reused. All pre-existing raw hashes remain intact.

## Prior verification scope

Prior valuation builds and disposable browser checks retain their dated scope.
The [M09 checkpoint](archive/checkpoints/2026/m09-browser-validation-2026-10-11.md)
owns the earlier matrix; the October 13 follow-up above owns current workflow evidence.
These isolated fixtures do not replace genuine-input portfolio proof.

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
