"""Exercise scanner isolation and evidence retention without Docker or a network."""

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parent / "scan_container_images.sh"
FAKE_DOCKER = r'''
import json
import os
import sys
from pathlib import Path

args = sys.argv[1:]
log = Path(os.environ["FAKE_DOCKER_LOG"])
with log.open("a") as handle:
    handle.write(json.dumps(args) + "\n")
if args[:2] == ["image", "save"]:
    Path(args[args.index("-o") + 1]).write_bytes(b"isolated image archive")
    raise SystemExit(0)
assert args[0] == "run", args
mounts = {}
for index, arg in enumerate(args):
    if arg == "-v":
        host, guest, *_ = args[index + 1].split(":")
        mounts[guest] = Path(host)
assert set(mounts) == {"/input", "/reports", "/cache"}, mounts
assert args[args.index("--cache-dir") + 1] == "/cache"
assert "--read-only" in args and "--cap-drop" in args
assert not any("docker.sock" in arg for arg in args)
cache = mounts["/cache"]
(cache / "trivy.db").write_bytes(b"regenerable database")
output = mounts["/reports"] / Path(args[args.index("--output") + 1]).name
output.write_text(json.dumps({
    "Metadata": {"OS": {"Family": "debian"}},
    "Results": [{"Class": "os-pkgs", "Packages": [{"Name": "fixture"}], "Vulnerabilities": []}],
}))
if output.name == os.environ.get("FAIL_REPORT"):
    raise SystemExit(42)
'''


class ScannerWorkflowTests(unittest.TestCase):
    def run_scan(self, fail_report=""):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            scratch, reports = root / "scratch", root / "reports"
            scratch.mkdir()
            fake = root / "docker-fixture"
            fake.write_text(f"#!{sys.executable}\n" + FAKE_DOCKER)
            fake.chmod(0o700)
            log = root / "docker.jsonl"
            result = subprocess.run(
                ["bash", str(SCRIPT), "fixture:first", "fixture:second"],
                env={**os.environ, "DOCKER_BIN": str(fake), "REPORT_DIR": str(reports),
                     "TMPDIR": str(scratch), "FAKE_DOCKER_LOG": str(log), "FAIL_REPORT": fail_report},
                capture_output=True, text=True, check=False,
            )
            self.assertEqual(result.returncode, 42 if fail_report else 0, result.stderr + result.stdout)
            self.assertEqual(list(scratch.iterdir()), [], "Temporary archives and databases must be removed.")
            self.assertEqual(sorted(file.name for file in reports.iterdir()), ["image-1.json", "image-2.json"])
            for file in reports.iterdir():
                self.assertEqual(json.loads(file.read_text())["Metadata"]["OS"]["Family"], "debian")
            calls = [json.loads(line) for line in log.read_text().splitlines()]
            runs = [args for args in calls if args[0] == "run"]
            self.assertEqual(len(runs), 2)
            cache_mounts = [next(arg for arg in args if arg.endswith(":/cache")) for args in runs]
            self.assertEqual(cache_mounts[0], cache_mounts[1], "Reuse one database within an invocation.")
            self.assertFalse(Path(cache_mounts[0].removesuffix(":/cache")).exists())

    def test_success_removes_cache_and_preserves_reports(self):
        self.run_scan()

    def test_failure_removes_cache_and_preserves_partial_evidence(self):
        self.run_scan("image-2.json")


if __name__ == "__main__":
    unittest.main()
