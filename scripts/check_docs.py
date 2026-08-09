#!/usr/bin/env python3
"""Validate links and retired-path references in active documentation."""

from __future__ import annotations

import re
import sys
from pathlib import Path
from urllib.parse import unquote


ROOT = Path(__file__).resolve().parents[1]
LINK_PATTERN = re.compile(r"\[[^\]]+\]\(([^)]+)\)")
INLINE_MARKDOWN_PATH_PATTERN = re.compile(r"`([^`\n]*\.md)`")
FENCE_PATTERN = re.compile(r"```.*?```", re.DOTALL)
RETIRED_ACTIVE_PATHS = (
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
    files = [root / "README.md", root / "AGENTS.md", root / "frontend" / "README.md"]
    files.extend(
        path
        for path in (root / "docs").rglob("*.md")
        if "archive" not in path.relative_to(root / "docs").parts
    )
    files.extend(
        path
        for path in (root / "damodaran_knowledge_base_v1").rglob("*.md")
        if "raw" not in path.relative_to(root / "damodaran_knowledge_base_v1").parts
    )
    files.extend((root / "skills").rglob("*.md"))
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


def validate(root: Path = ROOT) -> tuple[list[str], int]:
    root = root.resolve()
    errors: list[str] = []
    checked_links = 0
    for path in active_markdown_files(root):
        text = path.read_text(encoding="utf-8")
        searchable = FENCE_PATTERN.sub("", text)
        relative = path.relative_to(root)
        for retired_path in RETIRED_ACTIVE_PATHS:
            if retired_path in searchable:
                errors.append(f"{relative}: references retired active path {retired_path}")
        for match in LINK_PATTERN.finditer(searchable):
            destination = match.group(1).split(maxsplit=1)[0]
            target = _local_target(path, destination)
            if target is None:
                continue
            checked_links += 1
            if not target.exists():
                errors.append(f"{relative}: broken link {match.group(1)}")
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
