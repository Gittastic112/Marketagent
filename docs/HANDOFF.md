# Agent handoff

## Latest source boundary

PR 24 is the last verified installed application. The nine release reviews used public commit `ef2e2d668dce84d55714a43f63b22cdecb40267a`. The new release adds a dated first valuation and a decision on a pinned price. [Release evidence](current-state.md#dated-validation) · [Earlier integration record](archive/checkpoints/2026/integration-review-2026-11-19.md)

The November 19 release is installed locally. The signed-in Today page and its Evidence Trail passed a read-only check after the update. The original database and asset storage were preserved. [Installed verification](current-state.md#dated-validation) · [Installed-stack procedure](operations.md#select-the-installed-local-stack)

## Next work

| Order | Action | Finish condition |
|---|---|---|
| 1. Company evidence (M05) | Review the fifteen incomplete company/input combinations and establish publication eligibility for benchmark datasets and industry weights. The November 12 Alphabet minority-interest estimate has passed original-source review. | Track the precise missing disclosures and compare claims on the same date, currency and accounting basis. [Company ledger](limitations.md#selected-company-review-follow-up) |
| 2. Valuation workflow (M06) | Use the draft’s research date to inspect and apply an original revenue or net-income revision. Review the first calculation and confirm the saved version. | Validate the selected issuer on its financial basis as original evidence becomes available. The [valuation guide](user-guide.md#review-a-filing-and-valuation) describes the controls. |
| 3. Portfolio and research | Review a marked close, select a thesis assumption and record the reason to retain it, propose a change or seek more evidence. | Keep the price as pinned, original source and any chosen model version together. Record real use and any failures. [Product roadmap](roadmaps/product-roadmap.md#immediate-delivery-order) |

All nine [release-completion reviews](workstreams/README.md#release-completion-round) returned. A complete first-model submission has a durable receipt. Retrying it returns the same version. Debt subtotals remain held. The [dated release evidence](current-state.md#dated-validation) distinguishes the technical checks from completed issuer research.

Use the [adapter worklist](roadmaps/ui-adapter-worklist.md#implementation-backlog-from-the-zip) when a task needs a feed or a library. Six bounded original-source or pinned-reference examples have evidence. US corporate actions, transcript corrections and scanned-page OCR have [specific prerequisites](limitations.md#installed-adapters-and-remaining-source-prerequisites).

M01 through M04 have 40 accepted gate points. M05 is the first open gate. Five business days of actual research use and final user acceptance remain open. [Milestone board](roadmaps/completion-tracker.md#milestone-board)

## Start a change

1. Inspect local Git status. A working checkout can contain earlier edits beyond its branch tip. Resolve the exact GitHub commit for an independent review.
2. Read the nearest AGENTS.md, then the owning route, service, model, UI and tests listed in the [code map](code-map.md). For parallel work, choose the [review or implementation workflow](workstreams/README.md).
3. Use the [execution runbook](execution-runbook.md) for tests. Distinguish inspected source, isolated Mock Data, a signed-in local observation and original-source evidence when reporting results.

## Installed data and recovery

Use the existing Compose project and its verified image and volume selections. Keep the live database, original assets, reviewed evidence and one verified recovery set at rest. A documentation change needs no dump or application rebuild. Use the [installed-stack procedure](operations.md#select-the-installed-local-stack) and [retention policy](operations.md#essential-retention-policy).

The [documentation index](README.md) locates the user guide and technical references. The [limitation ledger](limitations.md) owns open product and operating boundaries. Earlier releases and their receipts are linked from [Current State](current-state.md).
