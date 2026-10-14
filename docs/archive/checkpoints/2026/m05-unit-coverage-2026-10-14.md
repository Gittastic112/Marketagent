# M05 unit and source coverage follow-up

October 14, 2026. Agent-prepared source evidence, with no financial approvals.
M01-M02 remain the only accepted milestones. M05-02/03/04/05 stay open.

## Parser behavior

`pdf_targeted_v4` adds explicit statement totals, banking line items, cash-flow
movements and weighted-share notes. Banking interest, deposits, parent/group
profit, pre-associate profit, financing components and cash-flow adjustments
retain distinct meanings. Investment rows remain separate physical evidence,
with an accounting-scope warning; no automatic cash/debt/component sums occur.

Observed embedded ITFRupee font encodings can identify INR only with a matching
unit-header symbol, embedded font resource and physical header position. The
candidate keeps that evidence and a review warning. An unembedded font name or
bare Latin letter cannot establish currency. Explicit per-share currency and
local share-count scales do not inherit a monetary million/crore scale.

Narrowly recognized wrapped labels retain original text and full-row highlights.
The spaced HDFC balance-sheet heading is recognized. Unexplained extra numeric
columns and currency glyphs attached to numbers remain skipped. No migration,
existing-candidate rewrite, financial import, approval or promotion was performed.

## Official reports and review packet

Local, Git-ignored output: `output/milestones/m05/review-batches-20261014-coverage/`.
Start with `review-packet.html`; `review-queue.json` retains pending decisions.
The October 13 originals and October 14 parser-repair packet remain unchanged.

- Ten retained India reports were hash-verified and checked with bounded
  single-page jobs. Earlier multi-page processing-limit failures are retained;
  CPU, memory and wall-time limits were not relaxed.
- 776 candidates compare to 760 distinct prepared reference entries. All values
  match: 720 also match units, and 56 have proposed HDFC unit corrections.
- No candidate lacks a prepared reference. Eight prepared entries remain outside
  parser coverage: four Airtel cash-flow entries with marginal numeric columns
  and four SBI per-share entries with currency glyphs attached to the values.
- 116 supplementary reference entries were selected from retained PDFium text,
  independently of app parser candidates. Repeated investment rows are selected
  by physical order and scope before comparing values, never by numerical fit.
- Counts include separate repeated disclosures and comparative years. They are
  not unique company facts, a completeness percentage or reviewed certification.

Processing Runs 89 and 90 retain an official NSE HDFC annual-report copy and HDFC
audited annual results. The NSE copy has the same missing-font problem. Rendered
audited-results pages 9 and 11 explicitly identify rupees/crore and rupees/share.
Sixteen annual-column anchors match the older annual report. This supports the
56 pending unit corrections without altering the original parser output.

The packet includes source hashes, exact pages, rendered unit/manual-row evidence,
comparison records and links to the existing ten-company and 100-topic note
review batches. Preview rows are not persisted candidate IDs. Any later import
must retain identical source bytes and use current stored candidate versions for
review/promotion. Source accuracy, accounting scope and model/industry choices
remain separate human decisions in the [single ledger](../../../agent_capabilities_and_limitations.md).

## Validation and runtime

The focused parser suite passes 76 tests, including 40 new coverage regressions.
The full backend suite passes 1,666 tests with six opt-in PostgreSQL skips and five
upstream warnings. It exits successfully after a slow shutdown; no test process
was killed to manufacture success. Four isolated rollout success/rollback tests pass.

Four isolated browser cases pass: PDF upload/review/unit correction/promotion/
normalization, stale-version correction recovery, exact-citation versus human
interpretation review, and invalid-session rejection. These use Mock Data in a
disposable database. Four review-packet desktop/mobile views pass without browser
errors, horizontal overflow or external requests. Unit and manual-row source
images, plus desktop/mobile packet screenshots, were visually inspected.

Normal backend and worker registrations now use
`market-intelligence-m05-coverage-runtime:20261014`, image
`sha256:ceba6ef58ea519bc9ce13c18d8baf5d154c7adc524941cb4dd68f8a2f1dc1051`.
The unchanged frontend remains the verified October 13 image. The installed parser
hash matches the final source and all ten final report previews:
`6e100c428def65be2f55965e6884af9607a68908b1fbbe6ae9dfc9d2657099bb`.

Verified format-3 backup: `backups/20261014T214541Z-15719-market-intelligence`;
dump SHA-256: `8e5424b62dd8c55bc45d8160f5bc5c8bcb0d118a3584a9b60d476b3a63f499b0`.
Seven temporary files totaling 14,333,174 bytes were copied and hash-verified
before replacement. All 109 table fingerprints match across rollout and normal
browser verification. The original PostgreSQL volume/schema and settings remain.

Normal checks cover 24 routes and 48 desktop/mobile views, with zero browser
errors/overflow and two forbidden-Origin checks. Maximum readiness is 11,789 ms,
inside the unchanged 15-second gate; this is not a load or speed-improvement claim.
Prior containers remained until browser/data acceptance. Previously active services
resumed; source refresh and pgAdmin stay stopped with restart=no. Ports remain
localhost-only. Disposable validation containers are removed; backups and rollback
images remain. Acquisition writes are limited to the two audited Processing Runs;
normal financial records were not changed.

GitHub publication is last on [draft PR #2](https://github.com/Gittastic112/Marketagent/pull/2),
using explicit paths and an isolated Git snapshot. The shared index is preserved;
the PR owns the exact final head/check receipt. No merge or new milestone acceptance.
