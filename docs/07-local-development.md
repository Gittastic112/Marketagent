# Local Development

Reviewed against checked-in configuration and installed runtime: 2026-11-07.

This guide owns setup and troubleshooting. The [runbook](08-execution-runbook.md)
owns test, build, migration and operational commands. Historical company IDs and
certification fixtures do not establish the contents of your normal database.

## First-time configuration

Use Docker Desktop with Compose. From the repository root, create the ignored
configuration only if it does not already exist:

```bash
cp -n .env.example .env
```

Edit it locally. Never put credentials in chat, screenshots, logs or tracked
files. There is no default application login. Set unique LOCAL_AUTH_USERNAME and
LOCAL_AUTH_PASSWORD values and generate a long random NEXTAUTH_SECRET locally.
NEXTAUTH_URL defaults to http://localhost:3000. Set a real SEC_USER_AGENT contact
identity before live SEC access.
Normal Compose also requires a private POSTGRES_PASSWORD. Use at least 32 random
URL-safe characters (letters, digits, `_` and `-`) because it forms part of the
database connection URL. Existing databases need the coordinated rotation in the
[runbook](08-execution-runbook.md#rotate-the-local-database-password); changing a
container variable alone does not change the persisted database role password.

| Setting | Boundary |
|---|---|
| NEXTAUTH_SECRET | Shared frontend/backend local identity secret; server-only |
| LOCAL_AUTH_USERNAME / LOCAL_AUTH_PASSWORD | Frontend local login only |
| API_BASE_URL | Host Next.js uses http://127.0.0.1:8000; Compose fixes http://backend:8000 |
| NEXT_PUBLIC_BROWSER_API_BASE_URL | Same-origin /api/backend, never credentials |
| DATABASE_URL | Host template uses localhost; Compose fixes the postgres service URL |
| POSTGRES_PASSWORD | Required by normal Compose for PostgreSQL and all database clients; no development fallback |
| PGADMIN_DEFAULT_PASSWORD | Optional disabled admin service only; no default password. Keep it unset and the service stopped until needed |
| Provider keys | Optional, server-only; missing configuration must remain visible |
| GEMINI_API_KEY / GEMINI_MODEL | Gemini key and accessible model ID, backend-only; verify with the runbook's explicit fixed-prompt probe |

Compose passes only settings explicitly listed in its environment blocks.
Adding a root .env variable does not automatically inject it into containers.
Database pool overrides, AI_DEMO_MODE and AI_PRIVACY_DISCLOSURE_VERSION are not
forwarded by normal Compose; backend defaults apply unless an appropriate
override explicitly configures them. Check [settings](../backend/app/core/config.py)
and [Compose](../docker-compose.yml) before assuming a value took effect.

Host Next.js development runs from frontend with Node 24 and npm ci. It does
not automatically load the repository-root .env. Supply required settings in
your local process environment without exposing them. Conversely,
frontend/.env.local does not configure Docker services.

## Start and sign in

For the existing November 7 installation, select its verified runtime override
using [the runbook](08-execution-runbook.md#select-the-installed-local-stack).
It identifies the active services, original database volume and patched images;
retained rollback containers belong to the former project. The commands below
are for a first-time installation without that existing runtime.

Startup changes the normal runtime and automatically attempts database migration.
Run it only when starting/deploying the app is intended:

```bash
python3 scripts/check_local_auth.py
docker compose up --build -d
```

Open http://localhost:3000/auth/signin. Preflight and /api/auth/readiness expose
configuration state, not secrets. After changing the shared secret, recreate
both backend and frontend; restarting does not reload Compose environment.
For frontend-only credential changes, recreate frontend and sign in again.
For Gemini key/model changes, recreate backend to load the new environment.
See the runbook for runtime and provider-probe commands.

Next.js validates the session and signs internal identity assertions. Raw
session cookies are not forwarded to FastAPI. Local sign-in is not production
identity. Companies and source catalogs are shared authenticated records;
private resource ownership is a separate boundary, not complete tenant isolation.

Browser-proxy writes require an Origin matching the configured local site; direct
scripts should use the documented backend authentication instead of spoofing browser
identity. Login attempts are bounded per process. Generic OAuth token storage is
disabled pending an owned provider-specific design. Normal backend/workers run as
an unprivileged user and mount benchmark data read-only. Keep `.env` readable only
by its owner. Do not weaken Docker socket permissions to resolve startup issues.

## Runtime choices and safety

- Normal services: production frontend, backend and persistent PostgreSQL.
- Hot reload: add docker-compose.dev.yml; backend watches backend/app only and
  runtime data stays read-only. The dev frontend uses a 2 GiB memory limit for its
  1.5 GiB heap. Rebuild after dependency changes.
- pgAdmin: optional admin profile, 512 MiB limit, no automatic restart. Stop it
  when administration is finished; it is not required for normal application use.
- Daily Brief worker: optional automation profile, deterministic generation,
  not autonomous AI or provider ingestion.
- Valuation source worker: same optional profile, separate process; explicitly
  enabled SEC/FRED/price refreshes update drafts, not reviewed facts or saved models.
- Browser tests: disposable project, database and ports via the runbook.
  Never point fixture writers at the normal database.

Only backend startup applies migrations. Both workers wait for its healthy
readiness check instead of applying migrations independently. Runtime images
exclude pytest/backend fixtures; local test dependencies are in
backend/requirements-test.txt and the test Compose definitions choose that target.

Normal and E2E Compose definitions bind published ports to 127.0.0.1. Recreate
existing services to apply changed bindings, then inspect `docker compose ps`;
restarting old containers is not enough. The normal runtime was recreated and its
localhost-only bindings verified on September 21. Checked-in database/admin
password defaults have been removed; previously running containers retain their
old configuration until coordinated rotation/recreation. Public deployment is not authorized.

Do not remove volumes, stamp migrations or prune Docker storage to hide errors.
Inspect exact targets and obtain explicit data-loss authorization before
destructive operations. The [schema map](03-database-schema.md) owns migration
head guidance. Backups/restores have separate runbook scripts; local backup
alone does not establish off-device recovery.

If macOS permits ordinary file writes but rejects renaming a completed backup
directory, use the current format-3 backup script. It publishes a checked `COMPLETE`
file inside the folder instead. Restore validates the marker and all checksums;
do not rename an old `.partial` folder or create the marker by hand. The October 12
normal backup and disposable restore passed without changing macOS permissions.

The verifier must also wait for its actual `proof` database over TCP. A temporary
PostgreSQL initialization server can answer `pg_isready` before that database
exists. The backup script now requires a successful bounded query before restore;
failed startup retains an incomplete backup and removes only its own verifier.

## Providers, uploads and reference data

Provider availability depends on the adapter, configuration and stored evidence,
not a placeholder key. See [data sources](04-data-sources-and-ingestion.md) and
[security](06-security-threat-model.md) for ingestion and external-AI boundaries.

Use the company filing/financial workflow for reviewable financial candidates,
or the Daily Brief private inbox for pasted-text/PDF research triage. Saving an
inbox source is local; selecting Scan explicitly sends its disclosed text to AI.
It does not transmit stored portfolio/thesis/model values. Review units,
currency, period, evidence locator and candidates before promotion. Mock Data
fixtures are not company research. Historical AAPL/APSEZ certification proves
supported reference paths, not normal database contents or authorization to
approve new facts. Database IDs are not portable identities.

Source-specific staging/finalization scripts may write and promote data.
Inspect inputs and obtain the required review authorization first; they are not
setup prerequisites. The [previous setup guide](archive/assessments/local-development-before-doc-audit-2026-09-19.md)
is retained as historical evidence only.

## Troubleshooting

| Symptom | First check |
|---|---|
| Docker unavailable | Desktop, selected context and socket permissions; never chmod a socket to 666 |
| Sign-in disabled | Auth readiness missing-variable names and container recreation |
| Backend unreachable | Service status and sanitized logs; liveness is not readiness |
| Migration failure | Current revision versus intact chain; stop on missing revisions |
| Provider failure | Safe Processing Run error, configuration, access, timeout and DNS evidence |
| Gemini model unavailable | A working key can still receive a model-not-found response; choose an accessible GEMINI_MODEL, recreate backend and rerun the fixed-prompt probe |
| Native frontend build failure | Supported Docker build gate; do not alter lockfiles blindly |
| Tests use old code | Use source-mounted unit-test Compose or a fresh browser-test image with recorded source identity |
| Browser tests slow under Docker Desktop | Finish other validation jobs first; inspect CPU/memory pressure and shared-folder overhead. Copy browser tests/artifacts into the runner during execution and retain failed timing evidence |

A failed fetch is unavailable, not successful stale data. A previous stored
observation may separately be old. Never replace failure with mock success.
