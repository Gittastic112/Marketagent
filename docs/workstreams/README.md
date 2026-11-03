# Workstream coordination

[Knull](../../Knull%28readme%29.md) is the current five-agent execution plan.
The product roadmap remains the long-term priority owner.

- [ownership.tsv](ownership.tsv) is the exclusive write allowlist. `file` means an
  exact path; `tree` reserves a directory including future files and ends in `/`.
  Paths are literal, not glob patterns. Unlisted paths are frozen for all agents.
- W1 owns briefing/research integration; W2 financial-source coverage; W3 portfolio
  history; W4 sensitivities; W5 backup/recovery. The plan defines behavioral limits
  inside each allocation. A broad file does not grant unrelated feature scope.
- Each agent writes only its own evidence tree. New trees are reservations until
  an agent starts; there are no completion receipts yet.
- The coordinator owns this directory's index/manifest, the plan and central docs.
  During parallel work agents propose shared changes in their own receipt rather
  than editing these files. After integration, put dated proof in the archive and
  keep the current handoff short.

Use the [runbook](../08-execution-runbook.md#parallel-workstream-checks) for guards
and isolated verification. The guard checks paths, not source semantics, runtime
isolation, test success or whether a supplied changed-file list is complete.
