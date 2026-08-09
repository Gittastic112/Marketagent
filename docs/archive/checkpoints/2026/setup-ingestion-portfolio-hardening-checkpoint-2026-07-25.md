# Setup, Ingestion, and Portfolio Hardening Checkpoint

**Date:** 2026-07-25

This checkpoint records the 30-step batch completed after the company setup
industry selector and SEC filing picker failed in the authenticated UI. It is a
verified implementation record, not a claim that every application workflow is
complete.

## Completed Steps

1. Reproduced the empty Damodaran industry selector in an authenticated browser.
2. Traced the selector through the wizard, API client, router, and mapping service.
3. Added exact-country taxonomy lookup before fallback lookup.
4. Added fallback to an available taxonomy when the requested country is absent.
5. Added an API warning that names the fallback country.
6. Made the wizard taxonomy request resilient to loading and failure states.
7. Verified 94 industry choices load for the current local dataset.
8. Inspected SEC preview, source selection, import state, and checkbox rendering.
9. Made SEC ingestion `source_id` optional in the API contract.
10. Added validation for a supplied SEC-compatible source.
11. Added resolution of an existing active SEC source.
12. Added local `SEC EDGAR` source creation when no SEC source exists.
13. Applied source resolution to selected and recent SEC ingestion routes.
14. Replaced the broken checkbox markup with the shared labeled checkbox field.
15. Removed the missing-source disable condition from the company filing picker.
16. Removed the direct Next.js rewrite that bypassed the authenticated proxy.
17. Corrected route revalidation after SEC import.
18. Propagated the authenticated user through ingestion and manual processing.
19. Made generated alerts user-owned and user-scoped for deduplication.
20. Replaced full-filing event descriptions with concise source-backed summaries.
21. Stripped HTML and bounded filing-diff, event, and alert display text.
22. Added raw-document summary read models and list/detail summary endpoints.
23. Migrated document, event, research, company, section, and AI pickers to summaries.
24. Prevented metadata edits from erasing stored raw filing text.
25. Scoped portfolio parents and all child CRUD routes to the current user.
26. Made missing active-position prices invalidate aggregate value/P&L/weights.
27. Corrected top-gainer/top-loser classification to use signed P&L.
28. Split portfolio entry into opening holdings, security activity, and cash activity.
29. Filtered Data page controls to active RSS sources and CIK-backed SEC companies.
30. Completed authenticated SEC checks, major-route smoke, and a temporary
    portfolio create, transact, deposit, price, value, snapshot, and cleanup cycle.

## Browser Verification

- Company setup displayed 94 industry choices with an explicit fallback warning.
- SEC preview displayed an automatic `SEC EDGAR` source, a normal labeled filing
  text checkbox, a filing choice, and an enabled import action.
- A real AAPL 2025 10-K import persisted source, raw document, event, and alert.
- Portfolio lifecycle produced the expected holding, cash, valuation, P&L, and
  snapshot, then removed every temporary record.
- Major authenticated route smoke returned the app shell without rendered
  failure states. `/data` and `/data-health` passed when checked independently
  after their first compilation.

## Remaining Work

1. Add PDF bounding-box overlays, OCR, complex table reconstruction, and
   accounting reconciliation.
2. Replace the explicitly mocked market-regime page with source-backed modules
   only as providers become available.
3. Load reviewed real-source India and US histories and reconcile them before
   removing labeled compatibility fallbacks.

## Post-Checkpoint Log Audit

The final backend log review exposed `/api/admin/damodaran/files` reading a
nonexistent `created_at` model attribute. The route now returns the model's
`imported_at` value through the existing `created_at` response field, requires
authenticated identity, and has a route-level regression test.

## Follow-On Completion

1. Added Playwright coverage for valuation draft save, reset, refresh, archive,
   reopen, review, and atomic promotion.
2. Added Playwright coverage for deterministic PDF upload, all candidate
   reviews/overrides, promotion, normalized coverage, and reconciliation.
3. Isolated browser tests in a separate `market-intel-e2e` Compose project with
   a tmpfs database, production-mode frontend, non-default ports, and automatic
   cleanup.
4. Added synthetic, explicitly `Mock Data` US and India three-period histories
   that verify normalization, trust readiness, exact reconciliation, historical
   revenue growth, and autofill. These are automated fixtures, not production
   research records.
5. Repaired fresh-database migration defects discovered by the isolated run:
   duplicate normalized-table operations and missing creation of
   `event_thesis_impacts`.
6. Removed the unauthenticated temporary runtime DDL route.
7. Verified `301` backend tests, `58` frontend tests, two Playwright workflows,
   TypeScript, production build, and zero known npm audit vulnerabilities.
