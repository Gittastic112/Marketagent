# Integration review, November 19, 2026

The four reviews examined the application released in [PR 22](https://github.com/Gittastic112/Marketagent/pull/22), commit `e3b39d4`. The following findings were reproduced or evaluated with synthetic evidence. They establish behavior under the stated conditions. The [current handoff](../../../HANDOFF.md) records installation and release status. [Limitations](../../../limitations.md) owns open evidence and policy decisions.

## Findings and verification

| ID | Change | Verification |
|---|---|---|
| 01 | Refuse a legacy upgrade that would discard populated industry pricing multiples. The online check locks the table before inspection. Offline SQL generation refuses a crossing that requires data inspection. | PostgreSQL at `76dd1d347c33` with each protected column populated alone and all three together. Retained revisions and values survive refusal. A competing writer waits on the guard. |
| 02 | Refuse an upgrade that would assign private rows to the fallback owner. The read-only diagnostic counts affected rows by table. | Fresh database, populated predecessor and an existing fallback account with and without private rows. Owner-scoped reads continue to enforce access. |
| 03 | Validate Alpha Vantage’s returned symbol for prices and history. Massive corporate actions report the venue evidence the vendor supplied. | Controlled vendor responses cover matching and conflicting symbols and absent or inconsistent venue evidence. |
| 04 | Store daily closes separately from quotes, keyed by the price source and adjustment basis. | Repeated quote-first and close-first writes retain one daily close of USD 100 alongside the current USD 104 quote. The chart returns the close. |
| 05 | Accept the reviewed edgartools SEC extraction contract in dated financial inputs with its accession, source hash and publication date. | An explicitly promoted synthetic FY2023 USD 100 disclosure becomes eligible after its February 1 filing. An earlier as-of date excludes it. Legacy SEC evidence remains covered. |
| 06 | Withhold holding value, complete NAV and linked returns when the selected price predates a split or bonus reflected in the share count. | Mock Data with a two-for-one split, a pre-split quote and a subsequent eligible close. |
| 07 | Serialize transaction creation by portfolio. Insert earlier activity in effective-date order and reconcile the resulting holdings and cash in the same transaction. | A purchase effective before a split produces 24 shares. An invalid proposed book rolls back. Deleting the inserted purchase restores the previous balance. Concurrent additions are checked against the resulting holdings, cash and transaction count on PostgreSQL. |
| 08 | Carry dependency warnings and review state into derived ratios. Include source changes in the saved basis signature. | Ratio tests retain the numeric result and expose source warnings. The valuation draft suite checks review, stale input and promotion behavior. |
| 09 | Select the configured benchmark series consistently at the boundaries and external cash flows. | Overlapping providers, mismatched symbols, incompatible share bases, conflicted dates and an eligible flat reference series. |
| 10 | Send only submitted fields when editing an alert and preserve an unavailable linked record. | Form payload tests distinguish omission from an explicit clear. A signed-in title edit preserves evidence, change description, issuer and event. |
| 11 | Deduplicate reviewed SEC overrides using their original source identity and retain amended accessions separately. | An unchanged extraction after an override from USD 100 to 95 creates zero candidates. A changed accession remains a distinct review item. |
| 12 | Retain ALFRED observations with the applicable series metadata, raw response, date and hash. Surface missing units, frequency or seasonal basis as partial evidence. | Mock vintage responses cover revisions, missing observations, a truncated response and metadata by vintage. Changing only the units produces a new raw receipt, and an identical repeat reuses it. Values stay in the source’s original units. |
| 13 | Enforce the same split and bonus exclusions when a portfolio risk request uses the default date or supplies it explicitly. | Both request forms report unavailable on the affected holding. Unaffected historical price series retain their prior behavior. |
| 14 | Commit a thesis change and its accumulated drift score together, under the owning thesis lock. | PostgreSQL accepts two competing updates exactly once and rolls both writes back on a forced storage failure. A second owner is denied access. |
| 15 | Treat malformed or unreadable successful JSON responses as unconfirmed writes. Preserve form input and allow deliberate bodyless success. | Server transport tests cover malformed 200/201, rejected response streams, valid JSON and 204. Uncertain writes issue one request. |
| 16 | Display document, sections, candidate and reference load states independently, with a retry and retained source context. | Server page tests distinguish valid empty results, partial failure, denied access and missing documents. |
| 17 | Return from a thesis to its original private price anchor and show a later same-date correction separately. | A USD 95 pin reopens alongside the corrected USD 98 close. The corrected point has no original pin. Owner checks, matching request IDs and concurrent pin retries are exercised. |
| 18 | Use a native modal for Evidence Trail, with keyboard focus contained and restored to the opener. | Signed-in Firefox at 1440×900 and 390×844 checks opening, Tab, Shift+Tab, Escape and focus return. |
| 19 | Accept fractional drift scores on the thesis form using its existing numeric contract. | Firefox submits 0.25 by keyboard on desktop and mobile, then rereads both the saved change and the updated thesis total. |

## Checks run on the release candidate

| Check | Result and scope |
|---|---|
| PostgreSQL preservation and concurrency | 28 passed, zero skipped, against disposable PostgreSQL. Includes preserved predecessor rows, table locks, competing saves, pin idempotency and chronological purchases. |
| Optional source, market and research adapters | 139 passed with the pinned packages and network-disabled fixtures. These tests overlap the core backend suite. |
| Frontend | 425 passed, zero skipped. TypeScript and the generated adapter interface check passed. |
| Recovery | 38 backup workflow and recovery metadata tests passed against disposable resources. |
| Packaging | The standalone frontend was built from its checked-in Dockerfile. The registry refused a fresh pull of the pinned backend base. The local backend package therefore reused the installed immutable runtime and its identical dependency locks with the reviewed application source. |
| Browser | Signed-in Firefox on local disposable PostgreSQL covered alert evidence retention, keyboard focus, corrected price pins and fractional thesis drift. |

## Reproduction and interpretation

Run the backend, optional adapter and frontend checks in the environments listed in the [execution runbook](../../../execution-runbook.md). The browser runner now executes both the ingestion concurrency suite and the predecessor preservation suite against a disposable PostgreSQL database. It builds the standalone frontend runner. Recovery tests use generated fixtures and an isolated Docker command double.

- **Portfolio reconciliation.** A separate read-only calculation compared 61 values or conditions across two stored USD example snapshots. Quantities, stored price basis, base-currency conversion, cash, NAV and attribution reconciled. The example has no configured benchmark. This exercise covers the labeled sample only.
- **XIRR.** Four synthetic, annual-spaced cash-flow streams exercised the current 365.25-day convention. Using days 0, 365, 730 and 1095 as needed, amounts `[-100, 110]` yielded approximately 10.0072%. Both `[-100, 100, -110]` (no root) and `[-100, 230, -132]` (two roots) yielded unavailable. For `[-100, 360, -431, 171.6]`, one of three roots was returned, approximately 30.0234%. Consumers cannot infer uniqueness from a returned number. Choosing a reporting convention remains a methodology decision.
- **Calendars and prices.** Pinned calendar fixtures exercise an early close, a holiday and daylight-saving changes. Historical listing identity, complete supplier coverage and the cause of a stock move require original evidence. The chart presents nearby documents as context and stores the analyst’s interpretation separately.
- **Thesis reassignment.** Changing a thesis company retains the original company on an existing pin. Owner checks still apply, including after a same-date price correction. A policy for moving or detaching historical pins and impacts remains open.
- **Release boundaries.** A refusal to discard legacy data is a preservation result. Mapping old multiples, assigning private records to an owner and correcting previously stored balances or drift totals require separate decisions. No personal records are needed to repeat the automated checks.
