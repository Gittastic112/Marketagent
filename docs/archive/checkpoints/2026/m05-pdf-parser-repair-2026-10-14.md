# M05 PDF parser repair and review preparation

October 14, 2026. Agent-prepared source checks, not financial approval.
M01-M02 remain the only accepted gates. M05-02/03/04/05 stay open.

## Change and compatibility

`pdf_targeted_v3` fixes demonstrated facing-page column mixing, fiscal-range
start-year errors, split Indian number tokens, missing explicit unit forms and
overbroad accounting labels. It separates parent/group profit and cash-flow
opening/closing/adjustment amounts, preserves bank cash and borrowing scopes,
distinguishes basic/diluted shares and current/noncurrent financing rows, and
removes indiscriminate debt/lease summation. Equal values on different physical
rows remain distinct evidence. Only overlapping text/table reads are deduplicated.

Facing-page detection requires a gutter plus independent unit declarations and
consecutive folios or repeated fiscal headers. Landscape shape alone is insufficient.
Text locators retain full physical-page dimensions and absolute coordinates with
`P<page>:S<region>:L<line>:Y<year>` identity. Certification verifies the region and
its half-page bounds while retaining legacy locator compatibility. No schema
migration, existing-candidate rewrite, review or promotion occurs.

Unexplained numeric columns are skipped. Unknown currency glyphs stay unknown;
crore/lakh alone does not establish INR. Generic share labels do not establish a
share scale. Accounting-specific source codes cannot silently become generic cash
or debt inputs through the existing normalizer. These are partial extraction rules,
not OCR, complete merged-table reconstruction or financial certification.

## Retained official-source evidence

Local, Git-ignored output: `output/milestones/m05/review-batches-20261014-parser/`.
The original October 13 packet and original report bytes remain unchanged.
Ten official India PDFs, two reports for each of five issuers, were checked against
their retained SHA-256 hashes. HDFC share-note pages supplement the earlier statement
selection. The comparison fixes source/metric/year/page before inspecting values;
it never chooses a reference by its numerical agreement.

- 202 candidates: 182 have one prepared reference and no numeric mismatch.
- Of those 182, 102 match value and unit; 80 need unit confirmation.
- 20 candidates have no prepared reference; 438 selected prepared rows are outside
  this parser's supported coverage. Neither denominator is a completeness score.
- References remain agent-prepared, incomplete and unapproved. No financial
  candidates, normalized histories, industry mappings or model assumptions were saved.
- 100 accounting-note topic batches contain 222 bounded source excerpts. Their
  selection prioritizes consolidated-report sections and discloses omitted locations.
  They are review aids, not resolved accounting/model decisions.

The [single ledger](../../../agent_capabilities_and_limitations.md) owns remaining
unit, reference, accounting, model and operator limitations. The earlier
[source preparation checkpoint](m05-source-review-preparation-2026-10-13.md)
retains the company-specific reconciliation exceptions and original evidence.

## Verification

Initial new regression run: 17 failures and four passes against the old parser.
The first broad run exposed an outdated fixture assumption that an unspecified
share scale was certifiable. The updated test now verifies rejection until a Mock
Data reviewer supplies a unit. Regional-location validation was added without
relaxing existing geometry/hash checks.

- Final backend suite: 1,626 passed, six opt-in PostgreSQL checks skipped, five
  upstream deprecation warnings. These skips are not PostgreSQL proof.
- Four rollout success/rollback tests pass with an isolated fake Docker engine.
- Four distinct isolated browser cases pass: PDF upload/review/unit correction/
  promotion/normalization, stale-version correction recovery, exact-citation versus
  interpretation review, and invalid-session rejection. The initial run was three
  passes and one failure because the custom runner omitted the required citation
  fixture. Seeding the disposable database and rerunning that case passed. The
  original failure artifacts remain; application code was not changed for it.
- Four packet desktop/mobile views pass with no page errors or external requests.
  A mobile overflow/squeezed-column layout was corrected and visually rechecked.
  The retained Reliance/Airtel facing-page renders were inspected against the
  corrected numbers; all 202 final candidate locators satisfy physical bounds.

## Runtime and publication

The normal backend and both worker registrations use
`market-intelligence-m05-parser-runtime:20261014`; frontend remains the verified
October 13 image. Parser and certification source hashes match the built image.
The runtime image ID is
`sha256:75ddd485e03c39652139a9d4aa393e942b1b3cce0b0a19c450c01168be243e5f`.

The first preflight safely refused replacement because earlier acquisition work
remained in the backend's temporary directory. Before retrying, 103 files totaling
181,120,153 bytes were copied into the ignored packet and hash-verified against
an archive of the stopped container. No unverified temporary path was allowed.
The earlier failed attempt and both verified backups remain retained.

The successful format-3 backup is
`backups/20261014T190043Z-13561-market-intelligence`; its dump SHA-256 is
`67be0d624408356a72e6163fc34376de63ca1316cbabd6b48d9a6b6d767b2d20`.
All 109 table fingerprints match before/after replacement and after authenticated
normal browser reads. Original PostgreSQL volume and schema remain. The 24 routes
and 48 desktop/mobile views show no browser errors, overflow or automatic
accessibility violations; two forbidden-Origin checks pass. Maximum readiness
was 1,608 ms. No normal financial imports/approvals, fixtures or external AI calls.

Previously active services resumed; source refresh and pgAdmin remain stopped
with restart=no. Ports bind 127.0.0.1. The disposable workflow stack was removed
without persistent volumes. Rollback images, backups and failure evidence remain.
One post-rollout idle snapshot totals about 496 MiB and 0.61% CPU; this is not a
load test or a permanent resource guarantee.

GitHub publication is last on [draft PR #2](https://github.com/Gittastic112/Marketagent/pull/2),
with only explicitly selected files and the shared Git index preserved. The PR
owns the exact final head/check receipt. No merge and no new accepted milestone.
