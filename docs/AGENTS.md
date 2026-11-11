# Documentation Rules

Read the [root rules](../AGENTS.md). Current docs describe present behavior;
archives preserve history, not instructions.

- HANDOFF.md owns the latest boundary, immediate next work, and validation links.
- current-state.md owns product status and dated verification evidence.
- code-map.md owns code entry points and change routing.
- architecture.md owns runtime flows and dependency boundaries.
- execution-runbook.md owns development and validation commands.
- operations.md owns runtime, provider, credential, backup and recovery commands.
- roadmaps/product-roadmap.md owns priorities; feature-register.md owns capability
  status. Do not use old checkpoint numbering as a queue.
- roadmaps/completion-tracker.md owns percentage requests and cumulative acceptance
  gates. "Finish 10%" means M01; "next 10%" means the earliest unfinished milestone.
- The [workstream design](workstreams/plan.md) retains technical assignments for
  an explicitly launched batch. [Ownership](workstreams/ownership.tsv) owns edit
  allocations; the completion tracker owns current acceptance status.
- limitations.md is the single limitation ledger.
- docs/skills contains task-specific workflow references. Do not duplicate their
  complete instructions into AGENTS.md or the handoff.

During the parallel batch, agents write their own allocated evidence directories
and propose central-doc changes there. The coordinator reconciles current docs
after integration; five agents must not append to the handoff or ledger at once.

Replace current status rather than appending milestones. Archive detailed proof
under archive/checkpoints/YYYY, old handoffs under archive/handoffs, and uncertain
old material under archive/needs-review. Preserve user documents.

Keep the handoff under 120 lines and current state under 180. Do not repeat test
counts throughout all docs. Distinguish source tests, production builds, isolated
browser fixtures, genuine-input proof, and previously recorded runtime evidence.

Use relative Markdown links to real paths. Do not invent planned folder trees.
Run python3 -m unittest scripts.test_check_docs and python3 scripts/check_docs.py.
Nested backend/frontend agent files are checked too. Update only affected docs.
