"""Report every OS finding; block available high/critical fixes, never hide them."""
from collections import Counter
import json
from pathlib import Path
import sys


def summarize(report: dict) -> tuple[dict[str, int], int]:
    if not report.get("Metadata", {}).get("OS", {}).get("Family"):
        raise ValueError("Container OS was not identified")
    results = [item for item in report.get("Results", []) if item.get("Class") == "os-pkgs"]
    if not results or not any(item.get("Packages") for item in results):
        raise ValueError("Container OS package inventory was not scanned")
    findings = [item for result in results for item in result.get("Vulnerabilities", [])]
    fixed = [item for item in findings if item.get("Severity") in {"HIGH", "CRITICAL"} and item.get("FixedVersion")]
    return dict(Counter(item.get("Severity", "UNKNOWN") for item in findings)), len(fixed)


def main(paths: list[str]) -> int:
    if not paths:
        raise ValueError("At least one scan report is required")
    blockers = 0
    for path in paths:
        counts, fixable = summarize(json.loads(Path(path).read_text()))
        print(f"{Path(path).name}: all OS findings {counts}; available high/critical fixes: {fixable}")
        blockers += fixable
    print("Unfixed findings still require review; a passing update gate is not a clean security audit.")
    return int(blockers > 0)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
