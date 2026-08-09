# Next 10: Quick Valuation and Manual Event Evidence Checkpoint

**Date:** 2026-08-07  
**Status:** Implemented and validated, without browser execution

## Quick Valuation Repair

The screenshot failure was a real route mismatch. The frontend called two
unregistered endpoints and displayed the backend `404 Not Found` message after
submission. The repaired workflow now:

1. Generates reviewable assumptions through
   `POST /api/valuation/quick/assumptions`.
2. Calculates transient FCFF output through
   `POST /api/valuation/quick/calculate`.
3. Uses the existing assumption-autofill and deterministic DCF engines.
4. Rejects invalid growth horizons, terminal growth/WACC relationships, zero
   diluted shares, non-positive prices, and other unsafe numeric inputs.
5. Labels output `Calculation` and `is_persisted=false`.
6. Creates no `ValuationModel`, `DcfAssumptionSet`, or `DcfOutput` rows.
7. Fails visibly instead of filling the form with invented defaults.

Quick Valuation remains deliberately smaller than the durable workflow. It does
not save scenarios, sensitivity tables, reverse DCF, review acknowledgements, or
source decisions.

## Next 10 Completed

1. Defined typed exact-search and manual-resolution contracts.
2. Added authenticated search limited to the event's linked stored document.
3. Bounded queries to 8-300 characters, context to 40-300 characters per side,
   and returned occurrences to 25.
4. Kept exact case, punctuation, and whitespace semantics; fuzzy matching and
   normalization remain disabled.
5. Added source-hash, offset, quote, and occurrence-index revalidation on save.
6. Added event/document/company consistency and event-row locking.
7. Added duplicate protection plus authenticated creator and explicit origin.
8. Added `/events/{id}/evidence-resolution` with search, empty, error, partial,
   selected-occurrence, saved, and existing-evidence states.
9. Linked manual rows from the historical Data Health queue.
10. Added backend and frontend regression coverage and reconciled trust docs.

## Validation

```text
focused Quick Valuation + evidence-resolution tests: 9 passed
API security/response + focused feature tests: 13 passed
complete backend suite: 412 passed, 4 upstream openpyxl warnings
frontend unit/static suite: 87 passed
TypeScript: passed
Next.js 16.2.11 webpack production build: passed
```

## Safety Contract

- Search is read-only and never calls an external URL or provider.
- Search responses contain bounded snippets, not `RawDocument.raw_text`.
- Save accepts only the event's linked document and repeats every exactness
  check while holding the event lock.
- A changed content hash, moved occurrence, mismatched company, invalid span, or
  duplicate returns a stable failure and creates no reference.
- Search/query provenance is stored server-side and creator identity comes from
  backend authentication.
- High locator confidence describes reproducibility of the source location, not
  confidence in the investment conclusion.

## Honest Limits

- Search does not recover paraphrases, normalized whitespace, or case changes.
- It cannot resolve sources without stored text, including OCR-only PDFs.
- Selection is one exact query occurrence, not an arbitrary expandable range.
- The UI was compiled and statically tested, but browser automation and
  screenshot comparison were not run in this batch.

## Next Recommended Work

Add reviewed balance-sheet and cash-flow statement identities, then add a
source-text range-expansion control only if it can preserve exact server-side
validation and bounded disclosure.
