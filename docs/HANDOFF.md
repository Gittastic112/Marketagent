# Agent Handoff

## Latest boundary

November 10, 2026: repository presentation and documentation cleanup. This pass
changes navigation, documentation ownership, and publication hygiene. It does not
change application behavior, financial evidence, migrations, or the running stack.
The [cleanup checkpoint](archive/checkpoints/2026/repository-presentation-2026-11-10.md)
owns its exact changes and validation.

GitHub confirms [PR9](https://github.com/Gittastic112/Marketagent/pull/9) merged on
November 9 at `9f17dd6a`. Earlier statements that it awaited approval are obsolete.
The default branch is `codex/worktree-recovery`; its name is retained. Local HEAD
is `fba390bf`, with substantial pre-existing uncommitted work. Do not reset, clean,
or broadly stage this checkout to make it match GitHub. Publish only reviewed
changes against the current remote base.

## Product and data scope

- Local research/demo for US and India equities, with USD portfolio reporting.
- November 9 authorizes four technology companies, hypothetical holdings, and
  Sample Apple research. The sourced Apple valuation is an Estimate with explicit
  analyst assumptions. None of this proves genuine transactions or complete facts.
- The November 5 removal of the historical companies/scenarios remains effective.
  Do not restore that universe or expand it as a cleanup/setup side effect.
- The 60 explicitly approved historical database archives were deleted November 9.
  Retain newer backups, source originals, review receipts, and failed evidence.
- No new external-AI permission, public deployment, broker activity, or local
  disposable dataset is authorized by a documentation task.

## Latest delivered behavior

The dashboard selects a funded owned portfolio by default and supports explicit
selection. Daily Brief leads with stored content; optional controls are collapsed.
Sample provenance, missing inputs, and filing baselines remain separate.
Thesis fields and paragraph formatting round-trip; financial review planning,
macro calculations, and AI claim-review cues retain their stated boundaries.

[Current State](current-state.md) owns validation dates and counts. The
[portfolio/UI checkpoint](archive/checkpoints/2026/portfolio-ui-2026-11-09.md)
and [analyst checkpoint](archive/checkpoints/2026/analyst-workflows-2026-11-09.md)
retain implementation and runtime evidence.

## Existing installation

The last recorded installation uses project `market-intelligence-product-20261107`
and its ignored runtime-image override. Source refresh and pgAdmin were stopped;
Daily Brief scheduling was running. These are November 9 observations, not a
fresh runtime inspection. Use [Operations](operations.md) and inspect actual
service/volume identity before an operational change. Preserve the database,
settings, original assets, backups, and rollback images.

## Next work

Use the [roadmap](roadmaps/product-roadmap.md) for priority and the
[single limitation ledger](limitations.md#ordered-operator-handoff)
for missing prerequisites. M01-M04 retain 40 accepted gate points; cleanup does
not advance product acceptance. Source completeness and actual-use days cannot
be supplied by tests. Host/off-device protection and the additional populated
recovery rehearsal remain deferred.
