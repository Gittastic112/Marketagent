# Operations

This guide owns commands that inspect or change an existing installation, ingest
external data, or manage recovery. Run from the repository root. First-time setup
lives in [Local development](local-development.md); tests and builds live in
the [runbook](execution-runbook.md). Inspect each command's side effects before
running it. Dated machine-specific observations are not fresh runtime checks.

## Select the installed local stack

The installation uses Compose project market-intelligence-review-20261112-financial-history
and the original database volume. Its ignored runtime-images.yml selects reviewed
images, the existing network and preserved volumes. Normal-runtime commands in
this runbook include that override to select the installed images and data.
On another checkout, use that installation's verified override; first-time setup
is covered in [local development](local-development.md#start-and-sign-in).

~~~bash
docker compose -f docker-compose.yml -f output/milestones/product-development-20261107/runtime-images.yml --profile '*' ps --all
docker compose -f docker-compose.yml -f output/milestones/product-development-20261107/runtime-images.yml --profile automation up -d --no-build postgres backend frontend scheduler
~~~

The daily brief scheduler belongs to the `automation` profile. Include `--profile automation` when checking its settings with `config --hash scheduler`. The start command above selects the four installed services. The optional source-refresh worker and pgAdmin can stay disabled.
Their unused containers need not be retained. The optional pgAdmin image has a
registry-qualified digest so Docker can fetch that exact version when needed.
Backend/frontend health checks use 30-second steady-state intervals and
five-second startup intervals. An unhealthy transition can therefore take longer
to report than the former ten-second polling; endpoints remain available for
an immediate explicit check. Startup/schema validation is unchanged.
Backup/restore helpers select a project through COMPOSE_PROJECT_NAME and accept
an ordered COMPOSE_FILE list, separated by COMPOSE_PATH_SEPARATOR (default `:`).
Each path becomes a separate `-f` argument, including paths with spaces. The local
November 15 repair validates every file and resolved configuration, then compares
the ordered absolute paths with the running database's Compose configuration label
before a dump or restore. Missing/mismatched configuration fails closed.
For this installation the list must include the base file followed by the runtime
override above. Verify images, volumes and writers without printing resolved secrets.
The backup helper restores the new dump into a temporary verification database and inventories its contents before marking it complete. The recorded November 18 check verified the single pre-change set against the normal database and original asset. A populated legacy-version upgrade and off-device recovery still need independent proof. Use the helper only for a [change that needs a recovery point](#when-to-make-a-backup). [Recorded verification](current-state.md#dated-validation)

Ordinary updates should reuse this selected Compose project. Apply the
[change-triggered backup policy](#when-to-make-a-backup), reusing a compatible
verified recovery set for application-only changes. Record the prior override,
image IDs and mounts; preserve private settings without printing their values.
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

## Update only the frontend

Use this for a presentation-only release after source application, frontend
tests/typecheck and documentation checks. The [Geist UI notes](geist-ui.md)
describe visual acceptance. For the combined Geist and adapter release, use the [frontend and backend checklist](roadmaps/ui-adapter-worklist.md#release-checklist). First verify the selected
project, current frontend image ID, mounts and port bindings using the existing
base file and runtime override. Preserve unrelated working-tree edits and all
private settings. A source patch alone does not change a production container.

Choose an unused release tag; this example is for the Geist update. Do not replace
an installed or retained rollback tag. From the original repository root:

~~~bash
runtime_override=output/milestones/product-development-20261107/runtime-images.yml
frontend_image=market-intelligence-review-frontend:geist-20261117-1
docker compose -f docker-compose.yml -f "$runtime_override" ps --all
docker compose -f docker-compose.yml -f "$runtime_override" images frontend
docker build --tag "$frontend_image" frontend
~~~

Stop if the build fails. Record the previous frontend image reference and ID;
then set only `services.frontend.image` in the existing runtime override to the
new image reference. Keep the same two Compose files, project name, network,
volumes and other service images. Adding a third persistent override changes the
configuration-file labels checked by the existing recovery helpers.

After source/build gates pass and the override is reviewed, replace only the
frontend. This command does not recreate PostgreSQL, the backend or workers:

~~~bash
docker compose -f docker-compose.yml -f "$runtime_override" config --quiet && \
  docker compose -f docker-compose.yml -f "$runtime_override" up -d --no-deps --no-build frontend
docker compose -f docker-compose.yml -f "$runtime_override" ps --all
curl --fail http://127.0.0.1:3000/api/auth/readiness
curl --fail http://127.0.0.1:8000/api/readiness
~~~

Wait for frontend readiness before browser acceptance; startup can take time.
Verify sign-in, affected routes, both themes and mobile layout against existing
records. Record the actual source revision, image ID and scoped results in
[Current State](current-state.md). Do not mark the UI installed merely because
the build succeeded. If it fails acceptance, restore the prior frontend image
reference in the same override and repeat the frontend-only replacement.
Keep that predecessor until verification passes, then apply the
[retention policy](#essential-retention-policy). This change needs no database
dump, migration, seed, restore, new normal stack or volume removal.

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
Image identities change with reviewed installations. Inspect the active override
and actual service identities before changing any service; use the latest
[dated installation receipt](../data/reviews/dependency-security-20261114.json)
as historical evidence, not a substitute for inspection. Source scheduling and
pgAdmin remain stopped.

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

On the November 18 installed chart release there were four normal containers: frontend, backend, PostgreSQL and the Daily Brief scheduler. The source-refresh worker and optional admin service were off. Docker can show multiple tags for shared layers. The installed data, recovery set and essential tooling have different storage roles. Inspect the current context before removing anything.

The [November 12 cleanup receipt](../data/reviews/docker-storage-cleanup-20261112.json) and [November 18 release record](https://github.com/Gittastic112/Marketagent/pull/21) preserve the earlier measured totals. Use the inspection commands above for a current measurement.

### Essential retention policy

Updated November 18, 2026: the user requires at most one retained backup set.
This replaces the earlier seven-local/four-weekly-copy target and blanket retention
of stopped rollback stacks. It is an operating policy, not installed automated
pruning. Retain the following roles, not a fresh copy per task or build.

| Material | Retention rule | Release condition |
|---|---|---|
| Live database and original asset stores | Keep the active authoritative data and required assets | Never delete/reset as routine cleanup |
| Original source reports, reviewed evidence, saved model versions and decision receipts | Keep canonical originals and the references needed to interpret decisions | Remove only proved redundant physical copies; unique evidence/history is not build waste |
| Current recovery set | One latest verified complete set covering database and required assets, with manifest and checksums | Replace only after the successor passes the required verification; never remove the only good copy first |
| Pre-change recovery role | Use the single verified set as the pre-change recovery point | Replace it after the change and successor restore proof pass; no separately retained predecessor |
| Current runtime images | Keep images used by the installed services | Retire a replaced image after the new service passes its scoped checks and no active rollback role needs it |
| Application rollback image | At most one predecessor per changed service while validating that deployment | Release after readiness, affected browser behavior and compatibility checks pass; no permanent stopped rollback container |
| Tools/test image | Keep only a currently required, non-redundant image | Retire when a verified replacement exists or the workflow no longer needs it |
| Containers, networks and volumes from completed tests | Remove exact identified disposable resources after evidence is captured | Confirm they have no active task, live mount or unique data; do not infer this from their name alone |
| Build cache and intermediate images | Temporary during active iteration; target zero unneeded cache at rest | Remove after the associated build/verification completes; do not interrupt another active job |
| Screenshots, reports and logs | Keep a compact validation receipt, representative proof and the minimum evidence needed for unresolved failures | Remove repeated captures, bulk exports and reproducible logs once they add no unique diagnostic value |
| Failed/incomplete backup or restore artifacts | Keep failure reason and the minimum necessary reproducer; retain any unique recoverable data | After diagnosis, remove disposable payloads by exact path; failure must never displace the verified recovery set |

The local recovery budget is one verified set at rest. Creating and verifying its
replacement temporarily requires both copies; remove the predecessor immediately
after the successor passes. A failed replacement must preserve the previous copy.
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

The format-3 helper verifies a dump by restoring it in isolation. Inspecting a checksum alone establishes file integrity. A historical-schema upgrade, off-device key recovery and a current-format restore each need their own evidence. Record which was exercised. Keep new test records out of the normal installation. [Deferred rehearsals](limitations.md#ordered-operator-handoff)

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
request for automation. The backup script defaults to pruning off and retains one
verified set when pruning is explicitly enabled. Enable it only after confirming
the current change no longer needs the predecessor. It validates script-owned
folders; unrelated archives require a separate inventory and exact-path cleanup.

## Data and operational tools

The [adapter operator guide](adapters/README.md) covers explicit Research Lab/source
actions, provider keys, optional image build arguments, isolated OCR and reference
snapshot refresh. These source additions do not install themselves into a running
stack. Keep the existing Compose project, data and review state when scheduling a
rollout; verify its exact image/profile identity. Marker currently reports a
dependency conflict, and Docling needs preprovisioned models plus an inference check.

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
  Alembic checks older revisions before applying any changes. PostgreSQL holds table locks through the upgrade transaction.
  The guard protects populated tables at `2167b87f7054`, non-null pricing multiples at `8550649236ca`,
  and private rows about to receive a fallback owner at `a1a1a1a1a1a1` or `b8b8b8b8b8b8`.
  The runner refuses offline SQL generation across these revisions. Use the online migration so it can inspect the data and hold the database lock through the upgrade.
  Empty predecessors can upgrade. Populated predecessors that trigger a guard retain their records and revision.
  Resolve the legacy definition or rightful owner before a preserving conversion. A current-head database skips earlier revisions.
  On an explicitly selected installation, `python -m app.db.migration_safety` prints just the table names and counts of fallback-owned records.
  An empty object means no matching rows in the supported private tables. This read-only diagnostic does not assign an owner.
  [PostgreSQL preservation evidence](archive/checkpoints/2026/integration-review-2026-11-19.md)
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
  fallback count is one if pruning is explicitly enabled. The count-only helper
  deletes older verified format-2/3 folders owned by the script and preserves
  invalid, unrelated, legacy and linked folders. It does not protect active pins.
  Apply the [essential retention policy](#essential-retention-policy), keep automatic
  pruning off during an active rollback need, and never remove the only verified recovery copy.
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
