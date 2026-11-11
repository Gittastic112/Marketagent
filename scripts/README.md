# Repository tools

Run from the repository root. [Execution runbook](../docs/execution-runbook.md)
owns validation commands; [Operations](../docs/operations.md) owns commands that
touch an installation or data. Read the arguments and target before execution.

## Verification

| Tool | Purpose and side effects |
|---|---|
| [check_docs.py](check_docs.py) | Read-only current links/anchors, context budgets, route coverage, and migration-head agreement |
| [check_secrets.py](check_secrets.py) | Heuristic source credential scan; does not establish full-history safety |
| [check_dependency_locks.py](check_dependency_locks.py) | Direct requirement and hash-lock consistency |
| [check_api_contracts.py](check_api_contracts.py) | Critical wire-contract comparison; only explicit --write regenerates the fixture |
| [validate_project_skills.py](validate_project_skills.py) | Project workflow-reference structure |
| [check_workstream_ownership.sh](check_workstream_ownership.sh) | Read-only disjoint ownership and optional changed-path checks |
| [check_local_auth.py](check_local_auth.py) | Operator auth-configuration preflight; private configuration must be accessible to the operator |
| [check_container_scan.py](check_container_scan.py) | Evaluate retained OS-scan JSON |
| [scan_container_images.sh](scan_container_images.sh) | Inspect images, invoke vulnerability scanning, and write reports; network/tooling required |
| [verify_release_baseline.sh](verify_release_baseline.sh) | Build and verify a clean source baseline using isolated containers and a disposable database |
| [run_browser_workflows.sh](run_browser_workflows.sh) | Build/start a separate browser-test project and write traces/screenshots |
| [verify_milestone_a.py](verify_milestone_a.py) | Legacy connectivity probe; --write additionally creates/ingests records. Not a release acceptance certificate |

Regression checks are the adjacent `test_*.py` modules and
[test_workstream_ownership.sh](test_workstream_ownership.sh).
Application behavior tests live in backend/tests, frontend/lib, and frontend/e2e.

## Recovery

| Tool | Purpose and side effects |
|---|---|
| [backup_local.sh](backup_local.sh) | Create and verify a local recovery archive; includes a disposable verification database |
| [restore_local.sh](restore_local.sh) | Replace the explicitly selected database after verification; destructive, requires exact-target authorization |
| [drill_backup_restore.sh](drill_backup_restore.sh) | Disposable isolated recovery drill, not a normal-database restore |
| [recovery_common.sh](recovery_common.sh) | Shared project/target selection and recovery helpers |
| [recovery_metadata.py](recovery_metadata.py), [recovery_inventory.sql](recovery_inventory.sql) | Manifest, hashes, and table/asset inventory support |
| [restore_drill_fixture.py](restore_drill_fixture.py) | Writes only the recovery drill's synthetic fixture |

Preserve backup archives, failed evidence, source originals, and rollback images.
A passed disposable drill is not encrypted off-device recovery.

## Data and reference tools

| Tool | Purpose and side effects |
|---|---|
| [ingest_damodaran.py](ingest_damodaran.py) | Explicit source-backed benchmark import; inspect preview/apply options and target |
| [certify_financial_histories.py](certify_financial_histories.py) | Reference certification workflow with database/source effects; not general financial truth |
| [evaluate_financial_extraction.py](evaluate_financial_extraction.py) | Retained unavailable entry point; directs callers to the actual Evaluation Lab |
| [seed_regressions.py](seed_regressions.py) | Synchronize source-backed regression coefficients; writes and may remove obsolete coefficients |
| [seed_regression_coefficients.py](seed_regression_coefficients.py) | Compatibility entry point for seed_regressions |
| [seed_sample_data.py](seed_sample_data.py) | Writes synthetic/sample records; never an automatic first-install step |
| [seed_e2e_reference_data.py](seed_e2e_reference_data.py) | Isolated browser/reference fixture setup; never target the user's database |

[Backend scripts](../backend/scripts/) contain provider probes, source-review
staging/finalization, and portfolio-readiness reporting. Their names do not imply
read-only behavior. Consult the runbook and Operations before invoking them.

## Retired tools

[Retired inventories](retired/README.md) record old scratch utilities and their
original hashes. Their retained local source copies are inactive and excluded
from publication and builds. Do not execute them as current procedures.
