# Marketagent UI and adapter worklist

The Geist interface and 22 adapter operations shipped in [PR 20](https://github.com/Gittastic112/Marketagent/pull/20). The company price chart and private thesis pins subsequently shipped in [PR 22](https://github.com/Gittastic112/Marketagent/pull/22). Use **Advanced → Research Lab** for adapter operations and **Companies → Overview → Price history** for chart annotations. [Verification by release](../current-state.md#dated-validation)

## November 18 handoff for build, UI and data verification

Priorities 1 and 2 are complete for this local release. Priority 3 is complete for the configured, bounded source examples below; unavailable entitlements and OCR assets remain explicit prerequisites in the [limitation ledger](../limitations.md#installed-adapters-and-remaining-source-prerequisites). The installation and publication steps for this batch are complete.

| Priority | Verified outcome | Next boundary |
|---|---|---|
| 1. Build and test | Full frontend/core backend and optional-adapter suites, TypeScript, both contract checks, production builds and disposable PostgreSQL gates pass. Exact counts and profile skips are in [Current State](../current-state.md#dated-validation). | Populated legacy recovery and actual-use acceptance remain separate gates. |
| 2. Verify and install the UI | Combined services are healthy on loopback ports, with the same database container, volumes, settings and worker selection. Desktop/mobile and light/dark checks cover research runs, search, memo, price/FX and PDF review. Target sizing, contrast, search focus/dismissal and mobile control sizing were repaired. | Maintain these regression gates when changing the interface. Public deployment remains outside scope; the user separately authorized GitHub publication. |
| 3. Check real sources | Installed peer discovery preserves separate Infosys listings and verified export hashes. Original SEC amendment, NSE action, ALFRED revision, OpenFIGI ambiguity and Apple PDF/Camelot evidence are retained with Processing Runs. Source candidates remain unapproved; six erroneous standard-parser candidates were retained as rejected and the parser repaired. | The ledger identifies the exact US-action, transcript and OCR prerequisites. Broader coverage below is still open; these examples do not prove complete financial statements or historical universes. |

## What landed

| Surface | Available in the combined source |
|---|---|
| Application shell | Bundled Geist Sans and Mono, light and dark themes, a compact sidebar, mobile navigation, route breadcrumbs and accessible focus controls. The saved theme is read before the page body renders. |
| Search and company setup | The top bar and Cmd/Ctrl+K open one company and evidence dialog. The sidebar links to full evidence search. Explicit ticker lookup can prefill Add company. Keyboard shortcuts respect fields and other dialogs. |
| Valuation and portfolio | Saved-model, scenario and version views use the shared theme. Memos render Markdown with evidence links and download against the displayed artifact. Price/FX imports support row filters, error navigation and exact-file preview/apply. |
| Research Lab | Hypothetical allocation, rebalancing simulations, return reports and candidate peers. Saved runs retain input/output hashes, owner, versions and exports. Changing tasks clears the previous result. Opening a saved run selects its task. Cursor pages expose older runs, malformed receipts are refused and benchmark comparisons show explicit units. |
| Inputs | FMP, Massive, official NSE MCP, OpenFIGI and exchange calendars. SEC annual facts, supplied Indian filing metadata, transcript retrieval, ALFRED vintages and selected-page PDF extraction have explicit source actions. Financial candidates link directly to review and their evidence. Input edits clear outdated receipts; filing drafts stay scoped to their company; failed attempts expose their Processing Run. |
| Supporting code | Three authenticated router groups, 22 adapter operations in the OpenAPI snapshot, generated TypeScript contracts, optional Python profiles, fixtures, CI checks and third-party notices. Browser timeouts account for worker time and receipt writes. Normal Compose passes optional build flags, provider settings and artifact paths to their consuming backend services. |

## Release checklist

Use these gates for future releases. The dated table above owns this release's outcome. Provider acceptance is recorded per configured source; a paid subscription is optional.

| Order | Work to do | Completion evidence |
|---|---|---|
| 1 | **Restore locked dependencies.** Run `npm ci` from `frontend` using Node 24. Build the source-mounted Linux/Python test image. Include the analysis and Camelot profiles in a separate build for optional coverage. | Full frontend tests, TypeScript, both adapter contract drift checks, core backend tests and optional adapter suites pass on this combined source. Record skips by profile. |
| 2 | **Build and test the release.** Build the frontend and backend from the same tree. Run the existing PostgreSQL concurrency/migration and browser gates in the disposable Compose project. | Sign in at desktop and mobile sizes. Verify both themes and fonts, navigation focus, search in a field and a modal, and a Research Lab run, history and download. Verify a saved memo and a price/FX preview. Check empty, unavailable and Mock Data states. |
| 3 | **Roll out locally.** Inspect the active Compose project, service selection, mounts and loopback ports. Select versioned frontend/backend images and align any worker that uses the changed backend. Preserve existing service state, volumes and the established recovery set. | Readiness passes, signed-in `/research-lab` reports actual capability states, an owned run reopens, and its downloaded hashes match. Record the image IDs and outcome. For a schema change, verify the actual migration head and preservation of the existing data under the [recovery policy](../operations.md#when-to-make-a-backup). |
| 4 | **Verify data access.** Run one expressly chosen operation through the installed app for each configured source. Start with existing entitlements. Use read-only provider requests and review the corresponding Processing Run and original evidence. | Record provider, operation, listing or series, timestamps, entitlement, freshness, partial counts and safe failures. A missing key or unavailable feed stays visible. See the per-package cases below. |
| 5 | **Provision optional local assets.** Pin the FinanceDatabase CSV and its manifest. If OCR is wanted, install the separate Docling interpreter and compatible local model assets. | A peer run rechecks its snapshot hash. Sample scanned pages yield exact source-page candidates within the worker limits. Marker stays unavailable pending a compatible dependency set. |

[Execution runbook](../execution-runbook.md) · [Operations](../operations.md) · [Adapter setup and examples](../adapters/README.md) · [UI acceptance](../geist-ui.md) · [Known limitations](../limitations.md)

## Implementation backlog from the ZIP

All 16 packages from the original handoff are accounted for below. The last column identifies the next piece of evidence or engineering work. The sequence after rollout is company evidence and review, reliable portfolio inputs, then search and workflow automation.

| Package | Implemented here | Remaining work and acceptance |
|---|---|---|
| MA-01 · SEC financials | Annual CompanyFacts candidates with filing cutoff, accession and source context; an Apple 10-K/10-K/A pair and repeat deduplication are verified against original facts. | Broaden issuer/tag coverage. Extend period identity and promotion rules before enabling quarterly or YTD review. |
| MA-02 · India market data | NSE MCP quote, dated history, dated observations and corporate actions; a live Infosys dividend response and its original locator/hash are verified. | Check holidays, special sessions, settlement series, delayed/partial observations and throttling. A prose dividend amount is not automatically applied to holdings. |
| MA-03 · US market data | FMP quote/history and Massive reference, quotes, daily aggregates and actions are registered in the existing provider workflow. | Verify subscribed endpoints on matched US listings. Check dates, adjustment basis, currency, missing trades, entitlements and outages. Reconcile dividends and splits before claiming total return. |
| MA-04 · Documents | Selected-page Camelot cells match an original Apple report. Standard extraction v8 separates share counts from EPS. Original bytes, warnings and rejected predecessor candidates are preserved. | Complete currency/statement-scope review and continued-table coverage. Scanned-page accuracy, runtime and memory remain unverified until the ledger's OCR prerequisites are met. |
| MA-05 · Macro vintages | GDP as-of snapshots on both sides of a real revision match original ALFRED responses, with the earlier snapshot retained. | Broaden series coverage and exercise missing observations, initial-release mode and incomplete pagination against genuine sources. |
| MA-06 · Portfolio allocation | Equal weight, minimum variance, maximum Sharpe and HRP on supplied research returns, with explicit constraints. | Build the owner-scoped conversion from portfolio history to an aligned base-currency dataset. Show exclusions and cash, document return basis, and reproduce a constrained allocation with the exact saved inputs. |
| MA-07 · Company workspace | Company price history uses stored daily closes. Dated documents, linked events and private thesis pins open from chart points. Comparable series retain provider, listing, currency and adjustment basis. | Add persistent named research lists and a resizable saved-model, peer-table and source workspace. Link exact PDF pages and preserve unsaved edits across navigation. |
| MA-08 · Price and FX import | Filterable rows, errors and an exact-hash preview/apply flow in Portfolio Setup. | Exercise duplicate, conflict, edited file, wrong portfolio, late response and retry cases in the integrated browser. Transaction/broker imports would require separate opening-balance, cash-flow and corporate-action handling. |
| MA-09 · Valuation memo | Markdown/GFM, safe citation links and export tied to the displayed artifact, alongside the November 16 saved-version repairs. | Verify long tables, broken source links, a switched model during generation and historical memo downloads. Match the artifact’s saved model, assumption and output IDs to its displayed contents. |
| MA-10 · Transcripts | Explicit EarningsCall/FMP retrieval and versioned speaker/section evidence. | Verify an entitled call and a correction. Add overlap polling, durable segment identity, reviewed guidance extraction and comparisons between calls. Preserve publication and first-observed times. |
| MA-11 · Hybrid evidence search | The palette uses the existing stored-evidence search. | Label questions and expected passages, measure the lexical baseline, then evaluate versioned embeddings and pgvector with the same owner, issuer, date and source-version filters. Adopt only if retrieval improves. |
| MA-12 · Durable jobs | Processing Runs record attempts, counts, failures and source context. | Pilot one workflow with durable checkpoints on PostgreSQL. Test cancellation, worker interruption, duplicate submission and recovery between external responses and local writes before scaling it out. DBOS is a candidate. |
| MA-13 · Contracts and replay | Generated adapter types, a schema snapshot, immutable saved inputs/results and JSON export. | Add named, owner-scoped versioned presets and one-click replay from a saved input hash. Record changed adapter/dependency versions and keep credentials out of presets. |
| MA-14 · Evaluation | Offline provider fixtures, schema, provenance, numerical and failure tests. | Expand edge cases from actual provider responses and document coverage. Add a labeled, versioned agent/prompt evaluation for an existing AI workflow, including citation, currency, refusal and unavailable-provider cases. |
| MA-15 · Identity and calendars | A live INFY lookup retains OpenFIGI's ambiguous candidates without merging issuers or listings; India filing checks and exchange schedules remain available. | Verify special Indian sessions. Design reviewed issuer/security/listing history with effective and observation dates, including ticker reuse, delisting and corrections. |
| MA-16 · Simulation and reporting | Native fixed-universe simulation, a zero-cost `bt` cross-check, QuantStats reports and saved JSON/HTML exports. | Connect validated portfolio histories, distributions, FX, cash and dated universe membership. Reconcile contributions, costs, execution sessions and missing/delisted assets against an independent example. |

The original research names alternatives including OpenBB, Riskfolio, skfolio, vectorbt, backtesting.py, LEAN and Qlib. They are design references for future requirements. The shipped calculation and provider choices are documented in the [implementation guide](../adapters/README.md). The [broader product roadmap](product-roadmap.md) and [acceptance tracker](completion-tracker.md) retain the rest of Marketagent’s work.

## Existing product release work

These project gates already existed when the ZIP arrived. They matter if the goal is Marketagent’s full local research/demo release. The [milestone board](completion-tracker.md#milestone-board) owns their complete task lists and order.

| Order | Work still needed |
|---|---|
| M05 · Company facts | Complete the reviewed, dated financial inputs for the four selected companies. Record unresolved source conflicts, currency, units and periods. |
| M06 · Valuation | Tie the selected model inputs, peer set, sensitivity, initial preview and saved version to that company evidence. Finish the dated-source proposal and period coverage from the [workspace plan](research-workspace-plan.md). |
| M07 · Portfolio | Reconcile the scoped example history, FX, flows and benchmark comparisons. Record unavailable performance measures where the evidence is insufficient. |
| M08 · Research loop | Verify the path from a new filing or event through Today, source review, a thesis decision and, where warranted, an explicitly saved valuation change. |
| M09 · Interface and responsiveness | Run the connected desktop/mobile workflows on the combined release, measure page responsiveness and repair confirmed regressions. Include worker status, bounded retries, contract drift and read-path performance. |
| M10 · Acceptance | Complete the installed checks, restart/retry evidence, five actual business days of scoped research use and final acceptance. Track the separately deferred recovery work in the existing ledger. |

For an independent review of these packages, start from the current published commit and use the [review assignments](../workstreams/README.md). The [release evidence](../current-state.md#dated-validation) distinguishes installed source checks from hosted fixtures.

## Package reconciliation and verification

The ZIP contains 181 files. Of those, 173 are the PR source change set, six are selected deliverables and two are packaging notes. Five of the selected deliverables have exact counterparts in the payload. The unique [consolidated research report](../archive/assessments/github-reuse-research-2026-11-17.md) is retained separately. The two packaging notes identify the base and PR head. The sample return series are labeled **Mock Data**.

The input base was `371b58c02cfd2b80429f28dbc13629165b5e392d`. The packaged PR head was `33df697d0f33c584944c440b5ec5835aea0aee24`. The receiving branch began at `f4010d2d4a82b9ca003726be5734aa49fce42e34`. The Geist changes and overlapping local edits were reconciled against that common base. [PR #20](https://github.com/Gittastic112/Marketagent/pull/20) · [Successful CI on the packaged commit](https://github.com/Gittastic112/Marketagent/actions/runs/44228408999)

Checks and outstanding runtime gates for the combined tree are recorded in [Current State](../current-state.md#dated-validation). The original [adapter verification receipt](../adapters/verification.md) covers the packaged branch.
