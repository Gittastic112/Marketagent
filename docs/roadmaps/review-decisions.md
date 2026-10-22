# Research/demo decision log

Updated October 22, 2026. This is the readable index for the
[versioned decision register](../../data/reviews/research-demo-decisions.json).
It records decisions and their effects; the [completion tracker](completion-tracker.md)
owns milestone acceptance and the [limitation ledger](../agent_capabilities_and_limitations.md)
owns unresolved gaps.

## Review authority

The user instructed: "Approve all of what you think is best just keep track of
these things somewhere so i can go back later if need be."

Authorization `AUTH-20261017-DELEGATED-REVIEW` replaces individual approval prompts
for the remaining research/demo financial, valuation and interpretation-review choices. Codex may make
evidence-based decisions within that scope and must record the rationale, sources,
assumptions, timestamp, affected records and remaining uncertainty. Decisions under
this authorization are **agent review under user delegation**, not personal user
inspection or independent human certification. Existing permissions and scope
boundaries remain in force.

To revisit a choice, name its ID or subject. Record a new dated entry with
`supersedes_decision_id`, preserve the old receipt, and recheck source/candidate
versions before applying a change. The original source packets remain intact.

## Decisions personally approved in chat

| ID | Approved scope | Application state |
|---|---|---|
| M05-AAPL-01 | FY2023 cash: USD29.965bn balance-sheet cash and USD30.737bn cash-flow closing cash including restricted cash; preserve separate definitions | Source approval recorded; valuation-available cash remains a separate input |
| M05-AAPL-02 | FY2025 term debt USD90.678bn, commercial paper USD7.979bn, operating leases USD12.490bn and finance leases USD1.230bn; subtotals and separate accounting treatment | Source approval recorded; valuation debt/lease bridge not yet applied |
| M05-AAPL-03A | FY2025 year-end shares 14,773.260m, average basic shares 14,948.500m and average diluted shares 15,004.697m; units and historical uses | Source approval recorded; valuation-date denominator not yet selected |
| M05-AAPL-03B | FY2025 dividends/equivalents declared USD15.413bn, paid USD15.421bn, buyback cash USD90.711bn and declaration USD1.02 per share/RSU; units, signs and definitions | Source approval recorded; USD8m declared/paid difference retained without an invented bridge |
| M05-AAPL-04A | US domicile, USD cash flows and matching discount-rate currency, operating-company FCFF DCF as primary method | Setup approval recorded; no numerical forecast or saved valuation changed |

Every approval's exact user message, scope, timestamp and source evidence is
embedded in the register. These approvals did not themselves promote financial
candidates. FY2025 Apple figures use the [official report](https://www.sec.gov/Archives/edgar/data/320193/000032019325000079/aapl-20250927.htm),
SHA-256 `45a0dd6e8ee4bf4bf47dc48d0c66d74d053adef8f8b9c5a62926d97d0c740e6c`.
The cash receipt separately pins its FY2024 source for the FY2023 balance sheet.

## Decisions under delegated authority

| ID | Decision and reason | Actual effect / verification |
|---|---|---|
| M05-US-BENCHMARK-INTAKE-20261017 | Load the six retained US benchmark workbooks dated January 5, 2026. The normal database had no dataset versions; source mirrors match the audited immutable originals | Added six active versions, 1,131 typed rows and six successful Processing Runs. Changed seven benchmark/audit tables; the other 102 tables are unchanged. Twenty-seven selected values match workbook cells |
| M05-AAPL-04B | Use Computers/Peripherals and the two software categories as separate labeled comparisons. Retain the FY2025 Products/Services revenue split as context; do not adopt a unique services allocation or apply industry averages as company forecasts | Products USD307.003bn and Services USD109.158bn reconcile to USD416.161bn. Company mapping, forecasts and saved valuations remain unchanged. A final weighted mapping still needs sound business and ratio-aggregation evidence |
| M05-HDFCBANK-05 | Accept 64 selected consolidated FY2024/FY2025 entries on their historical pre-bonus basis. Separate official audited results corroborate the annual PDF's missing currency glyph | Report retained as document 10/asset 1. Corrected 52 monetary units to INR crores and four EPS units to INR/share; eight existing share/EPS units retained. Eighteen statement/EPS checks pass; Processing Runs 97/98 succeed |
| M05-HDFCBANK-06 | Promote the reviewed entries with exact March 31 period ends. Preserve bank accounting labels and keep the unverified publication date unknown | Two annual periods, 60 distinct reported facts, 64 source revisions and eight normalized values. Run 99 succeeds; 101 other tables and unrelated rows within changed tables remain unchanged. Ingestion time is retained |
| M05-HDFCBANK-07 | Correct only four identical EPS projections just created by the first promotion, where statement and note occurrences were inserted twice | First projections retained; all source candidates/revisions preserved. Exact removed row IDs, values and timestamps are retained in the receipt and Run 99. Original source-history metadata is not rewritten |
| M05-NORMALIZATION-20261017 | Require actual, compatible inputs for derived financial figures. Keep missing values distinct from zero; require reported tax/net borrowing and distinguish gross/net capex | Pure calculation helper and regression checks replace implicit defaults. Repeated identical candidates produce one period fact, conflicts block promotion, and new source occurrences get sequential revisions. Other companies and saved valuations are not recalculated |
| M05-US-08 | Accept 355 selected historical candidates after independent original-report checks of units, values, concepts and dates. Retain 47 selected gaps, comparative definitions and all unselected older rows | [Exact review](../../data/reviews/us-financial-review-20261018.json) records ten original reports, 672 source-cell checks, source-encoded zeros and manual exceptions. Selected histories do not establish complete valuation inputs |
| M05-US-09 | Apply M05-US-08 only after source/current-candidate version checks and a fresh backup | [Application receipt](../../data/reviews/us-financial-application-20261018.json): Runs 100-105, 355 facts/revisions, 18 periods and 248 normalized values across six securities. Twelve normal financial views pass; unrelated records and all 109 post-browser fingerprints are unchanged |
| M05-IN-10 | Review exact Reliance/Airtel/ICICI/SBI histories; separate investment scope, restricted cash, bank accounts, EPS numerators and SBI comparative presentation. Record HDFC bonus treatment without changing its existing history | [Exact review](../../data/reviews/india-financial-review-20261018.json): 112 accounting equations and 24 EPS checks pass. Select 492 source occurrences, keeping 164 older comparatives held. This is historical evidence, not complete model approval |
| M05-IN-11 | Apply M05-IN-10 through exact-source intake and version-checked promotion after a fresh backup | [Application receipt](../../data/reviews/india-financial-application-20261018.json): Runs 106-121, eight source documents/assets, 456 distinct facts, 492 revisions, 12 periods and 72 normalized values. Sixteen normal financial/PDF views pass after the mobile keyboard fix; unrelated rows and all 109 post-browser fingerprints are unchanged |
| M05-HDFCBANK-12 | Accept 64 FY2025/FY2026 occurrences from the retained latest report, including four bonus-adjusted comparatives and one explicit basic-EPS arithmetic exception. Separate capital, dividends and share denominators | [Review receipt](../../data/reviews/hdfc-financial-review-20261022.json): 21 checks pass, one exception remains; no current bank valuation or FY2024 per-share comparability is inferred |
| M05-HDFCBANK-13 | Apply that exact selection through source/candidate version checks and expose normalized values with their review basis | [Application receipt](../../data/reviews/hdfc-financial-application-20261022.json): document 19/asset 10; HDFC has three periods, 90 facts, 128 revisions and 12 normalized values. Six normal views pass; unrelated data remains |
| M05-HDFCBANK-14 | Retire only obsolete active flags on old EPS revisions 61/63 after the committed promotion audit failed | Run 125 records the exact metadata repair; Run 124 remains failed. Values, units, sources and revision numbers are preserved. New promotions supersede all prior active occurrences within the same fact/period |
| M05-HDFCBANK-15 | Accept historical earnings-item distinctions, exact issued-share and award movements, and separate parent/minority/equity subtotals. Withhold unsupported recurring-profit, current-option-value and mechanical segment-weight estimates | [Accounting-note receipt](../../data/reviews/hdfc-accounting-notes-20261022.json): 24 exact arithmetic checks and 90 source-text checks, plus visual page review. Existing reported data and saved models are unchanged |
| M08-AI-REVIEW-20261018 | Review six saved actual responses and four existing adversarial fixtures. Accept four outputs only as constrained summaries; reject regional-to-company forecast directions and preserve the blocked period response | [Review receipt](../../data/reviews/ai-interpretation-review-20261018.json) separates citation checks from semantic judgment. All four misleading fixture claims are rejected. Original files, human-review fields, saved models and normal AI records are unchanged |
| M07-DEMO-REVIEW-20261018 | Accept existing examples for the explicitly revised demo gate, with partial/unavailable coverage preserved. Do not certify real records or fabricate missing models/benchmarks | 64 independent arithmetic checks and six normal browser views pass. Portfolio records are unchanged. The attribution table's mobile keyboard defect is fixed and verified; original complete-series/model and genuine multi-currency proof remain unperformed |

The [HDFC checkpoint](../archive/checkpoints/2026/hdfc-reviewed-normalization-2026-10-18.md)
owns the source, calculation, rollout and browser proof. These are delegated agent
decisions, not independent human certification. The selected historical basis does
not approve a current bank valuation. The [October 22 follow-up](../archive/checkpoints/2026/hdfc-latest-history-2026-10-22.md)
applies the later FY2025/FY2026 bonus-adjusted source basis, with FY2024 kept separate.
The [US/AI checkpoint](../archive/checkpoints/2026/us-financial-and-ai-review-2026-10-18.md)
records the subsequent source review, normal-data application and verification.
The [India checkpoint](../archive/checkpoints/2026/india-financial-review-2026-10-18.md)
records the later four-company application and the exact parser/UI changes.

The source categories are **Computers/Peripherals**, **Software (Internet)** and
**Software (System & Application)**. The service activities do not establish a
unique mapping among those categories. Revenue shares are not automatically the
right weights for beta, ROE or sales-to-capital ratios. See the retained source
evidence and [Damodaran's business-weighting guidance](https://pages.stern.nyu.edu/~adamodar/New_Home_Page/TenQs/TenQsBottomupBetas.htm).

### Imported benchmark versions

| Runtime version | Source | Source date | Typed rows |
|---|---|---|---:|
| 1 | betasUS-2026-01-05.xls | 2026-01-05 | 282 |
| 2 | waccUS-2026-01-05.xls | 2026-01-05 | 473 |
| 3 | marginUS-2026-01-05.xls | 2026-01-05 | 94 |
| 4 | capexUS-2026-01-05.xls | 2026-01-05 | 94 |
| 5 | roeUS-2026-01-05.xls | 2026-01-05 | 94 |
| 6 | wcdataUS-2026-01-05.xls | 2026-01-05 | 94 |

The register embeds hashes, source rows, import evidence and Processing Run IDs;
full database fingerprints stay in the local receipt. Import time does not make these January estimates
current market observations. The knowledge-base audit passes for all 64 originals.
Validation used the existing database and runtime libraries; no fixture dataset
was created and protected environment files were excluded. Fresh browser validation
was unavailable because browser automation failed to initialize; the intake proof
is at the database level. The subsequent HDFC browser checks use the existing normal
data and the repository's Docker Playwright runner; they do not retroactively add
browser proof for that benchmark-intake step.

## Continuing work

Reconcile the remaining company statements and accounting definitions, check
candidate versions, and prepare supported valuation inputs under delegated
authority. Keep source gaps visible and record a decision before applying a
material choice. Delegation removes repeated permission requests; it does not
supply missing evidence or close milestone gates by itself. GitHub publication
remains the final step of a coherent batch.
