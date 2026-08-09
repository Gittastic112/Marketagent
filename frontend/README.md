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
[`../docs/07-local-development.md`](../docs/07-local-development.md).

## Product Surface

The app includes company setup/research, filing and financial review, evidence,
events, alerts, thesis notes, valuation workflows, portfolios, market/macro
context, research sessions, narratives, search, Data Health, sources, and
settings. Capability status and limitations live in
[`../docs/roadmaps/feature-register.md`](../docs/roadmaps/feature-register.md).

Do not add mock values to make a route appear complete. Components must preserve
loading, empty, error, stale, partial, not-configured, mock, and success states.

## Run

Preferred, from the repository root:

```bash
docker compose up --build -d
```

Open `http://localhost:3000`.

Host development, with the backend already on `127.0.0.1:8000`:

```bash
npm ci
npm run dev
```

## Validate

```bash
npm test
npm run typecheck
npm run build
```

Use Playwright for changed user workflows. A successful build proves compilation,
not live provider behavior or visual correctness.

## Key Locations

| Path | Responsibility |
|---|---|
| `app/` | Routes and server/client composition |
| `app/api/backend/[...path]/route.ts` | Authenticated same-origin backend proxy |
| `components/` | Reusable UI and workflow components |
| `lib/api.ts` | Browser API client and shared contracts |
| `lib/server-api.ts` | Authenticated server-side backend client |
| `lib/auth-options.ts` | Local NextAuth credential configuration |
| `e2e/` | Isolated browser workflows |

See [`../docs/02-architecture.md`](../docs/02-architecture.md) for the full
system boundary.
