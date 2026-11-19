# Frontend

The frontend is a Next.js 16 App Router application for the local Market
Intelligence Engine. It is a research workspace, not a minimal dashboard.

## Runtime Boundaries

- Server-rendered requests use `API_BASE_URL`.
- Browser requests use the same-origin `/api/backend` proxy configured by
  `NEXT_PUBLIC_BROWSER_API_BASE_URL`.
- NextAuth local credentials protect pages and API proxy requests.
- The frontend signs short-lived internal identity assertions; it does not expose
  backend secrets or forward raw session cookies to FastAPI.
- Debug logs are disabled unless `NEXT_PUBLIC_DEBUG_LOGS=true`.

Required local auth settings are documented in
[`../docs/local-development.md`](../docs/local-development.md).

## Product Surface

The app includes company setup/research, filing and financial review, evidence,
events, alerts, thesis notes, valuation workflows, portfolios, market/macro
context, research sessions, narratives, search, Data Health, sources, and
settings. Daily Brief includes private text/PDF intake with explicit AI scans;
company/portfolio research cards retain filing sources and Comps opens the
reviewed-peer workspace. The [company price chart](components/company-price-chart.tsx) shows backend-supplied moves, dated sources and private thesis notes. See the [chart workflow](../docs/user-guide.md#inspect-a-price-move-and-pin-a-thesis-note) and [browser regression](e2e/price-timeline.spec.ts).
Capability status and limitations live in
[`../docs/roadmaps/feature-register.md`](../docs/roadmaps/feature-register.md).

Do not add mock values to make a route appear complete. Components must preserve
loading, empty, error, stale, partial, not-configured, mock, and success states.

## Run

For an existing installation, use the selected project and runtime override in
[Operations](../docs/operations.md#select-the-installed-local-stack). Frontend
changes require a production build and replacement of the frontend service;
restarting its existing container does not install changed source. Follow the
[frontend-only update](../docs/operations.md#update-only-the-frontend) procedure for presentation-only changes. The combined adapter release also updates the backend and follows the [release checklist](../docs/roadmaps/ui-adapter-worklist.md#release-checklist).
For a new installation, use [Local setup](../docs/local-development.md#start-and-sign-in).

Open `http://localhost:3000`.

Host development, from frontend, with the backend already on `127.0.0.1:8000`
and required auth/API settings in the process environment. Host Next.js does
not automatically load the repository-root .env:

```bash
npm ci
npm run dev
```

## Validate

From frontend:

```bash
npm test
npm run typecheck
```

Use the [runbook](../docs/execution-runbook.md) for the supported Docker
production-build gate and isolated browser runner. Use Playwright for changed user workflows. A successful build proves compilation,
not live provider behavior or visual correctness.

## Geist presentation

Bundled Geist fonts, neutral light/dark tokens, compact navigation and controls
are owned by the [style map](styles/README.md). The sidebar stores its display
preference in localStorage. Cmd/Ctrl+K opens company and evidence search. The sidebar links to the full evidence-search page.
The [UI notes](../docs/geist-ui.md) explain the prototype-to-application scope,
route behavior and visual checks. The [adapter worklist](../docs/roadmaps/ui-adapter-worklist.md) covers the combined release. The
[current state](../docs/current-state.md#dated-validation) records verification;
source availability does not mean the new UI is installed.

## Key Locations

| Path | Responsibility |
|---|---|
| `app/` | Routes and server/client composition |
| `app/api/backend/[...path]/route.ts` | Authenticated same-origin backend proxy |
| `components/` | Reusable UI and workflow components |
| `components/portfolio/` | Selected server-owned Overview, Performance, Activity and Setup views; expensive reads run only for the selected tab |
| `components/data-health/health-ui.tsx` | Operational-health presentation helpers |
| `components/brief-source-inbox.tsx`, `components/brief-source-findings.tsx` | Private intake, disclosed scan and source-linked valuation review |
| `components/company-research-cards.tsx` | Bounded company identity/business context for company and portfolio views |
| [Style map](styles/README.md), `app/globals.css`, `components/page.tsx`, `components/sidebar.tsx` | Ordered style modules, page primitives, responsive navigation and keyboard focus containment |
| `lib/api.ts` | Compatibility exports only |
| `lib/api/<domain>.ts` | Domain contracts and browser endpoint helpers |
| `lib/api/transport.ts` | HTTP, multipart, binary, and response parsing |
| `lib/api/contract.ts` | Shared envelope types and error identity, no environment reads |
| `lib/server-api.ts` | Authenticated server-side backend client |
| `lib/auth-options.ts` | Local NextAuth credential configuration |
| `e2e/` | Isolated browser workflows |

See [`../docs/architecture.md`](../docs/architecture.md) for the full
system boundary.

Use the [code map](../docs/code-map.md) to find the owner of a change. New domain
code imports transport directly and uses type-only cross-domain references.
Server code imports the shared contract and server client, never browser helpers.
Existing callers can keep using lib/api.ts while being migrated incrementally.
