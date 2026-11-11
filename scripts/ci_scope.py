#!/usr/bin/env python3
"""Fail closed when deciding whether a change needs the full CI suite."""

import argparse
import json
import os
import re
import subprocess
from pathlib import Path, PurePosixPath

FULL_JOBS = (
    "container-security",
    "recovery-quality-gate",
    "dependency-security",
    "release-baseline",
    "browser-quality-gate",
)
GUIDE_ROOTS = {"backend", "frontend", "scripts", "data", "docker"}
SHA = re.compile(r"[0-9a-f]{40}")


def changed_paths(base, head, *, cwd=None):
    """Include both sides of renames and every commit in the event's range."""
    if not all(isinstance(ref, str) and SHA.fullmatch(ref) and ref != "0" * 40 for ref in (base, head)):
        return None
    result = subprocess.run(
        ["git", "diff", "--no-ext-diff", "--no-renames", "--name-only", "-z", base, head, "--"],
        cwd=cwd, capture_output=True, check=False,
    )
    if result.returncode:
        return None
    return result.stdout.decode("utf-8", errors="replace").rstrip("\0").split("\0") if result.stdout else []


def is_documentation(file):
    parts = PurePosixPath(file).parts
    if not parts or file.startswith("/") or any(part in {".", ".."} for part in file.split("/")) or any(ord(char) < 32 for char in file):
        return False
    if file in {"README.md", "AGENTS.md"}:
        return True
    if parts[0] == "docs" and file.endswith(".md"):
        return True
    if len(parts) == 2 and parts[0] == ".github" and file.endswith(".md"):
        return True
    return parts[0] in GUIDE_ROOTS and len(parts) > 1 and parts[-1] in {"README.md", "AGENTS.md"}


def classify(paths, event, ref):
    if event not in {"push", "pull_request"} or (event == "push" and not ref.startswith("refs/heads/")):
        return True, "This event requires the full suite."
    if not paths:
        return True, "The comparison is empty or unavailable."
    if all(is_documentation(file) for file in paths):
        return False, "Only recognized Markdown documentation changed."
    return True, "Runtime, tooling, configuration, or an unrecognized path changed."


def gate_errors(needs):
    if not isinstance(needs, dict):
        return ["Missing CI results."]
    scope = needs.get("repository-checks", {})
    if scope.get("result") != "success":
        return ["Repository checks did not pass."]
    full = scope.get("outputs", {}).get("full_ci")
    if full not in {"true", "false"}:
        return ["Missing or invalid CI scope."]
    expected = "success" if full == "true" else "skipped"
    return [
        f"{name}: expected {expected}, got {needs.get(name, {}).get('result', 'missing')}."
        for name in FULL_JOBS if needs.get(name, {}).get("result") != expected
    ]


def classify_event():
    try:
        payload = json.loads(Path(os.environ["GITHUB_EVENT_PATH"]).read_text())
    except (KeyError, OSError, ValueError):
        payload = {}
    event = os.environ.get("GITHUB_EVENT_NAME", "")
    if event == "pull_request":
        pr = payload.get("pull_request", {})
        base, head = pr.get("base", {}).get("sha"), pr.get("head", {}).get("sha")
    else:
        base, head = payload.get("before"), os.environ.get("GITHUB_SHA")
    paths = changed_paths(base, head)
    full, reason = classify(paths, event, os.environ.get("GITHUB_REF", ""))
    print(f"Full suite: {str(full).lower()}. {reason}")
    output = os.environ.get("GITHUB_OUTPUT")
    if output:
        with open(output, "a") as handle:
            handle.write(f"full_ci={str(full).lower()}\n")
    if paths is not None:
        patch = subprocess.run(
            ["git", "diff", "--no-ext-diff", "--check", base, head, "--"],
            capture_output=True, check=False,
        )
        if patch.returncode:
            # Do not echo potentially sensitive source lines into public CI logs.
            print("Patch formatting failed. Run git diff --check over this change locally.")
            return 1
    return 0


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("classify", "gate"))
    args = parser.parse_args()
    if args.command == "classify":
        return classify_event()
    try:
        needs = json.loads(os.environ.get("CI_NEEDS_JSON", "null"))
    except ValueError:
        needs = None
    errors = gate_errors(needs)
    for error in errors:
        print(error)
    if not errors:
        print("All checks required for this change passed.")
    return int(bool(errors))


if __name__ == "__main__":
    raise SystemExit(main())
