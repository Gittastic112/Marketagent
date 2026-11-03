# India financial review and normal rollout: October 18, 2026

Delegated decisions `M05-IN-10` and `M05-IN-11` apply selected historical facts for
Reliance, Airtel, ICICI and SBI to the existing normal database. This is agent
review under `AUTH-20261017-DELEGATED-REVIEW`, not personal user inspection or
independent human certification. The five explicit Apple approvals are unchanged.
The [decision log](../../../roadmaps/review-decisions.md) links exact public receipts;
the [limitation ledger](../../../agent_capabilities_and_limitations.md) owns open gaps.

## Source and accounting review

Ten retained official India PDFs pass fresh original-hash checks. Independent
PDFium text verifies 774 selected reference spans/tokens on 33 pages; visual
inspection covers those pages and the additional HDFC bonus/SBI reclassification
notes. No new provider fetch or fixture database was needed. Original packets and
their blank human-review fields remain unchanged.

The review recomputes 112 source accounting equations exactly and 24 EPS cases to
INR0.005 per-share precision. It preserves monetary/share scales and exact March 31
annual dates. ICICI's adjusted diluted-profit numerators and Airtel's FY2025 FCCB
adjustment are used rather than blindly dividing headline parent income. Bank
deposits, RBI cash, operating investments and policyholder balances are not
corporate valuation debt or excess cash.

Airtel's restricted/trust cash, overdrafts and cash-flow definition remain separate;
its FY2026 escrow dash is retained. SBI's FY2025 interest/other-income transfer is
equal and opposite at INR6,250,862 thousand, with total income unchanged. The report
supports regrouping, but does not identify the precise account cause. HDFC's 1:1
bonus and retrospective share/EPS basis are recorded without rewriting the already
promoted FY2024/FY2025 pre-bonus history. Proposed dividends stay separate from paid
cash and historical weighted shares from a current valuation denominator.

## Parser correction and application

Parser v6 tracks explicit asset headings. Current and noncurrent investments get
distinct metric codes; unclassified bank investments retain their existing code.
Contextless table extraction cannot reintroduce an ambiguous generic duplicate.
Original text, locations and review warnings remain. Five new regression cases
fail against v5, then all 86 focused tests pass. A validation-harness setup failure
is separately retained; it made no product/database changes.

All ten PDFs reproduce 784 candidates with unchanged values, units and physical
locations. Sixteen scoped labels/asset-scope annotations change. The old HDFC
report's 56 raw-parser unit gaps still require its previously recorded correction;
this does not claim universal automatic unit recognition.

The exact selected source plan uses FY2024 from FY2025 reports and FY2025/FY2026
from FY2026 reports. The deployed parser rechecks every candidate field before
audited intake, version-checked review and promotion. Runs 106-121 succeed:

| Company | Selected occurrences | Distinct facts | Annual periods | Normalized values | Older entries held |
|---|---:|---:|---:|---:|---:|
| Reliance | 150 | 138 | 3 | 24 | 50 |
| Airtel | 138 | 126 | 3 | 24 | 46 |
| ICICI | 108 | 102 | 3 | 12 | 36 |
| SBI | 96 | 90 | 3 | 12 | 32 |
| Total | 492 | 456 | 12 | 72 | 164 |

Eight source documents/assets are retained with their exact hashes and unknown
publication dates. Repeated source occurrences become separate revisions of one
canonical period fact. Independent Decimal calculations verify persisted derived
values; missing debt/EBIT/tax/capex/FCFF/FCFE inputs stay unavailable. Nine expected
tables change; 100 other tables and unrelated rows within changed tables match.
US/HDFC facts, portfolios, saved valuations and existing sources remain unchanged.
Combined selected coverage is 32 periods, 871 facts, 911 revisions and 328 normalized
values across all 11 scoped securities. Full model suitability is still open.

## Runtime, browser and resources

Backend/workers image `market-intelligence-m05-india-reviewed-runtime:20261018`
is `sha256:d7f1586433647c71bef5e9cbd637f89d0dac506f2037fd0ace7a3139de1ccff3`.
Frontend image `market-intelligence-m05-accessible-pdf-frontend:20261018` is
`sha256:b26f726d436601f3891b02230173332261fee2bb96938bca4449eb37dd6de872`.
The original PostgreSQL container, volume, schema and runtime settings remain;
ports bind localhost. Runtime settings travel only in memory, with no protected
environment-file reads. Stopped rollback containers/images are retained.

Quiesced dumps before the backend and frontend changes are 12,146,346 and
111,095,724 bytes. The latter includes the new official PDFs and reviewed facts.
Both pass archive listing. This is not a new restore or off-device-recovery claim.

The first mobile source view fails keyboard accessibility because its scrolling
PDF region is unfocusable. The financial evidence page now uses the same focusable
region pattern as event evidence; the existing PDF workflow has a keyboard/axe
regression. The failed run is retained. All 302 frontend tests, production build
and type checking pass.

The final normal browser run passes 16 desktop/mobile financial and source views,
456 reported-value comparisons and 164 held-candidate checks. All four mobile PDF
regions scroll using the keyboard. Ready times are 396-813ms for financial pages
and 1,000-2,909ms for rendered evidence, within the unchanged 15-second budget.
No browser errors, page overflow, backend writes or axe violations are observed.
Screenshots and additional actual-viewport visual checks confirm the source regions;
full-page mobile captures retain the fixed-header capture artifact separately.
All 109 table fingerprints remain unchanged after application through the final
browser checks. Daily Brief resumes; source refresh and pgAdmin remain stopped.

A post-work sample records 0.44% combined CPU and 1,209.55MiB container working set,
excluding Docker VM overhead. Docker reports 25.41GB images, 3.338GB volumes and
4.487GB build cache; shared-layer totals are not additive. Backups, rollback
images, volumes and failed evidence are preserved. Usage is a dated observation,
not a promise that future ingestion/builds require no resources.

## Evidence and remaining work

Exact review: `data/reviews/india-financial-review-20261018.json`.
Application: `data/reviews/india-financial-application-20261018.json`.
Full source audit, parser comparisons, versions/fingerprints, rollout receipts,
backup listings, browser traces/screenshots and replay recipes are under
`output/milestones/india-review-20261018/`. The newly copied local skill folders
are user files and are excluded from this publication batch.

M05-02 now has selected-layout/reference proof. M05-03/04/05 still require broader
notes, HDFC's latest bonus-comparable history, accounting/model bridges and industry
mapping/weighting. M06 retains its input-basis gates. M01-M02 remain the only accepted
milestones: 20 acceptance points, not an estimate of engineering effort. Mac and
off-device setup remain deferred, local credential rotation stays an operator
gate, and M10 needs actual use and final acceptance. GitHub publication follows
local verification; the draft PR owns its latest exact-head CI status.
