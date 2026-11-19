# Agent handoff

## Latest source boundary

The November 19 release is on `main`. It addresses all 19 findings from the four reviews, plus the mobile target size for editing a company thesis. The [integration record](archive/checkpoints/2026/integration-review-2026-11-19.md) maps the fixes to their evidence. [Merged application PR](https://github.com/Gittastic112/Marketagent/pull/24) · [Verified application commit](https://github.com/Gittastic112/Marketagent/commit/e57d50f0bba1c5f03a5e97dc8a759dd2b11e7f78)

The November 19 release is installed locally. The signed-in Today page and its Evidence Trail passed a read-only check after the update. The original database and asset storage were preserved. [Installed verification](current-state.md#dated-validation) · [Installed-stack procedure](operations.md#select-the-installed-local-stack)

## Next work

| Order | Action | Finish condition |
|---|---|---|
| 1. Company evidence (M05) | Work through the remaining annual fields for Apple, NVIDIA, Meta and Alphabet, using original filings and the chosen November 12, 2026 valuation date. The eleven previously held candidates already have dispositions. | Record an exact disclosure, period, units and review decision, or document the specific unresolved component. The [company-by-company ledger](limitations.md#selected-company-review-follow-up) identifies each gap. |
| 2. Valuation workflow (M06) | Carry selected dated evidence into an explicit draft proposal and add a preview before the first model save. Existing saved-model edits already have a preview and version history. | Reproduce the proposed assumptions from their source revisions, confirm the reviewed calculation and verify a retry-safe save. [Workspace specifications](roadmaps/research-workspace-plan.md#delivery-sequence) |
| 3. Portfolio and research | The USD sample portfolio reconciles on its two stored dates. Connect a dated filing or marked move to a thesis decision and a reviewed valuation change when warranted. | Preserve the source, price observation and model version. A real multi-currency account and a configured benchmark still require their own evidence. [Product roadmap](roadmaps/product-roadmap.md#immediate-delivery-order) |

For these priorities, the [Knull-led release-completion round](workstreams/README.md#release-completion-round) assigns one chat per issuer, three workflow reviews and two independent checks. Knull returns one source-backed handoff for local verification and implementation.

Use the [adapter worklist](roadmaps/ui-adapter-worklist.md#implementation-backlog-from-the-zip) when a task needs a feed or a library. Six bounded original-source or pinned-reference examples have evidence. US corporate actions, transcript corrections and scanned-page OCR have [specific prerequisites](limitations.md#installed-adapters-and-remaining-source-prerequisites).

M01 through M04 have 40 accepted gate points. M05 is the first open gate. Five business days of actual research use and final user acceptance remain open. [Milestone board](roadmaps/completion-tracker.md#milestone-board)

## Start a change

1. Inspect local Git status. A working checkout can contain earlier edits beyond its branch tip. Resolve the exact GitHub commit for an independent review.
2. Read the nearest AGENTS.md, then the owning route, service, model, UI and tests listed in the [code map](code-map.md). For parallel work, choose the [review or implementation workflow](workstreams/README.md).
3. Use the [execution runbook](execution-runbook.md) for tests. Distinguish inspected source, isolated Mock Data, a signed-in local observation and original-source evidence when reporting results.

## Installed data and recovery

Use the existing Compose project and its verified image and volume selections. Keep the live database, original assets, reviewed evidence and one verified recovery set at rest. A documentation change needs no dump or application rebuild. Use the [installed-stack procedure](operations.md#select-the-installed-local-stack) and [retention policy](operations.md#essential-retention-policy).

The [documentation index](README.md) locates the user guide and technical references. The [limitation ledger](limitations.md) owns open product and operating boundaries. Earlier releases and their receipts are linked from [Current State](current-state.md).
