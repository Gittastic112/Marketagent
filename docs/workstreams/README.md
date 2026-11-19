# Coordinate a project review

## Four independent ChatGPT Pro reviews

For a code review, start with [the four-chat assignments and copyable Knull prompt](four-pro-chats.md). Pin one published commit and ask each chat to open an owning file at that revision. The four assignments cover data and adapters, valuation and portfolio math, research workflows and UI, and release safety and privacy.

Each chat returns findings with a commit permalink, observed or code-traced behavior, the consequence and a proposed check. One local integrator deduplicates findings, verifies them against the current checkout and implements accepted changes. Share public source and tests only. Keep private research, credentials, account data and backups local.

The four-chat packet is optional and can be deleted after the round. Remove its link from this page at the same time. The product roadmap, application and local workstream rules are independent of that packet.

## Parallel local implementation

For a batch explicitly assigned to local workers, use the [workstream scope index](plan.md), an exact edit allocation and one integration owner. Reserve shared contracts, migrations and central documents for that owner. Use isolated tests for writers and one normal installation for the verified result. The [runbook](../execution-runbook.md#parallel-workstream-checks) covers path checks and environment isolation.

The historical [five-workstream allocation](ownership.tsv) assigns briefing, financial sources, portfolio history, sensitivities and recovery. Its file and directory reservations apply to that assigned batch. The [evidence index](evidence/README.md) preserves earlier receipts. The [milestone board](../roadmaps/completion-tracker.md#milestone-board) owns product acceptance.
