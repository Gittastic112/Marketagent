# Feature Register

**Reviewed November 20, 2026.** Runtime validation dates remain in
[Current State](../current-state.md). The latest research scope is four selected
companies, with Sample research and a separately sourced Apple Estimate.

First release: local research/demo using existing data, explicitly chosen October
17. The [scope revision](completion-tracker.md#scope-revision-approved-october-17-2026)
excludes genuine portfolio validation and defers Mac/off-device setup. This changes
acceptance scope, not capability status or the truth labels of stored records.

The [first-valuation and chart workflows](../user-guide.md#review-a-filing-and-valuation) preserve dated sources, the evaluated inputs and private decisions. [Verification by environment](../current-state.md#dated-validation)

Status meanings:

- **Built:** real persisted behavior with meaningful tests.
- **Partial:** useful foundation exists, but coverage or workflow is incomplete.
- **Prototype:** visible behavior is mocked or simulated.
- **Experimental:** implemented analysis with explicit unvalidated assumptions or scope.
- **Not built:** no usable end-to-end implementation.

| Product area | Status | Current boundary |
|---|---|---|
| Local sign-in and owner scoping | Built | Localhost only; not production identity |
| Company CRUD and setup workflow | Built | India lookup/source automation partial |
| SEC filing ingestion | Built | Requires SEC identity/configuration. Filing discovery remains manual; annual companyfacts also run through the opt-in valuation source worker |
| RSS ingestion | Built | Feed quality and scheduling remain limited |
| Official India PDF upload | Built, manual | Identity-bound official guidance covers the five scoped NSE issuers, with checked date and required reports. Upload/excerpt/page/currency/scale review remains manual; source selection is not financial approval |
| Financial extraction candidates | Built, coverage limited | Selected PDF/XBRL layouts produce reviewable candidates. Repeated evidence keeps source revisions; conflicting scopes/units block promotion. Full statements and independent certification remain open. |
| Financial review plan | Built, read-only | Read-only three-year model-oriented tracks expose missing sources, review, units, scope conflicts, and promotion work. Counts do not certify completeness. |
| Local text-extraction evaluation | Built, limited scope | Owned reports compare stored text with reviewed reference rows and retain hashes plus numeric/unit/period/locator results. Missing units fail; broader parser/AI quality is not certified. |
| Financial normalization/reconciliation | Built, coverage limited | Compatible explicit inputs and current promoted provenance are required. Historical normalized values are not automatically repaired or evidence of current database contents. |
| Exact PDF/text evidence | Built | Historical records can have coarse fallback |
| Events, scoring, and alerts | Built | Extraction remains primarily rule-based |
| Thesis notes and evidence ledger | Built | Private notes can attach to an observed company close and reopen from the thesis with the saved price basis. The contradiction workflow remains partial. |
| Company price history and key moments | Built, coverage limited | Stored comparable daily closes, markers for moves of at least 5%, company documents and linked events with their dates. Gaps and conflicting closes can withhold a change. [Walkthrough](../user-guide.md#inspect-a-price-move-and-pin-a-thesis-note) |
| Daily brief | Built with disclosed coverage | Deterministic assembly with stored-input windows, caps, exclusions, source metadata, and separate private review state. Historical unknown coverage remains unknown; linkage is not source verification. |
| Private Daily Brief source inbox | Built, review-required | Text/PDF intake, explicitly consented AI scanning, exact passages, search, pagination, reversible archiving, and bounded private brief snapshots. No automatic facts or model edits. |
| Company and portfolio research cards | Built with source limits | Dated filing-backed business excerpts and direct research navigation. Missing descriptions stay unavailable; Comps opens the reviewed-peer workspace. |
| Private-source input comparison | Built, with analyst review receipts | Quoted period/currency/scope labels, exact evidence, immutable analyst receipts, and stale-review rejection. Bounded to 50 sources; no semantic contradiction or corroboration certification. |
| Stored evidence search | Built | Unified stored research with shared/owner-scoped boundaries. AI content must be approved and unblocked; search is not independent source verification. |
| Portfolios, holdings, cash, transactions | Built | No broker sync |
| Manual and provider-backed prices | Partial | Explicit Alpha Vantage, yfinance_personal, FMP, Massive and NSE MCP adapters; each provider's market/entitlement/adjustment limits remain. Configuration does not certify stored coverage or freshness |
| Source adapter intake | Built, review-required | EdgarTools and selected PDF tables, ALFRED snapshots, FMP/EarningsCall transcripts and supplied India disclosure metadata retain original evidence and Processing Runs. Optional OCR model inference remains unverified. |
| Identity and calendar inspection | Built with bounded coverage | OpenFIGI candidates retain ambiguity; versioned calendars and source-labeled overrides do not auto-merge identities or certify unsupported historical dates. |
| Research Lab | Experimental | Constrained PyPortfolioOpt allocations, compounded native/bt simulations, QuantStats exports and local reference peers use explicit research inputs and owner-scoped receipts. No trading, automatic ledger edits, or historical-universe certification. |
| Research navigation and artifact display | Built | Company/evidence search, exact-file price/FX review and Markdown memo/citation exports retain authentication and the saved artifact identity. [Installed and hosted checks](../current-state.md#dated-validation) |
| Portfolio valuation and exposure | Built | Current value, cash, exposures, and concentration are source-aware |
| Portfolio performance and attribution | Built; research/demo scope | Recorded activity/FX replay, snapshots, TWR/MWR, attribution, and price risk. Legacy or corrected history stays provisional. Genuine activity and multi-currency certification are outside v1. |
| FCFF DCF and scenarios | Built | Reviewed drafts, explicit units, atomic versions, deterministic calculations, and trust-gated results. Historical approved scenarios were removed; saved assumptions do not certify company facts. |
| Source-to-valuation refresh | Built, review-required | Owned queued SEC/FRED/price jobs update review-required drafts and retain cancellation history. Edits survive; facts/models are not auto-approved. Worker operation is opt-in and separately recorded. |
| Reverse DCF and diagnostics | Built | Failures and missing inputs are visible; results remain dependent on reviewed market and financial inputs |
| FCFE/DDM | Built, explicit-input single-stage estimates | Complete finite equity cash flows, cost of equity, growth, and shares required. Single-stage stable-growth estimates; historical outputs need a new saved version. |
| Financial-services and distressed engines | Built with explicit-input limits | Explicit equity/probability/recovery inputs and finite/convergence guards. Model-specific scenarios; unsupported supplementary/sensitivity methods stay unavailable. |
| Saved valuation output cards | Built with evidence limits | Shared stale/invalid/identity/currency/finite gates. Saved price inputs remain User Assumptions and diagnostic scores remain historical. |
| Scenario display integrity | Built with evidence limits | Owned model dispatch, explicit-zero preservation, saved currency, backend gaps, diagnostics, and request isolation. Shocks are not probabilities. |
| DCF implied pricing | Built with evidence limits | Saved income/book/revenue/margin basis replaces proxy earnings. Complete D&A evidence remains required for EBITDA; historical scores are not refreshed on read. |
| Relative valuation | Built with disclosed input-coverage limits | Reviewed peer sets, immutable diagnostic receipts, bounded retry-safe CSV, finite math, and disclosed saved-input basis. No independent fact verification, FX/accounting normalization, or calibrated comparability. |
| WACC and synthetic ratings | Built | Operating-lease capitalization remains incomplete |
| Assumption methodology selection | Built, review-required | Versioned US/India priors retain dataset/hash/cell provenance. Global labels, unsupported columns, incomplete inputs, and user judgment remain explicit. |
| Real options | Experimental | Owned saved-FCFF basis, explicit eligibility, and common-equity integration. Non-persisted supplemental analysis; legacy custom-base endpoints remain deprecated with separate limits. |
| Macro sensitivity | Built calculations, coverage limited | Explicit-input, non-writing calculations preserve missing/constant factors, chronological inputs, and partial coverage. No causal inference or complete provider/company coverage. |
| Weighted industry mapping | Built, provisional comparisons reviewed | Versioned, review-required mappings preserve manual edits. Unsupported blends and Reliance net external-revenue allocation remain unavailable; historical mapping receipts do not restore removed companies. |
| Damodaran source versioning | Built | Twelve recorded active US/India versions retain hashes, dates, and typed provenance. Not every retained workbook or column has a consuming parser. |
| Data Health | Built | Configuration, freshness, failures, readiness, bounded run windows, and owner-scoped receipt diagnostics. On-request inspection is not continuous monitoring. |
| AI memo and narrative assistance | Partial | Exact citations, review gates, bounded claim cues, and retained review receipts. The selected delegated evaluation is not general accuracy or semantic certification. |
| External AI consent | Built, explicit permissions required | Append-only owner/provider/action grants, refusals, and revocations plus per-action disclosure. Every send checks current permission; migration and reads grant nothing. |
| Research sessions | Built | Not yet a unified research workflow |
| Market regime | Built | Bounded manual inputs and one stored FRED NFCI calculation. Options, liquidity, volume, and breadth remain manual without compliant automated adapters. |
| Broker sync | Not built | Security design required first |
| Public deployment | Not built | Security and operations gates unmet |
| Documentation architecture | Built with maintenance gates | One owner per concern, descriptive paths, directory maps, categorized history, and automated links/anchors/route/schema/context checks. |

## Next Status Changes Expected

1. Complete the remaining sourced accounting and valuation-input reviews in the
   [tracker](completion-tracker.md), retaining explicit unavailable inputs.
2. Freeze and verify the research/demo release, then record actual use and final
   acceptance. Preparation does not supply those observations.
3. Keep real-portfolio validation, deferred host/off-device protection, unsupported
   provider modules and public hosting under their separately stated boundaries.
4. Preserve the new briefing coverage and scoped-consent regressions under roadmap
   priorities 3 and 6. Broader source coverage and interpretation quality remain
   distinct from these completed engineering changes.

Update this file when code changes a status. Put implementation proof in tests
and a dated archived checkpoint, not in additional columns here.
