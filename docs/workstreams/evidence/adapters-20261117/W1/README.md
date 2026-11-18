# W1 frontend implementation and validation

Date: 2026-11-18. Baseline: `371b58c02cfd2b80429f28dbc13629165b5e392d`. Branch: `work/adapters-ui-20261117`.

## Implemented behavior

| Surface | Change | Integrity boundary |
| --- | --- | --- |
| Valuation memo | Render Markdown headings, GFM tables, lists and code; resolve declared source markers to the existing evidence panel; export the original Markdown with returned artifact identifiers. | Raw HTML and images are omitted. Links allow HTTP(S) or authorized source anchors only. Unknown source markers stay unresolved. Returned model, assumption version, scenario and output mismatches are withheld. |
| Price and FX CSV review | Filter server preview rows by action, record type, problem field and text; inspect 50 rows per page; navigate errors or jump to the original CSV row. | This is the existing price/FX evidence importer, not a transaction importer. Apply retains the original file and server SHA-256. Portfolio identity changes invalidate prior responses. Counts and atomic apply cover the entire file, independent of the visible filter. |
| Research command palette | Cmd/Ctrl+K, keyboard result navigation, tracked company identities, stored-evidence search, explicit external ticker lookup and prefilled company review. | Latest-request guards prevent old search responses from replacing current results. Provider lookup does not create a company. No durable named lists are invented. |
| Research Lab | User-supplied JSON/file inputs for allocation, simulation, return report and peer discovery; actual capability status; saved run history; weights, backend metrics, a lazy-loaded wealth chart and bounded observations. | Native equal weight is accessible without an optional solver. Results remain hypothetical research. The UI does not calculate financial metrics, approve facts or modify holdings. Saved exports use the exact run ID. |
| Source adapters | Explicit SEC annual facts, India filing metadata intake, earnings transcripts, stored-PDF extraction and FRED vintage forms. | Company and document scope use existing identifiers. Source/candidate review remains separate. FMP transcript controls expose only its supported detail level 1. |
| Market and reference adapters | Explicit FMP, Massive and NSE quote/history/action requests; NSE dated observation; Massive reference; OpenFIGI identity candidates; exchange calendars. | Provider choice is visible. Source receipts and raw documents remain inspectable. Full response metadata is preserved, including envelope-only quote freshness warnings and `is_stale`. Corporate actions and identity candidates are not applied automatically. |
| Contract maintenance | Generated request and receipt types for the new three route families. | Committed OpenAPI comes from the integrated backend, not a handwritten duplicate. Runtime parsing and server validation remain authoritative. |

The memo's saved basis and the caller's remount key already existed at baseline. These changes harden rendering, returned-identity checks and download identity. They do **not** claim to repair all outstanding R6 saved-editor, stale-acknowledgement or reconciled-export defects, or the independent R7 thesis/memo contract issues.

The changes span multiple frontend responsibilities because the authorized scope includes memo, importer, search and three adapter families. Existing style tokens, layout components, Recharts and API transport are reused. No wholesale theme redesign or framework replacement is included.

## Generated contract workflow

The source snapshot is `frontend/lib/api/generated/adapters.openapi.json`; generated TypeScript is adjacent at `adapters.ts`. The snapshot currently contains 22 paths and 63 component schemas.

The backend owner supplies the deterministic source via `backend/scripts/export_adapter_contracts.py`. From the repository root, use that script's `--output frontend/lib/api/generated/adapters.openapi.json` when intentionally updating the contract. Its `--check` mode compares the committed snapshot to the actual registered backend routes. It requires the repository's normal test configuration and backend environment; it does not contact providers.

From `frontend/`:

```bash
npm run generate:adapter-types
npm run check:adapter-types
```

`check:adapter-types` regenerates into a temporary file and compares exact contents. `openapi-typescript` is pinned to 7.13.0 as a development dependency. The generator preserves optional fields with server defaults; request objects can omit those defaults. API helpers import the generated types only, so code generation does not add client runtime code. Unrelated existing API contracts and the compatibility facade are unchanged.

## Validation results

| Check | Result | Evidence |
| --- | --- | --- |
| `npm test` | 409 passed, 0 failed | `frontend-tests.txt` |
| `npm run typecheck` | Passed | `typecheck.txt` |
| `npm run check:adapter-types` | Passed | `generated-types.txt` |
| Host `npm run build`, Next 16.4.5, Node 24.22.1 | Passed | `production-build.txt` |
| `npm audit --json` | 0 vulnerabilities | `npm-audit.json` |
| Local Chromium workflow | Blocked before any browser interaction | `browser-blocker.txt` |
| Docker production/browser gate | Not run: Docker is unavailable in this environment | Remaining verification gate |

The utility tests cover source-marker/link policy, returned memo basis and artifact naming, exact-file evidence payloads, preview filtering and row navigation, company identity search, safe destinations, JSON parsing, explicit adapter routes, error field reporting and preservation of envelope-only stale-quote warnings. Existing integrity and boundary checks remain in place.

An independent read-only review compared the new forms, routes, result labels and ownership boundaries against the integrated backend. It caught the dropped market-response metadata before commit; the fix and a regression test are included. This is not a substitute for the blocked browser gate or for actual provider-entitlement tests.

The `vercel:react-best-practices` skill was applied after the TSX changes. The review checked identity reset/unmount cleanup, independent read requests, direct domain imports, native dialog keyboard behavior, bounded rows, stable keys and deferred chart loading. It did not introduce a new theme or a new grid framework.

## Security patch

The first host production build reported a known advisory in Next 16.4.1. A subsequent retry was not treated as a fix. Next was pinned to the smallest compatible patched release, 16.4.5, and the lockfile was updated. There is no separate `eslint-config-next` dependency in this project.

Maintainer advisories used to establish the affected range and patched version:

1. [CVE-2026-119790 / GHSA-mfr8-8qww-v76h](https://github.com/vercel/next.js/security/advisories/GHSA-mfr8-8qww-v76h)
2. [CVE-2026-119351 / GHSA-vc7v-qv4w-wrv8](https://github.com/vercel/next.js/security/advisories/GHSA-vc7v-qv4w-wrv8)

The patched production build and the final dependency audit passed. Existing optional-package platform metadata was preserved during dependency installation.

## Browser fixture and remaining verification

`browser-check.mjs` is an unexecuted workflow check after its launch attempt failed. `fixture-page.tsx` is a temporary harness for the real memo and evidence components. **The harness is not mounted in the committed application. There are no claimed screenshots or browser passes.**

The script uses dummy local credentials and intercepts every backend-proxy request with explicitly labelled Mock Data. The configured backend port is deliberately unused. It does not contact normal application data or external providers. Intended checks include memo rendering and delayed responses, exact-file import navigation/apply, palette search races and keyboard controls, native allocation, simulation, saved exports, adapter receipts, desktop/mobile overflow and axe accessibility. These checks remain pending until a permitted Chromium environment is available.

To rerun from the repository root in a disposable checkout, first mount the harness:

```bash
mkdir -p frontend/app/w1-ui-check
cp docs/workstreams/evidence/adapters-20261117/W1/fixture-page.tsx frontend/app/w1-ui-check/page.tsx
```

In one terminal, from `frontend/`, run:

```bash
env NEXTAUTH_SECRET=mock-data-w1-local-verification-only \
  LOCAL_AUTH_USERNAME=w1-mock-data \
  LOCAL_AUTH_PASSWORD=mock-data-local-check \
  NEXTAUTH_URL=http://127.0.0.1:13117 \
  API_BASE_URL=http://127.0.0.1:19817 \
  NEXT_TELEMETRY_DISABLED=1 \
  npm run dev -- --hostname 127.0.0.1 --port 13117
```

In another terminal, from the repository root:

```bash
node docs/workstreams/evidence/adapters-20261117/W1/browser-check.mjs
```

The default executable is `/usr/bin/chromium`; set `PLAYWRIGHT_CHROMIUM_EXECUTABLE` to an installed compatible Chromium path when necessary. Results, if the complete script passes, are written beneath the evidence folder's `browser-output/`. Stop the dev server and remove only the temporary `frontend/app/w1-ui-check/page.tsx` harness after the run. If its stale generated route declaration remains under `.next/dev/types`, clear that generated development cache before a production build.

## Upstream reuse and scope

Direct dependencies added: `react-markdown` 10.1.0, `remark-gfm` 4.0.1 and development-only `openapi-typescript` 7.13.0, all MIT licensed. Existing Next was patched to 16.4.5. Palette and review-grid behavior was implemented in this repository using its current contracts and components; no application source was copied from OpenStock, Ghostfolio or Wealthfolio. Inspiration and actual dependency reuse should remain distinct in central attribution.
