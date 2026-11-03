# M05 industry and accounting review, October 22-24, 2026

The existing normal database now contains seven provisional revenue mixes, four
single-industry comparisons and six audited India benchmark versions. An Amazon
profit-identity defect is repaired without changing any original reported amount.
This is delegated agent review for local research/demo use, not independent human
certification or approval of current valuations. M01-M02 remain the only accepted
milestones. No new local fixture database, fabricated activity or public deployment.

## Source review and decisions

The [review receipt](../../../../data/reviews/industry-and-accounting-review-20261022.json)
pins ten original report hashes, 25 US revenue cells, 30 source/arithmetic checks
and the exact India note/page treatment. Decisions M05-MAPPING-16 and M05-IN-NOTES-17
retain tax, elimination, parent/minority, EPS, dilution and segment-definition
differences. Original reports, workbooks and prior approvals are preserved.

- Apple: Products/Services comparisons; the internet-services category is an
  explicit proxy with an alternative software comparison. This supersedes only
  M05-AAPL-04B's provisional mapping decision, preserving five personal approvals.
- NVIDIA: two reported segments use one Semiconductor comparison.
- Microsoft: ten disclosed product/service lines retain mixed-business caveats.
- GOOG/GOOGL: the same issuer mix, with hedging outside business revenue weights.
- Amazon: reported regional retail and AWS segments; gross/net sales differences
  and mixed service activities remain explicit.
- Airtel: external-customer revenue only, excluding intersegment eliminations;
  an India benchmark does not establish Africa country risk.
- Reliance: Diversified comparison; no manufactured net external-revenue weights
  from gross turnover, GST and inconsistent intersegment bases.
- HDFC/ICICI/SBI: Bank (Money Center) comparisons, without claiming all group
  revenue is banking or revenue-weighting bank returns on equity.

M05-INDIA-BENCHMARK-18 imports the six retained January 5, 2026 India workbooks.
Mirrors match the immutable originals, including `roeIndia(1).xls`. Independent
XLS reading checks 1,968 numeric cells; 1,310 persisted typed rows match the
validated parser output across 20,936 attributes. Versions 7-12 and Runs 126-131
retain source date, hash, country and missing values. Global WACC inputs, small
samples and unsupported adjusted-margin columns remain visible limitations.

The [application receipt](../../../../data/reviews/industry-and-accounting-application-20261024.json)
records 29 allocations, Runs 132-142, ten changed tables and 99 unchanged tables.
Financial histories, saved valuations and portfolio records were unchanged by
this mapping/import step. It also contains the remaining per-company input review.

## Calculation corrections

Aggregation version 2 uses `1 / sum(weight / sales_to_capital)` for the capital
ratio. Margins and compatible sales-denominator ratios use revenue-weighted means.
Missing components withhold the whole field. Multi-industry returns on capital/
equity, capital structure and multi-year growth are unavailable without their
proper denominator/period basis. Industry financing totals are not inherited from
the first segment. A single taxonomy retains its own prior/context. The method
version participates in draft refresh while manual edits remain protected.

M05-AMZN-19 records [three after-tax losses](../../../../data/reviews/amazon-equity-income-review-20261022.json):
USD12m, USD101m and USD554m for FY2023-2025. Twelve original statement cells and
the retained SEC snapshot reconcile all three reported profits. Only explicitly
reviewed after-tax income enters the identity; the generic SEC equity-income tag
does not establish this presentation. No balancing amount or zero is invented.

The [Amazon application](../../../../data/reviews/amazon-equity-income-application-20261024.json)
adds candidates 1452-1454 and three facts/revisions through version-checked review
and promotion. Runs 143/144 succeed. Run 145 remains failed because its post-commit
audit expected unchanged provenance text. Reading the pre-change backup, without
restoring a database, proves all 901 earlier reported facts and all 332 normalized
values/units/warnings are unchanged. The installed prior provenance repair adds
54 exact source-revision references to 36 normalized rows. Every reference is
verified against its period, fact and active source revision. Run 146 records this
successful verification; no values were repaired or applied twice.

The scoped universe now has 33 periods, 904 facts, 978 source revisions and 332
normalized values. Amazon's three profit checks pass; parent/minority attribution
remains unavailable, so overall identity coverage is partial. All 11 companies
still need valuation input review; no current model was approved.

## Validation and normal runtime

- 33 focused pure calculation checks pass without a database. The earlier failing
  regression logs remain. The new draft-refresh integration regression passes in
  remote CI; local fixture creation remains outside authorization.
- 21 independent calculations verify the installed mixes and source-method
  provenance using the existing database in a read-only transaction.
- 22 normal desktop/mobile mapping views and four subsequent Amazon financial/
  valuation views pass: saved values, partial coverage, source notes, keyboard
  access, bounded scrolling, zero axe violations and no browser/backend writes.
  Maximum observed ready time is 1.101 seconds against the retained 15-second gate.
- October 24 verifies the same installed source after Docker restarts. All 109
  table/asset fingerprints still match the post-application browser baseline.
- Backend/workers use `739c9e32b83d`; frontend remains `ae3b16e35ee7` with Next.js
  16.4.1. Four changed service hashes match the runtime. Original PostgreSQL volume,
  settings and localhost-only bindings remain; no protected environment file read.
- Backend, frontend, PostgreSQL and Daily Brief worker run. Source refresh and
  pgAdmin remain stopped with restart disabled. Twenty-three rollback containers,
  their images, source evidence and failed receipts are retained.
- The final 128,252,312-byte quiesced dump passes archive listing and SHA-256
  verification. This is not a new restore test or encrypted off-device backup.
- A settled October 24 sample totals 609.1 MiB and 0.34% CPU across four running
  containers. This is an idle observation, not a sustained-load guarantee.

Local evidence is under `output/milestones/m05-completion-20261022/`, including
browser images, original failures, exact comparisons, source manifests, backups,
runtime receipts and reproducible operation scripts. User-added skill folders are
preserved locally and are not part of the publication whitelist.

Source commit `ceae4f6ce37b84f6ef2acd631306a53af1023a7a` passes all five GitHub
gates on both the [PR run](https://github.com/Gittastic112/Marketagent/actions/runs/40114933656)
and [push run](https://github.com/Gittastic112/Marketagent/actions/runs/40114929628):
1,758 backend tests, 304 frontend tests, TypeScript, production build, 64 browser
workflows, recovery, dependency and container-security checks. Six opt-in baseline
PostgreSQL skips are covered by all six passing checks in the separate browser job.
An exact 20-path publication preserves every unrelated remote file and the shared
local Git index. This checkpoint's final results follow as documentation only;
the installed application source is unchanged. Earlier CI remains dated evidence.

## Acceptance boundary

M05-03/05 and M06-04/07 remain open for complete accounting/equity/peer inputs and
genuine-source valuation verification. Reliance's unavailable weights, valuation-
date cash/claims/shares, sustainable bank equity inputs and explicit forecasts
are not supplied by benchmark imports. The feature register is reconciled, but
M10's full reviewed-input freeze, actual-use days and final acceptance are not
complete. The [single ledger](../../../agent_capabilities_and_limitations.md)
owns operator requirements and deferred host/off-device work.
