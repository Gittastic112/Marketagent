import tempfile
import unittest
from pathlib import Path

from scripts.check_docs import _local_target, validate


class DocumentationCheckTests(unittest.TestCase):
    def test_schema_document_matches_runtime_expected_head(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            runtime = root / "backend" / "app" / "services" / "runtime_readiness.py"
            runtime.parent.mkdir(parents=True)
            runtime.write_text('EXPECTED_MIGRATION_HEAD = "new_revision"\n', encoding="utf-8")
            (root / "docs").mkdir()
            schema = root / "docs" / "03-database-schema.md"
            schema.write_text('**Current source head:** `old_revision`.\n', encoding="utf-8")
            errors, _ = validate(root)
            self.assertTrue(any("migration head" in error for error in errors))
            schema.write_text('**Current source head:** `new_revision`.\n', encoding="utf-8")
            self.assertEqual(validate(root), ([], 0))

    def test_angle_link_with_spaces_and_optional_title(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "Current Notes.md").write_text("# Notes\n", encoding="utf-8")
            (root / "README.md").write_text('[notes](<Current Notes.md> "current notes")\n', encoding="utf-8")
            self.assertEqual(validate(root), ([], 1))

    def test_both_fence_styles_exclude_example_links(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "README.md").write_text(
                "```md\n[example](missing.md)\n```\n~~~md\n[example](missing.md)\n~~~\n",
                encoding="utf-8",
            )
            self.assertEqual(validate(root), ([], 0))

    def test_route_inventory_detects_missing_page_and_stale_count(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            page = root / "frontend" / "app" / "daily-brief" / "sources" / "[id]" / "page.tsx"
            page.parent.mkdir(parents=True)
            page.touch()
            (root / "docs").mkdir()
            inventory = root / "docs" / "09-route-inventory.md"
            inventory.write_text("0 App Router pages.\n", encoding="utf-8")
            errors, _ = validate(root)
            self.assertTrue(any("missing page" in error for error in errors))
            self.assertTrue(any("page count" in error for error in errors))
            inventory.write_text("1 App Router pages.\n[Page](../frontend/app/daily-brief/sources/[id]/page.tsx)\n", encoding="utf-8")
            self.assertEqual(validate(root), ([], 1))

    def test_root_plans_and_archive_indexes_are_checked(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            archive = root / "docs" / "archive"
            archive.mkdir(parents=True)
            (root / "plan.md").write_text("[missing](missing.md)\n", encoding="utf-8")
            (archive / "README.md").write_text("[missing](missing.md)\n", encoding="utf-8")
            errors, count = validate(root)
            self.assertEqual(count, 2)
            self.assertEqual(len(errors), 2)

    def test_nested_agent_instructions_are_checked(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            nested = root / "backend" / "app" / "schemas"
            nested.mkdir(parents=True)
            (nested / "AGENTS.md").write_text("[missing](missing.md)\n", encoding="utf-8")
            errors, count = validate(root)
            self.assertEqual(count, 1)
            self.assertEqual(errors, ["backend/app/schemas/AGENTS.md: broken link missing.md"])

    def test_handoff_context_budget_requires_archiving_history(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "docs").mkdir()
            (root / "docs" / "HANDOFF.md").write_text("history\n" * 121, encoding="utf-8")
            errors, _ = validate(root)
            self.assertTrue(any("120-line context budget" in error for error in errors))

    def test_runtime_dependency_folders_are_not_documentation(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            dependency = root / "frontend" / "node_modules" / "example"
            dependency.mkdir(parents=True)
            (dependency / "AGENTS.md").write_text("[missing](missing.md)\n", encoding="utf-8")
            self.assertEqual(validate(root), ([], 0))

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
