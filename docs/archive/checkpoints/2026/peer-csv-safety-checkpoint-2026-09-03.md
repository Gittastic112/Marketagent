# Peer CSV Safety Checkpoint

**Date:** 2026-09-03

## Twenty tracked steps

1. Enforce the UTF-8 byte limit before parsing or database access.
2. Reject invalid Unicode text at the request boundary.
3. Reject NUL bytes rather than storing them as evidence.
4. Parse CSV with strict quote handling.
5. Return controlled preview errors for malformed or oversized fields.
6. Reject surplus row cells instead of silently ignoring them.
7. Reject short rows instead of treating missing columns as empty values.
8. Stop reading beyond the 50-peer limit.
9. Report physical CSV line numbers for row errors.
10. Validate peer-set name length during preview, not only apply.
11. Validate peer-set notes length through the complete create contract.
12. Reject whitespace-only peer-set and source identities.
13. Reject non-finite numeric cells without echoing uploaded values in errors.
14. Sanitize invalid integer/company-ID cell errors.
15. Block CSV export when normalized and JSON evidence disagree.
16. Preserve literal apostrophe/formula-leading text through export and reimport.
17. Check browser file type and size before reading.
18. Decode UTF-8 strictly and expose sanitized file-read errors.
19. Clear stale previews and disable apply during file reads or failed requests.
20. Run regression/build/runtime checks and reconcile the limitation ledger.

These are implementation and verification steps, not 20 Git commits. The shared
worktree contains substantial earlier changes and remains uncommitted.

## Evidence and limits

The new backend safety tests reproduced 13 failures before the fixes. After the
fixes, all 43 peer lifecycle and CSV safety tests passed. The browser file-reader
tests cover eight cases, including BOM preservation, malformed UTF-8, NUL bytes,
oversized inputs, and file-read failures.

Validation: 670 backend tests passed with four upstream `openpyxl` deprecation
warnings; 47 focused CSV/peer/Alembic/readiness tests passed; 136 frontend tests,
TypeScript, and production Docker builds passed. Documentation validation covers
62 active Markdown files and 299 local links. No new interactive browser test
was run in this increment.

Deployment checks passed: backend and frontend healthchecks are healthy,
PostgreSQL is healthy, scheduler is running, backend readiness reports `m4` with
no missing tables/columns, and frontend auth readiness is configured for local
single-user use. Four documentation-checker tests and `git diff --check` pass.

Next unblocked task: owner-scoped idempotent CSV apply to make an uncertain
network retry safe without creating duplicate Draft sets.

This hardening does not independently verify financial evidence. CSV apply still
creates a new Draft each time; it has no exactly-once retry key. If a network
response is lost after a successful apply, inspect the existing sets before
retrying. The 1 MB limit applies to decoded CSV content, not a general HTTP request
body quota. No schema change is required; the head remains `m4m4m4m4m4m4`.

## Changed code

- `backend/app/services/peer_valuation_import.py`
- `backend/app/services/peer_valuation_sets.py`
- `backend/tests/test_peer_csv_safety.py`
- `frontend/lib/peer-csv-file.ts`
- `frontend/lib/peer-csv-file.test.ts`
- `frontend/components/valuation/peer-set-manager.tsx`
- `frontend/lib/frontend-integrity.test.ts`
