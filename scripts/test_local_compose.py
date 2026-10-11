"""Guard host exposure without loading environment files or requiring Docker."""
from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parents[1]


class LocalComposeTests(unittest.TestCase):
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
        for name in ("docker-compose.dev.yml", "docker-compose.test.yml", "docker-compose.tools.yml"):
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
        self.assertEqual(includes, {"!alembic.ini", "!pyproject.toml", "!backend/", "!backend/**",
                                    "!scripts/", "!scripts/**"})
        for pattern in ("**/.env", "**/.env.*", "**/.venv*", "**/venv", "**/__pycache__"):
            self.assertIn(pattern, patterns)
            self.assertGreater(patterns.index(pattern), patterns.index("!scripts/**"))


if __name__ == "__main__":
    unittest.main()
