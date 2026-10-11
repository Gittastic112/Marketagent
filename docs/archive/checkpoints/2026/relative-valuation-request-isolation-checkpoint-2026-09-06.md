# Relative Valuation Request Isolation: Next 10

Date: 2026-09-06

## Completed increments

1. Added a reusable latest-request token and deterministic deferred-promise tests.
2. Added a React resource hook with clean loading, error, retry, and cleanup states.
3. Scoped country loading and country-selection initialization to current data.
4. Isolated industry requests by country and removed obsolete options immediately.
5. Reset the entire peer editor and calculation scope when company identity changes.
6. Cleared usable peer evidence during refresh and on refresh failure.
7. Added independent benchmark/peer failure notices, retries, and peer refresh.
8. Invalidated old calculation successes, failures, and loading completion callbacks.
9. Added ready-selection/peer eligibility regressions and validated frontend integration.
10. Reconciled current docs and recorded remaining boundaries in the single ledger.

Implementation is split into frontend state/integration and documentation phases.
No backend formula, API contract, schema, normal database, or source file changed.
No git commits were created; existing user/prior-agent work remains intact.

## Files

- `frontend/lib/latest-request.ts` and `.test.ts`
- `frontend/lib/use-latest-resource.ts`
- `frontend/lib/relative-valuation-selection.ts` and `.test.ts`
- `frontend/components/valuation/relative-valuation-panel.tsx`
- `frontend/lib/frontend-integrity.test.ts`: moved the receipt contract assertion
  to the extracted eligibility utility; retained the panel wiring assertion.
- Current state, handoff, feature register, limitations ledger, and checkpoint index.

## Automated validation

- All 155 frontend tests pass, including 17 new regressions.
- TypeScript passes.
- Next.js 16.2.11 Docker production build passes.
- Backend code unchanged; prior 774-test full and 127-test focused gates are
  carried forward, not represented as new runs.
- Documentation checker: 62 active Markdown files, 313 local links; diff whitespace
  check passes.

## Browser and runtime validation

Used the Playwright CLI skill with a separate tmpfs PostgreSQL Compose project,
test-only credentials, a company/model visibly named Mock Data, and browser-only
intercepted responses. The normal database was never used for fixtures.

- Held the first country's response until the second country's response arrived.
  Confirmed only the second country's industry remained and could enable Run.
- Held a calculation response, changed country, then released it. Its old result
  did not render.
- Simulated a peer-list HTTP 503. Retry appeared and calculation was disabled.
  Removing the simulated failure and retrying restored the genuine empty state.
- Initial harness attempts failed because the fabricated envelope omitted `meta`
  and the CLI sandbox has no global `setTimeout`. Corrected the envelope and
  used explicit promise release; the final checks above passed.
- Inspected `output/playwright/.playwright-cli/page-2026-09-07T00-03-57-664Z.png`
  (UTC timestamp; still September 6 locally). The observed surrounding layout
  issue is recorded in the single limitations ledger, not counted as a visual pass.
- Rebuilt and replaced only the normal frontend container. Its healthcheck and
  auth readiness pass. Backend readiness remains `ready` at `o6o6o6o6o6o6`, with
  no missing tables, columns, or constraints.
- Closed the browser and removed the isolated stack and its disposable fixtures.

## Next task

Correct the DCF-to-relative-valuation input adapter and add explicit input-basis
disclosure. Details and other remaining limitations are maintained only in
[`agent_capabilities_and_limitations.md`](../../../agent_capabilities_and_limitations.md).
