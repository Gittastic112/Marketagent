# Knull’s release-completion round

**Round returned November 19, 2026.** The following is the original dispatch brief. Follow the [local implementation handoff](../HANDOFF.md#next-work) for current work and the [financial ledger](../limitations.md#selected-company-review-follow-up) for decisions.

Use **nine ChatGPT Pro chats plus Knull as coordinator**. Seven can start together. Four investigate all **16 open company/input combinations**. Three trace the first valuation save, the chart-to-thesis workflow, and portfolio calculations. Two independent reviewers then check the evidence and the proposed acceptance tests. The number of financial values that can be resolved depends on what the originals disclose. [Current priorities](../HANDOFF.md) · [Milestone board](../roadmaps/completion-tracker.md#milestone-board)

| Who | Can deliver |
|---|---|
| Knull and the Pro chats | Original-source research, independently checked calculations, code traces, proposed changes, test cases and one ordered handoff. |
| Local Codex | Verify the originals and calculations against the existing records, apply supported changes, implement features, run tests, check the signed-in app and publish the integrated result. |
| You | Use the app for research on five actual business days, report problems and give final acceptance. Decide on optional licensed access or local OCR resources if you want that coverage. The existing November 12 valuation date and delegated review decisions already apply. |

## Dispatch

1. Resolve `Gittastic112/Marketagent` on GitHub to **one full commit SHA containing this packet**. Give every chat the same tree and packet at that SHA. Keep that pin for the round even if `main` advances. Each chat gets its own brief and the relevant shared instructions below.
2. Before accepting work, have each chat prove access. An issuer reviewer returns its ticker, one actual matrix field and its commit permalink. A technical reviewer returns an owning symbol or named test it opened and its commit permalink. If access fails, give that chat only the necessary public files or excerpts from the pinned commit, with their paths. Record any remaining access gap. If Knull cannot open a chat, return its ready-to-paste brief as pending and continue with the others.
3. Dispatch **1–7**. As an issuer finishes, pass its locators and arithmetic to **8**. Pass the three workflow reports and the reviewed financial results to **9**. A held financial input can serve as a missing-data acceptance case. If four chats at a time is easier, run **1–4**, then **5–8**, then **9**.
4. Use the public repository, issuer or regulator filings and official provider documentation. Keep private thesis notes, portfolio exports, credentials, live database contents, backups, local logs and private chat links on the user’s side. Use labeled public Sample or **Mock Data** for workflow examples. Knull hands the output back to one local integrator.

To brief a worker, paste the following and append its numbered assignment and return instructions. Reviewers do not need access to one another’s chats.

```text
You own chat [number and name] in the Marketagent release-completion round. The pinned tree is [immutable tree URL]. Read your assignment in [immutable packet URL]. Open the relevant published file and return the requested access proof. Work read-only with public evidence. Follow the stated cutoff and return every assigned item, including gaps. Label what you inspected, independently calculated or propose to test. Cite originals and revision-specific code links. Send one report to Knull and identify any dependency.
```

## Chats 1–4 · Original financial evidence

Start with the [20-slot matrix and original-source locators](../../data/reviews/financial-five-input-review-20261112.json), the [dated evidence and methodology](../../data/reviews/valuation-inputs-asof-20261112.json) and the [remaining components by company](../limitations.md#selected-company-review-follow-up). The eleven earlier holds have dispositions. Preserve those decisions and the four resolved slots. Use information publicly available by **the end of November 12, 2026 in New York**. Distinguish the issuer’s fiscal period, filing publication date and valuation date. Later filings or corrections can be recorded separately for later review.

| Chat and fiscal years | Assigned open fields | What to investigate |
|---|---|---|
| **1. Apple (AAPL), FY2024–2026** | Debt, change in operating working capital, employee-award value **(3)** | Reconcile financing subtotals to outstanding debt, including repayments and lease treatment. Identify the operating portion of mixed accruals and what the award disclosures establish at the valuation date. Preserve the resolved minority and parent preferred claims. [Apple FY2024 filing](https://www.sec.gov/Archives/edgar/data/320193/000032019324000123/aapl-20240928.htm) |
| **2. NVIDIA (NVDA), FY2024–2026** | Debt, change in operating working capital, employee-award value **(3)** | Trace notes and deferred consideration separately. Match the working-capital components and award classes to NVIDIA’s own fiscal year ends. Preserve the resolved equipment/intangibles capex and minority claim. [NVIDIA FY2024 filing](https://www.sec.gov/Archives/edgar/data/1045810/000104581024000029/nvda-20240128.htm) |
| **3. Meta (META), FY2023–2025** | Debt, change in operating working capital, minority claim, preferred claim, employee-award value **(5)** | Look for amounts attributable to the parent and to other owners. Trace preferred rights and dated market quotes to their security and original source. A consolidation policy by itself cannot establish a zero balance. [Meta FY2023 filing](https://www.sec.gov/Archives/edgar/data/1326801/000132680124000012/meta-20231231.htm) |
| **4. Alphabet (GOOGL), FY2023–2025** | Debt, full-year depreciation and amortization, change in operating working capital, minority claim, employee-award value **(5)** | Reconcile full-year intangible amortization with reported depreciation. Identify any lease amortization already included. Keep carrying values, economic claims, share classes and award dilution distinct. [Alphabet FY2023 filing](https://www.sec.gov/Archives/edgar/data/1652044/000165204424000022/goog-20231231.htm) |

**Return one row per field and applicable fiscal period**, plus a separate dated row when a claim needs a point-in-time valuation. Use the matrix’s existing field keys. Each row needs:

- Ticker, field, fiscal period, observation date and filing publication date.
- Original issuer, regulator or exchange URL, accession or document identifier, and the note, table, row and column that support the figure. Record the issuer, security class, currency, unit, scale and sign where relevant.
- Disclosed amount and its accounting scope. For a **Calculation**, give the source for every operand, the formula and a reconciliation. Label a carrying-value proxy or gross award exposure as an **Estimate** where applicable.
- A proposed disposition of **ready for local review**, **partial**, or **held**. Name the exact missing component or conflict and the source that could resolve it. Silence cannot support zero. A later price, an unavailable original or a subtotal alone cannot complete a field.

## Chats 5–7 · Workflow design

| Chat | Starting evidence | Required return |
|---|---|---|
| **5. First valuation save (M06)** | Open `ValuationSetupDraftService.create_or_reopen`, the saved-model `previewValuationVersion` caller and the draft browser test. [Draft service](../../backend/app/services/valuation_setup_draft.py) · [Existing preview contract](../../frontend/lib/api/valuation-preview.ts) · [Draft tests](../../frontend/e2e/valuation-draft.spec.ts) | Trace one selected, dated source revision into a proposed assumption, first calculation preview and explicitly confirmed save. Specify what the analyst sees and what the backend validates. Give cases for an admissible value, held or stale evidence, a revision changing after preview, and a lost response followed by a retry. The retry should produce one saved version. Preserve the existing saved-model edit path. |
| **6. Price move to research decision (M08)** | Open `company_timeline`, the chart and the existing price-pin browser test. [Timeline and pins](../../backend/app/services/price_timeline.py) · [Chart](../../frontend/components/company-price-chart.tsx) · [Browser test](../../frontend/e2e/price-timeline.spec.ts) | Trace a marked close to an original filing, an owner-scoped thesis note, and a reviewed decision to change or retain an assumption. Identify where context is lost. Cover a move with a nearby source, one with no matched source, and a historical pin after a corrected close. Distinguish timing from a sourced explanation. Specify keyboard and mobile checks. Chat 5 owns saving the resulting model. |
| **7. Portfolio calculations (M07)** | Use the published two-date USD sample reconciliation and the replay and benchmark checks. [Prior proof](../archive/checkpoints/2026/integration-review-2026-11-19.md#reproduction-and-interpretation) · [Replay tests](../../backend/tests/test_portfolio_replay.py) · [Benchmark calculation](../../backend/app/services/portfolio_benchmark.py) · [Benchmark tests](../../backend/tests/test_portfolio_benchmark_opportunity_cost.py) | Identify what the 61 recorded checks cover. Supply a reproducible sample calculation with positions, dated prices, cash, currency and expected portfolio value. Specify what should display when a split makes a price unusable or the benchmark is missing. Use public fixture inputs if the stored sample details are unavailable. Record any real-account or licensed-data gap explicitly. |

For each workflow return the current behavior, one concrete proposed change or remaining proof, the owning code and test permalinks, the input and expected result, dependency and local verification step. A small proposed diff or regression test against the pin is welcome when it makes the change precise. Record the environment and result for work actually run. An already covered case can return its existing proof.

## Chats 8–9 · Independent review

**8. Financial reconciliation (M05/M06).** Start as the issuer reports arrive. Knull sends the primary locators and operand rows first. Independently reopen the originals and recompute each value proposed as ready, then compare with the issuer reviewer’s conclusion. Check dates, units, parent or subsidiary scope, lease and award double counting, and the distinction between a subtotal and a complete input. Separately assess eligible industry weights and country/currency conventions under the existing decisions. Keep unresolved industry allocation outside the 16-slot count. Return a checked value or exact disagreement per proposed value, plus one disposition per company/input combination. [Review decisions](../roadmaps/review-decisions.md) · [Industry mapping](../../backend/app/services/industry_mapping.py)

**9. Integration and acceptance (M06–M10).** Start when the three workflow reports and Chat 8’s dispositions are available. Trace one admissible input and one held input through the proposed workflow. Check that proposed behavior agrees across the financial, API and screen boundaries. Return an ordered local test matrix with fixtures, expected results and owners. Start from the [financial review recovery test](../../frontend/e2e/financial-review-recovery.spec.ts). Include first-save retry, owner isolation, corrected pins, portfolio basis, desktop/mobile access and appropriate restart or outage recovery. Assign each row to a public check, an isolated local test, a signed-in check, or genuine user research. Provide a short use log template with date, workflow, observed outcome and failure. The user records the five business days and final acceptance. [Execution runbook](../execution-runbook.md#choose-the-right-environment) · [Acceptance gates](../roadmaps/completion-tracker.md#milestone-board)

## Optional specialist chats

Knull can add **up to three** for concrete public evidence or documentation questions. Their research can begin before provider access is available. The six previously verified adapter examples are recorded in the ledger. Each specialist returns a public-source checklist, a local verification case and its outstanding prerequisites. Provider credentials and licensed payloads stay local. [Adapter prerequisites](../limitations.md#installed-adapters-and-remaining-source-prerequisites)

| Specialist | Pro work | What must happen locally |
|---|---|---|
| US corporate actions | Match the issuer, listing, effective date and price adjustment basis to an official action. | Verify the specific case using entitled Massive corporate-action access. |
| Transcript corrections | Identify an original/corrected pair and specify version, publication time, attribution and stale-result handling. | Verify both versions using entitled FMP or EarningsCall access and an actual correction. |
| Scanned filings | Specify how a genuine scanned page maps to table cells with page references and uncertainty. | Run a compatible isolated OCR setup with approved model files and an appropriate original scanned page. |

## Knull’s handoff to local Codex

Return **one private Markdown handoff**, with the pinned SHA and actual access gaps at the top. Use a distinct filename for this round so the earlier handoff is preserved.

1. Give a **16-slot scoreboard** with one owner and disposition per issuer/field. The three counts must sum to 16. A slot is ready only when all applicable periods and dated components have support. Include the per-period source rows and Chat 8’s checks immediately below it.
2. Consolidate the three workflow reports and Chat 9’s checks into a dependency-ordered list. Keep the evidence, consequences, smallest proposed changes and acceptance criteria together. Preserve competing interpretations with both primary locators when the originals do not resolve them.
3. List what local Codex can do now, what needs additional original or licensed evidence, and any decision that genuinely needs the user. A missing filing component is a source gap. Report any proposed change to an agreed financial convention separately.
4. Local Codex can start on independently checked items while other reports are pending. It checks the pin against current code, reproduces the proposed evidence and applies supported items through the existing review flow. It owns implementation, disjoint local edit assignments if useful, tests, release and documentation. Missing proof stays visible. Existing user data and the single verified recovery set follow the [operations policy](../operations.md#essential-retention-policy).

## Prompt to give Knull

```text
Coordinate the Marketagent release-completion round in nine independent, read-only ChatGPT Pro chats. Resolve Gittastic112/Marketagent main once to a full SHA containing docs/workstreams/release-completion-chats.md. Open the packet there and give each chat the same immutable tree, its numbered brief and its return instructions. Verify that each chat can open its assigned files.

Start 1–7. Send the issuer evidence that comes back from 1–4 to independent reviewer 8. Then give 5–7 and 8’s results to 9 for the integration and acceptance matrix. Cover all 16 company/input combinations with original sources available by the end of November 12, 2026 in New York. Keep unresolved components explicit. Use public code, public sources and labeled examples. Keep private app records, credentials, logs, backups and chat links local. Use optional specialists for concrete public follow-ups and record the local access they would need for live proof.

Return one private Markdown handoff for local Codex with the 16-slot scoreboard and per-period sources, three workflow work orders, independent checks, dependencies, exact local tests, and only decisions that genuinely need me. Local Codex owns changes and installation. I own actual-use records and final acceptance.
```
