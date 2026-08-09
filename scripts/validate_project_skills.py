from pathlib import Path

REQUIRED_SECTIONS = [
    "## Purpose",
    "## When to use",
    "## When NOT to use",
    "## Prerequisites",
    "## Inputs",
    "## Outputs",
    "## Workflow",
    "## Acceptance criteria",
    "## Common mistakes",
    "## Do not do",
    "## Related skills",
    "## References",
]


def main() -> int:
    root = Path("docs/skills")
    skill_files = sorted(path for path in root.glob("*/*.md") if path.name != "README.md")
    failures: list[str] = []

    for path in skill_files:
        text = path.read_text(encoding="utf-8")
        missing = [section for section in REQUIRED_SECTIONS if section not in text]
        if missing:
            failures.append(f"{path}: missing {', '.join(missing)}")

    if not skill_files:
        failures.append("No project skill files found under docs/skills/*/*.md")

    if failures:
        print("Project skill validation failed:")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print(f"Project skill validation passed: {len(skill_files)} skills checked")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
