import tempfile
import unittest
from pathlib import Path

from check_docs import _local_target, validate


class DocumentationCheckTests(unittest.TestCase):
    def test_local_target_resolves_relative_path(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "docs" / "README.md"
            source.parent.mkdir()
            source.write_text("", encoding="utf-8")
            self.assertEqual(
                _local_target(source, "../README.md"),
                (root / "README.md").resolve(),
            )

    def test_validate_reports_broken_active_link(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "docs").mkdir()
            (root / "damodaran_knowledge_base_v1").mkdir()
            (root / "README.md").write_text(
                "[missing](docs/missing.md)\n",
                encoding="utf-8",
            )
            (root / "AGENTS.md").write_text("# Agent\n", encoding="utf-8")
            errors, checked_links = validate(root)
            self.assertEqual(checked_links, 1)
            self.assertEqual(errors, ["README.md: broken link docs/missing.md"])

    def test_validate_ignores_archived_markdown(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            archive = root / "docs" / "archive"
            archive.mkdir(parents=True)
            (root / "damodaran_knowledge_base_v1").mkdir()
            (root / "README.md").write_text("# Root\n", encoding="utf-8")
            (root / "AGENTS.md").write_text("# Agent\n", encoding="utf-8")
            (archive / "old.md").write_text("[missing](missing.md)\n", encoding="utf-8")
            errors, checked_links = validate(root)
            self.assertEqual(checked_links, 0)
            self.assertEqual(errors, [])

    def test_validate_reports_broken_inline_markdown_path(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "docs").mkdir()
            (root / "damodaran_knowledge_base_v1").mkdir()
            (root / "README.md").write_text("Read `docs/missing.md`.\n", encoding="utf-8")
            (root / "AGENTS.md").write_text("# Agent\n", encoding="utf-8")
            errors, checked_links = validate(root)
            self.assertEqual(checked_links, 1)
            self.assertEqual(
                errors,
                ["README.md: broken inline Markdown path docs/missing.md"],
            )


if __name__ == "__main__":
    unittest.main()
