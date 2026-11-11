# Financial Statement Extraction Skill

## Purpose

Handle filing text/PDF/workbook/XBRL extraction, candidate review, promotion, and normalized financials without contaminating valuation with unreviewed data.

## When to use

- Filing text extraction.
- PDF filing upload and deterministic table-cell extraction.
- SEC XBRL `companyfacts` extraction.
- Screener `.xlsx` upload extraction.
- Financial candidate review/reject/override/promote.
- Normalized financial snapshots/metrics.
- Valuation autofill inputs sourced from financials.

## When NOT to use

- General RSS/news ingestion.
- Pure valuation formulas after reviewed inputs already exist.

## Prerequisites

- Use the handoff/code map already read, then the relevant sections of
  `docs/data-sources.md`. Consult Current State for evidence dates.
- Inspect `backend/app/services/financial_extraction.py`,
  `backend/app/services/pdf_financial_extraction.py`, and
  `backend/app/services/sec_xbrl_extractor.py`.

## Inputs

- Company.
- Filing `RawDocument`, validated PDF asset, or SEC CIK/companyfacts.
- Candidate metrics.
- User review/override decisions.

## Outputs

- Reviewable `financial_extraction_candidates`.
- Reviewed/rejected/overridden candidate states.
- Promoted metrics only after review.
- Provenance notes, warnings, units, and currency.
- Normalized coverage and trust-readiness reports.
- Source-versus-normalized reconciliation reports.

## Workflow

1. Ingest filing or SEC facts into source-linked records.
2. Extract candidates, not trusted facts.
3. Preserve source text, warning codes, method, confidence, fiscal period, unit,
   document id, and a typed locator: text line/page/section; PDF
   page/table/row/column plus point bounding boxes; spreadsheet
   sheet/row/column/cell; or XBRL concept/unit/period/accession.
4. Require a reporting unit plus user review before promotion.
5. Handle overrides separately from raw extracted values.
6. Promote only reviewed/overridden candidates.
7. Decide canonical storage: legacy financial tables, normalized financial tables, or both.
8. Feed trusted actuals through the canonical reviewed-financials path. The
   separate SEC draft adapter may suggest unreviewed annual candidates only with
   explicit candidate/source/period/unit/review labels. A suggestion is not a
   normalized fact, approval or permission to overwrite saved assumptions.
9. Block autofill from silently using placeholder actuals.
10. For workbook uploads, enforce type/size limits, hash content, reject duplicates, delete temporary files, and persist a processing run.
11. Read normalized coverage before backfill; distinguish normalized coverage from trust readiness and stop on currency conflicts.
12. Run reconciliation after normalization; mismatches block valuation use, and missing/normalized-only values remain explicit gaps.
13. Record filing, XBRL, workbook, and backfill attempts through the shared processing-run lifecycle.
14. For PDF uploads, require auth, extension/MIME/magic/size/page checks,
    sanitized basenames, company-scoped duplicate hashes, metadata-only
    responses, and authenticated `no-store` binary streaming.
15. Treat PDF extraction as a first-pass candidate source. Do not imply OCR,
    merged-cell reconstruction, total validation, or statement completeness.
16. Run `npm run test:e2e:pdf` after changing upload, candidate review,
    override, promotion, normalized coverage, or reconciliation behavior.
17. Use representative fixtures only when they are explicitly labeled
    `Mock Data` and isolated to tests. Never load
    `normalized_financial_histories.json` into production research tables.
18. Treat lexical passage matches and AI source suggestions as review
    candidates. Only stored exact spans that pass the owning validator may be
    described as exact evidence; neither state promotes a financial fact.

## Acceptance criteria

- Unreviewed extraction cannot feed valuation silently.
- Currency/unit and source provenance are present.
- Missing units, inferred years, and ambiguous source lines lower confidence and remain visible.
- Upload records use valid `Source`, `RawDocument`, content hash, and `ProcessingRun` rows; temporary paths are never persisted.
- PDF bytes are isolated in one-to-one `DocumentAsset` rows and never appear in
  raw-document or asset metadata responses.
- PDF candidates link to the exact authenticated source page and preserve table
  and cell bounding boxes using a documented coordinate system.
- Coverage reports identify missing/stale snapshots, low-confidence currency, and conflicts before and after writes.
- Reconciliation reports exact values, mismatches, gaps, deltas, provenance, and warnings.
- Absent reported metrics are not materialized as zero-valued source facts.
- XBRL source id handling is not hardcoded.
- Focused tests cover review, override, reject, and promote behavior.
- Promoted financials are not treated as canonical until the normalized financial storage/read path is documented.
- Source-grounded actuals come from reviewed/promoted metrics, not `AssumptionAutofillEngine` fallback defaults.
- The deterministic PDF browser fixture reviews all 12 candidates, supplies
  missing share units, promotes exactly 12, and verifies 2/2 trust-ready periods
  with zero reconciliation mismatches.
- Synthetic US and India histories verify the normalization/autofill contract;
  they do not prove real-source parser coverage.
- Citation assistance cannot bypass candidate review, reconciliation, or promotion.

## Common mistakes

- Treating SEC `companyfacts` as complete statements.
- Defaulting promoted currency to USD without checking company/reporting currency.
- Writing normalized tables without documenting canonical read path.
- Letting autofill defaults look like company actuals.
- Calling explicit text page markers or unverified parser boxes audited PDF coordinates.
- Treating 100% normalized coverage as trust-ready when currency confidence is low.
- Treating spreadsheet cell coordinates as audited PDF bounding boxes.
- Ignoring a reconciliation mismatch after source metrics change.
- Increasing PDF confidence before representative source totals and comparative
  periods reconcile.

## Do not do

- Do not call AI to calculate financial statements.
- Do not treat industry averages as company facts.
- Do not overwrite user-reviewed data silently.

## Related skills

- `data-ingestion-workflow`
- `valuation-workflow`
- `backend-api-change`
- `security-review`

## References

- `docs/HANDOFF.md`
- `docs/current-state.md`
- `docs/database-schema.md`
- `docs/roadmaps/product-roadmap.md`
- `backend/app/services/pdf_financial_extraction.py`
- `backend/app/api/routers/pdf_filings.py`
- `backend/tests/test_pdf_financial_extraction.py`
