"""Guard host exposure without loading environment files or requiring Docker."""
from pathlib import Path
import json
import os
import re
import shutil
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]


class BrowserRunnerTests(unittest.TestCase):
    """Mock Data commands only; never invoke Docker or read normal settings."""

    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.directory = Path(temporary.name)
        (self.directory / "scripts").mkdir()
        (self.directory / "frontend").mkdir()
        shutil.copyfile(ROOT / "scripts/run_browser_workflows.sh", self.directory / "scripts/run_browser_workflows.sh")
        binary = self.directory / "bin"
        binary.mkdir()
        for name in ("docker", "curl", "lsof", "npx"):
            command = binary / name
            command.write_text('''#!/usr/bin/env python3
import json, os, sys
from pathlib import Path
name = Path(sys.argv[0]).name
with open(os.environ["MOCK_COMMAND_LOG"], "a") as log:
    log.write(json.dumps({"command": name, "args": sys.argv[1:],
        "auth": {key: os.environ.get(key) for key in
            ("NEXTAUTH_SECRET", "LOCAL_AUTH_USERNAME", "LOCAL_AUTH_PASSWORD")},
        "base_url": os.environ.get("E2E_BASE_URL")}) + "\\n")
if name == "lsof":
    raise SystemExit(0 if os.environ.get("MOCK_PORT_BUSY") else 1)
if name == "npx":
    raise SystemExit(int(os.environ.get("MOCK_BROWSER_EXIT", "0")))
''')
            command.chmod(0o755)
        self.env = {key: value for key, value in os.environ.items()
                    if key not in {"NEXTAUTH_SECRET", "LOCAL_AUTH_USERNAME", "LOCAL_AUTH_PASSWORD",
                                   "E2E_FRONTEND_PORT", "E2E_BACKEND_PORT", "E2E_BASE_URL"}}
        self.env.update(PATH=f"{binary}{os.pathsep}{os.environ['PATH']}",
                        MOCK_COMMAND_LOG=str(self.directory / "calls.jsonl"))

    def run_script(self):
        result = subprocess.run(["bash", str(self.directory / "scripts/run_browser_workflows.sh"),
                                 "valuation-draft.spec.ts"], env=self.env, capture_output=True,
                                text=True, timeout=10)
        log = self.directory / "calls.jsonl"
        calls = [json.loads(line) for line in log.read_text().splitlines()] if log.exists() else []
        return result, calls

    def test_runs_without_normal_settings_and_uses_empty_compose_environment(self):
        result, calls = self.run_script()
        self.assertEqual(result.returncode, 0, result.stderr)
        docker = [call for call in calls if call["command"] == "docker"]
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
        self.assertIn("market-intel-e2e", calls[-1]["args"])


class LocalComposeTests(unittest.TestCase):
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
