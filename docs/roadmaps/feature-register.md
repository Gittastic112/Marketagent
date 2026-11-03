# Feature Register

**Source and runtime status reconciled:** 2026-11-02. Validation dates are in Current State.

First release: local research/demo using existing data, explicitly chosen October
17. The [scope revision](completion-tracker.md#scope-revision-approved-october-17-2026)
excludes genuine portfolio validation and defers Mac/off-device setup. This changes
acceptance scope, not capability status or the truth labels of stored records.

Status meanings:

- **Built:** real persisted behavior with meaningful tests.
- **Partial:** useful foundation exists, but coverage or workflow is incomplete.
- **Prototype:** visible behavior is mocked, simulated, or not decision-ready.
- **Not built:** no usable end-to-end implementation.

| Product area | Status | Current boundary |
|---|---|---|
| Local sign-in and owner scoping | Built | Localhost only; not production identity |
| Company CRUD and setup workflow | Built | India lookup/source automation partial |
| SEC filing ingestion | Built | Requires SEC identity/configuration. Filing discovery remains manual; annual companyfacts also run through the opt-in valuation source worker |
| RSS ingestion | Built | Feed quality and scheduling remain limited |
| Official India PDF upload | Built, manual | Identity-bound official guidance covers the five scoped NSE issuers, with checked date and required reports. Upload/excerpt/page/currency/scale review remains manual; source selection is not financial approval |
| Financial extraction candidates | Built, coverage limited | PDF v6 handles selected EPS/sidebar and investment-scope layouts with source warnings. All 11 scoped securities have selected reviewed histories. HDFC retains bonus comparability and one EPS exception. Repeated identical occurrences share one period fact; conflicts block promotion. Full statements/notes and independent certification remain open |
| Local text-extraction evaluation | Built, limited scope | Owned persisted runs compare stored text against independently reviewed reference rows, retaining hashes, precision/recall and separate numeric/unit/period/locator results. Missing units fail; no PDF/XBRL/AI or forecast certification is implied |
| Financial normalization/reconciliation | Built, coverage limited | Pure calculations preserve missing versus zero and require compatible inputs. The scoped universe has 33 periods and 336 normalized values, with exact active source-revision provenance on new normalization. Explicitly reviewed after-tax equity-method income can enter the profit identity; generic SEC concepts do not establish that presentation. Complete valuation inputs remain separate |
| Exact PDF/text evidence | Built | Historical records can have coarse fallback |
| Events, scoring, and alerts | Built | Extraction remains primarily rule-based |
| Thesis notes and evidence ledger | Built | Contradiction workflow partial |
| Daily brief | Built | Source-linked evidence, held-company impact, review history, owner-scoped local scheduling, an audited deterministic worker, broad backend coverage, the core browser workflow, an actual due cycle, sanitized Processing Run persistence, generated-brief inspection, next-run advancement, and idempotent owner/date reuse all pass |
| Private Daily Brief source inbox | Built, review-required | Explicit AI scanning, exact passages, field links, search, pagination and reversible archiving retain review state. M08 source adds bounded owner-scoped private snapshots to manual/scheduled deterministic briefs, separating current reviewed analyst context from pending/stale/incompatible evidence. No automatic numeric edits or external AI on read; installed in the normal runtime |
| Company and portfolio research cards | Built with source limits | Company identity, sourced annual business excerpts and direct Overview/Comps/Valuation/Filings navigation. One bounded read query; missing descriptions remain unavailable. Comps reuses the reviewed peer workflow, not a licensed data feed |
| Private-source input comparison | Built, with analyst review receipts | V2 distinguishes quoted same/unknown/incompatible period, currency and scope while retaining immutable v1 receipts. Owner-scoped exact evidence, rationale, version history and stale-review rejection remain bounded to 50 active sources. Copied content and Mock Data are not real corroboration; no semantic contradiction certification, AI approval or valuation edits |
| Stored evidence search | Built | Primary user-facing research objects are unified; shared narratives are labeled as interpretations, private research is owner-scoped, and only approved/unblocked AI output is indexed; backend coverage and the authenticated browser workflow passed |
| Portfolios, holdings, cash, transactions | Built | No broker sync |
| Manual and provider-backed prices | Partial | The selected adapter and its own configuration determine availability. FMP remains unsupported; configuration does not certify stored coverage or freshness |
| Portfolio valuation and exposure | Built | Current value, cash, exposures, and concentration are source-aware |
| Portfolio performance and attribution | Built; research/demo scope | M07 source adds dated transaction/cash replay, purchase-date FX, current-balance reconciliation and immutable snapshot provenance. Legacy/manual or corrected-activity history remains provisional across returns, attribution and benchmark reads. Risk is fixed-weight price return, not realized total return. Genuine-input readiness still rejects Mock Data; that real-activity validation is outside v1. Existing examples and reviewed valuation inputs retain their labels and gaps |
| FCFF DCF and scenarios | Built | Durable drafts use full currency/share units, model-specific reviews and source/version checks. Eleven explicitly approved historical research scenarios are saved, with source gaps, discretionary reserves and dilution stresses disclosed. They do not certify complete company facts. Direct discount rates permit explicitly reviewed unavailable financing components; related funding sensitivities remain unavailable. Missing comparisons and unanchored calendar dates stay null. Atomic versioned runs and trust-gated output remain |
| Source-to-valuation refresh | Built, review-required | Queued SEC annual/FRED/price steps populate drafts alongside existing benchmark priors. Owned queued jobs can be cancelled without losing their history. The opt-in source worker is stopped with restart disabled; Daily Brief scheduling runs separately. Explicit edits survive refresh; saved models and source approvals remain unchanged. India statements and unsupported fields remain manual |
| Reverse DCF and diagnostics | Built | Failures and missing inputs are visible; results remain dependent on reviewed market and financial inputs |
| FCFE/DDM | Built, explicit-input single-stage estimates | Complete finite equity cash flows, cost of equity, growth and shares required; zeros preserved, unavailable methods diagnosed. Stable-growth suitability and historical resaves still require review |
| Financial-services and distressed engines | Built with explicit-input limits | Finite equity input/zero/convergence guards, probability/recovery/share validation and equity-specific scenarios. Bank promotion excludes three unused operating inputs from the saved model and records that exclusion, preserving draft values. Three approved historical bank references retain full-parent-issuance and fixed-subsidiary-ownership assumptions. Unsupported adjusted sensitivities/supplementary estimates are withheld; historical outputs require a new saved version |
| Saved valuation output cards | Built with evidence limits | Shared trust/identity/currency/finite gates, explicit saved-price User Assumption label, historical score disclosure, and corrected-input recovery replace misleading output states |
| Scenario display integrity | Built with evidence limits | Owned model dispatch, zero-preserving shocks, stale/invalid API guards, saved currency, backend gaps, per-scenario diagnostics and request-isolated on-demand loading are implemented; shocks are not probabilistic forecasts |
| DCF implied pricing | Built with evidence limits | Saved net income/book/revenue/margin replace proxy earnings and EBITDA. Historical responses reconcile without storage rewrites; formulas, timestamps, zero/unavailable states and trust gates are visible. Full D&A evidence and historical score refresh remain outside this repair |
| Relative valuation | Built with disclosed input-coverage limits | Industry aggregates and owner-scoped reviewed peer sets retain normalized/versioned evidence, median/minimum-three gates, diagnostic receipts, retry-safe CSV v2, eligibility, comparability warnings, finite math, and request isolation. Saved DCF inputs now use an owned backend adapter with zero/book-equity preservation, EBIT provenance, explicit unavailable EBITDA, exact input-hash consent, stale/invalid-input gates, method coverage, and consumed input-basis disclosure. Remaining evidence, unit, and simplified-bridge boundaries are in the single limitations ledger |
| WACC and synthetic ratings | Built | Operating-lease capitalization remains incomplete |
| Assumption methodology selection | Built, review-required | Six January 2026 versions per country now supply US/India rate, beta, margin, reinvestment, ROE and working-capital priors, preserving dataset/hash/cell provenance. India workbook global-input labels remain explicit, not verified country-specific risk. Unsupported columns and missing values remain unavailable |
| Real options | Experimental | Owned FCFF panel validates saved inputs and explicit eligibility, integrates total equity before per-share conversion, and isolates requests/forms. Non-persisted; legacy custom-base endpoints are deprecated and warn that they do not enforce the saved-basis contract. Industry volatility is a prior, not company fact |
| Macro sensitivity | Partial | Provider and company exposure coverage uneven |
| Weighted industry mapping | Built, provisional comparisons reviewed | Seven saved revenue mixes and four single-industry comparisons are recorded under delegated review. Sales/capital uses a harmonic ratio; unsupported growth, return and financing blends are withheld. Versioned refresh preserves manual edits. Reliance's net external-revenue allocation remains unresolved |
| Damodaran source versioning | Built | Twelve active US/India versions retain original hashes, dates and typed-source provenance. Imports are audited and duplicate-safe; this does not imply every retained workbook or column has a consuming parser |
| Data Health | Built | Separates liveness/readiness, migration/schema blockers, run outcomes, freshness and RSS coverage. The fast page labels its latest-100-run window, displays 25 recent rows and leaves expensive diagnostics explicit. Mobile table keyboard access and all four diagnostic views pass on October 28. Owner-scoped receipt audits preserve bounded cursors, eligibility, conflict/coverage blockers and peer-review links |
| AI memo and narrative assistance | Partial | Exact-source validation, deterministic passage candidates and approval gates are built. Delegated semantic review covers six saved Gemini responses and four adversarial fixtures: four constrained summaries accepted, unsupported valuation directions rejected, one response still blocked. Original human verdicts remain blank. Citation checks and this small review set do not establish general interpretation accuracy |
| Research sessions | Built | Not yet a unified research workflow |
| Market regime | Built | Manual inputs are bounded; persisted FRED NFCI can supply one idempotent, exact-record-linked macro Calculation with explicit freshness, while options, liquidity, volume, and breadth remain manual because no compliant automated adapter is configured |
| Broker sync | Not built | Security design required first |
| Public deployment | Not built | Security and operations gates unmet |
| Documentation architecture | Built with maintenance gates | One current owner per concern, categorized archive, link/path/context checks, complete frontend page inventory and source/runtime migration-head agreement |

## Next Status Changes Expected

1. Complete the remaining sourced accounting and valuation-input reviews in the
   [tracker](completion-tracker.md), retaining explicit unavailable inputs.
2. Freeze and verify the research/demo release, then record actual use and final
   acceptance. Preparation does not supply those observations.
3. Keep real-portfolio validation, deferred host/off-device protection, unsupported
   provider modules and public hosting under their separately stated boundaries.

Update this file when code changes a status. Put implementation proof in tests
and a dated archived checkpoint, not in additional columns here.
