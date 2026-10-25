# M05/M06 UI and financing review, October 24, 2026

This extends the [industry/accounting checkpoint](m05-industry-and-accounting-2026-10-24.md)
under delegated research/demo review. Existing data, five personal approvals,
source reports, prior failed evidence and saved valuations are preserved.

## UI and matching changes

- Saved industry mixes open as compact summaries, with an explicit editor,
  readable field warnings, expandable coverage notes and full basis/source text.
- Segment removal has a visible label and an icon with reserved space. Mobile
  fields retain visible labels. The basis note is multiline.
- Drafting uses the saved mix and is disabled while edits are unsaved. Cancel
  restores the exact saved precision. Saving disables editor controls.
- A single-industry comparison does not create a fictitious 100% revenue mix.
  New allocations require explicit names and supported weights.
- Suggestions require a specific company-industry token and the requested
  benchmark market. Broad sector words no longer suggest unrelated biotech,
  healthcare or consumer services. Text similarity remains a review prompt.
- Financial identities show readable labels while preserving after-tax and
  parent/minority distinctions. Formula contracts and calculations are unchanged.

## Source review and application

[M05-BRIDGE-20 and M06-BRIDGE-01](../../../../data/reviews/financing-bridge-review-20261024.json)
pin three retained official reports, 66 original cells and 36 arithmetic checks.
Amazon's borrowing face/carrying amounts, operating/finance leases, imputed
interest and restricted cash remain separate. These historical definitions do
not establish complete current valuation debt or excess cash.

Alphabet FY2025 reports operating leases of USD15,954 million in both its balance
disclosure and maturity schedule. USD18,251 million undiscounted payments less
USD2,297 million imputed interest supports that reported total. Current and
noncurrent components sum to USD15,953 million. The USD1 million discrepancy is
retained without asserting that it is rounding. Both GOOG and GOOGL preserve the
same issuer evidence; their balances must not be added together.

The [application](../../../../data/reviews/financing-bridge-application-20261024.json)
promotes existing candidates 340/664, with unchanged amounts and explicit review
limitations, through Runs 147-150. It adds two facts/revisions and four normalized
aliases. Normalized warnings and both drafts retain the discrepancy and require
valuation review. Amazon's generic debt candidates stay held.

The initial final audit expected identical provenance strings and failed.
Independent reading of the backup, without restoring a database, verifies all
904 prior reported amounts and all 332 prior normalized values/units/warnings.
The installed earlier provenance repair adds exact source links and changes
source separators on 22 normalized records. All 34 referenced identities match
their current promoted candidates and revisions. Run 151 records successful
verification. The failed local audit is retained; the application was not rerun.

Totals after that lease application: 33 periods, 906 facts, 980 source revisions and 336 normalized
values. Saved valuations, portfolios, source assets and unrelated tables remain
unchanged. Twenty-one read-only benchmark calculations pass across the existing
11-company universe; every draft still requires valuation review.

## Borrowing-basis continuation

[M05-DEBT-21 and M06-DEBT-02](../../../../data/reviews/borrowing-basis-review-20261024.json)
check five retained official reports with 34 original cells, four inline XBRL facts
and 12 exact equations. This batch uses the existing sources and candidates.

- Alphabet FY2023/FY2024/FY2025 debt face amounts are USD13,000/12,000/49,085m;
  carrying amounts are USD12,870/11,882/48,543m. Current and noncurrent carrying
  components reconcile. Issued commercial paper is explicitly USD0/2,300/0m.
- NVIDIA FY2024/FY2025/FY2026 carrying debt is USD9,709/8,463/8,468m, with exact
  current/noncurrent components. FY2025 commercial paper is explicitly zero;
  the unsupported FY2024 zero remains held.
- Microsoft FY2024 short-term debt is USD6,693m. The borrowing note identifies
  its commercial-paper scope, while the face statement retains exact precision.
  FY2025 is explicitly zero. Commercial-paper investments remain assets.

The [application](../../../../data/reviews/borrowing-basis-application-20261024.json)
promotes 23 unchanged candidates through Runs 152-159. Six Alphabet face-value
totals and NVIDIA's unsupported zero stay held. It adds 23 facts and revisions,
bringing totals to 33 periods, 929 facts, 1,003 revisions and 336 normalized values.
All 906 prior facts and all normalized amounts/units/warnings remain unchanged.
There are 132 provenance enrichments and 325 verified current source references.
Saved valuations, source assets and 103 unrelated tables remain unchanged.

The pre-change 128,254,988-byte backup passes archive listing and SHA-256 validation;
it is not a restore rehearsal. Two read-only preflight failures arose from textual
timestamp precision and were corrected by comparing exact datetime instants.
A backup-listing pipe closed early before database writes; exit status and archive
validation remained required. After successful application, the wrapper compared
assets using table-style names. Matching assets by store/id, with unique identical
identity sets, verifies preservation. Failure evidence remains and the financial
application was not rerun. Separate read-only benchmark helper launch errors
(container socket permissions and package path) were corrected without app changes.

M06-DEBT-02 treats these amounts as historical evidence, not current market debt or
a complete lease-inclusive equity bridge. Twenty-one independent benchmark
calculations pass after application. All 11 drafts remain review-required and not
promotion-ready; both Alphabet drafts retain the USD1m lease warning. No saved
forecast, option value, WACC, share denominator or valuation is approved.

## Validation and rollout

Local checks: 64 focused backend tests without a fixture database; 309 frontend
tests; TypeScript and a production Next.js 16.4.1 build pass. The existing remote
browser workflow now checks compact display, full source disclosure, unsaved-edit
draft blocking, cancellation and visible removal on a narrow viewport.

The frontend and backend/worker images are installed. The original PostgreSQL
container, volume, schema, runtime settings and localhost-only bindings remain.
A 128,252,312-byte pre-change backup passes archive listing and hash validation;
this is not a new restore drill. Daily Brief resumes; source refresh and pgAdmin
remain stopped. Rollback copies retain files, logs, images and private settings.
The post-rollout sample totals about 680 MiB and 0.44% container CPU, a snapshot
of idle use rather than a capacity guarantee.

The user-approved localhost/127.0.0.1 and macOS OpenSSL read exceptions now work.
Protected environment restrictions remain. Fresh authenticated browser checks use
the normal application and existing data, with credentials only in memory.
Twenty-eight views cover all 11 valuation pages and selected Amazon/Alphabet
financial pages at 1440/390px. They verify saved precision, source disclosure,
coverage warnings, unsaved-edit drafting guards, Cancel, keyboard access and
visible mobile removal. Single-industry comparisons do not fabricate a mix.
Eight post-review financial views verify the 23 promoted and seven held entries.
Clean desktop/mobile screenshots confirm the compact summary and readable equations.

Both passes record zero browser errors, backend writes and accessibility violations.
All 109 table and source-asset fingerprints remain unchanged by each browser pass
and the separate read-only calculation check. Maximum recorded page readiness is
1,205ms against the unchanged 15-second gate; this is not a load or cold-start claim.
Daily Brief resumes after quiesced checks. Temporary browser/tool containers create
no dataset and are removed; normal services and existing data remain in place.

## GitHub publication

Source commit `6e2a6f8ba970835d986a975acb06640b31014aa2` contains exactly the
19 selected source/test/review/documentation paths. Every Git blob matches the
local manifest; all unlisted tree entries and modes are preserved. The shared
index hash remains `0f7cb26c0e162730396ea97090223c4eab69cf697f9b5124b156363f5cd7231e`.
Personal permission settings, protected files, source reports, backups and runtime
artifacts are excluded. Draft PR #2 remains stacked on draft PR #1.

All five gates pass on the exact source head in the
[PR run](https://github.com/Gittastic112/Marketagent/actions/runs/40127762419)
and [push run](https://github.com/Gittastic112/Marketagent/actions/runs/40127757426):
1,766 backend tests, 309 frontend tests, 64 browser workflows and six separate
PostgreSQL integration checks. The six baseline opt-in skips are covered by that
separate job. Dependency/container scans and concurrent backup/recovery also pass.
The changed browser test passes against remote fixtures. The separate normal-data
checks above verify the installed UI. The continuation publishes only the reviewed
receipts, decision register and affected documentation; installed source is unchanged.

M05-03/05 and M06-04/07 remain open. This batch does not add milestone acceptance
points or approve a current valuation. The tracker and limitation ledger own
remaining work, including the original Reliance and bank input gaps.

Local evidence: `output/milestones/m05-m06-ui-20261024/`, including source/build
manifest, test logs, backup comparison, failed audit, runtime and rollback receipts.
The continuation is retained in `output/milestones/m05-m06-normal-20261024/` and
`output/playwright/m05-m06-normal-20261024/`, including the independent post-review
browser pass, corrected audit, exact source checks and readiness summary.
