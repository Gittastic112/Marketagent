"""Exercise shell backup/count verification with a fake Docker executable only."""
from hashlib import sha256
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
COUNTS = "alpha\t2\nbeta\t0\ngamma\t3\n"
FAKE_DOCKER = '''#!/usr/bin/env python3
import json, os, sys
from pathlib import Path
args = sys.argv[1:]
with open(os.environ["FAKE_DOCKER_LOG"], "a") as log:
    log.write(json.dumps(args) + "\\n")
if "pg_dump" in args:
    print("Mock Data database dump")
elif "pg_restore" in args:
    sys.stdin.buffer.read()
elif "psql" in args:
    query = args[args.index("-c") + 1]
    if "pg_tables" in query:
        print("alpha\\nbeta\\ngamma")
    elif "octet_length" in query:
        print("1\\t12")
    else:
        # Docker exec -T can consume the surrounding shell loop's stdin.
        sys.stdin.buffer.read()
        table = query.split('"')[1]
        print({"alpha":2, "beta":int(os.environ.get("FAKE_BETA_COUNT", "0")), "gamma":3}[table])
elif "alembic" in args:
    print("mock_revision (head)")
elif "ps" in args:
    print(os.environ.get("FAKE_RUNNING_SERVICES", "backend\\nfrontend\\npostgres"))
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
            "COMPOSE_PROJECT_NAME": "mock-backup-test", "POSTGRES_DB": "mock_database"}

    def run_script(self, name, *args):
        return subprocess.run(["bash", str(ROOT / "scripts" / name), *map(str, args)],
            env=self.env, capture_output=True, text=True, timeout=30)

    def restore_fixture(self, counts=COUNTS):
        directory = self.directory / "restore-fixture"
        directory.mkdir()
        (directory / "database.dump").write_text("Mock Data database dump\n")
        (directory / "record_counts.tsv").write_text(counts)
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
        self.assertEqual((backups[0] / "record_counts.tsv").read_text(), COUNTS)

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
