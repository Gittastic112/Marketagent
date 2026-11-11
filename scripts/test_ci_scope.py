"""CI must skip expensive jobs only for an unambiguous documentation change."""

import subprocess
import tempfile
import unittest
from pathlib import Path

from scripts.ci_scope import FULL_JOBS, changed_paths, classify, gate_errors


class ScopeTests(unittest.TestCase):
    def test_documentation_only_change(self):
        self.assertFalse(classify(["README.md", "docs/architecture.md", "frontend/AGENTS.md"], "pull_request", "refs/pull/1/merge")[0])

    def test_runtime_and_unknown_paths_keep_every_check(self):
        for file in ("frontend/app/page.tsx", "backend/app/main.py", "scripts/check_docs.py", ".github/workflows/ci.yml", "docs/contract.json", "package-lock.json", "unknown.md", "damodaran_knowledge_base_v1/reference/model.md"):
            with self.subTest(file=file):
                self.assertTrue(classify(["README.md", file], "pull_request", "refs/pull/1/merge")[0])

    def test_missing_comparison_empty_diff_and_non_branch_events_run_full(self):
        for paths, event, ref in ((None, "push", "refs/heads/main"), ([], "push", "refs/heads/main"), (["README.md"], "push", "refs/tags/v1"), (["README.md"], "workflow_dispatch", "refs/heads/main"), (["README.md"], "unknown", "refs/heads/main")):
            with self.subTest(paths=paths, event=event, ref=ref):
                self.assertTrue(classify(paths, event, ref)[0])

    def test_invalid_paths_cannot_be_documentation(self):
        for file in ("../docs/x.md", "/docs/x.md", "docs/../backend/README.md", "docs/x.md\nbackend/app.py"):
            self.assertTrue(classify([file], "push", "refs/heads/main")[0])

    def test_push_uses_every_commit_in_the_supplied_range(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            def git(*args):
                return subprocess.check_output(["git", "-c", "core.hooksPath=/dev/null", "-C", directory, *args], text=True).strip()
            git("init", "-q")
            git("config", "user.name", "CI fixture")
            git("config", "user.email", "fixture@example.invalid")
            (root / "app.py").write_text("original\n")
            git("add", "app.py")
            git("commit", "-qm", "baseline")
            before = git("rev-parse", "HEAD")
            (root / "app.py").write_text("changed\n")
            git("commit", "-qam", "runtime change")
            (root / "README.md").write_text("# Guide\n")
            git("add", "README.md")
            git("commit", "-qm", "documentation")
            paths = changed_paths(before, git("rev-parse", "HEAD"), cwd=root)
            self.assertEqual(set(paths), {"app.py", "README.md"})
            self.assertTrue(classify(paths, "push", "refs/heads/main")[0])
            git("mv", "app.py", "retired.md")
            git("commit", "-qm", "rename")
            renamed = changed_paths(git("rev-parse", "HEAD^"), git("rev-parse", "HEAD"), cwd=root)
            self.assertIn("app.py", renamed)
            self.assertTrue(classify(renamed, "pull_request", "refs/pull/1/merge")[0])

    def test_missing_revisions_fail_closed(self):
        self.assertIsNone(changed_paths("0" * 40, "1" * 40))
        self.assertIsNone(changed_paths("not-a-revision", "1" * 40))


class GateTests(unittest.TestCase):
    def results(self, full=True):
        return {"repository-checks": {"result": "success", "outputs": {"full_ci": str(full).lower()}}, **{name: {"result": "success" if full else "skipped"} for name in FULL_JOBS}}

    def test_full_success_and_documentation_success(self):
        self.assertEqual(gate_errors(self.results()), [])
        self.assertEqual(gate_errors(self.results(False)), [])

    def test_failed_cancelled_missing_or_skipped_required_job_fails(self):
        for status in ("failure", "cancelled", "skipped", ""):
            results = self.results()
            results["browser-quality-gate"]["result"] = status
            self.assertTrue(gate_errors(results))
        results = self.results()
        del results["recovery-quality-gate"]
        self.assertTrue(gate_errors(results))

    def test_scope_failure_or_missing_output_cannot_pass(self):
        results = self.results(False)
        results["repository-checks"]["result"] = "failure"
        self.assertTrue(gate_errors(results))
        results = self.results(False)
        results["repository-checks"]["outputs"] = {}
        self.assertTrue(gate_errors(results))


if __name__ == "__main__":
    unittest.main()
