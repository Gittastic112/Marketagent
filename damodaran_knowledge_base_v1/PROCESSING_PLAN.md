# Damodaran Knowledge Base Processing Plan

Documentation reconciled: `2026-09-22`. Earlier intake history remains below.

The September 22 US intake adds three unique originals and verifies three
duplicates: 64 canonical raw files, 64 catalog rows, 44 processing-ledger rows,
and no pending inbox files. Existing source bytes remain unchanged. Six dated
US mirrors are scoped separately from India; see
[the intake reference](reference/us_benchmark_intake_2026.md). No company mapping
or doctrine was auto-approved. Application counts and tests below are historical;
use [application Current State](../docs/current-state.md) for newer evidence.

## Objective

Maintain a source-backed valuation knowledge layer that an agent can enter in
minutes, audit deterministically, and use without confusing doctrine, dated
benchmarks, empirical estimates, or company-specific examples.

## Historical intake checkpoint

The repository did not contain the required `raw/inbox/` directory. The folder
`Data for Model/` was therefore processed as the legacy intake location.

Intake result:

- `38` source files inspected: `35` legacy workbooks and `3` PDFs.
- `12` workbooks were byte-identical to existing canonical raw files and were
  recorded as verified duplicates without another copy.
- `26` unique sources were routed: `21` datasets, `2` model/tools, and `3` PDFs.
- Canonical immutable raw corpus after routing: `61` files.
- India benchmark snapshots expose an embedded update date of `2026-01-05`.
- `macro.xls` ends in 2009; `macrodur.xls` uses 1987-1997 sector regressions.
- No manual review items remain open. The ratings-date item was resolved by an
  explicit user assumption, and the application regression conflict was fixed
  against the source PDFs, both on `2026-08-07`.

The literal `raw/inbox/` is now empty and ready for future intake.

## Completed phases

### 1. Corpus integrity

- hashed every legacy intake source
- checked exact duplicates before routing
- copied unique originals without modification
- rebuilt `data/raw_file_hashes.csv`
- recorded source-to-canonical and application-mirror paths in
  `data/processing_ledger.csv`

### 2. Content classification

- inspected workbook sheet maps and embedded descriptions
- distinguished India, Global, and historical datasets
- visually inspected all three PDFs and extracted their dates/methods
- corrected retrieval metadata for the misleading filename
  `global regression debt.pdf` (it contains dividend regressions)

### 3. Knowledge extraction

- added exact 2025 debt/dividend regression equations and fit warnings
- mapped the synthetic-ratings workbook
- mapped the macro-duration workbook and historical-data limits
- added country-risk/default-adjustment formulas with dated provenance
- promoted no spreadsheet snapshot values into timeless doctrine

### 4. Operating structure

- created a real inbox with explicit intake rules
- expanded the source catalog with canonical paths, date confidence, and status
- added a deterministic integrity auditor and focused unit tests
- rewrote the start/index/manifest docs around the actual repository state

## Application phases and historical evidence

### Phase A: Resolve unsafe application regressions

Status: completed on `2026-08-07`.

The application now stores the six exact January 2025 source models and 26
coefficients. Seeding updates only these known models, removes only their obsolete
legacy rows, and is idempotent. API and UI inputs match the source variables and
units. Outputs are labeled `Estimate`, include provenance and fit, reject stored
coefficient drift, and disable the statistically unusable payout models.

Definition of done:

- exact source/version stored with each coefficient set
- unit contract enforced and tested
- weak models disabled or visibly low-confidence
- no destructive global delete during normal seeding
- API output labels the result `Estimate`

Validation: 7 focused regression tests and the full 419-test backend suite pass.
The local database was synchronized, and an immediate second seed run reported
26 unchanged coefficients with no creates, updates, or removals.

### Phase B: Preserve the ratings approval boundary

Status: source-backed application lookup completed on `2026-08-08`.

The user approved treating `ratings.xls` as recent. The workbook remains
source-date unknown with low date confidence, and the recency decision is a
`User Assumption`. A future dated source should be added as a new version rather
than rewriting this decision.

The application now uses all 45 exact source rows across large non-financial,
small/risky, and financial-service tables. The versioned catalog is tied to the
canonical source hash; API output exposes the selected band and full
provenance. The legacy two-table boolean remains compatible. Iterative
operating-lease capitalization remains unimplemented.

Validation: 27 focused ratings/WACC/coverage tests and the full 434-test backend
suite pass.

### Phase C: Close application ingestion coverage

Status: coverage inventory completed on `2026-08-08`; typed ingestion breadth
remains partial.

The versioned application registry now inventories all 35 mirrored workbooks
against canonical paths, dates, confidence, metric families, supported and
missing fields, destination tables, parser support, and corrective actions.
`GET /data-health/damodaran-coverage` combines that registry with physical
source presence, generic import metadata, and live typed-row counts. Data Health
shows unsupported, partial, not-ingested, metadata-only, source-missing,
historical, and user-assumed-recency states explicitly.

The 2026-08-08 local snapshot has all 35 mirrors present, 9 sources with typed
rows, 2,787 typed records, 5 fully supported sources, 17 partial sources, and 13
unsupported sources. Capex, ROE, Margin, Working Capital, Dividend, FCFE, and
Volatility now preserve source hashes and historical typed versions. The approved ROE workbook
contributes 94 exact industry rows, including unadjusted and R&D-adjusted ROE.
The four newer conversions each contribute 94 exact rows and reject missing
source headers. FCFE preserves aggregate before-debt and after-debt values rather
than inventing unavailable components. This expands the versioned-import slice;
it does not close the ingestion-breadth gate.

Definition of done:

- [x] coverage matrix per source and metric
- [x] unsupported files shown as unsupported rather than silently ignored
- [ ] idempotent versioned import for each approved source-specific parser
- [ ] source hash and as-of date on stored benchmark records
- [ ] focused parser and ingestion tests for each added source

Completed slice on `2026-08-08`:

- [x] shared hash-idempotent version service for Capex, ROE, Margin, Working
  Capital, Dividend, FCFE, Volatility, PE, PBV, PS, and EV/EBITDA
- [x] source hash, byte size, as-of/confidence, canonical path, active state,
  supersession time, and row count on those active versions
- [x] exact 94-row `roeIndia.xls` importer with null and aggregate-row handling
- [x] exact-header Margin, Working Capital, Dividend, and FCFE importers with
  null and aggregate-row handling
- [x] exact-header volatility importer with both workbook assumptions, preserved
  zero/null cells, active API reads, and no fabricated fallback
- [x] exact-header PE, PBV, PS, and EV/EBITDA importers with complete growth,
  return, margin, and normalization controls plus source-separated active reads
- [x] exact-header country-statistics importer with all meaningful scale,
  balance-sheet, multiple, dividend, and source-date fields plus active API reads
- [x] active-version filtering in assumption, industry, fallback, and country
  lookup consumers
- [x] live idempotence proof for eleven importers and Data Health mirror-hash
  visibility

In that historical database, active versions were Capex `#39`, ROE `#40`, Margin `#41`, Working
Capital `#42`, Dividend `#43`, FCFE `#44`, Volatility `#45`, PE `#46`, PBV
`#47`, PS `#48`, EV/EBITDA `#49`, and Country Statistics `#50`. Active typed
provenance is complete for twelve current sources, with no partial, missing, or
mismatched active source. Current source-specific typed replacement paths are
closed. New analytical breadth still requires an exact source contract and the
same preserved-version tests.

Do not mark the unchecked phase-wide items complete until every approved
source-specific importer uses the preserved-version contract. In particular,
do not infer a historical source hash by hashing today's mirror.

### Phase D: Retrieval efficiency

Priority: medium.

Add a small query helper over `source_catalog.csv`, `formula_map.csv`, and
machine-readable rules. Retrieval must filter by knowledge type, geography,
as-of date, and status before opening raw files.

Definition of done:

- one command finds the correct source for a valuation input
- superseded/historical/review-required sources are excluded by default
- agent output cites canonical path and as-of date

### Phase E: Ongoing intake

For every future inbox batch:

1. Run the audit and inventory pending files.
2. Hash before opening or routing.
3. Inspect content and embedded metadata.
4. Check exact and semantic duplicates.
5. Classify as doctrine, model/tool, dated data, or case evidence.
6. Copy the untouched original to its canonical raw destination.
7. Add extraction/reference material only where it reduces future rework.
8. Compare against canonical rules and application behavior.
9. Route unresolved conflicts to `review_queue/`.
10. Update ledgers, catalog, manifest, docs, and tests.
11. Refresh hashes and rerun the audit.

## Five-minute agent start

From the repository root:

```bash
python3 damodaran_knowledge_base_v1/tools/audit_kb.py
sed -n '1,220p' damodaran_knowledge_base_v1/INDEX.md
sed -n '1,260p' damodaran_knowledge_base_v1/AGENTS.md
find damodaran_knowledge_base_v1/raw/inbox -type f ! -name README.md -print
```

Exit codes from the auditor:

- `0`: corpus is consistent and inbox is empty
- `1`: integrity/catalog error
- `2`: integrity is valid but inbox files are pending processing

## Completion standard for an inbox run

An intake run is complete only when:

- every source has a hash and processing-ledger row
- every unique source has one canonical immutable raw path
- every canonical raw file has one catalog row
- source/as-of date and date confidence are explicit
- dated data has not been promoted as doctrine
- unresolved conflicts have review items
- `python3 -m unittest discover -s damodaran_knowledge_base_v1/tools -p 'test_*.py'` passes
- `python3 damodaran_knowledge_base_v1/tools/audit_kb.py` exits `0`
