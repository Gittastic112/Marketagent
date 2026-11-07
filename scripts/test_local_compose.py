"""Guard host exposure without loading environment files or requiring Docker."""
from pathlib import Path
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]


class RunnerCommandFixture(unittest.TestCase):
    """Mock Data commands only; never invoke Docker or read normal settings."""

    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.directory = Path(temporary.name)
        (self.directory / "scripts").mkdir()
        (self.directory / "frontend").mkdir()
        for script in ("run_browser_workflows.sh", "verify_release_baseline.sh"):
            shutil.copyfile(ROOT / "scripts" / script, self.directory / "scripts" / script)
        binary = self.directory / "bin"
        binary.mkdir()
        for name in ("docker", "curl", "lsof", "npx", "python3"):
            command = binary / name
            command.write_text(f"#!{sys.executable}\n" + '''import json, os, signal, sys
from pathlib import Path
name = Path(sys.argv[0]).name
with open(os.environ["MOCK_COMMAND_LOG"], "a") as log:
    log.write(json.dumps({"command": name, "args": sys.argv[1:],
        "auth": {key: os.environ.get(key) for key in
            ("NEXTAUTH_SECRET", "LOCAL_AUTH_USERNAME", "LOCAL_AUTH_PASSWORD")},
        "base_url": os.environ.get("E2E_BASE_URL")}) + "\\n")
if name == "lsof":
    raise SystemExit(0 if os.environ.get("MOCK_PORT_BUSY") else 1)
stage = {"npx": "browser", "python3": "preflight"}.get(name, name)
if name == "docker":
    args = sys.argv[1:]
    if args[0] in {"container", "network", "volume"}:
        if os.environ.get("MOCK_QUERY_EXIT"):
            raise SystemExit(int(os.environ["MOCK_QUERY_EXIT"]))
        project = next(arg.split("=", 2)[-1] for arg in args if arg.startswith("label="))
        prior_calls = [json.loads(line) for line in Path(os.environ["MOCK_COMMAND_LOG"]).read_text().splitlines()]
        after_build = any(call["command"] == "docker" and "build" in call["args"] for call in prior_calls)
        if (os.environ.get("MOCK_OCCUPIED_RESOURCE") == args[0]
                and (not os.environ.get("MOCK_OCCUPIED_AFTER_BUILD") or after_build)
                and (not os.environ.get("MOCK_OCCUPIED_UNIT_ONLY") or project.endswith("-unit"))):
            print("existing-Mock-Data-resource")
        raise SystemExit(0)
    stage = args[args.index("-f") + 2]
    if stage == "run" and args[args.index("-f") + 1].endswith("docker-compose.test.yml"):
        stage = "unit-run"
    if stage == "down":
        raise SystemExit(int(os.environ.get("MOCK_DOWN_EXIT", "0")))
if stage == os.environ.get("MOCK_SIGNAL_STAGE"):
    os.kill(os.getppid(), getattr(signal, "SIG" + os.environ["MOCK_SIGNAL"]))
if stage == os.environ.get("MOCK_FAIL_STAGE"):
    raise SystemExit(int(os.environ.get("MOCK_COMMAND_EXIT", "23")))
if name == "npx":
    raise SystemExit(int(os.environ.get("MOCK_BROWSER_EXIT", "0")))
''')
            command.chmod(0o755)
        self.env = {key: value for key, value in os.environ.items()
                    if not key.startswith("MOCK_") and key not in {
                        "NEXTAUTH_SECRET", "LOCAL_AUTH_USERNAME", "LOCAL_AUTH_PASSWORD",
                        "E2E_FRONTEND_PORT", "E2E_BACKEND_PORT", "E2E_BASE_URL"}}
        self.env.update(PATH=f"{binary}{os.pathsep}{os.environ['PATH']}",
                        MOCK_COMMAND_LOG=str(self.directory / "calls.jsonl"))

    def run_script(self, script="run_browser_workflows.sh"):
        log = self.directory / "calls.jsonl"
        log.unlink(missing_ok=True)
        args = ["valuation-draft.spec.ts"] if script == "run_browser_workflows.sh" else []
        result = subprocess.run(["bash", str(self.directory / "scripts" / script), *args],
                                env=self.env, capture_output=True,
                                text=True, timeout=10)
        log = self.directory / "calls.jsonl"
        calls = [json.loads(line) for line in log.read_text().splitlines()] if log.exists() else []
        return result, calls

    @staticmethod
    def compose_calls(calls):
        return [call for call in calls if call["command"] == "docker" and call["args"][0] == "compose"]

    @staticmethod
    def project(call):
        args = call["args"]
        return args[args.index("-p") + 1]

    @staticmethod
    def cleanup_calls(calls):
        return [call for call in RunnerCommandFixture.compose_calls(calls) if "down" in call["args"]]


class BrowserRunnerTests(RunnerCommandFixture):

    def test_runs_without_normal_settings_and_uses_empty_compose_environment(self):
        result, calls = self.run_script()
        self.assertEqual(result.returncode, 0, result.stderr)
        docker = self.compose_calls(calls)
        self.assertTrue(docker)
        for call in docker:
            self.assertEqual(call["args"][:3], ["compose", "--env-file", "/dev/null"])
            self.assertEqual(call["auth"], {
                "NEXTAUTH_SECRET": "browser-check-secret-not-for-production",
                "LOCAL_AUTH_USERNAME": "browser-check-user",
                "LOCAL_AUTH_PASSWORD": "browser-check-password",
            })
        browser = next(call for call in calls if call["command"] == "npx")
        self.assertEqual(browser["base_url"], "http://127.0.0.1:13000")
        self.assertEqual(browser["args"], ["--no-install", "playwright", "test", "valuation-draft.spec.ts"])

    def test_explicit_test_settings_reach_both_services_and_browser(self):
        self.env.update(NEXTAUTH_SECRET="Mock Data test signing key", LOCAL_AUTH_USERNAME="mock-user",
                        LOCAL_AUTH_PASSWORD="Mock Data password", E2E_FRONTEND_PORT="23000",
                        E2E_BACKEND_PORT="28000")
        result, calls = self.run_script()
        self.assertEqual(result.returncode, 0, result.stderr)
        relevant = [call for call in calls if call["command"] in {"docker", "npx"}]
        for call in relevant:
            for key in ("NEXTAUTH_SECRET", "LOCAL_AUTH_USERNAME", "LOCAL_AUTH_PASSWORD"):
                self.assertEqual(call["auth"][key], self.env[key])
        browser = next(call for call in calls if call["command"] == "npx")
        self.assertEqual(browser["base_url"], "http://127.0.0.1:23000")

    def test_port_conflict_exits_without_destroying_existing_test_services(self):
        self.env.update(MOCK_PORT_BUSY="1", NEXTAUTH_SECRET="Mock Data test signing key",
                        LOCAL_AUTH_USERNAME="mock-user", LOCAL_AUTH_PASSWORD="Mock Data password")
        result, calls = self.run_script()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("already allocated", result.stderr)
        self.assertFalse(any(call["command"] == "docker" for call in calls))

    def test_failed_browser_run_preserves_failure_and_cleans_up_test_project(self):
        self.env["MOCK_BROWSER_EXIT"] = "7"
        result, calls = self.run_script()
        self.assertEqual(result.returncode, 7, result.stderr)
        self.assertEqual(calls[-1]["command"], "docker")
        self.assertIn("down", calls[-1]["args"])
        self.assertRegex(self.project(calls[-1]), r"^market-intel-e2e-\d+-\d+-\d+$")
        self.assertEqual(len(self.cleanup_calls(calls)), 1)

    def test_each_run_owns_a_new_project_and_checks_all_existing_resource_kinds(self):
        projects = []
        for _ in range(2):
            result, calls = self.run_script()
            self.assertEqual(result.returncode, 0, result.stderr)
            compose = self.compose_calls(calls)
            project = self.project(compose[0])
            projects.append(project)
            self.assertTrue(all(self.project(call) == project for call in compose))
            checks = [call for call in calls if call["command"] == "docker" and call["args"][0] != "compose"]
            self.assertEqual({call["args"][0] for call in checks}, {"container", "network", "volume"})
            for call in checks:
                self.assertIn(f"label=com.docker.compose.project={project}", call["args"])
            self.assertIn("--all", next(call for call in checks if call["args"][0] == "container")["args"])
            self.assertEqual(len(self.cleanup_calls(calls)), 1)
            self.assertEqual(calls[-1], self.cleanup_calls(calls)[0])
        self.assertNotEqual(*projects)

    def test_existing_project_resources_are_never_adopted_or_deleted(self):
        for kind in ("container", "network", "volume"):
            with self.subTest(kind=kind):
                self.env["MOCK_OCCUPIED_RESOURCE"] = kind
                result, calls = self.run_script()
                self.assertNotEqual(result.returncode, 0)
                self.assertIn("refusing", result.stderr.lower())
                self.assertFalse(self.compose_calls(calls))

    def test_resource_inventory_failure_stops_before_any_mutation(self):
        self.env["MOCK_QUERY_EXIT"] = "31"
        result, calls = self.run_script()
        self.assertEqual(result.returncode, 31)
        self.assertFalse(self.compose_calls(calls))

    def test_resources_appearing_during_build_are_not_adopted_or_cleaned(self):
        self.env.update(MOCK_OCCUPIED_RESOURCE="network", MOCK_OCCUPIED_AFTER_BUILD="1")
        result, calls = self.run_script()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("refusing", result.stderr.lower())
        compose = self.compose_calls(calls)
        self.assertEqual(len(compose), 1)
        self.assertIn("build", compose[0]["args"])
        self.assertFalse(self.cleanup_calls(calls))

    def test_failed_build_never_cleans_up_a_project_it_did_not_start(self):
        self.env["MOCK_FAIL_STAGE"] = "build"
        result, calls = self.run_script()
        self.assertEqual(result.returncode, 23)
        self.assertFalse(self.cleanup_calls(calls))
        self.assertFalse(any("up" in call["args"] for call in self.compose_calls(calls)))

    def test_partial_startup_is_cleaned_once_without_masking_failure(self):
        self.env.update(MOCK_FAIL_STAGE="up", MOCK_DOWN_EXIT="9")
        result, calls = self.run_script()
        self.assertEqual(result.returncode, 23)
        self.assertEqual(len(self.cleanup_calls(calls)), 1)

    def test_signals_exit_with_signal_status_and_cleanup_only_once(self):
        for signal_name, status in (("INT", 130), ("TERM", 143)):
            with self.subTest(signal=signal_name):
                self.env.update(MOCK_SIGNAL_STAGE="browser", MOCK_SIGNAL=signal_name, MOCK_DOWN_EXIT="9")
                result, calls = self.run_script()
                self.assertEqual(result.returncode, status, result.stderr)
                self.assertEqual(len(self.cleanup_calls(calls)), 1)


class ReleaseRunnerTests(RunnerCommandFixture):

    def run_script(self, script="verify_release_baseline.sh"):
        return super().run_script(script)

    def test_preflight_failure_does_not_touch_docker(self):
        self.env["MOCK_FAIL_STAGE"] = "preflight"
        result, calls = self.run_script()
        self.assertEqual(result.returncode, 23)
        self.assertFalse(any(call["command"] == "docker" for call in calls))

    def test_existing_resources_in_either_project_block_before_build_or_cleanup(self):
        for unit_only in ("", "1"):
            for kind in ("container", "network", "volume"):
                with self.subTest(unit_only=unit_only, kind=kind):
                    self.env.update(MOCK_OCCUPIED_RESOURCE=kind, MOCK_OCCUPIED_UNIT_ONLY=unit_only)
                    result, calls = self.run_script()
                    self.assertNotEqual(result.returncode, 0)
                    self.assertIn("refusing", result.stderr.lower())
                    self.assertFalse(self.compose_calls(calls))

    def test_failed_build_does_not_cleanup_unstarted_projects(self):
        self.env["MOCK_FAIL_STAGE"] = "build"
        result, calls = self.run_script()
        self.assertEqual(result.returncode, 23)
        self.assertFalse(self.cleanup_calls(calls))

    def test_unit_resources_appearing_during_build_leave_both_projects_unowned(self):
        self.env.update(MOCK_OCCUPIED_RESOURCE="volume", MOCK_OCCUPIED_UNIT_ONLY="1",
                        MOCK_OCCUPIED_AFTER_BUILD="1")
        result, calls = self.run_script()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("refusing", result.stderr.lower())
        compose = self.compose_calls(calls)
        self.assertEqual(len(compose), 1)
        self.assertIn("build", compose[0]["args"])
        self.assertFalse(self.cleanup_calls(calls))

    def test_failed_unit_run_preserves_error_and_cleans_only_both_owned_projects(self):
        self.env.update(MOCK_FAIL_STAGE="unit-run", MOCK_DOWN_EXIT="9")
        result, calls = self.run_script()
        self.assertEqual(result.returncode, 23)
        cleanup = self.cleanup_calls(calls)
        self.assertEqual(len(cleanup), 2)
        unit = next(call for call in self.compose_calls(calls) if "backend-tests" in call["args"])
        unit_project = self.project(unit)
        self.assertTrue(unit_project.endswith("-unit"))
        self.assertEqual({self.project(call) for call in cleanup}, {unit_project, unit_project.removesuffix("-unit")})

    def test_release_calls_keep_empty_environment_and_use_unique_owned_projects(self):
        projects = []
        for _ in range(2):
            result, calls = self.run_script()
            self.assertEqual(result.returncode, 0, result.stderr)
            compose = self.compose_calls(calls)
            project = self.project(compose[0])
            projects.append(project)
            self.assertRegex(project, r"^market-intel-release-check-\d+-\d+-\d+$")
            for call in compose:
                self.assertEqual(call["args"][:3], ["compose", "--env-file", "/dev/null"])
                self.assertIn(self.project(call), {project, project + "-unit"})
            self.assertEqual({self.project(call) for call in self.cleanup_calls(calls)}, {project, project + "-unit"})
        self.assertNotEqual(*projects)

    def test_signal_before_or_after_start_preserves_status_and_ownership(self):
        for stage, cleanup_count in (("preflight", 0), ("up", 1), ("unit-run", 2)):
            with self.subTest(stage=stage):
                self.env.update(MOCK_SIGNAL_STAGE=stage, MOCK_SIGNAL="TERM")
                result, calls = self.run_script()
                self.assertEqual(result.returncode, 143, result.stderr)
                self.assertEqual(len(self.cleanup_calls(calls)), cleanup_count)


class LocalComposeTests(unittest.TestCase):
    def test_postgres_security_build_is_shared_by_runtime_browser_and_recovery(self):
        for name in ("docker-compose.yml", "docker-compose.e2e.yml", "docker-compose.recovery.yml"):
            with self.subTest(compose=name):
                source = (ROOT / name).read_text()
                self.assertIn("image: market-intelligence-postgres:local\n    build:\n      context: ./docker/postgres", source)
        postgres = (ROOT / "docker/postgres/Dockerfile").read_text()
        self.assertRegex(postgres, r"FROM postgres:16\.15-trixie@sha256:[a-f0-9]{64}")
        self.assertIn("/etc/apt/sources.list.d/pgdg.list", postgres)
        self.assertNotIn("COPY", postgres)
        self.assertLess(postgres.index("ge 3.0.4"), postgres.index("apt-get"))
        self.assertIn("inspect --format '{{.Image}}'", (ROOT / "scripts/backup_local.sh").read_text())
        self.assertIn("build postgres-e2e backend-e2e", (ROOT / "scripts/drill_backup_restore.sh").read_text())

    def test_security_snapshots_align_and_http_bootstrap_cannot_retry_vulnerable_apt(self):
        snapshots = set()
        for name in ("backend/Dockerfile", "frontend/Dockerfile", "docker/postgres/Dockerfile"):
            source = (ROOT / name).read_text()
            snapshots.update(re.findall(r"snapshot\.debian\.org/archive/[^/]+/(\d{8}T\d{6}Z)", source))
            self.assertIn("APT::Update::Error-Mode=any", source)
            self.assertNotIn("--allow-unauthenticated", source)
            self.assertNotIn("trusted=yes", source)
            self.assertIn("dpkg --compare-versions", source)
        self.assertEqual(snapshots, {"20261107T180000Z"})
        frontend = (ROOT / "frontend/Dockerfile").read_text()
        before_fixed = frontend.split("ge 2.6.2", 1)[0]
        self.assertEqual(before_fixed.count("Acquire::Retries=0"), 2)
        self.assertNotIn("Acquire::Retries=3", before_fixed)

    def test_normal_services_require_private_database_password(self):
        source = (ROOT / "docker-compose.yml").read_text()
        self.assertNotIn("marketintel_password", source)
        self.assertNotIn("admin_password", source)
        self.assertEqual(source.count("${POSTGRES_PASSWORD:?Set POSTGRES_PASSWORD privately before starting services}"), 4)
        self.assertIn("PGADMIN_DEFAULT_PASSWORD: ${PGADMIN_DEFAULT_PASSWORD:-}", source)

    def test_all_published_ports_are_explicitly_loopback_only(self):
        for name, expected in (("docker-compose.yml", 4), ("docker-compose.e2e.yml", 2)):
            with self.subTest(compose=name):
                source = (ROOT / name).read_text()
                blocks = re.findall(r"(?m)^    ports:\n((?:      - [^\n]+\n)+)", source)
                # Reject unrecognized long syntax instead of silently skipping it.
                self.assertEqual(len(blocks), source.count("    ports:"))
                ports = [line.strip()[2:].strip('"\'') for block in blocks for line in block.splitlines()]
                self.assertEqual(len(ports), expected)
                for port in ports:
                    self.assertTrue(port.startswith("127.0.0.1:"), f"{name} exposes a non-loopback port")

    def test_dev_and_unit_test_overrides_do_not_publish_additional_ports(self):
        for name in ("docker-compose.dev.yml", "docker-compose.test.yml", "docker-compose.tools.yml", "docker-compose.recovery.yml"):
            with self.subTest(compose=name):
                self.assertNotRegex((ROOT / name).read_text(), r"(?m)^\s*ports:")

    def test_workers_wait_for_migrated_backend_without_running_migrations(self):
        source = (ROOT / "docker-compose.yml").read_text()
        for worker, module in (("scheduler", "daily_brief_scheduler"),
                               ("source_scheduler", "valuation_source_scheduler")):
            with self.subTest(worker=worker):
                # Select until the next service, not an indented service property.
                block = re.split(r"\n  [a-z_]+:\n", source.split(f"\n  {worker}:\n", 1)[1])[0]
                self.assertNotIn("alembic upgrade", block)
                self.assertIn(f'command: ["python", "-m", "app.workers.{module}"]', block)
                self.assertRegex(block, r"depends_on:\n      backend:\n        condition: service_healthy")

    def test_admin_is_optional_bounded_and_does_not_restart_with_docker(self):
        source = (ROOT / "docker-compose.yml").read_text().split("\n  pgadmin:\n", 1)[1]
        self.assertIn('profiles: ["admin"]', source)
        self.assertIn('restart: "no"', source)
        self.assertIn("mem_limit: 512m", source)

    def test_development_reloads_only_application_code_and_keeps_data_readonly(self):
        source = (ROOT / "docker-compose.dev.yml").read_text()
        self.assertIn("--reload-dir backend/app", source)
        self.assertIn("./data:/workspace/data:ro", source)
        self.assertIn("mem_limit: 2g", source)

    def test_test_dependencies_and_targets_are_separate_from_runtime(self):
        runtime = (ROOT / "backend/requirements.txt").read_text()
        test = (ROOT / "backend/requirements-test.txt").read_text()
        self.assertNotRegex(runtime, r"(?m)^pytest[=\[]")
        self.assertIn("-r requirements.txt", test)
        self.assertRegex(test, r"(?m)^pytest==")
        dockerfile = (ROOT / "backend/Dockerfile").read_text()
        runtime_source, test_source = dockerfile.split("FROM application AS test", 1)
        self.assertNotIn("COPY backend backend", runtime_source)
        self.assertNotIn("COPY backend/tests", runtime_source)
        self.assertIn("COPY backend/tests backend/tests", test_source)
        self.assertTrue(dockerfile.rstrip().endswith("FROM application AS runtime"))
        for compose in ("docker-compose.test.yml", "docker-compose.e2e.yml"):
            self.assertRegex((ROOT / compose).read_text(), r"dockerfile: backend/Dockerfile\n      target: test")

    def test_backend_context_is_allowlisted_and_excludes_nested_secrets(self):
        patterns = [line.strip() for line in (ROOT / ".dockerignore").read_text().splitlines()
                    if line.strip() and not line.startswith("#")]
        self.assertEqual(patterns[0], "**")
        includes = {line for line in patterns if line.startswith("!")}
        self.assertEqual(includes, {"!alembic.ini", "!pyproject.toml", "!backend/", "!backend/Dockerfile",
                                    "!backend/requirements*.txt", "!backend/requirements*.lock",
                                    "!backend/app/", "!backend/app/**", "!backend/alembic/", "!backend/alembic/**",
                                    "!backend/scripts/", "!backend/scripts/**", "!backend/tests/", "!backend/tests/**",
                                    "!scripts/", "!scripts/**"})
        for pattern in ("**/.env", "**/.env.*", "**/.venv*", "**/venv", "**/__pycache__"):
            self.assertIn(pattern, patterns)
            self.assertGreater(patterns.index(pattern), patterns.index("!scripts/**"))


if __name__ == "__main__":
    unittest.main()
