# Coordinate research, review and implementation

| Assignment | Start here | What to return |
|---|---|---|
| Investigate an unresolved financial input or provider prerequisite | [Company evidence ledger](../limitations.md#selected-company-review-follow-up) · [Adapter prerequisites](../limitations.md#installed-adapters-and-remaining-source-prerequisites) | Original source, publication date, period, scope and calculation. State exactly what remains missing. |
| Review the code in independent Pro chats | [Four independent reviews](#four-independent-chatgpt-pro-reviews) | A finding tied to a published commit, its consequence and a check that would confirm it. |
| Implement an assigned batch locally | [Parallel local implementation](#parallel-local-implementation) | Changes within the agreed files, focused tests and evidence for one integrator. |

Use the [handoff](../HANDOFF.md#next-work) to select an open task. Keep portfolio records, private theses, user data, credentials and backups local. Pin the published commit when sharing source with review chats. The handoff identifies any newer local release.

## Release completion round

All nine November 19 reviews returned against `ef2e2d6`. Four chats examined the sixteen issuer inputs open at dispatch, three reviewed valuation, chart and portfolio workflows, and two checked evidence and acceptance tests. The [original assignments and Knull prompt](release-completion-chats.md) retain that round's scope and the three optional provider and OCR assignments. The [installed checks](../current-state.md#dated-validation) record the local result. Actual-use records and final acceptance belong to the user.

## Four independent ChatGPT Pro reviews

The [four assignments and Knull prompt](four-pro-chats.md) cover data and adapters, valuation and portfolio math, research workflows and UI, and release safety and privacy. Each chat first opens an owning file at the pinned revision. It returns a commit permalink, the observed or code-traced behavior, its consequence and a proposed test. A local integrator checks each finding against the working copy, combines duplicates and implements accepted changes. [November 19 integration results](../archive/checkpoints/2026/integration-review-2026-11-19.md)

## Parallel local implementation

Choose one integration owner and allocate files before starting local workers. Reserve shared contracts, migrations and central guides for the integrator. Run writing tests against isolated data. The [workstream plan](plan.md) and its [five-worker allocation](ownership.tsv) describe one earlier assignment. Confirm the paths for each new batch. [Test and ownership checks](../execution-runbook.md#parallel-workstream-checks) · [Evidence index](evidence/README.md)

Each Pro packet can be removed after its round by replacing its link here with the outcome. Keep these section headings so other guides continue to reach the right workflow.
