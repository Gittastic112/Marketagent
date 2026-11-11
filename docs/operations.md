# Operations

This guide owns commands that inspect or change an existing installation, ingest
external data, or manage recovery. Run from the repository root. First-time setup
lives in [Local development](local-development.md); tests and builds live in
the [runbook](execution-runbook.md). Inspect each command's side effects before
running it. Dated machine-specific observations are not fresh runtime checks.

## Select the installed local stack

The installation, updated November 9, uses Compose project market-intelligence-product-20261107
and the original database volume. Its ignored runtime-images.yml selects reviewed
images, the existing network and preserved volumes. Normal-runtime commands in
this runbook include that override so retained rollback containers are excluded.
On another checkout, use that installation's verified override; first-time setup
is covered in [local development](local-development.md#start-and-sign-in).

~~~bash
docker compose -f docker-compose.yml -f output/milestones/product-development-20261107/runtime-images.yml --profile '*' ps --all
docker compose -f docker-compose.yml -f output/milestones/product-development-20261107/runtime-images.yml up -d --no-build postgres backend frontend scheduler
~~~

The source-refresh worker and pgAdmin stay stopped unless deliberately enabled.
Backend/frontend health checks use 30-second steady-state intervals and
five-second startup intervals. An unhealthy transition can therefore take longer
to report than the former ten-second polling; endpoints remain available for
an immediate explicit check. Startup/schema validation is unchanged.
Existing backup/restore helpers select a project separately: set
COMPOSE_PROJECT_NAME=market-intelligence-product-20261107 for this installation.
Their ordinary operator environment behavior remains; agent verification uses
/dev/null plus settings held only in memory. The full backup helper creates a
disposable proof database, so it remains outside the current no-new-datasets scope.

## Rotate the local database password

This is an operator maintenance step, not an instruction for an agent to read
protected settings. It changes the existing role password without dropping data.
Finish active application writes first, retain a fresh verified backup, and keep
the old password privately until authentication is verified. Do not paste either
password into chat or commands. Never use `docker compose down -v`.

1. Privately add POSTGRES_PASSWORD to the root `.env`: at least 32 random URL-safe
   characters (letters, digits, `_`, `-`). Preserve all other settings. Update any
   separately configured host DATABASE_URL privately. Leave pgAdmin disabled and
   PGADMIN_DEFAULT_PASSWORD unset unless that separate service is required.
2. Use the verified November 7 security image override and validate
   configuration without printing it:

   ~~~bash
   docker compose -f docker-compose.yml -f output/milestones/product-development-20261107/runtime-images.yml config --quiet
   docker compose -f docker-compose.yml -f output/milestones/product-development-20261107/runtime-images.yml stop frontend backend scheduler source_scheduler
   docker exec -it market_intel_postgres psql -X -U marketintel -d marketintel
   ~~~

3. At the database prompt, enter `\password marketintel`, then enter the new
   password twice at the hidden prompts. Use `\q` to exit. This changes the role;
   the PostgreSQL container's startup variable alone cannot do that for an existing volume.
4. Recreate clients and PostgreSQL with the matching private setting, preserving
   the current image versions and stopped optional services:

   ~~~bash
   docker compose -f docker-compose.yml -f output/milestones/product-development-20261107/runtime-images.yml up -d --no-build --force-recreate postgres backend frontend scheduler
   docker compose -f docker-compose.yml -f output/milestones/product-development-20261107/runtime-images.yml create --no-build source_scheduler pgadmin
   docker compose -f docker-compose.yml -f output/milestones/product-development-20261107/runtime-images.yml ps --all
   ~~~

5. Verify backend/frontend/database health, sign-in and the user-selected company
   list. Preserve the November 9 research scope; do not automatically reseed or restore removed companies.
   Test password authentication with `docker exec -it market_intel_postgres psql
   -h 127.0.0.1 -U marketintel -d marketintel -W`, then `SELECT 1;` and `\q`.
   Source scheduling and pgAdmin must remain stopped. Record status only, never
   credential values. If clients fail, keep them stopped and correct the matching
   private setting; the same local database prompt can reset the role without a
   restore or data loss. Recheck all table/asset fingerprints afterward.

The November 2 rotation is already verified. These steps are for a future rotation,
which is complete only after private input and authentication/data checks pass.
The last recorded override selects November 9 application images and November 7
PostgreSQL R2. Inspect its current image selection before changing any service.

## Normal runtime operations

### Valuation source refresh

With user approval, set `VALUATION_REFRESH_ENABLED=true` and
`VALUATION_REFRESH_OWNER_ID` to the existing local user ID in ignored `.env`.
Never print credential values. The fixed schedule is weekdays 07:00
America/New_York; DST is handled automatically. The scope is active companies
with exchange/local-symbol identities, not arbitrary test catalog rows.

~~~bash
docker compose -f docker-compose.yml -f output/milestones/product-development-20261107/runtime-images.yml --profile automation up --no-build -d backend source_scheduler
docker compose -f docker-compose.yml -f output/milestones/product-development-20261107/runtime-images.yml --profile automation ps
docker compose -f docker-compose.yml -f output/milestones/product-development-20261107/runtime-images.yml logs --tail=50 source_scheduler
~~~

Manual refresh: open a company's valuation draft and choose **Fetch latest source
inputs**. It saves current edits, queues the job and polls progress. The worker
checks every 30 seconds. **Refresh Stored Inputs** performs no provider fetch.
Both paths preserve explicit edits and require review before model creation.
Source refreshes do not approve financial candidates or recalculate saved models.

The worker must stay running for manual queued jobs even if weekday automation
is disabled. A weekday startup after 07:00 runs that day's single due job; it does
not backfill older dates. A stopped/interrupted job is marked failed on the next
worker cycle and requires explicit retry. Provider failures and manual India
coverage appear in Data Health, not as fake success. Existing brief scheduling
remains separate.

### General runtime commands

These commands change the normal local runtime; use only within the requested
workflow. A code review or diagnosis alone does not authorize deploying changes.

~~~bash
docker compose -f docker-compose.yml -f output/milestones/product-development-20261107/runtime-images.yml up --no-build -d
docker compose -f docker-compose.yml -f output/milestones/product-development-20261107/runtime-images.yml ps
docker compose -f docker-compose.yml -f output/milestones/product-development-20261107/runtime-images.yml logs backend --tail=100
docker compose -f docker-compose.yml -f output/milestones/product-development-20261107/runtime-images.yml logs frontend --tail=100
curl --fail http://localhost:8000/api/health
curl --fail http://localhost:8000/api/readiness
~~~

Readiness checks DB/schema/migrations; liveness only proves a responding process.
If readiness fails, inspect returned blockers before changing the database.

~~~bash
docker compose -f docker-compose.yml -f output/milestones/product-development-20261107/runtime-images.yml exec backend alembic heads
docker compose -f docker-compose.yml -f output/milestones/product-development-20261107/runtime-images.yml exec backend alembic current
docker compose -f docker-compose.yml -f output/milestones/product-development-20261107/runtime-images.yml exec backend alembic upgrade head
~~~

Upgrade only an intact compatible migration chain. Never stamp/drop/reset data
to hide a missing revision. Never chmod a Docker socket to 666; inspect Desktop,
context and permissions instead.

Optional deterministic worker:

~~~bash
docker compose -f docker-compose.yml -f output/milestones/product-development-20261107/runtime-images.yml --profile automation up --no-build -d scheduler
docker compose -f docker-compose.yml -f output/milestones/product-development-20261107/runtime-images.yml logs scheduler --tail=100
docker compose -f docker-compose.yml -f output/milestones/product-development-20261107/runtime-images.yml stop scheduler
~~~

Scheduled briefs do not call external AI. Explicit AI refresh remains user-driven.
pgAdmin is optional via the admin profile. Normal Compose ports now specify
127.0.0.1. Existing containers need recreation to apply this, not just restart.
Do not recreate PostgreSQL without checking the persistent volume and backup;
never remove a database volume to change its port binding.

### Resource inspection and bounded cleanup

Measure after startup and again while idle. CPU can exceed 100% when a process
uses more than one core. Docker's memory limit is a ceiling, not memory consumed;
Desktop's VM can use additional memory outside these container measurements.

~~~bash
docker stats --no-stream
docker system df
docker compose -f docker-compose.yml -f output/milestones/product-development-20261107/runtime-images.yml ps --all
~~~

For occasional database administration, start pgAdmin explicitly and stop it
when finished. It has no automatic restart policy in the current configuration:

~~~bash
docker compose -f docker-compose.yml -f output/milestones/product-development-20261107/runtime-images.yml --profile admin up -d pgadmin
docker compose -f docker-compose.yml -f output/milestones/product-development-20261107/runtime-images.yml stop pgadmin
~~~

Inspect disk usage before a requested cleanup. A bounded build-cache cleanup,
which does not remove images, containers, volumes or database records, is:

~~~bash
docker builder prune --filter until=168h --keep-storage 5GB
docker system df
~~~

The command asks for confirmation. It targets old unused build cache and can
slow the next rebuild. It is not a persistent 5 GB quota: newer, shared or active
records can remain above that amount. Shared layers also mean Docker's categories
are not an exact sum of extra host disk use. See Docker's
[cache accounting](https://docs.docker.com/reference/cli/docker/buildx/du/) and
[garbage collection](https://docs.docker.com/build/cache/garbage-collection/) docs.
Do not treat an unattached volume or stopped image/container as disposable; it
can still hold data or a rollback image. Inventory those separately and obtain
exact-target authorization before deleting user data. No automatic pruning is set up.

## Data and operational tools

### US benchmark intake

The user-approved US-specific January 2026 sources have separate dated filenames.
This explicit, audited import does not fetch new versions or approve mappings:

~~~bash
docker compose -f docker-compose.yml -f output/milestones/product-development-20261107/runtime-images.yml exec -T backend python scripts/ingest_damodaran.py --market US
~~~

It supports beta_methods, wacc_methods, margin, capex, roe and working_capital.
Use `--only` to select these contracts. Repeating the same bytes is idempotent;
changed dates/populations require a separately registered source version. The
default `--market IN` retains the existing India workflow. Inspect coverage in
Data Health, then use **Refresh Stored Inputs** on an existing draft. New priors
remain review-required and do not alter saved models.

### Other tools

- The old `scripts/evaluate_financial_extraction.py` command is unavailable and
  exits nonzero. It never compared actual extraction with independent answers;
  its historical percentage output is not validation evidence. Use **Evaluation
  Lab** at `/evaluations` with a complete, separately reviewed reference and the
  exact stored text hash. This evaluates local text only, not PDF/XBRL parsing,
  financial approval or AI interpretation. The compatibility notice and its
  regression run in repository/release checks; older built images can retain
  the retired script until rebuilt.
- backend/scripts/check_ai_provider.py is an explicit external Gemini check, not
  a deterministic test. It sends only the fixed prompt `Reply exactly OK.`, uses
  GEMINI_API_KEY/GEMINI_MODEL from the backend environment and persists a sanitized
  Processing Run with model, prompt version and input hash. No company, portfolio
  or research records are sent. After a deliberate local configuration change:

  ~~~bash
  docker compose -f docker-compose.yml -f output/milestones/product-development-20261107/runtime-images.yml up -d --no-deps backend
  docker compose -f docker-compose.yml -f output/milestones/product-development-20261107/runtime-images.yml exec -T backend python backend/scripts/check_ai_provider.py
  ~~~

  Rebuild the backend first if source changed. An optional `--model` probes an
  override without changing configuration; health only uses runs for the current
  configured model. Success proves connectivity, not AI output quality or quota.
- scripts/ingest_damodaran.py imports supported source contracts and writes data.
  Inspect its --only options; generic inventory is not typed application support.
- scripts/verify_milestone_a.py is retired and exits unavailable, including with
  legacy --write flags. Use authenticated Data Health for provider checks and the
  release baseline runner for isolated software verification.
- backend/scripts/check_portfolio_real_input_readiness.py is a read-only,
  owner-scoped preflight. It does not seed, refresh, capture snapshots or satisfy
  the manual browser gate.
- scripts/backup_local.sh and restore_local.sh own backup/restore. Inspect exact
  targets and get data-loss authorization before restore/reset/volume deletion.
  Format 3 verifies the completed dump in a network-disabled, bounded scratch
  PostgreSQL 16 container; normal writes can continue. Its manifest contains all
  public table counts/content fingerprints and both PDF stores' byte hashes.
  Scratch readiness requires a successful TCP query to its `proof` database,
  with bounded connection/retry waits; socket readiness during initialization
  alone does not authorize restore. Startup failure retains an incomplete folder.
  Paths, complete checksums, format and inventory are checked before replacement.
  A format-3 backup becomes complete only when its atomic `COMPLETE` file matches
  the manifest hash. Payload/checksum files are flushed before publishing that
  marker; finalization does not rename the containing directory. This works with
  the observed macOS managed-workspace directory-rename restriction. No broad
  filesystem permission change is needed. This is not a power-loss guarantee.
  Restore rejects missing, changed or linked markers before touching the database.
  Existing verified format-2 folders remain readable. Restore refuses `.partial`
  or linked folders; format 1 needs explicit
  `RESTORE_ALLOW_LEGACY=true` and provides only count-based verification.
  It stops running/restarting `scheduler` and `source_scheduler` writers before database
  replacement and resumes only those that were running after verification.
  Custom worker names use `DAILY_BRIEF_SERVICE` and `SOURCE_REFRESH_SERVICE`;
  set them to empty for a stack without those workers. Quiesce any other writers
  manually. Worker lifecycle regressions use fake Docker, not the normal database.
  Verify a backup by restoring to a separate disposable database and comparing
  every table plus original asset bytes before normal-runtime maintenance.
  Run `bash scripts/drill_backup_restore.sh` for the isolated concurrent-write
  and original-byte drill. It builds `docker-compose.recovery.yml`, publishes no
  ports, checks the actual tmpfs data directory and never adopts an existing project.
  Fake-Docker and metadata tests cover corruption, failures, interruptions and
  worker state. PostgreSQL 16 is the supported fingerprint basis.
  `BACKUP_ROOT` selects a local folder. Directories/files use 0700/0600. Failed
  backups retain a folder without a valid `COMPLETE` marker for inspection. Old
  `.partial` backups remain incomplete. Retention
  defaults off; `BACKUP_PRUNE=true BACKUP_RETENTION_COUNT=7` deletes only older
  verified format-2/3 folders owned by this script. It preserves invalid, unrelated,
  legacy and linked folders. Never remove the only verified recovery copy.
  The metadata helper uses host Python when available; set
  `RECOVERY_PYTHON_IMAGE=market-intelligence-tools:local` after building the tools
  target to use bounded, network-disabled Docker instead. `DOCKER_BIN` accepts
  the Docker executable path; `COMPOSE_ENV_FILE=/dev/null` is mandatory for agent
  drills. Operator restores must supply the same reviewed Compose environment
  as the normal app, without printing or sharing its values.
  Off-device procedure: choose an encrypted removable/off-device destination,
  copy one complete verified folder, keep recovery keys/environment separately,
  then restore the retrieved copy into the disposable environment and compare
  every table/PDF hash. A same-disk folder or cloud sync alone is not that proof.
  No transfer, credential rotation, pruning or scheduled job is performed by default.
- Root legacy scripts are not maintained entry points unless explicitly verified.

### Backup maintenance cadence

For the local release, make a verified backup after a day of meaningful edits
and immediately before migrations, credential rotation or upgrades. Once an
encrypted off-device destination exists, retain a weekly copy there and rehearse
retrieval/restore monthly and after recovery-tool changes. Keep the latest seven
verified local copies and four weekly off-device copies as the initial retention
target, adjusting for measured storage and recovery needs. Until the off-device
restore has passed and exact deletion targets have been approved, retain existing
copies and leave automatic pruning off. Never delete the only verified copy.

This is an operating procedure, not a configured schedule. No recurring task,
transfer, secret export, encryption-key storage or deletion is authorized merely
by this paragraph. Use a separate explicit scheduling request for automation.
The [operator handoff](limitations.md#ordered-operator-handoff)
records the missing destination and privately retained recovery method; same-disk
folders cannot complete M03-07.
