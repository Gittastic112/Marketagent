# PDF Financial Extraction Checkpoint

**Date:** 2026-07-25  
**Status:** First deterministic milestone shipped; broader statement auditing proposed.

## Shipped

- Authenticated PDF upload at
  `POST /api/companies/{company_id}/filings/pdf`.
- `.pdf` extension, MIME, `%PDF-` signature, 20MB size, 500-page, basename,
  SHA-256, and duplicate controls.
- One-to-one `document_assets` storage for original PDF bytes.
- Metadata-only asset response and authenticated inline source streaming.
- Page text extraction and line-detected table parsing with `pdfplumber 0.11.10`.
- Explicit fiscal-year column mapping for supported financial metric aliases.
- Candidate units derived only from explicit PDF currency/scale text.
- Page/table/row/column and table/cell bounding-box evidence locators using
  `pdfplumber_top_left_points`.
- Review links that open the original PDF at the extracted page.
- Processing-run records for success, duplicate, validation, and parser errors.
- Focused fixture/API tests, full backend suite, frontend tests, typecheck, build,
  and Alembic head verification.
- Isolated authenticated Playwright coverage for upload, 12 candidate
  reviews/overrides, promotion, 2/2 normalized trust-ready periods, and zero
  source-reconciliation mismatches.

## Trust Boundary

Every extracted value is a `FinancialExtractionCandidate` with
`needs_review`. Nothing is auto-promoted into normalized financials or valuation.
High parser confidence means the supported label, year, unit, and cell geometry
were explicit. It does not mean the filing or statement is complete or audited.

## Known Limitations

- No OCR for scanned/image-only PDFs.
- No password-protected PDF support.
- No merged-cell, multiline-header, borderless-table, or cross-page table model.
- No statement-specific classification beyond the supported metric aliases.
- No subtotal, accounting-equation, comparative-column, or statement-total
  reconciliation.
- No on-page bounding-box highlight overlay; evidence opens at the source page.
- Synchronous parsing has size/page caps but no worker isolation, cancellation,
  malware scan, or hard CPU timeout.
- Binary database storage is acceptable for local-first use but should be
  replaced by encrypted object storage before a serious multi-user deployment.

## Proposed Next Milestones

### 1. Evidence Overlay

Render the PDF page and highlight the stored cell bounding box. Keep the
original PDF link as a fallback. Verify coordinate transforms at multiple zoom
levels and page rotations.

Acceptance:

- Highlight matches the source cell on representative US and India filings.
- No source text is rendered as trusted HTML.
- Missing geometry falls back to the page without a fake highlight.

### 2. Layout Profiles

Add deterministic profiles for common income statement, balance sheet, and cash
flow layouts, including multiline headers and cross-page continuations.

Acceptance:

- Profiles are selected from observable layout signals, not company identity.
- Unsupported layouts return explicit warnings and candidate gaps.
- Existing simple-table extraction remains stable.

### 3. Financial Reconciliation

Validate subtotals, balance-sheet equations, cash-flow roll-forwards, and
comparative periods before increasing confidence.

Acceptance:

- Reconciliation results preserve formulas, tolerances, source cells, and
  failure reasons.
- Mismatches block trust-ready status but do not rewrite source values.
- Tests include negative values, parentheses, multiple scales, and restatements.

### 4. Representative Source Set

Load reviewed annual/quarterly reports from at least one US and one India
company and measure extraction, normalized coverage, and reconciliation gaps.

Acceptance:

- No source file or credential is committed without approval.
- Results distinguish parser coverage from accounting trust readiness.
- Mapping changes are driven by the measured gaps.

### 5. Worker Isolation

Move parsing behind a bounded worker before any public or multi-user deployment.

Acceptance:

- Hard timeout, memory limit, cancellation, safe failure state, and retry policy.
- Optional malware/content-disarm scan is documented.
- Processing runs remain authoritative and never expose stack traces or paths.

## Verification Baseline

```text
Backend: 301 passed, 4 third-party openpyxl deprecation warnings
Frontend: 58 passed
Authenticated Playwright: 2 passed
TypeScript: 0 errors
Frontend production build: success
NPM audit: 0 known vulnerabilities
Alembic: a7a7a7a7a7a7 (head)
Docker services: 4 running
```
