# Documentation rules

Follow the [repository rules](../AGENTS.md). The [documentation index](README.md) routes readers to the current guide for their task.

- Put the next action and release boundary in the [handoff](HANDOFF.md), dated observations in [current state](current-state.md), missing evidence in [limitations](limitations.md) and acceptance decisions in the [milestone board](roadmaps/completion-tracker.md#milestone-board). Link to the owner when another guide needs the same facts.
- Use the [code map](code-map.md#route-a-domain-change) for implementation paths. The [runbook](execution-runbook.md) owns validation commands. [Operations](operations.md) owns runtime and recovery commands.
- A new current guide needs a clickable path from the documentation index, either directly or through its section guide. Relink incoming references when a file moves. Keep widely used section anchors working.
- Put superseded handoffs, plans and assessments in the matching [archive](archive/README.md) and link them from its index. Retain the original scope and date. Preserve the paths and contents of dated workstream receipts and private user documents.
- During an assigned parallel batch, workers record evidence inside their allocation. The coordinator updates shared guides after integration. [Coordination and ownership](workstreams/README.md#parallel-local-implementation)
- Keep the handoff under 120 lines and current state under 180. Distinguish code inspection, isolated tests, builds, installed observations and actual research use. Replace stale status and link older evidence by date.

Run both checks from the repository root after a documentation change.

~~~bash
python3 -m unittest scripts.test_check_docs
python3 scripts/check_docs.py
~~~

The checker verifies clickable navigation, paths, anchors, frontend pages, backend routers, command inventories and the documented migration head. [Verification environments](execution-runbook.md#choose-the-right-environment)
