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

Current totals: 33 periods, 906 facts, 980 source revisions and 336 normalized
values. Saved valuations, portfolios, source assets and unrelated tables remain
unchanged. Twenty-one read-only benchmark calculations pass across the existing
11-company universe; every draft still requires valuation review.

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

The user approved only localhost/127.0.0.1 network access and read-only access to
the macOS OpenSSL configuration. Those project-profile exceptions are saved;
protected environment restrictions remain. This active agent session still
returns a network-policy 403 and blocks the browser helper's system-file read.
Fresh normal-runtime browser verification is pending profile reload. Saved
screenshots identify the original defects; they do not verify this new UI.

GitHub publication and exact-head CI results are recorded below after local work.
M05-03/05 and M06-04/07 remain open. This batch does not add milestone acceptance
points or approve a current valuation. The tracker and limitation ledger own
remaining work, including the original Reliance and bank input gaps.

Local evidence: `output/milestones/m05-m06-ui-20261024/`, including source/build
manifest, test logs, backup comparison, failed audit, runtime and rollback receipts.
