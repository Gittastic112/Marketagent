# Active Product Planning

Product priorities, percentage execution and capability status have separate owners:

| Document | Purpose |
|---|---|
| [`product-roadmap.md`](product-roadmap.md) | Ordered priorities, acceptance gates, and deferred work |
| [`completion-tracker.md`](completion-tracker.md) | Ten cumulative 10% milestones, exact tasks, dependencies, status and evidence |
| [`feature-register.md`](feature-register.md) | Current shipped/partial/proposed status by product area |
| [Knull](../../Knull%28readme%29.md) | Next five independent agents, exact file ownership, phases and completion gates |

The [ownership manifest](../workstreams/ownership.tsv) supports that batch, not a
second roadmap. Per-agent evidence is reconciled once by the coordinator.
Percentage requests use the completion tracker. It maps Knull's existing technical
workstreams into the full local-release sequence; no agents start automatically.

Planning documents are not proof that a feature works. Verify code, tests, and
`../00-current-state.md` before implementation.

Dated checkpoints, previous assessments, provider research, and superseded
multi-thousand-line plans are preserved under [`../archive/`](../archive/).
