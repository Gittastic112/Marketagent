# Next 10: Exact Event PDF Evidence Checkpoint

**Date:** 2026-08-07  
**Status:** Implemented and validated, without browser execution

## Completed Steps

1. Defined one normalized event PDF-region contract using physical page number,
   top-left point coordinates, page dimensions, and a positive-area box.
2. Required new `pdf_region` writes to include that geometry.
3. Compared declared page dimensions with the stored PDF before persistence.
4. Normalized accepted geometry and rejected missing, mismatched, non-finite,
   unsupported, or out-of-bounds values.
5. Extended Data Health to identify malformed or irreproducible legacy regions.
6. Added a distinct `region` evidence precision and downgraded invalid legacy
   regions to partial page-level evidence.
7. Routed exact event evidence through the bounded authenticated page renderer.
8. Added `/documents/{id}/event-evidence` with claim context, source metadata,
   one proportional overlay, and an explicit source-PDF fallback.
9. Connected alert evidence and document review to the exact viewer only when
   strict frontend geometry validation passes.
10. Added backend/API, frontend parser, static integration, type, and production
    build regression checks and reconciled active documentation.

## Validation

```text
focused backend evidence tests: 10 passed
complete backend suite: 399 passed, 4 upstream openpyxl warnings
frontend unit/static suite: 84 passed
TypeScript: passed
Next.js 16.2.11 webpack production build: passed
```

## Exact Geometry Contract

```json
{
  "page": 12,
  "coordinate_system": "pdfplumber_top_left_points",
  "page_width": 612,
  "page_height": 792,
  "bounding_box": {
    "x0": 50,
    "top": 100,
    "x1": 550,
    "bottom": 130
  }
}
```

The `page` must equal `source_page`; dimensions must match the immutable stored
PDF within one point; coordinates must be finite, positive-area, and wholly
inside the page.

## Honest Limits

- Existing malformed/page-only PDF-region rows are audited, not rewritten.
- The viewer highlights one stored region and does not infer glyph, word, or
  table-cell geometry.
- Browser automation and screenshot comparison were not run in this batch.
- PDF worker isolation, malware scanning, and content disarm remain required
  before public deployment.

## Next Recommended Work

Backfill exact region evidence for high-priority historical alerts, then add
balance-sheet and cash-flow identities only after their source facts have been
reviewed with exact evidence.
