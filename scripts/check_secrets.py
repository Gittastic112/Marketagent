#!/usr/bin/env python3
"""Fail CI when source files contain credential-shaped values."""

from __future__ import annotations

import argparse
import re
from dataclasses import dataclass
from pathlib import Path


EXCLUDED_DIRS = {
    ".git",
    ".next",
    ".playwright-cli",
    ".pnpm-store",
    "backups",
    "data",
    "node_modules",
    "output",
    "playwright-report",
    "scratch",
}
SCANNED_SUFFIXES = {
    ".env",
    ".ini",
    ".js",
    ".json",
    ".md",
    ".mjs",
    ".py",
    ".sh",
    ".toml",
    ".ts",
    ".tsx",
    ".yaml",
    ".yml",
}
TOKEN_PATTERNS = (
    ("private_key", re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----")),
    ("aws_access_key", re.compile(r"\b(?:AKIA|ASIA)[A-Z0-9]{16}\b")),
    ("github_token", re.compile(r"\bgh[oprs]_[A-Za-z0-9]{30,}\b")),
    ("openai_key", re.compile(r"\bsk-(?:proj-)?[A-Za-z0-9_-]{20,}\b")),
    ("slack_token", re.compile(r"\bxox[baprs]-[A-Za-z0-9-]{20,}\b")),
)
ASSIGNMENT_PATTERN = re.compile(
    r"(?i)\b(?:api[_-]?key|access[_-]?token|auth[_-]?token|client[_-]?secret|"
    r"database[_-]?password|nextauth[_-]?secret|password|private[_-]?key)\b"
    r"\s*(?:=|:)\s*(?P<quote>[\"'])(?P<value>[^\"']+)(?P=quote)"
)
SAFE_VALUE_PARTS = (
    "${",
    "example",
    "fallback",
    "local-only",
    "marketintel_password",
    "not-for-production",
    "placeholder",
    "replace",
    "test",
    "your_",
    "your-",
)


@dataclass(frozen=True)
class Finding:
    path: Path
    line_number: int
    kind: str


def _is_safe_assignment(value: str) -> bool:
    normalized = value.strip().lower()
    return (
        not normalized
        or normalized in {"none", "null", "changeme"}
        or any(marker in normalized for marker in SAFE_VALUE_PARTS)
    )


def scan_text(path: Path, text: str) -> list[Finding]:
    findings: list[Finding] = []
    for line_number, line in enumerate(text.splitlines(), start=1):
        for kind, pattern in TOKEN_PATTERNS:
            if pattern.search(line):
                findings.append(Finding(path, line_number, kind))
        assignment = ASSIGNMENT_PATTERN.search(line)
        if assignment and not _is_safe_assignment(assignment.group("value")):
            findings.append(Finding(path, line_number, "credential_assignment"))
    return findings


def iter_source_files(root: Path):
    for path in root.rglob("*"):
        if not path.is_file() or any(
            part in EXCLUDED_DIRS or part == "venv" or part.startswith(".venv")
            for part in path.parts
        ):
            continue
        if path.name == ".env.example" or path.suffix.lower() in SCANNED_SUFFIXES:
            yield path


def scan_repository(root: Path) -> list[Finding]:
    findings: list[Finding] = []
    for path in iter_source_files(root):
        try:
            findings.extend(scan_text(path.relative_to(root), path.read_text(encoding="utf-8")))
        except UnicodeDecodeError:
            continue
    return findings


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", nargs="?", default=Path(__file__).resolve().parents[1], type=Path)
    args = parser.parse_args()
    findings = scan_repository(args.root.resolve())
    if findings:
        for finding in findings:
            print(f"{finding.path}:{finding.line_number}: possible {finding.kind}")
        print(f"Secret scan failed: {len(findings)} possible credential(s) found.")
        return 1
    print("Secret scan passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
