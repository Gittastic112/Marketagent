"""Exercise backup/restore orchestration without normal data or a Docker socket."""
from hashlib import sha256
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from scripts.test_recovery_metadata import inventory


ROOT = Path(__file__).resolve().parents[1]
FAKE_DOCKER = '''#!/usr/bin/env python3
import json, os, sys
from pathlib import Path
args = sys.argv[1:]
with open(os.environ["FAKE_DOCKER_LOG"], "a") as log:
    log.write(json.dumps(args) + "\\n")
if "pg_dump" in args:
    if os.environ.get("FAKE_DUMP_INTERRUPTED"):
        print("partial dump")
        raise SystemExit(1)
    print("Mock Data database dump")
elif "pg_restore" in args:
    sys.stdin.buffer.read()
    if "a" * 64 in args and not Path(os.environ["FAKE_DOCKER_LOG"] + ".ready").exists():
        raise SystemExit('Mock Data: database "proof" does not exist yet')
    if "--list" not in args and os.environ.get("FAKE_RESTORE_FAILED"):
        raise SystemExit(1)
elif "psql" in args and "-c" in args and args[args.index("-c") + 1] == "SELECT 1":
    assert args[args.index("-h") + 1] == "127.0.0.1"
    assert args[args.index("-U") + 1] == "proof"
    assert args[args.index("-d") + 1] == "proof"
    attempts = Path(os.environ["FAKE_DOCKER_LOG"] + ".attempts")
    attempt = int(attempts.read_text()) + 1 if attempts.exists() else 1
    attempts.write_text(str(attempt))
    if os.environ.get("FAKE_PROOF_UNAVAILABLE") or attempt < int(os.environ.get("FAKE_PROOF_READY_AFTER", "1")):
        raise SystemExit(1)
    Path(os.environ["FAKE_DOCKER_LOG"] + ".ready").write_text("Mock Data TCP proof database ready")
    print("1")
elif "psql" in args:
    sys.stdin.buffer.read()
    rows = json.loads(os.environ["FAKE_INVENTORY"])
    # The dump/scratch result is stable; live writes are deliberately different.
    if "compose" in args and os.environ.get("FAKE_BETA_COUNT"):
        for row in rows:
            if row.get("kind") == "table" and row.get("name") == "beta":
                row["rows"] = int(os.environ["FAKE_BETA_COUNT"])
    if "compose" in args and os.environ.get("FAKE_CONTENT_CORRUPTED"):
        rows[1]["sha256"] = "0" * 64
    if os.environ.get("FAKE_PROOF_INTERRUPTED"):
        os.kill(os.getppid(), 15)
        raise SystemExit(1)
    for row in rows:
        print(json.dumps(row))
elif "pg_isready" in args:
    # Model the entrypoint's temporary socket server accepting early probes.
    pass
elif "run" in args and "--detach" in args:
    print("a" * 64)
elif "rm" in args:
    pass
elif "alembic" in args:
    print("mock_revision (head)")
elif "ps" in args:
    if "-q" in args:
        print(os.environ.get("FAKE_SOURCE_CONTAINERS", "b" * 64))
    else:
        print(os.environ.get("FAKE_RUNNING_SERVICES", "backend\\nfrontend\\npostgres"))
elif "inspect" in args:
    print("sha256:" + "c" * 64)
elif any(command in args for command in ("stop", "dropdb", "createdb", "up")):
    pass
else:
    raise SystemExit("Unexpected mock Docker call")
'''


class BackupWorkflowTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.directory = Path(self.temporary.name)
        docker = self.directory / "docker"
        docker.write_text(FAKE_DOCKER)
        docker.chmod(0o755)
        self.env = {**os.environ, "PATH": f"{self.directory}{os.pathsep}{os.environ['PATH']}",
            "FAKE_DOCKER_LOG": str(self.directory / "calls.jsonl"),
            "BACKUP_ROOT": str(self.directory / "backups"), "BACKUP_PRUNE": "false",
            "COMPOSE_FILE": str(self.directory / "mock-compose.yml"),
            "COMPOSE_PROJECT_NAME": "mock-backup-test", "POSTGRES_DB": "mock_database",
            "DOCKER_BIN": str(docker), "RESTORE_ALLOW_LEGACY": "true", "RECOVERY_PYTHON_IMAGE": ""}
        rows = inventory()
        rows.extend({"kind": "table", "name": name, "rows": count, "sha256": sha256(name.encode()).hexdigest()}
            for name, count in (("alpha", 2), ("beta", 0), ("gamma", 3)))
        self.rows = rows
        self.env["FAKE_INVENTORY"] = json.dumps(rows)
        self.counts = "".join(f'{row["name"]}\t{row["rows"]}\n'
            for row in sorted(rows, key=lambda row: row.get("name", "")) if row["kind"] == "table")

    def run_script(self, name, *args):
        return subprocess.run(["bash", str(ROOT / "scripts" / name), *map(str, args)],
            env=self.env, capture_output=True, text=True, timeout=30)

    def test_recovery_shell_entrypoints_parse(self):
        for name in ("backup_local.sh", "restore_local.sh", "drill_backup_restore.sh", "recovery_common.sh"):
            with self.subTest(name=name):
                result = subprocess.run(["bash", "-n", str(ROOT / "scripts" / name)], capture_output=True, text=True)
                self.assertEqual(result.returncode, 0, result.stderr)

    def restore_fixture(self, counts=None):
        directory = self.directory / "restore-fixture"
        directory.mkdir()
        (directory / "database.dump").write_text("Mock Data database dump\n")
        (directory / "record_counts.tsv").write_text(self.counts if counts is None else counts)
        (directory / "manifest.json").write_text(json.dumps({"format_version": 1}))
        checksums = "".join(f"{sha256((directory / name).read_bytes()).hexdigest()}  {name}\n"
            for name in ("database.dump", "record_counts.tsv", "manifest.json"))
        (directory / "checksums.sha256").write_text(checksums)
        return directory

    def test_backup_counts_every_table_even_when_docker_reads_stdin(self):
        result = self.run_script("backup_local.sh")
        self.assertEqual(result.returncode, 0, result.stderr)
        backups = list((self.directory / "backups").iterdir())
        self.assertEqual(len(backups), 1)
        self.assertEqual((backups[0] / "record_counts.tsv").read_text(), self.counts)

    def fake_sleep(self):
        sleep = self.directory / "sleep"
        sleep.write_text("#!/usr/bin/env bash\nexit 0\n")
        sleep.chmod(0o755)

    def test_backup_verifier_uses_the_running_database_image(self):
        result = self.run_script("backup_local.sh")
        self.assertEqual(result.returncode, 0, result.stderr)
        calls = [json.loads(line) for line in Path(self.env["FAKE_DOCKER_LOG"]).read_text().splitlines()]
        proof = next(call for call in calls if "run" in call and "--detach" in call)
        self.assertEqual(proof[-1], "sha256:" + "c" * 64)

    def test_backup_rejects_ambiguous_database_selection_before_creating_verifier(self):
        self.env["FAKE_SOURCE_CONTAINERS"] = "b" * 64 + "\n" + "d" * 64
        result = self.run_script("backup_local.sh")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("exactly one running database", result.stderr)
        calls = [json.loads(line) for line in Path(self.env["FAKE_DOCKER_LOG"]).read_text().splitlines()]
        self.assertFalse(any("run" in call and "--detach" in call for call in calls))

    def test_backup_waits_for_tcp_query_on_intended_proof_database(self):
        self.fake_sleep()
        self.env["FAKE_PROOF_READY_AFTER"] = "3"
        directory = self.verified_backup()
        calls = self.calls()
        queries = [call for call in calls if "psql" in call and "SELECT 1" in call]
        self.assertEqual(len(queries), 3)
        for query in queries:
            self.assertEqual(query[query.index("-h") + 1], "127.0.0.1")
            self.assertEqual(query[query.index("-U") + 1], "proof")
            self.assertEqual(query[query.index("-d") + 1], "proof")
            self.assertIn("ON_ERROR_STOP=1", query)
            self.assertIn("PGCONNECT_TIMEOUT=1", query)
        first_restore = next(i for i, call in enumerate(calls) if "pg_restore" in call)
        last_query = max(i for i, call in enumerate(calls) if "SELECT 1" in call)
        self.assertLess(last_query, first_restore)
        self.assertTrue((directory / "COMPLETE").is_file())

    def test_backup_readiness_timeout_retains_partial_and_removes_only_owned_scratch(self):
        self.fake_sleep()
        self.env["FAKE_PROOF_UNAVAILABLE"] = "true"
        result = self.run_script("backup_local.sh")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Recovery verifier did not become ready", result.stderr)
        calls = self.calls()
        self.assertEqual(sum("SELECT 1" in call for call in calls), 60)
        self.assertFalse(any("pg_restore" in call for call in calls))
        self.assertEqual([call for call in calls if "rm" in call], [["rm", "--force", "a" * 64]])
        self.assertFalse(list((self.directory / "backups").glob("*/COMPLETE")))
        self.assertTrue(list((self.directory / "backups").glob("*/database.dump")))
        self.assertFalse(any(command in call for call in calls for command in ("stop", "dropdb", "up")))

    def verified_backup(self):
        result = self.run_script("backup_local.sh")
        self.assertEqual(result.returncode, 0, result.stderr)
        return next((self.directory / "backups").glob("*-market-intelligence"))

    def calls(self):
        path = self.directory / "calls.jsonl"
        return [json.loads(line) for line in path.read_text().splitlines()] if path.exists() else []

    def test_live_writes_cannot_change_completed_dump_manifest(self):
        self.env["FAKE_BETA_COUNT"] = "999"
        directory = self.verified_backup()
        self.assertIn("beta\t0\n", (directory / "record_counts.tsv").read_text())
        self.assertFalse(any("compose" in call and "psql" in call for call in self.calls()))
        scratch = next(call for call in self.calls() if "--detach" in call)
        self.assertEqual(scratch[scratch.index("--network") + 1], "none")
        self.assertNotIn("-p", scratch)
        self.assertTrue(any("rm" in call and "a" * 64 in call for call in self.calls()))

    def test_v3_restores_both_asset_stores_and_table_content(self):
        directory = self.verified_backup()
        self.env["RESTORE_ALLOW_LEGACY"] = "false"
        result = self.run_script("restore_local.sh", directory, "--yes-replace-database")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("format 3", result.stdout)

    def test_missing_completion_fails_before_stopping_services(self):
        directory = self.verified_backup()
        (directory / "COMPLETE").unlink()
        result = self.run_script("restore_local.sh", directory, "--yes-replace-database")
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse(any("dropdb" in call or "stop" in call for call in self.calls()))

    def test_backup_does_not_require_directory_rename_permission(self):
        blocked_mv = self.directory / "mv"
        blocked_mv.write_text('#!/usr/bin/env bash\nprintf "directory renames are denied\\n" >&2\nexit 1\n')
        blocked_mv.chmod(0o755)
        directory = self.verified_backup()
        self.assertTrue((directory / "COMPLETE").is_file())

    def test_equal_count_content_corruption_keeps_writers_stopped(self):
        directory = self.verified_backup()
        self.env["FAKE_CONTENT_CORRUPTED"] = "true"
        result = self.run_script("restore_local.sh", directory, "--yes-replace-database")
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse(any("up" in call for call in self.calls()))

    def test_failed_dump_is_partial_and_cannot_be_restored(self):
        self.env["FAKE_DUMP_INTERRUPTED"] = "true"
        result = self.run_script("backup_local.sh")
        self.assertNotEqual(result.returncode, 0)
        partial = next((self.directory / "backups").iterdir())
        self.assertFalse((partial / "COMPLETE").exists())
        result = self.run_script("restore_local.sh", partial, "--yes-replace-database")
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse(any("dropdb" in call or "stop" in call for call in self.calls()))

    def test_invalid_checksum_fails_before_stopping_services(self):
        directory = self.verified_backup()
        (directory / "database.dump").write_text("Corrupted Mock Data dump")
        result = self.run_script("restore_local.sh", directory, "--yes-replace-database")
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse(any("dropdb" in call or "stop" in call for call in self.calls()))

    def test_failed_restore_does_not_restart_writers(self):
        directory = self.verified_backup()
        self.env["FAKE_RESTORE_FAILED"] = "true"
        result = self.run_script("restore_local.sh", directory, "--yes-replace-database")
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse(any("up" in call for call in self.calls()))

    def test_interruption_removes_only_owned_scratch_and_retains_partial(self):
        self.env["FAKE_PROOF_INTERRUPTED"] = "true"
        result = self.run_script("backup_local.sh")
        self.assertNotEqual(result.returncode, 0)
        self.assertTrue(any("rm" in call and "a" * 64 in call for call in self.calls()))
        self.assertFalse(list((self.directory / "backups").glob("*/COMPLETE")))

    def test_restore_checks_every_manifest_table(self):
        result = self.run_script("restore_local.sh", self.restore_fixture(), "--yes-replace-database")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("Restore verified", result.stdout)

    def test_restore_quiesces_and_resumes_only_previously_running_workers(self):
        self.env["FAKE_RUNNING_SERVICES"] = "backend\nfrontend\npostgres\nscheduler\nsource_scheduler"
        result = self.run_script("restore_local.sh", self.restore_fixture(), "--yes-replace-database")
        self.assertEqual(result.returncode, 0, result.stderr)
        calls = [json.loads(line) for line in (self.directory / "calls.jsonl").read_text().splitlines()]
        stopped = next(call for call in calls if "stop" in call)
        started = next(call for call in calls if "up" in call)
        inventory = next(call for call in calls if "ps" in call)
        self.assertIn("running", inventory)
        self.assertIn("restarting", inventory)
        self.assertIn("scheduler", stopped)
        self.assertIn("source_scheduler", stopped)
        self.assertIn("scheduler", started)
        self.assertIn("source_scheduler", started)
        self.assertLess(calls.index(stopped), next(i for i, call in enumerate(calls) if "dropdb" in call))
        self.assertNotIn("postgres", stopped[stopped.index("stop") + 1:])

    def test_restore_does_not_enable_previously_stopped_workers(self):
        result = self.run_script("restore_local.sh", self.restore_fixture(), "--yes-replace-database")
        self.assertEqual(result.returncode, 0, result.stderr)
        calls = [json.loads(line) for line in (self.directory / "calls.jsonl").read_text().splitlines()]
        started = next(call for call in calls if "up" in call)
        self.assertNotIn("scheduler", started)
        self.assertNotIn("source_scheduler", started)

    def test_restore_supports_explicit_custom_worker_names(self):
        self.env.update({"DAILY_BRIEF_SERVICE": "brief_writer", "SOURCE_REFRESH_SERVICE": "source_writer",
                         "FAKE_RUNNING_SERVICES": "postgres\nbrief_writer\nsource_writer"})
        result = self.run_script("restore_local.sh", self.restore_fixture(), "--yes-replace-database")
        self.assertEqual(result.returncode, 0, result.stderr)
        calls = [json.loads(line) for line in (self.directory / "calls.jsonl").read_text().splitlines()]
        for command in ("stop", "up"):
            call = next(call for call in calls if command in call)
            self.assertIn("brief_writer", call)
            self.assertIn("source_writer", call)

    def test_restore_count_mismatch_does_not_restart_the_app(self):
        self.env["FAKE_BETA_COUNT"] = "1"
        self.env["FAKE_RUNNING_SERVICES"] = "backend\nfrontend\npostgres\nscheduler\nsource_scheduler"
        result = self.run_script("restore_local.sh", self.restore_fixture(), "--yes-replace-database")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("do not match", result.stderr)
        calls = [json.loads(line) for line in (self.directory / "calls.jsonl").read_text().splitlines()]
        self.assertFalse(any("up" in call for call in calls))
        stopped = next(call for call in calls if "stop" in call)
        self.assertIn("scheduler", stopped)
        self.assertIn("source_scheduler", stopped)

    def test_restore_rejects_an_incomplete_legacy_count_manifest(self):
        result = self.run_script("restore_local.sh", self.restore_fixture("alpha\t2\n"), "--yes-replace-database")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("do not match", result.stderr)
        calls = [json.loads(line) for line in (self.directory / "calls.jsonl").read_text().splitlines()]
        self.assertFalse(any("up" in call for call in calls))


if __name__ == "__main__":
    unittest.main()
