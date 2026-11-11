"""Compatibility notice for the retired, unauthenticated milestone checker."""

from __future__ import annotations

import sys


def main(argv: list[str] | None = None) -> int:
    print(
        "Not available: the legacy Milestone A verifier is retired. "
        "Use the authenticated Data Health workflow for provider checks, or "
        "scripts/verify_release_baseline.sh for isolated software verification. "
        "Acceptance criteria are in docs/roadmaps/completion-tracker.md.",
        file=sys.stderr,
    )
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
