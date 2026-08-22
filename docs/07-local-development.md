# Local Development & Manual Setup Guide

This guide contains everything you need to run the Market Intelligence Engine locally via Docker, configure environments, verify its health, and debug issues.

Since this is a local-first application, you have full control over the environment variables and API integrations.

---

## 1. Environment Configuration (`.env`)

Before starting the app, you must configure your `.env` file in the project root. **Never commit this file.** A template is provided in `.env.example`.

### Required Settings

| Key | Description | Example / Recommended Value |
| :--- | :--- | :--- |
| `DATABASE_URL` | PostgreSQL connection string. | `postgresql+psycopg://marketintel:marketintel_password@postgres:5432/marketintel` |
| `SEC_USER_AGENT` | **CRITICAL**: The SEC EDGAR API requires a declared contact header. General or empty user agents are blocked. | `"MarketIntelligenceApp/0.1 contact: your-email@example.com"` |
| `API_BASE_URL` | Server-side frontend API URL. | `http://127.0.0.1:8000` |
| `NEXTAUTH_SECRET` | Required for stable local sessions. Generate a long random string. | `openssl rand -base64 32` |
| `LOCAL_AUTH_USERNAME` | Local-only sign-in username. | Your chosen local username |
| `LOCAL_AUTH_PASSWORD` | Local-only sign-in password. | A unique local password |

Optional database capacity controls default to:

```text
DATABASE_POOL_SIZE=10
DATABASE_MAX_OVERFLOW=20
DATABASE_POOL_TIMEOUT_SECONDS=10
```

These values bound each backend process to 30 checked-out connections. They are
sized for the current Next.js server-render fan-out. Do not raise them without
checking the PostgreSQL connection budget and measuring the triggering page.

Authentication is a local access-control measure for the currently single-user
setup. It is not a production authentication or authorization design. The app
will reject protected API requests until these three `NEXTAUTH_*`/`LOCAL_AUTH_*`
values are set and the frontend is restarted.

Unsigned frontend page requests redirect to `/auth/signin`. If any required
local auth value is missing, the sign-in page shows a configuration error and
disables submission. API routes are excluded from this optimistic page redirect;
the backend still validates a short-lived, HMAC-signed internal identity
assertion and record ownership for protected data. Next.js validates the JWT and
creates this assertion for server-rendered pages, server actions, and the
same-origin browser API proxy. Raw session cookies are not forwarded to
FastAPI. `GET /api/auth/readiness` returns only the missing variable names and
configured state. It never returns environment values.

### Configure and use the localhost login

The app does not ship with a default username or password. You create both in
the root `.env` file:

```bash
cp .env.example .env
openssl rand -base64 32
```

If `.env` already exists, do not overwrite it. Open the existing file and set:

```text
NEXTAUTH_SECRET=<paste the generated random value>
NEXTAUTH_URL=http://localhost:3000
LOCAL_AUTH_USERNAME=<choose your username>
LOCAL_AUTH_PASSWORD=<choose a unique local password>
```

Do not put these values in `frontend/.env.local`, source files, tests,
documentation, screenshots, chat messages, or commits. Docker Compose reads
the root `.env`. It passes credentials only to the frontend and passes
`NEXTAUTH_SECRET` to both frontend and backend so they can sign and verify
internal identity assertions.

Recreate both application containers so they receive the shared secret:

```bash
python3 scripts/check_local_auth.py
docker compose up -d --force-recreate backend frontend
curl http://localhost:3000/api/auth/readiness
```

The preflight command returns only configured/missing state and exits nonzero
when a required value is absent. It never prints credential values.

### Choose the runtime mode

Normal local use now runs the production-built frontend and a single backend
process. This avoids keeping the Next.js development compiler and Python reload
watcher resident in memory:

```bash
docker compose up --build -d
```

Use the development override only while actively editing code:

```bash
docker compose -f docker-compose.yml -f docker-compose.dev.yml up --build -d
```

The development override retains hot reload and uses named Linux-only volumes
for `node_modules` and `.next`; it does not reinstall npm packages on every
restart. Its frontend heap is capped at 1536 MB. Rebuild the development stack
after changing `package-lock.json`.

PgAdmin is optional and no longer consumes memory during normal use. Start it
only when required:

```bash
docker compose --profile admin up -d pgadmin
```

All services cap local JSON logs at three 10 MB files. Docker image/build cache
can still use disk, so inspect it with `docker system df`; do not run broad prune
commands without reviewing what Docker will remove.

The readiness response must show:

```json
{
  "configured": true,
  "missing": [],
  "mode": "local_single_user",
  "production_ready": false
}
```

Then open `http://localhost:3000/auth/signin` and enter the exact
`LOCAL_AUTH_USERNAME` and `LOCAL_AUTH_PASSWORD` values you chose. A successful
sign-in redirects to the requested app page. NextAuth stores a local JWT session
cookie. Next.js validates it without a recursive HTTP callback, signs the
internal FastAPI identity assertion, and the backend commits the local `users`
row on first protected API use.

To sign out, use the app's sign-out control when present or open
`http://localhost:3000/api/auth/signout`. If credentials change, recreate the
frontend container and sign in again. Existing cookies may no longer validate
after `NEXTAUTH_SECRET` changes.

If sign-in stays disabled:

1. Confirm the three values are non-empty in the root `.env`.
2. Recreate, rather than merely restart, both application containers.
3. Check `docker compose exec frontend printenv NEXTAUTH_URL`.
4. Recheck `/api/auth/readiness`; it intentionally never returns secret values.
5. Inspect `docker compose logs frontend --tail=100`.

If credentials are accepted but the page stays on `Rendering` or `Compiling`,
confirm that you did not accidentally start the development override for normal
use:

1. Run `docker compose ps` and confirm both `backend` and `frontend` are up.
2. Run `curl http://localhost:8000/api/health`.
3. Recreate both containers with
   `docker compose up -d --force-recreate backend frontend`.
4. Inspect `docker compose logs backend --tail=100` and
   `docker compose logs frontend --tail=100`.
5. Confirm dashboard endpoint logs include successful `/daily-brief` and
   `/portfolios` requests. Protected requests no longer call
   `/api/auth/session` from FastAPI.

### Third-Party API Keys

Add these keys to your `.env` file only for providers you are actually testing. Missing keys should surface as not-configured/provider-health states, not fake data.
```text
FRED_API_KEY=
# Supported now: alphavantage (or alpha_vantage) and yfinance_personal.
# yfinance_personal is an explicit unofficial personal-use source.
MARKET_DATA_PROVIDER=alphavantage
ALPHA_VANTAGE_API_KEY=
GEMINI_API_KEY=
AI_DEMO_MODE=false
AI_PRIVACY_DISCLOSURE_VERSION=v1
```

`TIINGO_API_KEY` and `UPSTOX_ANALYTICS_TOKEN` are approved for later batches,
but the current application does not read them. Do not add them yet. Their
placeholders, backend settings, Docker wiring, provider-health checks, and
redaction tests must land with the corresponding adapters.

With `MARKET_DATA_PROVIDER=alphavantage`, a missing `ALPHA_VANTAGE_API_KEY`
returns `PROVIDER_NOT_CONFIGURED`; it does not fall back. For local personal
testing without a key, `MARKET_DATA_PROVIDER=yfinance_personal` is available,
but every result is labeled unofficial and its timestamp/delay limitations are
preserved. FMP is not implemented and is rejected explicitly.

Normal local use does not fall back to mock AI. With no `GEMINI_API_KEY`, AI
actions return `AI_PROVIDER_NOT_CONFIGURED`. Deterministic mock output is
allowed automatically under tests or when `AI_DEMO_MODE=true` is explicitly
set for a demo. Mock records and UI surfaces show `Mock Data`. Provider failure
returns `AI_PROVIDER_FAILED`; it never becomes mock success.

Before each active AI call, the UI lists the data classes that may be sent and
requires acknowledgement of `AI_PRIVACY_DISCLOSURE_VERSION`. Increment the
version when the disclosure meaning changes. Narrative extraction is not run
automatically during ingestion because ingestion has no separate user
acknowledgement.

> [!IMPORTANT]
> **After updating your `.env` file, you must restart your Docker containers** to load the new settings:
> `docker compose down && docker compose up -d`

---

## 2. Running Docker (The Whole Stack)

Ensure Docker Desktop is open and running.

**Start all services** (Frontend, Backend, PostgreSQL, pgAdmin) in the background:
```bash
docker compose up -d
```

**Rebuild after making code or dependency changes:**
```bash
docker compose up --build -d
```

**Completely reset the environment** (Warning: Deletes the database volume):
```bash
docker compose down -v
```
Only use this for disposable local data. If you care about preserving local records, inspect the migration state first.

---

## 3. Database Setup & Migrations

The backend container is configured to automatically run migrations (`alembic upgrade head`) when it starts.

Check the current migration head:
```bash
docker compose exec backend alembic heads
```

The current expected head is `z1z1z1z1z1z1`.

Apply migrations manually:
```bash
docker compose exec backend alembic upgrade head
```

If you need to generate a new migration after modifying `app/models/`:
```bash
docker compose exec backend alembic revision --autogenerate -m "Add new table"
```
*(Note: Always review the generated python file in `backend/alembic/versions` before applying it).*

You can verify the database state by opening **pgAdmin** in your browser at `http://localhost:5050` and logging in with:
- **Email**: `admin@local.com`
- **Password**: `admin_password`

---

## 4. How to Inspect Logs

To view logs for all services in real-time:
```bash
docker compose logs -f
```

To view logs for a specific service (e.g., the backend):
```bash
docker compose logs -f backend
```

---

## 5. Verifying API Health & Connectivity

**1. Check Backend Container Health:**
Open your browser to: `http://localhost:8000/api/health`
You should see an `ApiResponse` envelope whose `data.status` is `ok`.

The legacy health path also exists at `http://localhost:8000/health` for compatibility.

**2. Verify Frontend/Backend Connection:**
If the frontend UI at `http://localhost:3000` shows "Backend not reachable", check that `http://localhost:8000` is accessible from your host machine, and ensure CORS is properly configured in `backend/app/main.py`.

When auth is configured, opening `http://localhost:3000` while signed out should
redirect to `/auth/signin?callbackUrl=%2F`. A configuration error on that page
means the frontend container has not received all three required auth values.
You can inspect the non-secret readiness state directly:

```bash
curl http://localhost:3000/api/auth/readiness
```

Expected fields are `configured`, `missing`, `mode`, and `production_ready`.

### Upload and review a PDF filing

After signing in:

1. Open `/companies` and select a company.
2. Open the company's `Filings` view.
3. In `Upload PDF Filing`, select a text-based PDF up to 40MB, choose the
   document type, add the official source URL when known, and submit it. For a
   report above 500 pages, enter the consolidated statement/note pages in
   `Target pages`, for example `465-470, 542`.
4. Open `Financials` and review every extracted candidate. The parser does not
   auto-approve or auto-promote values.
5. Use `Open evidence` to inspect the original authenticated PDF at the
   extracted page before reviewing or overriding a value.
6. Promote only reviewed/overridden candidates after verifying units, fiscal
   years, and source cells.

The hard limit is 1,000 pages. Full scans stop at 500 pages, and targeted scans
are limited to 75 pages. Scanned-image PDFs, password-protected files, arbitrary
merged layouts, and statements without explicit fiscal-year headers may return
no candidates or a controlled parse error. Investor presentations are stored
as non-annual evidence and must not be used as annual certification input.

### Run authenticated browser workflows

The browser suite uses a disposable Compose project and does not touch the
normal local database. It requires Docker Desktop, configured credentials in
the ignored root `.env`, and Google Chrome on macOS.

From the repository root:

```bash
cd "/Users/mananmaheshwari/Documents/Codex/Market Intelligence App/market-intelligence-md-files copy"
cd frontend
npm run test:e2e
```

Focused commands:

```bash
npm run test:e2e:valuation
npm run test:e2e:pdf
npm run test:e2e:evidence
npm run test:e2e:integrity
npm run test:e2e:accessibility
```

The runner builds a production-mode frontend at `http://127.0.0.1:13000`, a
backend at `http://127.0.0.1:18000`, and a fresh tmpfs PostgreSQL database. It
migrates from base to the current Alembic head, creates only disposable test
records, and removes the `market-intel-e2e` stack and volumes on exit. It does
not print the configured username, password, or session secret.

The focused workflows cover:

- valuation draft save, reset-to-source, refresh, archive/reopen, review, and
  atomic promotion;
- deterministic PDF upload, all candidate reviews/overrides, promotion, 2/2
  normalized trust-ready periods, and zero reconciliation mismatches.
- alert evidence complete/missing states;
- responsive grouped navigation and company tabs, disclosed AI-provider
  failure recovery, and invalid CSV preview with row-level errors.
- semantic names and labels, duplicate IDs, image alternatives, keyboard
  focus, mobile drawer Escape/focus restoration, horizontal overflow, and
  desktop/mobile screenshots for six core routes.

### Back up and restore local data

```bash
./scripts/backup_local.sh
./scripts/drill_backup_restore.sh
```

Restore is destructive and requires the explicit flag:

```bash
./scripts/restore_local.sh backups/<backup-directory> --yes-replace-database
```

Set `BACKUP_PRUNE=true` to opt into retention pruning. These scripts do not
provide off-device storage or encryption by themselves.

### Assess real-source financial certification

The synthetic US/India fixture cannot certify the product. The checked-in
reference manifest uses stable company identity plus official payload/asset
hashes, not local database IDs:

```bash
docker compose exec backend python scripts/certify_financial_histories.py \
  data/certification/aapl-apsez-reference-manifest.json
```

The command exits non-zero unless every selector resolves exactly once and
eligible histories exist for both `US` and `IN`. For another corpus, use the
same portable selector structure with `is_mock: false` and
`source_assertion: "real_primary_source"`; do not commit private manifests.

Data Health runs a separate on-demand audit over current promoted records. It
checks exact locators, unique annual periods, source-versus-stored period ends,
eligible history counts, and certified market coverage. It does not repair data
or replace the manifest command.

The current local AAPL FY2022-FY2025 corpus is already reviewed, promoted, and
reconciled. Do not approve FY2021: it was outside the explicit authorization and
its aggregate debt remains missing. The source hash and result are recorded in
`docs/archive/checkpoints/2026/aapl-real-source-certification-checkpoint-2026-08-01.md`.

Adani Ports company ID `6` now has 51 promoted FY2023-FY2025 evidence rows:
48 reviewed statement facts and three reviewed operating-EBIT calculations.
The three March-ended periods are trust-ready and reconcile 27/27 canonical
metrics exactly:

```text
http://localhost:3000/companies/6/fundamentals
```

The source URLs, values, debt/NCI treatment, 2026-08-02 valuation cutoff, EBIT
method, and certification result are recorded in
`docs/archive/checkpoints/2026/adani-ports-real-source-checkpoint-2026-08-01.md`.

For industry review, open `http://localhost:3000/companies/6/valuation`.
The Revenue-Weighted Industry Mix editor lets each operating segment retain a
business label, Damodaran industry, revenue percentage, as-of date, source
document, and basis note. Weights must total 100%. It displays per-row module
coverage and overall blended-field coverage after save. The prior single
`Packaging & Container` user choice is preserved as a 100% row until actual
segment weights are entered; this is not a claim that the whole company belongs
in that benchmark. The full loaded taxonomy is available. `Advertising` was an
invalid old fallback and must not be restored.

To restage the exact supplied Adani package after a fresh local database:

```bash
docker cp "/Users/mananmaheshwari/Downloads/FY25.pdf" market_intel_backend:/tmp/adani-fy25.pdf
docker cp "/Users/mananmaheshwari/Downloads/FY24.pdf" market_intel_backend:/tmp/adani-fy24.pdf
docker cp "/Users/mananmaheshwari/Downloads/Q1 FY27.pdf" market_intel_backend:/tmp/adani-q1-fy27.pdf

docker compose exec backend python /workspace/backend/scripts/stage_adani_reference_data.py \
  --fy25-pdf /tmp/adani-fy25.pdf \
  --fy24-pdf /tmp/adani-fy24.pdf \
  --q1-fy27-pdf /tmp/adani-q1-fy27.pdf \
  --valuation-cutoff-date 2026-08-01 \
  --apply
```

The staging command verifies the expected SHA-256 hashes and never promotes
Adani candidates.

After explicit review approval, finalize the exact reference set with:

```bash
docker compose exec backend python /workspace/backend/scripts/finalize_adani_reference_data.py \
  --valuation-cutoff-date 2026-08-02 \
  --apply
```

The finalizer is idempotent and fail-closed. It verifies the two annual-report
SHA-256 hashes, the exact 48 metric/value/unit/page tuples, and the absence of
unapproved reviewed candidates. It creates or verifies the three EBIT formula
records, repairs legacy targeted-scan asset page counts from the original PDF
bytes, applies March 31 fiscal dates, preserves source-fact claim types,
normalizes, reconciles, refreshes draft `2` without dropping user edits, and
requires the AAPL/APSEZ two-market certification report to pass.

### Verify the clean release baseline

From the repository root:

```bash
./scripts/verify_release_baseline.sh
```

This uses a separate disposable Compose project. It builds production images,
migrates a fresh PostgreSQL database to the current head, checks health and auth
readiness, runs all backend tests, runs all frontend tests, and runs TypeScript.
The same command is the core GitHub Actions gate in `.github/workflows/ci.yml`.
It uses explicit test-only auth and SEC identity values and removes its volumes
on exit.

The default frontend is a multi-stage standalone Next.js image. It contains only
the traced production server and static output, not the development compiler,
test runner, or host `node_modules`. The opt-in development override masks
`/app/node_modules` and `/app/.next` with named Linux-only volumes. This prevents
a Mac host dependency tree from causing native-module errors such as
`Cannot find module '../lightningcss.linux-arm64-gnu.node'`.

When frontend dependencies change, rebuild the default runtime:

```bash
docker compose up --build -d frontend
```

For development mode, remove only the named frontend dependency volume before
rebuilding it. Do not use `docker compose down -v` unless the local PostgreSQL
database is intentionally disposable.

The US/India normalized-history fixture under
`backend/tests/fixtures/normalized_financial_histories.json` is synthetic
`Mock Data` for automated tests only. Do not import it as company research.

---

## 6. Testing Workflows via CLI

We provide a Python script to seed the database and test live connectivity:

Run the seed script inside the backend container:
```bash
docker compose exec backend python scripts/verify_milestone_a.py --write --rss-feed "https://example.com/feed.xml"
```

**Common CLI Failure Points:**
1. **"Backend health check failed"**: Backend is down. Run `docker compose ps`.
2. **"SEC company lookup failed (403)"**: Missing or invalid `SEC_USER_AGENT` in `.env`.
3. **"RSS feed returned errors"**: URL blocked or DNS issues in Docker. Restart Docker.

## 7. Documentation Map

Before implementing or debugging a feature, read:

- `docs/README.md` for the documentation index.
- `docs/HANDOFF.md` for the latest agent handoff.
- `docs/00-current-state.md` for current implementation state.
- `docs/agent_capabilities_and_limitations.md` for what is trusted, partial, mocked, or unsafe.
- `docs/06-security-threat-model.md` before adding external inputs, AI calls, imports, or provider integrations.

---

## Beginner Rule
If something breaks:
1. Check the Docker logs first (`docker compose logs backend`).
2. Do not run destructive migration commands (like `alembic stamp`) unless you understand the error.
3. Ask the AI: "Explain this error in plain English and identify the smallest likely fix."
