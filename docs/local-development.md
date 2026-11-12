# Local development

First-time setup and troubleshooting. [Execution runbook](execution-runbook.md)
owns development checks; [Operations](operations.md) owns changes to an existing
installation. Commands below run from the repository root.

## First-time configuration

Install Docker with Compose. Create local configuration only if it is absent:

~~~bash
cp -n .env.example .env
~~~

Edit it privately. There is no default application login. Never commit credentials
or paste them into chat, screenshots, or tracked reports.

| Setting | Purpose |
|---|---|
| LOCAL_AUTH_USERNAME / LOCAL_AUTH_PASSWORD | Unique local application login |
| NEXTAUTH_SECRET | Long random shared frontend/backend signing secret; server-only |
| NEXTAUTH_URL | Local application URL, normally http://localhost:3000 |
| POSTGRES_PASSWORD | Required private database password; at least 32 random URL-safe letters, digits, underscores, or hyphens |
| SEC_USER_AGENT | Real contact identity required before live SEC requests |
| Provider keys | Optional server-only settings for features you explicitly enable |
| GEMINI_API_KEY / GEMINI_MODEL | Optional Gemini key and accessible model ID |
| PGADMIN_DEFAULT_PASSWORD | Optional administration service only; leave disabled until needed |

For an existing database, changing POSTGRES_PASSWORD in a file does not change
the database role. Follow the coordinated
[rotation procedure](operations.md#rotate-the-local-database-password).

Compose injects only variables listed in its environment blocks. Adding a root
environment variable does not automatically configure a container. Compare
[Compose](../docker-compose.yml) and [backend settings](../backend/app/core/config.py)
before assuming an override applies. No provider key is needed merely to inspect
an empty local workspace.

## Start and sign in

These commands are for a new installation. Startup applies migrations:

~~~bash
docker compose up --build -d
docker compose ps
curl --fail http://localhost:8000/api/readiness
~~~

Open [the sign-in page](http://localhost:3000/auth/signin).
The database begins without the developer's private research and portfolio.
Add only the company/source scope you intend to review. Missing provider
configuration should remain visible, not replaced with example facts.

Existing installations use their verified
[runtime override](operations.md#select-the-installed-local-stack).
Recreate affected clients after changing settings; restart alone does not reload
Compose environment values. Changing the shared signing secret requires both
backend and frontend recreation and a new sign-in.

## Runtime choices

| Mode | Configuration and boundary |
|---|---|
| Normal local app | Production frontend/backend and persistent PostgreSQL in docker-compose.yml |
| Hot reload | Add docker-compose.dev.yml; watches source and keeps runtime reference mounts read-only |
| Daily Brief/source workers | Opt-in automation profile; separate deterministic brief and draft-refresh workers |
| Database administration | Opt-in admin profile; pgAdmin is not required for normal use |
| Tests and browser checks | Isolated definitions in the runbook; never point fixture writers at normal data |

Only backend startup runs migrations. Workers wait for backend readiness.
Published ports bind to 127.0.0.1; inspect actual running bindings after recreation.
Local sign-in and resource ownership do not establish public-deployment security.

## Editor and agent settings

Open the repository root in your editor. [pyproject.toml](../pyproject.toml) owns
the shared Python import path for Pyright/Pylance and pytest. Optional personal
VS Code preferences belong in the ignored .vscode directory; do not repeat the
project import-path settings there. No editor-specific folder is required.

The committed [.codex/config.toml](../.codex/config.toml) contains portable
project defaults and environment-file protections. Machine-specific paths,
network choices, and local permission overrides stay local. Review that diff
separately before committing; do not publish or silently discard local overrides.

## Host frontend development

Use Node 24 and the checked-in npm lockfile. Host Next.js runs from frontend and
does not automatically load the root environment file. Supply settings privately:

- API_BASE_URL: http://127.0.0.1:8000 for the host; Compose uses http://backend:8000.
- NEXT_PUBLIC_BROWSER_API_BASE_URL: the same-origin /api/backend proxy.
- NEXTAUTH_URL, NEXTAUTH_SECRET, LOCAL_AUTH_USERNAME, and LOCAL_AUTH_PASSWORD.

From frontend, run `npm ci` and `npm run dev` after starting the backend.
Frontend-local environment files do not configure Docker services.
Use the supported Docker production-build gate in the runbook.

## Providers and source review

[Data sources](data-sources.md) describes adapters and freshness.
Public filings and private text/PDF intake remain untrusted inputs. Review
currency, units, period, source identity, and candidate scope before promotion.
Selecting an external AI scan requires its disclosed scope and current permission.
Ordinary intake does not authorize transmission of private app data.

Source-staging, finalization, and seeding scripts are not setup prerequisites.
Historical reference certifications and database IDs are not portable live data.

## Troubleshooting

| Symptom | First check |
|---|---|
| Docker unavailable | Docker Desktop, selected context, and socket access; do not weaken socket permissions |
| Sign-in unavailable | /api/auth/readiness missing-variable names and container recreation |
| Backend unavailable | Service status and sanitized logs; liveness does not prove database readiness |
| Migration failure | Current revision against the intact chain; stop on missing revisions |
| Provider failure | Configuration, permitted access, and the sanitized Processing Run |
| Backup incomplete | Follow [Operations](operations.md); never forge a completion marker or restore over normal data to test |

Never remove database volumes, stamp migrations, reset data, or prune unknown
storage to hide a failure. Preserve backups and rollback images.
