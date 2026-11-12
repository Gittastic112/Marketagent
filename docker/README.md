# Docker and Compose

Docker packages the app and its dependencies. Compose selects which services run
together. For a first installation, use the normal app definition and follow
[local setup](../docs/local-development.md). Most users need only that file.

## Which file to use

| File at the repository root | Purpose | How it is used |
|---|---|---|
| [docker-compose.yml](../docker-compose.yml) | Normal local app: frontend, backend, persistent PostgreSQL | Default for docker compose; preserves the user database |
| [docker-compose.dev.yml](../docker-compose.dev.yml) | Source editing with hot reload | Overlay combined with the normal app definition |
| [docker-compose.test.yml](../docker-compose.test.yml) | Backend tests with disposable SQLite | Standalone; network disabled and source mounts read-only |
| [docker-compose.tools.yml](../docker-compose.tools.yml) | Repository checks and recovery-script fixtures | Standalone; network disabled, no Docker socket or normal database |
| [docker-compose.e2e.yml](../docker-compose.e2e.yml) | Browser, integration, and release verification | Standalone disposable PostgreSQL/backend/frontend project |
| [docker-compose.recovery.yml](../docker-compose.recovery.yml) | Backup and restore rehearsal | Standalone disposable PostgreSQL/backend project |

Only the dev file is an overlay. Do not merge the four isolated test definitions
with the normal app. The normal definition also has optional automation workers
and an optional admin profile for pgAdmin; neither is required to browse the app.

The files stay at the root because scripts and relative build/mount paths use
those locations. Separate definitions keep test fixtures away from normal data.
The [execution runbook](../docs/execution-runbook.md#choose-the-right-environment)
owns exact development and test commands. [Operations](../docs/operations.md)
owns installed-stack selection, backup, and recovery procedures.

## Image ownership

- [Backend Dockerfile](../backend/Dockerfile): application, test, and repository-tool targets.
- [Frontend Dockerfile](../frontend/Dockerfile): dependencies, build, and production runtime.
- [PostgreSQL Dockerfile](postgres/Dockerfile): pinned database image and reviewed OS updates.

Build contexts and runtime mounts are deliberately limited. Keep private settings,
backups, source-review evidence, and generated reports out of images.
