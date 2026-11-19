# Four independent reviews of Marketagent

Knull coordinates four ordinary ChatGPT Pro chats. The shared input is **one exact Git commit**. The deliverable is four evidence-backed work orders and one deduplicated queue for local implementation. The [coordination index](README.md) links to this optional packet. When retiring it after the review, remove the file and that link together. It contains no runtime configuration or user records.

## Start the round

1. Resolve the repository's current `main` to a full commit SHA on GitHub. Use the same immutable tree link in all four chats. Record any unpublished local change as outside this round. If reviewing an unmerged feature, use its published head SHA and identify it as such.
2. Give each chat its row below, this packet, the root and nearest `AGENTS.md`, `docs/HANDOFF.md`, and the relevant rows of `docs/code-map.md`. Ask it to open a specific owning file and quote a symbol with its commit permalink before starting. A link alone does not prove the chat can read it.
3. If a chat cannot read the tree, give it just its allowlisted source files, associated tests and relevant public docs from that SHA. Include a manifest with the SHA and paths. Exclude user records, backups, configuration values, uploads, private notes, account details and local logs. A missing file or unavailable provider receipt is an explicit evidence gap.
4. Keep the four chats read-only. Each may inspect a neighbor's interface to trace a caller. Route a proposed change in that neighbor to its owner. All dates, units, assumptions, evidence levels and open questions must survive the handoff.

## Review assignments

| Chat | Owns the review of | Starting paths and the task to return |
|---|---|---|
| **1. Data, sources and adapters** | Company/listing identity, prices and corporate actions, document acquisition, extraction and sourced financial facts. Owns what a field means on arrival and how it gets to review. | Start in `backend/app/providers/`, `backend/app/services/market_data/`, `backend/app/services/sec_ingestion.py`, `backend/app/services/sec_xbrl_ingestion.py`, and `docs/roadmaps/ui-adapter-worklist.md`. Trace one price to its stored quote or close, and one annual filing fact through a Processing Run to a review candidate. Return a matrix of shipped code, fixture proof, original-source proof and missing entitlements. For the chart, inspect provider, listing, currency, price basis, filing date versus publication time, corrections and missing sessions. [Source-matching rules](../reference/workflows.md#company-price-history-and-thesis-pins) |
| **2. Valuation and portfolio math** | Company-specific financial input mapping, saved valuations, sensitivity, holdings, cash flows, benchmarks, simulation and performance. Owns calculations after input acceptance. | Start in `backend/app/services/valuation_source_inputs.py`, `backend/app/services/valuation_review.py`, `backend/app/services/portfolio_replay.py`, `backend/app/services/portfolio_performance.py`, and `docs/roadmaps/completion-tracker.md`. Follow one held field into a model and one dated transaction into a return. Return the missing original input, convention, independent reconciliation or actual user choice for each discrepancy. For the chart, audit the comparison denominator, adjustments, gaps, splits and precision in the [timeline calculation](../../backend/app/services/price_timeline.py). |
| **3. Research workflow and interface** | Today, company research, evidence review, thesis notebook, brief and alert navigation, forms and browser behavior. Owns what the person can see, understand and do. | Start in `frontend/app/page.tsx`, `frontend/app/companies/[id]/`, `frontend/app/thesis-notes/`, `frontend/components/`, `frontend/lib/api/` and `frontend/e2e/`. Walk from a price move to its dated source to a private note saved against a specific thesis. Return the smallest screen/interaction changes, distinct missing-data states and keyboard/mobile acceptance steps. Trace the actual component and API caller. |
| **4. Platform, privacy and release** | Authentication, account scope, shared API transport, persistence/migrations, CI, private local installation, retention and recovery. Owns proving release safety. | Start in `backend/app/api/dependencies.py`, `backend/alembic/`, `frontend/app/api/backend/[...path]/route.ts`, `scripts/`, `.github/workflows/`, `docker/`, `docs/execution-runbook.md` and `docs/operations.md`. Trace a signed-in read/write, a retry and a schema upgrade. Return owner-isolation and concurrency checks, compatibility with existing rows, an install verification and the minimal recovery/cleanup boundary. |

For cross-cutting features, the four reviews intentionally inspect different decisions on the same path. Chat 1 owns provenance. Chat 2 owns math. Chat 3 owns user interaction. Chat 4 owns persistence safety, access and release. The local integrator resolves contract changes once.

## Return format for each chat

Start with the exact SHA, files actually opened, workflows inspected and gaps in access. For each distinct finding give:

| Field | Required content |
|---|---|
| Identifier and severity | Use `1-01`, `2-01`, etc. Critical means risk of data loss, privacy exposure or materially wrong financial output. Explain the consequence. |
| Evidence | Commit permalink and symbol, input or action, expected result and observed or code-traced behavior. Label each as inspected code, automated test, genuine-source receipt, local observation or unverified inference. |
| Proposed change | Smallest owning files, dependencies on other chats and the decision that requires an owner. Cite original vendor or issuer documentation for external claims. |
| Acceptance | A falsifiable example, exact assertions and the local check that would close the finding. Include the meaning of a missing value, failure or correction where relevant. |

Return up to five consequential findings, then remaining coverage and open questions. Zero findings is valid. Never invent a defect to meet a quota. List speculative ideas separately. A proposed test stays “proposed” until a named environment actually runs it.

## Integrate locally

1. Group by root cause. Preserve all supporting permalinks, assign one owner per fix, and separate confirmed bugs, optional features, missing original evidence and owner decisions.
2. Sequence the accepted work. Resolve listing and input semantics first, then shared API and migration contracts, calculations and persistence, then interface behavior. Privacy and regression checks apply throughout. A commercial entitlement or a private-use acceptance task can remain blocked while independent work proceeds.
3. For **local parallel coding**, use one clean worktree per approved change group at the same base. The coordinator writes an exact, disjoint file list per worker and owns shared contracts, migrations, lockfiles, central docs and merge order. Use the repository's workstream ownership rules for that batch. Never start four copies of the normal app or give a worker a live database.
4. Reproduce the issue locally, add a focused regression, implement, then run relevant suites, browser flows and migration checks against disposable data. Verify new schema on a populated copy where needed. Install only the integrated revision. Verify loopback health, stored counts and original assets. Preserve the single verified recovery set under the operations policy.
5. Return one queue with owner, evidence, dependencies, status and next authorized action. Record what actually ran and which claims still require a licensed feed, original filing, observed user behavior or a financial judgment. Delete temporary worktrees/builds after integration and verification.

## Prompt for Knull

> Coordinate four independent read-only ChatGPT Pro reviews of Gittastic112/Marketagent. Resolve main to an exact commit and open docs/workstreams/four-pro-chats.md at that commit. Use its assignments, access check and return format. Give each chat only its lane and the same pinned source tree. If the packet is newer than main, pin its published feature commit explicitly for all four. If a chat cannot open its files, supply a source-only lane packet or mark it blocked. Keep private app data, backups, secrets and local logs out of all chats. Collect all four reports, merge duplicates by root cause, preserve commit permalinks and distinguish verified findings from proposed tests. Return a dependency-ordered queue, exact local acceptance checks and the items that require my input. Leave code changes, tests, GitHub writes and installation to the local integrator.
