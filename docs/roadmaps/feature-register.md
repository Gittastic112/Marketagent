# Feature Register

**Source status reconciled:** 2026-09-30. Validation dates are in Current State.

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
| Official India PDF upload | Built | Automated NSE/BSE picker partial/not complete |
| Financial extraction candidates | Built | Layout coverage incomplete; review required |
| Local text-extraction evaluation | Built, limited scope | Owned persisted runs compare stored text against independently reviewed reference rows, retaining hashes, precision/recall and separate numeric/unit/period/locator results. Missing units fail; no PDF/XBRL/AI or forecast certification is implied |
| Financial normalization/reconciliation | Built | AAPL and APSEZ are certified; broader issuer/layout coverage partial |
| Exact PDF/text evidence | Built | Historical records can have coarse fallback |
| Events, scoring, and alerts | Built | Extraction remains primarily rule-based |
| Thesis notes and evidence ledger | Built | Contradiction workflow partial |
| Daily brief | Built | Source-linked evidence, held-company impact, review history, owner-scoped local scheduling, an audited deterministic worker, broad backend coverage, the core browser workflow, an actual due cycle, sanitized Processing Run persistence, generated-brief inspection, next-run advancement, and idempotent owner/date reuse all pass |
| Private Daily Brief source inbox | Built, review-required | Explicit AI scanning, exact passages, field links, search, pagination and reversible archiving retain review state. M08 source adds bounded owner-scoped private snapshots to manual/scheduled deterministic briefs, separating current reviewed analyst context from pending/stale/incompatible evidence. No automatic numeric edits or external AI on read; normal-runtime rollout remains pending |
| Company and portfolio research cards | Built with source limits | Company identity, sourced annual business excerpts and direct Overview/Comps/Valuation/Filings navigation. One bounded read query; missing descriptions remain unavailable. Comps reuses the reviewed peer workflow, not a licensed data feed |
| Private-source input comparison | Built, with analyst review receipts | V2 distinguishes quoted same/unknown/incompatible period, currency and scope while retaining immutable v1 receipts. Owner-scoped exact evidence, rationale, version history and stale-review rejection remain bounded to 50 active sources. Copied content and Mock Data are not real corroboration; no semantic contradiction certification, AI approval or valuation edits |
| Stored evidence search | Built | Primary user-facing research objects are unified; shared narratives are labeled as interpretations, private research is owner-scoped, and only approved/unblocked AI output is indexed; backend coverage and the authenticated browser workflow passed |
| Portfolios, holdings, cash, transactions | Built | No broker sync |
| Manual and provider-backed prices | Partial | Provider breadth/freshness incomplete |
| Portfolio valuation and exposure | Built | Current value, cash, exposures, and concentration are source-aware |
| Portfolio performance and attribution | Built, genuine-input proof pending | M07 source adds dated transaction/cash replay, purchase-date FX, current-balance reconciliation and immutable snapshot provenance. Legacy/manual or corrected-activity history remains provisional across returns, attribution and benchmark reads. Risk is fixed-weight price return, not realized total return. Owner-scoped readiness rejects Mock Data; actual multi-currency activity and reviewed valuation inputs remain required |
| FCFF DCF and scenarios | Built | Durable reviewed drafts, atomic versioned runs, field-level readiness, complete visible input coverage, currency audit fields, trust-gated output, and source-backed benchmark autofill are built; company inputs and every benchmark prior still require review |
| Source-to-valuation refresh | Built, review-required | Queued SEC annual/FRED/price steps populate drafts alongside existing benchmark priors; weekday 07:00 New York scheduling is enabled locally. Explicit edits survive refresh; saved models and source approvals remain unchanged. India statements and unsupported fields remain manual |
| Reverse DCF and diagnostics | Built | Failures and missing inputs are visible; results remain dependent on reviewed market and financial inputs |
| FCFE/DDM | Built, explicit-input single-stage estimates | Complete finite equity cash flows, cost of equity, growth and shares required; zeros preserved, unavailable methods diagnosed. Stable-growth suitability and historical resaves still require review |
| Financial-services and distressed engines | Built with explicit-input limits | Finite equity input/zero/convergence guards, probability/recovery/share validation, corrected distressed gap/bridge and equity-specific scenarios. Specialized form presets are removed; bank forms/scenarios validate equity inputs, saved projections label equity fields and relative years. Unsupported adjusted sensitivities/supplementary estimates are withheld; historical outputs require a new saved version |
| Saved valuation output cards | Built with evidence limits | Shared trust/identity/currency/finite gates, explicit saved-price User Assumption label, historical score disclosure, and corrected-input recovery replace misleading output states |
| Scenario display integrity | Built with evidence limits | Owned model dispatch, zero-preserving shocks, stale/invalid API guards, saved currency, backend gaps, per-scenario diagnostics and request-isolated on-demand loading are implemented; shocks are not probabilistic forecasts |
| DCF implied pricing | Built with evidence limits | Saved net income/book/revenue/margin replace proxy earnings and EBITDA. Historical responses reconcile without storage rewrites; formulas, timestamps, zero/unavailable states and trust gates are visible. Full D&A evidence and historical score refresh remain outside this repair |
| Relative valuation | Built with disclosed input-coverage limits | Industry aggregates and owner-scoped reviewed peer sets retain normalized/versioned evidence, median/minimum-three gates, diagnostic receipts, retry-safe CSV v2, eligibility, comparability warnings, finite math, and request isolation. Saved DCF inputs now use an owned backend adapter with zero/book-equity preservation, EBIT provenance, explicit unavailable EBITDA, exact input-hash consent, stale/invalid-input gates, method coverage, and consumed input-basis disclosure. Remaining evidence, unit, and simplified-bridge boundaries are in the single limitations ledger |
| WACC and synthetic ratings | Built | Operating-lease capitalization remains incomplete |
| Assumption methodology selection | Built | Country-separated India and US rate, ERP, beta, capital-structure and WACC methods preserve dataset/hash/cell provenance. US country-name aliases recover the supplied country-tax prior. Six dated US source contracts also supply margin/reinvestment/ROE/working-capital priors. Mappings require confirmation; India workbook global-input labels are explicit, not verified country-specific risk |
| Real options | Built with saved-basis limits | Owned FCFF panel validates saved inputs and explicit eligibility, integrates total equity before per-share conversion, and isolates requests/forms. Non-persisted; legacy custom-base endpoints have separate limits. Industry volatility is a prior, not company fact |
| Macro sensitivity | Partial | Provider and company exposure coverage uneven |
| Weighted industry mapping | Built | User confirmation required |
| Damodaran source versioning | Built | 24 of 41 mirrors have active typed rows and complete source provenance; the explicit US intake is audited and duplicate-safe |
| Data Health | Built | Separates liveness/readiness, migration/schema blockers, run outcomes, freshness, and RSS coverage; owner-scoped receipt audits have bounded cursor pages, explicit coverage counts, shared evidence eligibility, conflict/coverage blockers, and direct peer-review links |
| AI memo and narrative assistance | Partial | Exact-source validation, deterministic stored-text passage candidates, exact-offset submission, and approval gates are built; provider-generated citation completeness remains uneven |
| Research sessions | Built | Not yet a unified research workflow |
| Market regime | Built | Manual inputs are bounded; persisted FRED NFCI can supply one idempotent, exact-record-linked macro Calculation with explicit freshness, while options, liquidity, volume, and breadth remain manual because no compliant automated adapter is configured |
| Broker sync | Not built | Security design required first |
| Public deployment | Not built | Security and operations gates unmet |
| Documentation architecture | Built with maintenance gates | One current owner per concern, categorized archive, link/path/context checks, complete frontend page inventory and source/runtime migration-head agreement |

## Next Status Changes Expected

1. India provider and issuer coverage expands beyond the certified APSEZ case.
2. Portfolio risk/return comparison completes a manual real-input smoke with a multi-currency portfolio.
3. Remaining market-regime modules gain compliant automated providers only where exact stored-record provenance and licensing allow it.

Update this file when code changes a status. Put implementation proof in tests
and a dated archived checkpoint, not in additional columns here.
