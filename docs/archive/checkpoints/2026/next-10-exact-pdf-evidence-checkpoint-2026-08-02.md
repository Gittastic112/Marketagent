# Next 10: Exact Financial PDF Evidence Checkpoint

**Date:** 2026-08-02  
**Status:** Implemented and validated, without browser execution

## Completed Steps

1. Pinned `pypdfium2==5.12.1` and `Pillow==12.3.0` as direct backend runtime
   dependencies.
2. Added authenticated PNG rendering for a page from a stored document asset.
3. Limited render scale to `0.5`-`2.0` and output to 16 million pixels.
4. Added PNG output to the explicit binary response-contract inventory.
5. Added backend coverage for image bytes/dimensions, auth, page bounds, scale,
   content type, private caching, and `nosniff`.
6. Added strict finite, in-bounds `pdfplumber_top_left_points` geometry parsing.
7. Added support for single reported rows and multi-row component sums.
8. Added `/documents/{id}/financial-evidence` with source/candidate context and
   proportional overlays.
9. Routed supported candidate evidence links to the viewer while preserving
   direct PDF and document-level fallbacks.
10. Verified a live APSEZ promoted candidate and reconciled current-state,
    architecture, ingestion, security, runbook, handoff, roadmap, and register.

## Live Proof

```text
candidate_id: 40
document_id: 3
source_page: 465
locator_type: pdf_text_row
coordinate_system: pdfplumber_top_left_points
render_scale: 1.5
render_dimensions: 893 x 1170
render_size: 260741 bytes
PNG SHA-256: acb1ea73bfc3daab022336c5d003920f87e0177d7068b2fcc922e359b7dfe467
```

## Validation

```text
backend: 397 passed, 4 upstream openpyxl deprecation warnings
frontend: 80 passed
TypeScript: passed
Next.js 16.2.11 webpack production build: passed
focused binary/PDF contracts: 11 passed
```

## Security Contract

- The renderer accepts no URL and no uploaded request body.
- It renders only bytes already held by an authenticated document asset.
- Invalid pages fail before rendering; actual PDF bounds are checked again by
  the renderer.
- Scale and output pixels are bounded.
- PNG responses are inline, private, `no-store`, and `nosniff`.
- Frontend overlays require the declared top-left point coordinate system and
  finite boxes wholly inside the declared page.

## Honest Limits

- The viewer highlights the stored row box, not the exact numeric glyph inside
  that row. Component sums show every stored component row.
- Event `pdf_region` evidence does not yet use this viewer.
- No OCR, merged-cell reconstruction, or geometry inference was added.
- Browser automation and screenshot comparison were not executed in this batch.
- A malicious PDF parser/rendering boundary still requires worker isolation,
  malware scanning, and content-disarm controls before public deployment.

## Next Recommended Work

Reuse the bounded renderer for validated event PDF regions, then add
balance-sheet and cash-flow identities only after their required facts have
been reviewed with exact evidence.
