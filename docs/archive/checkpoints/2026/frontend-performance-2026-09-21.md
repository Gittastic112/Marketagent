# Frontend and Read-Path Performance

Date: 2026-09-21. Current limits remain in the [single ledger](../../../agent_capabilities_and_limitations.md).

## Scope and structural findings

The user requested remaining product repairs, a cleaner interface and faster
loading. The existing dirty worktree, untracked files, source documents and saved
research were preserved. This is a cross-cutting change across persistence
loading, workflow queries, server-page composition, shared presentation, tests and
current documentation. More than ten files are needed because fixing the query
graph alone does not remove unnecessary page work or protect the changed UI.
No dependency, database migration, external provider call or public deployment
was introduced by this batch.

- Company/portfolio/source/run relationships automatically loaded large related
  graphs, including histories unrelated to the requested response. Common reads
  now use explicit workflow loading. Company response tags remain eager; tests
  cover detached callers that need to load relationships before closing sessions.
- Portfolio valuation materialized full price histories to select one latest row.
  A SQL window now selects one eligible row per security, with deterministic
  date/ID ordering and separate identities for unlinked symbols.
- Provider health materialized historical runs. Windowed latest-status selection
  and SQL aggregates preserve last success, all-time counts and consecutive
  failures. Explicit AI demo mode cannot be mistaken for a working real adapter.
- Portfolio detail performed nearly every analysis/setup request before returning
  its complete page. It now resolves owned identity and streams only the selected
  Overview, Performance & risk, Activity or Data & setup server view. Old date-only
  URLs retain the performance view; errors are not disguised as missing records.
- Company list rendered every edit form. Only the selected form now mounts;
  search/market filters and a compact watchlist make the main task clearer.
- Dashboard uses the existing consolidated endpoint with a visible stored-value
  date, correct currency and portfolio name/basis. Dead analytics rendering and
  placeholder drift metrics were removed. Failed reads do not become zero values.
- Data Health presentation helpers have a separate owner; request orchestration
  remains in its page. The code map explains the new entry points.

## Interface and integrity repairs

Shared page/card/button styling, typography, spacing, contrast and navigation
were refined. Tables keep words intact and scroll within bounded panels rather
than breaking headings into individual letters. Main dashboard, companies,
valuation hub and portfolio views were inspected on desktop/mobile.

Mobile navigation makes background content inert, locks page scrolling, contains
forward/backward keyboard focus and restores the opener on Escape. An inherited
visibility transition initially prevented focus from reaching links; limiting
link/button transitions and checking actual visibility corrected it. Company tag
controls now have explicit accessible names. Warning labels use readable colors.

Advanced valuation refresh resets the versioned form, not its surrounding
workspace. The success notice and selected section survive a save; changed inputs
are confirmed against the backend. Financial formulas remain backend-owned.

Risk comparison derives private DCF context from the persisted portfolio owner.
It exposes latest price date/age and flags prices older than five calendar days
as partial, withholding the current DCF price gap. Historical risk remains visible
with warnings. An unlinked ticker cannot silently consume a linked security's
price, and a latest Mock Data row remains classified as mock outside the lookback.

## Measured normal-runtime effect

Read-only measurements used the same preserved local database. Backend timing
uses an authenticated TestClient with SQL statement counting; frontend timing
uses an actual authenticated request to the running standalone server and reads
the full response. Credentials/cookies remain in container memory and are not
printed. These are small local samples, not load testing or browser paint/hydration
metrics. The second post-update sample is recorded to avoid claiming a fixed speed.

| Backend read | Queries before | Queries after | Before ms | After ms |
|---|---:|---:|---:|---:|
| Companies | 26 | 3 | 631 | 20.7 |
| Company detail | 14 | 3 | 16 | 6.9 |
| Dashboard overview | 9 | 9 | 25 | 29.7 |
| Portfolios | 35 | 2 | 549 | 4.8 |
| Holdings | 38 | 2 | 289 | 6.7 |
| Portfolio valuation | 168 | 11 | 1,129 | 49.0 |
| Portfolio risk comparison | 204 | 12 | 1,480 | 44.7 |
| Provider health | 30 | 5 | 464 | 23.5 |

| Full server page response | Before ms | After, first ms | After, repeat ms |
|---|---:|---:|---:|
| Dashboard | 97 | 485 | 137 |
| Companies | 890 | 65 | 59 |
| Portfolios | 2,581 | 91 | 87 |
| Portfolio overview | 8,897 | 45 | 127 |
| Data Health | 3,501 | 193 | 152 |
| Valuation hub | 3,213 | 28 | 47 |
| Portfolio performance view | Not separately measured | 110 | 137 |
| Portfolio setup view | Not separately measured | 129 | 111 |

The portfolio overview response fell from 158,460 to 34,594 bytes; company list
from 245,698 to 78,114 bytes. Dashboard did not become faster in these samples:
its consolidated query was already small and the first request includes startup.
The substantial improvement is in the previously expensive company/portfolio/
provider paths. No cache hides unavailable responses or crosses owner boundaries.

## Verification and preservation

- The full backend suite, frontend utility suite, TypeScript and production builds
  passed. Exact current counts and the final browser scope belong in
  [Current State](../../../00-current-state.md).
- Query-budget tests also verify bounded ORM price/run materialization, not just
  response timing. Regression tests cover historical successes behind many failed
  runs, demo-mode truth, private owner context and stale price-gap suppression.
- Disposable valuation model 3 saved a second version with capex 120,
  depreciation 80 and buybacks 15. The page retained the success notice and showed
  the saved capex after refresh. This is Mock Data workflow evidence, not issuer
  financial certification; the normal database was not used for that write.
- Final-source desktop/mobile audit covered 28 routes at 1440px/390px. All 56
  returned 200 without page overflow, duplicate IDs, unnamed buttons/links or
  unlabelled visible fields. It includes saved valuation, company fundamentals and
  Admin, but is a sanity check, not full accessibility or every-state certification.
  Screenshots caught unreadable squeezed tables that overflow-only checks missed;
  the shared wrapping rule and company-column grouping were then corrected.
- Keyboard checks confirmed initial menu focus, backward/forward wrapping,
  Escape/opener focus, background inertness and scroll-lock cleanup. The portfolio
  period form retained its selected view. Company filtering produced one row and
  selected editing mounted exactly one form. The final browser error log was empty.
  Initial audit duplicates were temporary
  streaming markup; settled-page checks found none. CLI-only timing/selector
  failures were investigated separately from application failures.
- Final normal backend/frontend/scheduler deployment preserves the database and
  localhost bindings. All 107 table counts matched the fresh pre-update backup
  `backups/20260921T230055Z-market-intelligence`; migration head remains
  p7p7p7p7p7p7. The previous portfolio backup has independent restore proof; this
  batch checked the new backup's checksums/inventory and live count preservation,
  not off-device or nonempty-binary-asset recovery.
- Documentation, secret, project-workflow and whitespace gates passed. The
  task-owned `market-intel-polish-e2e` containers and tmpfs Mock Data database were
  removed, and the `polish` browser session closed. Fixtures can recreate the test
  data; normal containers, backups and generated evidence were retained.

Artifacts are under `output/playwright/polish-2026-09-21`. They include read-only
measurement scripts/results, route audits and screenshots. They are generated
verification artifacts, not a new application workflow or a source of credentials.

The ledger retains historical transaction replay, issuer/security separation,
reviewed financial/India coverage, optional Sheets integration, sensitivity/fiscal
anchoring, deeper workflow tests and public-deployment restrictions. This batch
does not claim that all remaining product work or every visual state is complete.
