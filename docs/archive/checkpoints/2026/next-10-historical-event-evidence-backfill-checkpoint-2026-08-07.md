# Next 10: Historical Event Evidence Backfill Checkpoint

**Date:** 2026-08-07  
**Status:** Implemented and validated, without browser execution

## Completed Steps

1. Added typed eligible, missing, unmatched, ambiguous, conflicting, applied,
   and race-skip statuses for historical evidence review.
2. Added a priority-ordered scanner for events without evidence references,
   bounded to 200 records per request.
3. Limited candidates to event descriptions and the authenticated user's alert
   evidence; another user's alert content is never considered or returned.
4. Required claims to be 24-2,000 characters and occur exactly once,
   case-sensitively, in stored source text.
5. Kept fuzzy and whitespace-normalized matching disabled and exposed manual
   corrective actions for every unsupported state.
6. Added GET preview and dry-run-first POST execution under Data Health.
7. Added event-row locks, duplicate rechecks, creator identity, source origin,
   and processing-run provenance to apply.
8. Added a Data Health review queue with exact claim coordinates, source links,
   status labels, limitations, and one explicit apply command.
9. Added ownership, ambiguity, conflict, bounds, dry-run, apply, rerun, and
   provenance regression coverage.
10. Ran a live read-only preview and reconciled current-state, architecture,
    security, runbook, handoff, roadmap, register, and capability docs.

## Live Preview

```text
bounded events checked: 1
eligible exact matches: 0
status counts: no_exact_match=1
live references created: 0
```

This is an honest limitation, not a failed run. The existing claim was not a
byte-exact source passage, so the workflow correctly left it for manual review.

## Validation

```text
focused backfill API tests: 4 passed
focused evidence/backfill tests: 10 passed
complete backend suite: 403 passed, 4 upstream openpyxl warnings
frontend unit/static suite: 85 passed
TypeScript: passed
Next.js 16.2.11 webpack production build: passed
git diff --check: passed
```

## Safety Contract

- GET performs no writes.
- POST defaults to `dry_run=true` and every POST creates a processing run.
- Apply locks the event and rechecks existing references before inserting.
- Alert evidence is current-user scoped.
- Only stored document text is searched; no URLs or providers are called.
- Exact offsets and quotes are persisted with a stable method and run ID.
- Fuzzy, normalized, ambiguous, conflicting, missing, and repeated matches are
  never promoted automatically.

## Honest Limits

- The scanner does not recover paraphrased historical summaries.
- It does not backfill sections, PDF geometry, OCR, or document-only evidence.
- It scans only events with no existing reference and does not replace weak
  legacy references automatically.
- Browser automation and screenshot comparison were not run in this batch.

## Next Recommended Work

Add a manual resolution workflow for the unmatched queue that lets the user
select and save an exact stored-text span without exposing raw filing bodies in
list APIs. After that, add reviewed balance-sheet and cash-flow identities.
