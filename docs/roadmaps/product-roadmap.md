# Product roadmap

Priorities for the local research/demo release. Reconciled November 10, 2026.
[Current State](../current-state.md) owns evidence, the
[feature register](feature-register.md) owns capability status, and the
[limitation ledger](../limitations.md) owns unresolved boundaries.

M01-M04 retain 40 accepted gate points. M05 is next in the
[completion tracker](completion-tracker.md). These are acceptance gates, not an
engineering-effort percentage. Existing implementation does not supply missing
financial facts, actual-use days, or final acceptance.

## Planning rule

Finish the connected review workflow before adding isolated engines or schema.
Completion requires backend behavior, frontend states, source/ownership metadata,
tests, and documentation to agree.

Preserve the November 9 four-company research scope. The removed historical
universe must not be restored automatically. Further issuer intake needs an
explicit company/source scope. The October 17 research/demo revision defers
host/off-device work and excludes genuine portfolio validation from v1.

The [workstream design](../workstreams/plan.md) retains detailed technical slices.
Its ownership rules apply to an explicitly assigned parallel batch; the plan
does not dispatch agents or replace current status.

## Priority 1: Frontend and Backend Truth Parity (FOUNDATION DELIVERED, FOLLOW-UPS OPEN)

Preserve explicit missing/zero, loading, empty, unavailable, stale, partial,
unconfigured, and Mock Data states. Verify representative desktop/mobile behavior,
authenticated server/browser access, and provenance through saved-input,
retry, and stale-write workflows. A build or source-string test alone is not
browser evidence. New methodology defaults must be reviewed/versioned or remain
explicit user assumptions.

## Priority 2: Broader Real-Issuer and India Provider Coverage (REFERENCE GATE PASSED, EXPANSION OPEN)

Review the selected companies' financials and complete supported valuation
bridges before expanding coverage. Retained AAPL/APSEZ reference certification
and removed-universe receipts remain historical, not current database inventory.

The next issuer/layout requires official sources, hashes, periods, units,
security/share scope, reconciliation, and explicit promotion. Minority interests,
cross-holdings, leases, currency, and dilution must stay visible.
India automation additionally requires a permitted official endpoint, documented
response/freshness/rate limits, bounded transport, Processing Runs, fixtures,
and non-writing preview. Unsupported exchange automation remains manual.

## Priority 3: Daily Evidence-to-Decision Loop (WORKFLOW VERIFIED, REVIEW OPEN)

Connect dashboard changes to exact sources, thesis review, valuation relevance,
and portfolio exposure. Stored-public coverage counts, private research intake,
search, reversible archiving, comparison receipts, and deterministic scheduling
are implemented.

Next acceptance depends on repeatable use and interpretation quality. Coverage
must disclose its window, caps, exclusions, failures, and review state. Exact
quotes or differing directions do not prove economic contradiction. No claim of
comprehensive overnight news coverage or automatic numerical forecast edits.

## Priority 4: Portfolio Attribution and Opportunity Cost (DEMO IMPLEMENTED, GENUINE PROOF OUTSIDE V1)

Preserve dated activity replay, FX, TWR/MWR, price/flow/position attribution,
benchmark comparison, risk alignment, and residual diagnostics.
Stale/missing prices and provisional histories must prevent false precision.
DCF gaps are Estimates, not annualized forecasts or trading instructions.

The existing example workflow can be checked against its stated inputs.
Genuine activity and multi-currency proof require a later scope with real
records. CSV preview/apply must retain exact hashes, ownership, source metadata,
duplicate handling, atomic writes, and Processing Runs.

## Priority 5: Provider Health and Market Regime (FOUNDATION DELIVERED)

Keep configuration, attempts, failures, freshness, source coverage, formula,
drivers, and confidence observable. Persisted FRED NFCI provides one
exact-record-linked macro calculation; unsupported options/liquidity/volume/
breadth feeds remain manual. A successful connection is not complete source coverage.

## Priority 6: Source-Backed AI Research (REVIEW FOUNDATION DELIVERED, QUALITY OPEN)

Retain exact citations, provenance, bounded output contracts, explicit disclosure,
and current owner/provider/action consent. Permission history and each output's
permitting decision are persisted. Revocation blocks future sends but cannot
recall data already transmitted.

Broaden evaluation using independently reviewed sources and known failure cases.
Numeric/period/instruction cues are review aids, not semantic truth.
Interpretation approval must not silently change financial facts or assumptions.
The [AI boundary](../limitations.md#ai-boundary) owns the exact limitations.

## Next increments

| Work | Entry requirement |
|---|---|
| Financial/model review | Supported missing disclosures and explicit assumptions within the selected scope |
| Additional issuer/layout | Selected company, dated official reports, reproducible reference checks |
| Official India provider | Permitted endpoint and intended-use rights before adapter implementation |
| Peer comparison expansion | Permitted peer data with currency, accounting, and period definitions before normalization/scoring |
| Operating acceptance | Actual research use, failure/retry observations, and final acceptance |

The delivered financial review planner, explicit-input macro calculations, and
bounded AI claim-review cues support these steps. They do not close their evidence
requirements. Choose the earliest unmet in-scope acceptance gate.

## Deferred

Broker integration, public hosting, real-time trading feeds, unapproved social
scraping, and new workbook parsers without a consuming workflow require separate
scope and prerequisites. Keep their status explicit.
