# M05 official sources and review preparation

October 13, 2026. Requested scope: gather official reports, reconcile numbers and
prepare company review batches while the operator defers Mac settings and the
off-device backup destination. This checkpoint does not accept M05 or promote data.

## Deliverables

The local packet is
`output/milestones/m05/review-batches-20261013/review-packet.html`.
It contains ten company HTML/JSON batches, retained originals, indexed report text,
exact reference locators, source hashes, comparisons, blank decisions and recipes.
The small [source register](../../../../data/certification/scoped-source-register-20261013.json)
is versioned; the approximately 218 MiB local packet is ignored by Git. Original
reports, candidate snapshots and renderings are not pushed to the repository.

| Batch | Issuer / securities | Fiscal years | Principal review focus |
|---|---|---|---|
| 01 | Apple / AAPL | 2023, 2024, 2025 | Restricted cash, debt/leases, share scale and payout |
| 02 | Microsoft / MSFT | 2024, 2025, 2026 | Finance leases, investment cash and capital spending |
| 03 | Reliance / RELIANCE | 2024, 2025, 2026 | GST, parent/NCI profit, deferred financing and bonus shares |
| 04 | HDFC Bank / HDFCBANK | 2024, 2025, 2026 | Bonus restatement, merger comparability and bank capital |
| 05 | NVIDIA / NVDA | 2024, 2025, 2026 | Split basis, combined PPE/intangible purchases and debt |
| 06 | Alphabet / GOOG and GOOGL | 2023, 2024, 2025 | Issuer/class denominators and lease/borrowing scope |
| 07 | Amazon / AMZN | 2023, 2024, 2025 | Face/carrying debt, restricted cash and financed assets |
| 08 | Bharti Airtel / BHARTIARTL | 2024, 2025, 2026 | Customer trust cash, exceptional items and share changes |
| 09 | ICICI Bank / ICICIBANK | 2024, 2025, 2026 | Mixed source scales, diluted earnings numerator and capital |
| 10 | State Bank of India / SBIN | 2024, 2025, 2026 | Revised income split, numeric grouping and bank capital |

Each batch has stable decision IDs, source/reference-review fields and candidate
versions where stored candidates exist. Reviewer, date, decision, reason and
correction start blank. Accounting/model approval is separate from transcription
review. The packet has no approval controls, database connection or active scripts.

## Acquisition and provenance

- Twenty selected official annual reports supply the three target years for all
  ten issuers. GOOG/GOOGL retain separate securities sharing one issuer's reports.
- Processing Runs 47-88 record 42 acquisition attempts: 36 successes and six
  failed/redirect attempts. Successes include entry pages, SEC submission indexes
  and supplementary reports as well as the twenty selected reports. Failures
  remain visible; retry successes do not erase them.
- Originals retain exact bytes, SHA-256, source URL, retrieval time, content type,
  byte count and Processing Run ID. SEC requests use the configured identity only
  in memory. Public-DNS checks, pinned destination addresses, verified TLS, no
  automatic redirects and bounded responses protect the acquisition path.
- A previous Microsoft FY2026 access gap is resolved by the official SEC 10-K.
  The issuer's annual-report landing page alone did not establish its absence.
- PDF source locators use one-based PDF page and extracted text-line positions.
  Printed page numbers can differ; Reliance/Airtel include two-page spreads.
  Cell bounding boxes are not independently audited. HTML locators retain explicit
  table, physical row and cell indexes from the hash-bound retained document.

## Reference preparation and reconciliation

The preparation recipe selects report rows directly, independently of the app
extractor and stored candidate values. There are 1,417 rows: 1,410 source selections
and seven explicitly labeled calculations. Of these, 1,174 are preferred versions
and 243 retain earlier comparative presentations. These are agent-prepared
references, not a complete or human-approved accuracy benchmark.

USD millions, Apple shares in thousands, INR crores/millions/thousands, actual
shares and per-share values retain distinct scales. Parent/group profit, class
denominators, borrowing/deposit/lease types and cash definitions remain separate.
Signs used for comparisons are explicit; a source dash stays null.

| Check | Result and boundary |
|---|---|
| Source arithmetic | 243 exact ties, one exact-tie exception and one uncomputed dash bridge. Decimal arithmetic uses no rounding tolerance. Some calculated totals reuse their components; the count is not an independent accuracy score |
| Stored SEC annual candidates | 402 rows checked: 352 numerical matches pending scope/review, three definition differences, four source dashes and 43 rows without a selected reference metric |
| Comparative revisions | Five changed rows: HDFC FY2025 diluted EPS and basic/diluted shares; SBI FY2025 interest earned and other income. Both versions are retained |
| Normal version check | All 402 candidate IDs, selected fields, timestamps and payload hashes still match the earlier export. All 667 candidates remain needs_review; no normalized histories or industry mappings exist |

Specific source findings:

- Amazon's stored total-debt candidate matches reported face value. Subtracting
  discount/issuance costs gives a carrying-value bridge lower by USD 374m, 360m
  and 440m in FY2023, FY2024 and FY2025. Both definitions have evidence; an explicit
  model choice is required, not an automatic correction of a false source number.
- Alphabet FY2025 operating leases total USD 15,954m, while selected current plus
  noncurrent components sum to USD 15,953m. The USD 1m difference stays visible;
  possible rounding/presentation is not a confirmed resolution.
- Airtel's FY2025 cash-flow bridge includes customer trust cash, restricted escrow
  and overdrafts and ties exactly. FY2026 escrow is a dash, so that bridge is not
  machine-completed. Trust cash is unavailable to the group.
- HDFC's FY2026 report restates FY2025 for a 1:1 bonus: diluted EPS 46.20 versus
  previously 92.39, with doubled weighted-average shares. FY2024 from the earlier
  report still needs an explicitly calculated common bonus basis. Merger-period
  comparability is a separate issue.
- SBI's later FY2025 comparative moves INR 625.0862 crore from interest earned to
  other income without changing total income. The general regrouping note does
  not independently establish the exact cause of this specific offset.

The first agent preparation selected Airtel balance-sheet tax assets/liabilities
instead of P&L tax charges. Three arithmetic failures exposed the mistake. The
recipe now selects the P&L rows explicitly; corrected arithmetic and rendered
source inspection pass. The initial diagnostic and correction are retained.

## Real-source PDF parser findings

The normal October 13 runtime image was run in isolated, read-only, network-disabled
containers against selected pages of ten India reports. No database connection
or candidate import was involved. All ten parsing calls completed, producing 94
candidates. Successful execution is not successful extraction:

| Comparison | Candidates |
|---|---:|
| Wrong reported value | 36 |
| Matching numeric value but missing/wrong unit | 16 |
| Accounting scope or selected reference unresolved | 42 |

Examples reproducible from retained previews:

- Reliance FY2026 cash becomes 158,842 crore by taking the opposite spread's trade
  payables; the source cash figure is 145,977 crore. Total assets similarly takes
  liabilities from the other printed page. Both wrong candidates are labeled high
  confidence by the existing extractor.
- SBI's unusual comma grouping is split into partial numeric tokens, with missing
  units and column misselection. Whole source values must survive tokenization.
- Airtel group profit is used where a parent-profit basis is required; cash-flow
  opening/closing balances can both become generic cash candidates.
- Bank RBI balances and borrowings lose their bank-specific meaning under generic
  cash/debt labels. Fixing a number alone does not establish model suitability.

The owning implementation is
`backend/app/services/pdf_financial_extraction.py`, with tests in
`backend/tests/test_pdf_financial_extraction.py`. Next engineering work is bounded
layout-region extraction, unit/number parsing and explicit accounting-scope
handling, followed by real-source previews and the existing review/browser gates.
No source-code fix or runtime rollout is claimed in this preparation checkpoint.

## Validation and state boundary

- All 36 retained original hashes verify. Reference IDs and preferred
  issuer/year/metric keys are unique; calculations retain input reference IDs.
- Eleven static HTML pages pass local-link and active-content checks. Chromium
  verifies all eleven at desktop/mobile widths: 22 views, no page errors, external
  requests or document overflow. Source images load. Desktop index and mobile
  HDFC rendering were also visually inspected.
- Selected rendered financial pages were visually inspected for Reliance, Airtel,
  HDFC, ICICI and SBI. This is a source-selection check, not a full report audit.
- Documentation validation and its focused regression suite are recorded with
  the packet. Application code/images are unchanged; the broad application suite
  is not re-run as evidence for these financial facts.
- Normal financial records are unchanged. The read-only recheck covers exported
  candidates and counts, not an all-table fingerprint. Acquisition Processing Runs
  were written, so the whole database is not claimed unchanged.

M05-02/03/04/05 remain open. Remaining note/model preparation and parser repairs
are agent work; source/reference, accounting, industry and model approval require
recorded human review. The [limitation ledger](../../../agent_capabilities_and_limitations.md)
owns those boundaries. M01-M02 remain accepted: 20 acceptance points. Mac settings
and off-device recovery remain deferred without blocking this preparation.
