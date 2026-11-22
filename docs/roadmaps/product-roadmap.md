# Product roadmap

The first open milestone is M05, financial coverage for four selected companies. The November 20 release installed on November 21 added dated first-valuation confirmation and chart-to-thesis decisions. The [milestone board](completion-tracker.md#milestone-board) owns acceptance and [current state](../current-state.md#dated-validation) records release verification.

## Planning rule

Finish the connected review workflow before adding isolated engines or schema.
Completion requires backend behavior, frontend states, source/ownership metadata,
tests, and documentation to agree.

The user also requested essential-only storage. Apply the
[retention policy](../operations.md#essential-retention-policy): no routine database
dumps for documentation/UI work, no permanent rollback stacks, and explicit roles
for the small amount of recovery material retained. Do not confuse deleting build
waste with permission to destroy unique source evidence or live records.

Preserve the November 9 four-company research scope. The removed historical
universe must not be restored automatically. Further issuer intake needs an
explicit company/source scope. The October 17 research/demo revision defers
host/off-device work and excludes genuine portfolio validation from v1.

The [workstream design](../workstreams/plan.md) retains detailed technical slices.
Its ownership rules apply to an explicitly assigned parallel batch; the plan
does not dispatch agents or replace current status.

## Immediate delivery order

| Order | Deliverable | Evidence required |
|---|---|---|
| M05 | Complete the remaining annual inputs for the four scoped companies. Start with the missing component of each issuer's debt, working capital or equity claim. | Match each original disclosure to its period, currency, accounting and share scope. [Selected-company ledger](../limitations.md#selected-company-review-follow-up) |
| M06 | Validate first-model proposals against complete issuer evidence. Annual revenue and net-income revisions can supply the draft. | First preview and confirmation preserve source identity, period and currency. Extend mapping only for a complete economic quantity. [Workspace plan](research-workspace-plan.md#delivery-sequence) |
| M07 and M08 | Exercise a pinned price, an original filing and the selected assumption in actual research. A proposed change can refer to a saved valuation version. | The USD example reconciles on its two stored dates. Actual portfolio coverage depends on dated prices, currency conversions and benchmark inputs. |
| M09 and M10 | Exercise the changed workflows on desktop and mobile, verify recovery within scope and record five actual business days of research use. | Keep technical results, user-reported use and final acceptance separately recorded. |

The [Knull-led round](../workstreams/README.md#release-completion-round) returned its nine reviews. The [local handoff](../HANDOFF.md#next-work) tracks which source checks and workflow changes have passed and what remains.

The [adapter worklist](ui-adapter-worklist.md#implementation-backlog-from-the-zip) names the remaining work in each of the 16 packages. For example, allocation and simulation already accept supplied returns. Connecting an owned portfolio requires aligned histories, cash flows, distributions and FX.

### Review repair sequence

The November 15 review produced 39 primary findings. The [intake register](../../data/reviews/code-review-intake-20261115.json) identifies each finding and its required check. The [repair ledger](../limitations.md#returned-code-review) records the published outcomes for R0 through R8, overlapping decisions and the remaining legacy-conversion limits.

## Boundaries to preserve while delivering

### Frontend and backend truth

Preserve explicit missing/zero, loading, empty, unavailable, stale, partial,
unconfigured, and Mock Data states. Verify representative desktop/mobile behavior,
authenticated server/browser access, and provenance through saved-input,
retry, and stale-write workflows. A build or source-string test alone is not
browser evidence. New methodology defaults must be reviewed/versioned or remain
explicit user assumptions.

### Financial and source coverage

Review the selected companies' financials and complete supported valuation
bridges before expanding coverage. Retained AAPL/APSEZ reference certification
and removed-universe receipts remain historical, not current database inventory.

The next issuer/layout requires official sources, hashes, periods, units,
security/share scope, reconciliation, and explicit promotion. Minority interests,
cross-holdings, leases, currency, and dilution must stay visible.
NSE MCP already supports scoped quotes, history and corporate actions. Expanding India coverage requires a permitted endpoint, documented freshness and limits, bounded requests, Processing Runs and independent checks for the new use case. Other exchanges and unsupported disclosures retain manual intake.

### Daily evidence-to-decision loop

Connect dashboard changes to exact sources, thesis review, valuation relevance,
and portfolio exposure. Stored-public coverage counts, private research intake,
search, reversible archiving, comparison receipts, and deterministic scheduling
are implemented.

Next acceptance depends on repeatable use and interpretation quality. Coverage
must disclose its window, caps, exclusions, failures, and review state. Exact
quotes or differing directions do not prove economic contradiction. No claim of
comprehensive overnight news coverage or automatic numerical forecast edits.

### Portfolio attribution and research context

Preserve dated activity replay, FX, TWR/MWR, price/flow/position attribution,
benchmark comparison, risk alignment, and residual diagnostics.
Stale/missing prices and provisional histories must prevent false precision.
DCF gaps are Estimates, not annualized forecasts or trading instructions.

The existing example workflow can be checked against its stated inputs.
Genuine activity and multi-currency proof require a later scope with real
records. CSV preview/apply must retain exact hashes, ownership, source metadata,
duplicate handling, atomic writes, and Processing Runs.

### Provider health and market regime

Keep configuration, attempts, failures, freshness, source coverage, formula,
drivers, and confidence observable. Persisted FRED NFCI provides one
exact-record-linked macro calculation; unsupported options/liquidity/volume/
breadth feeds remain manual. A successful connection is not complete source coverage.

### Source-backed AI research

Retain exact citations, provenance, bounded output contracts, explicit disclosure,
and current owner/provider/action consent. Permission history and each output's
permitting decision are persisted. Revocation blocks future sends but cannot
recall data already transmitted.

Broaden evaluation using independently reviewed sources and known failure cases.
Numeric/period/instruction cues are review aids, not semantic truth.
Interpretation approval must not silently change financial facts or assumptions.
The [AI boundary](../limitations.md#ai-boundary) owns the exact limitations.

## Source and expansion prerequisites

| Work | Entry requirement |
|---|---|
| Financial/model review | Supported missing disclosures and explicit assumptions within the selected scope |
| Additional issuer/layout | Selected company, dated official reports, reproducible reference checks |
| Additional India coverage | The installed NSE MCP adapter has a verified dividend observation. Verify the specific permitted endpoint, listing, session and access terms before expanding price or filing coverage. |
| Peer comparison expansion | Permitted peer data with currency, accounting, and period definitions before normalization/scoring |
| Operating acceptance | Actual research use, failure/retry observations, and final acceptance |

The delivered financial review planner, explicit-input macro calculations, and
bounded AI claim-review cues support these steps. They do not close their evidence
requirements. Keep cumulative acceptance in the existing gate order while following
the implementation packages above. Do not expand scope to fill an empty screen.

## Deferred

Broker integration, public hosting, real-time trading feeds, unapproved social
scraping, and new workbook parsers without a consuming workflow require separate
scope and prerequisites. Keep their status explicit.
