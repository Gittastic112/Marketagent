#!/usr/bin/env python3
"""Validate active documentation paths, heading links, and repository maps."""

from __future__ import annotations

import ast
import re
import os
import sys
from pathlib import Path
from urllib.parse import unquote


ROOT = Path(__file__).resolve().parents[1]
LINK_PATTERN = re.compile(r"\[[^\]]+\]\(([^)]+)\)")
INLINE_MARKDOWN_PATH_PATTERN = re.compile(r"`([^`\n]*\.md)`")
FENCE_PATTERN = re.compile(r"^[ \t]*(?P<fence>`{3,}|~{3,})[^\n]*\n.*?^[ \t]*(?P=fence)[ \t]*$", re.MULTILINE | re.DOTALL)
CONTEXT_LINE_BUDGETS = {
    "README.md": 100,
    "AGENTS.md": 160,
    "backend/AGENTS.md": 160,
    "frontend/AGENTS.md": 120,
    "docs/README.md": 80,
    "docs/HANDOFF.md": 120,
    "docs/current-state.md": 180,
    "docs/architecture.md": 180,
    "docs/local-development.md": 140,
    "docs/limitations.md": 240,
    "docs/workstreams/plan.md": 100,
    "docs/roadmaps/review-decisions.md": 85,
    "docs/reference/api-map.md": 100,
    "backend/scripts/README.md": 80,
}
LOCAL_ONLY_SKILL_DIRS = {"excel-live-control", "pdf", "playwright", "spreadsheets"}
RETIRED_ACTIVE_PATHS = (
    "Knull%28readme%29.md",
    "Knull(readme).md",
    "DELIVERY_VALIDATION.md",
    "docs/00-current-state.md",
    "docs/01-product-brief.md",
    "docs/02-architecture.md",
    "docs/03-database-schema.md",
    "docs/04-data-sources-and-ingestion.md",
    "docs/05-scoring-framework.md",
    "docs/06-security-threat-model.md",
    "docs/07-local-development.md",
    "docs/08-execution-runbook.md",
    "docs/09-beginner-glossary.md",
    "docs/09-route-inventory.md",
    "docs/12-assumption-methodology-engine.md",
    "docs/agent_capabilities_and_limitations.md",
    "docs/roadmaps/market-intelligence-build-roadmap.md",
    "docs/roadmaps/provider-data-execution-plan-2026-08-01.md",
    "docs/roadmaps/valuation-auto-pipeline-master-plan.md",
    "docs/roadmaps/world-class-product-ideation-register.md",
    "docs/world-class-product-execution-roadmap-2026-07-25.md",
    "docs/valuation-agent/master-build-plan.md",
    "docs/valuation-agent/autofill-workflow-plan.md",
    "docs/valuation-agent/data-batch-build-plan-index.md",
)


def active_markdown_files(root: Path = ROOT) -> list[Path]:
    root = root.resolve()
    files = [*root.glob("*.md"), *(root / ".github").glob("*.md")]
    files.extend(root / directory / "README.md" for directory in (
        "backend", "backend/scripts", "frontend", "scripts", "data", "docker",
    ))
    files.extend(
        path
        for path in (root / "docs").rglob("*.md")
        if path.name == "README.md" or (
            "archive" not in path.relative_to(root / "docs").parts
            and path.relative_to(root / "docs").parts[:2] != ("workstreams", "evidence")
        )
    )
    files.extend(
        path
        for path in (root / "damodaran_knowledge_base_v1").rglob("*.md")
        if "raw" not in path.relative_to(root / "damodaran_knowledge_base_v1").parts
    )
    files.extend(
        path for path in (root / "skills").rglob("*.md")
        if path.relative_to(root / "skills").parts[0] not in LOCAL_ONLY_SKILL_DIRS
    )
    # Nested instructions must not silently escape validation. Prune generated
    # dependencies rather than recursively scanning installed packages/builds.
    for directory in (root / "backend", root / "frontend"):
        for current, directories, names in os.walk(directory):
            directories[:] = [name for name in directories if name not in {
                "node_modules", ".next", ".venv", "__pycache__", ".pytest_cache",
            }]
            if "AGENTS.md" in names:
                files.append(Path(current) / "AGENTS.md")
    return sorted({path.resolve() for path in files if path.exists()})


def _local_target(source: Path, destination: str) -> Path | None:
    destination = destination.strip()
    if destination.startswith("<") and destination.endswith(">"):
        destination = destination[1:-1]
    if not destination or destination.startswith(("#", "http://", "https://", "mailto:")):
        return None
    destination = unquote(destination.split("#", 1)[0])
    if not destination:
        return None
    target = Path(destination)
    return target if target.is_absolute() else (source.parent / target).resolve()


def _link_destination(raw: str) -> str:
    raw = raw.strip()
    if raw.startswith("<") and ">" in raw:
        return raw[:raw.index(">") + 1]
    return raw.split(maxsplit=1)[0] if raw else ""


def _markdown_anchors(text: str) -> set[str]:
    """GitHub-style ATX heading anchors, including duplicate and explicit IDs."""
    text = FENCE_PATTERN.sub("", text)
    anchors = set(re.findall(r'<a\s+[^>]*(?:id|name)=["\']([^"\']+)["\']', text))
    used: set[str] = set()
    for heading in re.findall(r"^ {0,3}#{1,6}[ \t]+(.+?)\s*#*\s*$", text, re.MULTILINE):
        heading = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", heading)
        base = re.sub(r"[^\w\- ]", "", heading.lower()).replace(" ", "-")
        anchor, suffix = base, 0
        while anchor in used:
            suffix += 1
            anchor = f"{base}-{suffix}"
        used.add(anchor)
        anchors.add(anchor)
    return anchors


def _route_inventory_errors(root: Path) -> list[str]:
    inventory = root / "docs" / "route-inventory.md"
    if not inventory.exists():
        return []
    text = FENCE_PATTERN.sub("", inventory.read_text(encoding="utf-8"))
    pages = {path.resolve() for path in (root / "frontend" / "app").rglob("page.tsx")}
    listed = {_local_target(inventory, _link_destination(match.group(1)))
              for match in LINK_PATTERN.finditer(text)}
    errors = [f"docs/route-inventory.md: missing page {path.relative_to(root)}"
              for path in sorted(pages - listed)]
    count = re.search(r"(\d+) App Router pages", text)
    if not count or int(count.group(1)) != len(pages):
        errors.append(f"docs/route-inventory.md: page count must match {len(pages)} source pages")
    return errors


def _command_inventory_errors(root: Path) -> list[str]:
    errors: list[str] = []
    for directory in ("scripts", "backend/scripts"):
        commands = {
            path.resolve() for path in (root / directory).glob("*")
            if path.suffix in {".py", ".sh", ".sql"}
            and path.name != "__init__.py" and not path.name.startswith("test_")
            and path.is_file()
        }
        if not commands:
            continue
        guide = root / directory / "README.md"
        if not guide.exists():
            errors.append(f"{directory}/README.md: missing command inventory")
            continue
        text = FENCE_PATTERN.sub("", guide.read_text(encoding="utf-8"))
        listed = {_local_target(guide, _link_destination(match.group(1)))
                  for match in LINK_PATTERN.finditer(text)}
        errors.extend(f"{directory}/README.md: unmapped command {path.relative_to(root)}"
                      for path in sorted(commands - listed))
    return errors


def _backend_api_map_errors(root: Path) -> list[str]:
    inventory = root / "docs" / "reference" / "api-map.md"
    if not inventory.exists():
        return []
    text = FENCE_PATTERN.sub("", inventory.read_text(encoding="utf-8"))
    routers = {path.resolve() for path in (root / "backend" / "app" / "api" / "routers").glob("*.py")
               if path.name != "__init__.py"}
    listed = {_local_target(inventory, _link_destination(match.group(1)))
              for match in LINK_PATTERN.finditer(text)}
    errors = [f"docs/reference/api-map.md: unmapped HTTP router {path.relative_to(root)}"
              for path in sorted(routers - listed)]
    count = re.search(r"(\d+) HTTP router modules", text)
    if not count or int(count.group(1)) != len(routers):
        errors.append(f"docs/reference/api-map.md: router count must match {len(routers)} source modules")
    return errors


def _schema_head_errors(root: Path) -> list[str]:
    schema = root / "docs" / "database-schema.md"
    runtime = root / "backend" / "app" / "services" / "runtime_readiness.py"
    if not schema.exists() or not runtime.exists():
        return []
    expected = None
    for node in ast.parse(runtime.read_text(encoding="utf-8")).body:
        if isinstance(node, (ast.Assign, ast.AnnAssign)):
            targets = node.targets if isinstance(node, ast.Assign) else [node.target]
            if any(isinstance(target, ast.Name) and target.id == "EXPECTED_MIGRATION_HEAD" for target in targets):
                if isinstance(node.value, ast.Constant):
                    expected = node.value.value
    documented = re.search(r"\*\*Current source head:\*\*\s*`([^`]+)`", schema.read_text(encoding="utf-8"))
    if not expected or not documented or documented.group(1) != expected:
        return ["docs/database-schema.md: migration head must match runtime_readiness.EXPECTED_MIGRATION_HEAD"]
    return []


def validate(root: Path = ROOT) -> tuple[list[str], int]:
    root = root.resolve()
    errors: list[str] = []
    checked_links = 0
    anchor_cache: dict[Path, set[str]] = {}
    for path in active_markdown_files(root):
        text = path.read_text(encoding="utf-8")
        searchable = FENCE_PATTERN.sub("", text)
        relative = path.relative_to(root)
        budget = CONTEXT_LINE_BUDGETS.get(relative.as_posix())
        if budget is not None and len(text.splitlines()) > budget:
            errors.append(f"{relative}: exceeds {budget}-line context budget; archive history and link task-specific references")
        for retired_path in RETIRED_ACTIVE_PATHS:
            if retired_path in searchable:
                errors.append(f"{relative}: references retired active path {retired_path}")
        for match in LINK_PATTERN.finditer(searchable):
            destination = _link_destination(match.group(1))
            target = _local_target(path, destination)
            if target is None:
                if not destination.startswith("#"):
                    continue
                target = path
            else:
                checked_links += 1
            if not target.exists():
                errors.append(f"{relative}: broken link {match.group(1)}")
                continue
            fragment = unquote(destination.rstrip(">").partition("#")[2])
            if fragment and target.suffix.lower() == ".md":
                if target not in anchor_cache:
                    anchor_cache[target] = _markdown_anchors(target.read_text(encoding="utf-8"))
                if fragment not in anchor_cache[target]:
                    errors.append(f"{relative}: broken anchor {match.group(1)}")
        for destination in INLINE_MARKDOWN_PATH_PATTERN.findall(searchable):
            if any(marker in destination for marker in ("*", "<", ">")):
                continue
            if destination.startswith(("docs/", "frontend/", "skills/", "damodaran_knowledge_base_v1/")):
                target = (root / destination).resolve()
            elif destination in {"README.md", "AGENTS.md"}:
                target = (root / destination).resolve()
            elif path.is_relative_to(root / "damodaran_knowledge_base_v1") and destination.startswith(
                ("cases/", "core/", "data/", "knowledge/", "market/", "reference/", "review_queue/")
            ):
                target = (root / "damodaran_knowledge_base_v1" / destination).resolve()
            else:
                target = (path.parent / destination).resolve()
            checked_links += 1
            if not target.exists():
                errors.append(f"{relative}: broken inline Markdown path {destination}")
    errors.extend(_route_inventory_errors(root))
    errors.extend(_schema_head_errors(root))
    errors.extend(_command_inventory_errors(root))
    errors.extend(_backend_api_map_errors(root))
    return errors, checked_links


def main() -> int:
    errors, checked_links = validate()
    if errors:
        for error in errors:
            print(error)
        print(f"documentation check failed: {len(errors)} error(s), {checked_links} links checked")
        return 1
    print(
        f"documentation check passed: {len(active_markdown_files())} active Markdown files, "
        f"{checked_links} local links"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
