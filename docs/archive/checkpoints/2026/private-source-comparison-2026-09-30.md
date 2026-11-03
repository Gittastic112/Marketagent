# Private-source input comparison

Date: 2026-09-30 (New York). This is delivery evidence, not an execution queue.

## Delivered boundary

Daily Brief links to `/daily-brief/triage`, a company-scoped, read-only comparison
of the newest 50 active private sources. It groups stored AI suggestions by the
14 supported valuation inputs, with exact passages, source dates, model/prompt/
input hashes, review status and explicit coverage exclusions. Findings with no
mapped input remain visible. Source records and exact text copies are not votes
or independent corroboration.

Opposing increase/decrease suggestions across distinct content produce inspection
flags, not verified contradictions. Same-content disagreement is distinguished.
Mock Data is opt-in and compared only with other Mock Data. Rejected,
revision-required, failed, blocked, malformed or wrongly linked outputs are
excluded. Pending interpretation stays pending. No numerical input, model, AI
review status or source content is changed by comparison.

The service checks stored exact-span receipts against constrained output and
immutable-source metadata. It does not reread PDF bytes or recertify semantics.
Three queries bound reads; source bodies and published display JSON stay deferred.
Grouped references reuse one copy of each source finding. URLs are rebuilt from
the known field catalog. The browser uses request-scope isolation and clears old
evidence on a failure or company change.

Draft links enter the existing workspace, which may initialize a review-required
draft when absent. They do not apply comparison suggestions or create a saved
valuation. Browser checks verified the target input is visible and focused.

## Verification

- Backend: 1,245 passed, including 27 new comparison regressions. Five existing
  upstream deprecation warnings remain. Network-disabled, isolated test database.
- Frontend: 228 passed and TypeScript passed. Production backend, frontend and
  worker images built; final mobile-layout correction rebuilt and checked.
- API: 277 paths and 498 schemas. One additive GET; no existing wire contract or
  database migration changed. Schema head remains `r9r9r9r9r9r9`.
- Static: 23 documentation/security/localhost/backup-workflow checks, secret
  scan, project-workflow validation and Git whitespace checks passed.
- Disposable PostgreSQL and signed browser: Mock Data defaults, source exclusions,
  input/opposition filters, empty company, delayed old-company failure isolation,
  current 503 clearing/retry, 50-of-52 coverage warning, source/finding navigation,
  draft-field focus, and desktop/mobile layouts passed. No external AI requested.
- Visual inspection caught and corrected a cramped mobile heading and accordion
  summaries. Final 1440px and 390px layouts were inspected with no page overflow.
- Browser-control corrections: quoted a URL containing `?` for the shell; waited
  for a held simulated response before unrouting it. These were test-control
  issues, not suppressed application failures. Expected simulated 503s account
  for the recorded browser resource errors.
- Normal existing AAPL source: five non-mock pending-review findings mapped to
  five inputs, with no inferred cross-source opposition. One local service read
  took 66 ms; that is not a load-test or browser-interactivity guarantee. No new
  Gemini request or interpretation-quality certification occurred.
- All 108 normal table counts and row fingerprints, including migration metadata,
  were unchanged after deployment and the AAPL read. One source, two AI outputs,
  two models, four assumption sets, two holdings, three transactions and eleven
  drafts remained. No new backup/restore was needed for this read-only addition;
  the previously verified backup was retained.
- Normal backend/frontend are deployed and healthy on localhost. PostgreSQL and
  the two existing workers were not recreated. The exact disposable project
  `market-intel-source-triage`, its Mock Data and named browser session were removed.

## Change owners

- Backend: `schemas/brief_triage.py`, `services/brief_source_triage.py`, the existing
  `brief_sources` router, and `test_brief_source_triage.py`.
- Frontend: `lib/api/brief-triage.ts`, `components/brief-source-triage.tsx`, the new
  comparison page, inbox/detail/finding links, scoped research CSS and unit tests.
- Documentation: current state, handoff, architecture, source flow, route/code
  maps, feature register, roadmap and the single limitation ledger.

The next bounded research workstream is persisted analyst dispositions tied to
the compared evidence, with stale-review safeguards. It must not silently turn
direction flags into facts or apply assumptions. Broader scope stays in the ledger.

Ignored screenshots, browser logs and disposable verification helpers live in
`output/playwright/source-triage-2026-09-30/`. Current boundaries and remaining
work live in [the handoff](../../../HANDOFF.md) and
[the single limitation ledger](../../../agent_capabilities_and_limitations.md).
