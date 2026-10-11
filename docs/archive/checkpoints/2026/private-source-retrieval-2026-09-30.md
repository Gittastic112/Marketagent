# Private-source retrieval

Date: 2026-09-30. Source implementation and isolated verification, not a normal-runtime rollout.

## Completed workstream

The research inbox previously exposed only the latest 20 private sources. It now
supports owner-scoped title/stored-text search, company/format/scan-state filters,
and previous/older pages. Search uses escaped, case-insensitive literal matching
before pagination. A descending source-ID cursor avoids shifting forward pages
when newer sources arrive.

The existing latest-source API remains compatible. The new GET
`/brief-sources/search` returns items and an optional `next_before_id`. Inputs are
bounded; list responses omit original text and PDF bytes. At most one extra row
determines whether another page exists, and related reads retain the existing
three-query budget. Retrieval makes no AI/provider call or research/valuation write.

The UI separates intake from the source library, uses the existing request-scope
helper, clears unavailable results, and preserves active filters after saves/scans.
A newly saved source has a direct inspection link even when it does not match
the active filters. Company-catalog failures do not hide or disable text search.
Applied filters, source dates, review warnings and Mock Data labels remain visible.
Mobile source titles and status badges wrap onto separate lines when needed.

## Changed owners

- Backend: `backend/app/schemas/brief_sources.py`,
  `backend/app/services/brief_sources.py`, `backend/app/api/routers/brief_sources.py`.
- Frontend: `frontend/lib/api/brief-sources.ts`,
  `frontend/components/brief-source-inbox.tsx`, new
  `frontend/components/brief-source-library.tsx`, `frontend/app/research.css`.
- Regression coverage: new `backend/tests/test_brief_source_search.py`,
  `frontend/lib/brief-sources.test.ts`, new `frontend/e2e/brief-source-search.spec.ts`.
- Current documentation: handoff, current state, code map and the single limitation
  ledger. This cross-layer file count is required for an API-to-browser workflow;
  no migration, dependency change or financial calculation change was introduced.

## Verification

Full-suite counts live in [Current State](../../../00-current-state.md). Verification
used source-mounted, network-disabled backend tests, the repository's frontend
unit tests and TypeScript, and a separate PostgreSQL/Next.js/Chromium runtime.
The normal credentials and database were not used. All test source data was
explicitly labeled Mock Data; no external AI/provider action occurred.

- Focused and full backend suites pass. Cases include reaching every older source,
  insertion between pages, literal wildcard/markup/SQL text, intersecting filters,
  another owner's records/cursors, authentication, validation, original-body
  exclusion, query/row budgets and absence of writes.
- The full frontend suite and TypeScript pass. The new transport case checks
  encoded filters, cursor metadata, no-store requests and propagated failures.
- Before/after OpenAPI comparison preserves every existing path and schema exactly;
  the search path and two page-response schemas are the only additions.
- `brief-source-search.spec.ts` passes against the real signed login/proxy and
  PostgreSQL API. It covers older records, combined filters, saves outside current
  filters, source inspection, no implicit AI calls, late-response rejection,
  unavailable/empty states and mobile search during company-catalog failure.
- Additional browser checks mount the actual components with isolated response
  fixtures. They cover page traversal, preserved unsaved intake text, source links,
  consent gating, save isolation, delayed success after failure and recovery.
  Desktop and 390-pixel screenshots were inspected; horizontal overflow is checked.
- Fresh disposable PostgreSQL migrations reach q8q8q8q8q8q8 and readiness passes.
  No new migration was needed. Normal services retain their localhost bindings.
- The final standalone frontend image builds and passes signed login, real
  PostgreSQL-backed search and source inspection with desktop/mobile captures.
  Documentation unit/link checks and scoped Git whitespace checks pass.
  The disposable runtime and runner are removed; the verified image is retained.
  Browser reports/captures are under
  `output/playwright/private-source-retrieval-2026-09-30`.

The normal host Git/Python/browser tooling was sandbox-restricted. The existing
Docker Desktop socket supported isolated verification without reading project
environment files. A Git-index comparison and exact pre-edit file copies protected
prior changes; containerized Git subsequently checked the changed paths. No reset,
clean, staging, commit or source deletion was performed.

## Remaining boundary

The [single limitation ledger](../../../agent_capabilities_and_limitations.md)
owns retrieval and research limitations. Source code is verified; the normal local
app has not been redeployed with this change.
