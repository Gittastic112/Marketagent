# HDFC review, normalization and populated financial UI

Completed October 18, 2026 under `AUTH-20261017-DELEGATED-REVIEW`.
The [decision log](../../../roadmaps/review-decisions.md) owns review choices;
the [tracker](../../../roadmaps/completion-tracker.md) retains 20 acceptance points.
This is selected historical HDFC evidence, not whole-universe M05 acceptance.

## Source and review

Retained official annual report SHA-256:
`2a1879eee544526b7cecacb5380c2664f92e0d031361f5d54ffe55370c9487ea`.
Physical pages 441, 442 and 515 (printed 446, 447 and 520) were rendered and
visually checked. [Official annual report](https://www.hdfc.bank.in/content/dam/hdfcbankpws/in/en/pdf/annual-reports/2024-25/HDFC_Bank_Annual_Report_2024_25-310202.pdf).

Separate [official audited results](https://www.hdfc.bank.in/content/dam/hdfcbankpws/in/en/pdf/financial-results/2024-2025/quarter-4/financial-results-for-the-quarter-and-year-ended-March-31-2025.pdf),
physical pages 9 and 11, corroborate INR crore/share units despite the annual
report's unembedded currency glyph. Supplement SHA-256:
`6c5f091ab14a7d3b97114fe2d59a6a148722e9e67cf43d34cabe10181954cbd7`.

- M05-HDFCBANK-05 accepts 64 selected FY2024/FY2025 consolidated source entries.
  Fifty-two monetary units become INR crores and four EPS units INR/share;
  eight existing share/EPS units are retained. Fourteen exact statement identities
  and four rounded EPS checks pass. Review is delegated agent review.
- M05-HDFCBANK-06 applies exact March 31 year ends through the authenticated
  period API and current-version candidate promotion. The incorrect intake-as-
  publication timestamp is changed to unknown; actual ingestion time is retained.
- M05-HDFCBANK-07 corrects only four identical EPS projections created by that
  promotion. Their exact row IDs/values/timestamps remain in the receipt and
  Processing Run 99. All source candidates and source revisions are retained.

Document 10 / asset 1 retain the original PDF. Runs 97, 98 and 99 succeed.
Each annual period has 30 distinct reported facts and four normalized values:
parent-attributable net income, basic shares, diluted shares and minority interests.
All 64 source occurrences remain. Promotion changes eight tables; the other 101
tables and unrelated records within changed tables match their prior fingerprints.
Company mappings, other financials, saved valuations and portfolios are unchanged.
The final read-only scoped inventory retains 667 unpromoted US candidates. HDFC
is the only one of the 11 securities with normalized periods in this database;
its narrow historical selection does not count as complete model coverage.

## Correctness changes

`financial_metric_derivations.py` contains pure deterministic calculations;
`accounting_normalization.py` retains persistence and provenance. Missing inputs
stay unavailable, explicit zeros remain valid and arithmetic requires matching
units. Historical tax requires reported tax and pre-tax income. FCFE requires net
borrowing. Reported net capex is not reduced by depreciation a second time.
Coverage and reconciliation also keep net capex distinct from gross capex, so a
complete net-capex input does not create a needless gross-capex backfill request.
ROE/ROIC explicitly identify their period-end balance basis.

Promotion reuses pending metric inserts when the statement and notes repeat a
value, blocks conflicting duplicates before financial writes, and flushes source
revisions before assigning the next occurrence's sequence. Original source-history
metadata from the first HDFC attempt remains historical; it is not silently rewritten.
PDF intake no longer invents a publication date when the uploader supplies none.

Populated financial tables have named, keyboard-focusable scroll regions. The
review queue says no candidates are awaiting review after promotion. Normalization
and currency checks no longer claim complete valuation readiness; reconciliation
explicitly describes comparable normalized metrics. Neither label certifies a model.

## Validation and failure evidence

- Broad backend suite: 1,695 passed, six opt-in PostgreSQL checks skipped, five
  dependency deprecation warnings. After the final source-revision sequencing and
  capex-alias adjustments, all 71 focused financial/PDF tests passed. No migration changed.
- Frontend: 302 tests, production build and TypeScript passed. Installed Linux
  dependency versions match the lockfile; absent optional packages for other
  platforms are excluded from that comparison. No dependency was added/downloaded.
- Normal browser: four desktop/mobile filing/fundamental views, 64 source values,
  two exact periods and eight normalized values verified. Final checks performed
  zero period/promotion writes. Maximum readiness 953 ms against the unchanged
  15-second gate. Zero page errors, page overflow or detected accessibility violations.
  Mobile Tab/ArrowRight scrolling passed on the populated normalized table.
- Three views retain automatic color-contrast checks requiring manual interpretation
  because of background images or clipped scroll content. Screenshots were inspected;
  automated checks do not establish universal accessibility conformance.

Failed evidence is retained. The initial full-suite run lacked repository fixtures
(24 failures); mounting the existing data fixed the harness. Regressions separately
reproduced net-capex, duplicate insertion/conflict and revision-sequencing defects.
Normal promotion exposed four duplicate EPS projections, corrected as recorded
above. A later browser assertion incorrectly expected promoted rows in the review
queue; exact candidate-ID reads now verify those retained records. The populated
mobile browser then found the unfocusable scroll region, repaired before final proof.
The first frontend dependency preflight counted absent optional platform packages;
the final check verifies every installed version and every required package.

## Local rollout and resources

Backend/workers: `market-intelligence-m05-reviewed-financial-runtime:20261018`
(`sha256:e19bbd767299a3783d621dff5dac8732c9d78118a4caec495b448f1f0d037983`).
Frontend: `market-intelligence-m05-reviewed-frontend:20261017`
(`sha256:974314ac9d9556cd84ae8342acfc3c940385c95d0bbbe19dfc18507e7b7626ac`).
Four backend source hashes match the installed image; the frontend source manifest
pins its allowlisted build input. Protected environment files are excluded.
Runtime credentials/settings were forwarded only in memory.

The original PostgreSQL container, volume and schema are preserved. Backend and
frontend replacements retain localhost-only bindings and prior runtime settings.
Final browser reads preserve all 109 table fingerprints. The scheduler is resumed
after that check; later scheduled writes are not part of the unchanged-read claim.
The source scheduler and pgAdmin remain stopped. Ten replaced app containers are
removed after preserving temporary artifacts, without deleting any volume.
Rollback images and existing restore-verified backups remain. Three additional
quiesced dumps pass archive listing; no new restore verification is claimed.

Before the final capex-alias rollout, three samples of the four normal services totaled 506.6 to 507.7 MiB
container RAM and 0.30% to 0.72% CPU on the one-core percentage scale.
This excludes Docker VM overhead and is not a future resource guarantee. Docker
reported 24.70 GB of image layers across
86 images before that final image build; categories share layers and must not be added.
The Mac filesystem reported 26 GiB available. Retained images/backups are not disposable
database datasets. No new persistent fixture database or provider/AI call was made.

## Evidence location and remaining scope

Local artifacts are under `output/milestones/m05/delegated-review-20261017/`:
source/promotion/correction decisions, application receipts, failed/passing logs,
source manifests, quiesced dumps, temporary-file preservation and browser images.
Full database fingerprints remain local. The checked-in decision register embeds
public review receipts and bounded summaries. Failed artifacts are preserved.

The [single limitation ledger](../../../agent_capabilities_and_limitations.md)
owns open work: other company statements/notes, bank comparability/current model
inputs, earlier source-occurrence metadata, broader mappings and release acceptance.
This historical pre-August-2025-bonus basis is not current share/EPS comparability,
an approved bank valuation, independent human certification or M05 completion.
Mac/off-device setup remains deferred. Actual-use days and final acceptance are
not invented. GitHub publication follows the local checks and documentation audit.
