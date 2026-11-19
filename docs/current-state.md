# Current state

November 19, 2026. Marketagent is an installed local equity-research, valuation and portfolio application. Its accepted release scope is personal research/demo. A new installation starts with its own database. The [user guide](user-guide.md) describes the installed workflows and the [feature register](roadmaps/feature-register.md) records their implementation status.

## Product position

| Workflow | What is available |
|---|---|
| Today and Daily Brief | A dated portfolio summary, brief and active alerts come before the six-item research queue. Stored input counts, source links and review status are visible. Private brief intake supports text and PDF with optional, consented AI review. |
| Company research | Filing and event evidence, annual financial review, private theses and dated decisions. The closing-price chart opens source context and private annotations on an individual observation. |
| Valuation | Reviewed drafts, versioned FCFF and specialized models, saved-model previews, scenarios, sensitivities, reverse DCF and reviewed peer comparisons. The selected date on financial evidence alone does not rebase a model. |
| Portfolio | Recorded activity, dated snapshots, returns, attribution, benchmark comparison and price risk. The example holdings are hypothetical. |
| Adapters and Research Lab | Explicit market and source actions, candidate peers, hypothetical allocations, simulations and report exports with saved inputs and hashes. The analysis and Camelot profiles were installed. [Adapter guide](adapters/README.md) |
| Operations | Local sign-in, owner-scoped records, optional workers, Processing Runs, schema readiness and recovery tools. The source-refresh worker is opt-in. |

## Dated validation

The November 19 [integration review and verification record](archive/checkpoints/2026/integration-review-2026-11-19.md) covers the 19 findings in [PR 24](https://github.com/Gittastic112/Marketagent/pull/24). All seven [release checks](https://github.com/Gittastic112/Marketagent/actions/runs/44495900182) passed before merge, including 2,272 core backend tests, 139 optional adapter tests and 92 standard browser workflows. The three opt-in Mock Data provider workflows passed separately on local Firefox. The dated observations below identify the installed version. Separately, a read-only reconciliation of the existing USD sample portfolio passed 61 comparisons across its two stored dates. Each holding agreed with its recorded quantity and source price. Cash, total value and period attribution reconciled. Base-currency FX was one. No benchmark was configured.

The November 18 application-code release was [PR 22](https://github.com/Gittastic112/Marketagent/pull/22), merged as [`e3b39d4`](https://github.com/Gittastic112/Marketagent/commit/e3b39d404b72e69ae7084d6c77f51bd04d73f3d9). All seven jobs passed on the [merged application revision](https://github.com/Gittastic112/Marketagent/actions/runs/44419018336).

| Evidence | Scope and result |
|---|---|
| Hosted checks | 2,260 core backend tests passed with 37 skips. The separately installed optional profile passed 137 tests. The frontend passed 422 tests. The browser suite passed 90 workflows, including saving and reopening a price note using explicitly labeled Mock Data. The optional run overlaps the core suite. |
| Installed application | A read-only readiness check found the expected and installed database revision both at `w5w5w5w5w5w5`. Frontend, backend and PostgreSQL reported healthy. The brief scheduler was running. A signed-in check on the chart release opened a real stored move, a preceding-date filing and the private note form. |
| Stored market coverage | Each of the four scoped companies had 250 stored USD unadjusted closes, November 10, 2025 through November 6, 2026. A November 18 read found 33 moves of at least 5%. Six had non-sample company evidence on the relevant dates and 27 had none. The six matches establish timing only. |
| Data preservation | The price-pin migration created an empty table. All 109 pre-existing business-table fingerprints and the original PDF matched after installation. The single verified format-3 recovery set matched the pre-change data. The [retention policy](operations.md#essential-retention-policy) governs its replacement. |
| Adapter evidence | A pinned FinanceDatabase peer snapshot, an SEC annual amendment and repeat intake, an NSE dividend, two ALFRED snapshots around a revision, an ambiguous OpenFIGI listing, and cells from an original Apple PDF through Camelot were checked. [Original-source release receipt](../data/reviews/ui-adapter-release-20261118.json) |

Hosted tests, stored-source observations and actual use answer different questions. A source match can lead to a document. The application leaves the cause of a price move unverified. [Chart rules](reference/workflows.md#company-price-history-and-thesis-pins)

## Earlier release evidence

| Date | What the record covers |
|---|---|
| November 18 | The [combined adapter and Geist release](https://github.com/Gittastic112/Marketagent/pull/20) included the November 16 repairs. The [workflow repair receipt](../data/reviews/review-adapter-workflows-ten-sets-20261118.json) covers the next ten fixes. The [publication and recovery follow-up](https://github.com/Gittastic112/Marketagent/pull/21) records that release's final checks. |
| November 15 and 16 | [Initial review repairs](../data/reviews/review-repairs-ten-sets-20261115.json), [financial integrity and the Today layout](archive/checkpoints/2026/review-financial-integrity-release-2026-11-15.md), [evidence and model workflows](../data/reviews/review-evidence-workflows-ten-sets-20261116.json), and [research, worker and recovery repairs](../data/reviews/review-research-recovery-nine-sets-20261116.json). |
| November 12 through 14 | [Selected financial history](archive/checkpoints/2026/handoff-review-2026-11-12.md), [dispositions of the eleven held candidates](../data/reviews/financial-review-completion-20261112.json), [five-input review](../data/reviews/financial-five-input-review-20261112.json), [dated valuation input review](../data/reviews/valuation-inputs-asof-20261112.json), [workspace improvements](../data/reviews/research-workspace-ten-sets-20261114.json) and [dependency fixes](../data/reviews/dependency-security-20261114.json). |
| Earlier evidence | The [checkpoint index](archive/checkpoints/2026/README.md) covers recovery, financial reviews, installed UI checks and repository work. The [previous dated validation table](https://github.com/Gittastic112/Marketagent/blob/e3b39d404b72e69ae7084d6c77f51bd04d73f3d9/docs/current-state.md#dated-validation) preserves the longer chronology. |

## Acceptance and next priorities

M01 through M04 are accepted for **40 of 100 milestone gate points**. M05 is next. Three selected annual histories per company are reviewed. Apple and NVIDIA each have 10 of 13 source-linked checklist fields per year. Meta and Alphabet each have 8 of 13. No selected candidate awaits disposition. The [financial ledger](limitations.md#selected-company-review-follow-up) names the missing disclosures and reconciliations.

Next come dated evidence in a draft, initial-model preview, a connected source-to-thesis decision and any resulting reviewed model change. The last user-reported actual-use count was zero. M10 requires five actual business days and final acceptance. Genuine brokerage validation, host/off-device protection and populated legacy conversion retain their own scope and prerequisites. [Milestone board](roadmaps/completion-tracker.md#milestone-board) · [Handoff](HANDOFF.md) · [Limitations](limitations.md)
