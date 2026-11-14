# Operations

This guide owns commands that inspect or change an existing installation, ingest
external data, or manage recovery. Run from the repository root. First-time setup
lives in [Local development](local-development.md); tests and builds live in
the [runbook](execution-runbook.md). Inspect each command's side effects before
running it. Dated machine-specific observations are not fresh runtime checks.

## Select the installed local stack

The installation, updated November 12, uses Compose project market-intelligence-review-20261112-financial-history
and the original database volume. Its ignored runtime-images.yml selects reviewed
images, the existing network and preserved volumes. Normal-runtime commands in
this runbook include that override to select the installed images and data.
On another checkout, use that installation's verified override; first-time setup
is covered in [local development](local-development.md#start-and-sign-in).

~~~bash
docker compose -f docker-compose.yml -f output/milestones/product-development-20261107/runtime-images.yml --profile '*' ps --all
docker compose -f docker-compose.yml -f output/milestones/product-development-20261107/runtime-images.yml up -d --no-build postgres backend frontend scheduler
~~~

The source-refresh worker and pgAdmin stay disabled unless deliberately enabled.
Their unused containers need not be retained. The optional pgAdmin image has a
registry-qualified digest so Docker can fetch that exact version when needed.
Backend/frontend health checks use 30-second steady-state intervals and
five-second startup intervals. An unhealthy transition can therefore take longer
to report than the former ten-second polling; endpoints remain available for
an immediate explicit check. Startup/schema validation is unchanged.
Existing backup/restore helpers select a project separately: set
COMPOSE_PROJECT_NAME=market-intelligence-review-20261112-financial-history for this installation.
Their ordinary operator environment behavior remains; agent verification uses
/dev/null plus settings held only in memory. The full backup helper creates a
disposable proof database, so it remains outside the current no-new-datasets scope.

Ordinary updates should reuse this selected Compose project. Save a database
backup, the prior override, image IDs, settings and mounts before replacement.
Preserve source reports, review receipts and backup files from a container's
writable layer before removing it. Keep the installed, verified images as the
recovery baseline; retain a preceding version only while an update is being
verified. A chain of stopped application stacks is not the backup strategy.
Stop old writers and PostgreSQL before any replacement shares the same volume.
Verify one selected container per service and backup-helper database selection.

If an exceptional investigation must retain an old container, renaming it does
not change its Compose labels. Isolate that retained project from the replacement
until the investigation is complete. The November 12
[checkpoint](archive/checkpoints/2026/handoff-review-2026-11-12.md) and
output/milestones/financial-completion-20261112/deployment-history retain the
earlier rollout evidence; they do not require indefinite container retention.

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
The current override selects the financial-history backend and source-links frontend,
with the existing November 7 PostgreSQL R2. Inspect image identities before
changing any service. Source scheduling and pgAdmin remain stopped.

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

Apply the [essential retention policy](#essential-retention-policy) after measuring
the selected Docker context and filesystem. Reproducible cache is temporary working
material, not a recovery copy. Clear identified unused build/test material once its
operation has finished; avoid broad system/volume pruning. Shared layers mean Docker
categories are not an exact sum of extra host disk use. Record actual before/after
measurements, not only the displayed reclaimable estimate.

An unattached volume or stopped container can still contain unique data. Inspect
its mounts, role and content classification before removal. Existing authority to
remove disposable material does not authorise destroying unknown unique records.
No automatic pruning is configured by these instructions.

The November 12 [authorized storage cleanup](../data/reviews/docker-storage-cleanup-20261112.json)
removed 151 stopped containers, 256 obsolete image objects, 21 unused volumes,
three unused networks and the unused build cache. Four running containers, four
images and the active database/admin volumes remain. All 110 database table
fingerprints match the pre-cleanup snapshot. Source files and old database copies
found inside removed containers are retained outside Docker. Fourteen inactive
data/settings volumes have compressed archives with every file byte and ownership
mode checked before their removal. Exact targets, archive locations and hashes
are recorded in the receipt. No running container was restarted. The optional
admin image is fetched by its recorded registry digest when next enabled.

November 13 after the [P1 installation](../data/reviews/research-workspace-p1-20261113.json): four running containers, four images
(2.64 GB), two volumes (210.7 MB), and zero build cache. The tools image accounts
for the 717 MB Docker labels reclaimable; it is actively needed for repository and
recovery checks on this host. The whole local output directory occupies about
2.9 GB, including source/recovery/evidence material, so it is not a disposable cache.
The latest dated-input review directory is about 31 MB. The top-level backups
directory is about 3.1 MB; that is not the total of recovery copies stored elsewhere.
P1 replaced only the frontend, reused recovery material, and created no backup or
dataset. Its temporary preview, dependency/old frontend images, build context and
2.169 GB of reported build cache were removed. The output/backups sizes above are
the earlier planning measurement, not a new claim about their exact current sizes.

### Essential retention policy

Effective November 13, 2026, following the user's request to retain only essentials.
This replaces the earlier seven-local/four-weekly-copy target and blanket retention
of stopped rollback stacks. It is an operating policy, not installed automated
pruning. Retain the following roles, not a fresh copy per task or build.

| Material | Retention rule | Release condition |
|---|---|---|
| Live database and original asset stores | Keep the active authoritative data and required assets | Never delete/reset as routine cleanup |
| Original source reports, reviewed evidence, saved model versions and decision receipts | Keep canonical originals and the references needed to interpret decisions | Remove only proved redundant physical copies; unique evidence/history is not build waste |
| Current recovery set | One latest verified complete set covering database and required assets, with manifest and checksums | Replace only after the successor passes the required verification; never remove the only good copy first |
| Pre-change recovery set | At most one additional distinct set for an active schema/substantial data change, with a named task and release condition | Retire after the change is verified and the current recovery set covers the resulting state; one set can fulfil both roles before writes |
| Current runtime images | Keep images used by the installed services | Retire a replaced image after the new service passes its scoped checks and no active rollback role needs it |
| Application rollback image | At most one predecessor per changed service while validating that deployment | Release after readiness, affected browser behavior and compatibility checks pass; no permanent stopped rollback container |
| Tools/test image | Keep only a currently required, non-redundant image | Retire when a verified replacement exists or the workflow no longer needs it |
| Containers, networks and volumes from completed tests | Remove exact identified disposable resources after evidence is captured | Confirm they have no active task, live mount or unique data; do not infer this from their name alone |
| Build cache and intermediate images | Temporary during active iteration; target zero unneeded cache at rest | Remove after the associated build/verification completes; do not interrupt another active job |
| Screenshots, reports and logs | Keep a compact validation receipt, representative proof and the minimum evidence needed for unresolved failures | Remove repeated captures, bulk exports and reproducible logs once they add no unique diagnostic value |
| Failed/incomplete backup or restore artifacts | Keep failure reason and the minimum necessary reproducer; retain any unique recoverable data | After diagnosis, remove disposable payloads by exact path; failure must never displace the verified recovery set |

The ordinary local recovery budget is therefore one verified set, temporarily two
distinct sets when an active data/schema change needs a separate rollback point.
This favours current recovery over a long series of historical restore dates;
source revisions and model/decision history remain in the application.
Do not rotate an active pre-change set merely because a newer timestamp exists.

An older archive containing unique historical records is not proved redundant by
the existence of a current dump. Classify it explicitly: required recovery, unique
retained evidence, or disposable duplicate. Record the reason and the next review
condition for any exception. Do not create an archive of material already classified
as disposable merely to feel safer deleting it; that does not reclaim space.

#### When to make a backup

| Change | Required treatment |
|---|---|
| Documentation, read-only investigation, screenshots, ordinary frontend/layout change | No new database dump. Reuse existing recovery material |
| Application-only deployment with no schema/data mutation | Reuse a compatible verified recovery set; temporarily retain the changed service's current image |
| Schema migration, database-engine change or substantial persisted-data rewrite/import | Verify a suitable pre-change recovery set and matching asset/compatibility basis before writes |
| Meaningful research/data changes accumulated since the last verified recovery point | Refresh the current set at the end of that meaningful write session, then retire the superseded set under this policy |
| Unchanged data or repeated testing of the same source revision | No duplicate backup or copied evidence bundle |

A dump checksum or successful archive listing alone is not a full restore proof.
Use the supported verification level and label exactly what ran. The existing
restriction on new local disposable datasets and the deferred populated restore
rehearsal remain in the [operator handoff](limitations.md#ordered-operator-handoff).
If a required verification cannot run within scope, report that exact dependency;
do not restore over the normal database or call an unverified dump fully verified.

#### Cleanup procedure and receipt

1. Inventory exact paths/resource IDs, sizes, live references and task ownership.
   Do not read or export secret settings as part of inventory.
2. Identify the active database/assets, current verified recovery set, any active
   pre-change pin, current images and unique source/evidence dependencies.
3. Compare proposed duplicates by bytes/hash and logical contents where needed.
   A filename, age, stopped state, untracked status or Docker reclaimable label is
   insufficient. Keep referenced evidence at its canonical location.
4. Remove only the identified disposable targets within the user's cleanup scope.
   Unknown unique-data deletion needs a specific disposition, not a broad prune.
5. Confirm retained recovery checksums, runtime readiness and required mounts. For
   persisted-data operations, compare the affected records and preservation basis;
   do not create a full database dump just to prove a CSS or documentation edit.
6. Record one compact receipt: task/date, exact removed IDs/paths, retained roles,
   verification and measured byte savings. Reuse it in other docs by link.

Do not add a scheduled job or notification to enforce this policy without a user
request for automation. The current backup script defaults to pruning off and a
count of seven when explicitly enabled. Its pruning logic validates script-owned
folders but cannot protect a semantic pre-change pin. Merely setting the count to
two is unsafe if the root contains a pinned older set. Leave automatic pruning off;
select exact targets manually until role-aware retention is implemented and tested.

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
  When a new verified recovery point is required, use an authorised separate
  environment and compare every table plus original asset bytes. A frontend-only
  update does not trigger a new dump or restore rehearsal. Within an explicitly
  authorised drill scope, run `bash scripts/drill_backup_restore.sh` for the concurrent-write
  and original-byte drill. It builds `docker-compose.recovery.yml`, publishes no
  ports, checks the actual tmpfs data directory and never adopts an existing project.
  Fake-Docker and metadata tests cover corruption, failures, interruptions and
  worker state. PostgreSQL 16 is the supported fingerprint basis.
  `BACKUP_ROOT` selects a local folder. Directories/files use 0700/0600. Failed
  backups retain a folder without a valid `COMPLETE` marker for inspection. Old
  `.partial` backups remain incomplete. Script retention defaults off; its current
  fallback count is seven if pruning is explicitly enabled. The count-only helper
  deletes older verified format-2/3 folders owned by the script and preserves
  invalid, unrelated, legacy and linked folders. It does not protect active pins.
  Apply the [essential retention policy](#essential-retention-policy), keep automatic
  pruning off until role-safe, and never remove the only verified recovery copy.
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

Use the change-triggered [essential retention policy](#essential-retention-policy).
No backup is required for every working day, review, UI edit or application rebuild.
A meaningful data-write session or a relevant migration creates a recovery need;
an unchanged database does not. Avoid duplicate before/intermediate/after dumps
when one existing verified set and one necessary successor cover the operation.

Off-device protection remains deferred in the current release scope. If the user
later supplies an encrypted destination, define its bounded retention and retrieval
test at that time. Do not silently start weekly copying or preserve four weekly
copies under the superseded guidance. Same-disk recovery does not protect against
loss of the device.

This is an operating procedure, not a configured schedule. No recurring task,
transfer, secret export, encryption-key storage or deletion is authorized merely
by this paragraph. Use a separate explicit scheduling request for automation.
The [operator handoff](limitations.md#ordered-operator-handoff)
records the missing destination and privately retained recovery method; same-disk
folders cannot complete M03-07.
