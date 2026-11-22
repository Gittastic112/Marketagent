# Agent handoff

The November 20 release was installed and verified on November 21 from local application commit `17d5efcc36aba3a6c464f14f8e67d268bb955c1c`. It supports dated first valuations and decisions on a pinned stock close. The four services passed their checks, the database reached `x6x6x6x6x6x6`, and one verified recovery set remains. [Installed verification](current-state.md#dated-validation) · [Installed-stack procedure](operations.md#select-the-installed-local-stack)

The nine Pro reviews used GitHub base `ef2e2d668dce84d55714a43f63b22cdecb40267a`. The November 21 follow-up records the four issuer checks and updates the project guides. Use the release branch’s pull request history to check publication and hosted test results. [Review round](workstreams/README.md#release-completion-round) · [Release pull request history](https://github.com/Gittastic112/Marketagent/pulls?q=is%3Apr+head%3Acodex%2Fdated-valuation-and-thesis-decisions-20261120)

## Next work

| Priority | What closes it |
|---|---|
| 1. Company evidence (M05) | Five of twenty company/input combinations are supported on their stated basis. Fourteen are partial and one is held. Reopen a field when its specified original disclosure, period and accounting basis can be reconciled to November 12. Industry mappings also need eligible benchmark versions and sourced weights. [Company-by-company ledger](limitations.md#selected-company-review-follow-up) |
| 2. First valuation (M06) | Consolidated annual revenue and net income passed the draft workflow for Apple, NVIDIA, Meta and Alphabet. Review the selected company's remaining forecast and equity-bridge inputs, then preview and confirm a meaningful valuation. [Per-company field lists](../data/reviews/issuer-workflow-verification-20261121.json) · [Valuation guide](user-guide.md#review-a-filing-and-valuation) |
| 3. Real research and acceptance | Use a chart pin and a source on a real thesis question. Record use dates and failures. Five business days of actual research and final user acceptance remain open. [Chart guide](user-guide.md#record-a-decision-on-a-stock-chart) · [Milestone board](roadmaps/completion-tracker.md#milestone-board) |

For implementation, open the relevant [code-map section](code-map.md#route-a-domain-change) and [test environment](execution-runbook.md#choose-the-right-environment). For a provider prerequisite, use the [adapter worklist](roadmaps/ui-adapter-worklist.md#implementation-backlog-from-the-zip).
