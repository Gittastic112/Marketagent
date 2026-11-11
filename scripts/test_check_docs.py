import tempfile
import unittest
from pathlib import Path

from scripts.check_docs import _local_target, validate


class DocumentationCheckTests(unittest.TestCase):
    def test_command_inventory_reports_missing_tools_and_ignores_test_helpers(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            scripts = root / "scripts"
            scripts.mkdir()
            for name in ("check.py", "recover.sh", "inventory.sql", "test_check.py", "__init__.py"):
                (scripts / name).touch()
            guide = scripts / "README.md"
            guide.write_text("[check](check.py)\n[inventory](inventory.sql)\n", encoding="utf-8")
            errors, _ = validate(root)
            self.assertEqual(errors, ["scripts/README.md: unmapped command scripts/recover.sh"])
            guide.write_text("[check](check.py)\n[inventory](inventory.sql)\n[recover](recover.sh)\n", encoding="utf-8")
            self.assertEqual(validate(root), ([], 3))

    def test_backend_commands_require_an_inventory(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            scripts = root / "backend" / "scripts"
            scripts.mkdir(parents=True)
            (scripts / "probe.py").touch()
            self.assertEqual(validate(root)[0], ["backend/scripts/README.md: missing command inventory"])
            (scripts / "README.md").write_text("[probe](probe.py)\n", encoding="utf-8")
            self.assertEqual(validate(root), ([], 1))

    def test_backend_command_guide_links_are_checked(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            scripts = root / "backend" / "scripts"
            scripts.mkdir(parents=True)
            (scripts / "README.md").write_text("[missing](missing.md)\n", encoding="utf-8")
            self.assertEqual(validate(root)[0], ["backend/scripts/README.md: broken link missing.md"])

    def test_styles_guide_links_are_checked(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            styles = root / "frontend" / "styles"
            styles.mkdir(parents=True)
            (styles / "README.md").write_text("[missing](missing.css)\n", encoding="utf-8")
            self.assertEqual(validate(root)[0], ["frontend/styles/README.md: broken link missing.css"])

    def test_backend_api_map_detects_missing_module_and_stale_count(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            routers = root / "backend" / "app" / "api" / "routers"
            routers.mkdir(parents=True)
            (routers / "companies.py").touch()
            (routers / "__init__.py").touch()
            inventory = root / "docs" / "reference" / "api-map.md"
            inventory.parent.mkdir(parents=True)
            inventory.write_text("0 HTTP router modules.\n", encoding="utf-8")
            errors, _ = validate(root)
            self.assertTrue(any("unmapped HTTP router" in error for error in errors))
            self.assertTrue(any("router count" in error for error in errors))
            inventory.write_text("1 HTTP router modules.\n[Companies](../../backend/app/api/routers/companies.py)\n", encoding="utf-8")
            self.assertEqual(validate(root), ([], 1))

    def test_workstream_receipts_are_historical_but_their_index_is_checked(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            evidence = root / "docs" / "workstreams" / "evidence"
            evidence.mkdir(parents=True)
            (evidence / "old-review.md").write_text("[historical](missing.md)\n", encoding="utf-8")
            (evidence / "README.md").write_text("[index](missing.md)\n", encoding="utf-8")
            self.assertEqual(validate(root)[0], ["docs/workstreams/evidence/README.md: broken link missing.md"])

    def test_directory_guides_and_github_policies_are_checked(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for folder in ("backend", "scripts", "data", "docker", ".github"):
                (root / folder).mkdir()
                (root / folder / "README.md").write_text("[missing](missing.md)\n", encoding="utf-8")
            (root / ".github" / "SECURITY.md").write_text("[missing](missing.md)\n", encoding="utf-8")
            errors, count = validate(root)
            self.assertEqual(count, 6)
            self.assertEqual(len(errors), 6)

    def test_local_helper_copies_do_not_enter_application_docs(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            copied = root / "skills" / "spreadsheets"
            copied.mkdir(parents=True)
            (copied / "SKILL.md").write_text("[local tool](missing.md)\n", encoding="utf-8")
            maintained = root / "skills" / "security-review"
            maintained.mkdir()
            (maintained / "SKILL.md").write_text("[missing](missing.md)\n", encoding="utf-8")
            errors, count = validate(root)
            self.assertEqual(count, 1)
            self.assertEqual(errors, ["skills/security-review/SKILL.md: broken link missing.md"])

    def test_missing_local_heading_is_reported(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "README.md").write_text("[guide](guide.md#removed-heading)\n", encoding="utf-8")
            (root / "guide.md").write_text("# Actual heading\n", encoding="utf-8")
            errors, count = validate(root)
            self.assertEqual(count, 1)
            self.assertEqual(errors, ["README.md: broken anchor guide.md#removed-heading"])

    def test_same_page_duplicate_and_explicit_anchors(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "README.md").write_text(
                '# Setup & `review`\n# Setup & `review`\n<a id="stable"></a>\n'
                '[first](#setup--review)\n[second](#setup--review-1)\n[explicit](#stable)\n',
                encoding="utf-8",
            )
            self.assertEqual(validate(root), ([], 0))

    def test_fenced_headings_do_not_supply_anchors(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "README.md").write_text("```md\n# Example\n```\n[bad](#example)\n", encoding="utf-8")
            self.assertEqual(validate(root)[0], ["README.md: broken anchor #example"])

    def test_external_and_code_line_fragments_are_not_markdown_headings(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "example.py").write_text("pass\n", encoding="utf-8")
            (root / "README.md").write_text(
                "[code](example.py#L1)\n[web](https://example.com/guide#heading)\n", encoding="utf-8"
            )
            self.assertEqual(validate(root), ([], 1))

    def test_schema_document_matches_runtime_expected_head(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            runtime = root / "backend" / "app" / "services" / "runtime_readiness.py"
            runtime.parent.mkdir(parents=True)
            runtime.write_text('EXPECTED_MIGRATION_HEAD = "new_revision"\n', encoding="utf-8")
            (root / "docs").mkdir()
            schema = root / "docs" / "database-schema.md"
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
            inventory = root / "docs" / "route-inventory.md"
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
